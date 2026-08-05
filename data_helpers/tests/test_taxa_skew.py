"""Tests for publication-level taxonomic skew calculations."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from data_helpers.analysis.taxa import skew as ts


GROUP_ORDER = (
    "Vertebrates",
    "Invertebrates",
    "Plants",
    "Fungi",
    "Other",
    "Unresolved",
)
BENCHMARK_GROUPS = GROUP_ORDER[:-1]


def _match_item(
    name: str,
    *,
    status: str,
    group: str | None,
    reason: str,
) -> dict:
    return {
        "canonical_name": name,
        "status": status,
        "group_assignments": {
            "broad": {
                "group": group,
                "reason": reason,
            }
        },
    }


def _write_sources(tmp_path: Path) -> dict[str, Path]:
    uts = ["A", "B", "C", "D", "E", "F"]
    taxa_items = [
        [{"taxon_rank": "species", "canonical_name": "Example alpha"}],
        [{"taxon_rank": "kingdom", "canonical_name": "Not applicable"}],
        [{"taxon_rank": "kingdom", "canonical_name": "Unclear"}],
        [{"taxon_rank": "species", "canonical_name": "Example delta"}],
        [{"taxon_rank": "species", "canonical_name": "Example epsilon"}],
        [],
    ]
    matches = [
        [
            _match_item(
                "Example alpha",
                status="exact",
                group="Vertebrates",
                reason="matched_rule",
            )
        ],
        [
            _match_item(
                "Not applicable",
                status="special_value",
                group=None,
                reason="not_applicable",
            )
        ],
        [
            _match_item(
                "Unclear",
                status="special_value",
                group=None,
                reason="ineligible_match_status:special_value",
            )
        ],
        [
            _match_item(
                "Example delta",
                status="exact",
                group="Unresolved",
                reason="accepted_insufficient_hierarchy",
            )
        ],
        [
            _match_item(
                "Example epsilon",
                status="no_match",
                group=None,
                reason="ineligible_match_status:no_match",
            )
        ],
        [],
    ]
    taxa = pd.DataFrame(
        {
            "UT": uts,
            "publication_year": [2020] * 6,
            "broad_taxa_groups": [
                json.dumps(["Plants", "Vertebrates"]),
                "[]",
                "[]",
                json.dumps(["Unresolved"]),
                "[]",
                "[]",
            ],
            "llm_taxa_json": [json.dumps(items) for items in taxa_items],
            "taxa_match_status_json": [json.dumps(items) for items in matches],
            "taxa_record_status": [
                "resolved",
                "unresolved",
                "unresolved",
                "resolved",
                "unresolved",
                "unresolved",
            ],
            "n_llm_taxa": [len(items) for items in taxa_items],
            "n_taxa_matched": [1, 0, 0, 1, 0, 0],
            "n_taxa_unresolved": [0, 1, 1, 0, 1, 0],
            "n_taxa_api_failed": [0] * 6,
        }
    )
    frames = {
        "taxa": taxa,
        "driver": pd.DataFrame(
            {"UT": uts, "driver": [json.dumps(["Pollution"])] * 6}
        ),
        "threats_l0": pd.DataFrame(
            {"UT": uts, "pred_threat_l0": [json.dumps(["Pollution"])] * 6}
        ),
        "realm": pd.DataFrame(
            {"UT": uts, "realm": [json.dumps(["Terrestrial"])] * 6}
        ),
    }
    paths: dict[str, Path] = {}
    for name, frame in frames.items():
        path = tmp_path / f"{name}.csv"
        frame.to_csv(path, index=False)
        paths[name] = path
    return paths


def test_source_loading_preserves_exact_ut_grain(tmp_path: Path) -> None:
    sources = ts.load_coding_sources(_write_sources(tmp_path))

    assert len(sources.articles) == 6
    assert sources.articles["UT"].tolist() == ["A", "B", "C", "D", "E", "F"]
    assert sources.audit["unique_UT"].eq(6).all()
    assert sources.audit["same_UT_order_as_taxa"].all()
    assert sources.audit[
        ["taxa_UT_missing_from_source", "source_UT_missing_from_taxa"]
    ].eq(0).all().all()


def test_source_loading_rejects_key_set_mismatch(tmp_path: Path) -> None:
    paths = _write_sources(tmp_path)
    realm = pd.read_csv(paths["realm"])
    realm.loc[5, "UT"] = "G"
    realm.to_csv(paths["realm"], index=False)

    with pytest.raises(ts.TaxaSkewError, match="same UT key set"):
        ts.load_coding_sources(paths)


def test_preparation_accounts_for_every_article_and_fractionalizes(
    tmp_path: Path,
) -> None:
    sources = ts.load_coding_sources(_write_sources(tmp_path))
    evidence = ts.prepare_taxa_skew_evidence(
        sources,
        broad_group_order=GROUP_ORDER,
        benchmark_groups=BENCHMARK_GROUPS,
        unresolved_group="Unresolved",
        eligible_match_statuses=("exact", "fuzzy_accepted"),
    )

    assert len(evidence.articles) == 6
    assert len(evidence.included) == 1
    assert evidence.inclusion_audit["n_publications"].sum() == 6
    assert (
        evidence.attributions.groupby("UT")["fractional_publication_weight"]
        .sum()
        .eq(1)
        .all()
    )
    weights = evidence.attributions.set_index("broad_group")[
        "fractional_publication_weight"
    ]
    assert weights["Vertebrates"] == pytest.approx(0.5)
    assert weights["Plants"] == pytest.approx(0.5)
    statuses = evidence.match_status_audit.set_index("match_status")
    assert statuses.at["exact", "eligible_for_grouping"]
    assert not statuses.at["no_match", "eligible_for_grouping"]


def test_analysis_renormalizes_benchmark_and_reports_uncertainty(
    tmp_path: Path,
) -> None:
    sources = ts.load_coding_sources(_write_sources(tmp_path))
    evidence = ts.prepare_taxa_skew_evidence(
        sources,
        broad_group_order=GROUP_ORDER,
        benchmark_groups=BENCHMARK_GROUPS,
        unresolved_group="Unresolved",
        eligible_match_statuses=("exact", "fuzzy_accepted"),
    )
    benchmark = ts.DescribedDiversity(
        counts=pd.DataFrame(
            {
                "broad_group": GROUP_ORDER,
                "described_species_count": [1, 6, 2, 1, 1, 4],
                "described_species_share": np.array([1, 6, 2, 1, 1, 4]) / 15,
                "described_species_share_pct": (
                    np.array([1, 6, 2, 1, 1, 4]) / 15 * 100
                ),
            }
        ),
        audit=pd.DataFrame(),
    )
    analysis = ts.analyze_taxonomic_skew(
        evidence,
        benchmark,
        benchmark_groups=BENCHMARK_GROUPS,
        n_bootstrap=100,
        seed=7,
    )

    comparison = analysis.comparison.set_index("broad_group")
    assert comparison["described_species_share_pct"].sum() == pytest.approx(100)
    assert comparison["fractional_attention_share_pct"].sum() == pytest.approx(100)
    assert comparison.at["Vertebrates", "fractional_attention_share_pct"] == 50
    assert comparison.at["Plants", "fractional_attention_share_pct"] == 50
    assert analysis.bootstrap_intervals["attention_ci_low_pct"].notna().all()
    assert (
        analysis.allocation_sensitivity[
            "fractional_article_balanced_share_pct"
        ].sum()
        == pytest.approx(100)
    )


def test_focus_rebalances_each_publication_within_requested_groups(
    tmp_path: Path,
) -> None:
    sources = ts.load_coding_sources(_write_sources(tmp_path))
    evidence = ts.prepare_taxa_skew_evidence(
        sources,
        broad_group_order=GROUP_ORDER,
        benchmark_groups=BENCHMARK_GROUPS,
        unresolved_group="Unresolved",
        eligible_match_statuses=("exact", "fuzzy_accepted"),
    )

    focused = ts.focus_taxa_skew_evidence(
        evidence,
        benchmark_groups=("Vertebrates", "Invertebrates"),
    )

    assert len(focused.included) == 1
    assert focused.included.iloc[0]["benchmark_groups"] == ("Vertebrates",)
    assert focused.attributions["fractional_publication_weight"].sum() == pytest.approx(
        1
    )
    audit = focused.group_audit.set_index("broad_group")
    assert audit.at["Vertebrates", "fractional_attention_share_pct"] == pytest.approx(
        100
    )
    assert audit.at["Invertebrates", "fractional_attention_share_pct"] == pytest.approx(
        0
    )


def _prepared_articles() -> pd.DataFrame:
    """Four publications spanning both directions and the year boundary."""
    rows = [
        ("A", 2010, "negative", ("Vertebrates",)),
        ("B", 2010, "positive", ("Invertebrates",)),
        ("C", 1998, "negative", ("Plants",)),
        ("D", 2026, "negative", ("Fungi",)),
    ]
    return pd.DataFrame(
        {
            "UT": [r[0] for r in rows],
            "publication_year": [r[1] for r in rows],
            "s2_dir": [r[2] for r in rows],
            "broad_groups": [r[3] for r in rows],
            "broad_groups_all": [r[3] for r in rows],
            "taxa_broad_inclusion_state": [ts.INCLUSION_ORDER[0]] * len(rows),
        }
    )


def _empty_audit() -> pd.DataFrame:
    return pd.DataFrame()


def _prepare(articles: pd.DataFrame, **scope):
    return ts.prepare_taxa_skew_from_prepared(
        articles,
        benchmark_groups=BENCHMARK_GROUPS,
        unresolved_group="Unresolved",
        match_status_audit=_empty_audit(),
        group_reason_audit=_empty_audit(),
        special_value_audit=_empty_audit(),
        auxiliary_label_audit=_empty_audit(),
        **scope,
    )


def test_prepared_scope_defaults_to_the_whole_corpus() -> None:
    evidence = _prepare(_prepared_articles())

    assert set(evidence.included["UT"]) == {"A", "B", "C", "D"}


def test_prepared_scope_restricts_direction_and_year_window() -> None:
    evidence = _prepare(
        _prepared_articles(),
        direction="negative",
        start_year=2000,
        end_year=2025,
    )

    # B is positive-direction, C precedes the window, D follows it.
    assert set(evidence.included["UT"]) == {"A"}


def test_prepared_scope_requires_direction_column_when_filtering() -> None:
    articles = _prepared_articles().drop(columns=["s2_dir"])

    with pytest.raises(ts.TaxaSkewError, match="s2_dir"):
        _prepare(articles, direction="negative")


def test_prepared_scope_rejects_an_empty_universe() -> None:
    with pytest.raises(ts.TaxaSkewError, match="analytical scope"):
        _prepare(_prepared_articles(), direction="mixed")


def _trend_articles() -> pd.DataFrame:
    """Two years; 2001 adds a multi-group publication so weights must split."""
    rows = [
        ("A", 2000, ("Vertebrates",)),
        ("B", 2000, ("Invertebrates",)),
        ("C", 2001, ("Vertebrates",)),
        ("D", 2001, ("Vertebrates", "Invertebrates")),
    ]
    return pd.DataFrame(
        {
            "UT": [r[0] for r in rows],
            "publication_year": [r[1] for r in rows],
            "benchmark_groups": [r[2] for r in rows],
        }
    )


def test_trend_splits_multi_group_publications_and_closes_each_year() -> None:
    trend = ts.taxonomic_attention_trend(
        _trend_articles(), benchmark_groups=("Vertebrates", "Invertebrates")
    )

    # 2001: A vertebrate-only publication plus a half-half one -> 1.5 vs 0.5.
    counts = trend.set_index(["publication_year", "broad_group"])[
        "effective_publication_count"
    ]
    assert counts.loc[(2001, "Vertebrates")] == pytest.approx(1.5)
    assert counts.loc[(2001, "Invertebrates")] == pytest.approx(0.5)

    shares = trend.groupby("publication_year")["fractional_attention_share_pct"].sum()
    assert np.allclose(shares.to_numpy(), 100.0)


def test_trend_renormalises_over_a_subset_without_dropping_publications() -> None:
    trend = ts.taxonomic_attention_trend(
        _trend_articles(),
        benchmark_groups=("Vertebrates", "Invertebrates"),
        renormalise_over=("Vertebrates",),
    )

    # D still counts, at full weight, because Invertebrates left the denominator.
    assert set(trend["broad_group"]) == {"Vertebrates"}
    counts = trend.set_index("publication_year")["effective_publication_count"]
    assert counts.loc[2001] == pytest.approx(2.0)


def test_trend_single_group_filter_drops_multi_group_publications() -> None:
    trend = ts.taxonomic_attention_trend(
        _trend_articles(),
        benchmark_groups=("Vertebrates", "Invertebrates"),
        single_group_only=True,
    )

    counts = trend.set_index(["publication_year", "broad_group"])[
        "effective_publication_count"
    ]
    assert counts.loc[(2001, "Vertebrates")] == pytest.approx(1.0)
    assert counts.loc[(2001, "Invertebrates")] == pytest.approx(0.0)


def test_trend_rejects_non_benchmark_renormalisation_groups() -> None:
    with pytest.raises(ts.TaxaSkewError, match="non-benchmark"):
        ts.taxonomic_attention_trend(
            _trend_articles(),
            benchmark_groups=("Vertebrates", "Invertebrates"),
            renormalise_over=("Plants",),
        )


def test_trend_summary_reports_slope_and_both_representation_ratios() -> None:
    trend = pd.DataFrame(
        {
            "publication_year": [2000, 2010, 2000, 2010],
            "broad_group": ["Vertebrates"] * 2 + ["Invertebrates"] * 2,
            "fractional_attention_share_pct": [40.0, 30.0, 20.0, 30.0],
            "effective_publication_count": [4.0, 3.0, 2.0, 3.0],
        }
    )

    summary = ts.summarise_attention_trend(
        trend, described_shares={"Vertebrates": 5.0, "Invertebrates": 60.0}
    ).set_index("broad_group")

    # Ten points lost across ten years is minus ten points per decade.
    assert summary.loc["Vertebrates", "slope_pp_per_decade"] == pytest.approx(-10.0)
    assert summary.loc["Vertebrates", "change_pp"] == pytest.approx(-10.0)
    assert summary.loc["Vertebrates", "start_representation_ratio"] == pytest.approx(8.0)
    assert summary.loc["Vertebrates", "end_representation_ratio"] == pytest.approx(6.0)
    assert summary.loc["Invertebrates", "slope_pp_per_decade"] == pytest.approx(10.0)
