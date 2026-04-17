from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from evals_local.loaders import load_predictions
from .utils import col_examples

_WOS_COLS = ["UT (Unique WOS ID)", "Article Title", "Abstract", "Publication Year"]


def process_coding_partition(
    task_name: str,
    partition_key: str,
    run_name: str,
    coded_folder: str | Path,
    batch_outputs_folder: str | Path,
    source_data: str | Path,
    wos_df: pd.DataFrame | None = None,
) -> None:
    """
    Process one coding partition for any task (driver, threats, geography, …):
    raw → curated (enriched with WOS metadata).

    Works for all task types registered in evals_local.config.TASK_CONFIG.
    """
    coded_folder = Path(coded_folder)
    batch_outputs_folder = Path(batch_outputs_folder)

    src_dir = batch_outputs_folder / run_name
    if not src_dir.exists():
        print(f"⚠ Missing: {src_dir}, skipping")
        return

    part_dir = coded_folder / task_name / str(partition_key)
    raw_dir = part_dir / "raw"
    curated_dir = part_dir / "curated"
    for d in [raw_dir, curated_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # ── RAW ──────────────────────────────────────────────────────────
    raw_rows = []
    for fp in sorted(src_dir.glob("*.jsonl")):
        with open(fp) as f:
            for line in f:
                rec = json.loads(line)
                rec["_source_run"] = run_name
                rec["_source_file"] = fp.name
                raw_rows.append(rec)

    raw_df = pd.DataFrame(raw_rows)
    raw_df.to_csv(raw_dir / f"{task_name}_raw.csv", index=False)
    (raw_dir / "metadata.json").write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": f"Raw batch output JSONL records for {task_name}",
        "partitions": str(partition_key),
        "run": run_name,
        "task": task_name,
        "num_records": len(raw_df),
        "columns": col_examples(raw_df),
    }, indent=2))

    # ── CURATED ───────────────────────────────────────────────────────
    if wos_df is None:
        wos_df = pd.read_csv(source_data, usecols=_WOS_COLS)

    curated_df = load_predictions(task_name, run_name)
    n_before = len(curated_df)

    curated_df = curated_df.merge(
        wos_df,
        left_on="custom_id",
        right_on="UT (Unique WOS ID)",
        how="left",
    ).drop(columns=["UT (Unique WOS ID)"])

    assert len(curated_df) == n_before, (
        f"{partition_key}: row count changed after join ({n_before} → {len(curated_df)})"
    )
    unmatched = curated_df["Article Title"].isna().sum()
    if unmatched:
        print(f"  ⚠ {partition_key}: {unmatched} records did not match source_data")

    curated_df.to_csv(curated_dir / f"{task_name}_curated.csv", index=False)
    (curated_dir / "metadata.json").write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": f"Parsed {task_name} predictions enriched with WOS metadata",
        "partitions": str(partition_key),
        "run": run_name,
        "task": task_name,
        "num_records": len(curated_df),
        "enriched_from": str(source_data),
        "enriched_fields": ["Article Title", "Abstract", "Publication Year"],
        "columns": col_examples(curated_df),
    }, indent=2))

    print(f"{task_name} {partition_key}: raw={len(raw_df)}  curated={len(curated_df)} → {part_dir}")
