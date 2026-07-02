from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_CONFIG_PATH = ROOT / "checklists" / "mappings" / "repo_config.json"


# ── Env bootstrap ─────────────────────────────────────────────────────────────

def _bootstrap_env() -> None:
    """Load .env into os.environ at import time. Uses setdefault — shell vars take precedence."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ.setdefault(key, value)


_bootstrap_env()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_path(env_var: str) -> Path:
    """Read a required path from an env var; relative paths resolved from ROOT."""
    raw = os.environ.get(env_var, "").strip()
    if not raw:
        raise ValueError(f"Required env var {env_var!r} is not set. Add it to .env.")
    p = Path(raw)
    return p if p.is_absolute() else ROOT / p


def _load_repo_config() -> dict:
    """Load repo-level JSON config used for non-secret repository paths."""
    if not REPO_CONFIG_PATH.exists():
        raise ValueError(f"Required config file is missing: {REPO_CONFIG_PATH}")
    try:
        with REPO_CONFIG_PATH.open(encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in config file {REPO_CONFIG_PATH}: {exc}") from exc
    if not isinstance(config, dict):
        raise ValueError(f"Config file {REPO_CONFIG_PATH} must contain a JSON object.")
    return config


REPO_CONFIG = _load_repo_config()


def _resolve_repo_config_path(section: str, key: str) -> Path:
    """Read a required path from repo_config.json; relative paths resolved from ROOT."""
    section_config = REPO_CONFIG.get(section)
    if not isinstance(section_config, dict):
        raise ValueError(f"Required config section {section!r} is missing in {REPO_CONFIG_PATH}.")
    raw = section_config.get(key)
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"Required config key {section}.{key} is missing in {REPO_CONFIG_PATH}.")
    p = Path(raw.strip())
    return p if p.is_absolute() else ROOT / p



# ── Paths ─────────────────────────────────────────────────────────────────────

MAPPINGS_DIR      = _resolve_path("ORCHESTRATOR_MAPPINGS_DIR")
BATCH_OUTPUTS_DIR = _resolve_path("ORCHESTRATOR_BATCH_OUTPUTS_DIR")
BATCHES_DIR       = _resolve_path("ORCHESTRATOR_BATCHES_DIR")
LABELS_DIR        = _resolve_repo_config_path("evals", "labels_dir")
EVAL_OUTPUT_DIR   = _resolve_repo_config_path("evals", "output_dir")
GBIF_CACHE_PATH   = _resolve_repo_config_path("evals", "gbif_cache_path")


# ── Task registry ─────────────────────────────────────────────────────────────

# Default run-name suffixes per task when using a shared base name.
DEFAULT_RUN_SUFFIXES = {
    "driver":           "",
    "screening":        "-screen",
    "geography":        "-geography",
    "threats":          "-threats",
    "threats_l0":       "-threats",
    "threats_l1":       "-threats",
    "threats_l2":       "-threats",
    "ecosystems":       "-ecosystem",
    "ecosystems_realm": "-ecosystem",
    "ecosystems_biome": "-ecosystem",
    "ecosystems_efg":   "-ecosystem",
    "study":            "-study",
    "taxa":             "-taxa",
}

TASK_CONFIG: dict[str, dict] = {
    "driver": {
        "label_path": LABELS_DIR / "l1" / "L1) driver set.csv",
        "truth_cols": {"driver": "driver"},
        "task_type": "simple",
    },
    "screening": {
        "label_path": LABELS_DIR / "l0",
        "truth_cols": {"eligibility": "eligibility"},
        "task_type": "screening",
    },
    "threats": {
        "label_path": LABELS_DIR / "l2" / "L2) threats set.csv",
        "truth_cols": {"threats_l0": "threats_l0", "threats_l1": "threats_l1"},
        "task_type": "threats",
    },
    "threats_l0": {
        "label_path": LABELS_DIR / "l2" / "L2) threats set.csv",
        "truth_cols": {"threats_l0": "threats_l0"},
        "task_type": "threats_l0",
    },
    "threats_l1": {
        "label_path": LABELS_DIR / "l2" / "L2) threats set.csv",
        "truth_cols": {"threats_l1": "threats_l1"},
        "task_type": "threats_l1",
    },
    "threats_l2": {
        "label_path": LABELS_DIR / "l2" / "L2) threats set.csv",
        "truth_cols": {},
        "task_type": "threats_l2",
    },
    "geography": {
        "label_path": LABELS_DIR / "l3" / "L3) geography set.csv",
        "truth_cols": {"region": "region", "sub-region": "sub-region", "country": "country"},
        "task_type": "geo",
    },
    "ecosystems": {
        "label_path": LABELS_DIR / "l4" / "L4) ecosystem set.csv",
        "truth_cols": {"realm": "realm", "biome": "biome"},
        "task_type": "ecosystems",
    },
    "ecosystems_realm": {
        "label_path": LABELS_DIR / "l4" / "L4) ecosystem set.csv",
        "truth_cols": {"realm": "realm"},
        "task_type": "ecosystems_realm",
    },
    "ecosystems_biome": {
        "label_path": LABELS_DIR / "l4" / "L4) ecosystem set.csv",
        "truth_cols": {"biome": "biome"},
        "task_type": "ecosystems_biome",
    },
    "ecosystems_efg": {
        "label_path": LABELS_DIR / "l4" / "L4) ecosystem set.csv",
        "truth_cols": {},
        "task_type": "ecosystems_efg",
    },
    "study": {
        "label_path": LABELS_DIR / "l5" / "L5) study set.csv",
        "truth_cols": {"study_design": "study_design"},
        "task_type": "study",
    },
    "taxa": {
        "label_path": LABELS_DIR / "l6" / "L6) taxa set.csv",
        "truth_cols": {
            "kingdom": "kingdom",
            "phylum":  "phylum",
            "class":   "class",
            "order":   "order",
            "genus":   "genus",
            "specie":  "specie",
        },
        "task_type": "taxa",
    },
}
