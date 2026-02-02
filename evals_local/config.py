from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS_DIR = ROOT / "data" / "labels"
BATCH_OUTPUTS_DIR = ROOT / "labelling" / "artifacts" / "batch_outputs"
EVAL_OUTPUT_DIR = LABELS_DIR / "eval"
MAPPINGS_DIR = ROOT / "mappings"

# Default suffixes when using a base run name per task
DEFAULT_RUN_SUFFIXES = {
    "driver": "",
    "geography": "-geography",
    "threats": "-threats",
    "ecosystems": "-ecosystem",
    "study": "-study",
    "taxa": "-taxa",
}

# Task registry: file locations and truth columns to compare.
TASK_CONFIG: dict[str, dict] = {
    "driver": {
        "label_path": LABELS_DIR / "l1" / "L1) Drivers.xlsx",
        "truth_cols": {"driver": "driver"},
        "task_type": "simple",
    },
    "threats": {
        "label_path": LABELS_DIR / "l2" / "L2) threats.xlsx",
        "truth_cols": {"threats_l0": "threats_l0", "threats_l1": "threats_l1"},
        "task_type": "threats",
    },
    "geography": {
        "label_path": LABELS_DIR / "l3" / "L3) geography.xlsx",
        "truth_cols": {"region": "region", "sub-region": "sub-region", "country": "country"},
        "task_type": "geo",
    },
    "ecosystems": {
        "label_path": LABELS_DIR / "l4" / "L4) ecosystems.xlsx",
        "truth_cols": {"realm": "realm", "biome": "biome"},
        "task_type": "ecosystems",
    },
    "study": {
        "label_path": LABELS_DIR / "l5" / "L5) study.xlsx",
        "truth_cols": {"study_design": "study_design"},
        "task_type": "study",
    },
    "taxa": {
        "label_path": LABELS_DIR / "l6" / "L6) taxa.xlsx",
        "truth_cols": {
            "kingdom": "kingdom",
            "phylum": "phylum",
            "class": "class",
            "order": "order",
            "specie": "specie",
        },
        "task_type": "taxa",
    },
}
