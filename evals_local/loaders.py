from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from json_repair import repair_json  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    repair_json = None

from .config import BATCH_OUTPUTS_DIR, BATCHES_DIR, TASK_CONFIG
from .normalizers import normalize_geo_labels, to_label_list


def load_jsonl_folder(folder: Path) -> pd.DataFrame:
    paths = sorted(Path(folder).glob("*.jsonl"))
    if not paths:
        raise FileNotFoundError(f"No .jsonl files in {folder}")
    frames = [pd.read_json(p, lines=True) for p in paths]
    return pd.concat(frames, ignore_index=True)


def _output_text_from_record(record: dict) -> str | None:
    if not isinstance(record, dict):
        return None
    body = record.get("response", {}).get("body") if isinstance(record.get("response"), dict) else record.get("body")
    if not isinstance(body, dict):
        return None
    for item in body.get("output", []) or []:
        if item.get("type") == "message":
            for part in item.get("content", []) or []:
                if part.get("type") == "output_text":
                    return part.get("text")
    return None


def _safe_json(text: str | None) -> Any:
    if not isinstance(text, str) or not text.strip():
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


# --- Screening-specific helpers (mirrors screening-reader.ipynb) ---
ALLOWED_REASON_KEYS = {"stressor_spans", "use_type", "evidence_span", "biodiversity_span", "link_span"}


def parse_json_text(text: str):
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    if repair_json:
        try:
            return repair_json(text, return_objects=True)
        except Exception:
            pass

    cleaned = re.sub(r",\\s*([}\\]])", r"\\1", text.replace("\\r", "").replace("\\n", " "))
    try:
        return json.loads(cleaned)
    except Exception:
        return None


def extract_output_payload(output_list):
    # Return the first JSON payload found in the model output content, else None.
    for item in output_list or []:
        content_blocks = item.get("content") or []
        for block in content_blocks:
            text = block.get("text") if isinstance(block, dict) else None
            if not text:
                continue
            parsed = parse_json_text(text)
            if parsed is not None:
                return parsed
    return None


def flatten_steps(parsed: dict) -> dict:
    flat = {}
    if not isinstance(parsed, dict):
        return flat
    for step_key, step_val in parsed.items():
        if not isinstance(step_val, dict):
            continue
        flat[f"{step_key}_label"] = step_val.get("label")
        reason = step_val.get("reason")
        flat[f"{step_key}_reason"] = reason
        if isinstance(reason, dict):
            for k, v in reason.items():
                if ALLOWED_REASON_KEYS and k not in ALLOWED_REASON_KEYS:
                    continue
                flat[f"{step_key}_reason_{k}"] = v
    return flat


def parse_output_record(rec: dict) -> dict:
    body = (rec.get("response") or {}).get("body") or {}
    model = body.get("model")
    created_at = body.get("created_at")
    parsed = extract_output_payload(body.get("output"))
    flat = flatten_steps(parsed)
    return {
        "custom_id": rec.get("custom_id"),
        "model": model,
        "created_at": created_at,
        "raw_output": parsed,
        **flat,
    }


def load_screening_outputs(run: str) -> pd.DataFrame:
    out_dir = BATCH_OUTPUTS_DIR / run
    if not out_dir.exists():
        return pd.DataFrame()
    files = sorted(out_dir.glob("*.jsonl"))
    rows = []
    for fp in files:
        with open(fp) as f:
            for line in f:
                rec = json.loads(line)
                rows.append(parse_output_record(rec))
    df = pd.DataFrame(rows)
    if not df.empty and "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], unit="s", utc=True, errors="coerce")
    return df


def load_screening_batch_records(run: str, keep_cols=("UT", "title", "abstract", "doi")) -> pd.DataFrame:
    data_dir = BATCHES_DIR / run / "data"
    frames = []
    if not data_dir.exists():
        return pd.DataFrame(columns=keep_cols)
    for fp in sorted(data_dir.glob("*.jsonl")):
        frames.append(pd.read_json(fp, lines=True))
    if not frames:
        return pd.DataFrame(columns=keep_cols)
    df = pd.concat(frames, ignore_index=True)
    cols = [c for c in keep_cols if c in df.columns]
    return df[cols]


def load_screening_predictions(run: str) -> pd.DataFrame:
    batch_df = load_screening_batch_records(run)
    outputs_df = load_screening_outputs(run)
    joined = batch_df.merge(outputs_df, left_on="UT", right_on="custom_id", how="left")

    for col in ["step_0_label", "step_1_label", "step_2_label", "step_3_label"]:
        if col in joined.columns:
            joined[col] = pd.to_numeric(joined[col], errors="coerce").fillna(0).astype(int)
        else:
            joined[col] = 0

    joined["label_1_3"] = joined[["step_1_label", "step_2_label", "step_3_label"]].sum(axis=1)
    joined["pred_screening"] = joined.apply(
        lambda r: '[\"ELIGIBLE\"]' if (r["step_0_label"] == 0 and r["label_1_3"] == 3) else '[\"NOT_ELIGIBLE\"]',
        axis=1,
    )
    joined["pred"] = joined["pred_screening"]
    return joined


def load_screening_labels(folder: Path) -> pd.DataFrame:
    frames = [pd.read_csv(fp) for fp in sorted(folder.glob("*.csv"))]
    if not frames:
        return pd.DataFrame(columns=["custom_id", "eligibility"])
    df = pd.concat(frames, ignore_index=True)
    label_col = None
    if "eligbility" in df.columns:
        label_col = "eligbility"
    elif "eligibility" in df.columns:
        label_col = "eligibility"
    if label_col is None:
        return pd.DataFrame(columns=["custom_id", "eligibility"])

    # Handle both column name formats
    id_col = None
    if "UT (Unique WOS ID)" in df.columns:
        id_col = "UT (Unique WOS ID)"
    elif "ut_unique_wos_id_" in df.columns:
        id_col = "ut_unique_wos_id_"

    keep_cols = {id_col, "article_title", "abstract", "doi", "source", label_col} if id_col else {"article_title", "abstract", "doi", "source", label_col}
    df = df[[c for c in keep_cols if c in df.columns]]

    rename_map = {
        label_col: "eligibility",
        "article_title": "Article Title",
        "abstract": "Abstract",
        "doi": "DOI",
    }
    if id_col:
        rename_map[id_col] = "custom_id"

    df = df.rename(columns=rename_map)
    return df.drop_duplicates()


def load_predictions(task: str, run_name: str) -> pd.DataFrame:
    cfg = TASK_CONFIG[task]
    if cfg["task_type"] == "screening":
        return load_screening_predictions(run_name)

    folder = BATCH_OUTPUTS_DIR / run_name
    df = load_jsonl_folder(folder)

    # Ensure expected columns exist to avoid KeyErrors when runs are missing fields
    if "results_payload" not in df.columns:
        df["results_payload"] = None

    def _results_field(d, key):
        if isinstance(d, dict):
            node = d.get(key)
            if isinstance(node, dict):
                return node.get("results")
        return None

    def _first_result_field(d, key):
        if not isinstance(d, dict):
            return None
        results = d.get("results")
        if not isinstance(results, list):
            return None
        for item in results:
            if isinstance(item, dict):
                return item.get(key)
        return None

    if cfg["task_type"] in {"simple", "binary"}:
        df["output_text"] = df["response"].apply(_output_text_from_record)
        df["pred"] = df["output_text"].apply(lambda t: (_safe_json(t) or {}).get("results") if t else None)
    elif cfg["task_type"] == "threats":
        df["pred_threat_l0"] = df["results_payload"].apply(lambda d: _results_field(d, "threat_l0"))
        df["pred_threat_l1"] = df["results_payload"].apply(lambda d: _results_field(d, "threat_l1"))
        df["pred_threat_l2"] = df["results_payload"].apply(lambda d: _results_field(d, "threat_l2"))
    elif cfg["task_type"] == "geo":
        df["output_text"] = df["response"].apply(_output_text_from_record)
        df["payload"] = df["output_text"].apply(_safe_json)
        df["pred_regions"] = df["payload"].apply(lambda d: d.get("regions") if isinstance(d, dict) else None)
        df["pred_subregions"] = df["payload"].apply(lambda d: d.get("subregions") or d.get("sub_regions") if isinstance(d, dict) else None)
        df["pred_countries"] = df["payload"].apply(lambda d: d.get("countries_iso3") if isinstance(d, dict) else None)
    elif cfg["task_type"] == "ecosystems":
        df["pred_realm"] = df["results_payload"].apply(lambda d: _results_field(d, "realms"))
        df["pred_biome"] = df["results_payload"].apply(lambda d: _results_field(d, "biomes"))
        df["pred_efg"] = df["results_payload"].apply(lambda d: _results_field(d, "efgs"))
    elif cfg["task_type"] == "study":
        df["output_text"] = df["response"].apply(_output_text_from_record)
        df["payload"] = df["output_text"].apply(_safe_json)
        df["pred_study_design"] = df["payload"].apply(lambda d: _first_result_field(d, "study_design"))
    elif cfg["task_type"] == "taxa":
        df["output_text"] = df["response"].apply(_output_text_from_record)
        df["payload"] = df["output_text"].apply(_safe_json)
        df["pred_taxa"] = df["payload"].apply(lambda d: d.get("results") if isinstance(d, dict) else None)
        df["pred_taxa_names"] = df["pred_taxa"].apply(
            lambda items: [item.get("name") for item in items if isinstance(item, dict) and item.get("name")] if isinstance(items, list) else None
        )
    return df


def load_labels(task: str) -> pd.DataFrame:
    cfg = TASK_CONFIG[task]
    path: Path = cfg["label_path"]
    if cfg["task_type"] == "screening":
        return load_screening_labels(path)
    # Handle both CSV and Excel files
    if path.suffix == ".csv":
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)
    df = df.rename(columns={"UT (Unique WOS ID)": "custom_id"})
    return df


def join_truth_pred(task: str, run_name: str) -> pd.DataFrame:
    preds = load_predictions(task, run_name)
    labels = load_labels(task)

    # Restrict labels to the records we actually have predictions for
    if "custom_id" in preds.columns:
        pred_ids = set(preds["custom_id"].dropna().astype(str))
        labels = labels[labels["custom_id"].astype(str).isin(pred_ids)]

    # Align column names to a common scheme.
    join_how = "left"  # keep prediction rows; drop extra labels with no output
    keep_common = ["Article Title", "Abstract", "DOI", "source", "custom_id"]
    label_cols = [c for c in keep_common if c in labels.columns]
    if task == "driver":
        label_cols += ["driver"]
        merged = preds.merge(labels[label_cols], on="custom_id", how=join_how)
        merged = merged.rename(columns={"pred": "pred_driver"})
    elif task == "threats":
        label_cols += ["threats_l0", "threats_l1"]
        merged = preds.merge(labels[label_cols], on="custom_id", how=join_how)
    elif task == "geography":
        label_cols += ["region", "sub-region", "country"]
        merged = preds.merge(labels[label_cols], on="custom_id", how=join_how)
    elif task == "screening":
        label_cols += ["eligibility"]
        merged = preds.merge(labels[label_cols], on="custom_id", how=join_how)
        if "pred" in merged.columns:
            merged = merged.rename(columns={"pred": "pred_eligibility"})
        elif "pred_screening" in merged.columns:
            merged = merged.rename(columns={"pred_screening": "pred_eligibility"})
    elif task == "ecosystems":
        label_cols += ["realm", "biome"]
        merged = preds.merge(labels[label_cols], on="custom_id", how=join_how)
    elif task == "study":
        label_cols += ["study_design"]
        merged = preds.merge(labels[label_cols], on="custom_id", how=join_how)
    elif task == "taxa":
        label_cols += ["kingdom", "phylum", "class", "order", "specie"]
        merged = preds.merge(labels[label_cols], on="custom_id", how=join_how)
    else:
        merged = preds
    return merged


def normalize_truth_pred(task: str, df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Return df with prediction columns ready plus map truth->pred column names for metrics."""
    col_map: dict[str, str] = {}
    if task == "driver":
        col_map = {"driver": "pred_driver"}
    elif task == "threats":
        col_map = {"threats_l0": "pred_threat_l0", "threats_l1": "pred_threat_l1"}
    elif task == "geography":
        df["pred_countries"] = df["pred_countries"].apply(lambda v: [c.upper() for c in v] if isinstance(v, list) else v)
        col_map = {"region": "pred_regions", "sub-region": "pred_subregions", "country": "pred_countries"}
    elif task == "screening":
        col_map = {"eligibility": "pred_eligibility"}
    elif task == "ecosystems":
        col_map = {"realm": "pred_realm", "biome": "pred_biome"}
    elif task == "study":
        col_map = {"study_design": "pred_study_design"}
    elif task == "taxa":
        # Compare species-level only for now.
        df = df.rename(columns={"pred_taxa_names": "pred_taxa_names"})
        col_map = {"specie": "pred_taxa_names"}
    return df, col_map
