"""Main processing orchestration for partition embedding generation."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from tqdm import tqdm

from .config import EmbedConfig
from .embedder import EmbeddingGenerator
from .progress import ProgressTracker
from .storage import create_metadata_df, save_embeddings, save_metadata

logger = logging.getLogger(__name__)


def _find_partition_file(partition_dir: Path) -> Path | None:
    """Find the Excel file in a partition directory.

    Args:
        partition_dir: Partition directory path

    Returns:
        Path to Excel file, or None if not found
    """
    xlsx_files = list(partition_dir.glob("*.xlsx"))
    if not xlsx_files:
        return None
    if len(xlsx_files) > 1:
        logger.warning(f"Multiple Excel files found in {partition_dir}. Using first: {xlsx_files[0].name}")
    return xlsx_files[0]


def _load_partition_data(partition_name: str, config: EmbedConfig) -> tuple[pd.DataFrame, str]:
    """Load partition data from Excel file.

    Args:
        partition_name: Partition identifier (e.g., "1", "50")
        config: Configuration with partition paths

    Returns:
        Tuple of (DataFrame, partition_file_name)

    Raises:
        FileNotFoundError: If partition directory or Excel file not found
        ValueError: If required columns are missing
    """
    partition_dir = config.partitions_base / str(partition_name)
    if not partition_dir.exists():
        raise FileNotFoundError(f"Partition directory not found: {partition_dir}")

    excel_file = _find_partition_file(partition_dir)
    if excel_file is None:
        raise FileNotFoundError(f"No Excel file found in {partition_dir}")

    logger.info(f"Loading partition {partition_name} from {excel_file.name}")
    df = pd.read_excel(excel_file)

    # Verify required columns exist
    required_cols = ["Article Title", "Abstract", "UT (Unique WOS ID)"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    logger.info(f"Loaded {len(df)} records from partition {partition_name}")
    return df, excel_file.name


def process_partition(
    partition_name: str,
    config: EmbedConfig | None = None,
    show_progress: bool = True,
) -> dict[str, Any]:
    """Process a single partition to generate embeddings.

    This function:
    1. Loads partition data from Excel
    2. Checks for existing progress (if resume=True)
    3. Filters to unprocessed records
    4. Generates embeddings in batches
    5. Saves embeddings and metadata
    6. Updates progress tracking

    Args:
        partition_name: Partition identifier (e.g., "1", "50")
        config: Configuration (uses defaults if None)
        show_progress: Whether to show progress bar

    Returns:
        Dictionary with processing summary

    Raises:
        FileNotFoundError: If partition data not found
        ValueError: If configuration is invalid
    """
    config = config or EmbedConfig()
    start_time = time.time()

    # Setup output directory
    output_dir = config.output_base / str(partition_name)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize progress tracker
    tracker = ProgressTracker(output_dir)

    # Load partition data
    try:
        df, partition_file = _load_partition_data(partition_name, config)
    except Exception as e:
        logger.error(f"Failed to load partition {partition_name}: {e}")
        tracker.mark_failed(str(e))
        raise

    # Initialize embedding generator (lazy load, only once)
    embedder = EmbeddingGenerator(
        model_name=config.model_name,
        text_prefix=config.text_prefix,
        trust_remote_code=config.trust_remote_code,
    )

    # Initialize tracker metadata
    tracker.initialize(
        partition_name=str(partition_name),
        partition_file=partition_file,
        total_records=len(df),
        model_name=config.model_name,
        embedding_dimension=embedder.embedding_dim,
        config={
            "batch_size": config.batch_size,
            "text_prefix": config.text_prefix,
            "skip_empty_abstracts": config.skip_empty_abstracts,
        },
    )

    # Handle overwrite mode
    if config.overwrite:
        logger.info("Overwrite mode enabled. Processing all records.")
        df_to_process = df
    elif config.resume:
        # Filter to unprocessed records
        processed_ids = tracker.get_processed_ids()
        if processed_ids:
            logger.info(f"Resume mode: {len(processed_ids)} records already processed")
            df_to_process = df[~df["UT (Unique WOS ID)"].isin(processed_ids)]
        else:
            df_to_process = df
    else:
        df_to_process = df

    # Check if already complete
    if len(df_to_process) == 0:
        logger.info(f"Partition {partition_name} already fully processed. Skipping.")
        return tracker.get_summary()

    logger.info(f"Processing {len(df_to_process)} records from partition {partition_name}")

    # Prepare for batch processing
    all_embeddings = []
    all_ut_ids = []
    all_titles = []
    all_abstracts = []
    all_combined_texts = []
    failed_ids = []

    # Process in batches
    batch_size = config.batch_size
    total_batches = (len(df_to_process) + batch_size - 1) // batch_size

    iterator = range(0, len(df_to_process), batch_size)
    if show_progress:
        iterator = tqdm(iterator, total=total_batches, desc=f"Partition {partition_name}")

    for start_idx in iterator:
        end_idx = min(start_idx + batch_size, len(df_to_process))
        batch_df = df_to_process.iloc[start_idx:end_idx]

        # Prepare texts for embedding
        batch_texts = []
        batch_ut_ids = []
        batch_titles = []
        batch_abstracts = []
        batch_indices = []

        for idx, row in batch_df.iterrows():
            title = row["Article Title"]
            abstract = row["Abstract"]
            ut_id = row["UT (Unique WOS ID)"]

            # Prepare text
            prepared_text = embedder.prepare_text(
                title=title,
                abstract=abstract,
                skip_empty_abstracts=config.skip_empty_abstracts,
            )

            if prepared_text is None:
                # Skip this record
                failed_ids.append(ut_id)
                continue

            batch_texts.append(prepared_text)
            batch_ut_ids.append(ut_id)
            batch_titles.append(title)
            batch_abstracts.append(abstract)
            batch_indices.append(idx)

        # Generate embeddings for batch
        if batch_texts:
            try:
                batch_embeddings = embedder.embed_batch(
                    batch_texts,
                    batch_size=config.batch_size,
                    show_progress_bar=False,
                )

                # Accumulate results
                all_embeddings.append(batch_embeddings)
                all_ut_ids.extend(batch_ut_ids)
                all_titles.extend(batch_titles)
                all_abstracts.extend(batch_abstracts)
                all_combined_texts.extend(batch_texts)

                # Update progress
                tracker.update_batch(processed_ids=batch_ut_ids, failed_ids=[])

            except Exception as e:
                logger.error(f"Failed to embed batch starting at index {start_idx}: {e}")
                failed_ids.extend(batch_ut_ids)
                tracker.update_batch(processed_ids=[], failed_ids=batch_ut_ids)

    # Combine all embeddings
    if all_embeddings:
        combined_embeddings = np.vstack(all_embeddings)

        # Save embeddings
        save_embeddings(
            output_dir=output_dir,
            embeddings=combined_embeddings,
            record_ids=all_ut_ids,
            save_format=config.save_format,
        )

        # Create and save metadata
        metadata_df = create_metadata_df(
            ut_ids=all_ut_ids,
            titles=all_titles,
            abstracts=all_abstracts,
            combined_texts=all_combined_texts,
        )
        save_metadata(
            output_dir=output_dir,
            metadata_df=metadata_df,
            metadata_format=config.metadata_format,
        )

        logger.info(f"Saved {len(all_ut_ids)} embeddings to {output_dir}")

    # Mark as completed
    processing_time = time.time() - start_time
    tracker.mark_completed(processing_time_seconds=processing_time)

    summary = tracker.get_summary()
    summary["processing_time_seconds"] = processing_time
    summary["new_embeddings"] = len(all_ut_ids)
    summary["failed_records"] = len(failed_ids)

    logger.info(
        f"Completed partition {partition_name}: "
        f"{len(all_ut_ids)} embedded, {len(failed_ids)} failed, "
        f"{processing_time:.1f}s"
    )

    return summary


def process_partitions(
    partition_names: list[str] | range,
    config: EmbedConfig | None = None,
    show_progress: bool = True,
) -> dict[str, Any]:
    """Process multiple partitions sequentially.

    Args:
        partition_names: List or range of partition identifiers
        config: Configuration (uses defaults if None)
        show_progress: Whether to show progress bar

    Returns:
        Dictionary mapping partition names to their summaries
    """
    config = config or EmbedConfig()
    results = {}

    partition_list = list(partition_names)
    logger.info(f"Processing {len(partition_list)} partitions")

    for partition_name in partition_list:
        try:
            summary = process_partition(
                partition_name=str(partition_name),
                config=config,
                show_progress=show_progress,
            )
            results[str(partition_name)] = summary
        except Exception as e:
            logger.error(f"Failed to process partition {partition_name}: {e}")
            results[str(partition_name)] = {
                "status": "failed",
                "error": str(e),
            }

    return results


def process_all_partitions(
    config: EmbedConfig | None = None,
    start: int = 1,
    end: int = 234,
    show_progress: bool = True,
) -> dict[str, Any]:
    """Process all partitions from start to end (inclusive).

    Args:
        config: Configuration (uses defaults if None)
        start: First partition number (default: 1)
        end: Last partition number (default: 234)
        show_progress: Whether to show progress bar

    Returns:
        Dictionary mapping partition names to their summaries
    """
    return process_partitions(
        partition_names=range(start, end + 1),
        config=config,
        show_progress=show_progress,
    )
