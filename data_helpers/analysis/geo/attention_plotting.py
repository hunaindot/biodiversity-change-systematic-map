"""Radial overview of research attention across the complete IPBES geography.

The plot deliberately gives every mapped place one equal angular slot.  Evidence
therefore changes only the *radial* extent of a country bar; a place with no
captured evidence remains a visible structural slot instead of collapsing to zero
area.  The default visual reduces the hierarchy to region and country rings;
subregions remain analytical metadata but are omitted to make the clockwise
attention ranking legible.  The country ring distinguishes supported,
low-support, zero-evidence, and structurally unresolvable entries.

The module owns drawing only.  Callers should prepare a complete one-row-per-place
table and decide the evidentiary denominator used by ``attention_share_pct``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from numbers import Real
from textwrap import fill

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import colors as mcolors
from matplotlib.patches import Circle, Wedge

from data_helpers import visualization


REGION_ORDER = (
    "Africa",
    "Asia and the Pacific",
    "Americas",
    "Europe and Central Asia",
    "Antarctica",
)

# The first four colours are the established Result 04 geographic palette.
# Antarctica uses the remaining Okabe-Ito magenta rather than grey, which is
# reserved for the analytically important zero-evidence state.
REGION_COLORS = {
    "Africa": "#D9954C",
    "Asia and the Pacific": "#6F91C7",
    "Americas": "#2E7D32",
    "Europe and Central Asia": "#8C6BB1",
    "Antarctica": "#CC79A7",
}

SUPPORTED = "supported"
LOW_SUPPORT = "low_support"
ZERO_EVIDENCE = "zero"
UNRESOLVABLE = "unresolvable"
STATUS_ORDER = (SUPPORTED, LOW_SUPPORT, ZERO_EVIDENCE, UNRESOLVABLE)
SUPPRESSED_REGION_LABELS = frozenset({"Antarctica"})

ZERO_COLOR = visualization.BIODIVERSITY["neutral"]
UNRESOLVABLE_COLOR = "#EFEFEF"

# Display-only editorial names keep labels at 20 characters or fewer and distinct
# without changing the authoritative mapping names. Conventional abbreviations and
# en dashes reduce the disproportionate rim space required by a few long names.
COUNTRY_DISPLAY_OVERRIDES = {
    "Akrotiri and Dhekelia": "Akrotiri–Dhekelia",
    "Bonaire, Sint Eustatius and Saba": "Bonaire–Eust.–Saba",
    "Bosnia and Herzegovina": "Bosnia & Herzegovina",
    "British Indian Ocean Territory (the)": "BIOT",
    "Central African Republic (the)": "Central African Rep.",
    "Congo (the Democratic Republic of the)": "DR Congo",
    "Congo (the)": "Congo Republic",
    "Falkland Islands (the) [Malvinas]": "Falklands/Malvinas",
    "French Southern Territories (the)": "French S. Terr.",
    "Heard Island and McDonald Islands": "Heard–McDonald Is.",
    "Korea (the Republic of)": "South Korea",
    "Korea (the Democratic People's Republic of)": "North Korea",
    "Lao People's Democratic Republic (the)": "Lao PDR",
    "Northern Mariana Islands (the)": "N Mariana Islands",
    "Saint Helena, Ascension and Tristan da Cunha": "St Helena group",
    "Saint Kitts and Nevis": "St Kitts & Nevis",
    "Saint Pierre and Miquelon": "St Pierre & Miquelon",
    "Saint Vincent and the Grenadines": "St Vincent–Gren.",
    "Sao Tome and Principe": "São Tomé & Príncipe",
    "South Georgia and the South Sandwich Islands": "S Georgia–Sandwich",
    "Svalbard and Jan Mayen": "Svalbard–Jan Mayen",
    "Tanzania, the United Republic of": "Tanzania",
    "Turks and Caicos Islands (the)": "Turks & Caicos Is.",
    "United Kingdom of Great Britain and Northern Ireland (the)": "United Kingdom",
    "United States of America (the)": "United States",
    "United States Minor Outlying Islands (Navassa)": "Navassa Island",
    "United States Minor Outlying Islands (the)": "U.S. Outlying Is.",
    "Virgin Islands (British)": "British Virgin Is.",
    "Virgin Islands (U.S.)": "U.S. Virgin Islands",
}


class GeographicAttentionPlotError(ValueError):
    """Raised when the hierarchy cannot be plotted without ambiguity."""


def _blend_with_paper(color: str, amount: float) -> str:
    """Blend ``color`` toward the shared white paper colour."""
    if not 0 <= amount <= 1:
        raise ValueError("amount must be between zero and one")
    foreground = np.asarray(mcolors.to_rgb(color), dtype=float)
    paper = np.asarray(
        mcolors.to_rgb(visualization.BIODIVERSITY["paper"]), dtype=float
    )
    return mcolors.to_hex((1.0 - amount) * foreground + amount * paper)


def _polar_xy(radius: float, angle_degrees: float) -> tuple[float, float]:
    angle = np.deg2rad(angle_degrees)
    return radius * float(np.cos(angle)), radius * float(np.sin(angle))


def _display_country_name(country: str) -> str:
    """Return a concise rim label without altering the underlying country name."""
    if country in COUNTRY_DISPLAY_OVERRIDES:
        return COUNTRY_DISPLAY_OVERRIDES[country]
    # The second expression also cleans the mapping's one unclosed Macao qualifier.
    display = re.sub(r"\s*\([^)]*\)", "", country)
    display = re.sub(r"\s*\([^)]*$", "", display)
    # Source footnote markers have no corresponding note in the publication figure.
    display = re.sub(r"\s*\*+\s*$", "", display)
    return re.sub(r"\s+", " ", display).strip()


def _upright_tangential_rotation(angle_degrees: float) -> float:
    """Return an upright tangential text rotation for a polar angle."""
    rotation = ((angle_degrees - 90 + 180) % 360) - 180
    if rotation > 90:
        rotation -= 180
    elif rotation < -90:
        rotation += 180
    return rotation


def _run_span(
    start: int,
    size: int,
    *,
    slot_width: float,
    start_angle: float,
) -> tuple[float, float, float]:
    """Return low, high, and midpoint angles for a contiguous slot run."""
    high = start_angle - start * slot_width
    low = start_angle - (start + size) * slot_width
    return low, high, (low + high) / 2.0


def _inset_angles(
    low: float,
    high: float,
    requested_gap: float,
) -> tuple[float, float]:
    """Inset a wedge without allowing a narrow structural run to disappear."""
    span = high - low
    gap = min(requested_gap, 0.42 * span)
    return low + gap / 2.0, high - gap / 2.0


def _attention_scale(
    values_pct: np.ndarray,
    *,
    floor_pct: float,
) -> np.ndarray:
    """Map percentage shares to [0, 1] with a zero-preserving log transform."""
    values = np.asarray(values_pct, dtype=float)
    if values.ndim != 1:
        raise ValueError("values_pct must be one-dimensional")
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("values_pct must contain finite non-negative values")
    if not isinstance(floor_pct, Real) or isinstance(floor_pct, bool):
        raise TypeError("floor_pct must be numeric")
    if not np.isfinite(floor_pct) or floor_pct <= 0:
        raise ValueError("floor_pct must be finite and positive")
    maximum = float(values.max(initial=0.0))
    if maximum == 0:
        return np.zeros_like(values)
    return np.log1p(values / floor_pct) / np.log1p(maximum / floor_pct)


def _automatic_scale_ticks(maximum_pct: float, *, limit: int = 4) -> list[float]:
    """Choose up to ``limit`` decade ticks for the radial attention guide."""
    if maximum_pct <= 0:
        return []
    upper_exponent = int(np.floor(np.log10(maximum_pct)))
    lower_exponent = upper_exponent - 5
    ticks = [
        float(10.0**exponent)
        for exponent in range(lower_exponent, upper_exponent + 1)
        if 10.0**exponent <= maximum_pct * (1 + 1e-12)
    ]
    return ticks[-limit:]


def _normalise_boolean(series: pd.Series, *, name: str) -> pd.Series:
    if series.isna().any() or not series.isin([True, False]).all():
        raise GeographicAttentionPlotError(
            f"{name} must contain only non-missing booleans"
        )
    return series.astype(bool)


def _prepare_leaves(
    leaves: pd.DataFrame,
    *,
    region_col: str,
    subregion_col: str,
    country_col: str,
    iso3_col: str,
    count_col: str,
    share_col: str | None,
    status_col: str | None,
    resolvable_col: str | None,
    low_attention_threshold_pct: float,
    region_order: Sequence[str],
    sort_by_attention: bool,
) -> pd.DataFrame:
    required = {region_col, subregion_col, country_col, iso3_col, count_col}
    if share_col is not None:
        required.add(share_col)
    if status_col is not None:
        required.add(status_col)
    if resolvable_col is not None:
        required.add(resolvable_col)
    missing = sorted(required.difference(leaves.columns))
    if missing:
        raise GeographicAttentionPlotError(
            f"Leaf table is missing required column(s): {missing}"
        )
    if leaves.empty:
        raise GeographicAttentionPlotError("Leaf table cannot be empty")

    frame = leaves.copy().reset_index(drop=True)
    frame["_input_order"] = np.arange(len(frame))
    for column in (region_col, subregion_col, country_col):
        frame[column] = frame[column].astype("string").str.strip()
        if frame[column].isna().any() or frame[column].eq("").any():
            raise GeographicAttentionPlotError(
                f"{column} must contain non-empty labels"
            )
    if frame.duplicated([region_col, subregion_col, country_col]).any():
        duplicates = frame.loc[
            frame.duplicated(
                [region_col, subregion_col, country_col], keep=False
            ),
            [region_col, subregion_col, country_col],
        ]
        raise GeographicAttentionPlotError(
            "Leaf table contains duplicate hierarchy entries: "
            f"{duplicates.head(5).to_dict('records')}"
        )

    iso3 = frame[iso3_col].astype("string").fillna("").str.strip()
    frame["_iso3_display"] = iso3
    if resolvable_col is None:
        frame["_resolvable"] = iso3.str.len().eq(3)
    else:
        frame["_resolvable"] = _normalise_boolean(
            frame[resolvable_col], name=resolvable_col
        )

    counts = pd.to_numeric(frame[count_col], errors="coerce")
    invalid_count = (
        (counts.isna() & frame["_resolvable"])
        | (counts.notna() & ~np.isfinite(counts))
        | counts.lt(0).fillna(False)
    )
    if invalid_count.any():
        raise GeographicAttentionPlotError(
            f"{count_col} must contain finite non-negative counts for resolvable leaves"
        )
    numeric_counts = counts.fillna(0.0)
    if not np.allclose(numeric_counts, np.round(numeric_counts), rtol=0, atol=1e-9):
        raise GeographicAttentionPlotError(f"{count_col} must contain integers")
    frame["_count"] = numeric_counts.round().astype(np.int64)

    if share_col is None:
        total = int(frame["_count"].sum())
        frame["_share_pct"] = (
            frame["_count"] / total * 100.0 if total else 0.0
        )
    else:
        shares = pd.to_numeric(frame[share_col], errors="coerce")
        invalid_share = (
            (shares.isna() & frame["_resolvable"])
            | (shares.notna() & ~np.isfinite(shares))
            | shares.lt(0).fillna(False)
            | shares.gt(100).fillna(False)
        )
        if invalid_share.any():
            raise GeographicAttentionPlotError(
                f"{share_col} must contain finite percentages from zero to 100 "
                "for resolvable leaves"
            )
        frame["_share_pct"] = shares.fillna(0.0).astype(float)

    if status_col is None:
        frame["_status"] = np.select(
            [
                ~frame["_resolvable"],
                frame["_count"].eq(0),
                frame["_share_pct"].lt(low_attention_threshold_pct),
            ],
            [UNRESOLVABLE, ZERO_EVIDENCE, LOW_SUPPORT],
            default=SUPPORTED,
        )
    else:
        statuses = frame[status_col].astype("string").str.strip()
        invalid = sorted(set(statuses.dropna()).difference(STATUS_ORDER))
        if statuses.isna().any() or invalid:
            raise GeographicAttentionPlotError(
                f"{status_col} must use {list(STATUS_ORDER)}; invalid={invalid}"
            )
        frame["_status"] = statuses

    positive_resolved = frame["_status"].isin([SUPPORTED, LOW_SUPPORT])
    inconsistent = positive_resolved & (
        frame["_count"].le(0) | frame["_share_pct"].le(0)
    )
    if inconsistent.any():
        names = frame.loc[inconsistent, country_col].head(5).tolist()
        raise GeographicAttentionPlotError(
            "Supported and low-support leaves require positive counts and shares: "
            f"{names}"
        )

    configured = list(dict.fromkeys(region_order))
    if not configured:
        raise GeographicAttentionPlotError("region_order cannot be empty")
    observed = frame[region_col].drop_duplicates().tolist()
    full_region_order = [
        *configured,
        *[name for name in observed if name not in configured],
    ]
    region_rank = {name: index for index, name in enumerate(full_region_order)}
    frame["_region_rank"] = frame[region_col].map(region_rank)

    if sort_by_attention:
        region_attention = frame.groupby(
            region_col, sort=False, observed=True
        )["_share_pct"].sum()
        ordered_regions = sorted(
            observed,
            key=lambda name: (
                -float(region_attention[name]),
                region_rank[name],
                str(name),
            ),
        )
        attention_region_rank = {
            name: index for index, name in enumerate(ordered_regions)
        }
        frame["_region_rank"] = frame[region_col].map(attention_region_rank)
        frame["_missing_rank"] = np.select(
            [
                frame["_status"].eq(ZERO_EVIDENCE),
                frame["_status"].eq(UNRESOLVABLE),
            ],
            [1, 2],
            default=0,
        )
        return frame.sort_values(
            [
                "_region_rank",
                "_missing_rank",
                "_share_pct",
                "_count",
                country_col,
                "_input_order",
            ],
            ascending=[True, True, False, False, True, True],
            kind="stable",
        ).reset_index(drop=True)

    subregion_first = (
        frame.groupby([region_col, subregion_col], sort=False)["_input_order"]
        .min()
        .to_dict()
    )
    frame["_subregion_rank"] = [
        subregion_first[(region, subregion)]
        for region, subregion in frame[[region_col, subregion_col]].itertuples(
            index=False, name=None
        )
    ]
    return frame.sort_values(
        ["_region_rank", "_subregion_rank", "_input_order"],
        kind="stable",
    ).reset_index(drop=True)


def _hierarchy_runs(
    frame: pd.DataFrame,
    columns: Sequence[str],
) -> list[tuple[tuple[str, ...], int, int]]:
    """Return contiguous ``(keys, start, size)`` runs after hierarchy sorting."""
    runs: list[tuple[tuple[str, ...], int, int]] = []
    grouped = frame.groupby(list(columns), sort=False, observed=True).indices
    for raw_key, positions in grouped.items():
        key = raw_key if isinstance(raw_key, tuple) else (raw_key,)
        ordered = np.sort(np.asarray(positions, dtype=int))
        if ordered[-1] - ordered[0] + 1 != len(ordered):
            raise GeographicAttentionPlotError(
                f"Hierarchy group is not contiguous after ordering: {key}"
            )
        runs.append((tuple(str(value) for value in key), int(ordered[0]), len(ordered)))
    return sorted(runs, key=lambda item: item[1])


def _subregion_colors(
    frame: pd.DataFrame,
    *,
    region_col: str,
    subregion_col: str,
    region_colors: Mapping[str, str],
) -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for region, block in frame.groupby(region_col, sort=False, observed=True):
        subregions = block[subregion_col].drop_duplicates().tolist()
        amounts = (
            [0.30]
            if len(subregions) == 1
            else np.linspace(0.16, 0.48, len(subregions)).tolist()
        )
        for subregion, amount in zip(subregions, amounts, strict=True):
            result[(str(region), str(subregion))] = _blend_with_paper(
                region_colors[str(region)], float(amount)
            )
    return result


def _status_color(status: str, region_color: str) -> str:
    if status == SUPPORTED:
        return region_color
    if status == LOW_SUPPORT:
        return _blend_with_paper(region_color, 0.64)
    if status == ZERO_EVIDENCE:
        return ZERO_COLOR
    if status == UNRESOLVABLE:
        return UNRESOLVABLE_COLOR
    raise GeographicAttentionPlotError(f"Unrecognised status: {status}")


def _add_hierarchy_label(
    axis: plt.Axes,
    *,
    text: str,
    angle: float,
    span: float,
    radius: float,
    outer_radius: float,
    color: str,
    level: str,
    gid_label: str | None = None,
) -> None:
    """Draw a ring label, using a short leader for exceptionally narrow runs."""
    ink = visualization.BIODIVERSITY["ink"]
    if span >= (8.0 if level == "region" else 5.0):
        x, y = _polar_xy(radius, angle)
        wrapped = "\n".join(
            fill(
                line,
                width=18 if level == "region" else 14,
                break_long_words=False,
                break_on_hyphens=False,
            )
            for line in text.splitlines()
        )
        axis.text(
            x,
            y,
            wrapped,
            ha="center",
            va="center",
            rotation=_upright_tangential_rotation(angle),
            rotation_mode="anchor",
            fontsize=7.0 if level == "region" else 5.4,
            fontweight="bold" if level == "region" else "normal",
            color=(
                visualization.contrasting_text_color(color)
                if level == "region"
                else ink
            ),
            linespacing=0.95,
            zorder=8,
            gid=f"{level}-label:{gid_label or text}",
        )
        return

    anchor = _polar_xy(outer_radius, angle)
    target = _polar_xy(outer_radius + 0.34, angle)
    horizontal = np.cos(np.deg2rad(angle))
    annotation = axis.annotate(
        text,
        xy=anchor,
        xytext=target,
        ha="left" if horizontal >= 0 else "right",
        va="center",
        fontsize=6.0,
        fontweight="bold" if level == "region" else "normal",
        color=ink,
        arrowprops={
            "arrowstyle": "-",
            "color": color,
            "linewidth": 0.5,
            "shrinkA": 1.5,
            "shrinkB": 1.5,
        },
        annotation_clip=False,
        zorder=10,
    )
    annotation.set_gid(f"{level}-label:{gid_label or text}")


def _add_country_labels(
    axis: plt.Axes,
    frame: pd.DataFrame,
    *,
    country_col: str,
    angles: np.ndarray,
    radius: float,
    low_attention_threshold_pct: float,
    highlight_attention_threshold_pct: float,
) -> None:
    for position, row in frame.iterrows():
        text = _display_country_name(str(row[country_col]))
        angle = float(angles[position])
        x, y = _polar_xy(radius, angle)
        normalised = angle % 360
        left_half = 90 < normalised < 270
        rotation = angle if not left_half else angle + 180
        artist = axis.text(
            x,
            y,
            text,
            ha="left" if not left_half else "right",
            va="center",
            rotation=rotation,
            rotation_mode="anchor",
            fontsize=4.8,
            fontweight=(
                "bold"
                if float(row["_share_pct"]) > highlight_attention_threshold_pct
                else "normal"
            ),
            fontstyle=(
                "italic"
                if (
                    row["_status"] == ZERO_EVIDENCE
                    or (
                        0 < float(row["_share_pct"])
                        < low_attention_threshold_pct
                    )
                )
                else "normal"
            ),
            color=(
                "#686868"
                if row["_status"] == ZERO_EVIDENCE
                else visualization.BIODIVERSITY["ink"]
            ),
            clip_on=False,
            zorder=9,
        )
        artist.set_gid(f"country-label:{position}:{row[country_col]}")


def plot_geographic_attention_radial(
    leaves: pd.DataFrame,
    *,
    region_col: str = "region",
    subregion_col: str = "subregion",
    country_col: str = "country",
    iso3_col: str = "iso3",
    count_col: str = "record_count",
    share_col: str | None = "attention_share_pct",
    status_col: str | None = None,
    resolvable_col: str | None = None,
    region_order: Sequence[str] = REGION_ORDER,
    region_colors: Mapping[str, str] | None = None,
    low_attention_threshold_pct: float = 0.1,
    highlight_attention_threshold_pct: float = 1.0,
    start_angle: float = 90.0,
    attention_scale_floor_pct: float = 0.001,
    attention_ticks_pct: Sequence[float] | None = None,
    figsize: tuple[float, float] | None = None,
    show_subregions: bool = False,
    sort_by_attention: bool = True,
) -> plt.Figure:
    """Plot the complete IPBES geography and its research-attention distribution.

    Parameters
    ----------
    leaves:
        Complete one-row-per-location table.  Structural rows with zero evidence
        must already be present; this function never manufactures or drops leaves.
    share_col:
        Percentage-point share used for radial length.  Pass ``None`` to derive
        shares from ``count_col / sum(count_col)`` (country-publication assignments).
    status_col:
        Optional explicit status using ``supported``, ``low_support``, ``zero``,
        or ``unresolvable``.  Otherwise status is derived from ISO availability and
        ``low_attention_threshold_pct``.
    low_attention_threshold_pct:
        Positive attention shares below this percentage receive the pale version
        of their parent-region colour. The default is 0.1%.
    highlight_attention_threshold_pct:
        Country labels above this percentage are bold. The default is 1%; labels
        exactly at the threshold remain regular.
    show_subregions:
        Draw the intermediate subregion ring.  The default omits it for a simpler
        centre → region → country reading while retaining subregions in source data.
    sort_by_attention:
        Order regions, then countries within each region, by descending fractional
        attention.  Zero-captured and no-key leaves follow positive-attention leaves.

    Notes
    -----
    Country slots have equal angles and run clockwise from the top seam.  Region
    angular spans therefore encode numbers of mapped locations, *not* evidence
    volume.  Country attention is encoded by radial extent using
    ``log1p(share / floor)``.
    """
    if (
        not isinstance(low_attention_threshold_pct, Real)
        or isinstance(low_attention_threshold_pct, bool)
        or not np.isfinite(low_attention_threshold_pct)
        or not 0 < low_attention_threshold_pct <= 100
    ):
        raise GeographicAttentionPlotError(
            "low_attention_threshold_pct must be a finite percentage in (0, 100]"
        )
    if (
        not isinstance(highlight_attention_threshold_pct, Real)
        or isinstance(highlight_attention_threshold_pct, bool)
        or not np.isfinite(highlight_attention_threshold_pct)
        or not 0 <= highlight_attention_threshold_pct <= 100
    ):
        raise GeographicAttentionPlotError(
            "highlight_attention_threshold_pct must be a finite percentage in [0, 100]"
        )
    if not isinstance(show_subregions, bool):
        raise TypeError("show_subregions must be boolean")
    if not isinstance(sort_by_attention, bool):
        raise TypeError("sort_by_attention must be boolean")
    if show_subregions and sort_by_attention:
        raise GeographicAttentionPlotError(
            "show_subregions=True requires sort_by_attention=False so each "
            "subregion remains a contiguous hierarchy run"
        )

    colors = dict(REGION_COLORS if region_colors is None else region_colors)
    frame = _prepare_leaves(
        leaves,
        region_col=region_col,
        subregion_col=subregion_col,
        country_col=country_col,
        iso3_col=iso3_col,
        count_col=count_col,
        share_col=share_col,
        status_col=status_col,
        resolvable_col=resolvable_col,
        low_attention_threshold_pct=float(low_attention_threshold_pct),
        region_order=region_order,
        sort_by_attention=sort_by_attention,
    )
    missing_colors = sorted(set(frame[region_col]).difference(colors))
    if missing_colors:
        raise GeographicAttentionPlotError(
            f"region_colors is missing region(s): {missing_colors}"
        )
    invalid_colors = sorted(
        region
        for region in set(frame[region_col])
        if not mcolors.is_color_like(colors[region])
    )
    if invalid_colors:
        raise GeographicAttentionPlotError(
            f"region_colors contains invalid colours for: {invalid_colors}"
        )

    figure_size = figsize or (7.5, 7.5)
    figure, axis = plt.subplots(figsize=figure_size)
    axis.set_aspect("equal")
    axis.set_axis_off()

    # Fixed hierarchy geometry.  The outer attention band has enough range for a
    # strong concentration signal without turning low-support bars into hairlines.
    center_radius = 0.52
    region_inner, region_width = 0.56, 0.78
    region_outer = region_inner + region_width
    subregion_inner, subregion_width = 1.83, 0.48
    subregion_outer = subregion_inner + subregion_width
    country_inner = 1.88 if show_subregions else 1.40
    country_width = 0.30
    country_outer = country_inner + country_width
    bar_base = country_outer + 0.08
    maximum_bar_height = 1.93 if show_subregions else 2.23
    maximum_outer_radius = bar_base + maximum_bar_height

    count = len(frame)
    slot_width = 360.0 / count
    angles = start_angle - (np.arange(count, dtype=float) + 0.5) * slot_width
    scaled_attention = _attention_scale(
        frame["_share_pct"].to_numpy(dtype=float),
        floor_pct=attention_scale_floor_pct,
    )
    positive = frame["_status"].isin([SUPPORTED, LOW_SUPPORT]).to_numpy()
    positive &= frame["_share_pct"].to_numpy(dtype=float) > 0
    bar_heights = maximum_bar_height * scaled_attention
    bar_heights[positive] = np.maximum(bar_heights[positive], 0.022)
    bar_heights[~positive] = 0.0

    subregion_color_lookup = (
        _subregion_colors(
            frame,
            region_col=region_col,
            subregion_col=subregion_col,
            region_colors=colors,
        )
        if show_subregions
        else {}
    )

    # Faint guide rings sit behind the bars.  Their labels make the nonlinear
    # radial scale explicit rather than inviting a false linear reading.
    maximum_share = float(frame["_share_pct"].max())
    ticks = (
        _automatic_scale_ticks(maximum_share)
        if attention_ticks_pct is None
        else [float(value) for value in attention_ticks_pct]
    )
    if any(not np.isfinite(value) or value <= 0 for value in ticks):
        raise GeographicAttentionPlotError(
            "attention_ticks_pct must contain finite positive values"
        )
    ticks = sorted(set(value for value in ticks if value <= maximum_share))
    if ticks:
        tick_scaled = _attention_scale(
            np.asarray([*ticks, maximum_share], dtype=float),
            floor_pct=attention_scale_floor_pct,
        )[:-1]
        for tick, scaled in zip(ticks, tick_scaled, strict=True):
            radius = bar_base + maximum_bar_height * float(scaled)
            guide = Circle(
                (0, 0),
                radius,
                facecolor="none",
                edgecolor="#E5E5E5",
                linewidth=0.35,
                zorder=0.2,
            )
            guide.set_gid(f"attention-guide:{tick:g}")
            axis.add_patch(guide)
            x, y = _polar_xy(radius, start_angle)
            label = axis.text(
                x,
                y,
                f"{tick:g}%",
                ha="left",
                va="center",
                fontsize=6.6,
                fontweight="bold",
                color="#777777",
                bbox={
                    "boxstyle": "square,pad=0.08",
                    "facecolor": visualization.BIODIVERSITY["paper"],
                    "edgecolor": "none",
                    "alpha": 0.86,
                },
                zorder=11,
            )
            label.set_gid(f"attention-guide-label:{tick:g}")

    # Region ring.
    for (region,), run_start, run_size in _hierarchy_runs(frame, [region_col]):
        low, high, middle = _run_span(
            run_start,
            run_size,
            slot_width=slot_width,
            start_angle=start_angle,
        )
        theta1, theta2 = _inset_angles(low, high, requested_gap=1.05)
        wedge = Wedge(
            (0, 0),
            region_outer,
            theta1,
            theta2,
            width=region_width,
            facecolor=colors[region],
            edgecolor=visualization.BIODIVERSITY["paper"],
            linewidth=0.8,
            zorder=3,
        )
        wedge.set_gid(f"region:{region}")
        axis.add_patch(wedge)
        # Antarctica occupies a single narrow slot; its country label already
        # identifies the sector, while an internal region label crowds the guide.
        if region not in SUPPRESSED_REGION_LABELS:
            region_label = region.replace(" and ", " & ")
            _add_hierarchy_label(
                axis,
                text=region_label,
                angle=middle,
                span=high - low,
                radius=region_inner + region_width / 2,
                outer_radius=region_outer,
                color=colors[region],
                level="region",
                gid_label=region,
            )

    if show_subregions:
        # Optional diagnostic ring. Attention sorting can fragment subregions, so
        # the default simplified figure deliberately omits this intermediate level.
        for (region, subregion), run_start, run_size in _hierarchy_runs(
            frame, [region_col, subregion_col]
        ):
            low, high, middle = _run_span(
                run_start,
                run_size,
                slot_width=slot_width,
                start_angle=start_angle,
            )
            theta1, theta2 = _inset_angles(low, high, requested_gap=0.42)
            color = subregion_color_lookup[(region, subregion)]
            wedge = Wedge(
                (0, 0),
                subregion_outer,
                theta1,
                theta2,
                width=subregion_width,
                facecolor=color,
                edgecolor=visualization.BIODIVERSITY["paper"],
                linewidth=0.5,
                zorder=4,
            )
            wedge.set_gid(f"subregion:{region}:{subregion}")
            axis.add_patch(wedge)
            if subregion != region:
                _add_hierarchy_label(
                    axis,
                    text=subregion,
                    angle=middle,
                    span=high - low,
                    radius=subregion_inner + subregion_width / 2,
                    outer_radius=subregion_outer,
                    color=color,
                    level="subregion",
                )

    # Equal-angle structural country slots and outward evidence bars.
    for position, row in frame.iterrows():
        low, high, _ = _run_span(
            position,
            1,
            slot_width=slot_width,
            start_angle=start_angle,
        )
        theta1, theta2 = _inset_angles(
            low, high, requested_gap=min(0.12, 0.14 * slot_width)
        )
        region_color = colors[str(row[region_col])]
        facecolor = _status_color(str(row["_status"]), region_color)
        slot = Wedge(
            (0, 0),
            country_outer,
            theta1,
            theta2,
            width=country_width,
            facecolor=facecolor,
            edgecolor=visualization.BIODIVERSITY["paper"],
            linewidth=0.16,
            zorder=5,
        )
        slot.set_gid(f"country-slot:{position}:{row[country_col]}")
        axis.add_patch(slot)

        height = float(bar_heights[position])
        if height <= 0:
            continue
        bar_theta1, bar_theta2 = _inset_angles(
            low, high, requested_gap=min(0.25, 0.24 * slot_width)
        )
        bar = Wedge(
            (0, 0),
            bar_base + height,
            bar_theta1,
            bar_theta2,
            width=height,
            facecolor=facecolor,
            edgecolor="none",
            linewidth=0,
            zorder=6,
        )
        bar.set_gid(f"attention-bar:{position}:{row[country_col]}")
        axis.add_patch(bar)

    # A compact solid centre anchors the hierarchy without duplicating caption text.
    centre = Circle(
        (0, 0),
        center_radius,
        facecolor=visualization.BIODIVERSITY["ink"],
        edgecolor=visualization.BIODIVERSITY["ink"],
        linewidth=0.4,
        zorder=20,
    )
    centre.set_gid("evidence-centre")
    axis.add_patch(centre)
    _add_country_labels(
        axis,
        frame,
        country_col=country_col,
        angles=angles,
        radius=maximum_outer_radius + 0.12,
        low_attention_threshold_pct=float(low_attention_threshold_pct),
        highlight_attention_threshold_pct=float(
            highlight_attention_threshold_pct
        ),
    )

    limit = maximum_outer_radius + 0.72
    axis.set_xlim(-limit, limit)
    axis.set_ylim(-limit, limit)
    figure.subplots_adjust(left=0.015, right=0.985, top=0.985, bottom=0.015)
    return figure


__all__ = [
    "GeographicAttentionPlotError",
    "LOW_SUPPORT",
    "REGION_COLORS",
    "REGION_ORDER",
    "STATUS_ORDER",
    "SUPPORTED",
    "UNRESOLVABLE",
    "ZERO_COLOR",
    "ZERO_EVIDENCE",
    "plot_geographic_attention_radial",
]
