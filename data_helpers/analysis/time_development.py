"""Reusable table calculations for temporal biodiversity-loss results."""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd

from data_helpers.labels import parse_list_labels


def prepare_loss_evidence(
    corpus_df: pd.DataFrame,
    start_year: int,
    end_year: int,
    threat_order: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Filter biodiversity loss and build unique document–year–threat rows."""
    if corpus_df["UT"].isna().any() or not corpus_df["UT"].is_unique:
        raise ValueError("The merged corpus must contain one non-missing row per UT.")

    loss_df = corpus_df.loc[corpus_df["s2_dir"].eq("negative")].copy()
    loss_df["publication_year"] = pd.to_numeric(
        loss_df["publication_year"], errors="coerce"
    ).astype("Int64")
    in_window = loss_df["publication_year"].between(start_year, end_year)

    threat_long = loss_df.loc[
        in_window, ["UT", "publication_year", "pred_threat_l0"]
    ].copy()
    threat_long["pred_threat_l0"] = threat_long["pred_threat_l0"].map(
        parse_list_labels
    )
    documents_without_threat = int(
        threat_long["pred_threat_l0"].map(len).eq(0).sum()
    )
    threat_long = (
        threat_long.explode("pred_threat_l0")
        .dropna(subset=["publication_year", "pred_threat_l0"])
    )
    threat_long["pred_threat_l0"] = (
        threat_long["pred_threat_l0"].astype("string").str.strip()
    )
    threat_long = (
        threat_long.loc[threat_long["pred_threat_l0"].ne("")]
        .drop_duplicates(["UT", "publication_year", "pred_threat_l0"])
    )
    threat_long["publication_year"] = threat_long["publication_year"].astype(int)

    observed = set(threat_long["pred_threat_l0"])
    unconfigured = sorted(observed.difference(threat_order))
    if unconfigured:
        raise ValueError(f"Unconfigured pred_threat_l0 labels: {unconfigured}")

    audit = pd.DataFrame(
        {
            "metric": [
                "Eligible publications",
                "Biodiversity-loss publications",
                f"Loss publications in {start_year}–{end_year}",
                "Loss publications outside window or missing year",
                "In-window publications without usable threat",
                "Unique document–threat assignments",
                "Observed threat classes",
            ],
            "value": [
                len(corpus_df),
                len(loss_df),
                int(loss_df.loc[in_window, "UT"].nunique()),
                int((~in_window).sum()),
                documents_without_threat,
                len(threat_long),
                len(observed),
            ],
        }
    )
    return loss_df, threat_long, audit


def annual_publication_tables(
    loss_df: pd.DataFrame,
    start_year: int,
    end_year: int,
    partial_year: int,
    projection_window: tuple[int, int],
) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    """Build complete-year counts plus the explicitly labelled partial-year projection."""
    in_window = loss_df["publication_year"].between(start_year, end_year)
    annual_counts = (
        loss_df.loc[in_window]
        .assign(publication_year=lambda frame: frame["publication_year"].astype(int))
        .groupby("publication_year")["UT"]
        .nunique()
    )
    full_years = pd.RangeIndex(start_year, end_year + 1, name="publication_year")
    annual_counts = annual_counts.reindex(full_years, fill_value=0).rename(
        "n_publications"
    )

    annual_table = annual_counts.reset_index()
    annual_table["year_status"] = "complete"
    annual_table["cumulative_publications"] = annual_table[
        "n_publications"
    ].cumsum()
    annual_table["yoy_growth_pct"] = (
        annual_table["n_publications"].pct_change() * 100
    ).round(2)
    annual_table["share_of_total_pct"] = (
        annual_table["n_publications"] / annual_table["n_publications"].sum() * 100
    ).round(3)
    annual_table["projected_full"] = annual_table["n_publications"]
    annual_table["estimated_remainder"] = 0

    window_start, window_end = projection_window
    start_count = int(annual_counts.loc[window_start])
    end_count = int(annual_counts.loc[window_end])
    projection_cagr = (
        (end_count / start_count) ** (1 / (window_end - window_start)) - 1
    )
    observed_partial = int(
        loss_df.loc[loss_df["publication_year"].eq(partial_year), "UT"].nunique()
    )
    projected_full = int(round(end_count * (1 + projection_cagr)))
    estimated_remainder = max(projected_full - observed_partial, 0)

    partial_row = pd.DataFrame(
        [
            {
                "publication_year": partial_year,
                "n_publications": observed_partial,
                "year_status": "partial",
                "cumulative_publications": pd.NA,
                "yoy_growth_pct": pd.NA,
                "share_of_total_pct": pd.NA,
                "projected_full": projected_full,
                "estimated_remainder": estimated_remainder,
            }
        ]
    )
    # pandas 2.3 warns about future dtype inference for an all-NA partial-year cell.
    # The current inference is intentional because it preserves the established CSV
    # schema; scope the warning to this single compatibility append.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        annual_table = pd.concat(
            [annual_table, partial_row],
            ignore_index=True,
        )
    projection_table = pd.DataFrame(
        [
            {
                "partial_year": partial_year,
                "observed_partial": observed_partial,
                "cagr_window": f"{window_start}-{window_end}",
                "cagr_pct": round(projection_cagr * 100, 3),
                "base_year": window_end,
                "base_count": end_count,
                "projected_full": projected_full,
                "estimated_remainder": estimated_remainder,
            }
        ]
    )
    return annual_counts, annual_table, projection_table


def threat_composition_tables(
    threat_long: pd.DataFrame,
    annual_counts: pd.Series,
    threat_order: list[str],
    start_year: int,
    end_year: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build yearly threat counts, 100% shares, long output, and an audit."""
    observed_order = [
        threat
        for threat in threat_order
        if threat in set(threat_long["pred_threat_l0"])
    ]
    counts = (
        threat_long.groupby(
            ["publication_year", "pred_threat_l0"], observed=True
        )["UT"]
        .nunique()
        .rename("record_count")
        .reset_index()
        .pivot(
            index="publication_year",
            columns="pred_threat_l0",
            values="record_count",
        )
        .reindex(
            index=range(start_year, end_year + 1),
            columns=observed_order,
            fill_value=0,
        )
        .fillna(0)
        .astype(int)
    )
    counts.index.name = "publication_year"
    shares = (counts.div(counts.sum(axis=1), axis=0) * 100).round(4)
    assert np.allclose(
        shares.sum(axis=1).loc[counts.sum(axis=1) > 0], 100.0
    )

    long = (
        counts.reset_index()
        .melt(
            id_vars="publication_year",
            var_name="pred_threat_l0",
            value_name="record_count",
        )
        .merge(
            shares.reset_index().melt(
                id_vars="publication_year",
                var_name="pred_threat_l0",
                value_name="share_pct",
            ),
            on=["publication_year", "pred_threat_l0"],
        )
        .sort_values(["publication_year", "pred_threat_l0"])
        .reset_index(drop=True)
    )
    audit = pd.DataFrame(
        {
            "publication_year": counts.index,
            "n_publications": annual_counts.reindex(counts.index)
            .astype(int)
            .to_numpy(),
            "n_assignments": counts.sum(axis=1).to_numpy(),
        }
    )
    audit["labels_per_publication"] = (
        audit["n_assignments"] / audit["n_publications"]
    ).round(3)
    return counts, shares, long, audit


def cagr_pct(base: int, end: int, years: int) -> float:
    """Return compound annual growth in percent, or NaN for an invalid base."""
    if base <= 0 or years <= 0:
        return np.nan
    return ((end / base) ** (1.0 / years) - 1.0) * 100.0


def growth_tables(
    counts: pd.DataFrame,
    annual_counts: pd.Series,
    threat_order: list[str],
    threat_codes: dict[str, str],
    periods: list[dict[str, Any]],
    rolling_years: int,
    start_year: int,
    end_year: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series]:
    """Build fixed-window and rolling CAGR tables."""
    rows = []
    for threat in counts.columns:
        series = counts[threat]
        for period in periods:
            base_year = period["base_year"]
            end_period_year = period["end_year"]
            base = int(series.get(base_year, 0))
            end = int(series.get(end_period_year, 0))
            years = end_period_year - base_year
            value = cagr_pct(base, end, years)
            note = (
                "base year count is 0 (CAGR undefined)"
                if base == 0
                else "end year count is 0"
                if end == 0
                else ""
            )
            rows.append(
                {
                    "pred_threat_l0": threat,
                    "threat_code": threat_codes[threat],
                    "period": period["label"],
                    "base_year": base_year,
                    "base_count": base,
                    "end_year": end_period_year,
                    "end_count": end,
                    "n_years": years,
                    "cagr_pct": round(value, 2) if pd.notna(value) else np.nan,
                    "note": note,
                }
            )
    detailed = pd.DataFrame(rows)
    matrix = (
        detailed.pivot(
            index="pred_threat_l0", columns="period", values="cagr_pct"
        )
        .reindex(
            index=counts.columns,
            columns=[period["label"] for period in periods],
        )
    )
    matrix.index.name = "pred_threat_l0"

    rolling_end_years = np.arange(start_year + rolling_years, end_year + 1)
    rolling = pd.DataFrame(
        index=rolling_end_years, columns=counts.columns, dtype=float
    )
    for rolling_end in rolling_end_years:
        base_year = rolling_end - rolling_years
        for threat in counts.columns:
            rolling.loc[rolling_end, threat] = cagr_pct(
                int(counts.loc[base_year, threat]),
                int(counts.loc[rolling_end, threat]),
                rolling_years,
            )
    rolling.index.name = "window_end_year"
    overall = pd.Series(
        {
            rolling_end: cagr_pct(
                int(annual_counts.loc[rolling_end - rolling_years]),
                int(annual_counts.loc[rolling_end]),
                rolling_years,
            )
            for rolling_end in rolling_end_years
        },
        name="overall_biodiversity_loss",
    )
    rolling_all = rolling.copy()
    rolling_all.insert(0, "overall_biodiversity_loss", overall)
    return detailed, matrix, rolling_all, rolling, overall
