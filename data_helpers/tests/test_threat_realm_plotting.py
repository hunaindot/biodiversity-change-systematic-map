"""Tests for the annotation-free Threat-L0 LQ heatmap."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from data_helpers.analysis.realm.driver import ANALYSIS_REALMS, CORE_REALMS
from data_helpers.analysis.realm.threat_plotting import (
    plot_threat_fractional_bars,
    plot_threat_realm_heatmap,
)


THREATS = (
    "Pollution",
    "Climate Change & Severe Weather",
    "Natural System Modifications",
    "Biological Resource Use",
    "Invasive & Other Problematic Species, Genes & Diseases",
    "Human Intrusions & Disturbance",
    "Residential & Commercial Development",
    "Agriculture & Aquaculture",
    "Energy Production & Mining",
    "Transportation & Service Corridors",
)
THREAT_COLORS = {
    "Residential & Commercial Development": "#A96E4C",
    "Agriculture & Aquaculture": "#D9954C",
    "Energy Production & Mining": "#E8BC80",
    "Transportation & Service Corridors": "#F2D7AB",
    "Biological Resource Use": "#689B78",
    "Human Intrusions & Disturbance": "#C1DEC5",
    "Invasive & Other Problematic Species, Genes & Diseases": "#8FC89A",
    "Natural System Modifications": "#B9D2DF",
    "Pollution": "#6B95B8",
    "Climate Change & Severe Weather": "#0072B2",
}
REALMS = ANALYSIS_REALMS
SUPPORTS = {
    realm: np.int64(1_000 - 50 * position)
    for position, realm in enumerate(REALMS)
}
SUPPORTS["Subterranean-Marine"] = np.int64(36)


def _estimates() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    base = np.array(
        (0.12, 0.13, 0.11, 0.14, 0.08, 0.09, 0.07, 0.10, 0.08, 0.08)
    )
    for realm_position, realm in enumerate(REALMS):
        fractional = np.roll(base, realm_position % len(THREATS))
        for threat_position, threat in enumerate(THREATS):
            rows.append(
                {
                    "realm": realm,
                    "threat": threat,
                    "log2_lq": -2.5
                    + 0.25 * threat_position
                    + 0.15 * realm_position,
                    "fractional_composition": fractional[threat_position],
                }
            )
    return pd.DataFrame(rows)


def _plot(estimates: pd.DataFrame) -> plt.Figure:
    return plot_threat_realm_heatmap(
        estimates,
        threat_order=THREATS,
        realm_order=REALMS,
        realm_supports=SUPPORTS,
        threat_colors=THREAT_COLORS,
        threat_names={
            threat: f"Threat {index + 1}"
            for index, threat in enumerate(THREATS)
        },
        realm_names={
            realm: f"R{index + 1}"
            for index, realm in enumerate(REALMS)
        },
    )


def test_heatmap_uses_color_without_cell_percentages(tmp_path) -> None:
    figure = _plot(_estimates())
    assert figure.get_figwidth() == pytest.approx(7.4)
    assert figure.get_figheight() == pytest.approx(4.8)
    assert len(figure.axes) == 2
    assert len(figure.axes[0].texts) == 0
    assert len(figure.axes[0].collections) == 1
    assert len(figure.axes[0].patches) == len(THREATS)
    assert [
        matplotlib.colors.to_hex(patch.get_facecolor())
        for patch in figure.axes[0].patches
    ] == [THREAT_COLORS[threat].lower() for threat in THREATS]
    assert figure.texts[0].get_text() == "† Realm support < 50 publications"
    output = tmp_path / "threat-lq.pdf"
    figure.savefig(output)
    plt.close(figure)
    assert output.read_bytes().startswith(b"%PDF")


def test_heatmap_requires_one_complete_grid() -> None:
    with pytest.raises(ValueError, match="missing realm-threat cells"):
        _plot(_estimates().iloc[:-1])
    duplicated = pd.concat([_estimates(), _estimates().iloc[[0]]])
    with pytest.raises(ValueError, match="duplicate realm-threat cells"):
        _plot(duplicated)


def test_heatmap_rejects_non_substantive_threats() -> None:
    invalid_order = (*THREATS[:-1], "Unclear")
    estimates = _estimates().replace(
        {"Climate Change & Severe Weather": "Unclear"}
    )
    with pytest.raises(ValueError, match="must exclude non-substantive"):
        plot_threat_realm_heatmap(
            estimates,
            threat_order=invalid_order,
            realm_order=REALMS,
            realm_supports=SUPPORTS,
            threat_colors=THREAT_COLORS,
        )


def test_heatmap_requires_valid_threat_colors() -> None:
    invalid_colors = dict(THREAT_COLORS)
    invalid_colors[THREATS[0]] = "not-a-color"
    with pytest.raises(ValueError, match="contains invalid colors"):
        plot_threat_realm_heatmap(
            _estimates(),
            threat_order=THREATS,
            realm_order=REALMS,
            realm_supports=SUPPORTS,
            threat_colors=invalid_colors,
        )


@pytest.mark.parametrize(
    ("realm_order", "height"),
    [(REALMS, 6.2), (CORE_REALMS, 3.8)],
)
def test_horizontal_bar_views_accept_all_and_core_realms(
    realm_order: tuple[str, ...],
    height: float,
) -> None:
    figure = plot_threat_fractional_bars(
        _estimates().loc[lambda frame: frame["realm"].isin(realm_order)],
        threat_order=THREATS,
        realm_order=realm_order,
        realm_supports=SUPPORTS,
        threat_colors=THREAT_COLORS,
        threat_names={threat: threat for threat in THREATS},
        realm_names={realm: realm for realm in REALMS},
        figure_height=height,
        show_segment_labels=realm_order == CORE_REALMS,
    )
    axis = figure.axes[0]
    assert figure.get_figheight() == pytest.approx(height)
    assert len(axis.patches) == len(realm_order) * len(THREATS)
    assert axis.get_xlim() == pytest.approx((0, 100))
    assert axis.get_xlabel() == "Share of evidence by IUCN threat (%)"
    if realm_order == CORE_REALMS:
        assert axis.texts
        assert all(text.get_text().endswith("%") for text in axis.texts)
    else:
        assert not axis.texts
    plt.close(figure)


def test_bar_view_requires_fractional_composition_to_sum_to_one() -> None:
    estimates = _estimates()
    estimates.loc[0, "fractional_composition"] = 0
    with pytest.raises(ValueError, match="sum to one"):
        plot_threat_fractional_bars(
            estimates,
            threat_order=THREATS,
            realm_order=REALMS,
            realm_supports=SUPPORTS,
            threat_colors=THREAT_COLORS,
        )
