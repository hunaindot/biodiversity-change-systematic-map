"""Tests for the income-composition diagnostics.

These cover the transition, missing-assignment and threat-diversity helpers that
`02-unchecked-income-composition.ipynb` reports.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data_helpers.analysis import driver_composition as dc


GROUPS = ["Low income", "Lower middle income", "Upper middle income", "High income"]
INVASIVE = "Invasive & Other Problematic Species, Genes & Diseases"


def _classified(records: list[tuple[str, int, str, str]]) -> pd.DataFrame:
    return pd.DataFrame(
        records,
        columns=[
            "UT",
            "publication_year",
            "current_income_group",
            "historical_income_group",
        ],
    )


def _attributions(rows: list[tuple[str, str, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        rows, columns=["income_group", "threat", "attribution_weight"]
    )


def test_transition_counts_keep_only_dual_standard_assignments() -> None:
    classified = _classified(
        [
            ("a", 2001, "High income", "Upper middle income"),
            ("b", 2002, "High income", "High income"),
            ("c", 2003, "High income", "Not classified"),
            ("d", 2004, "Not classified", "High income"),
        ]
    )

    transitions = dc.income_transition_counts(classified, GROUPS)

    total = transitions["publication_country_assignments"].sum()
    assert total == 2, "Rows lacking a standard group under either scheme must drop."
    moved = transitions.loc[
        transitions["current_income_group"].ne(
            transitions["historical_income_group"]
        ),
        "publication_country_assignments",
    ].sum()
    assert moved == 1


def test_missing_by_year_counts_assignments_and_unique_publications() -> None:
    classified = _classified(
        [
            ("a", 2001, "High income", "Not classified"),
            ("a", 2001, "High income", "Not classified"),
            ("b", 2002, "High income", "High income"),
        ]
    )

    missing = dc.missing_historical_by_year(classified, GROUPS).set_index(
        "publication_year"
    )

    assert list(missing.index) == [2001]
    assert missing.loc[2001, "publication_country_assignments"] == 2
    assert missing.loc[2001, "unique_publications"] == 1


def test_diversity_of_an_even_split_is_the_number_of_threats() -> None:
    attributions = _attributions(
        [("Low income", threat, 1.0) for threat in ("a", "b", "c", "d")]
    )

    diversity = dc.income_threat_diversity(attributions, ["Low income"]).iloc[0]

    assert diversity["effective_number_of_threats"] == pytest.approx(4.0)
    assert diversity["shannon_entropy"] == pytest.approx(np.log(4))


def test_diversity_falls_when_one_threat_dominates() -> None:
    even = _attributions([("Low income", "a", 1.0), ("Low income", "b", 1.0)])
    skewed = _attributions([("Low income", "a", 9.0), ("Low income", "b", 1.0)])

    even_value = dc.income_threat_diversity(even, ["Low income"]).iloc[0]
    skewed_value = dc.income_threat_diversity(skewed, ["Low income"]).iloc[0]

    assert (
        skewed_value["effective_number_of_threats"]
        < even_value["effective_number_of_threats"]
    )
