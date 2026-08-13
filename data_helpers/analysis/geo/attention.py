"""Prepare an additive IPBES hierarchy of geographic research attention.

The integrated evidence corpus is one row per publication (``UT``), while its
country field is multi-valued.  Whole publication counts remain useful for
describing support in a country, but they are not additive: a publication about
two countries contributes one whole publication to both.  This module therefore
keeps whole counts and, separately, assigns each country-resolved publication a
total weight of one, split equally over its mapped countries.

The resulting fractional publication-equivalents are additive from country to
IPBES subregion, region, and root.  The complete IPBES mapping is retained,
including entries without an ISO3 key, so zero coverage and structurally
unresolvable mapping leaves remain visible rather than disappearing in an inner
join.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from data_helpers.analysis.geo.geography import load_crosswalk
from data_helpers.labels import parse_list_labels


ROOT_NODE_ID = "root:biodiversity-loss-evidence"
ROOT_LABEL = "Country-resolved biodiversity-loss evidence"

_NOT_APPLICABLE = {"NOTAPPLICABLE", "NA", "NONE"}
_AGGREGATE = {"ALLCOUNTRIES", "ALLREGIONS", "ALLSUBREGIONS", "GLOBAL", "WORLDWIDE"}
_UNCLEAR = {
    "UNCLEAR",
    "UNC",
    "UNCL",
    "UNK",
    "UNKN",
    "UNKNOWN",
    "UNS",
    "UNR",
    "UNL",
    "UNP",
    "",
}

_CROSSWALK_COLUMNS = ("iso3", "country", "region", "subregion")
_COUNTRY_OUTPUT_COLUMNS = (
    "node_id",
    "parent_id",
    "region",
    "subregion",
    "country",
    "iso3",
    "key_status",
    "whole_publications",
    "fractional_publication_equivalent",
    "attention_share_pct",
    "evidence_status",
    "below_evidence_threshold",
)
_HIERARCHY_COLUMNS = (
    "node_id",
    "parent_id",
    "depth",
    "node_type",
    "label",
    "region",
    "subregion",
    "country",
    "iso3",
    "key_status",
    "whole_publications",
    "fractional_publication_equivalent",
    "attention_share_pct",
    "within_parent_share_pct",
    "evidence_status",
    "below_evidence_threshold",
    "child_count",
)


class GeographyAttentionError(ValueError):
    """Raised when evidence or the IPBES hierarchy violates its grain."""


@dataclass(frozen=True)
class GeographyAttentionResult:
    """Notebook-ready tables for the geographic-attention result.

    ``whole_publications`` is a distinct-UT count and is intentionally not
    additive across siblings.  ``fractional_publication_equivalent`` and its
    percentage columns are the additive plotting measures.
    """

    assignments: pd.DataFrame
    countries: pd.DataFrame
    hierarchy: pd.DataFrame
    coverage: pd.DataFrame
    coverage_reasons: pd.DataFrame
    audit: pd.DataFrame
    unresolved_tokens: pd.DataFrame
    excluded_publications: pd.DataFrame


def _normalise_token(value: object) -> str:
    return re.sub(r"[^A-Za-z]", "", str(value)).upper()


def _slug(value: object) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).casefold()).strip("-")
    return slug or "unnamed"


def _region_id(region: str) -> str:
    return f"region:{_slug(region)}"


def _subregion_id(region: str, subregion: str) -> str:
    return f"subregion:{_slug(region)}:{_slug(subregion)}"


def _country_id(row: pd.Series) -> str:
    if row["key_status"] == "valid_iso3":
        return f"country:{row['iso3']}"
    return (
        "country:unresolvable:"
        f"{_slug(row['region'])}:{_slug(row['subregion'])}:{_slug(row['country'])}"
    )


def _prepare_crosswalk(crosswalk: pd.DataFrame | None) -> pd.DataFrame:
    source = load_crosswalk() if crosswalk is None else crosswalk
    missing = set(_CROSSWALK_COLUMNS).difference(source.columns)
    if missing:
        raise GeographyAttentionError(
            f"IPBES crosswalk lacks required columns: {sorted(missing)}"
        )
    if source.empty:
        raise GeographyAttentionError("IPBES crosswalk must contain at least one leaf.")

    work = source.loc[:, list(_CROSSWALK_COLUMNS)].copy().reset_index(drop=True)
    for column in ("country", "region", "subregion"):
        if work[column].isna().any():
            raise GeographyAttentionError(
                f"IPBES crosswalk contains missing {column} values."
            )
        work[column] = work[column].astype(str).str.strip()
        if work[column].eq("").any():
            raise GeographyAttentionError(
                f"IPBES crosswalk contains blank {column} values."
            )

    work["iso3"] = work["iso3"].fillna("").astype(str).str.strip().str.upper()
    nonblank_invalid = work["iso3"].ne("") & ~work["iso3"].str.fullmatch(
        r"[A-Z]{3}"
    )
    if nonblank_invalid.any():
        bad = work.loc[nonblank_invalid, "iso3"].drop_duplicates().tolist()
        raise GeographyAttentionError(
            "Nonblank IPBES country keys must be three ASCII letters; "
            f"found {bad}."
        )

    duplicated_paths = work.duplicated(["region", "subregion", "country"], keep=False)
    if duplicated_paths.any():
        examples = work.loc[
            duplicated_paths, ["region", "subregion", "country"]
        ].head(10).to_dict("records")
        raise GeographyAttentionError(
            f"IPBES country paths must be unique; duplicates include {examples}."
        )
    duplicated_iso3 = work.loc[work["iso3"].ne(""), "iso3"].duplicated(keep=False)
    if duplicated_iso3.any():
        codes = (
            work.loc[work["iso3"].ne("")]
            .loc[duplicated_iso3, "iso3"]
            .drop_duplicates()
            .tolist()
        )
        raise GeographyAttentionError(
            f"Each nonblank ISO3 must identify one IPBES leaf; duplicates: {codes}."
        )

    work["key_status"] = np.where(
        work["iso3"].ne(""), "valid_iso3", "unresolvable_key"
    )
    work["_mapping_order"] = np.arange(len(work), dtype=int)
    work["parent_id"] = [
        _subregion_id(region, subregion)
        for region, subregion in zip(
            work["region"], work["subregion"], strict=True
        )
    ]
    work["node_id"] = work.apply(_country_id, axis=1)
    if work["node_id"].duplicated().any():
        raise GeographyAttentionError("Generated country node IDs are not unique.")
    return work


def filter_biodiversity_loss_publications(
    evidence: pd.DataFrame,
    *,
    start_year: int = 2000,
    end_year: int = 2025,
    direction: str = "negative",
) -> pd.DataFrame:
    """Validate the prepared UT grain and retain one loss-analysis window.

    Publication years are coerced to nullable integers in the returned copy;
    records with missing or non-numeric years do not enter the window.
    """
    required = {"UT", "publication_year", "s2_dir", "pred_countries"}
    missing = required.difference(evidence.columns)
    if missing:
        raise GeographyAttentionError(
            f"Prepared evidence lacks required columns: {sorted(missing)}"
        )
    if evidence["UT"].isna().any() or evidence["UT"].duplicated().any():
        raise GeographyAttentionError(
            "Prepared evidence must contain one non-missing row per UT."
        )
    if (
        not isinstance(start_year, int)
        or isinstance(start_year, bool)
        or not isinstance(end_year, int)
        or isinstance(end_year, bool)
    ):
        raise GeographyAttentionError("start_year and end_year must be integers.")
    if start_year > end_year:
        raise GeographyAttentionError("start_year must not exceed end_year.")
    if not isinstance(direction, str) or not direction.strip():
        raise GeographyAttentionError("direction must be a nonblank string.")

    work = evidence.copy()
    work["publication_year"] = pd.to_numeric(
        work["publication_year"], errors="coerce"
    ).astype("Int64")
    mask = work["s2_dir"].eq(direction) & work["publication_year"].between(
        start_year, end_year
    )
    return work.loc[mask].copy()


def _classify_country_token(
    token: object, valid_iso3: set[str]
) -> tuple[str, str | None]:
    normalised = _normalise_token(token)
    if normalised in _NOT_APPLICABLE:
        return "not_applicable", None
    if normalised in _AGGREGATE:
        return "aggregate", None
    if normalised in _UNCLEAR:
        return "unclear", None
    if normalised in valid_iso3:
        return "mapped", normalised
    return "unresolved", None


def _safe_percent(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    result = pd.Series(0.0, index=numerator.index, dtype=float)
    positive = denominator.gt(0)
    result.loc[positive] = (
        numerator.loc[positive].astype(float)
        / denominator.loc[positive].astype(float)
        * 100.0
    )
    return result


def _build_hierarchy(
    assignments: pd.DataFrame,
    countries: pd.DataFrame,
    *,
    mapped_publications: int,
) -> pd.DataFrame:
    regions = countries[["region"]].drop_duplicates().copy()
    regions["node_id"] = regions["region"].map(_region_id)
    regions["parent_id"] = ROOT_NODE_ID

    subregions = countries[["region", "subregion"]].drop_duplicates().copy()
    subregions["node_id"] = [
        _subregion_id(region, subregion)
        for region, subregion in zip(
            subregions["region"], subregions["subregion"], strict=True
        )
    ]
    subregions["parent_id"] = subregions["region"].map(_region_id)

    if assignments.empty:
        region_values = pd.DataFrame(
            columns=[
                "region",
                "whole_publications",
                "fractional_publication_equivalent",
            ]
        )
        subregion_values = pd.DataFrame(
            columns=[
                "region",
                "subregion",
                "whole_publications",
                "fractional_publication_equivalent",
            ]
        )
    else:
        region_values = (
            assignments.groupby("region", observed=True, sort=False)
            .agg(
                whole_publications=("UT", "nunique"),
                fractional_publication_equivalent=("fractional_weight", "sum"),
            )
            .reset_index()
        )
        subregion_values = (
            assignments.groupby(["region", "subregion"], observed=True, sort=False)
            .agg(
                whole_publications=("UT", "nunique"),
                fractional_publication_equivalent=("fractional_weight", "sum"),
            )
            .reset_index()
        )

    regions = regions.merge(
        region_values, on="region", how="left", validate="one_to_one"
    )
    subregions = subregions.merge(
        subregion_values,
        on=["region", "subregion"],
        how="left",
        validate="one_to_one",
    )
    for frame in (regions, subregions):
        frame["whole_publications"] = frame["whole_publications"].fillna(0).astype(int)
        frame["fractional_publication_equivalent"] = frame[
            "fractional_publication_equivalent"
        ].fillna(0.0).astype(float)
        frame["attention_share_pct"] = (
            frame["fractional_publication_equivalent"] / mapped_publications * 100.0
            if mapped_publications
            else 0.0
        )
        frame["evidence_status"] = np.where(
            frame["whole_publications"].gt(0), "observed", "zero_captured"
        )

    root = pd.DataFrame(
        [
            {
                "node_id": ROOT_NODE_ID,
                "parent_id": pd.NA,
                "depth": 0,
                "node_type": "root",
                "label": ROOT_LABEL,
                "region": pd.NA,
                "subregion": pd.NA,
                "country": pd.NA,
                "iso3": pd.NA,
                "key_status": pd.NA,
                "whole_publications": mapped_publications,
                "fractional_publication_equivalent": float(mapped_publications),
                "attention_share_pct": 100.0 if mapped_publications else 0.0,
                "within_parent_share_pct": 100.0 if mapped_publications else 0.0,
                "evidence_status": (
                    "observed" if mapped_publications else "zero_captured"
                ),
                "below_evidence_threshold": pd.NA,
                "child_count": len(regions),
            }
        ]
    )

    region_rows = regions.assign(
        depth=1,
        node_type="region",
        label=regions["region"],
        subregion=pd.NA,
        country=pd.NA,
        iso3=pd.NA,
        key_status=pd.NA,
        within_parent_share_pct=regions["attention_share_pct"],
        below_evidence_threshold=pd.NA,
        child_count=regions["region"].map(
            subregions.groupby("region", sort=False).size()
        ),
    )

    region_denominators = regions.set_index("region")[
        "fractional_publication_equivalent"
    ]
    subregion_rows = subregions.assign(
        depth=2,
        node_type="subregion",
        label=subregions["subregion"],
        country=pd.NA,
        iso3=pd.NA,
        key_status=pd.NA,
        below_evidence_threshold=pd.NA,
        child_count=pd.Series(
            list(zip(subregions["region"], subregions["subregion"], strict=True)),
            index=subregions.index,
        ).map(countries.groupby(["region", "subregion"], sort=False).size()),
    )
    subregion_denominators = subregion_rows["region"].map(region_denominators)
    subregion_rows["within_parent_share_pct"] = _safe_percent(
        subregion_rows["fractional_publication_equivalent"],
        subregion_denominators,
    )

    country_rows = countries.copy()
    country_rows["depth"] = 3
    country_rows["node_type"] = "country"
    country_rows["label"] = country_rows["country"]
    country_rows["child_count"] = 0
    country_denominators = country_rows.set_index(
        ["region", "subregion"]
    ).index.map(
        subregions.set_index(["region", "subregion"])[
            "fractional_publication_equivalent"
        ]
    )
    country_rows["within_parent_share_pct"] = _safe_percent(
        country_rows["fractional_publication_equivalent"],
        pd.Series(country_denominators, index=country_rows.index),
    )

    hierarchy_frames = [
        root,
        region_rows.loc[:, list(_HIERARCHY_COLUMNS)],
        subregion_rows.loc[:, list(_HIERARCHY_COLUMNS)],
        country_rows.loc[:, list(_HIERARCHY_COLUMNS)],
    ]
    hierarchy = pd.concat(
        [frame.astype(object) for frame in hierarchy_frames],
        ignore_index=True,
    )
    hierarchy["whole_publications"] = pd.to_numeric(
        hierarchy["whole_publications"], errors="coerce"
    ).astype("Int64")
    for column in (
        "fractional_publication_equivalent",
        "attention_share_pct",
        "within_parent_share_pct",
    ):
        hierarchy[column] = pd.to_numeric(
            hierarchy[column], errors="coerce"
        ).astype("Float64")
    hierarchy["child_count"] = hierarchy["child_count"].astype(int)
    hierarchy["below_evidence_threshold"] = hierarchy[
        "below_evidence_threshold"
    ].astype(
        "boolean"
    )
    return hierarchy.loc[:, list(_HIERARCHY_COLUMNS)]


def _validate_result(
    result: GeographyAttentionResult,
    *,
    low_evidence_threshold: int,
) -> None:
    assignments = result.assignments
    countries = result.countries
    hierarchy = result.hierarchy
    excluded_publications = result.excluded_publications

    if excluded_publications.duplicated(["UT", "token"]).any():
        raise GeographyAttentionError(
            "Excluded publication-token rows must be unique."
        )
    if set(excluded_publications["UT"]).intersection(assignments["UT"]):
        raise GeographyAttentionError(
            "A complete-case-excluded publication entered mapped assignments."
        )

    if assignments.duplicated(["UT", "iso3"]).any():
        raise GeographyAttentionError(
            "Mapped assignments are not unique by UT and ISO3."
        )
    if not assignments.empty:
        per_publication = assignments.groupby("UT")["fractional_weight"].sum()
        if not np.allclose(per_publication.to_numpy(), 1.0):
            raise GeographyAttentionError(
                "Fractional country weights do not sum to one per publication."
            )

    valid_countries = countries.loc[
        countries["key_status"].eq("valid_iso3")
    ].set_index("iso3")
    expected_leaf_values = (
        assignments.groupby("iso3", observed=True)
        .agg(
            whole_publications=("UT", "nunique"),
            fractional_publication_equivalent=("fractional_weight", "sum"),
        )
        .reindex(valid_countries.index, fill_value=0)
    )
    if not np.array_equal(
        valid_countries["whole_publications"].astype(int).to_numpy(),
        expected_leaf_values["whole_publications"].astype(int).to_numpy(),
    ):
        raise GeographyAttentionError(
            "Country whole-publication counts do not match mapped assignments."
        )
    if not np.allclose(
        valid_countries["fractional_publication_equivalent"].astype(float),
        expected_leaf_values["fractional_publication_equivalent"].astype(float),
    ):
        raise GeographyAttentionError(
            "Country fractional weights do not match mapped assignments."
        )

    mapped_publications = int(assignments["UT"].nunique())
    expected_shares = (
        expected_leaf_values["fractional_publication_equivalent"].astype(float)
        / mapped_publications
        * 100.0
        if mapped_publications
        else np.zeros(len(expected_leaf_values), dtype=float)
    )
    if not np.allclose(
        valid_countries["attention_share_pct"].astype(float),
        expected_shares,
    ):
        raise GeographyAttentionError(
            "Country attention shares do not match mapped assignments."
        )
    expected_below_threshold = valid_countries["whole_publications"].lt(
        low_evidence_threshold
    )
    if not valid_countries["below_evidence_threshold"].eq(
        expected_below_threshold
    ).all():
        raise GeographyAttentionError(
            "Country below-threshold flags do not match whole-publication counts."
        )

    unresolvable = countries["key_status"].eq("unresolvable_key")
    unresolvable_value_columns = [
        "whole_publications",
        "fractional_publication_equivalent",
        "attention_share_pct",
        "below_evidence_threshold",
    ]
    if countries.loc[unresolvable, unresolvable_value_columns].notna().any().any():
        raise GeographyAttentionError(
            "Unresolvable mapping leaves must not carry measured evidence values."
        )
    if not assignments.empty and not assignments["mapped_country_count"].eq(
        assignments.groupby("UT")["iso3"].transform("nunique")
    ).all():
        raise GeographyAttentionError(
            "mapped_country_count does not match assignment cardinality."
        )

    allowed_statuses = {"observed", "zero_captured", "unresolvable_key"}
    if not set(countries["evidence_status"]).issubset(allowed_statuses):
        raise GeographyAttentionError("Country evidence statuses are invalid.")
    observed = countries["evidence_status"].eq("observed")
    zero = countries["evidence_status"].eq("zero_captured")
    unresolvable = countries["evidence_status"].eq("unresolvable_key")
    if not (
        observed.eq(
            countries["key_status"].eq("valid_iso3")
            & countries["whole_publications"].gt(0)
        ).all()
        and zero.eq(
            countries["key_status"].eq("valid_iso3")
            & countries["whole_publications"].eq(0)
        ).all()
        and unresolvable.eq(countries["key_status"].eq("unresolvable_key")).all()
    ):
        raise GeographyAttentionError("Country status/count reconciliation failed.")

    if hierarchy["node_id"].duplicated().any():
        raise GeographyAttentionError("Hierarchy node IDs are not unique.")
    ids = set(hierarchy["node_id"])
    nonroot_parents = set(hierarchy.loc[hierarchy["depth"].gt(0), "parent_id"])
    if not nonroot_parents.issubset(ids):
        raise GeographyAttentionError("Hierarchy contains a missing parent node.")

    root = hierarchy.loc[hierarchy["depth"].eq(0)]
    if len(root) != 1:
        raise GeographyAttentionError("Hierarchy must contain exactly one root.")
    root_weight = float(root["fractional_publication_equivalent"].iloc[0])
    country_weight = float(countries["fractional_publication_equivalent"].sum())
    region_weight = float(
        hierarchy.loc[
            hierarchy["node_type"].eq("region"),
            "fractional_publication_equivalent",
        ].sum()
    )
    if not (
        np.isclose(root_weight, country_weight)
        and np.isclose(root_weight, region_weight)
    ):
        raise GeographyAttentionError("Hierarchy fractional weights do not reconcile.")

    measured_hierarchy = hierarchy["fractional_publication_equivalent"].notna()
    expected_global_share = (
        hierarchy.loc[measured_hierarchy, "fractional_publication_equivalent"]
        .astype(float)
        / root_weight
        * 100.0
        if root_weight
        else np.zeros(int(measured_hierarchy.sum()), dtype=float)
    )
    if not np.allclose(
        hierarchy.loc[measured_hierarchy, "attention_share_pct"].astype(float),
        expected_global_share,
    ):
        raise GeographyAttentionError(
            "Hierarchy global attention shares do not match fractional weights."
        )

    parent_weights = hierarchy.set_index("node_id")[
        "fractional_publication_equivalent"
    ]
    child_sums = (
        hierarchy.loc[hierarchy["depth"].gt(0)]
        .groupby("parent_id", sort=False)["fractional_publication_equivalent"]
        .sum()
    )
    if not np.allclose(
        child_sums.to_numpy(), child_sums.index.map(parent_weights).to_numpy()
    ):
        raise GeographyAttentionError("A hierarchy parent does not equal its children.")

    measured_children = hierarchy["depth"].gt(0) & hierarchy[
        "fractional_publication_equivalent"
    ].notna()
    child_parent_weights = hierarchy.loc[measured_children, "parent_id"].map(
        parent_weights
    ).astype(float)
    child_weights = hierarchy.loc[
        measured_children, "fractional_publication_equivalent"
    ].astype(float)
    expected_parent_share = np.divide(
        child_weights.to_numpy() * 100.0,
        child_parent_weights.to_numpy(),
        out=np.zeros(len(child_weights), dtype=float),
        where=child_parent_weights.to_numpy() > 0,
    )
    if not np.allclose(
        hierarchy.loc[measured_children, "within_parent_share_pct"].astype(float),
        expected_parent_share,
    ):
        raise GeographyAttentionError(
            "Hierarchy within-parent shares do not match fractional weights."
        )

    coverage = result.coverage.set_index("coverage_status")["publication_count"]
    if set(coverage.index) != {"mapped_country", "no_mapped_country"}:
        raise GeographyAttentionError("Coverage rows must be mutually exhaustive.")
    analysis_total = int(
        result.audit.set_index("metric").loc["analysis_publications", "value"]
    )
    audit = result.audit.set_index("metric")["value"]
    if int(audit["window_publications_before_country_validation"]) != (
        analysis_total + excluded_publications["UT"].nunique()
    ):
        raise GeographyAttentionError(
            "Complete-case exclusions do not reconcile to the publication window."
        )
    if int(coverage.sum()) != analysis_total:
        raise GeographyAttentionError(
            "Coverage counts do not sum to the analysis corpus."
        )
    if int(result.coverage_reasons["publication_count"].sum()) != int(
        coverage["no_mapped_country"]
    ):
        raise GeographyAttentionError(
            "Coverage-reason counts do not reconcile to no-mapped-country publications."
        )


def prepare_geography_attention(
    evidence: pd.DataFrame,
    *,
    start_year: int = 2000,
    end_year: int = 2025,
    direction: str = "negative",
    low_evidence_threshold: int = 100,
    crosswalk: pd.DataFrame | None = None,
) -> GeographyAttentionResult:
    """Build full-country and additive hierarchy tables for Result 05.

    Publications containing any unresolved country token are excluded in full
    before country weights are calculated.  The denominator for
    ``attention_share_pct`` is the number of retained publications with at
    least one mapped IPBES country.  Retained publications without a mapped
    country remain explicit in ``coverage`` and ``audit`` but cannot be assigned
    to an IPBES hierarchy leaf.
    """
    if (
        not isinstance(low_evidence_threshold, int)
        or isinstance(low_evidence_threshold, bool)
        or low_evidence_threshold <= 1
    ):
        raise GeographyAttentionError(
            "low_evidence_threshold must be an integer greater than one."
        )
    mapping = _prepare_crosswalk(crosswalk)
    filtered = filter_biodiversity_loss_publications(
        evidence,
        start_year=start_year,
        end_year=end_year,
        direction=direction,
    )

    parsed_before_exclusion = filtered[["UT", "pred_countries"]].copy()
    parsed_before_exclusion["_tokens"] = parsed_before_exclusion[
        "pred_countries"
    ].map(parse_list_labels)
    mentions_before_exclusion = parsed_before_exclusion[
        ["UT", "_tokens"]
    ].explode("_tokens").dropna(subset=["_tokens"])

    valid_iso3 = set(mapping.loc[mapping["key_status"].eq("valid_iso3"), "iso3"])
    classified = mentions_before_exclusion["_tokens"].map(
        lambda token: _classify_country_token(token, valid_iso3)
    )
    mentions_before_exclusion["bucket"] = classified.map(lambda pair: pair[0])
    mentions_before_exclusion["iso3"] = classified.map(lambda pair: pair[1])

    unresolved_mentions = mentions_before_exclusion.loc[
        mentions_before_exclusion["bucket"].eq("unresolved")
    ].copy()
    excluded_ids = set(unresolved_mentions["UT"])
    excluded_publications = (
        unresolved_mentions.assign(
            token=lambda frame: frame["_tokens"].astype(str).str.strip()
        )
        .loc[:, ["UT", "token"]]
        .drop_duplicates()
        .sort_values(["UT", "token"], kind="stable")
        .reset_index(drop=True)
    )
    excluded_publications["exclusion_reason"] = "unresolved_country_token"

    filtered = filtered.loc[~filtered["UT"].isin(excluded_ids)].copy()
    parsed = parsed_before_exclusion.loc[
        ~parsed_before_exclusion["UT"].isin(excluded_ids)
    ].copy()
    mentions = mentions_before_exclusion.loc[
        ~mentions_before_exclusion["UT"].isin(excluded_ids)
    ].copy()
    empty_country_lists = int(parsed["_tokens"].map(len).eq(0).sum())

    mapped_mentions = mentions.loc[
        mentions["bucket"].eq("mapped"), ["UT", "iso3"]
    ]
    assignment_keys = mapped_mentions.drop_duplicates(["UT", "iso3"]).copy()
    mapped_country_count = assignment_keys.groupby("UT")["iso3"].nunique()
    assignment_keys["mapped_country_count"] = assignment_keys["UT"].map(
        mapped_country_count
    )
    assignment_keys["fractional_weight"] = (
        1.0 / assignment_keys["mapped_country_count"]
    )
    assignments = assignment_keys.merge(
        mapping.loc[
            mapping["key_status"].eq("valid_iso3"),
            ["iso3", "country", "region", "subregion", "_mapping_order"],
        ],
        on="iso3",
        how="left",
        sort=False,
        validate="many_to_one",
    )
    assignments = assignments.sort_values(
        ["UT", "_mapping_order"], kind="stable"
    ).reset_index(drop=True)
    assignments = assignments[
        [
            "UT",
            "iso3",
            "country",
            "region",
            "subregion",
            "mapped_country_count",
            "fractional_weight",
        ]
    ]

    mapped_publications = int(assignments["UT"].nunique())
    if assignments.empty:
        leaf_values = pd.DataFrame(
            columns=[
                "iso3",
                "whole_publications",
                "fractional_publication_equivalent",
            ]
        )
    else:
        leaf_values = (
            assignments.groupby("iso3", observed=True, sort=False)
            .agg(
                whole_publications=("UT", "nunique"),
                fractional_publication_equivalent=("fractional_weight", "sum"),
            )
            .reset_index()
        )

    # Blank ISO3 values deliberately repeat across the structurally
    # unresolvable mapping leaves, so this is many-to-one on the left even
    # though every valid ISO3 is unique.
    countries = mapping.merge(
        leaf_values, on="iso3", how="left", sort=False, validate="many_to_one"
    )
    resolvable = countries["key_status"].eq("valid_iso3")
    countries["whole_publications"] = pd.to_numeric(
        countries["whole_publications"], errors="coerce"
    ).astype("Int64")
    countries.loc[
        resolvable & countries["whole_publications"].isna(),
        "whole_publications",
    ] = 0
    countries.loc[~resolvable, "whole_publications"] = pd.NA

    countries["fractional_publication_equivalent"] = pd.to_numeric(
        countries["fractional_publication_equivalent"], errors="coerce"
    ).astype("Float64")
    countries.loc[
        resolvable & countries["fractional_publication_equivalent"].isna(),
        "fractional_publication_equivalent",
    ] = 0.0
    countries.loc[~resolvable, "fractional_publication_equivalent"] = pd.NA

    countries["attention_share_pct"] = pd.Series(
        pd.NA, index=countries.index, dtype="Float64"
    )
    if mapped_publications:
        countries.loc[resolvable, "attention_share_pct"] = (
            countries.loc[resolvable, "fractional_publication_equivalent"]
            / mapped_publications
            * 100.0
        )
    else:
        countries.loc[resolvable, "attention_share_pct"] = 0.0
    countries["evidence_status"] = np.select(
        [
            countries["key_status"].eq("unresolvable_key"),
            countries["whole_publications"].gt(0).fillna(False),
        ],
        ["unresolvable_key", "observed"],
        default="zero_captured",
    )
    countries["below_evidence_threshold"] = pd.Series(
        pd.NA, index=countries.index, dtype="boolean"
    )
    countries.loc[resolvable, "below_evidence_threshold"] = countries.loc[
        resolvable, "whole_publications"
    ].lt(low_evidence_threshold)
    countries = countries.sort_values("_mapping_order", kind="stable")
    countries = countries.loc[:, list(_COUNTRY_OUTPUT_COLUMNS)].reset_index(drop=True)

    hierarchy = _build_hierarchy(
        assignments,
        countries,
        mapped_publications=mapped_publications,
    )

    analysis_publications = len(filtered)
    no_mapped_publications = analysis_publications - mapped_publications
    coverage = pd.DataFrame(
        {
            "coverage_status": ["mapped_country", "no_mapped_country"],
            "publication_count": [mapped_publications, no_mapped_publications],
            "total_publications": [analysis_publications, analysis_publications],
        }
    )
    coverage["share_pct"] = (
        coverage["publication_count"] / analysis_publications * 100.0
        if analysis_publications
        else 0.0
    )

    mention_bucket_sets = mentions.groupby("UT", sort=False)["bucket"].agg(
        lambda values: frozenset(values)
    )
    no_mapped_ids = filtered.loc[
        ~filtered["UT"].isin(assignments["UT"]), "UT"
    ]
    parsed_token_counts = parsed.set_index("UT")["_tokens"].map(len)
    reason_order = ("not_applicable", "unclear", "aggregate", "unresolved")

    def coverage_reason(publication_id: object) -> str:
        if int(parsed_token_counts.loc[publication_id]) == 0:
            return "empty_country_list"
        buckets = mention_bucket_sets.get(publication_id, frozenset())
        return "+".join(bucket for bucket in reason_order if bucket in buckets)

    coverage_reasons = (
        no_mapped_ids.map(coverage_reason)
        .value_counts(sort=False)
        .rename_axis("coverage_reason")
        .rename("publication_count")
        .reset_index()
    )
    if coverage_reasons.empty:
        coverage_reasons = pd.DataFrame(
            columns=[
                "coverage_reason",
                "publication_count",
                "share_of_no_mapped_pct",
                "share_of_analysis_pct",
            ]
        )
    else:
        coverage_reasons["share_of_no_mapped_pct"] = (
            coverage_reasons["publication_count"] / no_mapped_publications * 100.0
            if no_mapped_publications
            else 0.0
        )
        coverage_reasons["share_of_analysis_pct"] = (
            coverage_reasons["publication_count"] / analysis_publications * 100.0
            if analysis_publications
            else 0.0
        )
        coverage_reasons = coverage_reasons.sort_values(
            ["publication_count", "coverage_reason"],
            ascending=[False, True],
            kind="stable",
        ).reset_index(drop=True)

    unresolved_tokens = (
        unresolved_mentions
        .groupby("_tokens", sort=False)["UT"]
        .agg(mention_count="size", publication_count="nunique")
        .rename_axis("token")
        .reset_index()
        .sort_values(["mention_count", "token"], ascending=[False, True])
        .reset_index(drop=True)
    )
    if unresolved_tokens.empty:
        unresolved_tokens = pd.DataFrame(
            columns=["token", "mention_count", "publication_count"]
        )

    bucket_counts = mentions["bucket"].value_counts().to_dict()
    mapped_before_exclusion = set(
        mentions_before_exclusion.loc[
            mentions_before_exclusion["bucket"].eq("mapped"), "UT"
        ]
    )
    metrics: list[tuple[str, int | float]] = [
        ("input_publications", len(evidence)),
        (
            "direction_matching_publications",
            int(evidence["s2_dir"].eq(direction).sum()),
        ),
        (
            "window_publications_before_country_validation",
            analysis_publications + len(excluded_ids),
        ),
        ("complete_case_excluded_publications", len(excluded_ids)),
        ("analysis_publications", analysis_publications),
        ("mapped_country_publications", mapped_publications),
        ("no_mapped_country_publications", no_mapped_publications),
        (
            "mapped_country_coverage_pct",
            mapped_publications / analysis_publications * 100.0
            if analysis_publications
            else 0.0,
        ),
        ("empty_country_list_publications", empty_country_lists),
    ]
    for bucket in ("mapped", "not_applicable", "unclear", "aggregate", "unresolved"):
        metrics.append((f"mentions_{bucket}", int(bucket_counts.get(bucket, 0))))
    metrics.extend(
        [
            ("unresolved_mentions_before_exclusion", len(unresolved_mentions)),
            ("unresolved_token_publications", len(excluded_ids)),
            ("mapped_publication_country_assignments", len(assignments)),
            (
                "duplicate_mapped_mentions_removed",
                len(mapped_mentions) - len(assignment_keys),
            ),
            (
                "fractional_publication_equivalents",
                float(assignments["fractional_weight"].sum()),
            ),
            ("low_evidence_threshold", low_evidence_threshold),
            ("mapping_leaves", len(countries)),
            (
                "mapping_valid_iso3_leaves",
                int(countries["key_status"].eq("valid_iso3").sum()),
            ),
            (
                "mapping_unresolvable_key_leaves",
                int(countries["key_status"].eq("unresolvable_key").sum()),
            ),
            (
                "observed_country_leaves",
                int(countries["evidence_status"].eq("observed").sum()),
            ),
            (
                "zero_captured_country_leaves",
                int(countries["evidence_status"].eq("zero_captured").sum()),
            ),
            (
                "supported_country_leaves",
                int(
                    (
                        countries["evidence_status"].eq("observed")
                        & countries["whole_publications"]
                        .ge(low_evidence_threshold)
                        .fillna(False)
                    ).sum()
                ),
            ),
            (
                "observed_below_threshold_country_leaves",
                int(
                    (
                        countries["evidence_status"].eq("observed")
                        & countries["whole_publications"]
                        .lt(low_evidence_threshold)
                        .fillna(False)
                    ).sum()
                ),
            ),
            (
                "below_threshold_valid_iso3_leaves",
                int(countries["below_evidence_threshold"].sum()),
            ),
            (
                "excluded_publications_with_mapped_country_before_exclusion",
                len(excluded_ids.intersection(mapped_before_exclusion)),
            ),
        ]
    )
    audit = pd.DataFrame(metrics, columns=["metric", "value"])

    result = GeographyAttentionResult(
        assignments=assignments,
        countries=countries,
        hierarchy=hierarchy,
        coverage=coverage,
        coverage_reasons=coverage_reasons,
        audit=audit,
        unresolved_tokens=unresolved_tokens,
        excluded_publications=excluded_publications,
    )
    _validate_result(result, low_evidence_threshold=low_evidence_threshold)
    return result


__all__ = [
    "GeographyAttentionError",
    "GeographyAttentionResult",
    "ROOT_LABEL",
    "ROOT_NODE_ID",
    "filter_biodiversity_loss_publications",
    "prepare_geography_attention",
]
