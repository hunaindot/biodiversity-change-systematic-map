"""Load and validate shared configuration for results notebooks."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DEFAULT_RESULTS_CONFIG_PATH = (
    Path(__file__).resolve().parents[1]
    / "checklists"
    / "mappings"
    / "results_config.json"
)
HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def load_results_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load the shared results configuration and validate reusable semantics."""
    config_path = Path(path) if path is not None else DEFAULT_RESULTS_CONFIG_PATH
    with config_path.open(encoding="utf-8") as handle:
        config = json.load(handle)

    if config.get("schema_version") != 1:
        raise ValueError("results_config.json must use schema_version 1.")

    categories = config.get("threat_l0", {}).get("categories", [])
    if not categories:
        raise ValueError("results_config.json has no threat_l0 categories.")
    labels = [entry.get("label") for entry in categories]
    if any(not label for label in labels) or len(labels) != len(set(labels)):
        raise ValueError("Threat labels must be non-empty and unique.")
    for entry in categories:
        if not entry.get("display_name"):
            raise ValueError(f"Missing display_name for threat: {entry['label']}")
        if not HEX_COLOR.fullmatch(str(entry.get("color", ""))):
            raise ValueError(f"Invalid color for threat: {entry['label']}")
        if not entry.get("code") or not entry.get("family"):
            raise ValueError(f"Missing code/family for threat: {entry['label']}")
        if not HEX_COLOR.fullmatch(str(entry.get("stack_sort_color", ""))):
            raise ValueError(
                f"Invalid stack_sort_color for threat: {entry['label']}"
            )
    stack_order = config["threat_l0"].get("stack_order", [])
    if len(stack_order) != len(set(stack_order)):
        raise ValueError("Threat stack_order must not contain duplicates.")
    if set(stack_order) != set(labels):
        raise ValueError("Threat stack_order must cover every configured threat.")

    driver_categories = config.get("driver_l1", {}).get("categories", [])
    if not driver_categories:
        raise ValueError("results_config.json has no driver_l1 categories.")
    driver_labels = [entry.get("label") for entry in driver_categories]
    if any(not label for label in driver_labels) or len(driver_labels) != len(
        set(driver_labels)
    ):
        raise ValueError("Driver labels must be non-empty and unique.")
    for entry in driver_categories:
        if not entry.get("display_name"):
            raise ValueError(f"Missing display_name for driver: {entry['label']}")
        if not HEX_COLOR.fullmatch(str(entry.get("color", ""))):
            raise ValueError(f"Invalid color for driver: {entry['label']}")
    driver_stack_order = config["driver_l1"].get("stack_order", [])
    if len(driver_stack_order) != len(set(driver_stack_order)):
        raise ValueError("Driver stack_order must not contain duplicates.")
    if set(driver_stack_order) != set(driver_labels):
        raise ValueError("Driver stack_order must cover every configured driver.")

    income = config.get("world_bank_income", {})
    for key in ["world_bank_mapping", "world_bank_snapshot_curated"]:
        if not income.get(key):
            raise ValueError(f"Missing world_bank_income setting: {key}")
    group_order = income.get("group_order", [])
    tier_order = income.get("tier_order", [])
    tiers = income.get("tiers", {})
    if not group_order or len(group_order) != len(set(group_order)):
        raise ValueError("Income groups must be non-empty and unique.")
    if set(tier_order) != set(tiers):
        raise ValueError("Income tier_order and tiers keys must match.")
    tier_members = [group for tier in tier_order for group in tiers[tier]]
    if len(tier_members) != len(set(tier_members)):
        raise ValueError("An income group cannot belong to more than one tier.")
    if set(tier_members) != set(group_order):
        raise ValueError("Income tiers must cover every configured income group.")

    screening_prep = config.get("screening_analysis_prep", {})
    for key in [
        "screening_source",
        "corpus_config",
        "chunksize",
        "output_directory",
    ]:
        if screening_prep.get(key) in (None, "", [], {}):
            raise ValueError(f"Missing screening_analysis_prep setting: {key}")
    if screening_prep["chunksize"] <= 0:
        raise ValueError("screening_analysis_prep chunksize must be positive.")

    evidence_prep = config.get("biodiversity_evidence_prep", {})
    if not evidence_prep.get("output_directory"):
        raise ValueError(
            "Missing biodiversity_evidence_prep setting: output_directory"
        )
    if not isinstance(evidence_prep.get("retain_eligible_build_cache"), bool):
        raise ValueError(
            "biodiversity_evidence_prep retain_eligible_build_cache must be boolean."
        )

    screening_results = config.get("screening_results", {})
    for key in ["output_directory", "figure_filename"]:
        if not screening_results.get(key):
            raise ValueError(f"Missing screening_results setting: {key}")

    climate = config.get("climate_data_prep", {})
    if climate.get("threat_label") not in labels:
        raise ValueError("Climate-data threat_label must be a configured threat.")
    for key in [
        "direction",
        "study_design",
        "output_directory",
        "country_export",
        "timeseries_export",
    ]:
        if not climate.get(key):
            raise ValueError(f"Missing climate_data_prep setting: {key}")

    climate_analysis = config.get("climate_change_analysis", {})
    for key in [
        "co2_per_capita_indicator",
        "co2_expected_latest_year",
        "focal_quadrant",
        "output_directory",
        "figure_subdirectory",
        "figure_filename",
    ]:
        if not climate_analysis.get(key):
            raise ValueError(f"Missing climate_change_analysis setting: {key}")

    driver = config.get("driver_composition", {})
    for key in [
        "direction",
        "sensitivity_study_design",
        "primary_start_year",
        "primary_end_year",
        "partial_end_year",
        "historical_classifications_file",
        "output_directory",
        "unchecked_output_directory",
        "data_subdirectory",
        "table_subdirectory",
        "figure_subdirectory",
        "composition_figure_filename",
        "classified_assignments_file",
        "threat_attributions_file",
        "bootstrap_replicates",
        "random_seed",
        "publication_periods",
        "focus_threats",
        "contrast_plot_excluded_threats",
    ]:
        if driver.get(key) in (None, "", [], {}):
            raise ValueError(f"Missing driver_composition setting: {key}")
    if driver["primary_start_year"] >= driver["primary_end_year"]:
        raise ValueError("Driver-composition primary years are invalid.")
    if driver["partial_end_year"] < driver["primary_end_year"]:
        raise ValueError("Driver-composition partial year precedes the primary end.")
    periods = driver["publication_periods"]
    if periods[0]["start_year"] != driver["primary_start_year"]:
        raise ValueError("Driver-composition periods must start at the primary year.")
    if periods[-1]["end_year"] != driver["primary_end_year"]:
        raise ValueError("Driver-composition periods must end at the primary year.")
    for previous, current in zip(periods, periods[1:]):
        if previous["end_year"] + 1 != current["start_year"]:
            raise ValueError("Driver-composition periods must be contiguous.")
    if not set(driver["focus_threats"]).issubset(labels):
        raise ValueError("Driver-composition focus threats must be configured threats.")
    if not set(driver["contrast_plot_excluded_threats"]).issubset(labels):
        raise ValueError(
            "Driver-composition plot exclusions must be configured threats."
        )
    if driver["output_directory"] == driver["unchecked_output_directory"]:
        raise ValueError(
            "Driver-composition unchecked outputs need their own directory."
        )
    realm = config.get("driver_realm", {})
    for key in [
        "direction",
        "primary_start_year",
        "primary_end_year",
        "core_realms",
        "analysis_realms",
        "realm_display_names",
        "realm_short_names",
        "output_directory",
        "figure_subdirectory",
        "lq_plot_cap",
        "l1_all_realm_bar_figure_filename",
        "l1_core_realm_bar_figure_filename",
        "l1_core_nested_figure_filename",
        "pollution_nameability_figure_filename",
    ]:
        if realm.get(key) in (None, "", [], {}):
            raise ValueError(f"Missing driver_realm setting: {key}")
    if realm["primary_start_year"] >= realm["primary_end_year"]:
        raise ValueError("Driver-realm primary years are invalid.")
    core_realms = realm["core_realms"]
    analysis_realms = realm["analysis_realms"]
    expected_analysis_realms = [
        "Terrestrial",
        "Subterranean",
        "Subterranean-Freshwater",
        "Subterranean-Marine",
        "Freshwater-Terrestrial",
        "Freshwater",
        "Freshwater-Marine",
        "Marine",
        "Marine-Terrestrial",
        "Marine-Freshwater-Terrestrial",
    ]
    expected_transition_realms = {
        "Subterranean-Freshwater",
        "Subterranean-Marine",
        "Freshwater-Terrestrial",
        "Freshwater-Marine",
        "Marine-Terrestrial",
        "Marine-Freshwater-Terrestrial",
    }
    for label, values in [
        ("core", core_realms),
        ("analysis", analysis_realms),
    ]:
        if len(values) != len(set(values)):
            raise ValueError(
                f"Driver-realm {label} realm labels must be unique."
            )
    if core_realms != ["Terrestrial", "Freshwater", "Marine"]:
        raise ValueError(
            "Driver-realm core realms must be terrestrial/freshwater/marine."
        )
    if analysis_realms != expected_analysis_realms:
        raise ValueError(
            "Driver-realm analysis_realms must match the ordered ecological "
            "L4 taxonomy."
        )
    if (
        set(core_realms)
        | expected_transition_realms
        | {"Subterranean"}
        != set(analysis_realms)
    ):
        raise ValueError(
            "Core, Subterranean, and transition realms must cover all "
            "analysis realms."
        )
    for mapping_key in ["realm_display_names", "realm_short_names"]:
        mapping = realm[mapping_key]
        if set(mapping) != set(analysis_realms) or any(
            not isinstance(value, str) or not value.strip()
            for value in mapping.values()
        ):
            raise ValueError(
                f"Driver-realm {mapping_key} must provide every analysis realm."
            )
    if not 0 < realm["lq_plot_cap"]:
        raise ValueError("Driver-realm lq_plot_cap must be positive.")

    threat_realm = config.get("threat_realm", {})
    for key in [
        "label_column",
        "figure_threats",
        "out_of_scope_threats",
        "lq_plot_cap",
        "figure_filename",
    ]:
        if threat_realm.get(key) in (None, "", [], {}):
            raise ValueError(f"Missing threat_realm setting: {key}")
    figure_threats = threat_realm["figure_threats"]
    out_of_scope_threats = threat_realm["out_of_scope_threats"]
    if len(figure_threats) != len(set(figure_threats)):
        raise ValueError("Threat-realm figure threats must be unique.")
    if len(out_of_scope_threats) != len(set(out_of_scope_threats)):
        raise ValueError("Threat-realm out-of-scope threats must be unique.")
    if set(figure_threats) & set(out_of_scope_threats):
        raise ValueError(
            "Threat-realm figure and out-of-scope threats must be disjoint."
        )
    if not set(figure_threats) <= set(labels):
        raise ValueError("Threat-realm figure threats must be configured threats.")
    if not set(out_of_scope_threats) <= set(labels):
        raise ValueError(
            "Threat-realm out-of-scope threats must be configured threats."
        )
    if not 0 < threat_realm["lq_plot_cap"]:
        raise ValueError("Threat-realm lq_plot_cap must be positive.")

    taxa_prep = config.get("taxa_analysis_prep", {})
    for key in [
        "taxa_source",
        "taxa_lineage_source",
        "gbif_source",
        "gbif_eml_source",
        "taxa_group_mapping",
        "corpus_config",
        "output_directory",
    ]:
        if taxa_prep.get(key) in (None, "", [], {}):
            raise ValueError(f"Missing taxa_analysis_prep setting: {key}")

    lens = config.get("taxonomic_lens", {})
    for key in [
        "direction",
        "primary_start_year",
        "primary_end_year",
        "output_directory",
        "table_subdirectory",
        "figure_subdirectory",
        "artifact_prefix",
        "bootstrap_replicates",
        "random_seed",
        "benchmark_groups",
        "unresolved_group",
        "combined_figure_filename",
        "benchmark_group_stack_order",
        "trend_residual_group",
        "geography_source",
        "geography_min_support",
        "geography_eb_kappa",
        "threat_gap_group",
        "threat_gap_source",
    ]:
        if lens.get(key) in (None, "", [], {}):
            raise ValueError(f"Missing taxonomic_lens setting: {key}")
    if lens["primary_start_year"] >= lens["primary_end_year"]:
        raise ValueError("Taxonomic-lens primary years are invalid.")
    if lens["bootstrap_replicates"] <= 0:
        raise ValueError("Taxonomic-lens bootstrap_replicates must be positive.")
    if sorted(lens["benchmark_group_stack_order"]) != sorted(lens["benchmark_groups"]):
        raise ValueError(
            "Taxonomic-lens benchmark_group_stack_order must be a permutation of "
            "benchmark_groups; the stacked bars and the comparison table share a scheme."
        )
    if lens["trend_residual_group"] not in lens["benchmark_groups"]:
        raise ValueError("Taxonomic-lens trend_residual_group is not a benchmark group.")
    if lens["geography_min_support"] <= 0:
        raise ValueError("Taxonomic-lens geography_min_support must be positive.")
    if lens["threat_gap_group"] not in lens["benchmark_groups"]:
        raise ValueError("Taxonomic-lens threat_gap_group is not a benchmark group.")

    geography_attention = config.get("geography_attention", {})
    for key in [
        "direction",
        "primary_start_year",
        "primary_end_year",
        "low_evidence_threshold",
        "low_attention_threshold_pct",
        "highlight_attention_threshold_pct",
        "output_directory",
        "data_subdirectory",
        "table_subdirectory",
        "figure_subdirectory",
        "assignments_file",
        "country_attention_file",
        "hierarchy_attention_file",
        "coverage_file",
        "coverage_reasons_file",
        "status_by_region_file",
        "gap_inventory_file",
        "audit_file",
        "unresolved_tokens_file",
        "excluded_publications_file",
        "manifest_filename",
        "reference_figure_filename",
        "clockwise_start_angle",
        "region_ordering",
        "country_ordering",
        "visual_levels",
        "region_order",
        "region_colors",
    ]:
        if geography_attention.get(key) in (None, "", [], {}):
            raise ValueError(f"Missing geography_attention setting: {key}")
    integer_settings = (
        "primary_start_year",
        "primary_end_year",
        "low_evidence_threshold",
        "clockwise_start_angle",
    )
    if any(
        not isinstance(geography_attention[key], int)
        or isinstance(geography_attention[key], bool)
        for key in integer_settings
    ):
        raise ValueError(
            "Geography-attention years, threshold, and start angle must be integers."
        )
    if (
        geography_attention["primary_start_year"]
        > geography_attention["primary_end_year"]
    ):
        raise ValueError("Geography-attention primary years are invalid.")
    if geography_attention["low_evidence_threshold"] <= 1:
        raise ValueError(
            "Geography-attention low_evidence_threshold must exceed one."
        )
    low_attention_threshold = geography_attention["low_attention_threshold_pct"]
    if (
        not isinstance(low_attention_threshold, (int, float))
        or isinstance(low_attention_threshold, bool)
        or not 0 < low_attention_threshold <= 100
    ):
        raise ValueError(
            "Geography-attention low_attention_threshold_pct must be in (0, 100]."
        )
    highlight_attention_threshold = geography_attention[
        "highlight_attention_threshold_pct"
    ]
    if (
        not isinstance(highlight_attention_threshold, (int, float))
        or isinstance(highlight_attention_threshold, bool)
        or not 0 <= highlight_attention_threshold <= 100
    ):
        raise ValueError(
            "Geography-attention highlight_attention_threshold_pct must be in [0, 100]."
        )
    if not 0 <= geography_attention["clockwise_start_angle"] < 360:
        raise ValueError(
            "Geography-attention clockwise_start_angle must be in [0, 360)."
        )
    if (
        geography_attention["region_ordering"]
        != "fractional_attention_descending"
    ):
        raise ValueError(
            "Geography-attention region_ordering must be "
            "fractional_attention_descending."
        )
    if (
        geography_attention["country_ordering"]
        != "positive_fractional_attention_descending_then_zero_then_no_key"
    ):
        raise ValueError(
            "Geography-attention country_ordering is unsupported."
        )
    if geography_attention["visual_levels"] != ["region", "country"]:
        raise ValueError(
            "Geography-attention visual_levels must be ['region', 'country']."
        )
    attention_regions = geography_attention["region_order"]
    if len(attention_regions) != len(set(attention_regions)):
        raise ValueError("Geography-attention region_order must be unique.")
    if set(geography_attention["region_colors"]) != set(attention_regions):
        raise ValueError(
            "Geography-attention region_colors must cover region_order."
        )
    for region, color in geography_attention["region_colors"].items():
        if not HEX_COLOR.fullmatch(str(color)):
            raise ValueError(
                f"Invalid geography-attention color for region: {region}"
            )

    temporal = config.get("temporal_development", {})
    for key in [
        "output_directory",
        "table_subdirectory",
        "figure_subdirectory",
        "combined_figure_filename",
    ]:
        if temporal.get(key) in (None, "", [], {}):
            raise ValueError(f"Missing temporal_development setting: {key}")
    start_year = temporal.get("analysis_start_year")
    end_year = temporal.get("analysis_end_year")
    if not isinstance(start_year, int) or not isinstance(end_year, int):
        raise ValueError("Temporal analysis years must be integers.")
    if start_year >= end_year:
        raise ValueError("Temporal analysis_start_year must precede end_year.")
    if temporal.get("focal_threat") not in labels:
        raise ValueError("Temporal focal_threat must be a configured threat.")
    temporal_order = temporal.get("threat_order", [])
    if len(temporal_order) != len(set(temporal_order)):
        raise ValueError("Temporal threat_order must not contain duplicates.")
    if set(temporal_order) != set(labels):
        raise ValueError("Temporal threat_order must cover every configured threat.")
    if not set(temporal.get("growth_plot_excluded_threats", [])).issubset(labels):
        raise ValueError("Temporal plot exclusions must be configured threats.")
    for period in temporal.get("cagr_periods", []):
        if period["base_year"] >= period["end_year"]:
            raise ValueError(f"Invalid CAGR period: {period['label']}")

    return config


def threat_l0_display(
    config: dict[str, Any],
) -> tuple[list[str], dict[str, str], dict[str, str]]:
    """Return canonical threat order, colors, and display names."""
    categories = config["threat_l0"]["categories"]
    order = [entry["label"] for entry in categories]
    colors = {entry["label"]: entry["color"] for entry in categories}
    display_names = {
        entry["label"]: entry["display_name"] for entry in categories
    }
    return order, colors, display_names


def threat_l0_temporal_display(
    config: dict[str, Any],
) -> tuple[
    dict[str, str],
    dict[str, str],
    dict[str, str],
]:
    """Return temporal-analysis codes, families, and stack-sort colors."""
    categories = config["threat_l0"]["categories"]
    codes = {entry["label"]: entry["code"] for entry in categories}
    families = {entry["label"]: entry["family"] for entry in categories}
    sort_colors = {
        entry["label"]: entry["stack_sort_color"] for entry in categories
    }
    return codes, families, sort_colors


def threat_l0_stack_order(config: dict[str, Any]) -> list[str]:
    """Return the canonical bottom-to-top threat stack and legend order."""
    return list(config["threat_l0"]["stack_order"])


def driver_l1_display(
    config: dict[str, Any],
) -> tuple[list[str], dict[str, str], dict[str, str]]:
    """Return canonical driver order, colors, and display names."""
    categories = config["driver_l1"]["categories"]
    order = [entry["label"] for entry in categories]
    colors = {entry["label"]: entry["color"] for entry in categories}
    display_names = {
        entry["label"]: entry["display_name"] for entry in categories
    }
    return order, colors, display_names


def driver_l1_stack_order(config: dict[str, Any]) -> list[str]:
    """Return the canonical bottom-to-top direct-driver stack order."""
    return list(config["driver_l1"]["stack_order"])
