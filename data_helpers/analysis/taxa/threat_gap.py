"""Per-country evidence versus threatened-species counts — ongoing F4 analysis.

**Exploratory, not manuscript-backing.** This asks a question the F4 headline does
not: within a single taxon group, is evidence distributed across countries the way
threatened-species counts are? The headline compares attention to *described*
diversity globally; this compares attention to *threat* geographically.

Three frames are produced and exported separately, because they answer three
questions and have three different denominators:

1. :func:`evidence_by_country` — every country in the mapped universe, with its
   publication counts and location quotient for one group. **No support cutoff**:
   the ``meets_min_support`` column flags thin countries, it never drops them.
2. :func:`threatened_species_by_country` — every country in the WDI snapshot, with
   its IUCN threatened counts by class.
3. :func:`match_evidence_and_threat` — the two joined, with the ratio of each
   country's share of evidence to its share of threatened species.

The WDI snapshot carries four threatened-species indicators. Three (birds, mammals,
higher plants) come from the **IUCN Red List** via UNEP-WCMC; the fourth, fish, is
credited to **FishBase**, not the Red List — do not describe the set as "four IUCN
indicators". "Threatened" is IUCN CR + EN + VU throughout.

Two limits bound what the comparison can carry:

* There is **no reptile or amphibian indicator**, so ``threatened_vertebrates`` here
  is birds + fish + mammals and understates true vertebrate threat. Amphibians are
  the most threatened vertebrate class, so tropical deficits are understated most.
* Fish are held apart because they scale with marine area rather than land area,
  which distorts small island and Gulf states — and because of the different source
  above. ``threatened_vertebrates_land`` (birds + mammals) is the comparable subset
  for a terrestrial reading and is what :func:`summarise_gap_by_region` uses.

Definitional quirks that survive into the counts: mammals **exclude whales and
porpoises**; birds are counted for every country in their breeding *or* wintering
range, so migratory species inflate flyway countries; higher plants are native
vascular plants only.

**Threat counts are not additive across countries.** A species is counted once per
country in its range — for birds, in every breeding *or* wintering range state. The
columns therefore sum to far more than the number of threatened species that exist:
4,684 birds across countries against a global unique figure near 1,400. Never present
a column sum as a world total.

That non-additivity is mostly harmless for the ratio, since both sides are shares of
a sum-over-countries and the evidence side double-counts multi-country publications
the same way — but the *pattern* of inflation is uneven and does move country cells:

* Narrow-range endemics count once, so endemic-rich countries (Madagascar, the
  Philippines, Indonesia) hold a **depressed** share of the inflated total and their
  deficits read better than they are.
* Wide-ranging and migratory species count many times, so countries sharing them
  hold an **inflated** share and their deficits read deeper than they are.

The two run opposite ways and cannot be signed without range-size data, which this
snapshot does not carry. Resolving it needs IUCN range polygons or a species-by-country
matrix, not WDI.

The World Bank's own series metadata warns that "cross-country comparability of
threatened species is limited", and names the Andes, Central and West Africa, Angola,
South and South-East Asia and Melanesia as having the sparsest mammal data. Both
belong in any write-up: the second means gaps found in those regions are floors, and
the first means country cells are indicative while the regional rollup is the
defensible unit.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


class TaxaThreatGapError(ValueError):
    """Raised when the evidence/threat join cannot be built as specified."""


#: WDI indicator code -> the column it becomes. Order fixes the column order.
#: EN.FSH.THRD.NO is sourced from FishBase, the other three from the IUCN Red List.
THREAT_INDICATORS: Mapping[str, str] = {
    "EN.BIR.THRD.NO": "threatened_birds",
    "EN.MAM.THRD.NO": "threatened_mammals",
    "EN.FSH.THRD.NO": "threatened_fish",
    "EN.HPT.THRD.NO": "threatened_higher_plants",
}

#: Classes summed into each aggregate. Fish are in the first and not the second.
VERTEBRATE_COLUMNS = ("threatened_birds", "threatened_mammals", "threatened_fish")
LAND_VERTEBRATE_COLUMNS = ("threatened_birds", "threatened_mammals")

#: What each table exports, keyed by artifact stem. The builders return more than this
#: on purpose — downstream steps need the intermediates — but a CSV a human reads should
#: carry only columns that table is about. Anything constant down the column (the group
#: name, the WDI year, an all-true flag) is a fact about the table, not a variable in it,
#: and belongs in the printed summary or the manifest instead.
EXPORT_COLUMNS: Mapping[str, tuple[str, ...]] = {
    "evidence-by-country": (
        "iso3", "country", "region", "subregion",
        "n_group_publications", "n_country_publications",
        "share_of_group_evidence_pct", "within_country_share_pct",
        "lq", "lq_eb", "meets_min_support",
    ),
    "threatened-species-by-country": (
        "iso3", "country", "region", "subregion",
        "threatened_birds", "threatened_mammals", "threatened_fish",
        "threatened_higher_plants",
        "threatened_vertebrates", "threatened_vertebrates_land", "threatened_total",
    ),
    "evidence-vs-threatened": (
        "iso3", "country", "region", "subregion",
        "n_group_publications",
        "threatened_birds", "threatened_mammals", "threatened_fish",
        "threatened_vertebrates_land", "threatened_vertebrates",
        "matched_evidence_share_pct",
        "matched_threatened_vertebrates_land_share_pct",
        "evidence_to_threatened_vertebrates_land_ratio",
        # Kept as the fish-inclusive sensitivity, not as a second headline.
        "evidence_to_threatened_vertebrates_ratio",
        # Capacity covariates: reported beside the comparison, never folded into it.
        "gdp_per_capita_usd", "rd_expenditure_pct_gdp",
        "researchers_per_million", "scientific_articles",
    ),
}


def select_export_columns(frame: pd.DataFrame, stem: str) -> pd.DataFrame:
    """Narrow a built frame to the columns its CSV should carry.

    Raises rather than silently skipping an absent column, so renaming a field in a
    builder cannot quietly drop it from the export.
    """
    try:
        columns = EXPORT_COLUMNS[stem]
    except KeyError:
        raise TaxaThreatGapError(
            f"No export column set named {stem!r}; known: {sorted(EXPORT_COLUMNS)}"
        ) from None
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise TaxaThreatGapError(f"Frame is missing export columns for {stem!r}: {missing}")
    return frame[list(columns)].copy()


#: Research-capacity covariates, all from the same WDI snapshot and ISO3 spine.
#: They separate two very different readings of a deficit: a country that publishes
#: little science of any kind, versus one that publishes plenty but little of it on
#: biodiversity relative to its threat load. Only the second is an allocation failure.
#: Coverage is thinner than the threat side (145-213 countries), so nulls are expected
#: and are left as nulls.
CAPACITY_INDICATORS: Mapping[str, str] = {
    "NY.GDP.PCAP.CD": "gdp_per_capita_usd",
    "GB.XPD.RSDV.GD.ZS": "rd_expenditure_pct_gdp",
    "SP.POP.SCIE.RD.P6": "researchers_per_million",
    "IP.JRN.ARTC.SC": "scientific_articles",
}


def _wdi_indicator_frame(
    source: str | Path,
    indicators: Mapping[str, str],
    *,
    iso3_col: str = "ipbes_iso3",
) -> pd.DataFrame:
    """Pivot a set of WDI indicator codes to one row per country.

    Shared by the threat and capacity loaders so both drop aggregates, reject
    duplicate country/indicator rows, and land on the same IPBES labels.
    ``wdi_year`` is the latest observation year across the requested indicators,
    which differ in vintage — it is a provenance note, not a per-value year.
    """
    source = Path(source)
    if not source.exists():
        raise TaxaThreatGapError(f"World Bank snapshot not found: {source}")

    frame = pd.read_parquet(source)
    required = {iso3_col, "indicator_code", "value", "year", "is_aggregate"}
    missing = required.difference(frame.columns)
    if missing:
        raise TaxaThreatGapError(f"Snapshot is missing columns: {sorted(missing)}")

    block = frame[
        frame["indicator_code"].isin(indicators) & ~frame["is_aggregate"].astype(bool)
    ].copy()
    if block.empty:
        raise TaxaThreatGapError(
            f"Snapshot carries none of the requested indicators: {sorted(indicators)}"
        )
    duplicated = int(block.duplicated([iso3_col, "indicator_code"]).sum())
    if duplicated:
        raise TaxaThreatGapError(
            f"Snapshot has {duplicated:,} duplicate country/indicator rows; the "
            "latest-observation view should carry one row per pair."
        )

    wide = block.pivot(index=iso3_col, columns="indicator_code", values="value")
    wide = wide.rename(columns=dict(indicators)).reindex(columns=list(indicators.values()))
    labels = (
        block[[iso3_col, "ipbes_country", "ipbes_region", "ipbes_subregion"]]
        .drop_duplicates(iso3_col)
        .set_index(iso3_col)
    )
    years = block.groupby(iso3_col)["year"].max()

    out = wide.join(labels).join(years.rename("wdi_year")).reset_index()
    return out.rename(
        columns={
            iso3_col: "iso3",
            "ipbes_country": "country",
            "ipbes_region": "region",
            "ipbes_subregion": "subregion",
        }
    )


def research_capacity_by_country(
    source: str | Path,
    *,
    indicators: Mapping[str, str] | None = None,
    iso3_col: str = "ipbes_iso3",
) -> pd.DataFrame:
    """Research-capacity covariates per country, for conditioning the focus score.

    Carried alongside the score rather than folded into it: a deficit that disappears
    once national scientific output is accounted for is a capacity story, and a deficit
    that survives is an allocation story. Keeping them as separate columns lets the
    reader see which they are looking at instead of taking that judgement on trust.

    Coverage is materially thinner than the threat side and varies by indicator, so
    missing values stay null. ``n_capacity_indicators`` counts how many of the
    requested indicators a country actually carries.
    """
    indicators = dict(indicators or CAPACITY_INDICATORS)
    out = _wdi_indicator_frame(source, indicators, iso3_col=iso3_col)
    columns = list(indicators.values())
    out["n_capacity_indicators"] = out[columns].notna().sum(axis=1).astype(int)
    ordered = ["iso3", "country", "region", "subregion", *columns, "n_capacity_indicators"]
    return out[ordered].sort_values("iso3").reset_index(drop=True)


def evidence_by_country(
    lq: pd.DataFrame,
    crosswalk: pd.DataFrame,
    *,
    group: str,
    key_col: str = "iso3",
    group_col: str = "broad_group",
) -> pd.DataFrame:
    """One row per country in the mapped universe, for a single taxon group.

    Every country the location quotient was computed for is kept, however few
    publications it holds — ``meets_min_support`` records the cutoff the maps use
    without applying it, so the size of the thin tail stays visible.

    ``support`` is the country's *total* geolocated publications across all groups
    (the LQ denominator ``D[c]``), not its publications about ``group``; the two are
    named apart here because conflating them is the easiest error to make.
    """
    missing = {key_col, group_col, "n", "support"}.difference(lq.columns)
    if missing:
        raise TaxaThreatGapError(
            f"Location-quotient frame is missing columns: {sorted(missing)}"
        )
    block = lq[lq[group_col] == group]
    if block.empty:
        raise TaxaThreatGapError(f"Group absent from the location-quotient frame: {group!r}")

    named = block.merge(
        crosswalk[["iso3", "country", "region", "subregion"]].drop_duplicates("iso3"),
        left_on=key_col,
        right_on="iso3",
        how="left",
    )
    group_total = float(named["n"].sum())
    frame = pd.DataFrame(
        {
            "iso3": named[key_col],
            "country": named["country"],
            "region": named["region"],
            "subregion": named["subregion"],
            "broad_group": group,
            "n_group_publications": named["n"].astype(int),
            "n_country_publications": named["support"].astype(int),
            "share_of_group_evidence_pct": named["n"] / group_total * 100.0,
            "within_country_share_pct": named["within_share"] * 100.0,
            "corpus_share_pct": named["global_share"] * 100.0,
            "lq": named["lq"],
            "log2_lq": named["log2_lq"],
        }
    )
    for column in ("lq_eb", "log2_lq_eb"):
        if column in named.columns:
            frame[column] = named[column]
    if "sufficient" in named.columns:
        frame["meets_min_support"] = named["sufficient"]
    return frame.sort_values("n_group_publications", ascending=False).reset_index(drop=True)


def threatened_species_by_country(
    source: str | Path,
    *,
    indicators: Mapping[str, str] | None = None,
    iso3_col: str = "ipbes_iso3",
) -> pd.DataFrame:
    """Threatened-species counts per country from the curated WDI snapshot.

    Red List for birds, mammals and higher plants; FishBase for fish. See the module
    docstring — the four are not one source and must not be summed into a single
    "IUCN" total in prose.

    Reads the IPBES-joined snapshot so country, region and subregion arrive on the
    same crosswalk the evidence side uses. Aggregate entities (regions, income
    groups) are dropped — they would double-count their members.

    Countries missing any of the four indicators are returned with a null in that
    column and a false ``threat_counts_complete`` flag rather than being dropped,
    so an absent count is never silently read as a zero.
    """
    indicators = dict(indicators or THREAT_INDICATORS)
    out = _wdi_indicator_frame(source, indicators, iso3_col=iso3_col)
    count_columns = list(indicators.values())
    out["threat_counts_complete"] = out[count_columns].notna().all(axis=1)
    # Sums use min_count so an all-null row stays null rather than collapsing to 0.
    out["threatened_vertebrates"] = out[list(VERTEBRATE_COLUMNS)].sum(axis=1, min_count=1)
    out["threatened_vertebrates_land"] = out[list(LAND_VERTEBRATE_COLUMNS)].sum(
        axis=1, min_count=1
    )
    out["threatened_total"] = out[count_columns].sum(axis=1, min_count=1)
    out["vertebrate_share_of_threatened_pct"] = (
        out["threatened_vertebrates"] / out["threatened_total"].replace(0, np.nan) * 100.0
    )

    ordered = [
        "iso3",
        "country",
        "region",
        "subregion",
        "wdi_year",
        *count_columns,
        "threatened_vertebrates",
        "threatened_vertebrates_land",
        "threatened_total",
        "vertebrate_share_of_threatened_pct",
        "threat_counts_complete",
    ]
    return out[ordered].sort_values("threatened_total", ascending=False).reset_index(drop=True)


def match_evidence_and_threat(
    evidence: pd.DataFrame,
    threatened: pd.DataFrame,
    *,
    threat_columns: Iterable[str] = ("threatened_vertebrates", "threatened_vertebrates_land"),
    how: str = "inner",
    covariates: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Join the two sides and score each country's evidence against its threat load.

    ``how="inner"`` (the default) returns only countries carrying **both** evidence
    and threat counts — the rows any ratio is defined on. ``how="outer"`` keeps
    one-sided countries too, with a null ratio; the ``match`` column records which
    sides each country appeared on either way.

    **The choice changes no number.** Shares and ratios are computed over matched
    countries regardless, since a share of a total that includes countries absent
    from the other side is not comparable — the join only decides which rows are
    returned. What is dropped is never dropped silently: the counts and totals lost
    on each side are recorded in ``.attrs`` for the caller to report.

    Each ``evidence_to_<column>_ratio`` is the country's share of group evidence
    divided by its share of that threat count: 1.0 means evidence tracks threat,
    below 1.0 means under-studied relative to threat.

    ``covariates`` is an optional per-country frame (the research-capacity indicators)
    left-joined on ``iso3``. It is merged *here* rather than by the caller because
    ``DataFrame.merge`` discards ``.attrs``, and the skip-but-report counts this
    function records there would be silently lost on the way out.
    """
    if how not in {"inner", "outer"}:
        raise TaxaThreatGapError(f"how must be 'inner' or 'outer', got {how!r}")
    threat_columns = tuple(threat_columns)
    for column in threat_columns:
        if column not in threatened.columns:
            raise TaxaThreatGapError(f"Threat frame is missing column: {column!r}")
    if "n_group_publications" not in evidence.columns:
        raise TaxaThreatGapError("Evidence frame is missing n_group_publications.")

    # Both sides carry country/region/subregion off the same IPBES crosswalk, so the
    # labels agree where they overlap -- but they must be *coalesced*, not taken from
    # one side. Dropping them from the evidence side leaves every evidence-only row
    # unlabelled, and those rows (Taiwan, overseas territories) are the ones a reader
    # most needs named.
    LABELS = ["country", "region", "subregion"]
    merged = evidence.merge(
        threatened,
        on="iso3",
        how="outer",
        indicator="_side",
        validate="one_to_one",
        suffixes=("_evidence", "_threat"),
    )
    for column in LABELS:
        left, right = f"{column}_evidence", f"{column}_threat"
        if left in merged.columns and right in merged.columns:
            merged[column] = merged[left].combine_first(merged[right])
            merged = merged.drop(columns=[left, right])
    merged["match"] = merged["_side"].map(
        {"both": "both", "left_only": "evidence only", "right_only": "threat only"}
    )
    merged = merged.drop(columns="_side")

    both = merged["match"].eq("both")
    evidence_total = float(merged.loc[both, "n_group_publications"].sum())
    merged["matched_evidence_share_pct"] = np.where(
        both & (evidence_total > 0),
        merged["n_group_publications"] / evidence_total * 100.0,
        np.nan,
    )
    for column in threat_columns:
        threat_total = float(merged.loc[both, column].sum())
        share = np.where(
            both & (threat_total > 0), merged[column] / threat_total * 100.0, np.nan
        )
        share_name = f"matched_{column}_share_pct"
        merged[share_name] = share
        with np.errstate(divide="ignore", invalid="ignore"):
            merged[f"evidence_to_{column}_ratio"] = np.where(
                np.asarray(share) > 0, merged["matched_evidence_share_pct"] / share, np.nan
            )

    merged["broad_group"] = merged["broad_group"].ffill().bfill()

    if covariates is not None:
        if "iso3" not in covariates.columns:
            raise TaxaThreatGapError("Covariate frame needs an iso3 column.")
        if covariates["iso3"].duplicated().any():
            raise TaxaThreatGapError("Covariate frame must carry one row per iso3.")
        # Labels already arrived on both sides; a third copy would only collide.
        extra = covariates.drop(columns=LABELS, errors="ignore")
        merged = merged.merge(extra, on="iso3", how="left", validate="one_to_one")

    # Skip-but-report: whatever the join drops is counted before it goes.
    evidence_only = merged[merged["match"].eq("evidence only")]
    threat_only = merged[merged["match"].eq("threat only")]
    dropped = {
        "n_matched_countries": int(both.sum()),
        "n_evidence_only_countries": int(len(evidence_only)),
        "n_threat_only_countries": int(len(threat_only)),
        "evidence_only_publications": float(
            evidence_only["n_group_publications"].sum()
        ),
        "evidence_only_countries": sorted(evidence_only["iso3"].dropna()),
        "threat_only_countries": sorted(threat_only["iso3"].dropna()),
    }
    for column in threat_columns:
        dropped[f"threat_only_{column}"] = float(threat_only[column].sum())

    if how == "inner":
        merged = merged[merged["match"].eq("both")].copy()
    result = merged.sort_values(
        ["match", "n_group_publications"], ascending=[True, False]
    ).reset_index(drop=True)
    result.attrs.update(dropped)
    return result


def summarise_gap_by_region(
    matched: pd.DataFrame,
    *,
    threat_column: str = "threatened_vertebrates_land",
    region_col: str = "region",
) -> pd.DataFrame:
    """Aggregate the matched countries to IPBES regions and re-score the ratio.

    Regional totals are far more stable than country cells, so this is the reading
    to quote when a country ratio rests on a handful of publications.
    """
    both = matched[matched["match"].eq("both")]
    if both.empty:
        raise TaxaThreatGapError("No countries appear on both sides.")
    grouped = (
        both.groupby(region_col, dropna=False)
        .agg(
            n_countries=("iso3", "nunique"),
            n_group_publications=("n_group_publications", "sum"),
            threatened_species=(threat_column, "sum"),
        )
        .reset_index()
    )
    grouped["evidence_share_pct"] = (
        grouped["n_group_publications"] / grouped["n_group_publications"].sum() * 100.0
    )
    grouped["threat_share_pct"] = (
        grouped["threatened_species"] / grouped["threatened_species"].sum() * 100.0
    )
    grouped["evidence_to_threat_ratio"] = (
        grouped["evidence_share_pct"] / grouped["threat_share_pct"]
    )
    return grouped.sort_values("evidence_to_threat_ratio", ascending=False).reset_index(
        drop=True
    )


__all__ = [
    "LAND_VERTEBRATE_COLUMNS",
    "THREAT_INDICATORS",
    "TaxaThreatGapError",
    "VERTEBRATE_COLUMNS",
    "EXPORT_COLUMNS",
    "CAPACITY_INDICATORS",
    "evidence_by_country",
    "match_evidence_and_threat",
    "research_capacity_by_country",
    "select_export_columns",
    "summarise_gap_by_region",
    "threatened_species_by_country",
]


def regional_evidence_trend(
    included: pd.DataFrame,
    countries: pd.DataFrame,
    regional: pd.DataFrame,
    crosswalk: pd.DataFrame,
    *,
    group: str,
    id_col: str = "UT",
    group_col: str = "benchmark_groups",
    country_col: str = "pred_countries",
    year_col: str = "publication_year",
    region_col: str = "region",
    exclude_iso3: Iterable[str] = (),
) -> pd.DataFrame:
    """Each region's share of one group's evidence, by publication year.

    The geographic counterpart of ``taxonomic_attention_trend``, and it answers the
    same question on the other axis: the mismatch is one claim, whether it is closing
    is a second one, and a section that asserts persistence for taxonomy while staying
    silent on geography is claiming more than it tested.

    Counting matches :func:`summarise_gap_by_region` exactly — unique documents per
    country, summed within region — so a yearly share and the pooled share are the same
    statistic at different resolutions. A publication naming two regions counts once in
    each, so shares are of the summed total rather than of publications.

    The threat benchmark is a single snapshot and cannot vary by year; it is carried
    through as a constant so each year's ratio is against a fixed target.

    ``exclude_iso3`` drops named countries before counting — a publication naming an
    excluded country alongside others still counts for the ones that remain, only the
    excluded country's own attribution is removed. Built for the single-country
    robustness check a large regional swing invites (a country whose corpus coverage
    itself expanded over the window can drive most of an apparent correction), not for
    routine use: the un-excluded call is the one that backs the reported trend.
    """
    for frame, columns, name in (
        (included, {id_col, group_col, year_col}, "Included"),
        (countries, {id_col, country_col}, "Country"),
        (regional, {region_col, "threat_share_pct"}, "Regional"),
    ):
        missing = columns.difference(frame.columns)
        if missing:
            raise TaxaThreatGapError(f"{name} frame is missing columns: {sorted(missing)}")

    source = included[[id_col, group_col, year_col]].merge(countries, on=id_col, how="inner")
    source = source[
        source[group_col].map(lambda value: group in (value or ()))
    ].copy()
    if source.empty:
        raise TaxaThreatGapError(f"No publications carry the group {group!r}.")

    source[country_col] = source[country_col].map(
        lambda value: list(value) if isinstance(value, (list, tuple, np.ndarray)) else []
    )
    long = source.explode(country_col).dropna(subset=[country_col])
    long[country_col] = long[country_col].astype(str).str.strip()
    excluded = {str(code).strip() for code in exclude_iso3}
    if excluded:
        long = long[~long[country_col].isin(excluded)]
        if long.empty:
            raise TaxaThreatGapError(f"Excluding {sorted(excluded)} left no publications.")

    places = crosswalk[["iso3", region_col]].drop_duplicates("iso3")
    long = long.merge(places, left_on=country_col, right_on="iso3", how="inner")
    # Unique document per (year, country), then summed within region -- the same
    # convention the pooled regional table uses.
    counted = (
        long.drop_duplicates([id_col, "iso3"])
        .groupby([year_col, region_col])[id_col]
        .nunique()
        .rename("n_publications")
        .reset_index()
    )
    grid = pd.MultiIndex.from_product(
        [sorted(counted[year_col].unique()), sorted(counted[region_col].unique())],
        names=[year_col, region_col],
    )
    counted = counted.set_index([year_col, region_col]).reindex(grid, fill_value=0).reset_index()

    totals = counted.groupby(year_col)["n_publications"].transform("sum")
    counted["evidence_share_pct"] = np.where(
        totals > 0, counted["n_publications"] / totals * 100.0, np.nan
    )
    counted["n_publications_year"] = totals
    benchmark = regional.set_index(region_col)["threat_share_pct"]
    counted["threat_share_pct"] = counted[region_col].map(benchmark)
    counted["evidence_to_threat_ratio"] = (
        counted["evidence_share_pct"] / counted["threat_share_pct"]
    )
    return counted.sort_values([year_col, region_col]).reset_index(drop=True)


def summarise_regional_trend(
    trend: pd.DataFrame,
    *,
    region_col: str = "region",
    year_col: str = "publication_year",
    share_col: str = "evidence_share_pct",
) -> pd.DataFrame:
    """Start/end shares, slope per decade, and start/end ratios for each region.

    Deliberately the same columns as ``summarise_attention_trend`` so the taxonomic and
    geographic persistence claims are read off identically shaped tables.
    """
    missing = {region_col, year_col, share_col, "threat_share_pct"}.difference(trend.columns)
    if missing:
        raise TaxaThreatGapError(f"Trend frame is missing columns: {sorted(missing)}")

    rows: list[dict[str, Any]] = []
    for region, block in trend.groupby(region_col):
        block = block.sort_values(year_col)
        years = block[year_col].to_numpy(dtype=float)
        shares = block[share_col].to_numpy(dtype=float)
        usable = ~np.isnan(shares)
        slope = float(np.polyfit(years[usable], shares[usable], 1)[0] * 10.0) if usable.sum() > 1 else np.nan
        threat = float(block["threat_share_pct"].iloc[0])
        rows.append(
            {
                region_col: region,
                "start_year": int(years[0]),
                "end_year": int(years[-1]),
                "start_share_pct": float(shares[0]),
                "end_share_pct": float(shares[-1]),
                "change_pp": float(shares[-1] - shares[0]),
                "slope_pp_per_decade": slope,
                "threat_share_pct": threat,
                "start_ratio": float(shares[0] / threat) if threat else np.nan,
                "end_ratio": float(shares[-1] / threat) if threat else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values("end_ratio").reset_index(drop=True)


__all__ += ["regional_evidence_trend", "summarise_regional_trend"]
