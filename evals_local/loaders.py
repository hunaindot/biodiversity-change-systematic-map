from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .config import BATCH_OUTPUTS_DIR, TASK_CONFIG
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


def load_predictions(task: str, run_name: str) -> pd.DataFrame:
    cfg = TASK_CONFIG[task]
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

    if cfg["task_type"] == "simple":
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
    elif task == "ecosystems":
        col_map = {"realm": "pred_realm", "biome": "pred_biome"}
    elif task == "study":
        col_map = {"study_design": "pred_study_design"}
    elif task == "taxa":
        # Compare species-level only for now.
        df = df.rename(columns={"pred_taxa_names": "pred_taxa_names"})
        col_map = {"specie": "pred_taxa_names"}
    return df, col_map
