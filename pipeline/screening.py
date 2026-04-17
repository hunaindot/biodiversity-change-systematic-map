from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

from evals_local.loaders import load_screening_outputs
from evals_local.normalizers import normalize_screening_label
from .utils import col_examples

_STAGE_COLS = ["s1_r", "s2_r", "s3_r", "s4_r"]
_WOS_COLS = ["UT (Unique WOS ID)", "Article Title", "Abstract", "Publication Year"]


def _classify_screening(r) -> str:
    """
    PROCESSING_ERROR if any stage col == 2 (missing col sentinel).
    ELIGIBLE iff all stage results non-zero.
    Otherwise NOT_ELIGIBLE.
    """
    if any(r[c] == 2 for c in _STAGE_COLS):
        return "PROCESSING_ERROR"
    return "ELIGIBLE" if all(r[c] != 0 for c in _STAGE_COLS) else "NOT_ELIGIBLE"


def process_screening_partition(
    partition_key: str | int,
    run_name: str,
    screened_folder: str | Path,
    batch_outputs_folder: str | Path,
    source_data: str | Path,
    wos_df: pd.DataFrame | None = None,
) -> None:
    """
    Process one screening partition: raw → curated → serving.

    raw/     : raw JSONL records as CSV
    curated/ : parsed + eligibility prediction
    serving/ : ELIGIBLE + PROCESSING_ERROR records enriched with WOS metadata
    """
    screened_folder = Path(screened_folder)
    batch_outputs_folder = Path(batch_outputs_folder)

    src_dir = batch_outputs_folder / run_name
    if not src_dir.exists():
        print(f"⚠ Missing: {src_dir}, skipping")
        return

    part_dir = screened_folder / str(partition_key)
    raw_dir = part_dir / "raw"
    curated_dir = part_dir / "curated"
    serving_dir = part_dir / "serving"
    for d in [raw_dir, curated_dir, serving_dir]:
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
    raw_df.to_csv(raw_dir / "screening_raw.csv", index=False)
    (raw_dir / "metadata.json").write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": "Raw batch output JSONL records",
        "partition": str(partition_key),
        "run": run_name,
        "num_records": len(raw_df),
        "columns": col_examples(raw_df),
    }, indent=2))

    # ── CURATED ───────────────────────────────────────────────────────
    curated_df = load_screening_outputs(run_name)
    curated_df["_source_run"] = run_name

    # s1_r–s4_r expected to be present; missing col gets sentinel 2 → PROCESSING_ERROR
    for col in _STAGE_COLS:
        if col not in curated_df.columns:
            print(f"  ⚠ p{partition_key}: missing column {col}, filling with 2 (processing error)")
            curated_df[col] = 2

    curated_df["pred_norm"] = curated_df.apply(_classify_screening, axis=1)
    curated_df["pred_screening"] = curated_df["pred_norm"].apply(lambda v: f'["{v}"]')

    curated_df.to_csv(curated_dir / "screening_curated.csv", index=False)
    eligible_count = int((curated_df["pred_norm"] == "ELIGIBLE").sum())
    not_eligible_count = int((curated_df["pred_norm"] == "NOT_ELIGIBLE").sum())
    processing_error_count = int((curated_df["pred_norm"] == "PROCESSING_ERROR").sum())
    (curated_dir / "metadata.json").write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": "Parsed & flattened screening outputs with eligibility prediction",
        "partition": str(partition_key),
        "run": run_name,
        "num_records": len(curated_df),
        "eligible": eligible_count,
        "not_eligible": not_eligible_count,
        "processing_error": processing_error_count,
        "columns": col_examples(curated_df),
        "eligibility_logic": "ELIGIBLE iff all(s1_r,s2_r,s3_r,s4_r != 0); PROCESSING_ERROR if any == 2 (missing col sentinel)",
    }, indent=2))

    # ── SERVING ───────────────────────────────────────────────────────
    if wos_df is None:
        wos_df = pd.read_csv(source_data, usecols=_WOS_COLS)

    serving_df = curated_df[curated_df["pred_norm"].isin(["ELIGIBLE", "PROCESSING_ERROR"])].copy()
    n_before = len(serving_df)

    serving_df = serving_df.merge(wos_df, left_on="custom_id", right_on="UT (Unique WOS ID)", how="left")
    assert len(serving_df) == n_before, (
        f"p{partition_key}: row count changed after join ({n_before} → {len(serving_df)})"
    )
    unmatched = serving_df["Article Title"].isna().sum()
    if unmatched:
        print(f"  ⚠ p{partition_key}: {unmatched} records did not match source_data")

    serving_df.to_csv(serving_dir / "screening_eligible.csv", index=False)
    (serving_dir / "metadata.json").write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": "ELIGIBLE and PROCESSING_ERROR records enriched with WOS metadata",
        "partition": str(partition_key),
        "run": run_name,
        "num_records": len(serving_df),
        "filter": "pred_norm in ['ELIGIBLE', 'PROCESSING_ERROR']",
        "enriched_from": str(source_data),
        "enriched_fields": ["Article Title", "Abstract", "Publication Year"],
        "columns": col_examples(serving_df),
    }, indent=2))

    pct = eligible_count / len(curated_df) * 100 if len(curated_df) else 0
    print(
        f"p{partition_key}: raw={len(raw_df)}  curated={len(curated_df)}"
        f"  eligible={eligible_count} ({pct:.1f}%)  processing_error={processing_error_count}"
    )


def create_screened_batch(
    partition_keys: Iterable[str | int],
    batch_key: str,
    screened_folder: str | Path,
    batched_folder: str | Path,
    limit: int = 10000,
) -> None:
    """
    Concatenate serving outputs from multiple partitions into one batch file.

    partition_keys : e.g. range(1, 8) for full mode, or ["sample"] for sample mode
    batch_key      : folder name for the output batch, e.g. "1-7" or "sample"
    """
    screened_folder = Path(screened_folder)
    batched_folder = Path(batched_folder)

    frames = []
    for pk in partition_keys:
        serving_csv = screened_folder / str(pk) / "serving" / "screening_eligible.csv"
        if not serving_csv.exists():
            raise FileNotFoundError(f"Missing serving file for partition {pk}: {serving_csv}")
        frames.append(pd.read_csv(serving_csv))

    batch_df = pd.concat(frames, ignore_index=True)
    if len(batch_df) > limit:
        raise ValueError(
            f"Batch '{batch_key}' has {len(batch_df)} records, exceeds limit of {limit}"
        )

    out_dir = batched_folder / str(batch_key)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "screening_eligible.csv"
    batch_df.to_csv(out_path, index=False)
    (out_dir / "metadata.json").write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": f"Batched serving (eligible) records for batch '{batch_key}'",
        "partitions": [str(pk) for pk in partition_keys],
        "num_records": len(batch_df),
        "limit": limit,
        "columns": col_examples(batch_df),
    }, indent=2))
    print(f"Batch '{batch_key}': {len(batch_df)} records → {out_path}")
