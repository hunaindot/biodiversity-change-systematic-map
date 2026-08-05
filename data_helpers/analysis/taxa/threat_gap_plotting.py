"""Regional evidence-versus-threatened-species figure for the F4 geographic gap."""

from __future__ import annotations

from typing import Iterable, Mapping

import matplotlib.pyplot as plt
import pandas as pd

from data_helpers import visualization

# Panel A of the F4 figure owns these two helpers. Importing rather than copying is
# deliberate: the regional figure's whole argument is that it reads like panel A, and a
# duplicated easing curve or label-separation rule would eventually drift from it.
from data_helpers.analysis.taxa.skew_plotting import _stacked_pair, _trend_lines

#: IPBES regions in a fixed order, so the legend does not reshuffle between runs.
REGION_ORDER = ("Africa", "Asia and the Pacific", "Americas", "Europe and Central Asia")

#: Drawn from the same house palette as the taxonomic figure's broad groups
#: (``schemes.broad.group_colors``) rather than a separate scheme, so the geographic
#: figure reads as its sibling. Africa takes the one warm hue: it carries the finding
#: and needs to separate from three cool neighbours.
REGION_COLORS = {
    "Africa": "#D9954C",
    "Asia and the Pacific": "#6F91C7",
    "Americas": "#2E7D32",
    "Europe and Central Asia": "#8C6BB1",
}


class TaxaThreatGapPlotError(ValueError):
    """Raised when the scatter cannot be drawn as specified."""


__all__ = [
    "REGION_COLORS",
    "REGION_ORDER",
    "TaxaThreatGapPlotError",
]


def plot_regional_representation_and_trend(
    regional: pd.DataFrame,
    regional_trend: pd.DataFrame,
    *,
    region_order: Iterable[str] = REGION_ORDER,
    region_colors: Mapping[str, str] | None = None,
    threat_column: str = "threat_share_pct",
    evidence_column: str = "evidence_share_pct",
    segment_label_min_pct: float = 4.0,
    label_min_gap: float = 9.5,
    trend_label_min_gap: float = 11.0,
    manuscript: bool = True,
    figsize: tuple[float, float] = (7.4, 3.7),
) -> plt.Figure:
    """The geographic mismatch and what happened to it, as its own two-panel figure.

    Panel A stacks each IPBES region's share of threatened land vertebrates against its
    share of the vertebrate evidence, joined by ribbons. Panel B tracks evidence share by
    publication year.

    It is built from the taxonomic figure's own ``_stacked_pair`` and ``_trend_lines``
    and uses the same house palette, so the two figures read as siblings without being
    crammed into one panel grid. The rhyme carries the argument: two unrelated benchmarks
    — GBIF described species there, IUCN threatened species here — and attention matches
    neither. Panel B is where the two figures part company: the taxonomic composition
    barely moved, while the geographic gap narrowed markedly.
    """
    region_colors = dict(region_colors or REGION_COLORS)
    required = {"region", threat_column, evidence_column}
    missing = required.difference(regional.columns)
    if missing:
        raise TaxaThreatGapPlotError(f"Regional frame is missing columns: {sorted(missing)}")
    trend_missing = {"region", "publication_year", evidence_column}.difference(
        regional_trend.columns
    )
    if trend_missing:
        raise TaxaThreatGapPlotError(
            f"Regional trend frame is missing columns: {sorted(trend_missing)}"
        )

    order = tuple(region for region in region_order if region in set(regional["region"]))
    if not order:
        raise TaxaThreatGapPlotError("No configured region appears in the frame.")
    absent = set(regional["region"]).difference(order)
    if absent:
        raise TaxaThreatGapPlotError(f"Regions missing from region_order: {sorted(absent)}")

    table = regional.set_index("region").reindex(order)

    fig, (axis_bars, axis_trend) = plt.subplots(
        1, 2, figsize=figsize, gridspec_kw={"width_ratios": [1.0, 1.28]}
    )
    _stacked_pair(
        axis_bars,
        categories=order,
        left_values=table[threat_column].to_numpy(dtype=float),
        right_values=table[evidence_column].to_numpy(dtype=float),
        colors=region_colors,
        captions=("Threatened\nvertebrates", "Vertebrate\nevidence"),
        segment_label_min_pct=segment_label_min_pct,
        label_min_gap=label_min_gap,
    )
    top = float(regional_trend[evidence_column].max())
    _trend_lines(
        axis_trend,
        regional_trend,
        series=order,
        colors=region_colors,
        series_col="region",
        year_col="publication_year",
        value_col=evidence_column,
        ylim=(0, max(55.0, top * 1.1)),
        ylabel="Share of vertebrate evidence %",
        xlabel="Publication year",
        label_min_gap=trend_label_min_gap,
    )

    if manuscript:
        ink = visualization.BIODIVERSITY["ink"]
        for label, axis in zip("AB", (axis_bars, axis_trend)):
            axis.text(
                -0.075, 1.02, label, transform=axis.transAxes, fontsize=9,
                fontweight="bold", va="bottom", color=ink,
            )
        fig.subplots_adjust(left=0.045, right=0.985, top=0.91, bottom=0.135, wspace=0.16)
    return fig


__all__ += ["plot_regional_representation_and_trend"]
