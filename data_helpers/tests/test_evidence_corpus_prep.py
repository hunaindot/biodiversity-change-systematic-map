"""Tests for shared screening and integrated evidence-corpus preparation."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from data_helpers.prep import evidence_corpus_prep as prep
from data_helpers.prep import corpus
from data_helpers.prep import taxa_analysis_prep


SCREENING_COLUMNS = [
    "UT",
    "title",
    "authors",
    "abstract",
    "source",
    "publication_year",
    "wos_categories",
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
]


def _screening_frame() -> pd.DataFrame:
    rows = []
    specs = [
        ("A", True, "ELIGIBLE", 1, 1, 1, 1, "negative"),
        ("B", True, "ELIGIBLE", 1, -1, 1, 1, "mixed"),
        ("C", False, "NOT_ELIGIBLE", 0, 1, 1, 1, "negative"),
        ("D", False, "NOT_ELIGIBLE", 0, 0, 1, 1, None),
    ]
    for ut, eligible, label, s1, s2, s3, s4, direction in specs:
        rows.append(
            {
                "UT": ut,
                "title": f"Title {ut}",
                "authors": "Author",
                "abstract": "Abstract",
                "source": "WOS",
                "publication_year": 2000,
                "wos_categories": "Ecology",
                "doi": f"10/example/{ut}",
                "eligibility": label,
                "s1_r": s1,
                "s2_r": s2,
                "s3_r": s3,
                "s4_r": s4,
                "s1_bio": "biodiversity",
                "s2_dir": direction,
                "s3_drivers": "driver",
                "s4_link": "link",
                "is_eligible": eligible,
                "raw_output": "not retained",
            }
        )
    return pd.DataFrame(rows)


def test_screening_preparation_reconciles_both_grains(tmp_path: Path) -> None:
    source = tmp_path / "screening.csv"
    _screening_frame().to_csv(source, index=False)
    bundle = prep.build_screening_preparation(
        source,
        eligible_columns=SCREENING_COLUMNS,
        chunksize=2,
        repository_root=tmp_path,
    )
    assert bundle.screening["UT"].tolist() == ["A", "B", "C", "D"]
    assert bundle.eligible["UT"].tolist() == ["A", "B"]
    assert bundle.manifest["summary"]["eligible_with_unclear_step"] == 1
    assert bundle.manifest["summary"]["eligible_negative"] == 1
    assert bundle.manifest["source"]["path"] == "screening.csv"
    assert bundle.exclusion_overlap["records"].sum() == 2
    assert bundle.exclusion_overlap.iloc[0]["records"] == 1

    store = prep.ScreeningPreparedStore(tmp_path / "prepared")
    paths = store.write(bundle)
    assert {path.name for path in paths} == {
        "screening_publications.parquet",
        "eligible_screening_publications.parquet",
        "screening_exclusion_overlap.csv",
        "manifest.json",
    }
    manifest, overlap = store.load_analysis()
    eligible, _ = store.load_eligible()
    assert manifest["rows"]["screening_publications"] == 4
    assert len(overlap) == 2
    assert eligible["UT"].tolist() == ["A", "B"]
    assert store.remove_eligible_build_cache()
    manifest_after, _ = store.load_analysis()
    assert not store.eligible_path.exists()
    assert manifest_after["consumed_build_cache"]["filename"] == store.eligible_path.name


def test_build_merged_corpus_from_prepared_screening(
    tmp_path: Path, monkeypatch
) -> None:
    eligible = _screening_frame().loc[
        lambda frame: frame["is_eligible"], SCREENING_COLUMNS
    ]
    coding = tmp_path / "driver.csv"
    pd.DataFrame(
        {"UT": ["A", "B"], "driver": ['["Climate Change"]', '["Pollution"]']}
    ).to_csv(coding, index=False)
    monkeypatch.setattr(
        corpus,
        "get_merged_corpus_config",
        lambda: {
            "key_column": "UT",
            "chunksize": 2,
            "screening": {
                "columns": SCREENING_COLUMNS,
                "eligibility_column": "is_eligible",
            },
            "coding_sources": [
                {"name": "driver", "path": coding, "columns": ["driver"]}
            ],
        },
    )
    merged = corpus.build_merged_corpus_from_eligible_screening(eligible)
    assert merged["UT"].tolist() == ["A", "B"]
    assert merged["driver"].tolist() == [
        '["Climate Change"]',
        '["Pollution"]',
    ]


def test_integrated_corpus_normalizes_lists_and_preserves_ut(tmp_path: Path) -> None:
    merged = pd.DataFrame(
        {
            "UT": ["A", "B"],
            "title": ["Title A", "Title B"],
            "authors": ["Author A", "Author B"],
            "abstract": ["Abstract A", "Abstract B"],
            "source": ["WOS", "WOS"],
            "publication_year": [2000, 2001],
            "wos_categories": ["Ecology", "Ecology"],
            "doi": ["10/example/A", "10/example/B"],
            "eligibility": ["ELIGIBLE", "ELIGIBLE"],
            "s1_r": [1, 1],
            "s2_r": [1, 1],
            "s3_r": [1, 1],
            "s4_r": [1, 1],
            "s1_bio": ["biodiversity", "biodiversity"],
            "s2_dir": ["negative", "mixed"],
            "s3_drivers": ["driver", "driver"],
            "s4_link": ["link", "link"],
            "pred_study_design": ["Observational", "Experimental"],
            "driver": ['["Climate Change"]', '["Pollution"]'],
            "pred_threat_l0": [
                '["Climate Change & Severe Weather"]',
                '["Pollution"]',
            ],
            "pred_regions": ['["Americas"]', '[]'],
            "pred_subregions": ['["North America"]', '[]'],
            "pred_countries": ['["USA"]', '[]'],
            "locales": ['["Lake"]', '[]'],
            "locale_coordinates": [None, None],
            "realm": ['["Freshwater"]', '["Terrestrial"]'],
            "pred_methods_data_collection": ['["FieldSurvey"]', '[]'],
            "pred_methods_analysis": ['["DiversityMetrics"]', '[]'],
            "pred_has_comparison": [False, True],
            "pred_comparison_types": ['[]', '["ControlImpact"]'],
        }
    )
    taxa = pd.DataFrame(
        {
            "UT": ["A", "B"],
            "publication_year": pd.Series([2000, 2001], dtype="Int64"),
            "s2_dir": ["negative", "mixed"],
            "pred_study_design": ["Observational", "Experimental"],
            "drivers": [("Climate Change",), ("Pollution",)],
            "threat_l0": [
                ("Climate Change & Severe Weather",),
                ("Pollution",),
            ],
            "realms": [("Freshwater",), ("Terrestrial",)],
            "class_labels": [("Aves",), ("Magnoliopsida",)],
            "broad_groups_all": [("Vertebrates",), ("Plants",)],
            "broad_groups": [("Vertebrates",), ("Plants",)],
            "analysis_groups_all": [("Vertebrates",), ("Vascular plants",)],
            "analysis_groups": [("Vertebrates",), ("Vascular plants",)],
            "detail_groups_all": [("Birds",), ("Vascular plants",)],
            "detail_groups": [("Birds",), ("Vascular plants",)],
            "taxa_record_status": ["resolved", "resolved"],
            "n_llm_taxa": [1, 1],
            "n_taxa_matched": [1, 1],
            "n_taxa_unresolved": [0, 0],
            "n_taxa_api_failed": [0, 0],
            "n_drivers": [1, 1],
            "n_broad_groups": [1, 1],
            "taxa_broad_state": ["resolved", "resolved"],
            "n_analysis_groups": [1, 1],
            "taxa_analysis_state": ["resolved", "resolved"],
            "n_detail_groups": [1, 1],
            "taxa_detail_state": ["resolved", "resolved"],
            "taxa_broad_inclusion_state": [
                "Included: at least one benchmarkable broad group",
                "Included: at least one benchmarkable broad group",
            ],
            "match_status_count__exact": [1, 1],
        }
    )
    rank_values = {
        "taxa_domain_labels": [("Eukaryota",), ("Eukaryota",)],
        "taxa_kingdom_labels": [("Animalia",), ("Plantae",)],
        "taxa_subkingdom_labels": [(), ()],
        "taxa_phylum_labels": [("Chordata",), ("Tracheophyta",)],
        "taxa_class_labels": [("Aves",), ("Magnoliopsida",)],
        "taxa_order_labels": [(), ()],
        "taxa_family_labels": [(), ()],
        "taxa_genus_labels": [(), ()],
        "taxa_species_labels": [(), ()],
    }
    for column, values in rank_values.items():
        taxa[column] = values
    publications, abstracts = prep.build_biodiversity_evidence_corpus(merged, taxa)
    assert publications["UT"].tolist() == ["A", "B"]
    assert publications.loc[0, "pred_countries"] == ("USA",)
    assert publications.loc[0, "taxa_class_labels"] == ("Aves",)
    assert json.loads(publications.loc[0, "taxa_summary_json"])["groups"]["detail"]["included"] == ["Birds"]
    assert abstracts.loc[0, "abstract"] == "Abstract A"
    assert "abstract" not in publications
    assert "wos_categories" not in publications
    assert "drivers" not in publications

    source = tmp_path / "source.txt"
    source.write_text("source", encoding="utf-8")
    manifest = prep.build_biodiversity_manifest(
        publications,
        abstracts,
        sources={"fake": source},
        screening_manifest={
            "schema_version": 1,
            "rows": {"eligible_screening_publications": 2},
        },
        taxa_manifest={
            "schema_version": 3,
            "grouping_rules_sha256": "abc",
            "rows": {"taxa_matches": 2, "taxon_items": 0},
        },
        repository_root=tmp_path,
    )
    store = prep.BiodiversityEvidenceStore(tmp_path / "corpus")
    matches = tmp_path / "taxa_matches.parquet"
    pq.write_table(
        pa.Table.from_arrays(
            [
                pa.array(["A", "B"], type=pa.string()),
                pa.array(
                    [[], []],
                    type=taxa_analysis_prep.TAXA_MATCH_TABLE_SCHEMA.field(
                        "taxa_matches"
                    ).type,
                ),
            ],
            schema=taxa_analysis_prep.TAXA_MATCH_TABLE_SCHEMA,
        ),
        matches,
    )
    paths = store.write(
        prep.BiodiversityEvidenceBuild(publications, abstracts, matches, manifest)
    )
    assert {path.name for path in paths} == {
        "biodiversity_evidence_corpus.parquet",
        "biodiversity_evidence_abstracts.parquet",
        "manifest.json",
    }
    loaded = store.load()
    assert loaded.publications.columns.tolist() == list(prep.EVIDENCE_COLUMNS)
    assert loaded.publications.loc[0, "pred_countries"] == ("USA",)
    assert len(loaded.publications.loc[0, "taxa_matches"]) == 0
    assert loaded.manifest["rows"]["publications"] == 2
    assert loaded.manifest["sources"]["fake"]["path"] == "source.txt"
    assert store.load_abstracts().loc[0, "abstract"] == "Abstract A"


def test_standardize_geography_lists_preserves_grain_and_columns(
    tmp_path: Path,
) -> None:
    mapping_path = tmp_path / "world_bank_mapping.json"
    mapping_path.write_text(
        json.dumps(
            {
                "records": [
                    {"ipbes_iso3": "USA", "has_world_bank_economy": True},
                    {"ipbes_iso3": "CHN", "has_world_bank_economy": True},
                    {"ipbes_iso3": "TWN", "has_world_bank_economy": False},
                ]
            }
        ),
        encoding="utf-8",
    )
    publications = pd.DataFrame(
        {
            "UT": ["A", "B", "C", "D", "E"],
            "pred_regions": [
                (),
                ("Americas", "Unclear"),
                ("Asia and the Pacific",),
                ("Americas",),
                ("All Regions",),
            ],
            "pred_subregions": [
                (),
                ("Unclear", "North America"),
                ("North-East Asia",),
                ("North America",),
                ("All Subregions",),
            ],
            "pred_countries": [
                (),
                ("USA", "Unclear"),
                ("USA", "CHN"),
                ("USA", "TWN"),
                ("Not Applicable",),
            ],
            "unchanged": [1, 2, 3, 4, 5],
        }
    )
    original_columns = publications.columns.tolist()
    original_uts = publications["UT"].copy()

    audit = prep.standardize_geography_lists(
        publications,
        world_bank_mapping_path=mapping_path,
    )

    assert publications.columns.tolist() == original_columns
    assert publications["UT"].equals(original_uts)
    assert len(publications) == 5
    assert publications["pred_regions"].tolist() == [
        ("Not Applicable",),
        ("Unclear",),
        ("Asia and the Pacific",),
        ("Americas",),
        ("All Regions",),
    ]
    assert publications["pred_subregions"].tolist() == [
        ("Not Applicable",),
        ("Unclear",),
        ("North-East Asia",),
        ("North America",),
        ("All Subregions",),
    ]
    assert publications["pred_countries"].tolist() == [
        ("Not Applicable",),
        ("Unclear",),
        ("USA", "CHN"),
        ("Unclear",),
        ("Not Applicable",),
    ]
    assert audit.set_index(["column", "rule"])["changed_values"].to_dict() == {
        ("pred_countries", "contains_unclear_to_unclear"): 1,
        ("pred_countries", "empty_to_not_applicable"): 1,
        ("pred_countries", "non_world_bank_country_to_unclear"): 1,
        ("pred_regions", "contains_unclear_to_unclear"): 1,
        ("pred_regions", "empty_to_not_applicable"): 1,
        ("pred_subregions", "contains_unclear_to_unclear"): 1,
        ("pred_subregions", "empty_to_not_applicable"): 1,
    }
