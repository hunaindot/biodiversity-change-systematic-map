"""Tests for the additive IPBES geographic-attention preparation."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data_helpers.analysis.geo.attention import (
    GeographyAttentionError,
    filter_biodiversity_loss_publications,
    prepare_geography_attention,
)


def _crosswalk() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "iso3": "AAA",
                "country": "Aland",
                "region": "Africa",
                "subregion": "West",
            },
            {
                "iso3": "BBB",
                "country": "Bland",
                "region": "Americas",
                "subregion": "North",
            },
            {
                "iso3": "",
                "country": "C land",
                "region": "Americas",
                "subregion": "North",
            },
            {
                "iso3": "DDD",
                "country": "Dland",
                "region": "Asia and the Pacific",
                "subregion": "East",
            },
        ]
    )


def _evidence() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "UT": ["A", "B", "C", "D", "E", "F", "G", "H"],
            "publication_year": [2000, "2001", 2002, 2003, 2004, 1999, 2002, 2005],
            "s2_dir": [
                "negative",
                "negative",
                "negative",
                "negative",
                "negative",
                "negative",
                "positive",
                "negative",
            ],
            "pred_countries": [
                ["AAA", "BBB", "aaa"],
                '["AAA"]',
                ["Not Applicable"],
                [],
                ["XXX"],
                ["BBB"],
                ["BBB"],
                ["Unclear", "DDD"],
            ],
        }
    )


def _audit(result) -> pd.Series:
    return result.audit.set_index("metric")["value"]


def test_preparation_fractionalizes_and_retains_every_mapping_leaf() -> None:
    result = prepare_geography_attention(
        _evidence(), crosswalk=_crosswalk(), low_evidence_threshold=2
    )

    assert result.assignments[["UT", "iso3"]].values.tolist() == [
        ["A", "AAA"],
        ["A", "BBB"],
        ["B", "AAA"],
        ["H", "DDD"],
    ]
    assert result.assignments.groupby("UT")["fractional_weight"].sum().eq(1).all()
    assert result.assignments.set_index(["UT", "iso3"]).loc[
        ("A", "AAA"), "fractional_weight"
    ] == pytest.approx(0.5)

    countries = result.countries.set_index("country")
    assert len(countries) == 4
    assert countries.loc["Aland", "whole_publications"] == 2
    assert countries.loc[
        "Aland", "fractional_publication_equivalent"
    ] == pytest.approx(1.5)
    assert countries.loc[
        "Bland", "fractional_publication_equivalent"
    ] == pytest.approx(0.5)
    assert countries.loc[
        "Dland", "fractional_publication_equivalent"
    ] == pytest.approx(1.0)
    assert countries.loc["Aland", "evidence_status"] == "observed"
    assert not countries.loc["Aland", "below_evidence_threshold"]
    assert countries.loc["Bland", "below_evidence_threshold"]
    assert countries.loc["C land", "evidence_status"] == "unresolvable_key"
    assert pd.isna(countries.loc["C land", "whole_publications"])
    assert pd.isna(countries.loc["C land", "fractional_publication_equivalent"])
    assert pd.isna(countries.loc["C land", "attention_share_pct"])
    assert pd.isna(countries.loc["C land", "below_evidence_threshold"])
    assert result.countries[
        "fractional_publication_equivalent"
    ].sum() == pytest.approx(3.0)
    assert result.countries["attention_share_pct"].sum() == pytest.approx(100.0)


def test_hierarchy_is_additive_but_preserves_distinct_whole_counts() -> None:
    result = prepare_geography_attention(_evidence(), crosswalk=_crosswalk())
    hierarchy = result.hierarchy
    root = hierarchy.loc[hierarchy["node_type"].eq("root")].iloc[0]
    regions = hierarchy.loc[hierarchy["node_type"].eq("region")].set_index("label")

    assert root["whole_publications"] == 3
    assert root["fractional_publication_equivalent"] == pytest.approx(3.0)
    assert regions.loc["Africa", "whole_publications"] == 2
    assert regions.loc["Americas", "whole_publications"] == 1
    assert regions.loc["Asia and the Pacific", "whole_publications"] == 1
    assert regions["whole_publications"].sum() == 4  # cross-region paper A
    assert regions["fractional_publication_equivalent"].sum() == pytest.approx(3.0)

    weights = hierarchy.set_index("node_id")["fractional_publication_equivalent"]
    child_sums = (
        hierarchy.loc[hierarchy["depth"].gt(0)]
        .groupby("parent_id")["fractional_publication_equivalent"]
        .sum()
    )
    assert np.allclose(child_sums.to_numpy(), child_sums.index.map(weights))


def test_coverage_and_audits_keep_unmapped_evidence_explicit() -> None:
    result = prepare_geography_attention(_evidence(), crosswalk=_crosswalk())
    coverage = result.coverage.set_index("coverage_status")
    audit = _audit(result)

    assert coverage.loc["mapped_country", "publication_count"] == 3
    assert coverage.loc["no_mapped_country", "publication_count"] == 2
    assert coverage["publication_count"].sum() == 5
    assert coverage["share_pct"].tolist() == pytest.approx([60.0, 40.0])
    assert audit["input_publications"] == 8
    assert audit["direction_matching_publications"] == 7
    assert audit["window_publications_before_country_validation"] == 6
    assert audit["complete_case_excluded_publications"] == 1
    assert audit["analysis_publications"] == 5
    assert audit["empty_country_list_publications"] == 1
    assert audit["mentions_mapped"] == 5
    assert audit["duplicate_mapped_mentions_removed"] == 1
    assert audit["mentions_not_applicable"] == 1
    assert audit["mentions_unclear"] == 1
    assert audit["mentions_unresolved"] == 0
    assert audit["unresolved_mentions_before_exclusion"] == 1
    assert audit["unresolved_token_publications"] == 1
    assert result.coverage_reasons.to_dict("records") == [
        {
            "coverage_reason": "empty_country_list",
            "publication_count": 1,
            "share_of_no_mapped_pct": pytest.approx(50.0),
            "share_of_analysis_pct": pytest.approx(20.0),
        },
        {
            "coverage_reason": "not_applicable",
            "publication_count": 1,
            "share_of_no_mapped_pct": pytest.approx(50.0),
            "share_of_analysis_pct": pytest.approx(20.0),
        },
    ]
    assert result.unresolved_tokens.to_dict("records") == [
        {"token": "XXX", "mention_count": 1, "publication_count": 1}
    ]
    assert result.excluded_publications.to_dict("records") == [
        {
            "UT": "E",
            "token": "XXX",
            "exclusion_reason": "unresolved_country_token",
        }
    ]


def test_complete_case_exclusion_removes_valid_codes_from_mixed_record() -> None:
    evidence = _evidence()
    evidence.loc[evidence["UT"].eq("E"), "pred_countries"] = pd.Series(
        [["AAA", "XXX"]],
        index=evidence.index[evidence["UT"].eq("E")],
    )

    result = prepare_geography_attention(evidence, crosswalk=_crosswalk())

    assert "E" not in set(result.assignments["UT"])
    assert _audit(result)[
        "excluded_publications_with_mapped_country_before_exclusion"
    ] == 1


def test_filter_helper_enforces_prepared_ut_grain() -> None:
    filtered = filter_biodiversity_loss_publications(_evidence())
    assert filtered["UT"].tolist() == ["A", "B", "C", "D", "E", "H"]
    assert str(filtered["publication_year"].dtype) == "Int64"

    duplicated = pd.concat([_evidence(), _evidence().iloc[[0]]], ignore_index=True)
    with pytest.raises(GeographyAttentionError, match="one non-missing row per UT"):
        filter_biodiversity_loss_publications(duplicated)


def test_crosswalk_validation_rejects_ambiguous_or_invalid_keys() -> None:
    duplicate = pd.concat([_crosswalk(), _crosswalk().iloc[[0]]], ignore_index=True)
    with pytest.raises(GeographyAttentionError, match="country paths must be unique"):
        prepare_geography_attention(_evidence(), crosswalk=duplicate)

    invalid = _crosswalk()
    invalid.loc[0, "iso3"] = "AA"
    with pytest.raises(GeographyAttentionError, match="three ASCII letters"):
        prepare_geography_attention(_evidence(), crosswalk=invalid)


def test_repository_crosswalk_keeps_all_ipbes_leaves_including_blank_iso3() -> None:
    one_publication = pd.DataFrame(
        {
            "UT": ["A"],
            "publication_year": [2025],
            "s2_dir": ["negative"],
            "pred_countries": [["USA"]],
        }
    )
    result = prepare_geography_attention(one_publication)

    assert len(result.countries) == 257
    assert result.countries["key_status"].value_counts().to_dict() == {
        "valid_iso3": 249,
        "unresolvable_key": 8,
    }
    assert result.hierarchy["node_type"].value_counts().to_dict() == {
        "country": 257,
        "subregion": 18,
        "region": 5,
        "root": 1,
    }
    assert result.countries["evidence_status"].value_counts().to_dict() == {
        "zero_captured": 248,
        "unresolvable_key": 8,
        "observed": 1,
    }
    no_key = result.countries["key_status"].eq("unresolvable_key")
    assert result.countries.loc[
        no_key,
        [
            "whole_publications",
            "fractional_publication_equivalent",
            "attention_share_pct",
            "below_evidence_threshold",
        ],
    ].isna().all().all()
