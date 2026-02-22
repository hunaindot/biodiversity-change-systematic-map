"""Command-line interface for WoS embeddings."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import EmbedConfig
from .processor import process_all_partitions, process_partition, process_partitions
from .progress import ProgressTracker
from .storage import load_embeddings, load_metadata


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration.

    Args:
        verbose: If True, set DEBUG level, otherwise INFO
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def cmd_process(args: argparse.Namespace) -> int:
    """Process a single partition or range of partitions.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    config = EmbedConfig.from_env()

    # Override config with CLI arguments
    if args.batch_size:
        config.batch_size = args.batch_size
    if args.no_resume:
        config.resume = False
    if args.overwrite:
        config.overwrite = True

    try:
        if args.partition:
            # Process single partition
            summary = process_partition(
                partition_name=args.partition,
                config=config,
                show_progress=not args.no_progress,
            )
            print(f"\nPartition {args.partition} summary:")
            for key, value in summary.items():
                print(f"  {key}: {value}")
            return 0

        elif args.start and args.end:
            # Process range
            results = process_partitions(
                partition_names=range(args.start, args.end + 1),
                config=config,
                show_progress=not args.no_progress,
            )
            print(f"\nProcessed {len(results)} partitions:")
            for partition_name, summary in results.items():
                status = summary.get("status", "unknown")
                print(f"  Partition {partition_name}: {status}")
            return 0

        else:
            print("Error: Must specify either --partition or both --start and --end", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_process_all(args: argparse.Namespace) -> int:
    """Process all partitions (1-234).

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    config = EmbedConfig.from_env()

    # Override config with CLI arguments
    if args.batch_size:
        config.batch_size = args.batch_size
    if args.no_resume:
        config.resume = False
    if args.overwrite:
        config.overwrite = True

    try:
        results = process_all_partitions(
            config=config,
            start=args.start,
            end=args.end,
            show_progress=not args.no_progress,
        )

        # Print summary
        completed = sum(1 for s in results.values() if s.get("status") == "completed")
        failed = sum(1 for s in results.values() if s.get("status") == "failed")

        print(f"\nProcessed {len(results)} partitions:")
        print(f"  Completed: {completed}")
        print(f"  Failed: {failed}")

        return 0 if failed == 0 else 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_verify(args: argparse.Namespace) -> int:
    """Verify outputs for a partition.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    config = EmbedConfig.from_env()

    try:
        # Load embeddings and metadata
        embeddings_data = load_embeddings(args.partition, config)
        metadata = load_metadata(args.partition, config)

        # Load progress
        output_dir = config.output_base / args.partition
        tracker = ProgressTracker(output_dir)
        summary = tracker.get_summary()

        # Verification checks
        print(f"\nPartition {args.partition} verification:")
        print(f"  Status: {summary['status']}")
        print(f"  Total records: {summary['total_records']}")
        print(f"  Processed records: {summary['processed_records']}")
        print(f"  Failed records: {summary['failed_records']}")
        print(f"\nEmbeddings:")
        print(f"  Shape: {embeddings_data['embeddings'].shape}")
        print(f"  Dtype: {embeddings_data['embeddings'].dtype}")
        print(f"  Record IDs: {len(embeddings_data['record_ids'])}")
        print(f"\nMetadata:")
        print(f"  Rows: {len(metadata)}")
        print(f"  Columns: {list(metadata.columns)}")

        # Check consistency
        num_embeddings = embeddings_data['embeddings'].shape[0]
        num_metadata = len(metadata)
        num_record_ids = len(embeddings_data['record_ids'])

        if num_embeddings == num_metadata == num_record_ids:
            print(f"\n✓ Verification passed: {num_embeddings} embeddings with matching metadata")
            return 0
        else:
            print(f"\n✗ Verification failed: Inconsistent counts")
            print(f"  Embeddings: {num_embeddings}")
            print(f"  Metadata rows: {num_metadata}")
            print(f"  Record IDs: {num_record_ids}")
            return 1

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_stats(args: argparse.Namespace) -> int:
    """Show statistics for a partition.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    config = EmbedConfig.from_env()

    try:
        output_dir = config.output_base / args.partition
        tracker = ProgressTracker(output_dir)
        summary = tracker.get_summary()

        print(f"\nPartition {args.partition} statistics:")
        print(f"  Status: {summary['status']}")
        print(f"  Total records: {summary['total_records']}")
        print(f"  Processed: {summary['processed_records']}")
        print(f"  Failed: {summary['failed_records']}")
        print(f"  Remaining: {summary['remaining_records']}")
        print(f"  Progress: {summary['progress_pct']:.1f}%")
        print(f"  Updated: {summary['updated_at']}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Generate embeddings for WoS research articles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Process command
    process_parser = subparsers.add_parser("process", help="Process partition(s)")
    process_parser.add_argument("--partition", type=str, help="Single partition to process")
    process_parser.add_argument("--start", type=int, help="Start partition number")
    process_parser.add_argument("--end", type=int, help="End partition number")
    process_parser.add_argument("--batch-size", type=int, help="Batch size for embedding")
    process_parser.add_argument("--no-resume", action="store_true", help="Don't resume from progress")
    process_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing embeddings")
    process_parser.add_argument("--no-progress", action="store_true", help="Don't show progress bar")
    process_parser.set_defaults(func=cmd_process)

    # Process-all command
    process_all_parser = subparsers.add_parser("process-all", help="Process all partitions (1-234)")
    process_all_parser.add_argument("--start", type=int, default=1, help="Start partition (default: 1)")
    process_all_parser.add_argument("--end", type=int, default=234, help="End partition (default: 234)")
    process_all_parser.add_argument("--batch-size", type=int, help="Batch size for embedding")
    process_all_parser.add_argument("--no-resume", action="store_true", help="Don't resume from progress")
    process_all_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing embeddings")
    process_all_parser.add_argument("--no-progress", action="store_true", help="Don't show progress bar")
    process_all_parser.set_defaults(func=cmd_process_all)

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify partition outputs")
    verify_parser.add_argument("partition", type=str, help="Partition to verify")
    verify_parser.set_defaults(func=cmd_verify)

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show partition statistics")
    stats_parser.add_argument("partition", type=str, help="Partition to show stats for")
    stats_parser.set_defaults(func=cmd_stats)

    # Parse arguments
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Execute command
    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
