"""Loads central dataset configuration from checklists/mappings/dataset_config.json."""
from __future__ import annotations

import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "checklists" / "mappings" / "dataset_config.json"

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

# L0 source weights
L0_SOURCE_WEIGHTS: dict[str, float] = _cfg["l0_source_weights"]

# Raw label configs — used by splitter and samplers to rebuild their own formats
LABEL_CONFIGS_RAW: dict = _cfg["label_configs"]

# Dataset-specific config sections
SCREENING_CFG: dict = _cfg["screening_dataset"]
CODING_CFG: dict = _cfg["coding_dataset"]
GBIF_CFG: dict = _cfg["gbif"]
