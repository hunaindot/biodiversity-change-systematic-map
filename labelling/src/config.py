from __future__ import annotations

import os
from pathlib import Path

# Base paths
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data" / "wos-data" / "2025"
MAPPINGS_DIR = ROOT_DIR / "mappings"

# Artifacts
ARTIFACTS_DIR = ROOT_DIR / "labelling" / "artifacts"
DATASETS_DIR = ARTIFACTS_DIR / "datasets"
BATCHES_DIR = ARTIFACTS_DIR / "batches"
BATCH_OUTPUTS_DIR = ARTIFACTS_DIR / "batch_outputs"

# Defaults
DEFAULT_MODEL = "gpt-5-nano-2025-08-07"
DEFAULT_REASONING_EFFORT = "low"
DEFAULT_COLUMNS = [
    "Document Type",
    "Authors",
    "Article Title",
    "Abstract",
    "DOI",
    "WoS Categories",
    "Publisher",
    "Publication Date",
    "Publication Year",
    "UT (Unique WOS ID)",
]


def ensure_artifact_dirs() -> None:
    """Create artifact directories if they do not exist."""
    for path in (
        ARTIFACTS_DIR,
        DATASETS_DIR,
        BATCHES_DIR,
        BATCH_OUTPUTS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def get_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Set OPENAI_API_KEY in your environment to call OpenAI.")
    return api_key
