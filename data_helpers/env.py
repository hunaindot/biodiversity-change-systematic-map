from __future__ import annotations

from pathlib import Path


def load_env(path: Path) -> dict[str, str]:
    """Parse a simple .env file (KEY=VALUE, optional quotes)."""
    env: dict[str, str] = {}
    if not path.exists():
        return env

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"").strip("'")
        env[key] = value
    return env


def get_env_int(env: dict[str, str], key: str, default: int) -> int:
    value = env.get(key)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_label_path(env: dict[str, str], label: str) -> Path:
    env_key = f"LABELS_{label.upper()}_PATH"
    raw = env.get(env_key)
    if raw:
        return Path(raw)
    return Path("data") / "labels" / label
