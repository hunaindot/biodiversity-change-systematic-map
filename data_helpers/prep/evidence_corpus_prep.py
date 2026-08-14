"""Prepare reusable screening and eligible biodiversity-evidence handoffs.

The full screening grain and the eligible evidence grain are deliberately
separate. Screening results use compact aggregates over every screened record;
substantive results use a one-row-per-UT corpus containing screening metadata
and configured coding dimensions, plus a separate text sidecar.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pandas.api.types import is_bool_dtype

from data_helpers.labels import parse_list_labels
from data_helpers.prep._provenance import source_signature


SCREENING_SCHEMA_VERSION = 1
EVIDENCE_SCHEMA_VERSION = 4
REASON_COLUMNS = ("s1_r", "s2_r", "s3_r", "s4_r")
STAGE_NAMES = {
    "s1_r": "Q1: biodiversity change",
    "s2_r": "Q2: direction of change",
    "s3_r": "Q3: anthropogenic driver",
    "s4_r": "Q4: driver-change linkage",
}
SCREENING_ANALYSIS_COLUMNS = (
    "UT",
    "publication_year",
    "source",
    "is_eligible",
    "eligibility",
    *REASON_COLUMNS,
    "s2_dir",
)
EVIDENCE_LIST_COLUMNS = (
    "driver",
    "pred_threat_l0",
    "pred_regions",
    "pred_subregions",
    "pred_countries",
    "locales",
    "realm",
    "pred_methods_data_collection",
    "pred_methods_analysis",
    "pred_comparison_types",
    "taxa_domain_labels",
    "taxa_kingdom_labels",
    "taxa_subkingdom_labels",
    "taxa_phylum_labels",
    "taxa_class_labels",
    "taxa_order_labels",
    "taxa_family_labels",
    "taxa_genus_labels",
    "taxa_species_labels",
)
GEOGRAPHY_LIST_COLUMNS = (
    "pred_regions",
    "pred_subregions",
    "pred_countries",
)
_NOT_APPLICABLE_LABEL = "Not Applicable"
_UNCLEAR_LABEL = "Unclear"
_SPECIAL_COUNTRY_TOKENS = {
    "",
    "NA",
    "NONE",
    "NOTAPPLICABLE",
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
    "ALLCOUNTRIES",
    "ALLREGIONS",
    "ALLSUBREGIONS",
    "GLOBAL",
    "WORLDWIDE",
}
EVIDENCE_CORE_COLUMNS = (
    "UT",
    "title",
    "authors",
    "source",
    "publication_year",
    "doi",
    "eligibility",
    "s1_r",
    "s2_r",
    "s3_r",
    "s4_r",
    "s1_bio",
    "s2_dir",
    "s3_drivers",
    "s4_link",
    "driver",
    "n_drivers",
    "pred_threat_l0",
    "pred_regions",
    "pred_subregions",
    "pred_countries",
    "locales",
    "locale_coordinates",
    "realm",
    "pred_study_design",
    "pred_methods_data_collection",
    "pred_methods_analysis",
    "pred_has_comparison",
    "pred_comparison_types",
    "taxa_domain_labels",
    "taxa_kingdom_labels",
    "taxa_subkingdom_labels",
    "taxa_phylum_labels",
    "taxa_class_labels",
    "taxa_order_labels",
    "taxa_family_labels",
    "taxa_genus_labels",
    "taxa_species_labels",
    "taxa_summary_json",
)
EVIDENCE_COLUMNS = (*EVIDENCE_CORE_COLUMNS, "taxa_matches")
TAXONOMY_RANK_COLUMNS = EVIDENCE_CORE_COLUMNS[29:38]
TAXONOMY_SUMMARY_COLUMNS = (
    "taxa_record_status",
    "n_llm_taxa",
    "n_taxa_matched",
    "n_taxa_unresolved",
    "n_taxa_api_failed",
    "broad_groups_all",
    "broad_groups",
    "n_broad_groups",
    "taxa_broad_state",
    "analysis_groups_all",
    "analysis_groups",
    "n_analysis_groups",
    "taxa_analysis_state",
    "detail_groups_all",
    "detail_groups",
    "n_detail_groups",
    "taxa_detail_state",
    "taxa_broad_inclusion_state",
)
class EvidenceCorpusPrepError(ValueError):
    """Raised when a prepared screening/corpus artifact violates its grain."""


def _normalise_country_token(value: object) -> str:
    """Normalize a coded country label for World Bank lookup."""
    return re.sub(r"[^A-Za-z]", "", str(value)).upper()


def standardize_geography_lists(
    publications: pd.DataFrame,
    *,
    world_bank_mapping_path: str | Path,
) -> pd.DataFrame:
    """Standardize existing geography lists in place without changing corpus grain.

    Empty region, subregion, and country lists become ``("Not Applicable",)``.
    Any list containing an ``Unclear`` label becomes exactly ``("Unclear",)``.
    Country lists also become ``("Unclear",)`` when any non-special token cannot
    enter the World Bank economy lookup. Valid non-empty lists are preserved.

    Returns a small audit of changed cells; no corpus rows or columns are added,
    removed, or reordered.
    """
    missing = set(GEOGRAPHY_LIST_COLUMNS).difference(publications.columns)
    if missing:
        raise EvidenceCorpusPrepError(
            f"Integrated corpus lacks geography columns: {sorted(missing)}"
        )

    mapping_path = Path(world_bank_mapping_path)
    with mapping_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    mapping_records = payload.get("records")
    if not isinstance(mapping_records, list):
        raise EvidenceCorpusPrepError(
            f"World Bank mapping at {mapping_path} has no records list."
        )
    world_bank_codes = {
        _normalise_country_token(record.get("ipbes_iso3", ""))
        for record in mapping_records
        if record.get("has_world_bank_economy") is True
        and len(str(record.get("ipbes_iso3", ""))) == 3
    }
    if not world_bank_codes:
        raise EvidenceCorpusPrepError(
            f"World Bank mapping at {mapping_path} contains no eligible country codes."
        )

    original_columns = list(publications.columns)
    original_uts = publications["UT"].reset_index(drop=True).copy()
    audit_counts: Counter[tuple[str, str]] = Counter()

    for column in GEOGRAPHY_LIST_COLUMNS:
        standardized: list[tuple[str, ...]] = []
        for value in publications[column]:
            labels = tuple(parse_list_labels(value))
            reason: str | None = None
            if not labels:
                replacement = (_NOT_APPLICABLE_LABEL,)
                reason = "empty_to_not_applicable"
            elif any(label.casefold() == "unclear" for label in labels):
                replacement = (_UNCLEAR_LABEL,)
                reason = "contains_unclear_to_unclear"
            elif column == "pred_countries" and any(
                (token := _normalise_country_token(label))
                not in _SPECIAL_COUNTRY_TOKENS
                and token not in world_bank_codes
                for label in labels
            ):
                replacement = (_UNCLEAR_LABEL,)
                reason = "non_world_bank_country_to_unclear"
            else:
                replacement = labels

            standardized.append(replacement)
            if reason is not None and replacement != labels:
                audit_counts[(column, reason)] += 1
        publications[column] = standardized

    if len(publications) != len(original_uts):
        raise EvidenceCorpusPrepError("Geography standardization changed row count.")
    if list(publications.columns) != original_columns:
        raise EvidenceCorpusPrepError("Geography standardization changed columns.")
    if not publications["UT"].reset_index(drop=True).equals(original_uts):
        raise EvidenceCorpusPrepError("Geography standardization changed UT order.")

    return pd.DataFrame(
        [
            {"column": column, "rule": reason, "changed_values": count}
            for (column, reason), count in sorted(audit_counts.items())
        ],
        columns=["column", "rule", "changed_values"],
    )


@dataclass(frozen=True)
class ScreeningPreparedBundle:
    """Full compact screening grain, eligible metadata, aggregates, provenance."""

    screening: pd.DataFrame
    eligible: pd.DataFrame
    exclusion_overlap: pd.DataFrame
    manifest: dict[str, Any]


@dataclass(frozen=True)
class BiodiversityEvidenceBundle:
    """Integrated one-row-per-eligible-publication corpus and provenance."""

    publications: pd.DataFrame
    manifest: dict[str, Any]


@dataclass(frozen=True)
class BiodiversityEvidenceBuild:
    """Frames and streamed taxonomy artifact needed to write the corpus."""

    publications: pd.DataFrame
    abstracts: pd.DataFrame
    taxa_matches_path: Path
    manifest: dict[str, Any]


def _eligible_mask(series: pd.Series) -> pd.Series:
    if is_bool_dtype(series):
        return series.fillna(False)
    return series.astype("string").str.strip().str.lower().isin({"true", "1", "yes"})


def _validate_key(frame: pd.DataFrame, source: str) -> None:
    if "UT" not in frame:
        raise EvidenceCorpusPrepError(f"{source} has no UT column.")
    missing = int(frame["UT"].isna().sum())
    duplicated = int(frame["UT"].duplicated().sum())
    if missing or duplicated:
        raise EvidenceCorpusPrepError(
            f"{source} violates one row per UT: "
            f"missing={missing:,}, duplicated={duplicated:,}."
        )


def _json_default(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if pd.isna(value):
        return None
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=_json_default,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _direction_audit(screening: pd.DataFrame) -> list[dict[str, Any]]:
    eligible = screening.loc[screening["is_eligible"]]
    directions = (
        eligible["s2_dir"]
        .fillna("missing")
        .astype(str)
        .str.strip()
        .replace("", "missing")
    )
    counts = directions.value_counts(dropna=False)
    return [
        {
            "direction_of_change": direction,
            "records": int(count),
            "percent_of_eligible": count / len(eligible) * 100,
        }
        for direction, count in counts.items()
    ]


def _exclusion_overlap(screening: pd.DataFrame) -> pd.DataFrame:
    complete = screening.loc[
        ~screening["is_eligible"]
        & screening[list(REASON_COLUMNS)].notna().all(axis=1)
    ]
    zero_steps = complete[list(REASON_COLUMNS)].eq(0).rename(columns=STAGE_NAMES)
    zero_steps = zero_steps.loc[zero_steps.any(axis=1)]
    overlap = (
        zero_steps.value_counts()
        .rename("records")
        .reset_index()
        .sort_values("records", ascending=False)
        .reset_index(drop=True)
    )
    overlap.insert(0, "intersection", range(1, len(overlap) + 1))
    overlap["combination"] = overlap.apply(
        lambda row: " + ".join(
            stage for stage in STAGE_NAMES.values() if row[stage]
        ),
        axis=1,
    )
    overlap["percent"] = (overlap["records"] / len(zero_steps) * 100).round(2)
    return overlap


def build_screening_preparation(
    screening_path: str | Path,
    *,
    eligible_columns: Iterable[str],
    chunksize: int,
    repository_root: str | Path,
) -> ScreeningPreparedBundle:
    """Read the full screening CSV once and build both reusable grains."""
    screening_path = Path(screening_path)
    if chunksize <= 0:
        raise EvidenceCorpusPrepError("chunksize must be positive.")
    raw_columns = pd.read_csv(screening_path, nrows=0).columns.tolist()
    eligible_columns = tuple(dict.fromkeys([*eligible_columns, "is_eligible"]))
    required = set(SCREENING_ANALYSIS_COLUMNS).union(eligible_columns)
    missing = required.difference(raw_columns)
    if missing:
        raise EvidenceCorpusPrepError(
            f"Full screening source lacks required columns: {sorted(missing)}"
        )

    compact_chunks: list[pd.DataFrame] = []
    eligible_chunks: list[pd.DataFrame] = []
    try:
        reader = pd.read_csv(
            screening_path,
            usecols=list(required),
            chunksize=chunksize,
            low_memory=False,
        )
        for chunk in reader:
            mask = _eligible_mask(chunk["is_eligible"])
            compact = chunk[list(SCREENING_ANALYSIS_COLUMNS)].copy()
            compact["is_eligible"] = mask.to_numpy()
            compact_chunks.append(compact)
            eligible = chunk.loc[mask, list(eligible_columns)].copy()
            eligible["is_eligible"] = True
            eligible_chunks.append(eligible)
    except ValueError as exc:
        raise EvidenceCorpusPrepError(
            f"Could not read required screening columns: {exc}"
        ) from exc

    screening = pd.concat(compact_chunks, ignore_index=True)
    eligible = pd.concat(eligible_chunks, ignore_index=True)
    _validate_key(screening, "Prepared full screening evidence")
    _validate_key(eligible, "Prepared eligible screening evidence")
    if not eligible["UT"].reset_index(drop=True).equals(
        screening.loc[screening["is_eligible"], "UT"].reset_index(drop=True)
    ):
        raise EvidenceCorpusPrepError(
            "Eligible screening artifact does not preserve the full-screening key order."
        )

    overlap = _exclusion_overlap(screening)
    eligibility_counts = screening["eligibility"].value_counts(dropna=False)
    eligible_count = int(screening["is_eligible"].sum())
    if eligible_count != len(eligible):
        raise EvidenceCorpusPrepError("Eligible screening counts do not reconcile.")
    unclear = screening[list(REASON_COLUMNS)].eq(-1).any(axis=1)
    negative = screening["s2_dir"].eq("negative")
    summary = {
        "screened_records": len(screening),
        "raw_column_count": len(raw_columns),
        "raw_columns": raw_columns,
        "eligible_records": eligible_count,
        "not_eligible_records": int((~screening["is_eligible"]).sum()),
        "eligibility_label_eligible": int(eligibility_counts.get("ELIGIBLE", 0)),
        "eligibility_label_not_eligible": int(
            eligibility_counts.get("NOT_ELIGIBLE", 0)
        ),
        "eligible_with_unclear_step": int(
            (screening["is_eligible"] & unclear).sum()
        ),
        "eligible_negative": int((screening["is_eligible"] & negative).sum()),
        "eligible_not_negative": int(
            (screening["is_eligible"] & ~negative).sum()
        ),
        "complete_ineligible_with_zero_reason": int(overlap["records"].sum()),
    }
    manifest = {
        "schema_version": SCREENING_SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": source_signature(
            screening_path, repository_root=repository_root
        ),
        "artifacts": {
            "screening_publications": "screening_publications.parquet",
            "eligible_screening_publications": "eligible_screening_publications.parquet",
            "screening_exclusion_overlap": "screening_exclusion_overlap.csv",
        },
        "rows": {
            "screening_publications": len(screening),
            "eligible_screening_publications": len(eligible),
            "screening_exclusion_overlap": len(overlap),
        },
        "summary": summary,
        "eligible_direction_audit": _direction_audit(screening),
        "screening_analysis_columns": list(SCREENING_ANALYSIS_COLUMNS),
        "eligible_columns": list(eligible.columns),
    }
    return ScreeningPreparedBundle(screening, eligible, overlap, manifest)


class ScreeningPreparedStore:
    """Write/load the compact full-screening and eligible-screening artifacts."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.screening_path = self.root / "screening_publications.parquet"
        self.eligible_path = self.root / "eligible_screening_publications.parquet"
        self.overlap_path = self.root / "screening_exclusion_overlap.csv"
        self.manifest_path = self.root / "manifest.json"

    def write(self, bundle: ScreeningPreparedBundle) -> list[Path]:
        self.root.mkdir(parents=True, exist_ok=True)
        bundle.screening.to_parquet(
            self.screening_path, index=False, compression="zstd"
        )
        bundle.eligible.to_parquet(
            self.eligible_path, index=False, compression="zstd"
        )
        bundle.exclusion_overlap.to_csv(self.overlap_path, index=False)
        _write_json(self.manifest_path, bundle.manifest)
        return [
            self.screening_path,
            self.eligible_path,
            self.overlap_path,
            self.manifest_path,
        ]

    def _load_manifest(self, *, require_eligible: bool = True) -> dict[str, Any]:
        required_paths = [
            self.screening_path,
            self.overlap_path,
            self.manifest_path,
        ]
        if require_eligible:
            required_paths.append(self.eligible_path)
        missing = [
            path
            for path in required_paths
            if not path.exists()
        ]
        if missing:
            raise EvidenceCorpusPrepError(
                "Prepared screening bundle is missing. Run the screening "
                f"preparation notebook. Missing: {[str(path) for path in missing]}"
            )
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema_version") != SCREENING_SCHEMA_VERSION:
            raise EvidenceCorpusPrepError(
                "Prepared screening schema is incompatible; rebuild it."
            )
        return manifest

    def load_analysis(self) -> tuple[dict[str, Any], pd.DataFrame]:
        """Load only the tiny aggregates required by screening results."""
        manifest = self._load_manifest(require_eligible=False)
        overlap = pd.read_csv(self.overlap_path)
        if len(overlap) != manifest["rows"]["screening_exclusion_overlap"]:
            raise EvidenceCorpusPrepError(
                "Prepared screening-overlap row count does not match manifest."
            )
        return manifest, overlap

    def remove_eligible_build_cache(self) -> bool:
        """Remove the consumed eligible-screening cache after corpus verification."""
        manifest = self._load_manifest(require_eligible=False)
        if not self.eligible_path.exists():
            return False
        self.eligible_path.unlink()
        manifest["artifacts"].pop("eligible_screening_publications", None)
        manifest["consumed_build_cache"] = {
            "filename": self.eligible_path.name,
            "removed_at_utc": datetime.now(timezone.utc).isoformat(),
            "recoverability": (
                "rerun notebooks/data_processing/03_screening_analysis_prep.ipynb"
            ),
        }
        _write_json(self.manifest_path, manifest)
        return True

    def load_eligible(self) -> tuple[pd.DataFrame, dict[str, Any]]:
        manifest = self._load_manifest()
        eligible = pd.read_parquet(self.eligible_path)
        _validate_key(eligible, "Prepared eligible screening publications")
        if len(eligible) != manifest["rows"]["eligible_screening_publications"]:
            raise EvidenceCorpusPrepError(
                "Prepared eligible screening row count does not match manifest."
            )
        return eligible, manifest

    def load(self) -> ScreeningPreparedBundle:
        manifest = self._load_manifest()
        screening = pd.read_parquet(self.screening_path)
        eligible = pd.read_parquet(self.eligible_path)
        overlap = pd.read_csv(self.overlap_path)
        _validate_key(screening, "Prepared screening publications")
        _validate_key(eligible, "Prepared eligible screening publications")
        if len(screening) != manifest["rows"]["screening_publications"]:
            raise EvidenceCorpusPrepError(
                "Prepared screening row count does not match manifest."
            )
        return ScreeningPreparedBundle(screening, eligible, overlap, manifest)


def _taxa_summary_json(taxa_articles: pd.DataFrame) -> pd.Series:
    """Pack publication-level taxonomy audits into deterministic JSON values."""
    match_columns = sorted(
        column
        for column in taxa_articles
        if column.startswith("match_status_count__")
    )
    required = set(TAXONOMY_SUMMARY_COLUMNS).union(match_columns)
    missing = required.difference(taxa_articles.columns)
    if missing:
        raise EvidenceCorpusPrepError(
            f"Prepared taxa artifact lacks summary columns: {sorted(missing)}"
        )

    def integer(value: Any) -> int:
        return 0 if pd.isna(value) else int(value)

    summaries: list[str] = []
    columns = [*TAXONOMY_SUMMARY_COLUMNS, *match_columns]
    for values in taxa_articles[list(columns)].itertuples(index=False, name=None):
        record = dict(zip(columns, values))
        payload = {
            "broad_inclusion_state": record["taxa_broad_inclusion_state"],
            "counts": {
                "api_failed": integer(record["n_taxa_api_failed"]),
                "llm_taxa": integer(record["n_llm_taxa"]),
                "matched": integer(record["n_taxa_matched"]),
                "unresolved": integer(record["n_taxa_unresolved"]),
            },
            "groups": {
                name: {
                    "all": list(record[f"{name}_groups_all"]),
                    "count": integer(record[f"n_{name}_groups"]),
                    "included": list(record[f"{name}_groups"]),
                    "state": record[f"taxa_{name}_state"],
                }
                for name in ("broad", "analysis", "detail")
            },
            "match_status_counts": {
                column.removeprefix("match_status_count__"): integer(record[column])
                for column in match_columns
            },
            "record_status": record["taxa_record_status"],
        }
        summaries.append(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        )
    return pd.Series(summaries, index=taxa_articles.index, dtype="string")


def build_biodiversity_evidence_corpus(
    merged_corpus: pd.DataFrame,
    taxa_articles: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the 39 scalar/list columns and separate abstract sidecar."""
    _validate_key(merged_corpus, "Merged eligible corpus")
    _validate_key(taxa_articles, "Prepared taxa publications")
    left_keys = pd.Index(merged_corpus["UT"])
    right_keys = pd.Index(taxa_articles["UT"])
    if len(left_keys.difference(right_keys)) or len(right_keys.difference(left_keys)):
        raise EvidenceCorpusPrepError(
            "Merged corpus and prepared taxa artifacts have different UT sets."
        )

    required_metadata = set(EVIDENCE_CORE_COLUMNS[:29]).difference({"n_drivers"})
    missing_metadata = required_metadata.difference(merged_corpus.columns)
    if missing_metadata:
        raise EvidenceCorpusPrepError(
            f"Merged corpus lacks required evidence columns: {sorted(missing_metadata)}"
        )
    if "abstract" not in merged_corpus or "wos_categories" not in merged_corpus:
        raise EvidenceCorpusPrepError(
            "Merged corpus must contain abstract and wos_categories so their "
            "intentional sidecar/drop treatment can be verified."
        )
    missing_taxa = set(TAXONOMY_RANK_COLUMNS).union(
        TAXONOMY_SUMMARY_COLUMNS, {"n_drivers"}
    ).difference(taxa_articles.columns)
    if missing_taxa:
        raise EvidenceCorpusPrepError(
            f"Prepared taxa artifact lacks required fields: {sorted(missing_taxa)}"
        )

    abstracts = merged_corpus[["UT", "abstract"]].copy()
    _validate_key(abstracts, "Biodiversity evidence abstracts")
    publications = merged_corpus.drop(
        columns=["abstract", "wos_categories"]
    ).copy()
    present_list_columns = [
        column for column in EVIDENCE_LIST_COLUMNS if column in publications
    ]
    for column in present_list_columns:
        publications[column] = publications[column].map(
            lambda value: tuple(parse_list_labels(value))
        )

    cross_checks = {
        "driver": "drivers",
        "pred_threat_l0": "threat_l0",
        "realm": "realms",
    }
    aligned_taxa = taxa_articles.set_index("UT").loc[publications["UT"]]
    for corpus_column, taxa_column in cross_checks.items():
        corpus_values = publications[corpus_column]
        if corpus_column == "driver":
            # The integrated corpus preserves the raw screening/coding state,
            # while taxa preparation deliberately excludes non-substantive
            # driver values before analysis.
            excluded = {"not applicable", "non applicable", "unclear"}
            corpus_values = corpus_values.map(
                lambda labels: tuple(
                    label for label in labels if label.casefold() not in excluded
                )
            )
        taxa_values = aligned_taxa[taxa_column]
        if corpus_column in {"driver", "pred_threat_l0"}:
            agrees = corpus_values.map(frozenset).reset_index(drop=True).equals(
                taxa_values.map(frozenset).reset_index(drop=True)
            )
        else:
            agrees = corpus_values.reset_index(drop=True).equals(
                taxa_values.reset_index(drop=True)
            )
        if not agrees:
            raise EvidenceCorpusPrepError(
                f"Prepared taxa and merged corpus disagree on {corpus_column}."
            )

    before = publications["UT"].reset_index(drop=True)
    aligned_taxa = aligned_taxa.reset_index(drop=True)
    publications["n_drivers"] = aligned_taxa["n_drivers"].to_numpy()
    for column in TAXONOMY_RANK_COLUMNS:
        publications[column] = aligned_taxa[column].map(
            lambda value: tuple(value) if value is not None else ()
        )
    publications["taxa_summary_json"] = _taxa_summary_json(aligned_taxa).to_numpy()
    missing_final = set(EVIDENCE_CORE_COLUMNS).difference(publications.columns)
    if missing_final:
        raise EvidenceCorpusPrepError(
            f"Integrated corpus lacks final columns: {sorted(missing_final)}"
        )
    publications = publications[list(EVIDENCE_CORE_COLUMNS)].copy()
    if len(publications) != len(merged_corpus) or not publications["UT"].reset_index(
        drop=True
    ).equals(before):
        raise EvidenceCorpusPrepError("Attaching taxa changed the UT grain or order.")
    _validate_key(publications, "Integrated biodiversity evidence corpus")
    if not abstracts["UT"].reset_index(drop=True).equals(before):
        raise EvidenceCorpusPrepError("Abstract sidecar changed the UT grain or order.")
    return publications, abstracts


def build_biodiversity_manifest(
    publications: pd.DataFrame,
    abstracts: pd.DataFrame,
    *,
    sources: Mapping[str, str | Path],
    screening_manifest: Mapping[str, Any],
    taxa_manifest: Mapping[str, Any],
    repository_root: str | Path,
) -> dict[str, Any]:
    """Record the complete integrated-corpus contract and its upstream lineage."""
    _validate_key(publications, "Integrated biodiversity evidence corpus")
    _validate_key(abstracts, "Biodiversity evidence abstracts")
    if list(publications.columns) != list(EVIDENCE_CORE_COLUMNS):
        raise EvidenceCorpusPrepError(
            "Integrated corpus core columns do not match the schema contract."
        )
    if list(abstracts.columns) != ["UT", "abstract"]:
        raise EvidenceCorpusPrepError(
            "Abstract sidecar must contain exactly UT and abstract."
        )
    if not abstracts["UT"].reset_index(drop=True).equals(
        publications["UT"].reset_index(drop=True)
    ):
        raise EvidenceCorpusPrepError(
            "Abstract sidecar does not preserve publication UT order."
        )
    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "grain": "one row per eligible screening publication (UT)",
        "scope": (
            "all screening-eligible publications; direction, year, threat, realm, "
            "geography, study, and taxa filters are not applied"
        ),
        "artifacts": {
            "biodiversity_evidence_corpus": "biodiversity_evidence_corpus.parquet",
            "biodiversity_evidence_abstracts": "biodiversity_evidence_abstracts.parquet",
        },
        "rows": {
            "publications": len(publications),
            "unique_UT": publications["UT"].nunique(),
            "abstracts": len(abstracts),
        },
        "columns": list(EVIDENCE_COLUMNS),
        "abstract_columns": ["UT", "abstract"],
        "list_columns": [
            column for column in EVIDENCE_LIST_COLUMNS if column in publications
        ],
        "nested_columns": {"taxa_matches": "list<struct>"},
        "sources": {
            name: source_signature(path, repository_root=repository_root)
            for name, path in sources.items()
        },
        "upstream": {
            "screening_schema_version": screening_manifest["schema_version"],
            "screening_eligible_rows": screening_manifest["rows"][
                "eligible_screening_publications"
            ],
            "taxa_schema_version": taxa_manifest["schema_version"],
            "taxa_grouping_rules_sha256": taxa_manifest[
                "grouping_rules_sha256"
            ],
            "taxa_match_rows": taxa_manifest["rows"]["taxa_matches"],
            "taxon_items": taxa_manifest["rows"]["taxon_items"],
        },
        "direction_counts": {
            str(key): int(value)
            for key, value in publications["s2_dir"].value_counts(
                dropna=False
            ).items()
        },
    }


class BiodiversityEvidenceStore:
    """Write and validate the integrated corpus and abstract sidecar."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.publication_path = self.root / "biodiversity_evidence_corpus.parquet"
        self.abstract_path = self.root / "biodiversity_evidence_abstracts.parquet"
        self.manifest_path = self.root / "manifest.json"

    def write(self, bundle: BiodiversityEvidenceBuild) -> list[Path]:
        """Stream nested taxa matches beside core columns without changing UT grain."""
        self.root.mkdir(parents=True, exist_ok=True)
        if list(bundle.publications.columns) != list(EVIDENCE_CORE_COLUMNS):
            raise EvidenceCorpusPrepError(
                "Cannot write biodiversity evidence with incompatible core columns."
            )
        match_file = pq.ParquetFile(bundle.taxa_matches_path)
        if match_file.schema_arrow.names != ["UT", "taxa_matches"]:
            raise EvidenceCorpusPrepError(
                "Taxa-match artifact must contain exactly UT and taxa_matches."
            )
        if match_file.metadata.num_rows != len(bundle.publications):
            raise EvidenceCorpusPrepError(
                "Taxa matches and evidence publications have different row counts."
            )

        temporary = tempfile.NamedTemporaryFile(
            prefix=f".{self.publication_path.stem}.",
            suffix=".parquet",
            dir=self.root,
            delete=False,
        )
        temporary_path = Path(temporary.name)
        temporary.close()
        writer: pq.ParquetWriter | None = None
        offset = 0
        try:
            for batch in match_file.iter_batches(batch_size=8_192):
                count = batch.num_rows
                core = bundle.publications.iloc[offset : offset + count]
                expected_uts = core["UT"].astype(str).tolist()
                observed_uts = batch.column(
                    batch.schema.get_field_index("UT")
                ).to_pylist()
                if observed_uts != expected_uts:
                    raise EvidenceCorpusPrepError(
                        "Taxa matches do not preserve evidence publication UT order."
                    )
                table = pa.Table.from_pandas(core, preserve_index=False)
                table = table.append_column(
                    "taxa_matches",
                    batch.column(batch.schema.get_field_index("taxa_matches")),
                )
                if table.schema.names != list(EVIDENCE_COLUMNS):
                    raise EvidenceCorpusPrepError(
                        "Streamed evidence columns do not match the schema contract."
                    )
                if writer is None:
                    writer = pq.ParquetWriter(
                        temporary_path,
                        table.schema,
                        compression="zstd",
                    )
                elif not table.schema.equals(writer.schema, check_metadata=False):
                    raise EvidenceCorpusPrepError(
                        "Evidence Arrow schema changed between streamed batches."
                    )
                writer.write_table(table)
                offset += count
            if writer is None or offset != len(bundle.publications):
                raise EvidenceCorpusPrepError(
                    "Taxa-match streaming did not cover every publication."
                )
            writer.close()
            writer = None
            os.replace(temporary_path, self.publication_path)
        except Exception:
            if writer is not None:
                writer.close()
            temporary_path.unlink(missing_ok=True)
            raise

        bundle.abstracts.to_parquet(
            self.abstract_path, index=False, compression="zstd"
        )
        _write_json(self.manifest_path, bundle.manifest)
        return [self.publication_path, self.abstract_path, self.manifest_path]

    def _load_manifest(self) -> dict[str, Any]:
        missing = [
            path
            for path in (
                self.publication_path,
                self.abstract_path,
                self.manifest_path,
            )
            if not path.exists()
        ]
        if missing:
            raise EvidenceCorpusPrepError(
                "Prepared biodiversity-evidence corpus is missing. Run its "
                f"data-processing notebook. Missing: {[str(path) for path in missing]}"
            )
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
            raise EvidenceCorpusPrepError(
                "Prepared biodiversity-evidence schema is incompatible; rebuild it."
            )
        return manifest

    def load(
        self,
        *,
        columns: Iterable[str] | None = None,
    ) -> BiodiversityEvidenceBundle:
        """Load all fields or an explicit projection from the main corpus."""
        manifest = self._load_manifest()
        expected_columns = manifest["columns"]
        selected = list(columns) if columns is not None else expected_columns
        if len(selected) != len(set(selected)):
            raise EvidenceCorpusPrepError("Requested evidence columns are duplicated.")
        unknown = set(selected).difference(expected_columns)
        if unknown:
            raise EvidenceCorpusPrepError(
                f"Requested evidence columns are unavailable: {sorted(unknown)}"
            )
        publications = pd.read_parquet(self.publication_path, columns=selected)
        for column in set(manifest.get("list_columns", ())).intersection(selected):
            publications[column] = publications[column].map(
                lambda value: tuple(value) if value is not None else ()
            )
        if "UT" in publications:
            _validate_key(publications, "Prepared biodiversity evidence corpus")
        if len(publications) != manifest["rows"]["publications"]:
            raise EvidenceCorpusPrepError(
                "Prepared biodiversity-evidence row count does not match manifest."
            )
        if list(publications.columns) != selected:
            raise EvidenceCorpusPrepError(
                "Prepared biodiversity-evidence columns do not match manifest."
            )
        return BiodiversityEvidenceBundle(publications, manifest)

    def load_abstracts(self) -> pd.DataFrame:
        """Load publication text only for analyses that explicitly require it."""
        manifest = self._load_manifest()
        abstracts = pd.read_parquet(self.abstract_path)
        if list(abstracts.columns) != manifest["abstract_columns"]:
            raise EvidenceCorpusPrepError(
                "Prepared abstract columns do not match the manifest."
            )
        _validate_key(abstracts, "Prepared biodiversity evidence abstracts")
        if len(abstracts) != manifest["rows"]["abstracts"]:
            raise EvidenceCorpusPrepError(
                "Prepared abstract row count does not match the manifest."
            )
        return abstracts


__all__ = [
    "BiodiversityEvidenceBundle",
    "BiodiversityEvidenceBuild",
    "BiodiversityEvidenceStore",
    "EVIDENCE_COLUMNS",
    "EVIDENCE_CORE_COLUMNS",
    "EVIDENCE_LIST_COLUMNS",
    "GEOGRAPHY_LIST_COLUMNS",
    "EvidenceCorpusPrepError",
    "REASON_COLUMNS",
    "SCREENING_ANALYSIS_COLUMNS",
    "STAGE_NAMES",
    "ScreeningPreparedBundle",
    "ScreeningPreparedStore",
    "build_biodiversity_evidence_corpus",
    "build_biodiversity_manifest",
    "build_screening_preparation",
    "standardize_geography_lists",
]
