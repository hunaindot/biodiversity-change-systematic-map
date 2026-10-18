"""Tests for the database-ready dataset variant."""

from __future__ import annotations

import pandas as pd
import pytest

from data_helpers.prep import db_dataset_prep as dp

LIST_DEFAULTS = {c: [["x"], ["y"], ["z"]] for c in dp.LIST_COLUMNS}


def _publications() -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "id": [1410940900001, 1498294300001, 1500000000001],
            "UT": ["WOS:1", "WOS:2", "WOS:3"],
            "title": ["a", "b", "c"],
            "locale_coordinates": ['["Not Applicable"]', '["1,2"]', '["Not Applicable"]'],
            "pred_regions_audit": [["a"], ["b"], ["c"]],
            "pred_subregions_audit": [["a"], ["b"], ["c"]],
            "pred_countries_audit": [["a"], ["b"], ["c"]],
            "taxa_record_status": ["resolved"] * 3,
            "text_available": [True] * 3,
            "plastics_mention": [False] * 3,
        }
    )
    for column, values in LIST_DEFAULTS.items():
        frame[column] = values
    frame["pred_countries"] = [["TUR", "fra"], ["Not Applicable"], ["USA", "Not Applicable", "Unclear"]]
    frame["pred_regions"] = [["Americas"], ["Not Applicable"], ["Unclear"]]
    return frame


def _abstracts() -> pd.DataFrame:
    return pd.DataFrame(
        {"id": [0, 0, 0], "UT": ["WOS:3", "WOS:1", "WOS:2"], "abstract": ["c.", "a.", None]}
    )


def test_build_applies_every_transformation() -> None:
    db, audit = dp.build_db_dataset(_publications(), _abstracts())
    assert db["id"].tolist() == [1, 2, 3]
    assert db["UT"].tolist() == ["WOS:1", "WOS:2", "WOS:3"]
    assert not set(dp.DROPPED_COLUMNS) & set(db.columns)
    assert db.columns.tolist().index("abstract") == db.columns.tolist().index("title") + 1
    assert db["abstract"].tolist()[0] == "a." and db["abstract"].isna().tolist() == [False, True, False]
    assert db.loc[0, "pred_countries"] == ["Turkey", "France"]
    assert db.loc[1, "pred_countries"] is None
    assert db.loc[2, "pred_countries"] == ["United States of America", "Not Applicable", "Unclear"]
    assert db.loc[1, "pred_regions"] is None and db.loc[2, "pred_regions"] == ["Unclear"]
    assert db["locale_coordinates"].tolist() == [None, '["1,2"]', None]
    assert audit["n_missing_abstract"] == 1
    assert audit["blanked_cells"]["pred_countries"] == 1


def test_mixed_not_applicable_list_is_not_blanked() -> None:
    db, _ = dp.build_db_dataset(_publications(), _abstracts())
    assert "Not Applicable" in db.loc[2, "pred_countries"]


def test_unconverted_tokens_are_reported() -> None:
    frame = _publications()
    frame.at[0, "pred_countries"] = ["TUR", "POR"]
    _, audit = dp.build_db_dataset(frame, _abstracts())
    tokens = audit["unconverted_country_tokens"].set_index("token")["n_mentions"]
    assert tokens["POR"] == 1


def test_id_is_reissued_last_and_unique() -> None:
    db, _ = dp.build_db_dataset(_publications(), _abstracts())
    assert db["id"].is_unique and db["id"].min() == 1


def test_mismatched_ut_sets_raise() -> None:
    abstracts = _abstracts().iloc[:2]
    with pytest.raises(dp.DbDatasetPrepError):
        dp.build_db_dataset(_publications(), abstracts)


def test_write_round_trips(tmp_path) -> None:
    db, _ = dp.build_db_dataset(_publications(), _abstracts())
    parquet_path, csv_path = dp.write_db_dataset(db, tmp_path)
    reloaded = pd.read_parquet(parquet_path)
    assert reloaded["id"].tolist() == [1, 2, 3]
    assert reloaded.loc[1, "pred_countries"] is None
    csv = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    assert csv.loc[1, "pred_countries"] == "" and csv.loc[0, "pred_regions"] == '["Americas"]'
