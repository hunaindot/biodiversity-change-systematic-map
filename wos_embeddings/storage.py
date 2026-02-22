"""Storage utilities for embeddings and metadata."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import EmbedConfig

logger = logging.getLogger(__name__)


def save_embeddings(
    output_dir: Path,
    embeddings: np.ndarray,
    record_ids: list[str],
    save_format: str = "npz",
) -> None:
    """Save embeddings to disk, merging with existing data if present.

    On reruns (e.g. after failures), new embeddings are appended to the
    existing file. Duplicate record IDs are avoided — if an ID already
    exists, the new embedding replaces the old one.

    Args:
        output_dir: Directory to save embeddings
        embeddings: Array of embeddings (N, embedding_dim)
        record_ids: List of UT IDs corresponding to embeddings
        save_format: Format to save (npz, hdf5, or pickle)

    Raises:
        ValueError: If save_format is not supported
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if save_format == "npz":
        output_path = output_dir / "embeddings.npz"

        # Merge with existing if present
        if output_path.exists():
            existing = np.load(output_path, allow_pickle=False)
            existing_embeddings = existing['embeddings']
            existing_ids = existing['record_ids'].tolist()

            # Build index of existing IDs for dedup
            new_ids_set = set(record_ids)
            keep_mask = [eid not in new_ids_set for eid in existing_ids]

            kept_embeddings = existing_embeddings[keep_mask]
            kept_ids = [eid for eid, keep in zip(existing_ids, keep_mask) if keep]

            # Combine: existing (minus duplicates) + new
            merged_embeddings = np.vstack([kept_embeddings, embeddings]) if len(kept_embeddings) > 0 else embeddings
            merged_ids = kept_ids + list(record_ids)

            logger.info(
                f"Merged embeddings: {len(kept_ids)} existing + {len(record_ids)} new = {len(merged_ids)} total"
            )
        else:
            merged_embeddings = embeddings
            merged_ids = list(record_ids)

        np.savez_compressed(
            output_path,
            embeddings=merged_embeddings,
            record_ids=np.array(merged_ids, dtype='U50'),
        )
        logger.debug(f"Saved embeddings to {output_path} (NPZ compressed)")

    elif save_format == "hdf5":
        try:
            import h5py
        except ImportError as e:
            raise ImportError("h5py is required for HDF5 format. Install with: pip install h5py") from e

        output_path = output_dir / "embeddings.h5"
        with h5py.File(output_path, 'a') as f:
            if 'embeddings' in f:
                # Append to existing dataset
                existing = f['embeddings']
                new_size = existing.shape[0] + embeddings.shape[0]
                existing.resize((new_size, embeddings.shape[1]))
                existing[-embeddings.shape[0]:] = embeddings

                existing_ids = f['record_ids']
                existing_ids.resize((new_size,))
                existing_ids[-len(record_ids):] = record_ids
            else:
                # Create new datasets
                f.create_dataset(
                    'embeddings',
                    data=embeddings,
                    maxshape=(None, embeddings.shape[1]),
                    compression='gzip',
                )
                f.create_dataset(
                    'record_ids',
                    data=np.array(record_ids, dtype='U50'),
                    maxshape=(None,),
                )
        logger.debug(f"Saved embeddings to {output_path} (HDF5)")

    elif save_format == "pickle":
        import pickle
        output_path = output_dir / "embeddings.pkl"
        with output_path.open('wb') as f:
            pickle.dump({'embeddings': embeddings, 'record_ids': record_ids}, f)
        logger.debug(f"Saved embeddings to {output_path} (Pickle)")

    else:
        raise ValueError(f"Unsupported save format: {save_format}. Use npz, hdf5, or pickle.")


def load_embeddings(partition_name: str, config: EmbedConfig) -> dict[str, Any]:
    """Load embeddings from disk.

    Args:
        partition_name: Partition identifier (e.g., "1", "50")
        config: Configuration with output paths and formats

    Returns:
        Dict with 'embeddings' (np.ndarray) and 'record_ids' (list of str)

    Raises:
        FileNotFoundError: If embeddings file doesn't exist
        ValueError: If save_format is not supported
    """
    output_dir = config.output_base / str(partition_name)

    if config.save_format == "npz":
        output_path = output_dir / "embeddings.npz"
        if not output_path.exists():
            raise FileNotFoundError(f"Embeddings not found: {output_path}")

        data = np.load(output_path, allow_pickle=False)
        return {
            'embeddings': data['embeddings'],
            'record_ids': data['record_ids'].tolist(),
        }

    elif config.save_format == "hdf5":
        try:
            import h5py
        except ImportError as e:
            raise ImportError("h5py is required for HDF5 format. Install with: pip install h5py") from e

        output_path = output_dir / "embeddings.h5"
        if not output_path.exists():
            raise FileNotFoundError(f"Embeddings not found: {output_path}")

        with h5py.File(output_path, 'r') as f:
            return {
                'embeddings': f['embeddings'][:],
                'record_ids': f['record_ids'][:].astype(str).tolist(),
            }

    elif config.save_format == "pickle":
        import pickle
        output_path = output_dir / "embeddings.pkl"
        if not output_path.exists():
            raise FileNotFoundError(f"Embeddings not found: {output_path}")

        with output_path.open('rb') as f:
            return pickle.load(f)

    else:
        raise ValueError(f"Unsupported save format: {config.save_format}")


def save_metadata(
    output_dir: Path,
    metadata_df: pd.DataFrame,
    metadata_format: str = "parquet",
) -> None:
    """Save metadata to disk, merging with existing data if present.

    On reruns, new metadata rows are appended. Duplicate UT IDs are
    replaced with the newer entry.

    Args:
        output_dir: Directory to save metadata
        metadata_df: DataFrame with metadata columns
        metadata_format: Format to save (parquet or csv)

    Raises:
        ValueError: If metadata_format is not supported
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if metadata_format == "parquet":
        output_path = output_dir / "metadata.parquet"

        if output_path.exists():
            existing_df = pd.read_parquet(output_path)
            # Remove rows with IDs that are in the new data (dedup)
            new_ids = set(metadata_df['ut'])
            existing_df = existing_df[~existing_df['ut'].isin(new_ids)]
            merged_df = pd.concat([existing_df, metadata_df], ignore_index=True)
            # Reindex embedding_index to be sequential
            merged_df['embedding_index'] = range(len(merged_df))
            logger.info(f"Merged metadata: {len(existing_df)} existing + {len(metadata_df)} new = {len(merged_df)} total")
        else:
            merged_df = metadata_df

        merged_df.to_parquet(output_path, index=False, compression='snappy')
        logger.debug(f"Saved metadata to {output_path} (Parquet)")

    elif metadata_format == "csv":
        output_path = output_dir / "metadata.csv"

        if output_path.exists():
            existing_df = pd.read_csv(output_path)
            new_ids = set(metadata_df['ut'])
            existing_df = existing_df[~existing_df['ut'].isin(new_ids)]
            merged_df = pd.concat([existing_df, metadata_df], ignore_index=True)
            merged_df['embedding_index'] = range(len(merged_df))
            logger.info(f"Merged metadata: {len(existing_df)} existing + {len(metadata_df)} new = {len(merged_df)} total")
        else:
            merged_df = metadata_df

        merged_df.to_csv(output_path, index=False)
        logger.debug(f"Saved metadata to {output_path} (CSV)")

    else:
        raise ValueError(f"Unsupported metadata format: {metadata_format}. Use parquet or csv.")


def load_metadata(partition_name: str, config: EmbedConfig) -> pd.DataFrame:
    """Load metadata from disk.

    Args:
        partition_name: Partition identifier (e.g., "1", "50")
        config: Configuration with output paths and formats

    Returns:
        DataFrame with metadata

    Raises:
        FileNotFoundError: If metadata file doesn't exist
        ValueError: If metadata_format is not supported
    """
    output_dir = config.output_base / str(partition_name)

    if config.metadata_format == "parquet":
        output_path = output_dir / "metadata.parquet"
        if not output_path.exists():
            raise FileNotFoundError(f"Metadata not found: {output_path}")
        return pd.read_parquet(output_path)

    elif config.metadata_format == "csv":
        output_path = output_dir / "metadata.csv"
        if not output_path.exists():
            raise FileNotFoundError(f"Metadata not found: {output_path}")
        return pd.read_csv(output_path)

    else:
        raise ValueError(f"Unsupported metadata format: {config.metadata_format}")


def create_metadata_df(
    ut_ids: list[str],
    titles: list[str],
    abstracts: list[str],
    combined_texts: list[str],
) -> pd.DataFrame:
    """Create metadata DataFrame from lists.

    Args:
        ut_ids: List of UT (Unique WOS ID) values
        titles: List of article titles
        abstracts: List of abstracts
        combined_texts: List of combined texts that were embedded

    Returns:
        DataFrame with metadata columns
    """
    return pd.DataFrame({
        'ut': ut_ids,
        'title': titles,
        'abstract': abstracts,
        'combined_text': combined_texts,
        'embedding_index': range(len(ut_ids)),
        'text_length': [len(t) for t in combined_texts],
        'processed_at': datetime.utcnow(),
    })
