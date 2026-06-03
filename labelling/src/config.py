from __future__ import annotations

import os
from pathlib import Path

# Repo root — internal anchor for resolving relative paths; not user-configurable.
ROOT_DIR = Path(__file__).resolve().parents[2]


# ── Env bootstrap ─────────────────────────────────────────────────────────────

def _bootstrap_env() -> None:
    """Load .env into os.environ at import time so constants below can read from it.
    Uses setdefault — env vars already set in the shell take precedence."""
    env_path = ROOT_DIR / ".env"
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

def _require_env(env_var: str) -> str:
    """Read a required string from an env var; raises if not set."""
    value = os.environ.get(env_var, "").strip()
    if not value:
        raise ValueError(f"Required env var {env_var!r} is not set. Add it to .env.")
    return value


def _resolve_dir(env_var: str) -> Path:
    """Read a required directory path from an env var; relative paths resolved from ROOT_DIR."""
    raw = _require_env(env_var)
    p = Path(raw)
    return p if p.is_absolute() else ROOT_DIR / p


def ensure_artifact_dirs() -> None:
    """Create artifact directories if they do not exist."""
    for path in (DATASETS_DIR, BATCHES_DIR, BATCH_OUTPUTS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def get_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Required env var 'OPENAI_API_KEY' is not set.")
    return api_key


# ── Paths ─────────────────────────────────────────────────────────────────────

MAPPINGS_DIR      = _resolve_dir("ORCHESTRATOR_MAPPINGS_DIR")
PROMPTS_DIR       = _resolve_dir("ORCHESTRATOR_PROMPTS_DIR")
DATASETS_DIR      = _resolve_dir("ORCHESTRATOR_DATASETS_DIR")
BATCHES_DIR       = _resolve_dir("ORCHESTRATOR_BATCHES_DIR")
BATCH_OUTPUTS_DIR = _resolve_dir("ORCHESTRATOR_BATCH_OUTPUTS_DIR")


# ── Model defaults ────────────────────────────────────────────────────────────

DEFAULT_MODEL            = _require_env("ORCHESTRATOR_MODEL")
DEFAULT_REASONING_EFFORT = _require_env("ORCHESTRATOR_REASONING")
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


# ── Prompt keys ───────────────────────────────────────────────────────────────

PROMPT_KEY_DRIVER     = _require_env("PROMPT_KEY_DRIVER")
PROMPT_KEY_SCREENING  = _require_env("PROMPT_KEY_SCREENING")
PROMPT_KEY_GEOGRAPHY  = _require_env("PROMPT_KEY_GEOGRAPHY")
PROMPT_KEY_TAXA       = _require_env("PROMPT_KEY_TAXA")
PROMPT_KEY_STUDY      = _require_env("PROMPT_KEY_STUDY")
PROMPT_KEY_ECOSYSTEMS = _require_env("PROMPT_KEY_ECOSYSTEMS")
PROMPT_KEY_ECOSYSTEMS_CORE  = _require_env("PROMPT_KEY_ECOSYSTEMS_CORE")
PROMPT_KEY_ECOSYSTEMS_REALM = _require_env("PROMPT_KEY_ECOSYSTEMS_REALM")
PROMPT_KEY_ECOSYSTEMS_BIOME = _require_env("PROMPT_KEY_ECOSYSTEMS_BIOME")
PROMPT_KEY_ECOSYSTEMS_EFG   = _require_env("PROMPT_KEY_ECOSYSTEMS_EFG")
PROMPT_KEY_THREATS    = _require_env("PROMPT_KEY_THREATS")
PROMPT_KEY_THREATS_CORE = _require_env("PROMPT_KEY_THREATS_CORE")
PROMPT_KEY_THREATS_L0   = _require_env("PROMPT_KEY_THREATS_L0")
PROMPT_KEY_THREATS_L1   = _require_env("PROMPT_KEY_THREATS_L1")
PROMPT_KEY_THREATS_L2   = _require_env("PROMPT_KEY_THREATS_L2")
