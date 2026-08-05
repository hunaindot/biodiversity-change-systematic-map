"""Where each broad taxon group is studied — a supplementary geographic lens.

This answers a different question from the F4 headline. The headline asks whether
attention matches described diversity; this asks whether a country's biodiversity
literature *specialises* in one taxon group relative to the corpus average. It is
supplementary because it carries no external benchmark: a country studying few
vertebrates may have few vertebrates, and nothing here distinguishes the two.

The metric is the documented Location Quotient, unchanged — see
``checklists/repo-readmes/others/geography-research-specialization.md``.

The per-group choropleths this module once fed were retired on 2026-08-02: they answer a
within-country specialization question that supports no F4 claim. What survives is the
location-quotient frame itself, which the evidence-versus-threat analysis consumes as its
per-country publication counts. Snapshot in
``notebooks/results/archive/retired-helpers/2026-08-02-f4-cleanup/``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from data_helpers.analysis.geo.geography import GeoAudit, location_quotient


class TaxaGeographyError(ValueError):
    """Raised when the geographic join cannot be built as specified."""


def load_publication_countries(
    source: str | Path,
    *,
    id_col: str = "UT",
    country_col: str = "pred_countries",
) -> pd.DataFrame:
    """Read one row per publication with its coded study countries.

    Reads the *data-processing* corpus handoff rather than any results notebook's
    output, so this analysis stays a sibling of ``taxa_analysis_prep`` rather than
    a dependant of Result 02.

    Parquet returns list columns as numpy arrays, and ``parse_list_labels`` raises
    on an empty array (``pd.isna`` is ambiguous there), so values are normalised to
    plain lists on the way out.
    """
    source = Path(source)
    if not source.exists():
        raise TaxaGeographyError(f"Country source not found: {source}")
    frame = pd.read_parquet(source, columns=[id_col, country_col])

    def _as_list(value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, (list, tuple)):
            return list(value)
        return [value]

    frame[country_col] = frame[country_col].map(_as_list)
    duplicated = int(frame[id_col].duplicated().sum())
    if duplicated:
        raise TaxaGeographyError(
            f"Country source is not one row per {id_col}: {duplicated:,} duplicates."
        )
    return frame


def taxa_country_specialization(
    included: pd.DataFrame,
    countries: pd.DataFrame,
    *,
    benchmark_groups: Iterable[str],
    level: str = "country",
    min_support: int = 100,
    eb_kappa: float | None = 30.0,
    id_col: str = "UT",
    group_col: str = "benchmark_groups",
    country_col: str = "pred_countries",
) -> tuple[pd.DataFrame, GeoAudit, pd.DataFrame]:
    """Location quotient of each broad group within each place.

    ``LQ[c, g] = (n[c, g] / D[c]) / (T[g] / D)`` on unique documents, exactly as
    the threat maps compute it — only the class axis changes from threat to taxon
    group. Returns the long LQ frame, the geography audit, and a one-row coverage
    frame recording how much of the taxonomic scope carries a usable country.

    Coverage is the headline caveat for this analysis and is returned rather than
    printed so the notebook can export it alongside the figure.
    """
    benchmark_groups = tuple(benchmark_groups)
    missing = {id_col, group_col}.difference(included.columns)
    if missing:
        raise TaxaGeographyError(f"Included frame is missing columns: {sorted(missing)}")

    source = included[[id_col, group_col]].merge(countries, on=id_col, how="left")
    source[country_col] = source[country_col].map(
        lambda value: list(value) if isinstance(value, (list, tuple, np.ndarray)) else []
    )
    source[group_col] = source[group_col].map(
        lambda value: [g for g in (value or ()) if g in benchmark_groups]
    )
    usable = source[source[group_col].map(len) > 0].copy()
    if usable.empty:
        raise TaxaGeographyError("No publications carry a benchmark group.")

    lq, audit = location_quotient(
        usable,
        level=level,
        by=group_col,
        id_col=id_col,
        country_col=country_col,
        min_support=min_support,
        eb_kappa=eb_kappa,
        verbose=False,
    )
    lq = lq.rename(columns={group_col: "broad_group"})

    n_scope = int(included[id_col].nunique())
    # Coverage must come from the LQ's own universe, not the audit. The audit counts
    # a publication as having geography whenever pred_countries is non-empty, and
    # "Not Applicable" is a non-empty token — that overstates coverage by ~37 points.
    n_universe = int(lq["universe"].iloc[0]) if len(lq) else 0
    n_sufficient_places = int(lq.loc[lq["sufficient"], "iso3"].nunique()) if len(lq) else 0
    coverage = pd.DataFrame(
        [
            {
                "scope": "Taxonomic scope (anchor)",
                "n_publications": n_scope,
                "share_of_scope_pct": 100.0,
            },
            {
                "scope": "…with at least one mapped country (the mapped universe)",
                "n_publications": n_universe,
                "share_of_scope_pct": n_universe / n_scope * 100.0,
            },
        ]
    )
    coverage.attrs["n_places_meeting_min_support"] = n_sufficient_places
    coverage.attrs["min_support"] = min_support
    return lq, audit, coverage


def group_slug(group: str) -> str:
    """Filename-safe form of a group name, for one-file-per-group exports."""
    return re.sub(r"[^a-z0-9]+", "-", group.lower()).strip("-")


__all__ = [
    "TaxaGeographyError",
    "group_slug",
    "load_publication_countries",
    "taxa_country_specialization",
]
