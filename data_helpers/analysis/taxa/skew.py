"""Publication-level taxonomic attention relative to described diversity.

The analysis keeps one row per publication while loading the taxa, driver,
Threats L0, and ecosystem-realm coding outputs. Multi-group publications are
fractionally allocated so every included publication contributes total weight
one to the headline taxonomic composition.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from data_helpers.labels import parse_list_labels
from data_helpers.analysis.taxa.benchmark import DescribedDiversity
from data_helpers.visualization import save_figure


class TaxaSkewError(ValueError):
    """Raised when a source or calculation violates the analysis contract."""


@dataclass(frozen=True)
class TaxaSkewSources:
    """Minimal source frames and their one-row-per-UT joined table."""

    taxa: pd.DataFrame
    driver: pd.DataFrame
    threats_l0: pd.DataFrame
    realm: pd.DataFrame
    articles: pd.DataFrame
    audit: pd.DataFrame


@dataclass(frozen=True)
class TaxaSkewEvidence:
    """Prepared article evidence, taxonomic attributions, and audits."""

    articles: pd.DataFrame
    included: pd.DataFrame
    attributions: pd.DataFrame
    inclusion_audit: pd.DataFrame
    group_audit: pd.DataFrame
    match_status_audit: pd.DataFrame
    group_reason_audit: pd.DataFrame
    special_value_audit: pd.DataFrame
    auxiliary_label_audit: pd.DataFrame


@dataclass(frozen=True)
class TaxaSkewFocus:
    """A publication-balanced re-expression over a subset of broad groups."""

    included: pd.DataFrame
    attributions: pd.DataFrame
    group_audit: pd.DataFrame


@dataclass(frozen=True)
class TaxaSkewAnalysis:
    """Headline comparison, uncertainty, and allocation sensitivity."""

    comparison: pd.DataFrame
    bootstrap_intervals: pd.DataFrame
    allocation_sensitivity: pd.DataFrame


class TaxaSkewResultStore:
    """Save compact tables, article evidence, and figures consistently."""

    def __init__(
        self,
        root: str | Path,
        *,
        table_subdirectory: str = "csv",
        data_subdirectory: str = "data",
        figure_subdirectory: str = "figures",
    ) -> None:
        self.root = Path(root)
        self.table_directory = self.root / table_subdirectory
        self.data_directory = self.root / data_subdirectory
        self.figure_directory = self.root / figure_subdirectory

    def save_table(
        self, table: pd.DataFrame, filename: str, *, index: bool = False
    ) -> Path:
        self.table_directory.mkdir(parents=True, exist_ok=True)
        path = self.table_directory / f"{filename}.csv"
        table.to_csv(path, index=index)
        print(f"Saved: {path}")
        return path

    def save_data(self, table: pd.DataFrame, filename: str) -> Path:
        self.data_directory.mkdir(parents=True, exist_ok=True)
        path = self.data_directory / f"{filename}.parquet"
        table.to_parquet(path, index=False)
        print(f"Saved: {path}")
        return path

    def save_json(self, payload: Mapping[str, Any], filename: str) -> Path:
        """Save compact analysis provenance beside the reported CSV tables."""
        self.table_directory.mkdir(parents=True, exist_ok=True)
        path = self.table_directory / f"{filename}.json"
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"Saved: {path}")
        return path

    def export_figure(self, figure: Any, filename: str) -> list[Path]:
        figure.set_layout_engine("none")
        return save_figure(
            figure,
            self.figure_directory / filename,
            formats=["pdf"],
            facecolor="white",
        )


SOURCE_COLUMNS: dict[str, tuple[str, ...]] = {
    "taxa": (
        "UT",
        "publication_year",
        "broad_taxa_groups",
        "llm_taxa_json",
        "taxa_match_status_json",
        "taxa_record_status",
        "n_llm_taxa",
        "n_taxa_matched",
        "n_taxa_unresolved",
        "n_taxa_api_failed",
    ),
    "driver": ("UT", "driver"),
    "threats_l0": ("UT", "pred_threat_l0"),
    "realm": ("UT", "realm"),
}

AUXILIARY_LABEL_COLUMNS = {
    "driver": "driver",
    "threats_l0": "pred_threat_l0",
    "realm": "realm",
}

NOT_APPLICABLE_VALUES = {"not applicable", "non applicable"}
UNCLEAR_VALUES = {"unclear"}
SPECIAL_EXCLUSION_VALUES = NOT_APPLICABLE_VALUES | UNCLEAR_VALUES

INCLUSION_ORDER = (
    "Included: at least one benchmarkable broad group",
    "Excluded: Not applicable only",
    "Excluded: Unclear only",
    "Excluded: mixed Not applicable and Unclear",
    "Excluded: accepted taxon but broad hierarchy unresolved",
    "Excluded: reported taxon but no accepted benchmarkable match",
    "Excluded: no taxon item returned",
)


def _read_source(path: str | Path, columns: Iterable[str]) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise TaxaSkewError(f"Required source does not exist: {path}")
    try:
        return pd.read_csv(
            path,
            usecols=list(columns),
            low_memory=False,
        )
    except ValueError as exc:
        raise TaxaSkewError(
            f"Could not read required columns from {path}: {exc}"
        ) from exc


def _validate_ut(frame: pd.DataFrame, source: str) -> None:
    if "UT" not in frame:
        raise TaxaSkewError(f"{source} has no UT column.")
    missing = int(frame["UT"].isna().sum())
    duplicated = int(frame["UT"].duplicated().sum())
    if missing or duplicated:
        raise TaxaSkewError(
            f"{source} violates the one-row-per-UT grain: "
            f"missing={missing:,}, duplicated={duplicated:,}."
        )


def load_coding_sources(paths: Mapping[str, str | Path]) -> TaxaSkewSources:
    """Load minimal columns from four coding outputs and join one-to-one."""
    missing_sources = set(SOURCE_COLUMNS).difference(paths)
    if missing_sources:
        raise TaxaSkewError(
            f"Missing configured coding sources: {sorted(missing_sources)}"
        )

    frames: dict[str, pd.DataFrame] = {}
    for source, columns in SOURCE_COLUMNS.items():
        frame = _read_source(paths[source], columns)
        _validate_ut(frame, source)
        frames[source] = frame

    anchor = frames["taxa"]["UT"].reset_index(drop=True)
    anchor_index = pd.Index(anchor)
    audit_rows: list[dict[str, Any]] = []
    for source, frame in frames.items():
        source_index = pd.Index(frame["UT"])
        audit_rows.append(
            {
                "source": source,
                "path": str(Path(paths[source])),
                "rows": len(frame),
                "unique_UT": frame["UT"].nunique(),
                "missing_UT": int(frame["UT"].isna().sum()),
                "duplicated_UT": int(frame["UT"].duplicated().sum()),
                "taxa_UT_missing_from_source": len(
                    anchor_index.difference(source_index, sort=False)
                ),
                "source_UT_missing_from_taxa": len(
                    source_index.difference(anchor_index, sort=False)
                ),
                "same_UT_order_as_taxa": source_index.equals(anchor_index),
                "columns_loaded": len(frame.columns),
                "grain": "one row per UT",
            }
        )
        if not source_index.equals(anchor_index):
            left_only = anchor_index.difference(source_index, sort=False)
            right_only = source_index.difference(anchor_index, sort=False)
            if len(left_only) or len(right_only):
                raise TaxaSkewError(
                    f"{source} does not have the same UT key set as taxa: "
                    f"taxa_only={len(left_only):,}, source_only={len(right_only):,}."
                )

    articles = frames["taxa"].copy()
    for source in ("driver", "threats_l0", "realm"):
        before = articles["UT"].reset_index(drop=True)
        articles = articles.merge(
            frames[source],
            on="UT",
            how="left",
            sort=False,
            validate="one_to_one",
        )
        if len(articles) != len(anchor) or not articles["UT"].reset_index(
            drop=True
        ).equals(before):
            raise TaxaSkewError(f"Joining {source} changed the UT grain or order.")

    return TaxaSkewSources(
        taxa=frames["taxa"],
        driver=frames["driver"],
        threats_l0=frames["threats_l0"],
        realm=frames["realm"],
        articles=articles,
        audit=pd.DataFrame(audit_rows),
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


def _ordered_labels(value: Any, order: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, np.ndarray):
        labels = parse_list_labels(value.tolist())
    else:
        labels = parse_list_labels(value)
    observed = set(labels)
    return tuple(label for label in order if label in observed)


def _taxa_inclusion_state(
    broad_groups: tuple[str, ...],
    llm_items: list[dict[str, Any]],
    benchmark_groups: set[str],
    unresolved_group: str,
) -> str:
    if benchmark_groups.intersection(broad_groups):
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


def _match_audits(
    taxa: pd.DataFrame,
    *,
    eligible_match_statuses: Iterable[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    status_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    special_counts: Counter[str] = Counter()
    for value in taxa["taxa_match_status_json"]:
        for item in _parse_json_items(value):
            status = str(item.get("status", "")).strip() or "<missing>"
            status_counts[status] += 1
            broad = (
                ((item.get("group_assignments") or {}).get("broad") or {})
                if isinstance(item.get("group_assignments"), dict)
                else {}
            )
            reason = str(broad.get("reason", "")).strip() or "<missing>"
            reason_counts[reason] += 1
            if status == "special_value":
                special = str(item.get("canonical_name", "")).strip() or "<missing>"
                special_counts[special] += 1

    eligible = set(eligible_match_statuses)
    total_items = sum(status_counts.values())
    status_audit = pd.DataFrame(
        [
            {
                "match_status": status,
                "taxon_item_count": count,
                "share_of_taxon_items_pct": count / total_items * 100,
                "eligible_for_grouping": status in eligible,
            }
            for status, count in status_counts.most_common()
        ]
    )
    reason_audit = pd.DataFrame(
        [
            {
                "broad_group_reason": reason,
                "taxon_item_count": count,
                "share_of_taxon_items_pct": count / total_items * 100,
            }
            for reason, count in reason_counts.most_common()
        ]
    )
    special_total = sum(special_counts.values())
    special_audit = pd.DataFrame(
        [
            {
                "special_value": value,
                "taxon_item_count": count,
                "share_of_special_values_pct": (
                    count / special_total * 100 if special_total else np.nan
                ),
                "article_exclusion_value": value.casefold()
                in SPECIAL_EXCLUSION_VALUES,
            }
            for value, count in special_counts.most_common()
        ]
    )
    return status_audit, reason_audit, special_audit


def auxiliary_label_inventory(sources: TaxaSkewSources) -> pd.DataFrame:
    """Count distinct article-level labels in the three future cross-cut fields."""
    rows: list[dict[str, Any]] = []
    for source, column in AUXILIARY_LABEL_COLUMNS.items():
        frame = getattr(sources, source)
        counter: Counter[str] = Counter()
        for value in frame[column]:
            counter.update(parse_list_labels(value))
        for label, count in counter.most_common():
            rows.append(
                {
                    "source": source,
                    "column": column,
                    "label": label,
                    "n_publications": count,
                    "special_for_later_crosscuts": label.casefold()
                    in SPECIAL_EXCLUSION_VALUES,
                }
            )
    return pd.DataFrame(rows)


def prepare_taxa_skew_evidence(
    sources: TaxaSkewSources,
    *,
    broad_group_order: Iterable[str],
    benchmark_groups: Iterable[str],
    unresolved_group: str,
    eligible_match_statuses: Iterable[str],
) -> TaxaSkewEvidence:
    """Build audited publication evidence without changing the article grain."""
    broad_group_order = tuple(broad_group_order)
    benchmark_groups = tuple(benchmark_groups)
    benchmark_group_set = set(benchmark_groups)
    if not benchmark_group_set.issubset(broad_group_order):
        raise TaxaSkewError("benchmark_groups must be part of broad_group_order.")
    if unresolved_group in benchmark_group_set:
        raise TaxaSkewError("The non-taxonomic unresolved group is not benchmarkable.")

    articles = sources.articles.copy()
    articles["broad_groups_all"] = articles["broad_taxa_groups"].map(
        lambda value: _ordered_labels(value, broad_group_order)
    )
    articles["benchmark_groups"] = articles["broad_groups_all"].map(
        lambda labels: tuple(group for group in benchmark_groups if group in labels)
    )
    articles["n_benchmark_groups"] = articles["benchmark_groups"].map(len)
    articles["llm_taxa_items"] = articles["llm_taxa_json"].map(_parse_json_items)
    articles["taxa_analysis_state"] = articles.apply(
        lambda row: _taxa_inclusion_state(
            row["broad_groups_all"],
            row["llm_taxa_items"],
            benchmark_group_set,
            unresolved_group,
        ),
        axis=1,
    )
    articles["taxa_included"] = articles["taxa_analysis_state"].eq(
        INCLUSION_ORDER[0]
    )
    if not articles["UT"].is_unique or len(articles) != len(sources.articles):
        raise TaxaSkewError("Preparing taxa evidence changed the one-row-per-UT grain.")

    state_counts = articles["taxa_analysis_state"].value_counts()
    inclusion_audit = pd.DataFrame(
        {
            "taxa_analysis_state": INCLUSION_ORDER,
            "included_in_primary": [
                state == INCLUSION_ORDER[0] for state in INCLUSION_ORDER
            ],
            "n_publications": [
                int(state_counts.get(state, 0)) for state in INCLUSION_ORDER
            ],
        }
    )
    inclusion_audit["share_of_all_publications_pct"] = (
        inclusion_audit["n_publications"] / len(articles) * 100
    )
    if inclusion_audit["n_publications"].sum() != len(articles):
        raise TaxaSkewError("Article inclusion categories do not sum to the source.")

    included = articles.loc[articles["taxa_included"]].copy()
    attributions = (
        included[
            ["UT", "publication_year", "benchmark_groups", "n_benchmark_groups"]
        ]
        .explode("benchmark_groups", ignore_index=True)
        .rename(columns={"benchmark_groups": "broad_group"})
    )
    attributions["fractional_publication_weight"] = (
        1.0 / attributions["n_benchmark_groups"]
    )
    article_weights = attributions.groupby("UT")[
        "fractional_publication_weight"
    ].sum()
    if len(article_weights) != len(included) or not np.allclose(
        article_weights.to_numpy(), 1.0
    ):
        raise TaxaSkewError(
            "Fractional broad-group weights do not sum to one per publication."
        )

    group_audit = pd.DataFrame({"broad_group": benchmark_groups})
    unique_counts = attributions.groupby("broad_group")["UT"].nunique()
    effective_counts = attributions.groupby("broad_group")[
        "fractional_publication_weight"
    ].sum()
    group_audit["n_unique_publications"] = (
        group_audit["broad_group"].map(unique_counts).fillna(0).astype(int)
    )
    group_audit["publication_coverage_pct"] = (
        group_audit["n_unique_publications"] / len(included) * 100
    )
    group_audit["effective_publication_count"] = (
        group_audit["broad_group"].map(effective_counts).fillna(0.0)
    )
    group_audit["fractional_attention_share_pct"] = (
        group_audit["effective_publication_count"] / len(included) * 100
    )

    status_audit, reason_audit, special_audit = _match_audits(
        sources.taxa,
        eligible_match_statuses=eligible_match_statuses,
    )
    return TaxaSkewEvidence(
        articles=articles.drop(columns="llm_taxa_items"),
        included=included.drop(columns="llm_taxa_items"),
        attributions=attributions,
        inclusion_audit=inclusion_audit,
        group_audit=group_audit,
        match_status_audit=status_audit,
        group_reason_audit=reason_audit,
        special_value_audit=special_audit,
        auxiliary_label_audit=auxiliary_label_inventory(sources),
    )


def prepare_taxa_skew_from_prepared(
    articles: pd.DataFrame,
    *,
    benchmark_groups: Iterable[str],
    unresolved_group: str,
    match_status_audit: pd.DataFrame,
    group_reason_audit: pd.DataFrame,
    special_value_audit: pd.DataFrame,
    auxiliary_label_audit: pd.DataFrame,
    direction: str | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
) -> TaxaSkewEvidence:
    """Express the canonical prepared handoff as broad-skew evidence.

    Source linkage, label parsing, match accounting, and broad grouping have
    already been performed by ``taxa_analysis_prep``. This adapter retains the
    original Vector 1 estimand while keeping those processing operations out of
    the results notebook.

    ``direction`` and ``start_year``/``end_year`` restrict the analytical
    universe before any weighting. They exist so this baseline can be expressed
    on the same grain as the driver, realm, and temporal analyses, which scope to
    negative-direction evidence in complete publication years. Leaving them at
    ``None`` retains the corpus-wide universe, which spans every screened
    direction and is therefore **not** the biodiversity-loss dataset reported in
    the paper.
    """
    benchmark_groups = tuple(benchmark_groups)
    benchmark_group_set = set(benchmark_groups)
    if not benchmark_groups or len(benchmark_group_set) != len(benchmark_groups):
        raise TaxaSkewError("benchmark_groups must be unique and non-empty.")
    required = {
        "UT",
        "publication_year",
        "broad_groups_all",
        "broad_groups",
        "taxa_broad_inclusion_state",
    }
    if direction is not None:
        required.add("s2_dir")
    missing = required.difference(articles.columns)
    if missing:
        raise TaxaSkewError(
            f"Prepared taxa publications lack required columns: {sorted(missing)}"
        )
    if not articles["UT"].is_unique or articles["UT"].isna().any():
        raise TaxaSkewError("Prepared taxa publications violate one row per UT.")

    if direction is not None:
        articles = articles.loc[articles["s2_dir"].eq(direction)]
    if start_year is not None or end_year is not None:
        years = articles["publication_year"]
        lower = years.ge(start_year) if start_year is not None else True
        upper = years.le(end_year) if end_year is not None else True
        articles = articles.loc[lower & upper]
    if articles.empty:
        raise TaxaSkewError(
            "No publication remains after applying the configured analytical scope."
        )

    evidence_articles = articles.copy()
    evidence_articles["benchmark_groups"] = evidence_articles["broad_groups"].map(
        lambda labels: tuple(group for group in benchmark_groups if group in labels)
    )
    evidence_articles["n_benchmark_groups"] = evidence_articles[
        "benchmark_groups"
    ].map(len)
    evidence_articles["taxa_analysis_state"] = evidence_articles[
        "taxa_broad_inclusion_state"
    ]
    evidence_articles["taxa_included"] = evidence_articles[
        "taxa_analysis_state"
    ].eq(INCLUSION_ORDER[0])

    invalid_included = evidence_articles.loc[
        evidence_articles["taxa_included"]
        & evidence_articles["n_benchmark_groups"].eq(0)
    ]
    if not invalid_included.empty:
        raise TaxaSkewError(
            "Prepared broad inclusion state contains no benchmarkable group."
        )
    if evidence_articles["broad_groups_all"].map(
        lambda labels: unresolved_group in labels
    ).any() and unresolved_group in benchmark_group_set:
        raise TaxaSkewError("The unresolved group cannot be benchmarkable.")

    state_counts = evidence_articles["taxa_analysis_state"].value_counts()
    inclusion_audit = pd.DataFrame(
        {
            "taxa_analysis_state": INCLUSION_ORDER,
            "included_in_primary": [
                state == INCLUSION_ORDER[0] for state in INCLUSION_ORDER
            ],
            "n_publications": [
                int(state_counts.get(state, 0)) for state in INCLUSION_ORDER
            ],
        }
    )
    inclusion_audit["share_of_all_publications_pct"] = (
        inclusion_audit["n_publications"] / len(evidence_articles) * 100
    )
    if inclusion_audit["n_publications"].sum() != len(evidence_articles):
        raise TaxaSkewError("Prepared inclusion states do not sum to the source.")

    included = evidence_articles.loc[evidence_articles["taxa_included"]].copy()
    attributions = (
        included[
            ["UT", "publication_year", "benchmark_groups", "n_benchmark_groups"]
        ]
        .explode("benchmark_groups", ignore_index=True)
        .rename(columns={"benchmark_groups": "broad_group"})
    )
    attributions["fractional_publication_weight"] = (
        1.0 / attributions["n_benchmark_groups"]
    )
    article_weights = attributions.groupby("UT")[
        "fractional_publication_weight"
    ].sum()
    if len(article_weights) != len(included) or not np.allclose(
        article_weights.to_numpy(), 1.0
    ):
        raise TaxaSkewError(
            "Prepared fractional group weights do not sum to one per publication."
        )

    group_audit = pd.DataFrame({"broad_group": benchmark_groups})
    unique_counts = attributions.groupby("broad_group")["UT"].nunique()
    effective_counts = attributions.groupby("broad_group")[
        "fractional_publication_weight"
    ].sum()
    group_audit["n_unique_publications"] = (
        group_audit["broad_group"].map(unique_counts).fillna(0).astype(int)
    )
    group_audit["publication_coverage_pct"] = (
        group_audit["n_unique_publications"] / len(included) * 100
    )
    group_audit["effective_publication_count"] = (
        group_audit["broad_group"].map(effective_counts).fillna(0.0)
    )
    group_audit["fractional_attention_share_pct"] = (
        group_audit["effective_publication_count"] / len(included) * 100
    )
    return TaxaSkewEvidence(
        articles=evidence_articles,
        included=included,
        attributions=attributions,
        inclusion_audit=inclusion_audit,
        group_audit=group_audit,
        match_status_audit=match_status_audit.copy(),
        group_reason_audit=group_reason_audit.copy(),
        special_value_audit=special_value_audit.copy(),
        auxiliary_label_audit=auxiliary_label_audit.copy(),
    )


def focus_taxa_skew_evidence(
    evidence: TaxaSkewEvidence,
    *,
    benchmark_groups: Iterable[str],
) -> TaxaSkewFocus:
    """Rebalance the primary evidence within a specified subset of groups.

    Publications without any focal group leave the focused denominator. Each
    remaining publication contributes total weight one across only its focal
    groups. The function therefore supports literature-aligned comparisons,
    such as an animal-only Vertebrates-versus-Invertebrates sensitivity,
    without re-reading or re-matching the source taxa.
    """
    group_order = tuple(benchmark_groups)
    if not group_order or len(group_order) != len(set(group_order)):
        raise TaxaSkewError("Focused benchmark_groups must be unique and non-empty.")
    available_groups = set(evidence.group_audit["broad_group"])
    if not set(group_order).issubset(available_groups):
        raise TaxaSkewError(
            "Focused benchmark_groups must be part of the prepared evidence."
        )

    focused = evidence.included.copy()
    focused["benchmark_groups"] = focused["benchmark_groups"].map(
        lambda labels: tuple(group for group in group_order if group in labels)
    )
    focused = focused.loc[focused["benchmark_groups"].map(len).gt(0)].copy()
    if focused.empty:
        raise TaxaSkewError("No publication contains a requested focal group.")
    focused["n_benchmark_groups"] = focused["benchmark_groups"].map(len)

    attributions = (
        focused[
            ["UT", "publication_year", "benchmark_groups", "n_benchmark_groups"]
        ]
        .explode("benchmark_groups", ignore_index=True)
        .rename(columns={"benchmark_groups": "broad_group"})
    )
    attributions["fractional_publication_weight"] = (
        1.0 / attributions["n_benchmark_groups"]
    )
    article_weights = attributions.groupby("UT")[
        "fractional_publication_weight"
    ].sum()
    if len(article_weights) != len(focused) or not np.allclose(
        article_weights.to_numpy(), 1.0
    ):
        raise TaxaSkewError(
            "Focused broad-group weights do not sum to one per publication."
        )

    group_audit = pd.DataFrame({"broad_group": group_order})
    unique_counts = attributions.groupby("broad_group")["UT"].nunique()
    effective_counts = attributions.groupby("broad_group")[
        "fractional_publication_weight"
    ].sum()
    group_audit["n_unique_publications"] = (
        group_audit["broad_group"].map(unique_counts).fillna(0).astype(int)
    )
    group_audit["publication_coverage_pct"] = (
        group_audit["n_unique_publications"] / len(focused) * 100
    )
    group_audit["effective_publication_count"] = (
        group_audit["broad_group"].map(effective_counts).fillna(0.0)
    )
    group_audit["fractional_attention_share_pct"] = (
        group_audit["effective_publication_count"] / len(focused) * 100
    )
    return TaxaSkewFocus(
        included=focused,
        attributions=attributions,
        group_audit=group_audit,
    )


def _bootstrap_attention(
    included: pd.DataFrame,
    *,
    group_order: tuple[str, ...],
    n_bootstrap: int,
    seed: int,
) -> np.ndarray:
    if n_bootstrap <= 0:
        raise TaxaSkewError("n_bootstrap must be positive.")
    pattern_counts = (
        included["benchmark_groups"]
        .value_counts(sort=False)
        .rename_axis("benchmark_groups")
        .rename("n_publications")
        .reset_index()
    )
    matrix = np.zeros((len(pattern_counts), len(group_order)), dtype=float)
    positions = {group: position for position, group in enumerate(group_order)}
    for row_index, groups in enumerate(pattern_counts["benchmark_groups"]):
        if not groups:
            raise TaxaSkewError("Included evidence contains an empty group pattern.")
        for group in groups:
            matrix[row_index, positions[group]] = 1.0 / len(groups)
    probabilities = (
        pattern_counts["n_publications"].to_numpy(dtype=float) / len(included)
    )
    rng = np.random.default_rng(seed)
    sampled_patterns = rng.multinomial(
        len(included), probabilities, size=n_bootstrap
    )
    return sampled_patterns @ matrix / len(included) * 100


def analyze_taxonomic_skew(
    evidence: TaxaSkewEvidence | TaxaSkewFocus,
    benchmark: DescribedDiversity,
    *,
    benchmark_groups: Iterable[str],
    n_bootstrap: int,
    seed: int,
) -> TaxaSkewAnalysis:
    """Compare fractional publication attention with the fixed GBIF benchmark."""
    group_order = tuple(benchmark_groups)
    benchmark_counts = (
        benchmark.counts.set_index("broad_group")["described_species_count"]
        .reindex(group_order)
        .fillna(0)
        .astype(int)
    )
    if benchmark_counts.sum() <= 0 or (benchmark_counts <= 0).any():
        raise TaxaSkewError(
            "Every benchmarkable group must have a positive species count."
        )
    benchmark_share = benchmark_counts / benchmark_counts.sum() * 100

    comparison = evidence.group_audit.set_index("broad_group").reindex(group_order)
    comparison["described_species_count"] = benchmark_counts
    comparison["described_species_share_pct"] = benchmark_share
    comparison["expected_effective_publications"] = (
        len(evidence.included) * comparison["described_species_share_pct"] / 100
    )
    comparison["effective_publication_minus_expected"] = (
        comparison["effective_publication_count"]
        - comparison["expected_effective_publications"]
    )
    comparison["attention_minus_described_pp"] = (
        comparison["fractional_attention_share_pct"]
        - comparison["described_species_share_pct"]
    )
    comparison["representation_ratio"] = (
        comparison["fractional_attention_share_pct"]
        / comparison["described_species_share_pct"]
    )
    representation_ratio = comparison["representation_ratio"].to_numpy()
    comparison["log2_representation_ratio"] = np.log2(
        representation_ratio,
        out=np.full_like(representation_ratio, np.nan, dtype=float),
        where=representation_ratio > 0,
    )
    comparison["representation"] = np.where(
        comparison["representation_ratio"] >= 1,
        "Over-attended",
        "Under-attended",
    )

    bootstrap = _bootstrap_attention(
        evidence.included,
        group_order=group_order,
        n_bootstrap=n_bootstrap,
        seed=seed,
    )
    intervals = pd.DataFrame(
        {
            "broad_group": group_order,
            "attention_ci_low_pct": np.quantile(bootstrap, 0.025, axis=0),
            "attention_ci_high_pct": np.quantile(bootstrap, 0.975, axis=0),
        }
    ).set_index("broad_group")
    intervals["gap_ci_low_pp"] = (
        intervals["attention_ci_low_pct"] - comparison["described_species_share_pct"]
    )
    intervals["gap_ci_high_pp"] = (
        intervals["attention_ci_high_pct"]
        - comparison["described_species_share_pct"]
    )
    comparison = comparison.join(intervals)
    comparison.insert(0, "broad_group", comparison.index)
    comparison = comparison.reset_index(drop=True)

    assignment_total = evidence.group_audit["n_unique_publications"].sum()
    single = evidence.included.loc[evidence.included["n_benchmark_groups"].eq(1)]
    single_counts = (
        single["benchmark_groups"]
        .map(lambda groups: groups[0])
        .value_counts()
        .reindex(group_order, fill_value=0)
    )
    sensitivity = evidence.group_audit.set_index("broad_group").reindex(group_order)
    sensitivity = pd.DataFrame(
        {
            "broad_group": group_order,
            "fractional_article_balanced_share_pct": sensitivity[
                "fractional_attention_share_pct"
            ].to_numpy(),
            "full_count_assignment_share_pct": (
                sensitivity["n_unique_publications"] / assignment_total * 100
            ).to_numpy(),
            "single_group_only_share_pct": (
                single_counts / len(single) * 100
            ).to_numpy(),
            "single_group_only_publications": len(single),
        }
    )
    sensitivity["largest_absolute_difference_from_primary_pp"] = (
        sensitivity[
            ["full_count_assignment_share_pct", "single_group_only_share_pct"]
        ]
        .sub(sensitivity["fractional_article_balanced_share_pct"], axis=0)
        .abs()
        .max(axis=1)
    )

    return TaxaSkewAnalysis(
        comparison=comparison,
        bootstrap_intervals=comparison[
            [
                "broad_group",
                "fractional_attention_share_pct",
                "attention_ci_low_pct",
                "attention_ci_high_pct",
                "attention_minus_described_pp",
                "gap_ci_low_pp",
                "gap_ci_high_pp",
            ]
        ].copy(),
        allocation_sensitivity=sensitivity,
    )


def taxonomic_attention_trend(
    included: pd.DataFrame,
    *,
    benchmark_groups: Iterable[str],
    single_group_only: bool = False,
    renormalise_over: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Fractional attention share per benchmark group per publication year.

    Uses the same article-balanced weighting as ``analyze_taxonomic_skew``: each
    publication carries total weight one, split evenly across the benchmark groups
    it names, so a publication naming two groups adds 0.5 to each rather than 1.
    Shares therefore sum to 100% within every year.

    ``single_group_only`` restricts to publications naming exactly one group, and
    ``renormalise_over`` restricts the denominator to a subset of groups (used to
    check that a residual bucket is not driving an apparent trend). Both are
    robustness levers; neither is the primary specification.
    """
    benchmark_groups = tuple(benchmark_groups)
    kept = tuple(renormalise_over) if renormalise_over is not None else benchmark_groups
    unknown = set(kept).difference(benchmark_groups)
    if unknown:
        raise TaxaSkewError(
            f"renormalise_over contains non-benchmark groups: {sorted(unknown)}"
        )
    required = {"publication_year", "benchmark_groups"}
    missing = required.difference(included.columns)
    if missing:
        raise TaxaSkewError(f"Included frame is missing columns: {sorted(missing)}")

    records: list[tuple[int, str, float]] = []
    for year, groups in zip(included["publication_year"], included["benchmark_groups"]):
        groups = tuple(groups or ())
        if single_group_only and len(groups) != 1:
            continue
        retained = [group for group in groups if group in kept]
        if not retained:
            continue
        weight = 1.0 / len(retained)
        for group in retained:
            records.append((int(year), group, weight))
    if not records:
        raise TaxaSkewError("No publications remain after filtering; cannot build a trend.")

    long = pd.DataFrame(records, columns=["publication_year", "broad_group", "weight"])
    per_year = long.groupby(["publication_year", "broad_group"], as_index=False)[
        "weight"
    ].sum()
    per_year = per_year.rename(columns={"weight": "effective_publication_count"})
    totals = per_year.groupby("publication_year")["effective_publication_count"].transform("sum")
    per_year["fractional_attention_share_pct"] = (
        per_year["effective_publication_count"] / totals * 100.0
    )
    per_year["n_effective_publications_year"] = totals

    complete = pd.MultiIndex.from_product(
        [sorted(per_year["publication_year"].unique()), kept],
        names=["publication_year", "broad_group"],
    )
    per_year = (
        per_year.set_index(["publication_year", "broad_group"])
        .reindex(complete)
        .fillna({"effective_publication_count": 0.0, "fractional_attention_share_pct": 0.0})
        .reset_index()
    )

    yearly_totals = per_year.groupby("publication_year")[
        "fractional_attention_share_pct"
    ].sum()
    if not np.allclose(yearly_totals.to_numpy(), 100.0):
        raise TaxaSkewError("Yearly attention shares must each sum to 100%.")
    return per_year.sort_values(["broad_group", "publication_year"]).reset_index(drop=True)


def summarise_attention_trend(
    trend: pd.DataFrame,
    *,
    described_shares: Mapping[str, float] | None = None,
) -> pd.DataFrame:
    """Per-group start, end, and ordinary-least-squares slope in points per decade.

    ``described_shares`` are the static described-diversity percentages; when given,
    the ratio of attention to described diversity is reported for the first and last
    year so the reader can see whether a gap closed or widened.
    """
    rows: list[dict[str, Any]] = []
    for group, block in trend.groupby("broad_group", sort=False):
        block = block.sort_values("publication_year")
        years = block["publication_year"].to_numpy(dtype=float)
        shares = block["fractional_attention_share_pct"].to_numpy(dtype=float)
        slope = float(np.polyfit(years, shares, 1)[0]) * 10.0
        record = {
            "broad_group": group,
            "start_year": int(years[0]),
            "end_year": int(years[-1]),
            "start_share_pct": float(shares[0]),
            "end_share_pct": float(shares[-1]),
            "change_pp": float(shares[-1] - shares[0]),
            "slope_pp_per_decade": slope,
        }
        if described_shares is not None and group in described_shares:
            described = float(described_shares[group])
            record["described_species_share_pct"] = described
            record["start_representation_ratio"] = float(shares[0]) / described
            record["end_representation_ratio"] = float(shares[-1]) / described
        rows.append(record)
    return pd.DataFrame(rows)


__all__ = [
    "DescribedDiversity",
    "TaxaSkewAnalysis",
    "TaxaSkewError",
    "TaxaSkewEvidence",
    "TaxaSkewFocus",
    "TaxaSkewResultStore",
    "TaxaSkewSources",
    "analyze_taxonomic_skew",
    "auxiliary_label_inventory",
    "focus_taxa_skew_evidence",
    "load_coding_sources",
    "prepare_taxa_skew_evidence",
    "summarise_attention_trend",
    "taxonomic_attention_trend",
]
