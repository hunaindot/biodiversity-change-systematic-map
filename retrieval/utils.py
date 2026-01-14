from __future__ import annotations

import re
from typing import Iterable, Optional

import pandas as pd


def norm_keyword(x: Optional[str]) -> Optional[str]:
    """Normalize keyword-like values for raw (non-analyzed) fields."""
    if x is None:
        return None
    s = str(x).strip().lower()
    if not s or s == "nan":
        return None
    s = re.sub(r"\s+", "_", s)
    return s


def split_vernaculars(x: Optional[str]) -> list[str]:
    if x is None:
        return []
    s = str(x).strip()
    if not s or s == "nan":
        return []
    parts = re.split(r"[|;,\n\t]+", s)
    return [p.strip() for p in parts if p and p.strip()]


def to_int_or_none(x) -> Optional[int]:
    try:
        if x is None or (hasattr(pd, "isna") and pd.isna(x)):
            return None
        return int(float(x))
    except Exception:
        return None


def to_bool01(x) -> int:
    if x is None or (hasattr(pd, "isna") and pd.isna(x)):
        return 0
    if isinstance(x, bool):
        return 1 if x else 0
    s = str(x).strip().lower()
    return 1 if s in {"1", "true", "t", "yes", "y"} else 0


def edge_ngrams(text: Optional[str], min_n: int, max_n: int) -> list[str]:
    if text is None:
        return []
    s = str(text).strip().lower()
    if not s or s == "nan":
        return []

    tokens = re.findall(r"[0-9a-z]+", s)
    grams = set()
    for tok in tokens:
        if len(tok) < min_n:
            continue
        upper = min(max_n, len(tok))
        for n in range(min_n, upper + 1):
            grams.add(tok[:n])
    return sorted(grams)


def make_name_text(row: dict) -> str:
    """Aggregate canonical, scientific, hierarchical names, and vernaculars."""
    parts: list[str] = []
    for key in [
        "canonicalName",
        "scientificName",
        "genericName",
        "specificEpithet",
        "infraspecificEpithet",
        "kingdom",
        "phylum",
        "class",
        "order",
        "family",
        "genus",
    ]:
        value = row.get(key)
        if value is None or (hasattr(pd, "isna") and pd.isna(value)):
            continue
        s = str(value).strip()
        if s and s.lower() != "nan":
            parts.append(s)
    parts.extend(split_vernaculars(row.get("vernaculars_named")))
    return " | ".join(parts)


def first_value(doc, field: str, default=None):
    try:
        vals = doc[field]
        return vals[0] if vals else default
    except Exception:
        return default
