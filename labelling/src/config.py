from __future__ import annotations

import json
import os
from pathlib import Path

# Repo root — internal anchor for resolving relative paths; not user-configurable.
ROOT_DIR = Path(__file__).resolve().parents[2]
REPO_CONFIG_PATH = ROOT_DIR / "checklists" / "mappings" / "repo_config.json"


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


def _load_repo_config() -> dict:
    """Load repo-level JSON config used for non-secret repository settings."""
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


def _require_repo_config_section(section: str) -> dict:
    section_config = REPO_CONFIG.get(section)
    if not isinstance(section_config, dict):
        raise ValueError(f"Required config section {section!r} is missing in {REPO_CONFIG_PATH}.")
    return section_config


def _require_repo_config_string(section: str, key: str) -> str:
    section_config = _require_repo_config_section(section)
    raw = section_config.get(key)
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"Required config key {section}.{key} is missing in {REPO_CONFIG_PATH}.")
    return raw.strip()


def _resolve_repo_config_path(section: str, key: str) -> Path:
    """Read a required path from repo_config.json; relative paths resolved from ROOT_DIR."""
    raw = _require_repo_config_string(section, key)
    p = Path(raw)
    return p if p.is_absolute() else ROOT_DIR / p


def _require_prompt_key(key: str) -> str:
    prompts_config = _require_repo_config_section("prompts")
    keys_config = prompts_config.get("keys")
    if not isinstance(keys_config, dict):
        raise ValueError(f"Required config section 'prompts.keys' is missing in {REPO_CONFIG_PATH}.")
    raw = keys_config.get(key)
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"Required config key prompts.keys.{key} is missing in {REPO_CONFIG_PATH}.")
    return raw.strip()


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
PROMPTS_DIR       = _resolve_repo_config_path("prompts", "dir")
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

PROMPT_KEY_DRIVER     = _require_prompt_key("driver")
PROMPT_KEY_SCREENING  = _require_prompt_key("screening")
PROMPT_KEY_GEOGRAPHY  = _require_prompt_key("geography")
PROMPT_KEY_TAXA       = _require_prompt_key("taxa")
PROMPT_KEY_STUDY      = _require_prompt_key("study")
PROMPT_KEY_ECOSYSTEMS = _require_prompt_key("ecosystems")
PROMPT_KEY_ECOSYSTEMS_CORE  = _require_prompt_key("ecosystems_core")
PROMPT_KEY_ECOSYSTEMS_REALM = _require_prompt_key("ecosystems_realm")
PROMPT_KEY_ECOSYSTEMS_BIOME = _require_prompt_key("ecosystems_biome")
PROMPT_KEY_ECOSYSTEMS_EFG   = _require_prompt_key("ecosystems_efg")
PROMPT_KEY_THREATS    = _require_prompt_key("threats")
PROMPT_KEY_THREATS_CORE = _require_prompt_key("threats_core")
PROMPT_KEY_THREATS_L0   = _require_prompt_key("threats_l0")
PROMPT_KEY_THREATS_L1   = _require_prompt_key("threats_l1")
PROMPT_KEY_THREATS_L2   = _require_prompt_key("threats_l2")
