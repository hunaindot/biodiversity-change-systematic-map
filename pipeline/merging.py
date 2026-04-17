from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .utils import col_examples

_ALL_TASKS = ["driver", "threats", "geography", "ecosystems", "study", "taxa"]


def _pred_cols(df: pd.DataFrame) -> list[str]:
    """Return columns that carry model predictions (named 'pred' or starting with 'pred_')."""
    return [c for c in df.columns if c == "pred" or c.startswith("pred_")]


def check_chain(
    batch_key: str,
    batched_folder: str | Path,
    coded_folder: str | Path,
    tasks: list[str] | None = None,
) -> dict:
    """
    Print + return availability of every coding task for a batch partition.

    Returns a dict keyed by "screening" and each task name, each with:
      exists (bool), path (str), n_records (int if exists), pred_columns (list if task)
    """
    batched_folder = Path(batched_folder)
    coded_folder = Path(coded_folder)
    tasks = tasks or _ALL_TASKS

    chain: dict[str, dict] = {}

    # ── Screening batch ───────────────────────────────────────────────
    batch_csv = batched_folder / batch_key / "screening_eligible.csv"
    s_info: dict = {"path": str(batch_csv), "exists": batch_csv.exists()}
    if batch_csv.exists():
        df = pd.read_csv(batch_csv)
        s_info["n_records"] = len(df)
        s_info["columns"] = list(df.columns)
    chain["screening"] = s_info

    # ── Coding tasks ──────────────────────────────────────────────────
    for task in tasks:
        curated_csv = coded_folder / task / batch_key / "curated" / f"{task}_curated.csv"
        t_info: dict = {"path": str(curated_csv), "exists": curated_csv.exists()}
        if curated_csv.exists():
            df = pd.read_csv(curated_csv)
            t_info["n_records"] = len(df)
            t_info["pred_columns"] = _pred_cols(df)
        chain[task] = t_info

    # ── Print report ──────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"  Chain report — batch: {batch_key}")
    print(f"{'=' * 60}")
    for stage, info in chain.items():
        tick = "✓" if info["exists"] else "✗"
        n = info.get("n_records", "-") if info["exists"] else "-"
        print(f"  {tick}  {stage:<15}  records={n}")
        if info["exists"] and "pred_columns" in info:
            print(f"         pred cols: {info['pred_columns']}")
    print()

    return chain


def build_merged_partition(
    batch_key: str,
    batched_folder: str | Path,
    coded_folder: str | Path,
    merged_folder: str | Path,
    source_data: str | Path | None = None,
    tasks: list[str] | None = None,
) -> None:
    """
    Build the final systematic-map dataset for one screened batch.

    Steps:
      1. Print chain report (which tasks have data).
      2. Load the screened batch CSV as base (all columns kept).
      3. Left-join each available task's curated CSV on custom_id,
         keeping only pred columns (renamed to avoid collisions).
      4. Save merged CSV + Parquet + metadata.json to merged_folder / batch_key /.

    Rename rule:
      - 'pred' (driver) → 'pred_driver'
      - 'pred_*' columns keep their names (already task-specific).
    """
    batched_folder = Path(batched_folder)
    coded_folder = Path(coded_folder)
    merged_folder = Path(merged_folder)
    source_data = Path(source_data) if source_data else None
    tasks = tasks or _ALL_TASKS

    # 1. Chain report
    chain = check_chain(batch_key, batched_folder, coded_folder, tasks)

    if not chain["screening"]["exists"]:
        print(f"✗  No screened batch found for '{batch_key}', cannot merge.")
        return

    # 2. Base
    base_df = pd.read_csv(batched_folder / batch_key / "screening_eligible.csv")

    # Enrich with DOI / Authors from source_data if missing and key present.
    enrich_cols = ["DOI", "Authors"]
    missing_enrich = [c for c in enrich_cols if c not in base_df.columns]
    if source_data and missing_enrich:
        if "UT (Unique WOS ID)" in base_df.columns:
            src_df = pd.read_csv(source_data, usecols=["UT (Unique WOS ID)", *missing_enrich])
            n_before = len(base_df)
            base_df = base_df.merge(src_df, on="UT (Unique WOS ID)", how="left")
            assert len(base_df) == n_before
            print(f"Base: added {missing_enrich} from {source_data}")
        else:
            print("  ⚠  Cannot add DOI/Authors — base lacks 'UT (Unique WOS ID)' column.")

    print(f"Base (screened batch): {len(base_df)} records, {len(base_df.columns)} cols")

    joined_tasks: list[str] = []
    skipped_tasks: list[str] = []

    # 3. Join each task
    for task in tasks:
        info = chain.get(task, {})
        if not info.get("exists"):
            skipped_tasks.append(task)
            continue

        task_df = pd.read_csv(info["path"])
        preds = _pred_cols(task_df)
        if not preds:
            print(f"  ⚠  {task}: no pred columns found, skipping")
            skipped_tasks.append(task)
            continue

        # Rename bare 'pred' to 'pred_{task}' to avoid collision
        rename_map = {c: f"pred_{task}" for c in preds if c == "pred"}
        task_df = task_df[["custom_id"] + preds].copy()
        if rename_map:
            task_df = task_df.rename(columns=rename_map)

        n_before = len(base_df)
        base_df = base_df.merge(task_df, on="custom_id", how="left")
        assert len(base_df) == n_before, (
            f"Row count changed after joining {task} ({n_before} → {len(base_df)})"
        )
        joined_tasks.append(task)
        print(f"  ✓  {task}: added cols {[rename_map.get(c, c) for c in preds]}")

    # 4. Save
    out_dir = merged_folder / batch_key
    out_dir.mkdir(parents=True, exist_ok=True)

    out_csv = out_dir / f"{batch_key}_merged.csv"
    out_parquet = out_dir / f"{batch_key}_merged.parquet"

    base_df.to_csv(out_csv, index=False)
    parquet_path: str | None = None
    try:
        # Parquet for faster downstream reads; falls back to pandas' default engine.
        base_df.to_parquet(out_parquet, index=False)
        parquet_path = str(out_parquet)
    except Exception as exc:  # pragma: no cover - informational
        print(f"   ⚠  Parquet save failed ({exc}); CSV saved OK.")

    (out_dir / "metadata.json").write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": f"Final systematic-map dataset for batch {batch_key}",
        "batch_key": batch_key,
        "n_records": len(base_df),
        "n_columns": len(base_df.columns),
        "tasks_joined": joined_tasks,
        "tasks_missing": skipped_tasks,
        "csv_path": str(out_csv),
        "parquet_path": parquet_path,
        "columns": col_examples(base_df),
    }, indent=2))

    print(f"\n✓  Saved → {out_csv}")
    if parquet_path:
        print(f"   Parquet → {out_parquet}")
    print(f"   {len(base_df)} records  ·  {len(base_df.columns)} columns")
    print(f"   tasks joined : {joined_tasks}")
    if skipped_tasks:
        print(f"   tasks missing: {skipped_tasks}")
