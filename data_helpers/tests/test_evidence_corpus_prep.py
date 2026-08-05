"""Tests for shared screening and integrated evidence-corpus preparation."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from data_helpers.prep import evidence_corpus_prep as prep
from data_helpers.prep import corpus


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
    )
    assert bundle.screening["UT"].tolist() == ["A", "B", "C", "D"]
    assert bundle.eligible["UT"].tolist() == ["A", "B"]
    assert bundle.manifest["summary"]["eligible_with_unclear_step"] == 1
    assert bundle.manifest["summary"]["eligible_negative"] == 1
    assert bundle.exclusion_overlap["records"].sum() == 2
    assert bundle.exclusion_overlap.iloc[0]["records"] == 1

    store = prep.ScreeningPreparedStore(tmp_path / "prepared")
    paths = store.write(bundle)
    assert {path.name for path in paths} == {
        "screening-publications.parquet",
        "eligible-screening-publications.parquet",
        "screening-exclusion-overlap.csv",
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
            "publication_year": [2000, 2001],
            "s2_dir": ["negative", "mixed"],
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
            "realm": ['["Freshwater"]', '["Terrestrial"]'],
            "pred_methods_data_collection": ['["FieldSurvey"]', '[]'],
            "pred_methods_analysis": ['["DiversityMetrics"]', '[]'],
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
        }
    )
    publications = prep.build_biodiversity_evidence_corpus(merged, taxa)
    assert publications["UT"].tolist() == ["A", "B"]
    assert publications.loc[0, "pred_countries"] == ("USA",)
    assert publications.loc[0, "detail_groups"] == ("Birds",)
    assert publications.loc[0, "class_labels"] == ("Aves",)
    assert "drivers" not in publications

    source = tmp_path / "source.txt"
    source.write_text("source", encoding="utf-8")
    manifest = prep.build_biodiversity_manifest(
        publications,
        sources={"fake": source},
        screening_manifest={
            "schema_version": 1,
            "rows": {"eligible_screening_publications": 2},
        },
        taxa_manifest={
            "schema_version": 1,
            "grouping_rules_sha256": "abc",
        },
    )
    store = prep.BiodiversityEvidenceStore(tmp_path / "corpus")
    paths = store.write(prep.BiodiversityEvidenceBundle(publications, manifest))
    assert {path.name for path in paths} == {
        "biodiversity-evidence-corpus.parquet",
        "manifest.json",
    }
    loaded = store.load()
    assert loaded.publications.loc[0, "pred_countries"] == ("USA",)
    assert loaded.manifest["rows"]["publications"] == 2
