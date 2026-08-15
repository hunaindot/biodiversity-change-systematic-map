"""Symbols removed from live `data_helpers` modules on 2026-08-15.

Snapshot only -- this file is not importable as-is and is not on any import path.
Each block records one symbol (or a tightly-coupled group), the module it came
from, and confirms it had zero references anywhere in the repo outside its own
definition, its own `__all__` entry, and (where noted) its own dedicated unit
test. Verified with `command grep -rnw` scoped across `data_helpers`, the 11
active notebooks (`notebooks/data_processing/*.ipynb`,
`notebooks/results/*.ipynb` excluding `archive/`), `checklists/`, `README.md`,
and `CLAUDE.md` -- excluding the 135GB `data/` directory and any `archive/`
directory, which are not code. To restore a symbol, paste its block back into
the named module at roughly its old location and re-add any import/`__all__`
entry noted below.

This audit was requested directly ("check data_helpers for orphaned code, ignore
archives"), run as a background research agent, then independently spot-checked
by hand before any code was touched. The user then asked for every flagged item
(including one, `plot_regional_representation_and_trend`, previously flagged and
explicitly kept on 2026-08-02/08-05) to be moved to archive.

This is a companion to `.claude/removed-code/2026-08-05-dead-data-helpers-symbols.py`
(untracked, in `.claude/`) and the original 2026-08-01
`notebooks/results/archive/retired-helpers/removed-symbols/removed_symbols.py`
snapshot -- both of which were discovered, mid-audit, to have been lost from
disk (see this folder's README.md). This snapshot is placed under
`notebooks/results/archive/` and explicitly `git add`ed so it cannot silently
vanish the same way.
"""

# =============================================================================
# data_helpers/analysis/taxa/skew.py
# =============================================================================
# A whole legacy "load straight from raw coding CSVs" sub-pipeline, superseded
# by prepare_taxa_skew_from_prepared (which reads the taxa_analysis_prep
# parquet handoff instead). All symbols below were test-covered
# (test_taxa_skew.py) but had zero references in any active notebook or other
# data_helpers module.

# -----------------------------------------------------------------------------
# TaxaSkewSources (dataclass)
# FROM: lines 29-38, between TaxaSkewError and TaxaSkewEvidence
# ALSO REMOVE ON UNDO: "TaxaSkewSources" from __all__ (was alphabetically after
# TaxaSkewResultStore)
# -----------------------------------------------------------------------------

# @dataclass(frozen=True)
# class TaxaSkewSources:
#     """Minimal source frames and their one-row-per-UT joined table."""
#
#     taxa: pd.DataFrame
#     driver: pd.DataFrame
#     threats_l0: pd.DataFrame
#     realm: pd.DataFrame
#     articles: pd.DataFrame
#     audit: pd.DataFrame


# -----------------------------------------------------------------------------
# TaxaSkewFocus (dataclass)
# FROM: lines 56-63, between TaxaSkewEvidence and TaxaSkewAnalysis
# SOLE PRODUCER: focus_taxa_skew_evidence (also removed below) -- with that gone,
# analyze_taxonomic_skew's signature was narrowed from
# `evidence: TaxaSkewEvidence | TaxaSkewFocus` to `evidence: TaxaSkewEvidence`.
# ALSO REMOVE ON UNDO: "TaxaSkewFocus" from __all__; widen
# analyze_taxonomic_skew's `evidence` parameter back to the union type.
# -----------------------------------------------------------------------------

# @dataclass(frozen=True)
# class TaxaSkewFocus:
#     """A publication-balanced re-expression over a subset of broad groups."""
#
#     included: pd.DataFrame
#     attributions: pd.DataFrame
#     group_audit: pd.DataFrame


# -----------------------------------------------------------------------------
# TaxaSkewResultStore.save_data (method)
# FROM: inside TaxaSkewResultStore, between save_table and save_json
# ZERO test coverage (not even called by test_taxa_skew.py), zero notebook use.
# ALSO REMOVE ON UNDO: re-add the `data_subdirectory: str = "data"` __init__
# parameter and `self.data_directory = self.root / data_subdirectory` line,
# both of which existed solely to support this method. Also update the stale
# CLAUDE.md line documenting this class's method surface (was line 176: listed
# `save_data` alongside `save_table`/`save_json`/`export_figure`) -- fixed in
# this same cleanup.
# -----------------------------------------------------------------------------

# def save_data(self, table: pd.DataFrame, filename: str) -> Path:
#     self.data_directory.mkdir(parents=True, exist_ok=True)
#     path = self.data_directory / f"{filename}.parquet"
#     table.to_parquet(path, index=False)
#     print(f"Saved: {path}")
#     return path


# -----------------------------------------------------------------------------
# SOURCE_COLUMNS, AUXILIARY_LABEL_COLUMNS (module constants)
# FROM: lines 127-149, between TaxaSkewResultStore and NOT_APPLICABLE_VALUES
# Sole consumers: load_coding_sources (SOURCE_COLUMNS) and
# auxiliary_label_inventory (AUXILIARY_LABEL_COLUMNS), both removed below.
# ALSO REMOVE ON UNDO: nothing else references these names.
# -----------------------------------------------------------------------------

# SOURCE_COLUMNS: dict[str, tuple[str, ...]] = {
#     "taxa": (
#         "UT",
#         "publication_year",
#         "broad_taxa_groups",
#         "llm_taxa_json",
#         "taxa_match_status_json",
#         "taxa_record_status",
#         "n_llm_taxa",
#         "n_taxa_matched",
#         "n_taxa_unresolved",
#         "n_taxa_api_failed",
#     ),
#     "driver": ("UT", "driver"),
#     "threats_l0": ("UT", "pred_threat_l0"),
#     "realm": ("UT", "realm"),
# }
#
# AUXILIARY_LABEL_COLUMNS = {
#     "driver": "driver",
#     "threats_l0": "pred_threat_l0",
#     "realm": "realm",
# }


# -----------------------------------------------------------------------------
# NOT_APPLICABLE_VALUES, UNCLEAR_VALUES, SPECIAL_EXCLUSION_VALUES (constants)
# FROM: lines 151-153, immediately before INCLUSION_ORDER (INCLUSION_ORDER
# itself is LIVE -- still used by prepare_taxa_skew_from_prepared -- and was
# NOT removed).
# All three were used only inside _taxa_inclusion_state, _match_audits, and
# auxiliary_label_inventory (all removed below); no live function references
# them.
# -----------------------------------------------------------------------------

# NOT_APPLICABLE_VALUES = {"not applicable", "non applicable"}
# UNCLEAR_VALUES = {"unclear"}
# SPECIAL_EXCLUSION_VALUES = NOT_APPLICABLE_VALUES | UNCLEAR_VALUES


# -----------------------------------------------------------------------------
# _read_source, _validate_ut, load_coding_sources
# FROM: lines 166-263, immediately before _parse_json_items
# ALSO REMOVE ON UNDO: "load_coding_sources" from __all__. Re-add the
# `import json` companions if separated (json itself is still used elsewhere
# in skew.py, by save_json, so its import stayed).
# NEEDS ON RESTORE: also restore TaxaSkewSources and SOURCE_COLUMNS above.
# -----------------------------------------------------------------------------

# def _read_source(path: str | Path, columns: Iterable[str]) -> pd.DataFrame:
#     path = Path(path)
#     if not path.exists():
#         raise TaxaSkewError(f"Required source does not exist: {path}")
#     try:
#         return pd.read_csv(
#             path,
#             usecols=list(columns),
#             low_memory=False,
#         )
#     except ValueError as exc:
#         raise TaxaSkewError(
#             f"Could not read required columns from {path}: {exc}"
#         ) from exc
#
#
# def _validate_ut(frame: pd.DataFrame, source: str) -> None:
#     if "UT" not in frame:
#         raise TaxaSkewError(f"{source} has no UT column.")
#     missing = int(frame["UT"].isna().sum())
#     duplicated = int(frame["UT"].duplicated().sum())
#     if missing or duplicated:
#         raise TaxaSkewError(
#             f"{source} violates the one-row-per-UT grain: "
#             f"missing={missing:,}, duplicated={duplicated:,}."
#         )
#
#
# def load_coding_sources(paths: Mapping[str, str | Path]) -> TaxaSkewSources:
#     """Load minimal columns from four coding outputs and join one-to-one."""
#     missing_sources = set(SOURCE_COLUMNS).difference(paths)
#     if missing_sources:
#         raise TaxaSkewError(
#             f"Missing configured coding sources: {sorted(missing_sources)}"
#         )
#
#     frames: dict[str, pd.DataFrame] = {}
#     for source, columns in SOURCE_COLUMNS.items():
#         frame = _read_source(paths[source], columns)
#         _validate_ut(frame, source)
#         frames[source] = frame
#
#     anchor = frames["taxa"]["UT"].reset_index(drop=True)
#     anchor_index = pd.Index(anchor)
#     audit_rows: list[dict[str, Any]] = []
#     for source, frame in frames.items():
#         source_index = pd.Index(frame["UT"])
#         audit_rows.append(
#             {
#                 "source": source,
#                 "path": str(Path(paths[source])),
#                 "rows": len(frame),
#                 "unique_UT": frame["UT"].nunique(),
#                 "missing_UT": int(frame["UT"].isna().sum()),
#                 "duplicated_UT": int(frame["UT"].duplicated().sum()),
#                 "taxa_UT_missing_from_source": len(
#                     anchor_index.difference(source_index, sort=False)
#                 ),
#                 "source_UT_missing_from_taxa": len(
#                     source_index.difference(anchor_index, sort=False)
#                 ),
#                 "same_UT_order_as_taxa": source_index.equals(anchor_index),
#                 "columns_loaded": len(frame.columns),
#                 "grain": "one row per UT",
#             }
#         )
#         if not source_index.equals(anchor_index):
#             left_only = anchor_index.difference(source_index, sort=False)
#             right_only = source_index.difference(anchor_index, sort=False)
#             if len(left_only) or len(right_only):
#                 raise TaxaSkewError(
#                     f"{source} does not have the same UT key set as taxa: "
#                     f"taxa_only={len(left_only):,}, source_only={len(right_only):,}."
#                 )
#
#     articles = frames["taxa"].copy()
#     for source in ("driver", "threats_l0", "realm"):
#         before = articles["UT"].reset_index(drop=True)
#         articles = articles.merge(
#             frames[source],
#             on="UT",
#             how="left",
#             sort=False,
#             validate="one_to_one",
#         )
#         if len(articles) != len(anchor) or not articles["UT"].reset_index(
#             drop=True
#         ).equals(before):
#             raise TaxaSkewError(f"Joining {source} changed the UT grain or order.")
#
#     return TaxaSkewSources(
#         taxa=frames["taxa"],
#         driver=frames["driver"],
#         threats_l0=frames["threats_l0"],
#         realm=frames["realm"],
#         articles=articles,
#         audit=pd.DataFrame(audit_rows),
#     )


# -----------------------------------------------------------------------------
# _parse_json_items, _ordered_labels, _taxa_inclusion_state, _match_audits,
# auxiliary_label_inventory, prepare_taxa_skew_evidence
# FROM: lines 266-512 (contiguous block, immediately before
# prepare_taxa_skew_from_prepared, which is LIVE and was NOT touched)
# ALSO REMOVE ON UNDO: "auxiliary_label_inventory" and
# "prepare_taxa_skew_evidence" from __all__.
# NOTE: `from collections import Counter` and
# `from data_helpers.labels import parse_list_labels` were removed from the
# top of skew.py as part of this cut -- both were used exclusively by
# _match_audits/auxiliary_label_inventory below. Re-add both imports on
# restore.
# -----------------------------------------------------------------------------

# def _parse_json_items(value: Any) -> list[dict[str, Any]]:
#     if not isinstance(value, str) or not value.strip():
#         return []
#     try:
#         parsed = json.loads(value)
#     except json.JSONDecodeError:
#         return []
#     if not isinstance(parsed, list):
#         return []
#     return [item for item in parsed if isinstance(item, dict)]
#
#
# def _ordered_labels(value: Any, order: Iterable[str]) -> tuple[str, ...]:
#     if isinstance(value, np.ndarray):
#         labels = parse_list_labels(value.tolist())
#     else:
#         labels = parse_list_labels(value)
#     observed = set(labels)
#     return tuple(label for label in order if label in observed)
#
#
# def _taxa_inclusion_state(
#     broad_groups: tuple[str, ...],
#     llm_items: list[dict[str, Any]],
#     benchmark_groups: set[str],
#     unresolved_group: str,
# ) -> str:
#     if benchmark_groups.intersection(broad_groups):
#         return INCLUSION_ORDER[0]
#     if unresolved_group in broad_groups:
#         return INCLUSION_ORDER[4]
#
#     names = {
#         str(item.get("canonical_name", "")).strip().casefold()
#         for item in llm_items
#         if str(item.get("canonical_name", "")).strip()
#     }
#     if not llm_items:
#         return INCLUSION_ORDER[6]
#     if names and names.issubset(NOT_APPLICABLE_VALUES):
#         return INCLUSION_ORDER[1]
#     if names and names.issubset(UNCLEAR_VALUES):
#         return INCLUSION_ORDER[2]
#     if names and names.issubset(SPECIAL_EXCLUSION_VALUES):
#         return INCLUSION_ORDER[3]
#     return INCLUSION_ORDER[5]
#
#
# def _match_audits(
#     taxa: pd.DataFrame,
#     *,
#     eligible_match_statuses: Iterable[str],
# ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
#     status_counts: Counter[str] = Counter()
#     reason_counts: Counter[str] = Counter()
#     special_counts: Counter[str] = Counter()
#     for value in taxa["taxa_match_status_json"]:
#         for item in _parse_json_items(value):
#             status = str(item.get("status", "")).strip() or "<missing>"
#             status_counts[status] += 1
#             broad = (
#                 ((item.get("group_assignments") or {}).get("broad") or {})
#                 if isinstance(item.get("group_assignments"), dict)
#                 else {}
#             )
#             reason = str(broad.get("reason", "")).strip() or "<missing>"
#             reason_counts[reason] += 1
#             if status == "special_value":
#                 special = str(item.get("canonical_name", "")).strip() or "<missing>"
#                 special_counts[special] += 1
#
#     eligible = set(eligible_match_statuses)
#     total_items = sum(status_counts.values())
#     status_audit = pd.DataFrame(
#         [
#             {
#                 "match_status": status,
#                 "taxon_item_count": count,
#                 "share_of_taxon_items_pct": count / total_items * 100,
#                 "eligible_for_grouping": status in eligible,
#             }
#             for status, count in status_counts.most_common()
#         ]
#     )
#     reason_audit = pd.DataFrame(
#         [
#             {
#                 "broad_group_reason": reason,
#                 "taxon_item_count": count,
#                 "share_of_taxon_items_pct": count / total_items * 100,
#             }
#             for reason, count in reason_counts.most_common()
#         ]
#     )
#     special_total = sum(special_counts.values())
#     special_audit = pd.DataFrame(
#         [
#             {
#                 "special_value": value,
#                 "taxon_item_count": count,
#                 "share_of_special_values_pct": (
#                     count / special_total * 100 if special_total else np.nan
#                 ),
#                 "article_exclusion_value": value.casefold()
#                 in SPECIAL_EXCLUSION_VALUES,
#             }
#             for value, count in special_counts.most_common()
#         ]
#     )
#     return status_audit, reason_audit, special_audit
#
#
# def auxiliary_label_inventory(sources: TaxaSkewSources) -> pd.DataFrame:
#     """Count distinct article-level labels in the three future cross-cut fields."""
#     rows: list[dict[str, Any]] = []
#     for source, column in AUXILIARY_LABEL_COLUMNS.items():
#         frame = getattr(sources, source)
#         counter: Counter[str] = Counter()
#         for value in frame[column]:
#             counter.update(parse_list_labels(value))
#         for label, count in counter.most_common():
#             rows.append(
#                 {
#                     "source": source,
#                     "column": column,
#                     "label": label,
#                     "n_publications": count,
#                     "special_for_later_crosscuts": label.casefold()
#                     in SPECIAL_EXCLUSION_VALUES,
#                 }
#             )
#     return pd.DataFrame(rows)
#
#
# def prepare_taxa_skew_evidence(
#     sources: TaxaSkewSources,
#     *,
#     broad_group_order: Iterable[str],
#     benchmark_groups: Iterable[str],
#     unresolved_group: str,
#     eligible_match_statuses: Iterable[str],
# ) -> TaxaSkewEvidence:
#     """Build audited publication evidence without changing the article grain."""
#     broad_group_order = tuple(broad_group_order)
#     benchmark_groups = tuple(benchmark_groups)
#     benchmark_group_set = set(benchmark_groups)
#     if not benchmark_group_set.issubset(broad_group_order):
#         raise TaxaSkewError("benchmark_groups must be part of broad_group_order.")
#     if unresolved_group in benchmark_group_set:
#         raise TaxaSkewError("The non-taxonomic unresolved group is not benchmarkable.")
#
#     articles = sources.articles.copy()
#     articles["broad_groups_all"] = articles["broad_taxa_groups"].map(
#         lambda value: _ordered_labels(value, broad_group_order)
#     )
#     articles["benchmark_groups"] = articles["broad_groups_all"].map(
#         lambda labels: tuple(group for group in benchmark_groups if group in labels)
#     )
#     articles["n_benchmark_groups"] = articles["benchmark_groups"].map(len)
#     articles["llm_taxa_items"] = articles["llm_taxa_json"].map(_parse_json_items)
#     articles["taxa_analysis_state"] = articles.apply(
#         lambda row: _taxa_inclusion_state(
#             row["broad_groups_all"],
#             row["llm_taxa_items"],
#             benchmark_group_set,
#             unresolved_group,
#         ),
#         axis=1,
#     )
#     articles["taxa_included"] = articles["taxa_analysis_state"].eq(
#         INCLUSION_ORDER[0]
#     )
#     if not articles["UT"].is_unique or len(articles) != len(sources.articles):
#         raise TaxaSkewError("Preparing taxa evidence changed the one-row-per-UT grain.")
#
#     state_counts = articles["taxa_analysis_state"].value_counts()
#     inclusion_audit = pd.DataFrame(
#         {
#             "taxa_analysis_state": INCLUSION_ORDER,
#             "included_in_primary": [
#                 state == INCLUSION_ORDER[0] for state in INCLUSION_ORDER
#             ],
#             "n_publications": [
#                 int(state_counts.get(state, 0)) for state in INCLUSION_ORDER
#             ],
#         }
#     )
#     inclusion_audit["share_of_all_publications_pct"] = (
#         inclusion_audit["n_publications"] / len(articles) * 100
#     )
#     if inclusion_audit["n_publications"].sum() != len(articles):
#         raise TaxaSkewError("Article inclusion categories do not sum to the source.")
#
#     included = articles.loc[articles["taxa_included"]].copy()
#     attributions = (
#         included[
#             ["UT", "publication_year", "benchmark_groups", "n_benchmark_groups"]
#         ]
#         .explode("benchmark_groups", ignore_index=True)
#         .rename(columns={"benchmark_groups": "broad_group"})
#     )
#     attributions["fractional_publication_weight"] = (
#         1.0 / attributions["n_benchmark_groups"]
#     )
#     article_weights = attributions.groupby("UT")[
#         "fractional_publication_weight"
#     ].sum()
#     if len(article_weights) != len(included) or not np.allclose(
#         article_weights.to_numpy(), 1.0
#     ):
#         raise TaxaSkewError(
#             "Fractional broad-group weights do not sum to one per publication."
#         )
#
#     group_audit = pd.DataFrame({"broad_group": benchmark_groups})
#     unique_counts = attributions.groupby("broad_group")["UT"].nunique()
#     effective_counts = attributions.groupby("broad_group")[
#         "fractional_publication_weight"
#     ].sum()
#     group_audit["n_unique_publications"] = (
#         group_audit["broad_group"].map(unique_counts).fillna(0).astype(int)
#     )
#     group_audit["publication_coverage_pct"] = (
#         group_audit["n_unique_publications"] / len(included) * 100
#     )
#     group_audit["effective_publication_count"] = (
#         group_audit["broad_group"].map(effective_counts).fillna(0.0)
#     )
#     group_audit["fractional_attention_share_pct"] = (
#         group_audit["effective_publication_count"] / len(included) * 100
#     )
#
#     status_audit, reason_audit, special_audit = _match_audits(
#         sources.taxa,
#         eligible_match_statuses=eligible_match_statuses,
#     )
#     return TaxaSkewEvidence(
#         articles=articles.drop(columns="llm_taxa_items"),
#         included=included.drop(columns="llm_taxa_items"),
#         attributions=attributions,
#         inclusion_audit=inclusion_audit,
#         group_audit=group_audit,
#         match_status_audit=status_audit,
#         group_reason_audit=reason_audit,
#         special_value_audit=special_audit,
#         auxiliary_label_audit=auxiliary_label_inventory(sources),
#     )


# -----------------------------------------------------------------------------
# focus_taxa_skew_evidence
# FROM: lines 672-744, between prepare_taxa_skew_from_prepared (LIVE, kept) and
# _bootstrap_attention (LIVE, kept)
# The leftover implementation of the "animal-only Vertebrates-vs-Invertebrates
# sensitivity" check the 2026-08-01 decisions-log entry says was stripped from
# the F4 manuscript notebook.
# ALSO REMOVE ON UNDO: "focus_taxa_skew_evidence" from __all__.
# NEEDS ON RESTORE: also restore TaxaSkewFocus above, and widen
# analyze_taxonomic_skew's `evidence` parameter back to
# `TaxaSkewEvidence | TaxaSkewFocus`.
# -----------------------------------------------------------------------------

# def focus_taxa_skew_evidence(
#     evidence: TaxaSkewEvidence,
#     *,
#     benchmark_groups: Iterable[str],
# ) -> TaxaSkewFocus:
#     """Rebalance the primary evidence within a specified subset of groups.
#
#     Publications without any focal group leave the focused denominator. Each
#     remaining publication contributes total weight one across only its focal
#     groups. The function therefore supports literature-aligned comparisons,
#     such as an animal-only Vertebrates-versus-Invertebrates sensitivity,
#     without re-reading or re-matching the source taxa.
#     """
#     group_order = tuple(benchmark_groups)
#     if not group_order or len(group_order) != len(set(group_order)):
#         raise TaxaSkewError("Focused benchmark_groups must be unique and non-empty.")
#     available_groups = set(evidence.group_audit["broad_group"])
#     if not set(group_order).issubset(available_groups):
#         raise TaxaSkewError(
#             "Focused benchmark_groups must be part of the prepared evidence."
#         )
#
#     focused = evidence.included.copy()
#     focused["benchmark_groups"] = focused["benchmark_groups"].map(
#         lambda labels: tuple(group for group in group_order if group in labels)
#     )
#     focused = focused.loc[focused["benchmark_groups"].map(len).gt(0)].copy()
#     if focused.empty:
#         raise TaxaSkewError("No publication contains a requested focal group.")
#     focused["n_benchmark_groups"] = focused["benchmark_groups"].map(len)
#
#     attributions = (
#         focused[
#             ["UT", "publication_year", "benchmark_groups", "n_benchmark_groups"]
#         ]
#         .explode("benchmark_groups", ignore_index=True)
#         .rename(columns={"benchmark_groups": "broad_group"})
#     )
#     attributions["fractional_publication_weight"] = (
#         1.0 / attributions["n_benchmark_groups"]
#     )
#     article_weights = attributions.groupby("UT")[
#         "fractional_publication_weight"
#     ].sum()
#     if len(article_weights) != len(focused) or not np.allclose(
#         article_weights.to_numpy(), 1.0
#     ):
#         raise TaxaSkewError(
#             "Focused broad-group weights do not sum to one per publication."
#         )
#
#     group_audit = pd.DataFrame({"broad_group": group_order})
#     unique_counts = attributions.groupby("broad_group")["UT"].nunique()
#     effective_counts = attributions.groupby("broad_group")[
#         "fractional_publication_weight"
#     ].sum()
#     group_audit["n_unique_publications"] = (
#         group_audit["broad_group"].map(unique_counts).fillna(0).astype(int)
#     )
#     group_audit["publication_coverage_pct"] = (
#         group_audit["n_unique_publications"] / len(focused) * 100
#     )
#     group_audit["effective_publication_count"] = (
#         group_audit["broad_group"].map(effective_counts).fillna(0.0)
#     )
#     group_audit["fractional_attention_share_pct"] = (
#         group_audit["effective_publication_count"] / len(focused) * 100
#     )
#     return TaxaSkewFocus(
#         included=focused,
#         attributions=attributions,
#         group_audit=group_audit,
#     )


# =============================================================================
# data_helpers/analysis/taxa/skew_plotting.py
# =============================================================================

# -----------------------------------------------------------------------------
# SKEW_CAVEAT (constant) and plot_taxonomic_skew (function)
# FROM: lines 18-22 (constant) and 39-379 (function), the file's original
# opening figure builder, before _ribbon/_separate_labels/_stacked_pair/
# _trend_lines/plot_representation_and_trend (all LIVE, kept).
# Superseded by plot_representation_and_trend per the 2026-08-02 decisions-log
# entry ("Deleted... the superseded plot_taxonomic_skew call").
# ALSO REMOVE ON UNDO: "plot_taxonomic_skew" from __all__ (was
# `["plot_representation_and_trend", "plot_taxonomic_skew"]`). Re-add the
# `import textwrap`, `from matplotlib.lines import Line2D`, and
# `from matplotlib.ticker import FuncFormatter` imports at the top of the file
# -- all three were used exclusively inside this function.
# -----------------------------------------------------------------------------

# SKEW_CAVEAT = (
#     "Measures publication attention, not conservation need, ecological importance, "
#     "population decline, or undescribed diversity. GBIF accepted species-rank share is a "
#     "described-diversity proxy, not a complete species inventory."
# )
#
#
# def plot_taxonomic_skew(
#     comparison: pd.DataFrame,
#     *,
#     group_order: Iterable[str],
#     group_colors: dict[str, str],
#     mapping: Mapping | None = None,
#     scheme_name: str = "broad",
#     manuscript: bool = True,
# ) -> plt.Figure:
#     """Plot absolute composition differences and relative representation.
#
#     ``mapping`` is the full taxa-group config (as returned by
#     ``taxa_analysis_prep.load_taxa_mapping``); when supplied, a tinted PhyloPic
#     silhouette is placed beside each group's y-tick label on both panels.
#     """
#     group_order = tuple(group_order)
#     required = {
#         "broad_group",
#         "effective_publication_count",
#         "fractional_attention_share_pct",
#         "attention_ci_low_pct",
#         "attention_ci_high_pct",
#         "described_species_share_pct",
#         "representation_ratio",
#         "log2_representation_ratio",
#     }
#     missing = required.difference(comparison.columns)
#     if missing:
#         raise ValueError(f"Comparison table is missing columns: {sorted(missing)}")
#     if set(group_colors).issuperset(group_order) is False:
#         raise ValueError("group_colors must cover every plotted broad group.")
#     if set(comparison["broad_group"]) != set(group_order):
#         raise ValueError("Comparison table must contain every broad group once.")
#
#     icon_paths = (
#         taxa_clipart.ensure_clipart_cached(mapping)
#         if mapping and not manuscript
#         else {}
#     )
#     scheme = mapping["schemes"][scheme_name] if mapping and not manuscript else None
#
#     top_row = comparison.loc[comparison["representation_ratio"].idxmax()]
#     bottom_row = comparison.loc[comparison["representation_ratio"].idxmin()]
#     total_publications = float(comparison["effective_publication_count"].sum())
#     headline = (
#         f"{top_row['broad_group']} receive {top_row['representation_ratio']:.2f}× more "
#         f"attention than their described-diversity share; {bottom_row['broad_group']} receive "
#         f"{bottom_row['representation_ratio']:.2f}×. "
#         f"n = {total_publications:,.0f} publications with a resolved benchmark group."
#     )
#
#     fig, (axis_share, axis_ratio) = plt.subplots(
#         1,
#         2,
#         figsize=(7.4, 3.35 if manuscript else 4.75),
#         gridspec_kw={"width_ratios": [1.48, 1.0]},
#     )
#
#     share_data = (
#         comparison.set_index("broad_group")
#         .reindex(group_order)
#         .reset_index()
#     )
#     y_share = np.arange(len(share_data))
#     described = share_data["described_species_share_pct"].to_numpy()
#     attention = share_data["fractional_attention_share_pct"].to_numpy()
#     colors = [group_colors[group] for group in share_data["broad_group"]]
#
#     for position, left, right in zip(y_share, described, attention):
#         axis_share.plot(
#             [left, right],
#             [position, position],
#             color=visualization.BIODIVERSITY["neutral"],
#             linewidth=1.6,
#             solid_capstyle="round",
#             zorder=1,
#         )
#     xerr = np.vstack(
#         [
#             attention - share_data["attention_ci_low_pct"].to_numpy(),
#             share_data["attention_ci_high_pct"].to_numpy() - attention,
#         ]
#     )
#     axis_share.errorbar(
#         attention,
#         y_share,
#         xerr=xerr,
#         fmt="none",
#         ecolor=visualization.BIODIVERSITY["ink"],
#         elinewidth=0.8,
#         capsize=2.2,
#         zorder=2,
#     )
#     axis_share.scatter(
#         described,
#         y_share,
#         s=30,
#         facecolor=visualization.BIODIVERSITY["paper"],
#         edgecolor=visualization.BIODIVERSITY["ink"],
#         linewidth=0.9,
#         zorder=3,
#     )
#     axis_share.scatter(
#         attention,
#         y_share,
#         s=38,
#         c=colors,
#         edgecolor=visualization.BIODIVERSITY["paper"],
#         linewidth=0.7,
#         zorder=4,
#     )
#     for position, benchmark_value, attention_value in zip(
#         y_share, described, attention
#     ):
#         benchmark_offset = -4 if benchmark_value <= attention_value else 4
#         benchmark_alignment = (
#             "right" if benchmark_value <= attention_value else "left"
#         )
#         benchmark_y_offset = 7 if position == len(y_share) - 1 else -8
#         benchmark_vertical_alignment = (
#             "bottom" if position == len(y_share) - 1 else "top"
#         )
#         attention_offset = 4 if attention_value >= benchmark_value else -4
#         attention_alignment = (
#             "left" if attention_value >= benchmark_value else "right"
#         )
#         axis_share.annotate(
#             f"{benchmark_value:.1f}%",
#             (benchmark_value, position),
#             xytext=(benchmark_offset, benchmark_y_offset),
#             textcoords="offset points",
#             ha=benchmark_alignment,
#             va=benchmark_vertical_alignment,
#             fontsize=6.2,
#             color="#666666",
#         )
#         axis_share.annotate(
#             f"{attention_value:.1f}%",
#             (attention_value, position),
#             xytext=(attention_offset, 7),
#             textcoords="offset points",
#             ha=attention_alignment,
#             va="bottom",
#             fontsize=6.4,
#             color=visualization.BIODIVERSITY["ink"],
#         )
#     axis_share.set_yticks(y_share, share_data["broad_group"])
#     if scheme is not None:
#         taxa_clipart.add_group_icons(
#             axis_share,
#             groups=share_data["broad_group"],
#             y_positions=y_share,
#             scheme=scheme,
#             group_colors=group_colors,
#             icon_paths=icon_paths,
#             x_offset=-0.30,
#         )
#     axis_share.invert_yaxis()
#     axis_share.set_xlim(
#         0,
#         max(
#             70,
#             float(
#                 share_data[
#                     [
#                         "attention_ci_high_pct",
#                         "described_species_share_pct",
#                     ]
#                 ]
#                 .max()
#                 .max()
#             )
#             + 5,
#         ),
#     )
#     axis_share.set_xlabel("Share of publications or described species (%)")
#     axis_share.legend(
#         handles=[
#             Line2D(
#                 [0],
#                 [0],
#                 marker="o",
#                 color="none",
#                 markerfacecolor=visualization.BIODIVERSITY["paper"],
#                 markeredgecolor=visualization.BIODIVERSITY["ink"],
#                 markersize=4.8,
#                 label="GBIF accepted species-rank share",
#             ),
#             Line2D(
#                 [0],
#                 [0],
#                 marker="o",
#                 color="none",
#                 markerfacecolor=visualization.BIODIVERSITY["primary"],
#                 markeredgecolor=visualization.BIODIVERSITY["paper"],
#                 markersize=5.4,
#                 label="Publication attention (95% bootstrap CI)",
#             ),
#         ],
#         loc="lower left",
#         bbox_to_anchor=(0.0, 1.015),
#         ncol=2,
#         frameon=False,
#         fontsize=6.2,
#         columnspacing=1.0,
#         handletextpad=0.4,
#         borderaxespad=0.0,
#     )
#     _neutral_axes(axis_share)
#
#     ratio_data = (
#         comparison.set_index("broad_group")
#         .reindex(group_order)
#         .reset_index()
#     )
#     y_ratio = np.arange(len(ratio_data))
#     log_ratio = ratio_data["log2_representation_ratio"].to_numpy()
#     ratio_colors = [group_colors[group] for group in ratio_data["broad_group"]]
#     axis_ratio.axvline(
#         0,
#         color=visualization.BIODIVERSITY["ink"],
#         linewidth=0.8,
#         linestyle=(0, (3, 2)),
#         zorder=1,
#     )
#     for position, value in zip(y_ratio, log_ratio):
#         axis_ratio.plot(
#             [0, value],
#             [position, position],
#             color=visualization.BIODIVERSITY["neutral"],
#             linewidth=1.4,
#             solid_capstyle="round",
#             zorder=1,
#         )
#     axis_ratio.scatter(
#         log_ratio,
#         y_ratio,
#         s=38,
#         c=ratio_colors,
#         edgecolor=visualization.BIODIVERSITY["paper"],
#         linewidth=0.7,
#         zorder=3,
#     )
#     for position, value, ratio in zip(
#         y_ratio, log_ratio, ratio_data["representation_ratio"]
#     ):
#         place_right = value >= 0 or value <= -1.5
#         axis_ratio.annotate(
#             f"{ratio:.2f}×",
#             (value, position),
#             xytext=(5 if place_right else -5, 0),
#             textcoords="offset points",
#             ha="left" if place_right else "right",
#             va="center",
#             fontsize=6.5,
#             color=visualization.BIODIVERSITY["ink"],
#         )
#     axis_ratio.set_yticks(y_ratio, ratio_data["broad_group"])
#     if scheme is not None:
#         taxa_clipart.add_group_icons(
#             axis_ratio,
#             groups=ratio_data["broad_group"],
#             y_positions=y_ratio,
#             scheme=scheme,
#             group_colors=group_colors,
#             icon_paths=icon_paths,
#             x_offset=-0.34,
#         )
#     axis_ratio.invert_yaxis()
#     lower = min(-2.5, float(np.floor(log_ratio.min() * 2) / 2) - 0.25)
#     upper = max(3.0, float(np.ceil(log_ratio.max() * 2) / 2) + 0.45)
#     axis_ratio.set_xlim(lower, upper)
#     ticks = np.arange(np.ceil(lower), np.floor(upper) + 1)
#     axis_ratio.set_xticks(ticks)
#     axis_ratio.xaxis.set_major_formatter(
#         FuncFormatter(lambda value, _: f"{2 ** value:g}×")
#     )
#     axis_ratio.set_xlabel("Representation ratio (log2 scale)")
#     axis_ratio.text(
#         0,
#         1.015,
#         "Proportional attention",
#         transform=axis_ratio.get_xaxis_transform(),
#         ha="center",
#         va="bottom",
#         fontsize=6.2,
#         color="#666666",
#     )
#     _neutral_axes(axis_ratio)
#
#     axis_share.text(
#         -0.16,
#         1.03,
#         "A",
#         transform=axis_share.transAxes,
#         fontsize=9,
#         fontweight="bold",
#         va="bottom",
#     )
#     axis_ratio.text(
#         -0.20,
#         1.03,
#         "B",
#         transform=axis_ratio.transAxes,
#         fontsize=9,
#         fontweight="bold",
#         va="bottom",
#     )
#     if manuscript:
#         fig.subplots_adjust(
#             left=0.16,
#             right=0.985,
#             top=0.86,
#             bottom=0.16,
#             wspace=0.36,
#         )
#     else:
#         fig.suptitle(
#             "Taxonomic attention versus described diversity",
#             x=0.02,
#             y=0.99,
#             ha="left",
#             fontsize=10,
#             color=visualization.BIODIVERSITY["ink"],
#         )
#         fig.text(0.02, 0.945, headline, ha="left", va="top", fontsize=7.5, color="#555555")
#         caveat = SKEW_CAVEAT
#         if icon_paths:
#             caveat = f"{caveat} {taxa_clipart.CLIPART_CREDIT}"
#         fig.text(0.02, 0.02, textwrap.fill(caveat, 150), fontsize=5.3, color="#777777")
#         fig.subplots_adjust(
#             left=0.20,
#             right=0.985,
#             top=0.80,
#             bottom=0.18,
#             wspace=0.43,
#         )
#     return fig


# =============================================================================
# data_helpers/analysis/realm/driver_plotting.py
# =============================================================================

# -----------------------------------------------------------------------------
# _fold_change_label (helper) and plot_driver_lq_heatmap (function)
# FROM: lines 101-108 (helper) and 147-293 (function), between
# _validate_common_inputs and plot_driver_fractional_bars (LIVE, kept).
# Standalone driver x realm Location-Quotient heatmap; 03_realm_composition.ipynb
# only calls plot_driver_fractional_bars and plot_pollution_nameability_trends.
# _fold_change_label was exclusive to this function; every other private helper
# it used (_matrix, _support_label, _validate_common_inputs, _validate_order,
# _validate_mapping) is also called by the two live functions and was left
# untouched.
# ALSO REMOVE ON UNDO: "plot_driver_lq_heatmap" from __all__.
# -----------------------------------------------------------------------------

# def _fold_change_label(log2_value: float) -> str:
#     fold_change = 2.0**log2_value
#     if np.isclose(fold_change, round(fold_change), atol=1e-10):
#         return f"{fold_change:.0f}×"
#     if fold_change >= 1:
#         return f"{fold_change:.1f}×"
#     return f"{fold_change:.2g}×"
#
#
# def plot_driver_lq_heatmap(
#     estimates: pd.DataFrame,
#     *,
#     driver_order: Sequence[str],
#     realm_order: Sequence[str],
#     driver_names: Mapping[str, str],
#     realm_names: Mapping[str, str],
#     realm_supports: Mapping[str, int],
#     lq_limit: float = 2.0,
# ) -> plt.Figure:
#     """Plot a standalone LQ heatmap with color as the sole cell encoding."""
#     drivers, realms = _validate_common_inputs(
#         driver_order=driver_order,
#         realm_order=realm_order,
#         driver_names=driver_names,
#         realm_names=realm_names,
#         realm_supports=realm_supports,
#     )
#     if (
#         not isinstance(lq_limit, Real)
#         or isinstance(lq_limit, bool)
#         or not np.isfinite(lq_limit)
#         or lq_limit <= 0
#     ):
#         raise ValueError("lq_limit must be a finite positive number")
#     log2_lq = _matrix(
#         estimates,
#         value="log2_lq",
#         realms=realms,
#         drivers=drivers,
#     )
#     if log2_lq.isna().any().any():
#         raise ValueError("log2_lq cannot contain missing values")
#
#     figure, axis = plt.subplots(figsize=(7.4, 5.0))
#     norm = mcolors.TwoSlopeNorm(
#         vmin=-float(lq_limit),
#         vcenter=0,
#         vmax=float(lq_limit),
#     )
#     color_map = plt.get_cmap("PRGn")
#     values = np.clip(log2_lq.to_numpy(), -lq_limit, lq_limit)
#     mesh = axis.pcolormesh(
#         np.arange(len(drivers) + 1),
#         np.arange(len(realms) + 1),
#         values,
#         cmap=color_map,
#         norm=norm,
#         shading="flat",
#         edgecolors=BIODIVERSITY["paper"],
#         linewidth=0.45,
#         antialiased=False,
#     )
#     axis.set(
#         xlim=(0, len(drivers)),
#         ylim=(len(realms), 0),
#         xticks=np.arange(len(drivers)) + 0.5,
#         yticks=np.arange(len(realms)) + 0.5,
#         xticklabels=[
#             fill(
#                 driver_names[driver],
#                 width=13,
#                 break_long_words=False,
#                 break_on_hyphens=False,
#             )
#             for driver in drivers
#         ],
#         yticklabels=[
#             _support_label(
#                 realm,
#                 realm_names=realm_names,
#                 realm_supports=realm_supports,
#             )
#             for realm in realms
#         ],
#     )
#     axis.tick_params(
#         axis="x",
#         top=True,
#         labeltop=True,
#         bottom=False,
#         labelbottom=False,
#         length=0,
#         colors=BIODIVERSITY["ink"],
#         labelsize=7.5,
#         pad=5,
#     )
#     axis.tick_params(
#         axis="y",
#         length=0,
#         colors=BIODIVERSITY["ink"],
#         labelsize=7.5,
#         pad=5,
#     )
#     axis.spines[:].set_visible(False)
#     axis.grid(False)
#
#     finite = log2_lq.to_numpy()[np.isfinite(log2_lq.to_numpy())]
#     low_tail = np.isneginf(log2_lq.to_numpy()).any() or (
#         finite.size and finite.min() < -lq_limit
#     )
#     high_tail = np.isposinf(log2_lq.to_numpy()).any() or (
#         finite.size and finite.max() > lq_limit
#     )
#     extend = (
#         "both"
#         if low_tail and high_tail
#         else "min"
#         if low_tail
#         else "max"
#         if high_tail
#         else "neither"
#     )
#     ticks = np.linspace(-lq_limit, lq_limit, 5)
#     colorbar = figure.colorbar(
#         mesh,
#         ax=axis,
#         orientation="vertical",
#         fraction=0.035,
#         pad=0.035,
#         ticks=ticks,
#         extend=extend,
#     )
#     colorbar.ax.set_yticklabels([_fold_change_label(value) for value in ticks])
#     colorbar.ax.tick_params(
#         length=0,
#         colors=BIODIVERSITY["ink"],
#         labelsize=7.5,
#     )
#     colorbar.outline.set_linewidth(0.5)
#     colorbar.outline.set_edgecolor(BIODIVERSITY["neutral"])
#     colorbar.set_label(
#         "Driver prevalence / pooled prevalence",
#         fontsize=8.5,
#         labelpad=5,
#     )
#     figure.text(
#         0.305,
#         0.018,
#         f"† Realm support < {LOW_SUPPORT_THRESHOLD} publications",
#         fontsize=6.8,
#         color=BIODIVERSITY["ink"],
#     )
#     figure.subplots_adjust(left=0.305, right=0.90, top=0.84, bottom=0.07)
#     return figure


# =============================================================================
# data_helpers/analysis/taxa/clipart.py
# =============================================================================

# -----------------------------------------------------------------------------
# add_title_icon
# FROM: lines 105-133, the file's last function, after add_group_icons (LIVE,
# kept -- used by 04_taxonomic_lens.ipynb).
# Sibling to add_group_icons but places the taxon silhouette beside a panel
# *title* instead of beside a y-axis label. Zero test coverage, zero notebook
# usage.
# ALSO REMOVE ON UNDO: "add_title_icon" from __all__.
# -----------------------------------------------------------------------------

# def add_title_icon(
#     axis: Axes,
#     *,
#     group: str,
#     scheme: Mapping,
#     group_colors: Mapping[str, str],
#     icon_paths: Mapping[str, Path],
#     zoom: float = 0.11,
#     position: tuple[float, float] = (-0.03, 1.16),
# ) -> None:
#     """Place a small tinted taxon silhouette beside a panel title.
#
#     ``position`` is in axes-fraction coordinates (both axes), anchored above
#     the panel so it sits next to a title set with ``loc="left"``.
#     """
#     asset_name = scheme["group_clipart"].get(group)
#     if asset_name is None or asset_name not in icon_paths:
#         return
#     rgba = _tinted_icon(icon_paths[asset_name], group_colors[group])
#     offset_image = OffsetImage(rgba, zoom=zoom)
#     annotation = AnnotationBbox(
#         offset_image,
#         position,
#         xycoords="axes fraction",
#         frameon=False,
#         box_alignment=(1, 0.5),
#         annotation_clip=False,
#     )
#     axis.add_artist(annotation)


# =============================================================================
# data_helpers/prep/taxa_analysis_prep.py
# =============================================================================

# -----------------------------------------------------------------------------
# match_status_audit_from_articles
# FROM: lines 1051-1071, the file's last function, immediately before __all__.
# Zero test coverage, zero notebook usage -- not even wired into
# 02_taxa_analysis_prep.ipynb, its natural consumer.
# ALSO REMOVE ON UNDO: "match_status_audit_from_articles" from __all__.
# -----------------------------------------------------------------------------

# def match_status_audit_from_articles(articles: pd.DataFrame) -> pd.DataFrame:
#     """Aggregate compact per-publication match-status counters for any subset."""
#     rows: list[dict[str, Any]] = []
#     columns = [
#         column for column in articles if column.startswith("match_status_count__")
#     ]
#     total = int(articles[columns].sum().sum())
#     for column in columns:
#         count = int(articles[column].sum())
#         status = column.removeprefix("match_status_count__")
#         rows.append(
#             {
#                 "match_status": status,
#                 "n_taxon_items": count,
#                 "share_of_taxon_items_pct": count / total * 100 if total else np.nan,
#                 "eligible_for_grouping": status in {"exact", "fuzzy_accepted"},
#             }
#         )
#     return pd.DataFrame(rows).sort_values(
#         "n_taxon_items", ascending=False, ignore_index=True
#     )


# =============================================================================
# data_helpers/analysis/taxa/threat_gap_plotting.py
# =============================================================================
# The entire file was reduced to REGION_ORDER + REGION_COLORS (both LIVE --
# imported directly into 04_taxonomic_lens.ipynb) plus __all__. Everything
# below was removed as one block; all of it existed solely to support
# plot_regional_representation_and_trend.
#
# NOTE ON PRIOR DECISION: this function (+ TaxaThreatGapPlotError) was
# previously flagged as test-only-dead on 2026-08-02 and again in the
# 2026-08-05 repo-wide audit, and deliberately KEPT both times ("small,
# reusable, in case the geographic panel is ever needed alone"). The user
# explicitly asked, in this 2026-08-15 cleanup, to archive it anyway --
# overriding that prior decision.
# ALSO REMOVE ON UNDO: re-add "TaxaThreatGapPlotError" and
# "plot_regional_representation_and_trend" to __all__. Re-add the removed
# imports: `from typing import Iterable, Mapping`, `import matplotlib.pyplot
# as plt`, `import pandas as pd`, `from data_helpers import visualization`,
# and `from data_helpers.analysis.taxa.skew_plotting import _stacked_pair,
# _trend_lines` -- all were used exclusively by this function.
# -----------------------------------------------------------------------------

# class TaxaThreatGapPlotError(ValueError):
#     """Raised when the scatter cannot be drawn as specified."""
#
#
# def plot_regional_representation_and_trend(
#     regional: pd.DataFrame,
#     regional_trend: pd.DataFrame,
#     *,
#     region_order: Iterable[str] = REGION_ORDER,
#     region_colors: Mapping[str, str] | None = None,
#     threat_column: str = "threat_share_pct",
#     evidence_column: str = "evidence_share_pct",
#     segment_label_min_pct: float = 4.0,
#     label_min_gap: float = 9.5,
#     trend_label_min_gap: float = 11.0,
#     manuscript: bool = True,
#     figsize: tuple[float, float] = (7.4, 3.7),
# ) -> plt.Figure:
#     """The geographic mismatch and what happened to it, as its own two-panel figure.
#
#     Panel A stacks each IPBES region's share of threatened land vertebrates against its
#     share of the vertebrate evidence, joined by ribbons. Panel B tracks evidence share by
#     publication year.
#
#     It is built from the taxonomic figure's own ``_stacked_pair`` and ``_trend_lines``
#     and uses the same house palette, so the two figures read as siblings without being
#     crammed into one panel grid. The rhyme carries the argument: two unrelated benchmarks
#     -- GBIF described species there, IUCN threatened species here -- and attention matches
#     neither. Panel B is where the two figures part company: the taxonomic composition
#     barely moved, while the geographic gap narrowed markedly.
#     """
#     region_colors = dict(region_colors or REGION_COLORS)
#     required = {"region", threat_column, evidence_column}
#     missing = required.difference(regional.columns)
#     if missing:
#         raise TaxaThreatGapPlotError(f"Regional frame is missing columns: {sorted(missing)}")
#     trend_missing = {"region", "publication_year", evidence_column}.difference(
#         regional_trend.columns
#     )
#     if trend_missing:
#         raise TaxaThreatGapPlotError(
#             f"Regional trend frame is missing columns: {sorted(trend_missing)}"
#         )
#
#     order = tuple(region for region in region_order if region in set(regional["region"]))
#     if not order:
#         raise TaxaThreatGapPlotError("No configured region appears in the frame.")
#     absent = set(regional["region"]).difference(order)
#     if absent:
#         raise TaxaThreatGapPlotError(f"Regions missing from region_order: {sorted(absent)}")
#
#     table = regional.set_index("region").reindex(order)
#
#     fig, (axis_bars, axis_trend) = plt.subplots(
#         1, 2, figsize=figsize, gridspec_kw={"width_ratios": [1.0, 1.28]}
#     )
#     _stacked_pair(
#         axis_bars,
#         categories=order,
#         left_values=table[threat_column].to_numpy(dtype=float),
#         right_values=table[evidence_column].to_numpy(dtype=float),
#         colors=region_colors,
#         captions=("Threatened\nvertebrates", "Vertebrate\nevidence"),
#         segment_label_min_pct=segment_label_min_pct,
#         label_min_gap=label_min_gap,
#     )
#     top = float(regional_trend[evidence_column].max())
#     _trend_lines(
#         axis_trend,
#         regional_trend,
#         series=order,
#         colors=region_colors,
#         series_col="region",
#         year_col="publication_year",
#         value_col=evidence_column,
#         ylim=(0, max(55.0, top * 1.1)),
#         ylabel="Share of vertebrate evidence %",
#         xlabel="Publication year",
#         label_min_gap=trend_label_min_gap,
#     )
#
#     if manuscript:
#         ink = visualization.BIODIVERSITY["ink"]
#         for label, axis in zip("AB", (axis_bars, axis_trend)):
#             axis.text(
#                 -0.075, 1.02, label, transform=axis.transAxes, fontsize=9,
#                 fontweight="bold", va="bottom", color=ink,
#             )
#         fig.subplots_adjust(left=0.045, right=0.985, top=0.91, bottom=0.135, wspace=0.16)
#     return fig
