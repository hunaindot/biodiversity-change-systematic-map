from __future__ import annotations

import json
from functools import lru_cache
import json
import ast
import math
from pathlib import Path
from typing import Iterable

from .config import MAPPINGS_DIR


def to_label_set(value) -> set[str]:
    """Coerce list/tuple/set/str/None into a lower-cased, deduped set of strings."""
    seq: list[str] = []
    if value is None:
        seq = []
    elif isinstance(value, float) and math.isnan(value):
        seq = []
    elif isinstance(value, (list, tuple, set)):
        seq = list(value)
    elif isinstance(value, str):
        parsed = value
        # try JSON or python-literal decoding for stringified lists
        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(value)
                break
            except Exception:
                parsed = value
                continue
        if isinstance(parsed, (list, tuple, set)):
            seq = list(parsed)
        else:
            seq = [value]
    else:
        seq = [str(value)]
    clean = {
        s for s in (str(item).strip().lower() for item in seq)
        if s and s != "nan"
    }
    return clean


def to_label_list(value) -> list[str]:
    return sorted(to_label_set(value))


@lru_cache(maxsize=1)
def load_iso_maps() -> tuple[dict[str, str], dict[str, str]]:
    """Return iso3->name and name_lower->iso3 from ipbes_regions.json."""
    path = MAPPINGS_DIR / "ipbes_regions.json"
    if not path.exists():
        return {}, {}
    data = json.loads(path.read_text(encoding="utf-8"))
    iso_to_name: dict[str, str] = {}
    name_to_iso: dict[str, str] = {}

    def _walk(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict):
                    iso = item.get("ISO_3166_alpha_3") or item.get("GID_0")
                    name = item.get("Country")
                    if iso and name:
                        iso_upper = iso.strip().upper()
                        iso_to_name.setdefault(iso_upper, name.strip())
                        name_to_iso.setdefault(name.strip().lower(), iso_upper)
    _walk(data)
    return iso_to_name, name_to_iso


def normalize_geo_labels(values) -> set[str]:
    """Normalize geography labels to ISO3 where possible; keep lower-case names fallback."""
    iso_to_name, name_to_iso = load_iso_maps()
    out: set[str] = set()
    if values is None:
        return out
    if isinstance(values, (str, bytes)):
        # try to decode stringified lists
        decoded = values
        for parser in (json.loads, ast.literal_eval):
            try:
                decoded = parser(values)
                break
            except Exception:
                decoded = values
                continue
        values = decoded if isinstance(decoded, (list, tuple, set)) else [decoded]
    if not isinstance(values, Iterable):
        values = [values]
    for raw in values:
        if raw is None:
            continue
        text = str(raw).strip()
        if not text or text.lower() == "nan":
            continue
        if len(text) == 3 and text.isalpha():
            out.add(text.upper())
            continue
        iso = name_to_iso.get(text.lower())
        if iso:
            out.add(iso)
        else:
            out.add(text.lower())
    return out


def normalize_screening_label(value) -> str:
    """
    Canonicalize screening labels to either ELIGIBLE or NOT_ELIGIBLE.
    Accepts single strings or single-item lists; returns empty string if missing.
    """
    labels = to_label_list(value)
    if not labels:
        return ""
    raw = labels[0].strip().lower().replace("-", "_").replace(" ", "_")
    if raw in {"eligible"}:
        return "ELIGIBLE"
    if raw in {"not_eligible", "noteligible", "ineligible"}:
        return "NOT_ELIGIBLE"
    return raw.upper()
