"""Build and validate the canonical analysis-ready taxa handoff.

Raw source linkage, serialized-label parsing, taxonomic grouping states, match
audits, and the GBIF broad benchmark are performed once in the data-processing
layer. Results notebooks consume the compact bundle and perform only their
analysis-specific filtering, estimation, inference, and plotting.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from data_helpers.labels import parse_list_labels
from data_helpers.analysis.taxa.benchmark import DescribedDiversity


SCHEMA_VERSION = 2
INCLUSION_ORDER = (
    "Included: at least one benchmarkable broad group",
    "Excluded: Not applicable only",
    "Excluded: Unclear only",
    "Excluded: mixed Not applicable and Unclear",
    "Excluded: accepted taxon but broad hierarchy unresolved",
    "Excluded: reported taxon but no accepted benchmarkable match",
    "Excluded: no taxon item returned",
)
NOT_APPLICABLE_VALUES = {"not applicable", "non applicable"}
UNCLEAR_VALUES = {"unclear"}
SPECIAL_EXCLUSION_VALUES = NOT_APPLICABLE_VALUES | UNCLEAR_VALUES
LIST_COLUMNS = (
    "drivers",
    "threat_l0",
    "realms",
    "class_labels",
    "broad_groups_all",
    "broad_groups",
    "analysis_groups_all",
    "analysis_groups",
    "detail_groups_all",
    "detail_groups",
)
TAXA_SOURCE_COLUMNS = (
    "UT",
    "class",
    "broad_taxa_groups",
    "taxa_analysis_groups",
    "taxa_detail_groups",
    "llm_taxa_json",
    "taxa_match_status_json",
    "taxa_record_status",
    "n_llm_taxa",
    "n_taxa_matched",
    "n_taxa_unresolved",
    "n_taxa_api_failed",
)
CORPUS_COLUMNS = (
    "UT",
    "publication_year",
    "s2_dir",
    "driver",
    "pred_threat_l0",
    "realm",
    "pred_study_design",
)


class TaxaAnalysisPrepError(ValueError):
    """Raised when the prepared taxa handoff violates its contract."""


@dataclass(frozen=True)
class TaxaPreparedBundle:
    """Loaded analysis-ready publications, GBIF benchmark, and provenance."""

    articles: pd.DataFrame
    benchmark: DescribedDiversity
    manifest: dict[str, Any]

    def audit_frame(self, name: str) -> pd.DataFrame:
        rows = self.manifest.get("audits", {}).get(name)
        if rows is None:
            raise TaxaAnalysisPrepError(f"Prepared manifest has no audit: {name}")
        return pd.DataFrame(rows)


def load_taxa_mapping(path: str | Path) -> dict[str, Any]:
    """Load the current three-scheme taxa grouping configuration."""
    try:
        mapping = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TaxaAnalysisPrepError(f"Could not load taxa mapping: {exc}") from exc
    if mapping.get("schema_version") != 3:
        raise TaxaAnalysisPrepError("Taxa mapping must use schema_version 3.")
    schemes = mapping.get("schemes", {})
    for name in ("broad", "analysis", "detail"):
        scheme = schemes.get(name, {})
        order = scheme.get("group_order", [])
        if not order or len(order) != len(set(order)):
            raise TaxaAnalysisPrepError(
                f"Taxa {name} group order must be non-empty and unique."
            )
        if scheme.get("unresolved_group") not in order:
            raise TaxaAnalysisPrepError(
                f"Taxa {name} group order must contain its unresolved state."
            )
    return mapping


def grouping_rules_fingerprint(mapping: Mapping[str, Any]) -> str:
    """Hash grouping semantics while allowing figure colors to change freely."""
    semantics = {
        "schema_version": mapping.get("schema_version"),
        "eligible_match_statuses": mapping.get("eligible_match_statuses"),
        "not_applicable_values": mapping.get("not_applicable_values"),
        "schemes": {
            name: {
                "output_column": scheme.get("output_column"),
                "group_order": scheme.get("group_order"),
                "unresolved_group": scheme.get("unresolved_group"),
                "rules": scheme.get("rules"),
            }
            for name, scheme in mapping.get("schemes", {}).items()
        },
    }
    canonical = json.dumps(semantics, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_ut(frame: pd.DataFrame, source: str) -> None:
    if "UT" not in frame:
        raise TaxaAnalysisPrepError(f"{source} has no UT column.")
    missing = int(frame["UT"].isna().sum())
    duplicated = int(frame["UT"].duplicated().sum())
    if missing or duplicated:
        raise TaxaAnalysisPrepError(
            f"{source} violates one-row-per-UT grain: "
            f"missing={missing:,}, duplicated={duplicated:,}."
        )


def _parse_json_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, str) or not value.strip():
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def _ordered_labels(value: Any, order: Iterable[str], source: str) -> tuple[str, ...]:
    order = tuple(order)
    labels = parse_list_labels(value)
    unknown = set(labels).difference(order)
    if unknown:
        raise TaxaAnalysisPrepError(
            f"{source} contains unconfigured labels: {sorted(unknown)}"
        )
    observed = set(labels)
    return tuple(label for label in order if label in observed)


def _configured_labels(
    value: Any,
    order: Iterable[str],
    *,
    excluded: Iterable[str],
    source: str,
) -> tuple[str, ...]:
    order = tuple(order)
    excluded_casefold = {label.casefold() for label in excluded}
    labels = [
        label
        for label in parse_list_labels(value)
        if label.casefold() not in excluded_casefold
    ]
    unknown = set(labels).difference(order)
    if unknown:
        raise TaxaAnalysisPrepError(
            f"{source} contains unconfigured labels: {sorted(unknown)}"
        )
    observed = set(labels)
    return tuple(label for label in order if label in observed)


def _broad_inclusion_state(
    broad_groups: tuple[str, ...],
    llm_items: list[dict[str, Any]],
    biological_groups: set[str],
    unresolved_group: str,
) -> str:
    if biological_groups.intersection(broad_groups):
        return INCLUSION_ORDER[0]
    if unresolved_group in broad_groups:
        return INCLUSION_ORDER[4]
    names = {
        str(item.get("canonical_name", "")).strip().casefold()
        for item in llm_items
        if str(item.get("canonical_name", "")).strip()
    }
    if not llm_items:
        return INCLUSION_ORDER[6]
    if names and names.issubset(NOT_APPLICABLE_VALUES):
        return INCLUSION_ORDER[1]
    if names and names.issubset(UNCLEAR_VALUES):
        return INCLUSION_ORDER[2]
    if names and names.issubset(SPECIAL_EXCLUSION_VALUES):
        return INCLUSION_ORDER[3]
    return INCLUSION_ORDER[5]


def _scheme_state(
    all_groups: tuple[str, ...],
    biological_groups: tuple[str, ...],
    unresolved_group: str,
) -> str:
    if biological_groups:
        return "resolved"
    if unresolved_group in all_groups:
        return "unresolved_only"
    return "no_group"


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_") or "missing"


def _source_signature(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    stat = source.stat()
    return {
        "path": str(source),
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _auxiliary_inventory(articles: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source, column in (
        ("driver", "drivers"),
        ("threats_l0", "threat_l0"),
        ("realm", "realms"),
    ):
        counter: Counter[str] = Counter()
        for labels in articles[column]:
            counter.update(labels)
        rows.extend(
            {
                "source": source,
                "column": column,
                "label": label,
                "n_publications": count,
                "special_for_later_crosscuts": label.casefold()
                in SPECIAL_EXCLUSION_VALUES,
            }
            for label, count in counter.most_common()
        )
    return rows


def build_taxa_publications(
    corpus_df: pd.DataFrame,
    *,
    taxa_path: str | Path,
    mapping: Mapping[str, Any],
    driver_order: Iterable[str],
    threat_order: Iterable[str],
) -> tuple[pd.DataFrame, dict[str, list[dict[str, Any]]]]:
    """Build the complete one-row-per-UT analysis-ready taxa table."""
    missing = set(CORPUS_COLUMNS).difference(corpus_df.columns)
    if missing:
        raise TaxaAnalysisPrepError(
            f"Merged corpus is missing required columns: {sorted(missing)}"
        )
    _validate_ut(corpus_df, "Eligible merged corpus")
    taxa_path = Path(taxa_path)
    try:
        taxa = pd.read_csv(
            taxa_path, usecols=list(TAXA_SOURCE_COLUMNS), low_memory=False
        )
    except ValueError as exc:
        raise TaxaAnalysisPrepError(
            "Taxa source lacks current broad/analysis/detail enrichment fields."
        ) from exc
    _validate_ut(taxa, "Taxa-with-API source")
    corpus_keys = pd.Index(corpus_df["UT"])
    taxa_keys = pd.Index(taxa["UT"])
    corpus_only = corpus_keys.difference(taxa_keys, sort=False)
    taxa_only = taxa_keys.difference(corpus_keys, sort=False)
    if len(corpus_only) or len(taxa_only):
        raise TaxaAnalysisPrepError(
            "Taxa and corpus UT sets differ: "
            f"corpus_only={len(corpus_only):,}, taxa_only={len(taxa_only):,}."
        )

    original_keys = corpus_df["UT"].reset_index(drop=True)
    joined = corpus_df[list(CORPUS_COLUMNS)].merge(
        taxa, on="UT", how="left", sort=False, validate="one_to_one"
    )
    if len(joined) != len(corpus_df) or not joined["UT"].reset_index(
        drop=True
    ).equals(original_keys):
        raise TaxaAnalysisPrepError("Joining taxa changed the UT grain or order.")

    schemes = mapping["schemes"]
    excluded = set(mapping.get("not_applicable_values", ())) | {
        "Not Applicable",
        "Unclear",
    }
    driver_order = tuple(driver_order)
    threat_order = tuple(threat_order)
    articles = joined[
        [
            "UT",
            "publication_year",
            "s2_dir",
            "pred_study_design",
            "taxa_record_status",
            "n_llm_taxa",
            "n_taxa_matched",
            "n_taxa_unresolved",
            "n_taxa_api_failed",
        ]
    ].copy()
    articles["publication_year"] = pd.to_numeric(
        articles["publication_year"], errors="coerce"
    ).astype("Int64")
    articles["drivers"] = joined["driver"].map(
        lambda value: _configured_labels(
            value,
            driver_order,
            excluded=excluded,
            source="Driver labels",
        )
    )
    articles["threat_l0"] = joined["pred_threat_l0"].map(
        lambda value: _configured_labels(
            value,
            threat_order,
            excluded=(),
            source="Threat-L0 labels",
        )
    )
    articles["realms"] = joined["realm"].map(
        lambda value: tuple(parse_list_labels(value))
    )
    class_exclusions = {
        str(label).strip().casefold()
        for label in mapping.get("not_applicable_values", ())
    }
    articles["class_labels"] = joined["class"].map(
        lambda value: tuple(
            label
            for label in parse_list_labels(value)
            if label.casefold() not in class_exclusions
        )
    )

    for name, source_column in (
        ("broad", "broad_taxa_groups"),
        ("analysis", "taxa_analysis_groups"),
        ("detail", "taxa_detail_groups"),
    ):
        scheme = schemes[name]
        order = tuple(scheme["group_order"])
        unresolved = scheme["unresolved_group"]
        all_column = f"{name}_groups_all"
        biological_column = f"{name}_groups"
        articles[all_column] = joined[source_column].map(
            lambda value, order=order, name=name: _ordered_labels(
                value, order, f"{name.title()} taxon groups"
            )
        )
        articles[biological_column] = articles[all_column].map(
            lambda labels, unresolved=unresolved: tuple(
                label for label in labels if label != unresolved
            )
        )
        articles[f"n_{name}_groups"] = articles[biological_column].map(len)
        articles[f"taxa_{name}_state"] = [
            _scheme_state(all_groups, biological_groups, unresolved)
            for all_groups, biological_groups in zip(
                articles[all_column], articles[biological_column]
            )
        ]

    broad_order = tuple(schemes["broad"]["group_order"])
    broad_unresolved = schemes["broad"]["unresolved_group"]
    broad_biological = set(broad_order).difference({broad_unresolved})
    llm_items = joined["llm_taxa_json"].map(_parse_json_items)
    articles["taxa_broad_inclusion_state"] = [
        _broad_inclusion_state(groups, items, broad_biological, broad_unresolved)
        for groups, items in zip(articles["broad_groups_all"], llm_items)
    ]

    global_status: Counter[str] = Counter()
    global_reason: Counter[str] = Counter()
    global_special: Counter[str] = Counter()
    per_article_status: list[Counter[str]] = []
    for value in joined["taxa_match_status_json"]:
        status_counts: Counter[str] = Counter()
        for item in _parse_json_items(value):
            status = str(item.get("status") or "<missing>").strip()
            status_counts[status] += 1
            global_status[status] += 1
            assignments = item.get("group_assignments")
            broad = (
                (assignments.get("broad") or {})
                if isinstance(assignments, dict)
                else {}
            )
            reason = str(broad.get("reason") or "<missing>").strip()
            global_reason[reason] += 1
            if status == "special_value":
                value_name = str(item.get("canonical_name") or "<missing>").strip()
                global_special[value_name] += 1
        per_article_status.append(status_counts)
    for status in global_status:
        articles[f"match_status_count__{_slug(status)}"] = [
            counts[status] for counts in per_article_status
        ]
    articles["n_drivers"] = articles["drivers"].map(len)

    source_audit = [
        {
            "source": "eligible merged corpus",
            "rows": len(corpus_df),
            "unique_UT": corpus_df["UT"].nunique(),
            "missing_UT": int(corpus_df["UT"].isna().sum()),
            "duplicated_UT": int(corpus_df["UT"].duplicated().sum()),
            "grain": "one row per UT",
        },
        {
            "source": "taxa-with-api",
            "rows": len(taxa),
            "unique_UT": taxa["UT"].nunique(),
            "missing_UT": int(taxa["UT"].isna().sum()),
            "duplicated_UT": int(taxa["UT"].duplicated().sum()),
            "grain": "one row per UT",
        },
    ]
    total_items = sum(global_status.values())
    eligible_statuses = set(mapping.get("eligible_match_statuses", ()))
    audits = {
        "source_grain": source_audit,
        "match_status": [
            {
                "match_status": status,
                "taxon_item_count": count,
                "share_of_taxon_items_pct": count / total_items * 100,
                "eligible_for_grouping": status in eligible_statuses,
            }
            for status, count in global_status.most_common()
        ],
        "broad_group_reason": [
            {
                "broad_group_reason": reason,
                "taxon_item_count": count,
                "share_of_taxon_items_pct": count / total_items * 100,
            }
            for reason, count in global_reason.most_common()
        ],
        "special_value": [
            {
                "special_value": value,
                "taxon_item_count": count,
                "share_of_special_values_pct": (
                    count / sum(global_special.values()) * 100
                    if global_special
                    else np.nan
                ),
                "article_exclusion_value": value.casefold()
                in SPECIAL_EXCLUSION_VALUES,
            }
            for value, count in global_special.most_common()
        ],
        "auxiliary_labels": _auxiliary_inventory(articles),
    }
    return articles, audits


def build_gbif_broad_benchmark(
    gbif_path: str | Path,
    mapping_path: str | Path,
) -> DescribedDiversity:
    """Build the accepted species-rank broad benchmark once for later results."""
    from data_helpers.analysis.taxa import benchmark as taxa_driver

    broad_mapping = taxa_driver.load_broad_group_mapping(mapping_path)
    return taxa_driver.build_described_diversity_benchmark(
        gbif_path, broad_mapping
    )


def build_manifest(
    articles: pd.DataFrame,
    benchmark: DescribedDiversity,
    *,
    mapping: Mapping[str, Any],
    audits: Mapping[str, list[dict[str, Any]]],
    sources: Mapping[str, str | Path],
) -> dict[str, Any]:
    """Create compact processing provenance and reconciliation audits."""
    if len(articles) != articles["UT"].nunique():
        raise TaxaAnalysisPrepError("Prepared publications are not one row per UT.")
    scheme_audits: dict[str, Any] = {}
    for name in ("broad", "analysis", "detail"):
        state_counts = articles[f"taxa_{name}_state"].value_counts()
        scheme_audits[name] = {
            "group_order": mapping["schemes"][name]["group_order"],
            "state_counts": {key: int(value) for key, value in state_counts.items()},
            "resolved_publications": int(articles[f"n_{name}_groups"].gt(0).sum()),
        }
    broad_inclusion = articles["taxa_broad_inclusion_state"].value_counts()
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "grouping_rules_sha256": grouping_rules_fingerprint(mapping),
        "sources": {name: _source_signature(path) for name, path in sources.items()},
        "artifacts": {
            "taxa_publications": "taxa_publications.parquet",
            "gbif_broad_benchmark": "gbif_broad_benchmark.csv",
        },
        "rows": {
            "taxa_publications": len(articles),
            "unique_UT": articles["UT"].nunique(),
            "gbif_benchmark_groups": len(benchmark.counts),
        },
        "group_schemes": scheme_audits,
        "broad_inclusion_counts": {
            state: int(broad_inclusion.get(state, 0)) for state in INCLUSION_ORDER
        },
        "benchmark_audit": benchmark.audit.to_dict(orient="records"),
        "audits": dict(audits),
    }


def _json_default(value: Any) -> Any:
    """Convert pandas/numpy scalar values used in compact audit records."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if pd.isna(value):
        return None
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class TaxaPreparedStore:
    """Write and validate the three-file prepared taxa bundle."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.article_path = self.root / "taxa_publications.parquet"
        self.benchmark_path = self.root / "gbif_broad_benchmark.csv"
        self.manifest_path = self.root / "manifest.json"

    def write(self, bundle: TaxaPreparedBundle) -> list[Path]:
        self.root.mkdir(parents=True, exist_ok=True)
        bundle.articles.to_parquet(
            self.article_path, index=False, compression="zstd"
        )
        bundle.benchmark.counts.to_csv(self.benchmark_path, index=False)
        self.manifest_path.write_text(
            json.dumps(
                bundle.manifest,
                indent=2,
                sort_keys=True,
                default=_json_default,
                allow_nan=False,
            )
            + "\n",
            encoding="utf-8",
        )
        return [self.article_path, self.benchmark_path, self.manifest_path]

    def load(self, *, mapping: Mapping[str, Any]) -> TaxaPreparedBundle:
        missing = [
            path
            for path in (self.article_path, self.benchmark_path, self.manifest_path)
            if not path.exists()
        ]
        if missing:
            raise TaxaAnalysisPrepError(
                "Prepared taxa bundle is missing. Run "
                "notebooks/data_processing/02_taxa_analysis_prep.ipynb. "
                f"Missing: {[str(path) for path in missing]}"
            )
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema_version") != SCHEMA_VERSION:
            raise TaxaAnalysisPrepError(
                "Prepared taxa schema is incompatible; rebuild the prep notebook."
            )
        expected_fingerprint = grouping_rules_fingerprint(mapping)
        if manifest.get("grouping_rules_sha256") != expected_fingerprint:
            raise TaxaAnalysisPrepError(
                "Prepared taxa grouping rules are stale; rebuild the prep notebook."
            )
        articles = pd.read_parquet(self.article_path)
        for column in LIST_COLUMNS:
            articles[column] = articles[column].map(
                lambda value: tuple(value) if value is not None else ()
            )
        _validate_ut(articles, "Prepared taxa publications")
        expected_rows = manifest["rows"]["taxa_publications"]
        if len(articles) != expected_rows:
            raise TaxaAnalysisPrepError(
                "Prepared taxa row count does not match manifest: "
                f"artifact={len(articles):,}, manifest={expected_rows:,}."
            )
        expected_unique = manifest["rows"]["unique_UT"]
        if articles["UT"].nunique() != expected_unique:
            raise TaxaAnalysisPrepError(
                "Prepared taxa unique-UT count does not match the manifest."
            )
        counts = pd.read_csv(self.benchmark_path)
        required_benchmark = {
            "broad_group",
            "described_species_count",
            "described_species_share",
            "described_species_share_pct",
        }
        missing_benchmark = required_benchmark.difference(counts.columns)
        duplicated_groups = (
            int(counts["broad_group"].duplicated().sum())
            if "broad_group" in counts
            else 0
        )
        if missing_benchmark or duplicated_groups:
            raise TaxaAnalysisPrepError(
                "Prepared GBIF benchmark violates its column/group contract: "
                f"missing={sorted(missing_benchmark)}, "
                f"duplicated_groups={duplicated_groups}."
            )
        expected_groups = manifest["rows"]["gbif_benchmark_groups"]
        if len(counts) != expected_groups:
            raise TaxaAnalysisPrepError(
                "Prepared GBIF benchmark group count does not match the manifest."
            )
        benchmark = DescribedDiversity(
            counts=counts,
            audit=pd.DataFrame(manifest.get("benchmark_audit", [])),
        )
        return TaxaPreparedBundle(
            articles=articles,
            benchmark=benchmark,
            manifest=manifest,
        )


def match_status_audit_from_articles(articles: pd.DataFrame) -> pd.DataFrame:
    """Aggregate compact per-publication match-status counters for any subset."""
    rows: list[dict[str, Any]] = []
    columns = [
        column for column in articles if column.startswith("match_status_count__")
    ]
    total = int(articles[columns].sum().sum())
    for column in columns:
        count = int(articles[column].sum())
        status = column.removeprefix("match_status_count__")
        rows.append(
            {
                "match_status": status,
                "n_taxon_items": count,
                "share_of_taxon_items_pct": count / total * 100 if total else np.nan,
                "eligible_for_grouping": status in {"exact", "fuzzy_accepted"},
            }
        )
    return pd.DataFrame(rows).sort_values(
        "n_taxon_items", ascending=False, ignore_index=True
    )


__all__ = [
    "INCLUSION_ORDER",
    "TaxaAnalysisPrepError",
    "TaxaPreparedBundle",
    "TaxaPreparedStore",
    "build_gbif_broad_benchmark",
    "build_manifest",
    "build_taxa_publications",
    "grouping_rules_fingerprint",
    "load_taxa_mapping",
    "match_status_audit_from_articles",
]
