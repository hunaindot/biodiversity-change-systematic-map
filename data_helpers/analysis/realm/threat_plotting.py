"""Standalone Threat-L0 location-quotient heatmap by ecosystem realm."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from numbers import Integral, Real

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import colors as mcolors
from matplotlib.patches import Patch, Rectangle

from data_helpers.visualization import BIODIVERSITY, contrasting_text_color


LOW_SUPPORT_THRESHOLD = 50
EXCLUDED_THREATS = frozenset(
    {"Other Options", "Unclear", "Geological Events"}
)


def _validate_order(
    values: Sequence[str],
    *,
    name: str,
    expected_length: int | None = None,
) -> tuple[str, ...]:
    if isinstance(values, str):
        raise TypeError(f"{name} must be a sequence, not one string")
    order = tuple(values)
    wrong_length = (
        not order
        if expected_length is None
        else len(order) != expected_length
    )
    if wrong_length or len(order) != len(set(order)):
        requirement = (
            "one or more"
            if expected_length is None
            else f"exactly {expected_length}"
        )
        raise ValueError(
            f"{name} must contain {requirement} unique labels"
        )
    if any(not isinstance(value, str) or not value for value in order):
        raise ValueError(f"{name} must contain non-empty strings")
    return order


def _display_mapping(
    mapping: Mapping[str, str] | None,
    labels: Sequence[str],
    *,
    name: str,
) -> dict[str, str]:
    if mapping is None:
        return {label: label for label in labels}
    missing = [label for label in labels if label not in mapping]
    if missing:
        raise ValueError(f"{name} is missing labels: {missing}")
    return {label: str(mapping[label]) for label in labels}


def _color_mapping(
    mapping: Mapping[str, str],
    labels: Sequence[str],
    *,
    name: str,
) -> dict[str, str]:
    missing = [label for label in labels if label not in mapping]
    if missing:
        raise ValueError(f"{name} is missing labels: {missing}")
    invalid = [label for label in labels if not mcolors.is_color_like(mapping[label])]
    if invalid:
        raise ValueError(f"{name} contains invalid colors for: {invalid}")
    return {label: str(mapping[label]) for label in labels}


def _validate_realm_supports(
    realms: Sequence[str],
    realm_supports: Mapping[str, int],
) -> None:
    missing = [realm for realm in realms if realm not in realm_supports]
    invalid = [
        realm
        for realm in realms
        if realm in realm_supports
        and (
            not isinstance(realm_supports[realm], Integral)
            or isinstance(realm_supports[realm], bool)
            or realm_supports[realm] <= 0
        )
    ]
    if missing or invalid:
        raise ValueError(
            "realm_supports must contain positive integers for every realm"
        )


def _support_label(
    realm: str,
    *,
    realm_names: Mapping[str, str],
    realm_supports: Mapping[str, int],
) -> str:
    marker = "†" if realm_supports[realm] < LOW_SUPPORT_THRESHOLD else ""
    return f"{realm_names[realm]}{marker}\n(n={realm_supports[realm]:,})"


def _fold_change_label(log2_value: float) -> str:
    fold_change = 2.0**log2_value
    if np.isclose(fold_change, round(fold_change), atol=1e-10):
        return f"{fold_change:.0f}×"
    if fold_change >= 1:
        return f"{fold_change:.1f}×"
    return f"{fold_change:.2g}×"


def plot_threat_realm_heatmap(
    estimates: pd.DataFrame,
    *,
    threat_order: Sequence[str],
    realm_order: Sequence[str],
    realm_supports: Mapping[str, int],
    threat_colors: Mapping[str, str],
    threat_names: Mapping[str, str] | None = None,
    realm_names: Mapping[str, str] | None = None,
    lq_limit: float = 2.0,
) -> plt.Figure:
    """Plot LQ by threat and realm, using color as the sole cell encoding."""
    threats = _validate_order(
        threat_order,
        name="threat_order",
        expected_length=10,
    )
    realms = _validate_order(
        realm_order,
        name="realm_order",
        expected_length=10,
    )
    excluded = sorted(set(threats).intersection(EXCLUDED_THREATS))
    if excluded:
        raise ValueError(
            f"threat_order must exclude non-substantive labels: {excluded}"
        )
    if (
        not isinstance(lq_limit, Real)
        or isinstance(lq_limit, bool)
        or not np.isfinite(lq_limit)
        or lq_limit <= 0
    ):
        raise ValueError("lq_limit must be a finite positive number")
    _validate_realm_supports(realms, realm_supports)

    threat_labels = _display_mapping(
        threat_names, threats, name="threat_names"
    )
    identity_colors = _color_mapping(
        threat_colors, threats, name="threat_colors"
    )
    realm_labels = _display_mapping(
        realm_names, realms, name="realm_names"
    )
    required = {"realm", "threat", "log2_lq"}
    missing = sorted(required.difference(estimates.columns))
    if missing:
        raise ValueError(f"estimates is missing column(s): {missing}")
    selected = estimates[["realm", "threat", "log2_lq"]].copy()
    unexpected_realms = sorted(set(selected["realm"]).difference(realms))
    unexpected_threats = sorted(set(selected["threat"]).difference(threats))
    if unexpected_realms or unexpected_threats:
        raise ValueError(
            "estimates contains labels outside the configured orders: "
            f"realms={unexpected_realms}, threats={unexpected_threats}"
        )
    if selected.duplicated(["realm", "threat"]).any():
        raise ValueError("estimates contains duplicate realm-threat cells")
    expected = pd.MultiIndex.from_product(
        [realms, threats], names=["realm", "threat"]
    )
    observed = pd.MultiIndex.from_frame(selected[["realm", "threat"]])
    missing_cells = expected.difference(observed)
    if len(missing_cells):
        raise ValueError(
            f"estimates is missing realm-threat cells: {list(missing_cells)}"
        )
    selected["log2_lq"] = pd.to_numeric(
        selected["log2_lq"], errors="coerce"
    )
    if selected["log2_lq"].isna().any():
        raise ValueError("estimates.log2_lq cannot contain missing values")
    matrix = (
        selected.pivot(index="threat", columns="realm", values="log2_lq")
        .reindex(index=threats, columns=realms)
        .astype(float)
    )

    figure, axis = plt.subplots(figsize=(7.4, 4.8))
    norm = mcolors.TwoSlopeNorm(
        vmin=-float(lq_limit),
        vcenter=0,
        vmax=float(lq_limit),
    )
    color_map = plt.get_cmap("PRGn")
    values = np.clip(matrix.to_numpy(), -lq_limit, lq_limit)
    mesh = axis.pcolormesh(
        np.arange(len(realms) + 1),
        np.arange(len(threats) + 1),
        values,
        cmap=color_map,
        norm=norm,
        shading="flat",
        edgecolors=BIODIVERSITY["paper"],
        linewidth=0.45,
        antialiased=False,
    )
    axis.set(
        xlim=(0, len(realms)),
        ylim=(len(threats), 0),
        xticks=np.arange(len(realms)) + 0.5,
        yticks=np.arange(len(threats)) + 0.5,
        xticklabels=[
            (
                f"{realm_labels[realm]}"
                f"{'†' if realm_supports[realm] < LOW_SUPPORT_THRESHOLD else ''}"
            )
            for realm in realms
        ],
        yticklabels=[threat_labels[threat] for threat in threats],
    )
    axis.tick_params(
        length=0,
        colors=BIODIVERSITY["ink"],
        labelsize=7.5,
    )
    axis.tick_params(axis="y", pad=15)
    for row, threat in enumerate(threats):
        axis.add_patch(
            Rectangle(
                (-0.035, row + 0.08),
                0.022,
                0.84,
                transform=axis.get_yaxis_transform(),
                facecolor=identity_colors[threat],
                edgecolor=BIODIVERSITY["paper"],
                linewidth=0.4,
                clip_on=False,
                zorder=3,
            )
        )
    axis.spines[:].set_visible(False)
    axis.grid(False)

    finite = matrix.to_numpy()[np.isfinite(matrix.to_numpy())]
    low_tail = np.isneginf(matrix.to_numpy()).any() or (
        finite.size and finite.min() < -lq_limit
    )
    high_tail = np.isposinf(matrix.to_numpy()).any() or (
        finite.size and finite.max() > lq_limit
    )
    extend = (
        "both"
        if low_tail and high_tail
        else "min"
        if low_tail
        else "max"
        if high_tail
        else "neither"
    )
    ticks = np.linspace(-lq_limit, lq_limit, 5)
    colorbar = figure.colorbar(
        mesh,
        ax=axis,
        orientation="vertical",
        fraction=0.026,
        pad=0.025,
        ticks=ticks,
        extend=extend,
    )
    colorbar.ax.set_yticklabels([_fold_change_label(value) for value in ticks])
    colorbar.ax.tick_params(
        length=0,
        colors=BIODIVERSITY["ink"],
        labelsize=7.5,
    )
    colorbar.outline.set_linewidth(0.5)
    colorbar.outline.set_edgecolor(BIODIVERSITY["neutral"])
    colorbar.set_label(
        "Threat prevalence / pooled prevalence",
        fontsize=8.5,
        labelpad=5,
    )
    figure.text(
        0.985,
        0.985,
        f"† Realm support < {LOW_SUPPORT_THRESHOLD} publications",
        ha="right",
        va="top",
        fontsize=6.8,
        color=BIODIVERSITY["ink"],
    )
    figure.subplots_adjust(left=0.35, right=0.94, top=0.95, bottom=0.09)
    return figure


def plot_threat_fractional_bars(
    estimates: pd.DataFrame,
    *,
    threat_order: Sequence[str],
    realm_order: Sequence[str],
    realm_supports: Mapping[str, int],
    threat_colors: Mapping[str, str],
    threat_names: Mapping[str, str] | None = None,
    realm_names: Mapping[str, str] | None = None,
    figure_height: float | None = None,
    show_segment_labels: bool = False,
    segment_label_min_pct: float = 6.0,
) -> plt.Figure:
    """Plot horizontal 100%-stacked substantive Threat-L0 composition."""
    threats = _validate_order(
        threat_order,
        name="threat_order",
        expected_length=10,
    )
    realms = _validate_order(realm_order, name="realm_order")
    excluded = sorted(set(threats).intersection(EXCLUDED_THREATS))
    if excluded:
        raise ValueError(
            f"threat_order must exclude non-substantive labels: {excluded}"
        )
    _validate_realm_supports(realms, realm_supports)
    threat_labels = _display_mapping(
        threat_names, threats, name="threat_names"
    )
    realm_labels = _display_mapping(
        realm_names, realms, name="realm_names"
    )
    colors = _color_mapping(
        threat_colors, threats, name="threat_colors"
    )
    if not isinstance(show_segment_labels, bool):
        raise TypeError("show_segment_labels must be boolean")
    if (
        not isinstance(segment_label_min_pct, Real)
        or isinstance(segment_label_min_pct, bool)
        or not np.isfinite(segment_label_min_pct)
        or not 0 <= segment_label_min_pct <= 100
    ):
        raise ValueError(
            "segment_label_min_pct must be between zero and 100"
        )

    value = "fractional_composition"
    required = {"realm", "threat", value}
    missing = sorted(required.difference(estimates.columns))
    if missing:
        raise ValueError(f"estimates is missing column(s): {missing}")
    selected = estimates[["realm", "threat", value]].copy()
    unexpected_realms = sorted(set(selected["realm"]).difference(realms))
    unexpected_threats = sorted(set(selected["threat"]).difference(threats))
    if unexpected_realms or unexpected_threats:
        raise ValueError(
            "estimates contains labels outside the configured orders: "
            f"realms={unexpected_realms}, threats={unexpected_threats}"
        )
    if selected.duplicated(["realm", "threat"]).any():
        raise ValueError("estimates contains duplicate realm-threat cells")
    expected = pd.MultiIndex.from_product(
        [realms, threats], names=["realm", "threat"]
    )
    observed = pd.MultiIndex.from_frame(selected[["realm", "threat"]])
    missing_cells = expected.difference(observed)
    if len(missing_cells):
        raise ValueError(
            f"estimates is missing realm-threat cells: {list(missing_cells)}"
        )
    selected[value] = pd.to_numeric(selected[value], errors="coerce")
    matrix = (
        selected.pivot(index="realm", columns="threat", values=value)
        .reindex(index=realms, columns=threats)
        .astype(float)
    )
    if (
        not np.isfinite(matrix.to_numpy()).all()
        or (matrix.to_numpy() < 0).any()
        or (matrix.to_numpy() > 1).any()
    ):
        raise ValueError(
            "fractional_composition must contain finite proportions"
        )
    if not np.allclose(
        matrix.sum(axis=1).to_numpy(), 1.0, rtol=0, atol=1e-6
    ):
        raise ValueError(
            "fractional_composition must sum to one within every realm"
        )

    height = figure_height or max(2.9, 0.43 * len(realms) + 1.9)
    figure, axis = plt.subplots(figsize=(7.4, height))
    positions = np.arange(len(realms))
    left = np.zeros(len(realms))
    for threat in threats:
        values = 100 * matrix[threat].to_numpy()
        axis.barh(
            positions,
            values,
            left=left,
            height=0.66,
            color=colors[threat],
            edgecolor=BIODIVERSITY["paper"],
            linewidth=0.4,
            zorder=2,
        )
        if show_segment_labels:
            for position, start, width in zip(positions, left, values):
                if width >= segment_label_min_pct:
                    axis.text(
                        start + width / 2,
                        position,
                        f"{width:.0f}%",
                        ha="center",
                        va="center",
                        fontsize=6.8,
                        color=contrasting_text_color(colors[threat]),
                        zorder=3,
                    )
        left += values
    axis.set(
        xlim=(0, 100),
        ylim=(len(realms) - 0.5, -0.5),
        xticks=[0, 25, 50, 75, 100],
        yticks=positions,
        yticklabels=[
            _support_label(
                realm,
                realm_names=realm_labels,
                realm_supports=realm_supports,
            )
            for realm in realms
        ],
    )
    axis.set_xlabel("Share of evidence by IUCN threat (%)", fontsize=8.5)
    axis.tick_params(
        length=0,
        colors=BIODIVERSITY["ink"],
        labelsize=7.5,
    )
    axis.grid(False)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.spines["bottom"].set_bounds(0, 100)
    axis.spines["bottom"].set_color(BIODIVERSITY["neutral"])
    axis.spines["bottom"].set_linewidth(0.6)

    figure.legend(
        handles=[
            Patch(
                facecolor=colors[threat],
                edgecolor=BIODIVERSITY["paper"],
                linewidth=0.4,
                label=threat_labels[threat],
            )
            for threat in threats
        ],
        loc="lower left",
        ncol=4,
        mode="expand",
        bbox_to_anchor=(0.02, 0.012, 0.96, 0.16),
        frameon=False,
        fontsize=6.5,
        handlelength=1.1,
        columnspacing=0.8,
        borderaxespad=0,
    )
    footer = (
        f"† Realm support < {LOW_SUPPORT_THRESHOLD} publications"
        if any(realm_supports[realm] < LOW_SUPPORT_THRESHOLD for realm in realms)
        else ""
    )
    if footer:
        figure.text(
            0.30,
            0.005,
            footer,
            fontsize=6.8,
            color=BIODIVERSITY["ink"],
        )
    figure.subplots_adjust(
        left=0.30,
        right=0.985,
        top=0.98,
        bottom=0.29 if not footer else 0.25,
    )
    return figure


__all__ = [
    "EXCLUDED_THREATS",
    "LOW_SUPPORT_THRESHOLD",
    "plot_threat_fractional_bars",
    "plot_threat_realm_heatmap",
]
