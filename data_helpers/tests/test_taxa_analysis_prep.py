"""Contract tests for the canonical taxa analysis-preparation bundle."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pandas as pd
import pytest

from data_helpers.prep import taxa_analysis_prep
from data_helpers.analysis.taxa import skew as taxa_skew
from data_helpers.analysis.taxa.benchmark import DescribedDiversity


ROOT = Path(__file__).resolve().parents[2]
MAPPING_PATH = ROOT / "checklists" / "mappings" / "taxa_broad_groups.json"
LAND = "Land/sea use change"
CLIMATE = "Climate Change"
THREAT = "Biological Resource Use"


def _corpus() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "UT": ["A", "B", "C", "D"],
            "publication_year": [2000, 2001, 2002, 2003],
            "s2_dir": ["negative"] * 4,
            "driver": [
                json.dumps([LAND, CLIMATE]),
                json.dumps([CLIMATE]),
                json.dumps([LAND]),
                "[]",
            ],
            "pred_threat_l0": [json.dumps([THREAT])] * 4,
            "realm": ['["Terrestrial"]'] * 4,
            "pred_study_design": ["Observational"] * 4,
        }
    )


def _write_taxa(path: Path) -> None:
    def status(name: str, state: str, reason: str) -> str:
        return json.dumps(
            [
                {
                    "canonical_name": name,
                    "status": state,
                    "group_assignments": {"broad": {"reason": reason}},
                }
            ]
        )

    frame = pd.DataFrame(
        {
            "UT": ["A", "B", "C", "D"],
            "class": [
                '["Mammalia", "Insecta"]',
                '["Magnoliopsida"]',
                "[]",
                "[]",
            ],
            "broad_taxa_groups": [
                '["Vertebrates", "Invertebrates"]',
                '["Plants"]',
                '["Unresolved"]',
                "[]",
            ],
            "taxa_analysis_groups": [
                '["Vertebrates", "Arthropods"]',
                '["Vascular plants"]',
                '["Unresolved"]',
                "[]",
            ],
            "taxa_detail_groups": [
                '["Mammals", "Arthropods"]',
                '["Vascular plants"]',
                '["Unresolved"]',
                "[]",
            ],
            "llm_taxa_json": [
                '[{"canonical_name": "Example animal"}]',
                '[{"canonical_name": "Example plant"}]',
                '[{"canonical_name": "Example unresolved"}]',
                '[{"canonical_name": "Not applicable"}]',
            ],
            "taxa_match_status_json": [
                status("Example animal", "exact", "vertebrata"),
                status("Example plant", "fuzzy_accepted", "plantae"),
                status("Example unresolved", "exact", "hierarchy_missing"),
                status("Not applicable", "special_value", "special_value"),
            ],
            "taxa_record_status": [
                "resolved",
                "resolved",
                "unresolved",
                "not_applicable",
            ],
            "n_llm_taxa": [1] * 4,
            "n_taxa_matched": [1, 1, 1, 0],
            "n_taxa_unresolved": [0, 0, 1, 0],
            "n_taxa_api_failed": [0] * 4,
        }
    )
    rank_values = {
        "domain": ['["Eukaryota"]'] * 4,
        "kingdom": ['["Animalia"]', '["Plantae"]', "[]", "[]"],
        "subkingdom": ["[]"] * 4,
        "phylum": ['["Chordata", "Arthropoda"]', '["Tracheophyta"]', "[]", "[]"],
        "order": ['["Primates", "Coleoptera"]', "[]", "[]", "[]"],
        "family": ["[]"] * 4,
        "genus": ["[]"] * 4,
        "species": ["[]"] * 4,
    }
    for column, values in rank_values.items():
        frame[column] = values
    frame.to_csv(path, index=False)


def _write_lineage(path: Path) -> None:
    statuses = ["exact", "fuzzy_accepted", "exact", "special_value"]
    rows = []
    for index, (ut, status) in enumerate(zip(["A", "B", "C", "D"], statuses)):
        resolved = status != "special_value"
        rows.append(
            {
                "UT": ut,
                "llm_taxon_index": 0,
                "llm_canonical_name": f"Taxon {ut}",
                "llm_taxon_rank": "species" if resolved else None,
                "match_status": status,
                "matched_taxon_key": str(index + 1) if resolved else None,
                "matched_name": f"Matched {ut}" if resolved else None,
                "matched_rank": "species" if resolved else None,
                "taxonomic_status": "accepted" if resolved else None,
                "match_type": "exact" if resolved else None,
                "confidence": 1.0 if resolved else None,
                "synonym": False if resolved else None,
                "broad_group": None,
                "broad_group_rule_id": None,
                "broad_group_reason": None,
                "broad_group_eligible": resolved,
                "analysis_group": None,
                "analysis_group_rule_id": None,
                "analysis_group_reason": None,
                "detail_group": None,
                "detail_group_rule_id": None,
                "detail_group_reason": None,
                "error_message": None,
                "lineage_position": 0 if resolved else None,
                "lineage_key": str(index + 1) if resolved else None,
                "lineage_rank": "species" if resolved else None,
                "lineage_name": f"Matched {ut}" if resolved else None,
            }
        )
    pd.DataFrame(rows).to_parquet(path, index=False)


@pytest.fixture()
def prepared(tmp_path: Path):
    mapping = taxa_analysis_prep.load_taxa_mapping(MAPPING_PATH)
    taxa_path = tmp_path / "taxa.csv"
    _write_taxa(taxa_path)
    articles, audits = taxa_analysis_prep.build_taxa_publications(
        _corpus(),
        taxa_path=taxa_path,
        mapping=mapping,
        driver_order=(LAND, CLIMATE),
        threat_order=(THREAT,),
    )
    return mapping, taxa_path, articles, audits


def test_preparation_preserves_grain_and_states(prepared) -> None:
    mapping, _, articles, audits = prepared
    assert articles["UT"].tolist() == ["A", "B", "C", "D"]
    assert articles["UT"].is_unique
    assert articles.loc[0, "drivers"] == (LAND, CLIMATE)
    assert articles.loc[0, "analysis_groups"] == ("Vertebrates", "Arthropods")
    assert articles.loc[0, "class_labels"] == ("Mammalia", "Insecta")
    assert articles.loc[0, "taxa_class_labels"] == ("Mammalia", "Insecta")
    assert articles.loc[0, "taxa_phylum_labels"] == ("Chordata", "Arthropoda")
    assert "taxa_domain_labels" not in articles
    assert "taxa_subkingdom_labels" not in articles
    assert articles.loc[2, "taxa_analysis_state"] == "unresolved_only"
    assert articles["taxa_broad_inclusion_state"].tolist() == [
        taxa_analysis_prep.INCLUSION_ORDER[0],
        taxa_analysis_prep.INCLUSION_ORDER[0],
        taxa_analysis_prep.INCLUSION_ORDER[4],
        taxa_analysis_prep.INCLUSION_ORDER[1],
    ]
    assert articles["match_status_count__exact"].tolist() == [1, 0, 1, 0]
    assert sum(row["taxon_item_count"] for row in audits["match_status"]) == 4
    assert mapping["schema_version"] == 3
    assert mapping["sunburst_clipart"]["Animalia"] == "animal_cat"
    assert set(mapping["sunburst_clipart"].values()).issubset(
        mapping["clipart_assets"]
    )
    assert mapping["sunburst_order_clipart"]["Rodentia"] == "mammal_mouse"
    assert set(mapping["sunburst_order_clipart"].values()).issubset(
        mapping["clipart_assets"]
    )


def test_store_round_trip_is_four_files_and_rejects_stale_rules(
    tmp_path: Path, prepared
) -> None:
    mapping, taxa_path, articles, audits = prepared
    benchmark = DescribedDiversity(
        counts=pd.DataFrame(
                {
                    "broad_group": ["Vertebrates", "Invertebrates", "Plants"],
                    "described_species_count": [10, 80, 10],
                    "described_species_share": [0.1, 0.8, 0.1],
                    "described_species_share_pct": [10.0, 80.0, 10.0],
                }
        ),
        audit=pd.DataFrame([{"stage": "accepted species", "records": 100}]),
    )
    store = taxa_analysis_prep.TaxaPreparedStore(tmp_path / "bundle")
    lineage_path = tmp_path / "lineage.parquet"
    _write_lineage(lineage_path)
    match_summary = store.write_matches(
        lineage_path, expected_uts=articles["UT"]
    )
    manifest = taxa_analysis_prep.build_manifest(
        articles,
        benchmark,
        mapping=mapping,
        audits=audits,
        match_summary=match_summary,
        sources={"taxa": taxa_path, "lineage": lineage_path},
        repository_root=tmp_path,
    )
    paths = store.write(
        taxa_analysis_prep.TaxaPreparedBundle(articles, benchmark, manifest)
    )
    assert {path.name for path in paths} == {
        "taxa_publications.parquet",
        "taxa_matches.parquet",
        "gbif_broad_benchmark.csv",
        "manifest.json",
    }
    assert {path.name for path in store.root.iterdir()} == {path.name for path in paths}
    assert manifest["sources"]["taxa"]["path"] == "taxa.csv"
    assert manifest["sources"]["lineage"]["path"] == "lineage.parquet"

    loaded = store.load(mapping=mapping)
    assert loaded.articles.loc[0, "broad_groups"] == (
        "Vertebrates",
        "Invertebrates",
    )
    assert loaded.benchmark.counts["described_species_count"].sum() == 100
    assert loaded.manifest["taxa_matches_audit"]["taxon_items"] == 4

    changed = copy.deepcopy(mapping)
    changed["schemes"]["broad"]["rules"][0]["group"] = "Other"
    with pytest.raises(taxa_analysis_prep.TaxaAnalysisPrepError, match="stale"):
        store.load(mapping=changed)


def test_vector_one_adapter_preserves_article_balanced_attribution(prepared) -> None:
    _, _, articles, audits = prepared
    evidence = taxa_skew.prepare_taxa_skew_from_prepared(
        articles,
        benchmark_groups=(
            "Vertebrates",
            "Invertebrates",
            "Plants",
            "Fungi",
            "Other",
        ),
        unresolved_group="Unresolved",
        match_status_audit=pd.DataFrame(audits["match_status"]),
        group_reason_audit=pd.DataFrame(audits["broad_group_reason"]),
        special_value_audit=pd.DataFrame(audits["special_value"]),
        auxiliary_label_audit=pd.DataFrame(audits["auxiliary_labels"]),
    )
    assert evidence.included["UT"].tolist() == ["A", "B"]
    assert evidence.attributions.groupby("UT")[
        "fractional_publication_weight"
    ].sum().eq(1).all()
    assert evidence.inclusion_audit["n_publications"].sum() == 4
