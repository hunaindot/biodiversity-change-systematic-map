"""Focused tests for the minimal Threat-L0 × realm analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data_helpers.analysis.realm import driver as dr
from data_helpers.analysis.realm import threat as tr


AGRICULTURE = "Agriculture & Aquaculture"
BIOLOGICAL = "Biological Resource Use"
NATURAL = "Natural System Modifications"
POLLUTION = "Pollution"
CLIMATE = "Climate Change & Severe Weather"
LAND = "Land/sea use change"


def _driver_record(ut: str, *, realm: str = "Terrestrial") -> dict[str, object]:
    return {
        "UT": ut,
        "s2_dir": "negative",
        "publication_year": 2000,
        "driver": [LAND],
        "realm": [realm],
    }


def _primary(records: list[dict[str, object]]) -> dr.DriverRealmEvidence:
    return dr.prepare_driver_realm_evidence(
        pd.DataFrame(records),
        realm_order=dr.CORE_REALMS,
    )


def _threat_corpus(labels: dict[str, object]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"UT": ut, "pred_threat_l0": value}
            for ut, value in labels.items()
        ]
    )


def _balanced_evidence() -> tr.ThreatRealmEvidence:
    records = [
        _driver_record("T1"),
        _driver_record("T2"),
        _driver_record("F1", realm="Freshwater"),
        _driver_record("F2", realm="Freshwater"),
        _driver_record("M1", realm="Marine"),
        _driver_record("M2", realm="Marine"),
    ]
    threats = {
        "T1": [AGRICULTURE, POLLUTION],
        "T2": [AGRICULTURE],
        "F1": [POLLUTION],
        "F2": [POLLUTION, NATURAL],
        "M1": [BIOLOGICAL, CLIMATE],
        "M2": [BIOLOGICAL],
    }
    return tr.prepare_threat_realm_evidence(
        _primary(records),
        _threat_corpus(threats),
    )


def test_preparation_preserves_denominator_and_audits_bad_labels() -> None:
    primary = _primary(
        [
            _driver_record("T1"),
            _driver_record("T2"),
            _driver_record("F1", realm="Freshwater"),
            _driver_record("M1", realm="Marine"),
        ]
    )
    evidence = tr.prepare_threat_realm_evidence(
        primary,
        _threat_corpus(
            {
                "T1": [AGRICULTURE, POLLUTION, POLLUTION],
                "F1": [],
                "M1": [POLLUTION, "Geological Events", "Invented threat"],
            }
        ),
    )

    assert evidence.documents["UT"].tolist() == ["T1", "T2", "F1", "M1"]
    assert tuple(evidence.threat_matrix.columns) == tr.DEFAULT_ANALYSIS_THREATS
    assert evidence.threat_matrix.to_numpy().sum() == 3
    audit = evidence.audit.set_index("metric")["value"]
    assert audit["Primary analysis publications"] == 4
    assert audit["Publications absent from threat corpus"] == 1
    assert audit["Publications carrying an unknown threat label"] == 1
    assert audit["Publications carrying an out-of-scope threat label"] == 1
    assert evidence.unknown_labels["unknown_label"].tolist() == [
        "Invented threat"
    ]


def test_summary_separates_prevalence_lq_and_fractional_composition() -> None:
    summary = tr.threat_realm_summary(_balanced_evidence()).set_index(
        ["realm", "threat"]
    )
    assert summary.at[
        ("Terrestrial", AGRICULTURE), "prevalence"
    ] == pytest.approx(1)
    assert summary.at[
        ("Terrestrial", AGRICULTURE), "pooled_prevalence"
    ] == pytest.approx(2 / 6)
    assert summary.at[
        ("Terrestrial", AGRICULTURE), "lq"
    ] == pytest.approx(3)
    assert summary.at[
        ("Terrestrial", AGRICULTURE), "fractional_composition"
    ] == pytest.approx(0.75)
    compositions = summary["fractional_composition"].unstack("threat")
    assert np.allclose(compositions.sum(axis=1), 1)


def test_substantive_composition_reweights_each_eligible_publication() -> None:
    evidence = _balanced_evidence()
    composition = tr.threat_realm_fractional_composition(
        evidence,
        threat_order=tr.DEFAULT_DISPLAY_THREATS,
    ).set_index(["realm", "threat"])
    assert composition.at[
        ("Terrestrial", AGRICULTURE), "fractional_composition"
    ] == pytest.approx(0.75)
    shares = composition["fractional_composition"].unstack("threat")
    assert np.allclose(shares.sum(axis=1), 1)


def test_substantive_composition_ignores_residual_only_publications() -> None:
    primary = _primary(
        [
            _driver_record("T1"),
            _driver_record("T2"),
            _driver_record("F1", realm="Freshwater"),
            _driver_record("M1", realm="Marine"),
        ]
    )
    evidence = tr.prepare_threat_realm_evidence(
        primary,
        _threat_corpus(
            {
                "T1": [AGRICULTURE, "Unclear"],
                "T2": ["Unclear"],
                "F1": [POLLUTION],
                "M1": [BIOLOGICAL],
            }
        ),
    )
    composition = tr.threat_realm_fractional_composition(evidence)
    terrestrial = composition.loc[
        composition["realm"].eq("Terrestrial")
    ].set_index("threat")
    assert terrestrial["n_documents"].iloc[0] == 2
    assert terrestrial["n_composition_documents"].iloc[0] == 1
    assert terrestrial.at[
        AGRICULTURE, "fractional_composition"
    ] == pytest.approx(1)


def test_conditional_driver_threat_mix_uses_available_mapped_labels_only() -> None:
    primary = _primary(
        [
            _driver_record("T1"),
            _driver_record("T2"),
            _driver_record("T3"),
            _driver_record("F1", realm="Freshwater"),
            _driver_record("M1", realm="Marine"),
        ]
    )
    threats = tr.prepare_threat_realm_evidence(
        primary,
        _threat_corpus(
            {
                "T1": [AGRICULTURE, POLLUTION, "Unclear"],
                "T2": [AGRICULTURE, NATURAL],
                "T3": ["Unclear"],
                "F1": [AGRICULTURE],
                "M1": [NATURAL],
            }
        ),
    )
    composition = tr.conditional_driver_threat_composition(
        primary,
        threats,
        driver_to_threats={LAND: (AGRICULTURE, NATURAL)},
        realm_order=("Terrestrial",),
    ).set_index("threat")

    assert composition["n_driver_documents"].unique().tolist() == [3]
    assert composition["n_available_documents"].unique().tolist() == [2]
    assert composition["mapped_coverage"].unique().tolist() == pytest.approx(
        [2 / 3]
    )
    assert composition.at[AGRICULTURE, "conditional_share"] == pytest.approx(
        0.75
    )
    assert composition.at[NATURAL, "conditional_share"] == pytest.approx(0.25)
    assert composition["conditional_share"].sum() == pytest.approx(1)


def test_unlabelled_publications_remain_in_prevalence_denominator() -> None:
    primary = _primary(
        [
            _driver_record("T1"),
            _driver_record("T2"),
            _driver_record("F1", realm="Freshwater"),
            _driver_record("M1", realm="Marine"),
        ]
    )
    evidence = tr.prepare_threat_realm_evidence(
        primary,
        _threat_corpus(
            {
                "T1": [AGRICULTURE],
                "T2": [],
                "F1": [POLLUTION],
                "M1": [BIOLOGICAL],
            }
        ),
    )
    agriculture = tr.threat_realm_summary(evidence).loc[
        lambda frame: frame["realm"].eq("Terrestrial")
        & frame["threat"].eq(AGRICULTURE)
    ].iloc[0]
    assert agriculture["n_documents"] == 2
    assert agriculture["n_labelled_documents"] == 1
    assert agriculture["prevalence"] == pytest.approx(0.5)


def test_complete_taxonomy_produces_120_threat_cells() -> None:
    records = [
        _driver_record(f"realm-{index}", realm=realm)
        for index, realm in enumerate(dr.ANALYSIS_REALMS)
    ]
    driver_evidence = dr.prepare_driver_realm_evidence(pd.DataFrame(records))
    threats = {
        record["UT"]: list(tr.DEFAULT_ANALYSIS_THREATS)
        for record in records
    }
    evidence = tr.prepare_threat_realm_evidence(
        driver_evidence,
        _threat_corpus(threats),
    )
    summary = tr.threat_realm_summary(evidence)
    assert len(summary) == (
        len(dr.ANALYSIS_REALMS) * len(tr.DEFAULT_ANALYSIS_THREATS)
    )
    assert len(tr.threat_realm_counts(evidence)) == len(dr.ANALYSIS_REALMS)
