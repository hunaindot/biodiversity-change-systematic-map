from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from data_helpers import corpus
from data_helpers._config import get_merged_corpus_config


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    pd.DataFrame(rows).to_csv(path, index=False)


def _fixture_config(tmp_path: Path) -> dict[str, object]:
    screening_path = tmp_path / "screening.csv"
    driver_path = tmp_path / "driver.csv"
    study_path = tmp_path / "study.csv"

    _write_csv(
        screening_path,
        [
            {"UT": "C", "title": "third", "is_eligible": " yes ", "ignored": "x"},
            {"UT": "A", "title": "first", "is_eligible": "false", "ignored": "x"},
            {"UT": "B", "title": "second", "is_eligible": "1", "ignored": "x"},
            {"UT": "D", "title": "fourth", "is_eligible": "no", "ignored": "x"},
        ],
    )
    _write_csv(
        driver_path,
        [
            {"UT": "B", "driver": "pollution", "ignored": "x"},
            {"UT": "C", "driver": "climate", "ignored": "x"},
        ],
    )
    _write_csv(
        study_path,
        [
            {"UT": "C", "study_design": "observational"},
            {"UT": "B", "study_design": "experimental"},
        ],
    )
    return {
        "key_column": "UT",
        "chunksize": 2,
        "screening": {
            "path": screening_path,
            "eligibility_column": "is_eligible",
            "columns": ["UT", "title"],
        },
        "coding_sources": [
            {"name": "driver", "path": driver_path, "columns": ["driver"]},
            {"name": "study", "path": study_path, "columns": ["study_design"]},
        ],
    }


def test_repo_config_resolves_merged_corpus_paths() -> None:
    config = get_merged_corpus_config()

    screening = config["screening"]
    assert isinstance(screening, dict)
    assert Path(screening["path"]).is_absolute()
    assert screening["columns"][0] == "UT"
    assert [source["name"] for source in config["coding_sources"]] == [
        "driver",
        "threats_l0",
        "geography",
        "ecosystems_realm",
        "study",
    ]


def test_build_merged_corpus_filters_and_preserves_screening_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _fixture_config(tmp_path)
    monkeypatch.setattr(corpus, "get_merged_corpus_config", lambda: config)

    result = corpus.build_merged_corpus()

    assert result.columns.tolist() == ["UT", "title", "driver", "study_design"]
    assert result["UT"].tolist() == ["C", "B"]
    assert result["driver"].tolist() == ["climate", "pollution"]
    assert result["study_design"].tolist() == ["observational", "experimental"]


def test_eligible_mask_supports_boolean_and_normalized_string_values() -> None:
    boolean_mask = corpus._eligible_mask(
        pd.Series([True, False, None], dtype="boolean")
    )
    string_mask = corpus._eligible_mask(
        pd.Series([" TRUE ", "1", "Yes", "false", "", None])
    )

    assert boolean_mask.tolist() == [True, False, False]
    assert string_mask.tolist() == [True, True, True, False, False, False]


def test_build_merged_corpus_rejects_mismatched_source_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _fixture_config(tmp_path)
    driver_path = Path(config["coding_sources"][0]["path"])
    _write_csv(
        driver_path, [{"UT": "C", "driver": "climate"}, {"UT": "X", "driver": "other"}]
    )
    monkeypatch.setattr(corpus, "get_merged_corpus_config", lambda: config)

    with pytest.raises(
        corpus.CorpusMergeError, match=r"left_only': 1, 'right_only': 1"
    ):
        corpus.build_merged_corpus()


def test_build_merged_corpus_rejects_duplicate_source_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _fixture_config(tmp_path)
    driver_path = Path(config["coding_sources"][0]["path"])
    _write_csv(
        driver_path, [{"UT": "C", "driver": "climate"}, {"UT": "C", "driver": "other"}]
    )
    monkeypatch.setattr(corpus, "get_merged_corpus_config", lambda: config)

    with pytest.raises(corpus.CorpusMergeError, match="not one row per UT"):
        corpus.build_merged_corpus()


def test_build_merged_corpus_reports_missing_columns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _fixture_config(tmp_path)
    config["coding_sources"][0]["columns"] = ["missing_driver"]
    monkeypatch.setattr(corpus, "get_merged_corpus_config", lambda: config)

    with pytest.raises(corpus.CorpusMergeError, match="missing_driver"):
        corpus.build_merged_corpus()
