"""Tests for the taxonomic-skew publication figure."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from data_helpers.analysis.taxa import skew_plotting as plotting


GROUPS = ("Vertebrates", "Invertebrates", "Plants", "Fungi", "Other")
COLORS = {
    "Vertebrates": "#2E7D32",
    "Invertebrates": "#6F91C7",
    "Plants": "#D9954C",
    "Fungi": "#8C6BB1",
    "Other": "#7F8C8D",
}


def test_taxonomic_skew_figure_has_two_directly_labelled_panels() -> None:
    comparison = pd.DataFrame(
        {
            "broad_group": GROUPS,
            "effective_publication_count": [280, 170, 420, 40, 90],
            "fractional_attention_share_pct": [28, 17, 42, 4, 9],
            "attention_ci_low_pct": [27.8, 16.8, 41.8, 3.8, 8.8],
            "attention_ci_high_pct": [28.2, 17.2, 42.2, 4.2, 9.2],
            "described_species_share_pct": [5, 65, 17, 7, 6],
            "representation_ratio": [5.6, 17 / 65, 42 / 17, 4 / 7, 1.5],
            "log2_representation_ratio": [
                2.485,
                -1.936,
                1.305,
                -0.807,
                0.585,
            ],
        }
    )

    figure = plotting.plot_taxonomic_skew(
        comparison,
        group_order=GROUPS,
        group_colors=COLORS,
    )

    assert len(figure.axes) == 2
    assert len(figure.axes[0].get_yticklabels()) == len(GROUPS)
    assert len(figure.axes[1].get_yticklabels()) == len(GROUPS)
    assert figure.axes[0].get_xlim()[0] == 0
    assert figure.axes[1].get_xlabel() == "Representation ratio (log2 scale)"
    plt.close(figure)


def _representation_comparison() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "broad_group": GROUPS,
            "described_species_share_pct": [5.0, 65.0, 17.0, 7.0, 6.0],
            "fractional_attention_share_pct": [35.0, 20.0, 34.0, 3.0, 8.0],
        }
    )


def _representation_trend() -> pd.DataFrame:
    years = [2000, 2010, 2020]
    return pd.DataFrame(
        {
            "publication_year": years * len(GROUPS),
            "broad_group": [g for g in GROUPS for _ in years],
            "fractional_attention_share_pct": [
                37.0, 35.0, 32.0,
                22.0, 20.0, 19.0,
                32.0, 34.0, 35.0,
                2.5, 3.0, 3.4,
                6.5, 8.0, 10.0,
            ],
        }
    )


STACK_ORDER = ("Invertebrates", "Fungi", "Other", "Plants", "Vertebrates")


def test_representation_figure_shares_one_axis_and_omits_the_residual_group() -> None:
    figure = plotting.plot_representation_and_trend(
        _representation_comparison(),
        _representation_trend(),
        group_order=STACK_ORDER,
        group_colors=COLORS,
        residual_group="Other",
    )

    bars, trend = figure.axes
    # Both stacked bars live on one axes, so the 0-100% scale is shared by construction.
    assert bars.get_ylim() == (0, 100)
    assert [t.get_text() for t in bars.get_xticklabels()] == [
        "Described\nspecies",
        "Research\nattention",
    ]
    # Four groups drawn, not five: the residual bucket is excluded from panel b.
    assert len(trend.get_lines()) == len(GROUPS) - 1
    # The trend axis starts at zero, so a small slope is never visually inflated.
    assert trend.get_ylim()[0] == 0
    plt.close(figure)


def test_representation_figure_labels_every_group_directly() -> None:
    figure = plotting.plot_representation_and_trend(
        _representation_comparison(),
        _representation_trend(),
        group_order=STACK_ORDER,
        group_colors=COLORS,
    )

    bars, trend = figure.axes
    bar_labels = {t.get_text() for t in bars.texts}
    assert set(GROUPS).issubset(bar_labels)
    # Fungi at 3% of attention is too narrow to carry a legible percentage label.
    assert "3.0%" not in bar_labels
    described_percentages = [
        float(text.get_text().removesuffix("%"))
        for text in bars.texts
        if text.get_text().endswith("%") and text.get_position()[0] == 0.0
    ]
    assert sum(described_percentages) == 100.0
    assert {t.get_text() for t in trend.texts}.issuperset(set(GROUPS) - {"Other"})
    plt.close(figure)


def test_representation_figure_rejects_unplotted_trend_groups() -> None:
    import pytest

    with pytest.raises(ValueError, match="unplotted groups"):
        plotting.plot_representation_and_trend(
            _representation_comparison(),
            _representation_trend(),
            group_order=STACK_ORDER,
            group_colors=COLORS,
            trend_groups=("Archaea",),
        )
