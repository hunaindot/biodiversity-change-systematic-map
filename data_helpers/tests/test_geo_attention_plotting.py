"""Tests for the complete-IPBES radial research-attention figure."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
from matplotlib.patches import Wedge
import pandas as pd
import pytest

from data_helpers.analysis.geo import attention_plotting as plotting


def _leaves() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "region": "Africa",
                "subregion": "West Africa",
                "country": "Alpha",
                "iso3": "AAA",
                "record_count": 1_000,
                "attention_share_pct": 10.0,
            },
            {
                "region": "Africa",
                "subregion": "West Africa",
                "country": "Beta",
                "iso3": "BBB",
                "record_count": 25,
                "attention_share_pct": 0.025,
            },
            {
                "region": "Africa",
                "subregion": "East Africa",
                "country": "Gamma",
                "iso3": "GAM",
                "record_count": 0,
                "attention_share_pct": 0.0,
            },
            {
                "region": "Americas",
                "subregion": "Caribbean",
                "country": "Delta",
                "iso3": "DDD",
                "record_count": 500,
                "attention_share_pct": 5.0,
            },
            {
                "region": "Americas",
                "subregion": "Caribbean",
                "country": "Epsilon",
                "iso3": "EEE",
                "record_count": 10,
                "attention_share_pct": 0.10,
            },
            {
                "region": "Americas",
                "subregion": "South America",
                "country": "Zeta",
                "iso3": "ZZZ",
                "record_count": 100,
                "attention_share_pct": 1.0,
            },
            {
                "region": "Europe and Central Asia",
                "subregion": "Central Asia",
                "country": "Eta",
                "iso3": "ETA",
                "record_count": 0,
                "attention_share_pct": 0.0,
            },
            {
                "region": "Europe and Central Asia",
                "subregion": "Central Asia",
                "country": "Uncoded place",
                "iso3": "",
                "record_count": pd.NA,
                "attention_share_pct": pd.NA,
            },
        ]
    )


def _wedges_with_gid(axis, prefix: str) -> list[Wedge]:
    return [
        patch
        for patch in axis.patches
        if isinstance(patch, Wedge)
        and (patch.get_gid() or "").startswith(prefix)
    ]


def test_radial_figure_retains_equal_angle_slot_for_every_leaf() -> None:
    figure = plotting.plot_geographic_attention_radial(_leaves())
    axis = figure.axes[0]
    slots = _wedges_with_gid(axis, "country-slot:")

    assert len(slots) == len(_leaves())
    widths = [slot.theta2 - slot.theta1 for slot in slots]
    assert max(widths) - min(widths) == pytest.approx(0.0, abs=1e-10)
    assert tuple(figure.get_size_inches()) == pytest.approx((7.5, 7.5))
    plt.close(figure)


def test_status_styles_and_no_bar_states_are_distinct() -> None:
    figure = plotting.plot_geographic_attention_radial(_leaves())
    axis = figure.axes[0]
    slots = {
        patch.get_gid().split(":", 2)[-1]: patch
        for patch in _wedges_with_gid(axis, "country-slot:")
    }
    bars = _wedges_with_gid(axis, "attention-bar:")

    assert len(bars) == 5  # supported and low-support leaves only
    assert mcolors.to_hex(slots["Alpha"].get_facecolor()) == plotting.REGION_COLORS[
        "Africa"
    ].lower()
    assert mcolors.to_hex(slots["Gamma"].get_facecolor()) == plotting.ZERO_COLOR.lower()
    assert slots["Uncoded place"].get_hatch() is None
    assert (
        mcolors.to_hex(slots["Uncoded place"].get_facecolor())
        == plotting.UNRESOLVABLE_COLOR.lower()
    )
    assert mcolors.to_hex(slots["Beta"].get_facecolor()) != mcolors.to_hex(
        slots["Alpha"].get_facecolor()
    )
    assert not any("Gamma" in (bar.get_gid() or "") for bar in bars)
    assert not any("Uncoded place" in (bar.get_gid() or "") for bar in bars)
    plt.close(figure)


def test_simplified_hierarchy_draws_regions_but_no_subregion_ring() -> None:
    leaves = _leaves()
    figure = plotting.plot_geographic_attention_radial(leaves)
    axis = figure.axes[0]

    assert len(_wedges_with_gid(axis, "region:")) == leaves["region"].nunique()
    assert _wedges_with_gid(axis, "subregion:") == []
    gids = {text.get_gid() for text in axis.texts}
    assert {f"region-label:{name}" for name in leaves["region"].unique()} <= gids
    assert not any((gid or "").startswith("subregion-label:") for gid in gids)
    region_labels = {
        text.get_gid().removeprefix("region-label:"): text.get_text()
        for text in axis.texts
        if (text.get_gid() or "").startswith("region-label:")
    }
    assert region_labels["Africa"] == "Africa"
    assert region_labels["Europe and Central Asia"].replace(
        "\n", " "
    ) == "Europe & Central Asia"
    all_region_text = " ".join(region_labels.values()).lower()
    assert " and " not in all_region_text
    assert "n =" not in all_region_text
    assert "places" not in all_region_text
    for text in axis.texts:
        if (text.get_gid() or "").startswith("region-label:"):
            rotation = ((text.get_rotation() + 180) % 360) - 180
            assert -90 <= rotation <= 90
    plt.close(figure)


@pytest.mark.parametrize(
    ("angle", "expected"),
    [(40, -50), (150, 60), (230, -40), (310, 40)],
)
def test_tangential_region_rotation_is_upright(angle: float, expected: float) -> None:
    assert plotting._upright_tangential_rotation(angle) == pytest.approx(expected)


def test_antarctica_wedge_is_retained_but_region_annotation_is_suppressed() -> None:
    antarctica = _leaves().iloc[[0]].assign(
        region="Antarctica",
        subregion="Antarctica",
        country="Antarctica",
        iso3="ATA",
        record_count=1,
        attention_share_pct=0.001,
    )
    figure = plotting.plot_geographic_attention_radial(
        pd.concat([_leaves(), antarctica], ignore_index=True)
    )
    axis = figure.axes[0]

    assert len(_wedges_with_gid(axis, "region:Antarctica")) == 1
    gids = {text.get_gid() for text in axis.texts}
    assert any(
        (gid or "").startswith("country-label:")
        and (gid or "").endswith(":Antarctica")
        for gid in gids
    )
    assert "region-label:Antarctica" not in gids
    plt.close(figure)


def test_clockwise_order_descends_by_region_and_country_attention() -> None:
    figure = plotting.plot_geographic_attention_radial(_leaves())
    slots = _wedges_with_gid(figure.axes[0], "country-slot:")
    names = [slot.get_gid().split(":", 2)[-1] for slot in slots]

    assert names == [
        "Alpha",
        "Beta",
        "Gamma",
        "Delta",
        "Zeta",
        "Epsilon",
        "Eta",
        "Uncoded place",
    ]
    label_names = [
        text.get_gid().split(":", 2)[-1]
        for text in figure.axes[0].texts
        if (text.get_gid() or "").startswith("country-label:")
    ]
    assert label_names == [
        "Alpha",
        "Beta",
        "Gamma",
        "Delta",
        "Zeta",
        "Epsilon",
        "Eta",
        "Uncoded place",
    ]
    midpoints = [(slot.theta1 + slot.theta2) / 2 for slot in slots]
    slot_width = 360 / len(slots)
    assert midpoints[0] == pytest.approx(90 - slot_width / 2)
    assert all(left > right for left, right in zip(midpoints, midpoints[1:]))
    plt.close(figure)


def test_country_labels_above_one_percent_are_bold() -> None:
    figure = plotting.plot_geographic_attention_radial(_leaves())
    labels = {
        text.get_gid().split(":", 2)[-1]: text
        for text in figure.axes[0].texts
        if (text.get_gid() or "").startswith("country-label:")
    }

    assert labels["Alpha"].get_fontweight() == "bold"
    assert labels["Delta"].get_fontweight() == "bold"
    assert labels["Zeta"].get_fontweight() == "normal"  # exactly 1%
    assert labels["Beta"].get_fontweight() == "normal"
    plt.close(figure)


def test_country_labels_below_point_one_percent_are_italic() -> None:
    figure = plotting.plot_geographic_attention_radial(_leaves())
    labels = {
        text.get_gid().split(":", 2)[-1]: text
        for text in figure.axes[0].texts
        if (text.get_gid() or "").startswith("country-label:")
    }

    assert labels["Beta"].get_fontstyle() == "italic"
    assert labels["Epsilon"].get_fontstyle() == "normal"  # exactly 0.1%
    assert labels["Zeta"].get_fontstyle() == "normal"
    plt.close(figure)


def test_optional_subregion_ring_requires_hierarchy_order() -> None:
    figure = plotting.plot_geographic_attention_radial(
        _leaves(),
        show_subregions=True,
        sort_by_attention=False,
    )
    assert len(_wedges_with_gid(figure.axes[0], "subregion:")) == _leaves()[
        ["region", "subregion"]
    ].drop_duplicates().shape[0]
    plt.close(figure)

    with pytest.raises(
        plotting.GeographicAttentionPlotError,
        match="show_subregions=True requires sort_by_attention=False",
    ):
        plotting.plot_geographic_attention_radial(
            _leaves(), show_subregions=True, sort_by_attention=True
        )


def test_attention_bar_lengths_are_monotonic_and_log_compressed() -> None:
    figure = plotting.plot_geographic_attention_radial(_leaves())
    axis = figure.axes[0]
    bars = {
        patch.get_gid().split(":", 2)[-1]: patch
        for patch in _wedges_with_gid(axis, "attention-bar:")
    }

    alpha_height = bars["Alpha"].width
    zeta_height = bars["Zeta"].width
    beta_height = bars["Beta"].width
    assert alpha_height > zeta_height > beta_height > 0
    # Alpha has 40x Beta's share; the log transform intentionally compresses that.
    assert alpha_height / beta_height < 4
    plt.close(figure)


def test_attention_guide_labels_are_bold() -> None:
    figure = plotting.plot_geographic_attention_radial(_leaves())
    labels = [
        text
        for text in figure.axes[0].texts
        if (text.get_gid() or "").startswith("attention-guide-label:")
    ]

    assert labels
    assert all(text.get_fontweight() == "bold" for text in labels)
    plt.close(figure)


def test_solid_center_and_country_name_labels_are_present_without_legend() -> None:
    figure = plotting.plot_geographic_attention_radial(_leaves())
    axis = figure.axes[0]

    centres = [
        patch for patch in axis.patches if patch.get_gid() == "evidence-centre"
    ]
    assert len(centres) == 1
    assert mcolors.to_hex(centres[0].get_facecolor()) == "#2b2b2b"
    assert figure.texts == []
    country_labels = {
        text.get_gid().split(":", 2)[-1]: text
        for text in axis.texts
        if (text.get_gid() or "").startswith("country-label:")
    }
    assert set(country_labels) == set(_leaves()["country"])
    assert country_labels["Gamma"].get_fontstyle() == "italic"
    assert country_labels["Alpha"].get_fontstyle() == "normal"
    assert figure.legends == []
    plt.close(figure)


def test_country_labels_use_names_and_figure_draws() -> None:
    leaves = _leaves()
    long_name = "A country or area name longer than twenty-four characters"
    leaves.loc[leaves["country"].eq("Alpha"), "country"] = long_name
    figure = plotting.plot_geographic_attention_radial(
        leaves,
        figsize=(8.0, 8.0),
    )
    axis = figure.axes[0]
    country_labels = [
        text
        for text in axis.texts
        if (text.get_gid() or "").startswith("country-label:")
    ]

    assert len(country_labels) == len(leaves)
    assert {text.get_text() for text in country_labels} >= {
        long_name,
        "Beta",
        "Gamma",
    }
    assert all("\n" not in text.get_text() for text in country_labels)
    assert not {"AAA", "BBB", "GAM"}.intersection(
        text.get_text() for text in country_labels
    )
    assert tuple(figure.get_size_inches()) == pytest.approx((8.0, 8.0))
    figure.canvas.draw()
    plt.close(figure)


def test_country_display_names_remove_parentheses_and_avoid_collisions() -> None:
    assert plotting._display_country_name(
        "Venezuela (Bolivarian Republic of)"
    ) == "Venezuela"
    assert plotting._display_country_name(
        "Macao (Special Adminstrative Region China"
    ) == "Macao"
    assert plotting._display_country_name(
        "Congo (the Democratic Republic of the)"
    ) == "DR Congo"
    assert plotting._display_country_name("Congo (the)") == "Congo Republic"
    assert plotting._display_country_name(
        "Korea (the Democratic People's Republic of)"
    ) == "North Korea"
    assert plotting._display_country_name("Korea (the Republic of)") == "South Korea"
    assert plotting._display_country_name("Western Sahara*") == "Western Sahara"


def test_long_country_display_names_are_compact_but_identifiable() -> None:
    expected = {
        "Akrotiri and Dhekelia": "Akrotiri–Dhekelia",
        "Bonaire, Sint Eustatius and Saba": "Bonaire–Eust.–Saba",
        "Bosnia and Herzegovina": "Bosnia & Herzegovina",
        "British Indian Ocean Territory (the)": "BIOT",
        "Central African Republic (the)": "Central African Rep.",
        "Congo (the)": "Congo Republic",
        "Falkland Islands (the) [Malvinas]": "Falklands/Malvinas",
        "French Southern Territories (the)": "French S. Terr.",
        "Heard Island and McDonald Islands": "Heard–McDonald Is.",
        "Lao People's Democratic Republic (the)": "Lao PDR",
        "Northern Mariana Islands (the)": "N Mariana Islands",
        "United Kingdom of Great Britain and Northern Ireland (the)": "United Kingdom",
        "Saint Helena, Ascension and Tristan da Cunha": "St Helena group",
        "Saint Kitts and Nevis": "St Kitts & Nevis",
        "Saint Pierre and Miquelon": "St Pierre & Miquelon",
        "Saint Vincent and the Grenadines": "St Vincent–Gren.",
        "Sao Tome and Principe": "São Tomé & Príncipe",
        "South Georgia and the South Sandwich Islands": "S Georgia–Sandwich",
        "Svalbard and Jan Mayen": "Svalbard–Jan Mayen",
        "Tanzania, the United Republic of": "Tanzania",
        "Turks and Caicos Islands (the)": "Turks & Caicos Is.",
        "United States of America (the)": "United States",
        "United States Minor Outlying Islands (the)": "U.S. Outlying Is.",
        "Virgin Islands (British)": "British Virgin Is.",
    }

    rendered = {
        source: plotting._display_country_name(source) for source in expected
    }
    assert rendered == expected
    assert max(len(name.split()) for name in rendered.values()) <= 4
    assert max(len(name) for name in rendered.values()) <= 20


def test_share_can_be_derived_from_country_assignment_counts() -> None:
    leaves = _leaves().drop(columns="attention_share_pct")
    figure = plotting.plot_geographic_attention_radial(
        leaves, share_col=None
    )

    assert len(_wedges_with_gid(figure.axes[0], "attention-bar:")) == 5
    plt.close(figure)


@pytest.mark.parametrize("threshold", [0, -0.1, 101, float("nan"), True])
def test_low_attention_threshold_must_be_a_valid_percentage(threshold) -> None:
    with pytest.raises(
        plotting.GeographicAttentionPlotError,
        match="low_attention_threshold_pct",
    ):
        plotting.plot_geographic_attention_radial(
            _leaves(), low_attention_threshold_pct=threshold
        )


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (
            lambda frame: pd.concat([frame, frame.iloc[[0]]], ignore_index=True),
            "duplicate hierarchy entries",
        ),
        (
            lambda frame: frame.assign(record_count=-1),
            "finite non-negative counts",
        ),
        (
            lambda frame: frame.drop(columns="country"),
            "missing required column",
        ),
    ],
)
def test_invalid_leaf_tables_fail_loudly(mutator, message: str) -> None:
    with pytest.raises(plotting.GeographicAttentionPlotError, match=message):
        plotting.plot_geographic_attention_radial(mutator(_leaves()))
