"""Tests for the ongoing evidence-versus-threatened-species lens."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from data_helpers.analysis.taxa import threat_gap as tg


def _lq_frame() -> pd.DataFrame:
    """Two countries, one thin, so the support cutoff has something to flag."""
    return pd.DataFrame(
        {
            "iso3": ["USA", "MMR", "USA", "MMR"],
            "broad_group": ["Vertebrates", "Vertebrates", "Plants", "Plants"],
            "n": [800, 12, 200, 8],
            "support": [1000, 20, 1000, 20],
            "within_share": [0.8, 0.6, 0.2, 0.4],
            "global_share": [0.5, 0.5, 0.25, 0.25],
            "lq": [1.6, 1.2, 0.8, 1.6],
            "log2_lq": [np.log2(1.6), np.log2(1.2), np.log2(0.8), np.log2(1.6)],
            "lq_eb": [1.59, 1.05, 0.81, 1.20],
            "log2_lq_eb": [np.log2(1.59), np.log2(1.05), np.log2(0.81), np.log2(1.20)],
            "sufficient": [True, False, True, False],
        }
    )


def _crosswalk() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "iso3": ["USA", "MMR"],
            "country": ["United States", "Myanmar"],
            "region": ["Americas", "Asia and the Pacific"],
            "subregion": ["North America", "South-East Asia"],
        }
    )


def _wdi_parquet(tmp_path: Path, *, drop: tuple[str, ...] = ()) -> Path:
    rows = []
    counts = {
        "USA": {"EN.BIR.THRD.NO": 87, "EN.MAM.THRD.NO": 43, "EN.FSH.THRD.NO": 283,
                "EN.HPT.THRD.NO": 688},
        "MMR": {"EN.BIR.THRD.NO": 51, "EN.MAM.THRD.NO": 47, "EN.FSH.THRD.NO": 40,
                "EN.HPT.THRD.NO": 60},
    }
    labels = {
        "USA": ("United States", "Americas", "North America"),
        "MMR": ("Myanmar", "Asia and the Pacific", "South-East Asia"),
    }
    for iso3, values in counts.items():
        country, region, subregion = labels[iso3]
        for code, value in values.items():
            if (iso3, code) in drop:
                continue
            rows.append(
                {
                    "ipbes_iso3": iso3,
                    "ipbes_country": country,
                    "ipbes_region": region,
                    "ipbes_subregion": subregion,
                    "indicator_code": code,
                    "value": float(value),
                    "year": 2022,
                    "is_aggregate": False,
                }
            )
    capacity = {
        "USA": {"NY.GDP.PCAP.CD": 82769.0, "GB.XPD.RSDV.GD.ZS": 3.6,
                "SP.POP.SCIE.RD.P6": 4821.0, "IP.JRN.ARTC.SC": 455856.0},
        "MMR": {"NY.GDP.PCAP.CD": 1233.0, "IP.JRN.ARTC.SC": 391.0},
    }
    for iso3, values in capacity.items():
        country, region, subregion = labels[iso3]
        for code, value in values.items():
            rows.append(
                {
                    "ipbes_iso3": iso3,
                    "ipbes_country": country,
                    "ipbes_region": region,
                    "ipbes_subregion": subregion,
                    "indicator_code": code,
                    "value": float(value),
                    "year": 2023,
                    "is_aggregate": False,
                }
            )
    # An aggregate entity that must never reach the output.
    rows.append(
        {
            "ipbes_iso3": "WLD",
            "ipbes_country": "World",
            "ipbes_region": "World",
            "ipbes_subregion": "World",
            "indicator_code": "EN.BIR.THRD.NO",
            "value": 9999.0,
            "year": 2022,
            "is_aggregate": True,
        }
    )
    path = tmp_path / "wdi.parquet"
    pd.DataFrame(rows).to_parquet(path)
    return path


def test_evidence_keeps_every_country_and_only_flags_thin_support() -> None:
    frame = tg.evidence_by_country(_lq_frame(), _crosswalk(), group="Vertebrates")

    assert set(frame["iso3"]) == {"USA", "MMR"}
    # The cutoff is reported, never applied: Myanmar survives with the flag false.
    assert frame.set_index("iso3").loc["MMR", "meets_min_support"] is np.False_ or (
        not frame.set_index("iso3").loc["MMR", "meets_min_support"]
    )
    assert frame["share_of_group_evidence_pct"].sum() == pytest.approx(100.0)


def test_evidence_separates_group_publications_from_country_total() -> None:
    frame = tg.evidence_by_country(_lq_frame(), _crosswalk(), group="Vertebrates")
    usa = frame.set_index("iso3").loc["USA"]

    assert usa["n_group_publications"] == 800
    assert usa["n_country_publications"] == 1000


def test_evidence_rejects_an_absent_group() -> None:
    with pytest.raises(tg.TaxaThreatGapError, match="absent"):
        tg.evidence_by_country(_lq_frame(), _crosswalk(), group="Fungi")


def test_threat_counts_drop_aggregates_and_sum_the_right_classes(tmp_path: Path) -> None:
    frame = tg.threatened_species_by_country(_wdi_parquet(tmp_path)).set_index("iso3")

    assert "WLD" not in frame.index
    usa = frame.loc["USA"]
    # Vertebrates include fish; the land subset must not.
    assert usa["threatened_vertebrates"] == 87 + 43 + 283
    assert usa["threatened_vertebrates_land"] == 87 + 43
    assert usa["threatened_total"] == 87 + 43 + 283 + 688
    assert bool(usa["threat_counts_complete"])


def test_threat_counts_keep_incomplete_countries_as_null_not_zero(tmp_path: Path) -> None:
    path = _wdi_parquet(tmp_path, drop=(("MMR", "EN.FSH.THRD.NO"),))
    frame = tg.threatened_species_by_country(path).set_index("iso3")

    mmr = frame.loc["MMR"]
    assert pd.isna(mmr["threatened_fish"])
    assert not bool(mmr["threat_counts_complete"])
    # The land subset is unaffected and stays usable.
    assert mmr["threatened_vertebrates_land"] == 51 + 47


def test_threat_counts_report_a_missing_snapshot(tmp_path: Path) -> None:
    with pytest.raises(tg.TaxaThreatGapError, match="not found"):
        tg.threatened_species_by_country(tmp_path / "absent.parquet")


def _with_threat_only(threatened: pd.DataFrame) -> pd.DataFrame:
    """Add a country holding threatened species but carrying no evidence."""
    return pd.concat(
        [
            threatened,
            threatened.head(1).assign(iso3="MDG", country="Madagascar", region="Africa"),
        ],
        ignore_index=True,
    )


def test_match_defaults_to_countries_present_on_both_sides(tmp_path: Path) -> None:
    evidence = tg.evidence_by_country(_lq_frame(), _crosswalk(), group="Vertebrates")
    threatened = _with_threat_only(tg.threatened_species_by_country(_wdi_parquet(tmp_path)))

    matched = tg.match_evidence_and_threat(evidence, threatened)

    assert set(matched["iso3"]) == {"USA", "MMR"}
    assert set(matched["match"]) == {"both"}


def test_match_records_what_the_inner_join_dropped(tmp_path: Path) -> None:
    """Dropped rows are counted before they go -- skip-but-report, never silent."""
    evidence = tg.evidence_by_country(_lq_frame(), _crosswalk(), group="Vertebrates")
    threatened = _with_threat_only(tg.threatened_species_by_country(_wdi_parquet(tmp_path)))

    matched = tg.match_evidence_and_threat(evidence, threatened)

    assert matched.attrs["n_matched_countries"] == 2
    assert matched.attrs["n_threat_only_countries"] == 1
    assert matched.attrs["threat_only_countries"] == ["MDG"]
    assert matched.attrs["threat_only_threatened_vertebrates_land"] == 87 + 43


def test_match_can_keep_one_sided_countries_on_request(tmp_path: Path) -> None:
    evidence = tg.evidence_by_country(_lq_frame(), _crosswalk(), group="Vertebrates")
    threatened = _with_threat_only(tg.threatened_species_by_country(_wdi_parquet(tmp_path)))

    matched = tg.match_evidence_and_threat(evidence, threatened, how="outer")

    assert set(matched["iso3"]) == {"USA", "MMR", "MDG"}
    assert matched.set_index("iso3").loc["MDG", "match"] == "threat only"
    # One-sided rows carry no share: their denominator would not be comparable.
    assert pd.isna(matched.set_index("iso3").loc["MDG", "matched_evidence_share_pct"])


def test_match_rejects_an_unknown_join_mode(tmp_path: Path) -> None:
    evidence = tg.evidence_by_country(_lq_frame(), _crosswalk(), group="Vertebrates")
    threatened = tg.threatened_species_by_country(_wdi_parquet(tmp_path))

    with pytest.raises(tg.TaxaThreatGapError, match="inner"):
        tg.match_evidence_and_threat(evidence, threatened, how="left")


def test_inner_and_outer_agree_on_every_matched_value(tmp_path: Path) -> None:
    """The join mode selects rows; it must never change a share or a ratio."""
    evidence = tg.evidence_by_country(_lq_frame(), _crosswalk(), group="Vertebrates")
    threatened = _with_threat_only(tg.threatened_species_by_country(_wdi_parquet(tmp_path)))

    inner = tg.match_evidence_and_threat(evidence, threatened).set_index("iso3")
    outer = tg.match_evidence_and_threat(evidence, threatened, how="outer").set_index("iso3")

    column = "evidence_to_threatened_vertebrates_land_ratio"
    pd.testing.assert_series_equal(inner[column], outer.loc[inner.index, column])


def test_match_labels_countries_present_on_only_one_side(tmp_path: Path) -> None:
    """One-sided rows must keep their names -- they are the rows worth reading."""
    evidence = tg.evidence_by_country(_lq_frame(), _crosswalk(), group="Vertebrates")
    # An evidence-only country: studied, but absent from the World Bank snapshot.
    evidence = pd.concat(
        [
            evidence,
            evidence.head(1).assign(
                iso3="TWN", country="Taiwan", region="Asia and the Pacific",
                subregion="North-East Asia", n_group_publications=210,
            ),
        ],
        ignore_index=True,
    )
    threatened = tg.threatened_species_by_country(_wdi_parquet(tmp_path))

    matched = tg.match_evidence_and_threat(evidence, threatened, how="outer").set_index(
        "iso3"
    )

    assert matched.loc["TWN", "match"] == "evidence only"
    assert matched.loc["TWN", "country"] == "Taiwan"
    assert matched.loc["TWN", "region"] == "Asia and the Pacific"
    # Matched rows keep exactly one label column, not a suffixed pair.
    assert "country_evidence" not in matched.columns
    assert matched.loc["USA", "country"] == "United States"


def test_match_ratio_is_evidence_share_over_threat_share(tmp_path: Path) -> None:
    evidence = tg.evidence_by_country(_lq_frame(), _crosswalk(), group="Vertebrates")
    threatened = tg.threatened_species_by_country(_wdi_parquet(tmp_path))

    matched = tg.match_evidence_and_threat(evidence, threatened).set_index("iso3")

    evidence_share = 800 / (800 + 12) * 100
    threat_share = (87 + 43) / (87 + 43 + 51 + 47) * 100
    assert matched.loc["USA", "evidence_to_threatened_vertebrates_land_ratio"] == (
        pytest.approx(evidence_share / threat_share)
    )
    # Both sides sum to 100% over the matched countries.
    assert matched["matched_evidence_share_pct"].sum() == pytest.approx(100.0)
    assert matched["matched_threatened_vertebrates_land_share_pct"].sum() == (
        pytest.approx(100.0)
    )


def test_match_rejects_a_missing_threat_column(tmp_path: Path) -> None:
    evidence = tg.evidence_by_country(_lq_frame(), _crosswalk(), group="Vertebrates")
    threatened = tg.threatened_species_by_country(_wdi_parquet(tmp_path))

    with pytest.raises(tg.TaxaThreatGapError, match="missing column"):
        tg.match_evidence_and_threat(evidence, threatened, threat_columns=("absent",))


def test_export_columns_drop_intermediates_but_keep_the_headline(tmp_path: Path) -> None:
    evidence = tg.evidence_by_country(_lq_frame(), _crosswalk(), group="Vertebrates")
    trimmed = tg.select_export_columns(evidence, "evidence-by-country")

    assert list(trimmed.columns) == list(tg.EXPORT_COLUMNS["evidence-by-country"])
    # Constant-down-the-column fields are facts about the table, not variables in it.
    assert "broad_group" not in trimmed.columns
    assert "corpus_share_pct" not in trimmed.columns
    # The counts the table exists for survive.
    assert trimmed["n_group_publications"].sum() == 812


def test_export_selection_raises_rather_than_silently_dropping(tmp_path: Path) -> None:
    evidence = tg.evidence_by_country(_lq_frame(), _crosswalk(), group="Vertebrates")

    with pytest.raises(tg.TaxaThreatGapError, match="missing export columns"):
        tg.select_export_columns(evidence.drop(columns="lq"), "evidence-by-country")
    with pytest.raises(tg.TaxaThreatGapError, match="No export column set"):
        tg.select_export_columns(evidence, "not-a-table")


def test_capacity_covariates_load_with_partial_coverage(tmp_path: Path) -> None:
    """Thin coverage is expected; a missing indicator stays null, never zero."""
    capacity = tg.research_capacity_by_country(_wdi_parquet(tmp_path)).set_index("iso3")

    assert capacity.loc["USA", "researchers_per_million"] == pytest.approx(4821.0)
    assert capacity.loc["USA", "n_capacity_indicators"] == 4
    # Myanmar carries only two of the four; the rest must be null, not zero.
    assert pd.isna(capacity.loc["MMR", "researchers_per_million"])
    assert pd.isna(capacity.loc["MMR", "rd_expenditure_pct_gdp"])
    assert capacity.loc["MMR", "n_capacity_indicators"] == 2
    assert "WLD" not in capacity.index


def test_every_export_set_is_satisfiable_by_its_builder(tmp_path: Path) -> None:
    """Each column set must actually be selectable from the frame it describes."""
    evidence = tg.evidence_by_country(_lq_frame(), _crosswalk(), group="Vertebrates")
    threatened = tg.threatened_species_by_country(_wdi_parquet(tmp_path))
    capacity = tg.research_capacity_by_country(_wdi_parquet(tmp_path))
    matched = tg.match_evidence_and_threat(evidence, threatened, covariates=capacity)

    for stem, frame in (
        ("evidence-by-country", evidence),
        ("threatened-species-by-country", threatened),
        ("evidence-vs-threatened", matched),
    ):
        assert not tg.select_export_columns(frame, stem).empty


def test_region_summary_scores_aggregated_totals(tmp_path: Path) -> None:
    evidence = tg.evidence_by_country(_lq_frame(), _crosswalk(), group="Vertebrates")
    threatened = tg.threatened_species_by_country(_wdi_parquet(tmp_path))
    matched = tg.match_evidence_and_threat(evidence, threatened)

    summary = tg.summarise_gap_by_region(matched).set_index("region")

    assert summary.loc["Americas", "n_group_publications"] == 800
    assert summary.loc["Americas", "threatened_species"] == 87 + 43
    assert summary["evidence_share_pct"].sum() == pytest.approx(100.0)
    # Sorted most- to least-studied relative to threat.
    assert summary.index[0] == "Americas"


def _regional_trend_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Two years, two regions, with CHN carrying most of one region's apparent rise.

    APAC goes from 1 to 4 publications across the years; three of those four extra come
    from CHN alone, so excluding CHN should flatten most, not all, of the apparent slope.
    """
    included = pd.DataFrame(
        {
            "UT": [f"P{i}" for i in range(1, 8)],
            "publication_year": [2000, 2000, 2025, 2025, 2025, 2025, 2025],
            "benchmark_groups": [("Vertebrates",)] * 7,
        }
    )
    countries = pd.DataFrame(
        {
            "UT": [f"P{i}" for i in range(1, 8)],
            "pred_countries": [
                ["USA"], ["MMR"],
                ["USA"], ["USA"], ["MMR"], ["CHN"], ["CHN"],
            ],
        }
    )
    regional = pd.DataFrame(
        {
            "region": ["Americas", "Asia and the Pacific"],
            "threat_share_pct": [50.0, 50.0],
        }
    )
    crosswalk = pd.DataFrame(
        {
            "iso3": ["USA", "MMR", "CHN"],
            "region": ["Americas", "Asia and the Pacific", "Asia and the Pacific"],
        }
    )
    return included, countries, regional, crosswalk


def test_regional_trend_excludes_a_named_country() -> None:
    included, countries, regional, crosswalk = _regional_trend_inputs()

    full = tg.regional_evidence_trend(
        included, countries, regional, crosswalk, group="Vertebrates"
    )
    without_china = tg.regional_evidence_trend(
        included, countries, regional, crosswalk, group="Vertebrates", exclude_iso3=["CHN"],
    )

    apac_2025_full = full[
        (full["region"] == "Asia and the Pacific") & (full["publication_year"] == 2025)
    ]["n_publications"].iloc[0]
    apac_2025_excl = without_china[
        (without_china["region"] == "Asia and the Pacific")
        & (without_china["publication_year"] == 2025)
    ]["n_publications"].iloc[0]

    assert apac_2025_full == 3  # MMR + 2x CHN
    assert apac_2025_excl == 1  # MMR only
    # The Americas side is untouched by excluding an Asia-Pacific country.
    americas_full = full[
        (full["region"] == "Americas") & (full["publication_year"] == 2025)
    ]["n_publications"].iloc[0]
    americas_excl = without_china[
        (without_china["region"] == "Americas") & (without_china["publication_year"] == 2025)
    ]["n_publications"].iloc[0]
    assert americas_full == americas_excl == 2


def test_regional_trend_exclusion_flattens_the_slope() -> None:
    included, countries, regional, crosswalk = _regional_trend_inputs()

    full = tg.summarise_regional_trend(
        tg.regional_evidence_trend(included, countries, regional, crosswalk, group="Vertebrates")
    ).set_index("region")
    without_china = tg.summarise_regional_trend(
        tg.regional_evidence_trend(
            included, countries, regional, crosswalk, group="Vertebrates", exclude_iso3=["CHN"],
        )
    ).set_index("region")

    apac_row = "Asia and the Pacific"
    assert full.loc[apac_row, "slope_pp_per_decade"] > without_china.loc[
        apac_row, "slope_pp_per_decade"
    ]


def test_regional_trend_exclusion_rejects_emptying_the_frame() -> None:
    included, countries, regional, crosswalk = _regional_trend_inputs()

    with pytest.raises(tg.TaxaThreatGapError, match="left no publications"):
        tg.regional_evidence_trend(
            included, countries, regional, crosswalk,
            group="Vertebrates", exclude_iso3=["USA", "MMR", "CHN"],
        )


def test_regional_trend_exclusion_default_is_a_no_op() -> None:
    included, countries, regional, crosswalk = _regional_trend_inputs()

    default = tg.regional_evidence_trend(
        included, countries, regional, crosswalk, group="Vertebrates"
    )
    explicit_empty = tg.regional_evidence_trend(
        included, countries, regional, crosswalk, group="Vertebrates", exclude_iso3=[]
    )
    pd.testing.assert_frame_equal(default, explicit_empty)
