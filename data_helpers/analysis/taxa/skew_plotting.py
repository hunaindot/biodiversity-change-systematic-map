"""Publication figures for taxonomic attention versus described diversity."""

from __future__ import annotations

import textwrap
from typing import Iterable, Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.ticker import FuncFormatter

from data_helpers import visualization
from data_helpers.analysis.taxa import clipart as taxa_clipart

SKEW_CAVEAT = (
    "Measures publication attention, not conservation need, ecological importance, "
    "population decline, or undescribed diversity. GBIF accepted species-rank share is a "
    "described-diversity proxy, not a complete species inventory."
)


def _neutral_axes(axis: plt.Axes) -> None:
    axis.spines[["top", "right"]].set_visible(False)
    axis.spines[["left", "bottom"]].set_color(
        visualization.BIODIVERSITY["neutral"]
    )
    axis.spines[["left", "bottom"]].set_linewidth(0.6)
    axis.tick_params(
        length=0,
        colors=visualization.BIODIVERSITY["ink"],
        labelsize=7.0,
    )
    axis.grid(False)


def plot_taxonomic_skew(
    comparison: pd.DataFrame,
    *,
    group_order: Iterable[str],
    group_colors: dict[str, str],
    mapping: Mapping | None = None,
    scheme_name: str = "broad",
    manuscript: bool = True,
) -> plt.Figure:
    """Plot absolute composition differences and relative representation.

    ``mapping`` is the full taxa-group config (as returned by
    ``taxa_analysis_prep.load_taxa_mapping``); when supplied, a tinted PhyloPic
    silhouette is placed beside each group's y-tick label on both panels.
    """
    group_order = tuple(group_order)
    required = {
        "broad_group",
        "effective_publication_count",
        "fractional_attention_share_pct",
        "attention_ci_low_pct",
        "attention_ci_high_pct",
        "described_species_share_pct",
        "representation_ratio",
        "log2_representation_ratio",
    }
    missing = required.difference(comparison.columns)
    if missing:
        raise ValueError(f"Comparison table is missing columns: {sorted(missing)}")
    if set(group_colors).issuperset(group_order) is False:
        raise ValueError("group_colors must cover every plotted broad group.")
    if set(comparison["broad_group"]) != set(group_order):
        raise ValueError("Comparison table must contain every broad group once.")

    icon_paths = (
        taxa_clipart.ensure_clipart_cached(mapping)
        if mapping and not manuscript
        else {}
    )
    scheme = mapping["schemes"][scheme_name] if mapping and not manuscript else None

    top_row = comparison.loc[comparison["representation_ratio"].idxmax()]
    bottom_row = comparison.loc[comparison["representation_ratio"].idxmin()]
    total_publications = float(comparison["effective_publication_count"].sum())
    headline = (
        f"{top_row['broad_group']} receive {top_row['representation_ratio']:.2f}× more "
        f"attention than their described-diversity share; {bottom_row['broad_group']} receive "
        f"{bottom_row['representation_ratio']:.2f}×. "
        f"n = {total_publications:,.0f} publications with a resolved benchmark group."
    )

    fig, (axis_share, axis_ratio) = plt.subplots(
        1,
        2,
        figsize=(7.4, 3.35 if manuscript else 4.75),
        gridspec_kw={"width_ratios": [1.48, 1.0]},
    )

    share_data = (
        comparison.set_index("broad_group")
        .reindex(group_order)
        .reset_index()
    )
    y_share = np.arange(len(share_data))
    described = share_data["described_species_share_pct"].to_numpy()
    attention = share_data["fractional_attention_share_pct"].to_numpy()
    colors = [group_colors[group] for group in share_data["broad_group"]]

    for position, left, right in zip(y_share, described, attention):
        axis_share.plot(
            [left, right],
            [position, position],
            color=visualization.BIODIVERSITY["neutral"],
            linewidth=1.6,
            solid_capstyle="round",
            zorder=1,
        )
    xerr = np.vstack(
        [
            attention - share_data["attention_ci_low_pct"].to_numpy(),
            share_data["attention_ci_high_pct"].to_numpy() - attention,
        ]
    )
    axis_share.errorbar(
        attention,
        y_share,
        xerr=xerr,
        fmt="none",
        ecolor=visualization.BIODIVERSITY["ink"],
        elinewidth=0.8,
        capsize=2.2,
        zorder=2,
    )
    axis_share.scatter(
        described,
        y_share,
        s=30,
        facecolor=visualization.BIODIVERSITY["paper"],
        edgecolor=visualization.BIODIVERSITY["ink"],
        linewidth=0.9,
        zorder=3,
    )
    axis_share.scatter(
        attention,
        y_share,
        s=38,
        c=colors,
        edgecolor=visualization.BIODIVERSITY["paper"],
        linewidth=0.7,
        zorder=4,
    )
    for position, benchmark_value, attention_value in zip(
        y_share, described, attention
    ):
        benchmark_offset = -4 if benchmark_value <= attention_value else 4
        benchmark_alignment = (
            "right" if benchmark_value <= attention_value else "left"
        )
        benchmark_y_offset = 7 if position == len(y_share) - 1 else -8
        benchmark_vertical_alignment = (
            "bottom" if position == len(y_share) - 1 else "top"
        )
        attention_offset = 4 if attention_value >= benchmark_value else -4
        attention_alignment = (
            "left" if attention_value >= benchmark_value else "right"
        )
        axis_share.annotate(
            f"{benchmark_value:.1f}%",
            (benchmark_value, position),
            xytext=(benchmark_offset, benchmark_y_offset),
            textcoords="offset points",
            ha=benchmark_alignment,
            va=benchmark_vertical_alignment,
            fontsize=6.2,
            color="#666666",
        )
        axis_share.annotate(
            f"{attention_value:.1f}%",
            (attention_value, position),
            xytext=(attention_offset, 7),
            textcoords="offset points",
            ha=attention_alignment,
            va="bottom",
            fontsize=6.4,
            color=visualization.BIODIVERSITY["ink"],
        )
    axis_share.set_yticks(y_share, share_data["broad_group"])
    if scheme is not None:
        taxa_clipart.add_group_icons(
            axis_share,
            groups=share_data["broad_group"],
            y_positions=y_share,
            scheme=scheme,
            group_colors=group_colors,
            icon_paths=icon_paths,
            x_offset=-0.30,
        )
    axis_share.invert_yaxis()
    axis_share.set_xlim(
        0,
        max(
            70,
            float(
                share_data[
                    [
                        "attention_ci_high_pct",
                        "described_species_share_pct",
                    ]
                ]
                .max()
                .max()
            )
            + 5,
        ),
    )
    axis_share.set_xlabel("Share of publications or described species (%)")
    axis_share.legend(
        handles=[
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor=visualization.BIODIVERSITY["paper"],
                markeredgecolor=visualization.BIODIVERSITY["ink"],
                markersize=4.8,
                label="GBIF accepted species-rank share",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor=visualization.BIODIVERSITY["primary"],
                markeredgecolor=visualization.BIODIVERSITY["paper"],
                markersize=5.4,
                label="Publication attention (95% bootstrap CI)",
            ),
        ],
        loc="lower left",
        bbox_to_anchor=(0.0, 1.015),
        ncol=2,
        frameon=False,
        fontsize=6.2,
        columnspacing=1.0,
        handletextpad=0.4,
        borderaxespad=0.0,
    )
    _neutral_axes(axis_share)

    ratio_data = (
        comparison.set_index("broad_group")
        .reindex(group_order)
        .reset_index()
    )
    y_ratio = np.arange(len(ratio_data))
    log_ratio = ratio_data["log2_representation_ratio"].to_numpy()
    ratio_colors = [group_colors[group] for group in ratio_data["broad_group"]]
    axis_ratio.axvline(
        0,
        color=visualization.BIODIVERSITY["ink"],
        linewidth=0.8,
        linestyle=(0, (3, 2)),
        zorder=1,
    )
    for position, value in zip(y_ratio, log_ratio):
        axis_ratio.plot(
            [0, value],
            [position, position],
            color=visualization.BIODIVERSITY["neutral"],
            linewidth=1.4,
            solid_capstyle="round",
            zorder=1,
        )
    axis_ratio.scatter(
        log_ratio,
        y_ratio,
        s=38,
        c=ratio_colors,
        edgecolor=visualization.BIODIVERSITY["paper"],
        linewidth=0.7,
        zorder=3,
    )
    for position, value, ratio in zip(
        y_ratio, log_ratio, ratio_data["representation_ratio"]
    ):
        place_right = value >= 0 or value <= -1.5
        axis_ratio.annotate(
            f"{ratio:.2f}×",
            (value, position),
            xytext=(5 if place_right else -5, 0),
            textcoords="offset points",
            ha="left" if place_right else "right",
            va="center",
            fontsize=6.5,
            color=visualization.BIODIVERSITY["ink"],
        )
    axis_ratio.set_yticks(y_ratio, ratio_data["broad_group"])
    if scheme is not None:
        taxa_clipart.add_group_icons(
            axis_ratio,
            groups=ratio_data["broad_group"],
            y_positions=y_ratio,
            scheme=scheme,
            group_colors=group_colors,
            icon_paths=icon_paths,
            x_offset=-0.34,
        )
    axis_ratio.invert_yaxis()
    lower = min(-2.5, float(np.floor(log_ratio.min() * 2) / 2) - 0.25)
    upper = max(3.0, float(np.ceil(log_ratio.max() * 2) / 2) + 0.45)
    axis_ratio.set_xlim(lower, upper)
    ticks = np.arange(np.ceil(lower), np.floor(upper) + 1)
    axis_ratio.set_xticks(ticks)
    axis_ratio.xaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"{2 ** value:g}×")
    )
    axis_ratio.set_xlabel("Representation ratio (log2 scale)")
    axis_ratio.text(
        0,
        1.015,
        "Proportional attention",
        transform=axis_ratio.get_xaxis_transform(),
        ha="center",
        va="bottom",
        fontsize=6.2,
        color="#666666",
    )
    _neutral_axes(axis_ratio)

    axis_share.text(
        -0.16,
        1.03,
        "A",
        transform=axis_share.transAxes,
        fontsize=9,
        fontweight="bold",
        va="bottom",
    )
    axis_ratio.text(
        -0.20,
        1.03,
        "B",
        transform=axis_ratio.transAxes,
        fontsize=9,
        fontweight="bold",
        va="bottom",
    )
    if manuscript:
        fig.subplots_adjust(
            left=0.16,
            right=0.985,
            top=0.86,
            bottom=0.16,
            wspace=0.36,
        )
    else:
        fig.suptitle(
            "Taxonomic attention versus described diversity",
            x=0.02,
            y=0.99,
            ha="left",
            fontsize=10,
            color=visualization.BIODIVERSITY["ink"],
        )
        fig.text(0.02, 0.945, headline, ha="left", va="top", fontsize=7.5, color="#555555")
        caveat = SKEW_CAVEAT
        if icon_paths:
            caveat = f"{caveat} {taxa_clipart.CLIPART_CREDIT}"
        fig.text(0.02, 0.02, textwrap.fill(caveat, 150), fontsize=5.3, color="#777777")
        fig.subplots_adjust(
            left=0.20,
            right=0.985,
            top=0.80,
            bottom=0.18,
            wspace=0.43,
        )
    return fig



def _ribbon(
    axis: plt.Axes,
    *,
    x_left: float,
    x_right: float,
    left_bounds: tuple[float, float],
    right_bounds: tuple[float, float],
    color: str,
    alpha: float = 0.22,
) -> None:
    """Join one group's segment in the left bar to its segment in the right bar."""
    t = np.linspace(0.0, 1.0, 64)
    ease = 0.5 * (1.0 - np.cos(np.pi * t))
    x = x_left + (x_right - x_left) * t
    lower = left_bounds[0] + (right_bounds[0] - left_bounds[0]) * ease
    upper = left_bounds[1] + (right_bounds[1] - left_bounds[1]) * ease
    axis.fill_between(x, lower, upper, color=color, alpha=alpha, linewidth=0, zorder=1)


def _separate_labels(
    anchors: Iterable[float],
    *,
    minimum_gap: float,
    lower: float = 0.0,
    upper: float = 100.0,
) -> list[float]:
    """Nudge ascending label positions apart to at least ``minimum_gap``.

    One forward pass pushes each label up off its predecessor, then one backward
    pass pulls the stack down if it overran ``upper``. Positions stay in their
    original order, so a label never crosses the segment it belongs to.
    """
    positions = [float(value) for value in anchors]
    for index in range(1, len(positions)):
        positions[index] = max(positions[index], positions[index - 1] + minimum_gap)
    overflow = positions[-1] - upper if positions else 0.0
    if overflow > 0:
        for index in range(len(positions) - 1, -1, -1):
            positions[index] -= overflow
            if index and positions[index] - positions[index - 1] >= minimum_gap:
                break
            overflow = (
                positions[index - 1] + minimum_gap - positions[index] if index else 0.0
            )
    return [min(max(value, lower), upper) for value in positions]


def _stacked_pair(
    axis: plt.Axes,
    *,
    categories: Sequence[str],
    left_values: "np.ndarray",
    right_values: "np.ndarray",
    colors: Mapping[str, str],
    captions: tuple[str, str],
    segment_label_min_pct: float,
    label_min_gap: float,
    icon_lookup: Mapping[str, str] | None = None,
    icon_zoom: float = 0.072,
    xlim: tuple[float, float] = (-0.42, 2.35),
) -> None:
    """Two 100% stacked bars on one axis, joined by ribbons, labelled on the right.

    Shared by the taxonomic panel and the geographic one so the two cannot drift in
    easing, label separation, segment-label threshold or bar geometry — the geographic
    panel's argument is that it reads like the taxonomic one.
    """
    paper = visualization.BIODIVERSITY["paper"]
    bar_width = 0.30
    x_left_bar, x_right_bar = 0.0, 1.0
    left_edge = x_left_bar + bar_width / 2
    right_edge = x_right_bar - bar_width / 2
    label_x_icon = x_right_bar + bar_width / 2 + 0.15
    label_x_text = label_x_icon + (0.22 if icon_lookup else -0.05)

    left_base = right_base = 0.0
    anchors: list[float] = []
    for index, name in enumerate(categories):
        color = colors[name]
        l_value, r_value = float(left_values[index]), float(right_values[index])
        for x_pos, base, value in (
            (x_left_bar, left_base, l_value),
            (x_right_bar, right_base, r_value),
        ):
            axis.bar(
                x_pos, value, bottom=base, width=bar_width, color=color,
                edgecolor=paper, linewidth=0.8, zorder=3,
            )
            if value >= segment_label_min_pct:
                axis.text(
                    x_pos, base + value / 2, f"{value:.0f}%", ha="center", va="center",
                    fontsize=7, color=paper, fontweight="bold", zorder=4,
                )
        _ribbon(
            axis, x_left=left_edge, x_right=right_edge,
            left_bounds=(left_base, left_base + l_value),
            right_bounds=(right_base, right_base + r_value),
            color=color,
        )
        anchors.append(right_base + r_value / 2)
        left_base += l_value
        right_base += r_value

    positions = _separate_labels(anchors, minimum_gap=label_min_gap)
    for name, label_y in zip(categories, positions):
        color = colors[name]
        asset = (icon_lookup or {}).get(name)
        if asset:
            axis.add_artist(
                AnnotationBbox(
                    OffsetImage(taxa_clipart._tinted_icon(asset, color), zoom=icon_zoom),
                    (label_x_icon, label_y), xycoords="data", frameon=False,
                    box_alignment=(0.5, 0.5), pad=0.0, annotation_clip=False,
                )
            )
        axis.text(
            label_x_text, label_y, name, ha="left", va="center",
            fontsize=7, color=color, fontweight="bold", zorder=4,
        )

    axis.set_xlim(*xlim)
    axis.set_ylim(0, 100)
    axis.set_xticks([x_left_bar, x_right_bar])
    axis.set_xticklabels(list(captions), fontsize=7)
    # No y-axis: each segment states its own percentage and both bars are 0-100%.
    axis.set_yticks([])
    _neutral_axes(axis)
    axis.spines[["bottom", "left"]].set_visible(False)
    axis.tick_params(axis="x", length=0, pad=4)


def _trend_lines(
    axis: plt.Axes,
    trend: pd.DataFrame,
    *,
    series: Sequence[str],
    colors: Mapping[str, str],
    series_col: str,
    year_col: str,
    value_col: str,
    ylim: tuple[float, float],
    ylabel: str,
    xlabel: str,
    label_min_gap: float,
) -> None:
    """One line per series with a direct end-label, shared by both trend panels."""
    ends: list[tuple[str, float, float]] = []
    for name in series:
        block = trend[trend[series_col] == name].sort_values(year_col)
        years = block[year_col].to_numpy(dtype=float)
        values = block[value_col].to_numpy(dtype=float)
        axis.plot(
            years, values, color=colors[name], linewidth=1.7,
            solid_capstyle="round", zorder=3,
        )
        ends.append((name, years[-1], values[-1]))

    ordered = sorted(ends, key=lambda item: item[2])
    scale = (ylim[1] - ylim[0]) / 100.0
    positions = _separate_labels(
        [value for _, _, value in ordered],
        minimum_gap=label_min_gap * scale,
        lower=ylim[0],
        upper=ylim[1],
    )
    for (name, last_year, _), label_y in zip(ordered, positions):
        axis.text(
            last_year + 0.6, label_y, name, ha="left", va="center",
            fontsize=7, color=colors[name], fontweight="bold",
        )

    all_years = trend[year_col].to_numpy(dtype=float)
    axis.set_xlim(all_years.min() - 0.5, all_years.max() + 8.5)
    axis.set_ylim(*ylim)
    axis.set_xticks([2000, 2005, 2010, 2015, 2020, 2025])
    axis.set_ylabel(ylabel)
    axis.set_xlabel(xlabel)
    _neutral_axes(axis)


def plot_representation_and_trend(
    comparison: pd.DataFrame,
    trend: pd.DataFrame,
    *,
    group_order: Iterable[str],
    group_colors: Mapping[str, str],
    trend_groups: Iterable[str] | None = None,
    residual_group: str | None = "Other",
    segment_label_min_pct: float = 3.4,
    label_min_gap: float = 10.5,
    mapping: Mapping | None = None,
    scheme_name: str = "broad",
    icon_zoom: float = 0.072,
    manuscript: bool = True,
    regional: pd.DataFrame | None = None,
    regional_trend: pd.DataFrame | None = None,
    region_order: Iterable[str] | None = None,
    region_colors: Mapping[str, str] | None = None,
    region_threat_column: str = "threat_share_pct",
    region_evidence_column: str = "evidence_share_pct",
    region_segment_label_min_pct: float = 4.0,
    region_label_min_gap: float = 9.5,
    region_trend_label_min_gap: float = 11.0,
) -> plt.Figure:
    """Composition against a benchmark, and how it moved — on one or two rows.

    With ``comparison`` and ``trend`` alone the figure is the two-panel taxonomic one:
    panel A stacks described-species share and research-attention share as two bars on
    one 0-100% axis joined by ribbons, panel B tracks attention share by year.

    Supplying ``regional``, ``regional_trend``, ``region_order``, and ``region_colors``
    adds a second row on the geographic axis — threatened-species share against evidence
    share (panel C), and evidence share by year (panel D) — giving a 2x2 whose columns
    are *mismatch* and *persistence* and whose rows are *taxonomic* and *geographic*.
    Both rows call the same ``_stacked_pair`` and ``_trend_lines`` helpers, so the
    geographic row reads exactly like the taxonomic one; that rhyme is the argument,
    since the two rows use unrelated benchmarks (GBIF described species, IUCN threatened
    species) and fail alike. ``region_order``/``region_colors`` are not owned by this
    module — pass ``threat_gap_plotting.REGION_ORDER``/``REGION_COLORS``.

    ``group_order`` runs bottom to top in panel A. Put the two groups carrying the claim
    at the ends, where each has a clean edge to read against. ``trend_groups`` defaults
    to every group except ``residual_group``, which is excluded because a residual bucket
    carries the largest slope while being the least interpretable series; say so in the
    caption, since the figure no longer says it.

    ``mapping`` is the full taxa-group config (as returned by
    ``taxa_analysis_prep.load_taxa_mapping``); when supplied, a tinted PhyloPic
    silhouette sits to the left of each group name in panel A. Retain
    ``taxa_clipart.CLIPART_CREDIT`` in the caption when icons are drawn. Icons draw in
    panel A regardless of layout; the geographic row has no equivalent scheme.
    """
    group_order = tuple(group_order)
    required = {
        "broad_group",
        "described_species_share_pct",
        "fractional_attention_share_pct",
    }
    missing = required.difference(comparison.columns)
    if missing:
        raise ValueError(f"Comparison table is missing columns: {sorted(missing)}")
    if set(comparison["broad_group"]) != set(group_order):
        raise ValueError("Comparison table must contain every plotted group once.")
    if not set(group_colors).issuperset(group_order):
        raise ValueError("group_colors must cover every plotted group.")

    if trend_groups is None:
        trend_groups = tuple(g for g in group_order if g != residual_group)
    else:
        trend_groups = tuple(trend_groups)
    unknown = set(trend_groups).difference(group_order)
    if unknown:
        raise ValueError(f"trend_groups contains unplotted groups: {sorted(unknown)}")

    add_regional = regional is not None or regional_trend is not None
    if add_regional:
        if regional is None or regional_trend is None:
            raise ValueError("regional and regional_trend must be supplied together.")
        if region_order is None or region_colors is None:
            raise ValueError(
                "region_order and region_colors are required when regional data is supplied."
            )
        region_order = tuple(region_order)
        region_required = {"region", region_threat_column, region_evidence_column}
        region_missing = region_required.difference(regional.columns)
        if region_missing:
            raise ValueError(f"Regional frame is missing columns: {sorted(region_missing)}")
        if set(regional["region"]) != set(region_order):
            raise ValueError("Regional frame must contain every region in region_order once.")
        if not set(region_colors).issuperset(region_order):
            raise ValueError("region_colors must cover every plotted region.")

    ink = visualization.BIODIVERSITY["ink"]
    table = comparison.set_index("broad_group").reindex(group_order)
    described = table["described_species_share_pct"].to_numpy(dtype=float)
    attention = table["fractional_attention_share_pct"].to_numpy(dtype=float)

    icon_paths = taxa_clipart.ensure_clipart_cached(mapping) if mapping else {}
    scheme = mapping["schemes"][scheme_name] if mapping else None
    icon_lookup = {}
    if scheme:
        for group in group_order:
            asset = scheme.get("group_clipart", {}).get(group)
            if asset and asset in icon_paths:
                icon_lookup[group] = icon_paths[asset]

    if add_regional:
        fig, ((axis_bars, axis_trend), (axis_region_bars, axis_region_trend)) = plt.subplots(
            2, 2, figsize=(7.4, 6.5),
            gridspec_kw={"width_ratios": [1.0, 1.28], "height_ratios": [1.0, 1.0]},
        )
    else:
        fig, (axis_bars, axis_trend) = plt.subplots(
            1, 2, figsize=(7.4, 3.7), gridspec_kw={"width_ratios": [1.0, 1.28]}
        )

    _stacked_pair(
        axis_bars,
        categories=group_order,
        left_values=described,
        right_values=attention,
        colors=group_colors,
        captions=("Described\nspecies", "Research\nattention"),
        segment_label_min_pct=segment_label_min_pct,
        label_min_gap=label_min_gap,
        icon_lookup=icon_lookup or None,
        icon_zoom=icon_zoom,
    )
    _trend_lines(
        axis_trend,
        trend,
        series=trend_groups,
        colors=group_colors,
        series_col="broad_group",
        year_col="publication_year",
        value_col="fractional_attention_share_pct",
        ylim=(0, 42),
        ylabel="Research attention %",
        xlabel="Publication year",
        label_min_gap=0.0,
    )

    if add_regional:
        region_table = regional.set_index("region").reindex(region_order)
        _stacked_pair(
            axis_region_bars,
            categories=region_order,
            left_values=region_table[region_threat_column].to_numpy(dtype=float),
            right_values=region_table[region_evidence_column].to_numpy(dtype=float),
            colors=region_colors,
            captions=("Threatened birds\nand mammals", "Vertebrate\nevidence"),
            segment_label_min_pct=region_segment_label_min_pct,
            label_min_gap=region_label_min_gap,
        )
        region_top = float(regional_trend[region_evidence_column].max())
        _trend_lines(
            axis_region_trend,
            regional_trend,
            series=region_order,
            colors=region_colors,
            series_col="region",
            year_col="publication_year",
            value_col=region_evidence_column,
            ylim=(0, max(55.0, region_top * 1.1)),
            ylabel="Share of vertebrate evidence %",
            xlabel="Publication year",
            label_min_gap=region_trend_label_min_gap,
        )

    if manuscript:
        # Panel letters match 02/03: lowercase, bold, 9 pt, just outside the axes.
        panel_axes = (
            (axis_bars, axis_trend, axis_region_bars, axis_region_trend)
            if add_regional
            else (axis_bars, axis_trend)
        )
        for label, axis in zip("abcd", panel_axes):
            axis.text(
                -0.075, 1.02, label, transform=axis.transAxes, fontsize=9,
                fontweight="bold", va="bottom", color=ink,
            )
        if add_regional:
            fig.subplots_adjust(
                left=0.045, right=0.985, top=0.96, bottom=0.075, hspace=0.42, wspace=0.16,
            )
        else:
            fig.subplots_adjust(left=0.045, right=0.985, top=0.91, bottom=0.135, wspace=0.16)
    return fig


__all__ = ["plot_representation_and_trend", "plot_taxonomic_skew"]
