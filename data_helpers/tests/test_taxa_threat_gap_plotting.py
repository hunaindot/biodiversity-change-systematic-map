"""Tests for the regional evidence-versus-threat figure."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from data_helpers.analysis.taxa import threat_gap_plotting as tgp


def _regional() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "region": list(tgp.REGION_ORDER),
            "threat_share_pct": [27.6, 36.7, 22.0, 13.7],
            "evidence_share_pct": [8.8, 25.7, 41.4, 24.1],
            "evidence_to_threat_ratio": [0.32, 0.70, 1.88, 1.76],
        }
    )


def _regional_trend() -> pd.DataFrame:
    years = list(range(2000, 2026))
    rows = []
    for region, start, end in zip(
        tgp.REGION_ORDER, [6.9, 17.2, 50.4, 25.5], [9.7, 35.3, 34.7, 20.3]
    ):
        for index, year in enumerate(years):
            rows.append(
                {
                    "region": region,
                    "publication_year": year,
                    "evidence_share_pct": start
                    + (end - start) * index / (len(years) - 1),
                }
            )
    return pd.DataFrame(rows)


def test_regional_figure_stacks_both_bars_to_full_height() -> None:
    figure = tgp.plot_regional_representation_and_trend(_regional(), _regional_trend())
    axis = figure.axes[0]

    bars = list(axis.patches)
    assert len(bars) == 8
    left = [b for b in bars if b.get_x() < 0.5]
    assert sum(b.get_height() for b in left) == pytest.approx(100.0, abs=0.05)
    right = [b for b in bars if b.get_x() > 0.5]
    assert sum(b.get_height() for b in right) == pytest.approx(100.0, abs=0.05)
    plt.close(figure)


def test_regional_figure_labels_regions_by_name_only() -> None:
    """Panel A of the taxonomic figure carries bare names; this one must match."""
    figure = tgp.plot_regional_representation_and_trend(_regional(), _regional_trend())
    drawn = {text.get_text() for text in figure.axes[0].texts}

    assert "Africa" in drawn
    assert not any("its share" in text for text in drawn)
    # Bar captions live in the x tick labels, exactly as panel A of the taxa figure.
    captions = [text.get_text() for text in figure.axes[0].get_xticklabels()]
    assert any("Threatened" in text for text in captions)
    assert any("Vertebrate" in text for text in captions)
    plt.close(figure)


def test_regional_figure_draws_a_trend_line_per_region() -> None:
    figure = tgp.plot_regional_representation_and_trend(_regional(), _regional_trend())
    trend_axis = figure.axes[1]

    assert len(trend_axis.lines) == len(tgp.REGION_ORDER)
    labelled = {text.get_text() for text in trend_axis.texts}
    assert set(tgp.REGION_ORDER).issubset(labelled)
    plt.close(figure)


def test_regional_figure_uses_the_taxonomic_house_palette() -> None:
    """Sibling figures: the region colours come from the broad-group palette."""
    assert tgp.REGION_COLORS["Americas"] == "#2E7D32"
    assert tgp.REGION_COLORS["Asia and the Pacific"] == "#6F91C7"
    # Africa takes the one warm hue so it separates from three cool neighbours.
    assert tgp.REGION_COLORS["Africa"] == "#D9954C"


def test_regional_figure_carries_no_y_axis_on_the_bars() -> None:
    """Both bars are 0-100% and every segment states its own percentage."""
    figure = tgp.plot_regional_representation_and_trend(_regional(), _regional_trend())
    axis = figure.axes[0]

    assert list(axis.get_yticks()) == []
    assert not axis.spines["left"].get_visible()
    plt.close(figure)


def test_regional_figure_refuses_to_silently_drop_a_region() -> None:
    frame = _regional()
    frame.loc[len(frame)] = ["Antarctica", 1.0, 1.0, 1.0]

    with pytest.raises(tgp.TaxaThreatGapPlotError, match="missing from region_order"):
        tgp.plot_regional_representation_and_trend(frame, _regional_trend())


def test_regional_figure_rejects_a_frame_without_shares() -> None:
    with pytest.raises(tgp.TaxaThreatGapPlotError, match="Regional frame is missing"):
        tgp.plot_regional_representation_and_trend(
            _regional().drop(columns="threat_share_pct"), _regional_trend()
        )


def test_regional_figure_rejects_a_trend_without_years() -> None:
    with pytest.raises(tgp.TaxaThreatGapPlotError, match="trend frame is missing"):
        tgp.plot_regional_representation_and_trend(
            _regional(), _regional_trend().drop(columns="publication_year")
        )
