"""Progress tracking and meta.json management for incremental processing."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Track processing progress for a partition with meta.json.

    This class manages the meta.json file that tracks which records have been
    processed, enabling resume capability and incremental processing.

    Attributes:
        output_dir: Directory where meta.json is stored
        meta_path: Path to meta.json file
        meta: Current metadata dictionary
    """

    def __init__(self, output_dir: Path):
        """Initialize progress tracker.

        Args:
            output_dir: Directory to store meta.json
        """
        self.output_dir = output_dir
        self.meta_path = output_dir / "meta.json"
        self.meta = self._load_or_init()

    def _load_or_init(self) -> dict[str, Any]:
        """Load existing meta.json or initialize new one.

        Returns:
            Metadata dictionary
        """
        if self.meta_path.exists():
            try:
                with self.meta_path.open('r') as f:
                    meta = json.load(f)
                logger.info(f"Loaded existing progress from {self.meta_path}")
                return meta
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load meta.json: {e}. Starting fresh.")
                return self._create_empty_meta()
        else:
            logger.info("No existing progress found. Starting fresh.")
            return self._create_empty_meta()

    def _create_empty_meta(self) -> dict[str, Any]:
        """Create empty metadata dictionary.

        Returns:
            Empty metadata with default values
        """
        return {
            "partition_name": None,
            "partition_file": None,
            "total_records": 0,
            "processed_records": 0,
            "failed_records": 0,
            "last_processed_index": -1,
            "processing_status": "pending",
            "model_name": None,
            "embedding_dimension": None,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "processing_time_seconds": 0,
            "processed_ut_ids": [],
            "failed_ut_ids": [],
            "config": {},
        }

    def get_processed_ids(self) -> set[str]:
        """Get set of already-processed UT IDs.

        Returns:
            Set of processed UT IDs
        """
        return set(self.meta.get("processed_ut_ids", []))

    def initialize(
        self,
        partition_name: str,
        partition_file: str,
        total_records: int,
        model_name: str,
        embedding_dimension: int,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize metadata for a new partition.

        Args:
            partition_name: Partition identifier (e.g., "1", "50")
            partition_file: Name of the partition Excel file
            total_records: Total number of records in partition
            model_name: Name of embedding model
            embedding_dimension: Dimension of embeddings
            config: Optional configuration dictionary
        """
        # Only initialize if not already set
        if self.meta.get("partition_name") is None:
            self.meta.update({
                "partition_name": partition_name,
                "partition_file": partition_file,
                "total_records": total_records,
                "model_name": model_name,
                "embedding_dimension": embedding_dimension,
                "config": config or {},
                "processing_status": "in_progress",
            })
            self.save()
            logger.info(f"Initialized progress tracking for partition {partition_name}")

    def update_batch(
        self,
        processed_ids: list[str],
        failed_ids: list[str] | None = None,
    ) -> None:
        """Update progress after processing a batch.

        When a previously failed ID is now processed successfully,
        it is removed from failed_ut_ids and added to processed_ut_ids.

        Args:
            processed_ids: List of successfully processed UT IDs
            failed_ids: Optional list of failed UT IDs
        """
        failed_ids = failed_ids or []

        existing_processed = set(self.meta.get("processed_ut_ids", []))
        existing_failed = set(self.meta.get("failed_ut_ids", []))

        # Add new processed IDs (avoid duplicates)
        new_processed = [uid for uid in processed_ids if uid not in existing_processed]
        self.meta["processed_ut_ids"].extend(new_processed)

        # Remove newly processed IDs from failed list (recovered on rerun)
        newly_processed_set = set(processed_ids)
        recovered = existing_failed & newly_processed_set
        if recovered:
            self.meta["failed_ut_ids"] = [
                uid for uid in self.meta["failed_ut_ids"] if uid not in recovered
            ]
            logger.info(f"Recovered {len(recovered)} previously failed IDs on rerun")

        # Add new failed IDs (only if not already processed)
        all_processed = set(self.meta["processed_ut_ids"])
        new_failed = [
            uid for uid in failed_ids
            if uid not in existing_failed and uid not in all_processed
        ]
        self.meta["failed_ut_ids"].extend(new_failed)

        # Update counts
        self.meta["processed_records"] = len(self.meta["processed_ut_ids"])
        self.meta["failed_records"] = len(self.meta["failed_ut_ids"])

        # Update timestamp
        self.meta["updated_at"] = datetime.utcnow().isoformat() + "Z"

        self.save()
        logger.debug(f"Updated progress: +{len(new_processed)} processed, +{len(new_failed)} failed")

    def mark_completed(self, processing_time_seconds: float | None = None) -> None:
        """Mark partition processing as completed.

        Args:
            processing_time_seconds: Optional total processing time
        """
        self.meta["processing_status"] = "completed"
        self.meta["updated_at"] = datetime.utcnow().isoformat() + "Z"

        if processing_time_seconds is not None:
            self.meta["processing_time_seconds"] = processing_time_seconds

        self.save()
        logger.info(f"Marked partition as completed: {self.meta['processed_records']} records processed")

    def mark_failed(self, error_message: str | None = None) -> None:
        """Mark partition processing as failed.

        Args:
            error_message: Optional error message to store
        """
        self.meta["processing_status"] = "failed"
        self.meta["updated_at"] = datetime.utcnow().isoformat() + "Z"

        if error_message:
            self.meta["error_message"] = error_message

        self.save()
        logger.error(f"Marked partition as failed: {error_message}")

    def save(self) -> None:
        """Save metadata to disk atomically.

        Uses atomic write (write to temp, then rename) to ensure consistency.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Write to temp file first
        temp_path = self.meta_path.with_suffix('.json.tmp')
        with temp_path.open('w') as f:
            json.dump(self.meta, f, indent=2)

        # Atomic rename
        temp_path.replace(self.meta_path)
        logger.debug(f"Saved progress to {self.meta_path}")

    def audit(self, actual_record_ids: set[str]) -> dict[str, Any]:
        """Audit meta.json against actual saved embeddings.

        Ensures processed_ut_ids only contains IDs that are actually present
        in the embeddings file. Removes any orphaned IDs and updates counts.

        Args:
            actual_record_ids: Set of UT IDs actually present in saved embeddings

        Returns:
            Audit report with counts of removed/corrected entries
        """
        claimed_processed = set(self.meta.get("processed_ut_ids", []))
        claimed_failed = set(self.meta.get("failed_ut_ids", []))

        # Find IDs claimed as processed but not in actual embeddings
        orphaned = claimed_processed - actual_record_ids
        # Find IDs in embeddings but not claimed as processed
        unclaimed = actual_record_ids - claimed_processed

        report = {
            "claimed_processed": len(claimed_processed),
            "actual_in_embeddings": len(actual_record_ids),
            "orphaned_removed": len(orphaned),
            "unclaimed_added": len(unclaimed),
            "failed_cleaned": 0,
        }

        changed = False

        # Remove orphaned IDs from processed list
        if orphaned:
            self.meta["processed_ut_ids"] = [
                uid for uid in self.meta["processed_ut_ids"] if uid not in orphaned
            ]
            logger.warning(f"Audit: removed {len(orphaned)} orphaned IDs from processed list")
            changed = True

        # Add unclaimed IDs that are actually in embeddings
        if unclaimed:
            self.meta["processed_ut_ids"].extend(list(unclaimed))
            logger.info(f"Audit: added {len(unclaimed)} unclaimed IDs to processed list")
            changed = True

        # Clean failed list: remove any IDs that are now in processed
        all_processed = set(self.meta["processed_ut_ids"])
        failed_before = len(self.meta.get("failed_ut_ids", []))
        self.meta["failed_ut_ids"] = [
            uid for uid in self.meta.get("failed_ut_ids", []) if uid not in all_processed
        ]
        failed_cleaned = failed_before - len(self.meta["failed_ut_ids"])
        report["failed_cleaned"] = failed_cleaned
        if failed_cleaned:
            logger.info(f"Audit: removed {failed_cleaned} recovered IDs from failed list")
            changed = True

        # Update counts
        if changed:
            self.meta["processed_records"] = len(self.meta["processed_ut_ids"])
            self.meta["failed_records"] = len(self.meta["failed_ut_ids"])
            self.meta["updated_at"] = datetime.utcnow().isoformat() + "Z"
            self.save()
            logger.info(f"Audit complete: {report}")
        else:
            logger.info("Audit complete: meta.json is consistent, no changes needed")

        return report

    def get_summary(self) -> dict[str, Any]:
        """Get summary of current progress.

        Returns:
            Dictionary with key progress metrics
        """
        total = self.meta.get("total_records", 0)
        processed = self.meta.get("processed_records", 0)
        failed = self.meta.get("failed_records", 0)
        remaining = total - processed - failed

        return {
            "partition_name": self.meta.get("partition_name"),
            "status": self.meta.get("processing_status"),
            "total_records": total,
            "processed_records": processed,
            "failed_records": failed,
            "remaining_records": remaining,
            "progress_pct": (processed / total * 100) if total > 0 else 0,
            "updated_at": self.meta.get("updated_at"),
        }


def load_progress(output_dir: Path) -> set[str]:
    """Load set of processed UT IDs from meta.json.

    Convenience function for quick loading of processed IDs.

    Args:
        output_dir: Directory containing meta.json

    Returns:
        Set of processed UT IDs (empty set if no progress file exists)
    """
    tracker = ProgressTracker(output_dir)
    return tracker.get_processed_ids()
