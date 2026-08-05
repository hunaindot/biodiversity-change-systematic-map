"""Prepare reusable screening and eligible biodiversity-evidence handoffs.

The full screening grain and the eligible evidence grain are deliberately
separate. Screening results use compact aggregates over every screened record;
substantive results use a single one-row-per-UT corpus containing screening
metadata and all configured coding dimensions.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype

from data_helpers.labels import parse_list_labels


SCREENING_SCHEMA_VERSION = 1
EVIDENCE_SCHEMA_VERSION = 2
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
    "class_labels",
    "pred_methods_data_collection",
    "pred_methods_analysis",
    "pred_comparison_types",
    "broad_groups_all",
    "broad_groups",
    "analysis_groups_all",
    "analysis_groups",
    "detail_groups_all",
    "detail_groups",
)
TAXA_DUPLICATE_COLUMNS = {
    "publication_year",
    "s2_dir",
    "pred_study_design",
    "drivers",
    "threat_l0",
    "realms",
}


class EvidenceCorpusPrepError(ValueError):
    """Raised when a prepared screening/corpus artifact violates its grain."""


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


def _source_signature(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    stat = source.stat()
    return {
        "path": str(source),
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


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
        "source": _source_signature(screening_path),
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


def build_biodiversity_evidence_corpus(
    merged_corpus: pd.DataFrame,
    taxa_articles: pd.DataFrame,
) -> pd.DataFrame:
    """Attach current taxa fields and normalize list labels without exploding UT."""
    _validate_key(merged_corpus, "Merged eligible corpus")
    _validate_key(taxa_articles, "Prepared taxa publications")
    left_keys = pd.Index(merged_corpus["UT"])
    right_keys = pd.Index(taxa_articles["UT"])
    if len(left_keys.difference(right_keys)) or len(right_keys.difference(left_keys)):
        raise EvidenceCorpusPrepError(
            "Merged corpus and prepared taxa artifacts have different UT sets."
        )

    publications = merged_corpus.copy()
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

    taxa_columns = [
        column
        for column in taxa_articles.columns
        if column != "UT"
        and column not in TAXA_DUPLICATE_COLUMNS
        and column not in publications.columns
    ]
    before = publications["UT"].reset_index(drop=True)
    publications = publications.merge(
        taxa_articles[["UT", *taxa_columns]],
        on="UT",
        how="left",
        sort=False,
        validate="one_to_one",
    )
    if len(publications) != len(merged_corpus) or not publications[
        "UT"
    ].reset_index(drop=True).equals(before):
        raise EvidenceCorpusPrepError("Attaching taxa changed the UT grain or order.")
    _validate_key(publications, "Integrated biodiversity evidence corpus")
    return publications


def build_biodiversity_manifest(
    publications: pd.DataFrame,
    *,
    sources: Mapping[str, str | Path],
    screening_manifest: Mapping[str, Any],
    taxa_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Record the complete integrated-corpus contract and its upstream lineage."""
    _validate_key(publications, "Integrated biodiversity evidence corpus")
    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "grain": "one row per eligible screening publication (UT)",
        "scope": (
            "all screening-eligible publications; direction, year, threat, realm, "
            "geography, study, and taxa filters are not applied"
        ),
        "artifact": "biodiversity_evidence_corpus.parquet",
        "rows": {
            "publications": len(publications),
            "unique_UT": publications["UT"].nunique(),
        },
        "columns": list(publications.columns),
        "list_columns": [
            column for column in EVIDENCE_LIST_COLUMNS if column in publications
        ],
        "sources": {name: _source_signature(path) for name, path in sources.items()},
        "upstream": {
            "screening_schema_version": screening_manifest["schema_version"],
            "screening_eligible_rows": screening_manifest["rows"][
                "eligible_screening_publications"
            ],
            "taxa_schema_version": taxa_manifest["schema_version"],
            "taxa_grouping_rules_sha256": taxa_manifest[
                "grouping_rules_sha256"
            ],
        },
        "direction_counts": {
            str(key): int(value)
            for key, value in publications["s2_dir"].value_counts(
                dropna=False
            ).items()
        },
    }


class BiodiversityEvidenceStore:
    """Write and validate the single integrated eligible-publication file."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.publication_path = self.root / "biodiversity_evidence_corpus.parquet"
        self.manifest_path = self.root / "manifest.json"

    def write(self, bundle: BiodiversityEvidenceBundle) -> list[Path]:
        self.root.mkdir(parents=True, exist_ok=True)
        bundle.publications.to_parquet(
            self.publication_path, index=False, compression="zstd"
        )
        _write_json(self.manifest_path, bundle.manifest)
        return [self.publication_path, self.manifest_path]

    def load(self) -> BiodiversityEvidenceBundle:
        missing = [
            path
            for path in (self.publication_path, self.manifest_path)
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
        publications = pd.read_parquet(self.publication_path)
        for column in manifest.get("list_columns", []):
            publications[column] = publications[column].map(
                lambda value: tuple(value) if value is not None else ()
            )
        _validate_key(publications, "Prepared biodiversity evidence corpus")
        if len(publications) != manifest["rows"]["publications"]:
            raise EvidenceCorpusPrepError(
                "Prepared biodiversity-evidence row count does not match manifest."
            )
        if list(publications.columns) != manifest["columns"]:
            raise EvidenceCorpusPrepError(
                "Prepared biodiversity-evidence columns do not match manifest."
            )
        return BiodiversityEvidenceBundle(publications, manifest)


__all__ = [
    "BiodiversityEvidenceBundle",
    "BiodiversityEvidenceStore",
    "EVIDENCE_LIST_COLUMNS",
    "EvidenceCorpusPrepError",
    "REASON_COLUMNS",
    "SCREENING_ANALYSIS_COLUMNS",
    "STAGE_NAMES",
    "ScreeningPreparedBundle",
    "ScreeningPreparedStore",
    "build_biodiversity_evidence_corpus",
    "build_biodiversity_manifest",
    "build_screening_preparation",
]
