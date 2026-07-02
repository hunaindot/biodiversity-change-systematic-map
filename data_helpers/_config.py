"""Loads central dataset configuration from checklists/mappings/dataset_config.json."""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = REPO_ROOT / "checklists" / "mappings" / "dataset_config.json"

with _CONFIG_PATH.open(encoding="utf-8") as _f:
    _cfg: dict = json.load(_f)

# Special keys — shared across splitter and samplers
MISSING_KEY: str = _cfg["special_keys"]["missing"]
MULTI_LABEL_KEY: str = _cfg["special_keys"]["multi_label"]
NO_KINGDOM_KEY: str = _cfg["special_keys"]["no_kingdom"]

# Column names — shared across creator scripts
BASE_COLS: list[str] = _cfg["base_columns"]

# Sampling
N_SAMPLE: int = _cfg["sampling"]["n_sample"]

# Train/dev/test split settings
SPLIT_CFG: dict = _cfg["splits"]

# Raw label configs — used by splitter and samplers to rebuild their own formats
LABEL_CONFIGS_RAW: dict = _cfg["label_configs"]

# Dataset-specific config sections
SCREENING_CFG: dict = _cfg["screening_dataset"]
CODING_CFG: dict = _cfg["coding_dataset"]
GBIF_CFG: dict = _cfg["gbif"]


def _require_section(config: dict, name: str, path: str) -> dict:
    value = config.get(name)
    if not isinstance(value, dict):
        raise ValueError(f"Required config section {path}.{name} is missing in {_CONFIG_PATH}.")
    return value


def _require_int(config: dict, name: str, path: str) -> int:
    value = config.get(name)
    if not isinstance(value, int):
        raise ValueError(f"Required integer config key {path}.{name} is missing in {_CONFIG_PATH}.")
    return value


def _require_string(config: dict, name: str, path: str) -> str:
    value = config.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Required string config key {path}.{name} is missing in {_CONFIG_PATH}.")
    return value.strip()


def get_split_ratios() -> dict[str, float]:
    ratios = _require_section(SPLIT_CFG, "ratios", "splits")
    raw = {split: _require_int(ratios, split, "splits.ratios") for split in ("train", "dev", "test")}
    total = sum(raw.values())
    if total <= 0:
        raise ValueError(f"Config key splits.ratios must sum to > 0 in {_CONFIG_PATH}.")
    return {split: raw[split] / total for split in raw}


def get_split_seed() -> int:
    return _require_int(SPLIT_CFG, "seed", "splits")


def get_split_label_path(label: str) -> Path:
    label_paths = _require_section(SPLIT_CFG, "label_paths", "splits")
    raw = _require_string(label_paths, label, "splits.label_paths")
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path
