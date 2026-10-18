"""Database-ready variant of the core publication dataset.

Same grain and content as ``04_dataset/dataset.parquet`` (one row per eligible
publication), reshaped for loading into a database: abstracts are joined in,
``["Not Applicable"]`` placeholders become blanks, ``pred_countries`` carries
country names instead of ISO3 codes, review/derived-flag columns are dropped, and
``id`` is re-issued as ``1..N`` as the very last step.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from data_helpers.analysis.geo import geography

NOT_APPLICABLE = "Not Applicable"
# Original dataset columns that the database variant drops.
DROPPED_COLUMNS = (
    "pred_regions_audit",
    "pred_subregions_audit",
    "pred_countries_audit",
    "taxa_record_status",
    "text_available",
    "plastics_mention",
)
# List-valued columns that are blanked when they hold only ``Not Applicable``.
BLANKABLE_COLUMNS = (
    "pred_regions",
    "pred_subregions",
    "pred_countries",
    "locales",
    "locale_coordinates",
    "realm",
    "biome",
)
LIST_COLUMNS = (
    "driver",
    "pred_threat_l0",
    "pred_regions",
    "pred_subregions",
    "pred_countries",
    "locales",
    "realm",
    "biome",
    "pred_study_design",
    "pred_methods_data_collection",
    "pred_methods_analysis",
    "pred_comparison_types",
    "taxa_kingdom_labels",
    "taxa_phylum_labels",
    "taxa_class_labels",
    "taxa_order_labels",
    "taxa_family_labels",
    "taxa_genus_labels",
    "taxa_species_labels",
)


class DbDatasetPrepError(ValueError):
    """Raised when the database dataset cannot be built from its inputs."""


def _is_only_not_applicable(value: object) -> bool:
    if isinstance(value, str):
        text = value.strip()
        if text == NOT_APPLICABLE:
            return True
        try:
            parsed = json.loads(text)
        except ValueError:
            return False
        return isinstance(parsed, list) and list(parsed) == [NOT_APPLICABLE]
    if isinstance(value, (list, tuple, np.ndarray)):
        return list(value) == [NOT_APPLICABLE]
    return False


def blank_not_applicable(
    publications: pd.DataFrame, columns: tuple[str, ...] = BLANKABLE_COLUMNS
) -> dict[str, int]:
    """Replace values that are exactly ``["Not Applicable"]`` with ``None`` in place.

    Mixed lists such as ``["USA", "Not Applicable"]`` are left untouched. Returns
    the number of blanked cells per column.
    """
    counts: dict[str, int] = {}
    for column in columns:
        mask = publications[column].map(_is_only_not_applicable).to_numpy(dtype=bool)
        publications[column] = publications[column].astype(object).where(~mask, None)
        counts[column] = int(mask.sum())
    return counts


def country_name_lookup() -> dict[str, str]:
    """Map normalised ISO3 codes to IPBES crosswalk country names.

    A trailing ``" (the)"`` is dropped (``"United States of America (the)"`` becomes
    ``"United States of America"``); other qualifiers are kept. Crosswalk rows
    without an ISO3 code (e.g. sub-national entries) are not addressable.
    """
    crosswalk = geography.load_crosswalk()
    lookup: dict[str, str] = {}
    for iso3, name in zip(crosswalk["iso3"], crosswalk["country"]):
        key = geography._normalise(iso3)
        if key:
            lookup[key] = name.removesuffix(" (the)")
    return lookup


def countries_to_names(
    publications: pd.DataFrame, lookup: dict[str, str] | None = None
) -> pd.DataFrame:
    """Replace ISO3 codes in ``pred_countries`` with country names, in place.

    Tokens that are not valid ISO3 codes (``Unclear``, ``Not Applicable``, malformed
    codes) are kept verbatim, never dropped. Returns an audit of the kept tokens.
    """
    lookup = lookup or country_name_lookup()
    unmapped: dict[str, int] = {}

    def convert(value: object) -> object:
        if value is None:
            return None
        names = []
        for token in value:
            name = lookup.get(geography._normalise(token))
            if name is None:
                unmapped[token] = unmapped.get(token, 0) + 1
                names.append(token)
            else:
                names.append(name)
        return names

    publications["pred_countries"] = publications["pred_countries"].map(convert)
    return (
        pd.Series(unmapped, name="n_mentions", dtype="int64")
        .rename_axis("token")
        .reset_index()
        .sort_values("n_mentions", ascending=False, ignore_index=True)
    )


def build_db_dataset(
    publications: pd.DataFrame, abstracts: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return the database dataset and an audit of every change made.

    ``publications`` is ``dataset.parquet``; ``abstracts`` is
    ``dataset_abstracts.parquet``. Row order is preserved and ``id`` is re-issued
    as ``1..N`` after every other step.
    """
    for frame, label in ((publications, "dataset"), (abstracts, "abstracts")):
        if not frame["UT"].is_unique:
            raise DbDatasetPrepError(f"{label} UT is not unique.")
    if set(publications["UT"]) != set(abstracts["UT"]):
        raise DbDatasetPrepError("dataset and abstracts do not cover the same UT set.")
    missing = [c for c in DROPPED_COLUMNS if c not in publications.columns]
    if missing:
        raise DbDatasetPrepError(f"dataset is missing expected columns: {missing}")

    db = publications.drop(columns=list(DROPPED_COLUMNS)).copy()
    abstract_by_ut = abstracts.set_index("UT")["abstract"]
    db["abstract"] = db["UT"].map(abstract_by_ut)
    # Place the abstract directly after the title.
    columns = db.columns.tolist()
    columns.remove("abstract")
    columns.insert(columns.index("title") + 1, "abstract")
    db = db[columns]

    country_audit = countries_to_names(db)
    blanked = blank_not_applicable(db)

    db["id"] = np.arange(1, len(db) + 1, dtype="int64")
    audit = {
        "blanked_cells": blanked,
        "unconverted_country_tokens": country_audit,
        "n_missing_abstract": int(db["abstract"].isna().sum()),
    }
    return db, audit


def _json_text(value: object) -> object:
    if value is None:
        return None
    return json.dumps(list(value), ensure_ascii=False)


def write_db_dataset(
    db: pd.DataFrame, directory: str | Path
) -> list[Path]:
    """Write ``dataset_for_db.parquet`` (native lists) and ``dataset_for_db.csv``.

    The CSV stores list fields as JSON text and blanks as empty fields.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    parquet_path = directory / "dataset_for_db.parquet"
    csv_path = directory / "dataset_for_db.csv"

    db.to_parquet(parquet_path, index=False)
    csv_frame = db.copy()
    for column in LIST_COLUMNS:
        csv_frame[column] = csv_frame[column].map(_json_text)
    csv_frame.to_csv(csv_path, index=False, encoding="utf-8")
    return [parquet_path, csv_path]


__all__ = [
    "BLANKABLE_COLUMNS",
    "DROPPED_COLUMNS",
    "DbDatasetPrepError",
    "LIST_COLUMNS",
    "blank_not_applicable",
    "build_db_dataset",
    "countries_to_names",
    "country_name_lookup",
    "write_db_dataset",
]
