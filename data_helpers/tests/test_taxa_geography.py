"""Tests for the supplementary taxa-geography lens."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from data_helpers.analysis.taxa import geography as tg


GROUPS = ("Vertebrates", "Invertebrates")


def _countries_parquet(tmp_path: Path) -> Path:
    """Country column written the way parquet gives it back: numpy arrays."""
    frame = pd.DataFrame(
        {
            "UT": [f"W{i}" for i in range(6)],
            "pred_countries": [
                np.array(["USA"]),
                np.array(["USA"]),
                np.array(["BRA"]),
                np.array(["Not Applicable"]),
                np.array([], dtype=object),
                None,
            ],
        }
    )
    path = tmp_path / "corpus.parquet"
    frame.to_parquet(path)
    return path


def test_country_loading_normalises_arrays_and_nulls(tmp_path: Path) -> None:
    frame = tg.load_publication_countries(_countries_parquet(tmp_path))

    assert all(isinstance(value, list) for value in frame["pred_countries"])
    # An empty array must survive as [], not raise: parse_list_labels calls pd.isna,
    # which is ambiguous on an empty array.
    assert frame.loc[frame["UT"] == "W4", "pred_countries"].item() == []
    assert frame.loc[frame["UT"] == "W5", "pred_countries"].item() == []


def test_country_loading_rejects_a_duplicated_identifier(tmp_path: Path) -> None:
    path = tmp_path / "dupes.parquet"
    pd.DataFrame({"UT": ["A", "A"], "pred_countries": [["USA"], ["BRA"]]}).to_parquet(path)

    with pytest.raises(tg.TaxaGeographyError, match="one row per"):
        tg.load_publication_countries(path)


def test_country_loading_reports_a_missing_source(tmp_path: Path) -> None:
    with pytest.raises(tg.TaxaGeographyError, match="not found"):
        tg.load_publication_countries(tmp_path / "absent.parquet")


def test_coverage_counts_mapped_countries_not_merely_non_empty_labels() -> None:
    """`Not Applicable` is a non-empty token but maps nowhere; it must not count."""
    included = pd.DataFrame(
        {
            "UT": ["A", "B", "C", "D"],
            "benchmark_groups": [
                ("Vertebrates",),
                ("Vertebrates",),
                ("Invertebrates",),
                ("Invertebrates",),
            ],
        }
    )
    countries = pd.DataFrame(
        {
            "UT": ["A", "B", "C", "D"],
            "pred_countries": [["USA"], ["Not Applicable"], ["BRA"], []],
        }
    )

    _, _, coverage = tg.taxa_country_specialization(
        included, countries, benchmark_groups=GROUPS, min_support=1, eb_kappa=30
    )

    assert coverage.loc[0, "n_publications"] == 4
    # Only A and C carry a mappable country, so coverage is 2/4 -- never 3/4.
    assert coverage.loc[1, "n_publications"] == 2
    assert coverage.loc[1, "share_of_scope_pct"] == pytest.approx(50.0)


def test_specialization_rejects_a_frame_without_groups() -> None:
    included = pd.DataFrame({"UT": ["A"], "benchmark_groups": [("Fungi",)]})
    countries = pd.DataFrame({"UT": ["A"], "pred_countries": [["USA"]]})

    with pytest.raises(tg.TaxaGeographyError, match="benchmark group"):
        tg.taxa_country_specialization(included, countries, benchmark_groups=GROUPS)


def test_group_slug_is_filename_safe() -> None:
    assert tg.group_slug("Bacteria & archaea") == "bacteria-archaea"
    assert tg.group_slug("Other or unspecified plants") == "other-or-unspecified-plants"
