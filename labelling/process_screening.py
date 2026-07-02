"""
Post-screening processor: extract eligible records from one or more screening runs,
deduplicate, partition into batches, and write Excel files + partition_metadata.json.

Usage (from repo root):
    python labelling/process_screening.py <run_name1> [run_name2 ...] \
        --output-dir <folder_name> [--batch-size 400000]

Output layout:
    data/<output-dir>/
        partition_metadata.json
        1/wos_01_<max_year>-<min_year>.xlsx
        2/wos_02_<max_year>-<min_year>.xlsx
        ...
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_SCRIPT_DIR))

from evals_local.loaders import load_screening_predictions
from src.config import DATASETS_DIR

_CORE_FIELDS = ["UT", "title", "authors", "abstract", "source", "publication_year", "wos_categories", "doi"]
_STAGE_NUMERIC_COLS = ["s1_r", "s2_r", "s3_r", "s4_r"]
_STAGE_LABEL_COLS = ["s1_bio", "s2_dir", "s3_drivers", "s4_link"]


def _load_dataset(run_name: str) -> dict[str, dict]:
    """Return {UT: document} from the dataset JSON saved by orchestrator."""
    path = DATASETS_DIR / f"{run_name}-dataset.json"
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found for run '{run_name}': {path}")
    return json.loads(path.read_text(encoding="utf-8"))["documents"]


def _load_run(run_name: str) -> tuple[pd.DataFrame, dict]:
    """
    Load predictions and dataset for one run.

    Returns:
        eligible_df  — DataFrame with _CORE_FIELDS + stage numeric/label cols for eligible records.
        run_summary  — counts for metadata.

    Raises AssertionError if prediction UTs and dataset UTs don't match exactly.
    """
    pred_df = load_screening_predictions(run_name)
    docs = _load_dataset(run_name)

    pred_uts = set(pred_df["UT"].astype(str))
    dataset_uts = set(docs.keys())
    missing_in_dataset = pred_uts - dataset_uts
    missing_in_preds = dataset_uts - pred_uts

    if missing_in_dataset or missing_in_preds:
        parts = []
        if missing_in_dataset:
            parts.append(f"{len(missing_in_dataset)} prediction UTs absent from dataset")
        if missing_in_preds:
            parts.append(f"{len(missing_in_preds)} dataset UTs absent from predictions")
        raise AssertionError(
            f"[{run_name}] Join mismatch — {'; '.join(parts)}. "
            "Ensure run_name matches the dataset that was used for this run."
        )

    # Stage-failure breakdown (first failing stage per record)
    s1, s2, s3, s4 = (pred_df[c] for c in ["s1_r", "s2_r", "s3_r", "s4_r"])
    no_output = int(pred_df["custom_id"].isna().sum())
    stage_failures = {
        "stage_1": int((s1 == 0).sum()),
        "stage_2": int(((s1 == 1) & (s2 == 0)).sum()),
        "stage_3": int(((s1 == 1) & (s2 == 1) & (s3 == 0)).sum()),
        "stage_4": int(((s1 == 1) & (s2 == 1) & (s3 == 1) & (s4 == 0)).sum()),
    }

    eligible_mask = pred_df["pred"] == '["ELIGIBLE"]'
    eligible_pred = pred_df[eligible_mask].copy()
    eligible_pred["UT"] = eligible_pred["UT"].astype(str)

    # Core doc fields from dataset
    eligible_docs = [
        {field: docs[ut].get(field, "") for field in _CORE_FIELDS}
        for ut in eligible_pred["UT"]
    ]
    core_df = pd.DataFrame(eligible_docs) if eligible_docs else pd.DataFrame(columns=_CORE_FIELDS)

    # Stage cols to carry for auditability
    stage_label_cols = [c for c in _STAGE_LABEL_COLS if c in pred_df.columns]
    stage_df = eligible_pred[_STAGE_NUMERIC_COLS + stage_label_cols].reset_index(drop=True)
    eligible_df = pd.concat([core_df, stage_df], axis=1)

    run_summary = {
        "total": len(pred_df),
        "eligible": int(eligible_mask.sum()),
        "not_eligible": int((~eligible_mask).sum()),
        "no_output": no_output,
        "stage_failures": stage_failures,
    }
    return eligible_df, run_summary


def _list_to_str(val) -> str:
    if isinstance(val, list):
        return "; ".join(str(v) for v in val)
    return str(val) if val is not None else ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract eligible records from screening runs and write partitioned Excel files."
    )
    parser.add_argument(
        "run_names",
        nargs="+",
        help="One or more screening run names (e.g. train-screening-l0-v1).",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output folder name under data/ (e.g. 'screening_eligible').",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=400_000,
        help="Maximum records per output partition (default: 400000).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    output_base = _REPO_ROOT / "data" / args.output_dir

    per_run_summaries: dict[str, dict] = {}
    all_frames: list[pd.DataFrame] = []
    seen_uts: set[str] = set()

    for run_name in args.run_names:
        print(f"Loading run '{run_name}' ...")
        eligible_df, summary = _load_run(run_name)

        run_uts = set(eligible_df["UT"].astype(str))
        overlap = run_uts & seen_uts
        if overlap:
            raise AssertionError(
                f"Duplicate UTs across runs: {len(overlap)} record(s) from '{run_name}' "
                f"already seen in a previous run. Sample: {sorted(overlap)[:5]}"
            )

        seen_uts |= run_uts
        all_frames.append(eligible_df)
        per_run_summaries[run_name] = summary

        print(
            f"  total={summary['total']:,}  eligible={summary['eligible']:,}  "
            f"not_eligible={summary['not_eligible']:,}  no_output={summary['no_output']:,}"
        )

    if not all_frames or all(len(f) == 0 for f in all_frames):
        print("No eligible records found. Nothing to write.")
        return

    combined = pd.concat(all_frames, ignore_index=True)
    combined["UT"] = combined["UT"].astype(str)

    # Final sanity check — assert no duplicates survived (should be caught above, but verify)
    dupes = combined["UT"][combined["UT"].duplicated(keep=False)].unique().tolist()
    if dupes:
        raise AssertionError(
            f"Duplicate UTs in combined output ({len(dupes)} unique IDs). "
            f"Sample: {dupes[:5]}"
        )

    total_eligible = len(combined)
    n_partitions = -(-total_eligible // args.batch_size)  # ceiling division
    print(f"\nTotal eligible records: {total_eligible:,}")
    print(f"Writing {n_partitions} partition(s) of up to {args.batch_size:,} records ...")

    partition_details: list[dict] = []

    for i in range(n_partitions):
        chunk = combined.iloc[i * args.batch_size : (i + 1) * args.batch_size].copy()
        part_num = i + 1

        years = pd.to_numeric(chunk["publication_year"], errors="coerce").dropna()
        max_year = int(years.max()) if len(years) else 0
        min_year = int(years.min()) if len(years) else 0

        filename = f"wos_{part_num:02d}_{max_year}-{min_year}.xlsx"
        part_dir = output_base / str(part_num)
        part_dir.mkdir(parents=True, exist_ok=True)
        dest = part_dir / filename

        excel_df = chunk.copy()
        excel_df["authors"] = excel_df["authors"].apply(_list_to_str)
        excel_df["wos_categories"] = excel_df["wos_categories"].apply(_list_to_str)
        excel_df["eligibility"] = "ELIGIBLE"

        # Column order: core fields → eligibility → stage numerics → stage labels
        stage_label_cols = [c for c in _STAGE_LABEL_COLS if c in excel_df.columns]
        col_order = _CORE_FIELDS + ["eligibility"] + _STAGE_NUMERIC_COLS + stage_label_cols
        excel_df = excel_df[[c for c in col_order if c in excel_df.columns]]

        excel_df.to_excel(dest, index=False)
        print(f"  Partition {part_num}: {len(chunk):,} records → {dest.relative_to(_REPO_ROOT)}")

        partition_details.append({
            "partition": part_num,
            "file": str(dest.relative_to(_REPO_ROOT)),
            "records": len(chunk),
            "year_range": {"min": min_year, "max": max_year},
        })

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(output_base.relative_to(_REPO_ROOT)),
        "batch_size": args.batch_size,
        "run_names": args.run_names,
        "per_run": per_run_summaries,
        "totals": {
            "input_records": sum(s["total"] for s in per_run_summaries.values()),
            "eligible": total_eligible,
            "not_eligible": sum(s["not_eligible"] for s in per_run_summaries.values()),
            "no_output": sum(s["no_output"] for s in per_run_summaries.values()),
        },
        "partitions": partition_details,
    }

    output_base.mkdir(parents=True, exist_ok=True)
    meta_path = output_base / "partition_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
    print(f"\nMetadata written to {meta_path.relative_to(_REPO_ROOT)}")


if __name__ == "__main__":
    main()
