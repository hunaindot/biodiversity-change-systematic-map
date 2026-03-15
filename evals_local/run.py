from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Dict

import pandas as pd

from .config import EVAL_OUTPUT_DIR, TASK_CONFIG, DEFAULT_RUN_SUFFIXES, BATCH_OUTPUTS_DIR
from .loaders import join_truth_pred, normalize_truth_pred
from .metrics import label_metrics, record_confusion, binary_metrics
from .normalizers import normalize_geo_labels, normalize_region_labels, to_label_set, normalize_screening_label, normalize_threat_labels


def _ensure_dirs(run_name: str) -> tuple[Path, Path]:
    data_dir = EVAL_OUTPUT_DIR / run_name / "data"
    metrics_dir = EVAL_OUTPUT_DIR / run_name / "metrics"
    data_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    return data_dir, metrics_dir


def _normalizer_for(task: str, col: str):
    if task == "geography":
        if col == "region":
            return normalize_region_labels
        if col == "sub-region":
            return to_label_set
        return normalize_geo_labels
    if task == "screening":
        return lambda v: {normalize_screening_label(v)}
    if task == "threats":
        return normalize_threat_labels
    return to_label_set


def run_task(task: str, run_name: str) -> dict:
    df = join_truth_pred(task, run_name)
    df, col_map = normalize_truth_pred(task, df)

    # Optional per-truth-column include masks to skip rows with placeholder labels
    include_masks: dict[str, pd.Series | None] = {}
    if task == "threats":
        banned = {"no threat_l2 candidates found", "no threat_l1 candidates found", "unclear"}

        # Build l0 mask first
        l0_cols = [c for c in ["threats_l0", "pred_threat_l0"] if c in df.columns]
        if l0_cols:
            l0_mask_parts = [df[c].apply(lambda v: len(to_label_set(v) & banned) == 0) for c in l0_cols]
            l0_mask = pd.concat(l0_mask_parts, axis=1).all(axis=1)
        else:
            l0_mask = None
        include_masks["threats_l0"] = l0_mask

        # Build l1 mask and propagate l0 exclusions: if l0 is banned, exclude the whole record
        l1_cols = [c for c in ["threats_l1", "pred_threat_l1"] if c in df.columns]
        if l1_cols:
            l1_mask_parts = [df[c].apply(lambda v: len(to_label_set(v) & banned) == 0) for c in l1_cols]
            l1_mask = pd.concat(l1_mask_parts, axis=1).all(axis=1)
            if l0_mask is not None:
                l1_mask = l1_mask & l0_mask
        else:
            l1_mask = l0_mask
        include_masks["threats_l1"] = l1_mask

    data_dir, metrics_dir = _ensure_dirs(run_name)
    data_path = data_dir / f"{task}.xlsx"

    # add normalized truth/pred columns to preserve exact label sets
    metric_paths = {}
    if task == "screening":
        truth_col, pred_col = next(iter(col_map.items()))
        truth_col = truth_col
        pred_col = pred_col

        df["true_label"] = df[truth_col]
        df["pred_label"] = df[pred_col]
        if "ut_unique_wos_id_" not in df.columns:
            df["ut_unique_wos_id_"] = df.get("custom_id")

        truth_norm = df[truth_col].apply(normalize_screening_label)
        pred_norm = df[pred_col].apply(normalize_screening_label)
        df[f"{truth_col}_truth_norm"] = truth_norm
        df[f"{truth_col}_pred_norm"] = pred_norm

        has_truth = truth_norm != ""
        pred_pos = pred_norm == "ELIGIBLE"
        true_pos = truth_norm == "ELIGIBLE"
        for col in ["tp", "fp", "fn", "tn"]:
            df[col] = pd.NA
        df.loc[has_truth, "tp"] = (pred_pos & true_pos & has_truth).astype("Int64")
        df.loc[has_truth, "fp"] = (pred_pos & ~true_pos & has_truth).astype("Int64")
        df.loc[has_truth, "fn"] = (~pred_pos & true_pos & has_truth).astype("Int64")
        df.loc[has_truth, "tn"] = (~pred_pos & ~true_pos & has_truth).astype("Int64")

        metrics_df, confusion_df = binary_metrics(
            truth_norm,
            pred_norm,
            labels=["ELIGIBLE", "NOT_ELIGIBLE"],
        )
        metrics_path = metrics_dir / f"{task}_{truth_col}_label_metrics.xlsx"
        confusion_path = metrics_dir / f"{task}_{truth_col}_confusion.xlsx"
        metrics_df.to_excel(metrics_path, index=False, engine='openpyxl')
        confusion_df.to_excel(confusion_path, index=False, engine='openpyxl')
        metric_paths[truth_col] = str(metrics_path)
        metric_paths[f"{truth_col}_confusion"] = str(confusion_path)

        ref_cols = [
            "UT", "title", "abstract", "doi", "custom_id", "model", "created_at", "raw_output",
            "s1_r", "s1_bio", "s2_r", "s2_dir", "s3_r", "s3_drivers", "s4_r", "s4_link",
            "ut_unique_wos_id_", "true_label", "pred_label", "tp", "fp", "fn", "tn",
        ]
        # Ensure all columns exist before reindex
        for col in ref_cols:
            if col not in df.columns:
                df[col] = pd.NA
        df_out = df.reindex(columns=ref_cols)

        # Remove timezone info from datetime columns (Excel doesn't support timezones)
        for col in df_out.columns:
            if pd.api.types.is_datetime64_any_dtype(df_out[col]):
                df_out[col] = df_out[col].dt.tz_localize(None)

        df_out.to_excel(data_path, index=False, engine='openpyxl')
        return {"task": task, "rows": len(df), "data_path": str(data_path), "metric_paths": metric_paths}

    for truth_col, pred_col in col_map.items():
        norm = _normalizer_for(task, truth_col)
        df[f"{truth_col}_truth_norm"] = df[truth_col].apply(lambda v: sorted(norm(v)))
        df[f"{truth_col}_pred_norm"] = df[pred_col].apply(lambda v: sorted(norm(v)))

    # Remove timezone info from datetime columns (Excel doesn't support timezones)
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    df.to_excel(data_path, index=False, engine='openpyxl')

    for truth_col, pred_col in col_map.items():
        norm = _normalizer_for(task, truth_col)
        include_mask = include_masks.get(truth_col)
        df = record_confusion(df, truth_col, pred_col, base=truth_col, normalizer=norm, include_mask=include_mask)
        metrics_df = label_metrics(df, truth_col, pred_col, normalizer=norm, include_mask=include_mask)
        out_path = metrics_dir / f"{task}_{truth_col}_label_metrics.xlsx"
        metrics_df.to_excel(out_path, index=False, engine='openpyxl')
        metric_paths[truth_col] = str(out_path)

    # Remove timezone info from datetime columns before final save (Excel doesn't support timezones)
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    # save updated df with confusion columns
    df.to_excel(data_path, index=False, engine='openpyxl')
    return {"task": task, "rows": len(df), "data_path": str(data_path), "metric_paths": metric_paths}


def _parse_run_name_map(raw: list[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"Invalid mapping '{item}', expected task=run_name")
        task, name = item.split("=", 1)
        out[task.strip()] = name.strip()
    return out


def resolve_run_name(task: str, run_name: str | None, run_name_map: Dict[str, str] | None, base_run_name: str | None, use_suffixes: bool) -> str:
    # explicit map wins
    if run_name_map and task in run_name_map:
        candidate = run_name_map[task]
    elif use_suffixes and base_run_name:
        candidate = f"{base_run_name}{DEFAULT_RUN_SUFFIXES.get(task, '')}"
    else:
        candidate = run_name or base_run_name
    if not candidate:
        raise ValueError("No run name provided.")

    folder = BATCH_OUTPUTS_DIR / candidate
    has_jsonl = any(folder.glob("*.jsonl"))
    # auto-fallback: prefer suffix folder when base is used for non-driver tasks and suffix has outputs
    if base_run_name and not use_suffixes:
        suffix_candidate = f"{base_run_name}{DEFAULT_RUN_SUFFIXES.get(task, '')}"
        suffix_folder = BATCH_OUTPUTS_DIR / suffix_candidate
        suffix_has = any(suffix_folder.glob("*.jsonl"))
        if (not has_jsonl or (candidate == base_run_name and task != "driver")) and suffix_has:
            candidate = suffix_candidate
    return candidate


def run_tasks_with_mapping(
    run_name: str | None,
    tasks: Iterable[str] | None = None,
    run_name_map: Dict[str, str] | None = None,
    base_run_name: str | None = None,
    use_suffixes: bool = False,
) -> list[dict]:
    tasks = list(tasks) if tasks else list(TASK_CONFIG.keys())
    summaries = []
    for task in tasks:
        if task not in TASK_CONFIG:
            raise ValueError(f"Unknown task '{task}'")
        resolved = resolve_run_name(task, run_name, run_name_map, base_run_name, use_suffixes)
        summaries.append(run_task(task, resolved))
    return summaries


def run_tasks(run_name: str, tasks: Iterable[str] | None = None, use_suffixes: bool = False, per_task_run_names: Dict[str, str] | None = None) -> list[dict]:
    """Wrapper that applies the suffix/auto-fallback logic by default."""
    return run_tasks_with_mapping(
        run_name=run_name,
        tasks=tasks,
        run_name_map=per_task_run_names,
        base_run_name=run_name,
        use_suffixes=use_suffixes,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run local eval metrics from labelling outputs.")
    parser.add_argument("run_name", nargs="?", help="Run name (shared) or base run name if --use-default-suffixes.")
    parser.add_argument("--tasks", nargs="*", help="Subset of tasks to run (default: all).")
    parser.add_argument(
        "--per-task-run-names",
        nargs="*",
        help="Explicit mapping like driver=p25 geography=p25-geo threats=p25-threats",
    )
    parser.add_argument(
        "--use-default-suffixes",
        action="store_true",
        help="Treat positional run_name as base and append default suffixes per task (driver='', screening='-screen', geography='-geography', threats='-threats', ecosystems='-ecosystem', study='-study', taxa='-taxa').",
    )
    args = parser.parse_args(argv)

    run_name_map = _parse_run_name_map(args.per_task_run_names) if args.per_task_run_names else None
    summaries = run_tasks_with_mapping(
        run_name=args.run_name,
        tasks=args.tasks,
        run_name_map=run_name_map,
        base_run_name=args.run_name if args.use_default_suffixes else None,
        use_suffixes=args.use_default_suffixes,
    )
    for summary in summaries:
        print(f"{summary['task']}: rows={summary['rows']} data={summary['data_path']}")
        for truth, path in summary["metric_paths"].items():
            print(f"  metrics {truth}: {path}")


if __name__ == "__main__":
    main()
