"""Minimal Threat-L0 research-emphasis summaries by ecosystem realm.

Threat-L0 is a parallel descriptive taxonomy attached to the exact publication
universe prepared for the L1 realm analysis. Missing or unusable threat labels
remain in the publication denominator. Geological Events is recognized but
excluded because it was outside the coding scope of this map.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from data_helpers.analysis.realm.driver import (
    ANALYSIS_REALMS,
    DriverRealmError,
    DriverRealmEvidence,
    RealmEvidencePreparation,
)
from data_helpers.labels import parse_list_labels


THREAT_L0_CATEGORIES = (
    "Residential & Commercial Development",
    "Agriculture & Aquaculture",
    "Energy Production & Mining",
    "Transportation & Service Corridors",
    "Biological Resource Use",
    "Human Intrusions & Disturbance",
    "Invasive & Other Problematic Species, Genes & Diseases",
    "Natural System Modifications",
    "Pollution",
    "Climate Change & Severe Weather",
    "Geological Events",
    "Other Options",
    "Unclear",
)
OUT_OF_SCOPE_THREATS = ("Geological Events",)
DEFAULT_ANALYSIS_THREATS = tuple(
    threat
    for threat in THREAT_L0_CATEGORIES
    if threat not in OUT_OF_SCOPE_THREATS
)
DEFAULT_DISPLAY_THREATS = tuple(
    threat
    for threat in DEFAULT_ANALYSIS_THREATS
    if threat not in {"Other Options", "Unclear"}
)
_THREAT_CANONICAL = {
    label.casefold(): label for label in THREAT_L0_CATEGORIES
}


class ThreatRealmError(DriverRealmError):
    """Raised when Threat-L0 inputs violate the realm-analysis contract."""


@dataclass
class ThreatRealmEvidence:
    """One row per publication and its aligned in-scope threat matrix."""

    documents: pd.DataFrame
    threat_matrix: pd.DataFrame
    audit: pd.DataFrame
    unknown_labels: pd.DataFrame
    threat_order: tuple[str, ...] = DEFAULT_ANALYSIS_THREATS
    realm_order: tuple[str, ...] = ANALYSIS_REALMS


def _audit_frame(rows: list[tuple[str, int]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["metric", "value"])


def _validate_threat_order(threat_order: Sequence[str]) -> tuple[str, ...]:
    order = tuple(str(label) for label in threat_order)
    if order != DEFAULT_ANALYSIS_THREATS:
        raise ThreatRealmError(
            "threat_order must match the 12 in-scope Threat-L0 categories."
        )
    return order


def _coerce_primary_documents(
    primary: RealmEvidencePreparation | DriverRealmEvidence | pd.DataFrame,
) -> tuple[pd.DataFrame, tuple[str, ...]]:
    if isinstance(primary, RealmEvidencePreparation):
        source = primary.evidence.documents
        realm_order = primary.evidence.realm_order
    elif isinstance(primary, DriverRealmEvidence):
        source = primary.documents
        realm_order = primary.realm_order
    elif isinstance(primary, pd.DataFrame):
        source = primary
        required = {"UT", "realm"}
        missing = sorted(required.difference(source.columns))
        if missing:
            raise ThreatRealmError(
                f"Primary DataFrame is missing column(s): {missing}"
            )
        observed = set(source["realm"].astype("string").dropna())
        realm_order = tuple(
            realm for realm in ANALYSIS_REALMS if realm in observed
        )
    else:
        raise ThreatRealmError(
            "primary must be RealmEvidencePreparation, DriverRealmEvidence, "
            "or a prepared DataFrame."
        )

    required = {"UT", "realm"}
    missing = sorted(required.difference(source.columns))
    if missing:
        raise ThreatRealmError(
            f"Prepared primary evidence is missing column(s): {missing}"
        )
    documents = source[["UT", "realm"]].copy()
    if documents["UT"].isna().any() or not documents["UT"].is_unique:
        raise ThreatRealmError(
            "Prepared primary evidence must have unique, non-missing UT."
        )
    realm_values = documents["realm"].astype("string")
    invalid = sorted(set(realm_values.dropna()).difference(realm_order))
    if invalid or realm_values.isna().any():
        raise ThreatRealmError(
            "Prepared evidence contains realm label(s) outside its configured "
            f"order: {invalid}"
        )
    documents["realm"] = pd.Categorical(
        realm_values, categories=realm_order, ordered=True
    )
    return documents.reset_index(drop=True), tuple(realm_order)


def _parse_threat_labels(
    value: Any,
    included_order: Sequence[str],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], int]:
    included = set(included_order)
    canonical: list[str] = []
    unknown: list[str] = []
    out_of_scope: list[str] = []
    parsed = parse_list_labels(value)
    for label in parsed:
        resolved = _THREAT_CANONICAL.get(label.casefold())
        if resolved is None:
            if label not in unknown:
                unknown.append(label)
        elif resolved not in included:
            if resolved not in out_of_scope:
                out_of_scope.append(resolved)
        elif resolved not in canonical:
            canonical.append(resolved)
    return (
        tuple(canonical),
        tuple(unknown),
        tuple(out_of_scope),
        len(parsed),
    )


def prepare_threat_realm_evidence(
    primary: RealmEvidencePreparation | DriverRealmEvidence | pd.DataFrame,
    corpus_df: pd.DataFrame,
    *,
    threat_order: Sequence[str] = DEFAULT_ANALYSIS_THREATS,
    threat_column: str = "pred_threat_l0",
) -> ThreatRealmEvidence:
    """Attach in-scope Threat-L0 predictions to the fixed realm denominator."""
    order = _validate_threat_order(threat_order)
    documents, realm_order = _coerce_primary_documents(primary)
    required = {"UT", threat_column}
    missing = sorted(required.difference(corpus_df.columns))
    if missing:
        raise ThreatRealmError(f"Corpus is missing required column(s): {missing}")
    if corpus_df["UT"].isna().any():
        raise ThreatRealmError("The threat corpus contains missing UT values.")
    if not corpus_df["UT"].is_unique:
        raise ThreatRealmError("The threat corpus must be one row per UT.")

    source = corpus_df[["UT", threat_column]].rename(
        columns={threat_column: "_threat_raw"}
    )
    merged = documents.merge(
        source,
        on="UT",
        how="left",
        validate="one_to_one",
        indicator="_corpus_match",
    )
    parsed = merged["_threat_raw"].map(
        lambda value: _parse_threat_labels(value, order)
    )
    merged["threat_labels"] = parsed.map(lambda item: item[0])
    merged["unknown_threat_labels"] = parsed.map(lambda item: item[1])
    merged["out_of_scope_threat_labels"] = parsed.map(lambda item: item[2])
    merged["_n_parsed_labels"] = parsed.map(lambda item: item[3])
    merged["n_threats"] = merged["threat_labels"].map(len).astype(int)

    threat_matrix = pd.DataFrame(
        {
            threat: merged["threat_labels"].map(
                lambda labels: threat in labels
            )
            for threat in order
        },
        dtype=bool,
    )
    documents_out = merged[
        [
            "UT",
            "realm",
            "threat_labels",
            "unknown_threat_labels",
            "out_of_scope_threat_labels",
            "n_threats",
        ]
    ].reset_index(drop=True)

    unknown_long = (
        merged[["UT", "realm", "unknown_threat_labels"]]
        .explode("unknown_threat_labels")
        .dropna(subset=["unknown_threat_labels"])
        .rename(columns={"unknown_threat_labels": "unknown_label"})
    )
    if unknown_long.empty:
        unknown_summary = pd.DataFrame(
            columns=["unknown_label", "n_documents", "realms"]
        )
    else:
        unknown_summary = (
            unknown_long.groupby("unknown_label", observed=True)
            .agg(
                n_documents=("UT", "nunique"),
                realms=(
                    "realm",
                    lambda values: "; ".join(
                        realm
                        for realm in realm_order
                        if realm in set(values.astype("string"))
                    ),
                ),
            )
            .reset_index()
            .sort_values(
                ["n_documents", "unknown_label"],
                ascending=[False, True],
            )
            .reset_index(drop=True)
        )

    matched = merged["_corpus_match"].eq("both")
    empty_raw = merged["_n_parsed_labels"].eq(0)
    has_unknown = merged["unknown_threat_labels"].map(len).gt(0)
    has_out_of_scope = merged["out_of_scope_threat_labels"].map(len).gt(0)
    usable = merged["n_threats"].gt(0)
    audit = _audit_frame(
        [
            ("Primary analysis publications", int(len(merged))),
            ("Publications matched to threat corpus", int(matched.sum())),
            ("Publications absent from threat corpus", int((~matched).sum())),
            ("Publications with an empty threat prediction", int(empty_raw.sum())),
            (
                "Publications carrying an unknown threat label",
                int(has_unknown.sum()),
            ),
            (
                "Publications carrying an out-of-scope threat label",
                int(has_out_of_scope.sum()),
            ),
            (
                "Publications without a usable canonical threat",
                int((~usable).sum()),
            ),
            ("Threat-labelled publications", int(usable.sum())),
            (
                "Multi-threat publications",
                int(merged["n_threats"].gt(1).sum()),
            ),
            (
                "Unique document–threat assignments",
                int(threat_matrix.to_numpy().sum()),
            ),
        ]
    )
    evidence = ThreatRealmEvidence(
        documents=documents_out,
        threat_matrix=threat_matrix,
        audit=audit,
        unknown_labels=unknown_summary,
        threat_order=order,
        realm_order=realm_order,
    )
    _validate_evidence(evidence)
    return evidence


def _validate_evidence(evidence: ThreatRealmEvidence) -> None:
    if len(evidence.documents) != len(evidence.threat_matrix):
        raise ThreatRealmError("Documents and threat_matrix are not row-aligned.")
    if not evidence.documents.index.equals(evidence.threat_matrix.index):
        raise ThreatRealmError("Documents and threat_matrix indices are not aligned.")
    if tuple(evidence.threat_matrix.columns) != evidence.threat_order:
        raise ThreatRealmError("threat_matrix columns do not match threat_order.")
    if evidence.documents["UT"].isna().any() or not evidence.documents["UT"].is_unique:
        raise ThreatRealmError(
            "Prepared threat evidence must contain unique, non-missing UT."
        )
    if not set(
        evidence.documents["realm"].astype("string").dropna()
    ).issubset(evidence.realm_order):
        raise ThreatRealmError(
            "Prepared threat evidence contains a realm outside realm_order."
        )


def threat_realm_counts(evidence: ThreatRealmEvidence) -> pd.DataFrame:
    """Return realm denominators and Threat-L0 label coverage."""
    _validate_evidence(evidence)
    documents = evidence.documents
    rows = []
    for realm in evidence.realm_order:
        mask = documents["realm"].astype("string").eq(realm)
        n_documents = int(mask.sum())
        if n_documents == 0:
            raise ThreatRealmError(
                f"No publications are available for configured realm: {realm}"
            )
        n_labelled = int(documents.loc[mask, "n_threats"].gt(0).sum())
        rows.append(
            {
                "realm": realm,
                "n_documents": n_documents,
                "n_labelled_documents": n_labelled,
                "label_coverage": n_labelled / n_documents,
            }
        )
    return pd.DataFrame(rows)


def threat_realm_summary(evidence: ThreatRealmEvidence) -> pd.DataFrame:
    """Calculate Threat-L0 prevalence, pooled LQ, and fractional composition."""
    _validate_evidence(evidence)
    documents = evidence.documents.reset_index(drop=True)
    matrix = evidence.threat_matrix.astype(float).reset_index(drop=True)
    n_labels = matrix.sum(axis=1).to_numpy(float)
    fractional = pd.DataFrame(
        np.divide(
            matrix.to_numpy(),
            n_labels[:, None],
            out=np.zeros_like(matrix.to_numpy()),
            where=n_labels[:, None] > 0,
        ),
        columns=evidence.threat_order,
    )
    total_documents = len(documents)
    pooled_counts = matrix.sum(axis=0)
    pooled_prevalence = pooled_counts / total_documents

    rows: list[dict[str, Any]] = []
    for realm in evidence.realm_order:
        mask = documents["realm"].astype("string").eq(realm).to_numpy()
        n_documents = int(mask.sum())
        if n_documents == 0:
            raise ThreatRealmError(
                f"No publications are available for configured realm: {realm}"
            )
        realm_matrix = matrix.loc[mask]
        realm_fractional = fractional.loc[mask]
        n_labelled = int(documents.loc[mask, "n_threats"].gt(0).sum())
        label_coverage = n_labelled / n_documents
        attribution_rates = realm_fractional.mean(axis=0)
        rate_total = float(attribution_rates.sum())
        for threat in evidence.threat_order:
            n_threat = int(realm_matrix[threat].sum())
            prevalence = n_threat / n_documents
            pooled = float(pooled_prevalence[threat])
            lq = prevalence / pooled if pooled > 0 else np.nan
            attribution_rate = float(attribution_rates[threat])
            composition = (
                attribution_rate / rate_total if rate_total > 0 else np.nan
            )
            rows.append(
                {
                    "realm": realm,
                    "threat": threat,
                    "n_documents": n_documents,
                    "n_labelled_documents": n_labelled,
                    "label_coverage": label_coverage,
                    "n_threat_documents": n_threat,
                    "prevalence": prevalence,
                    "prevalence_pct": 100 * prevalence,
                    "pooled_prevalence": pooled,
                    "lq": lq,
                    "log2_lq": np.log2(lq) if lq > 0 else -np.inf,
                    "fractional_attribution_rate": attribution_rate,
                    "fractional_composition": composition,
                    "fractional_composition_pct": 100 * composition,
                }
            )
    return pd.DataFrame(rows)


def threat_realm_fractional_composition(
    evidence: ThreatRealmEvidence,
    *,
    threat_order: Sequence[str] = DEFAULT_DISPLAY_THREATS,
) -> pd.DataFrame:
    """Return publication-weighted composition for substantive Threat-L0 labels.

    Each publication carrying at least one selected threat contributes total
    weight one, divided equally across its selected threats. Publications with
    only residual labels do not enter the composition denominator.
    """
    _validate_evidence(evidence)
    order = tuple(str(label) for label in threat_order)
    if (
        len(order) != len(DEFAULT_DISPLAY_THREATS)
        or len(order) != len(set(order))
        or set(order) != set(DEFAULT_DISPLAY_THREATS)
    ):
        raise ThreatRealmError(
            "threat_order must contain the 10 substantive Threat-L0 labels."
        )

    documents = evidence.documents.reset_index(drop=True)
    matrix = evidence.threat_matrix.loc[:, order].astype(float).reset_index(
        drop=True
    )
    n_selected = matrix.sum(axis=1).to_numpy(float)
    usable = n_selected > 0
    fractional = pd.DataFrame(
        np.divide(
            matrix.to_numpy(),
            n_selected[:, None],
            out=np.zeros_like(matrix.to_numpy()),
            where=n_selected[:, None] > 0,
        ),
        columns=order,
    )

    rows: list[dict[str, Any]] = []
    for realm in evidence.realm_order:
        realm_mask = (
            documents["realm"].astype("string").eq(realm).to_numpy()
        )
        composition_mask = realm_mask & usable
        n_documents = int(realm_mask.sum())
        n_composition_documents = int(composition_mask.sum())
        if n_composition_documents == 0:
            raise ThreatRealmError(
                "No publications carry a substantive Threat-L0 label in "
                f"configured realm: {realm}"
            )
        shares = fractional.loc[composition_mask].mean(axis=0)
        for threat in order:
            share = float(shares[threat])
            rows.append(
                {
                    "realm": realm,
                    "threat": threat,
                    "n_documents": n_documents,
                    "n_composition_documents": n_composition_documents,
                    "fractional_composition": share,
                    "fractional_composition_pct": 100 * share,
                }
            )
    return pd.DataFrame(rows)


def conditional_driver_threat_composition(
    driver_evidence: DriverRealmEvidence,
    threat_evidence: ThreatRealmEvidence,
    *,
    driver_to_threats: Mapping[str, Sequence[str]],
    realm_order: Sequence[str],
) -> pd.DataFrame:
    """Resolve each driver into its available directly mapped Threat-L0 mix.

    Within each realm × driver block, publications without a directly mapped
    threat are excluded. A publication carrying multiple mapped threats
    contributes total weight one, divided equally among those threats.
    """
    _validate_evidence(threat_evidence)
    realms = tuple(str(realm) for realm in realm_order)
    if not realms or len(realms) != len(set(realms)):
        raise ThreatRealmError("realm_order must contain unique realm labels.")
    unexpected_realms = sorted(
        set(realms).difference(driver_evidence.realm_order)
    )
    if unexpected_realms:
        raise ThreatRealmError(
            f"realm_order contains unconfigured realms: {unexpected_realms}"
        )
    if not driver_to_threats:
        raise ThreatRealmError("driver_to_threats must not be empty.")
    unexpected_drivers = sorted(
        set(driver_to_threats).difference(driver_evidence.driver_order)
    )
    if unexpected_drivers:
        raise ThreatRealmError(
            "driver_to_threats contains unconfigured drivers: "
            f"{unexpected_drivers}"
        )
    configured_threats = set(threat_evidence.threat_order)
    mapping: dict[str, tuple[str, ...]] = {}
    for driver, labels in driver_to_threats.items():
        threats = tuple(str(label) for label in labels)
        if not threats or len(threats) != len(set(threats)):
            raise ThreatRealmError(
                f"Mapped threats for {driver} must be unique and non-empty."
            )
        unexpected = sorted(set(threats).difference(configured_threats))
        if unexpected:
            raise ThreatRealmError(
                f"Mapped threats for {driver} are not configured: {unexpected}"
            )
        mapping[driver] = threats

    driver_documents = driver_evidence.documents.reset_index(drop=True)
    threat_documents = threat_evidence.documents.reset_index(drop=True)
    if not driver_documents["UT"].equals(threat_documents["UT"]):
        raise ThreatRealmError(
            "Driver and Threat-L0 evidence must contain the same ordered UTs."
        )
    driver_matrix = driver_evidence.driver_matrix.reset_index(drop=True)
    threat_matrix = threat_evidence.threat_matrix.reset_index(drop=True)

    rows: list[dict[str, Any]] = []
    realm_values = driver_documents["realm"].astype("string")
    for realm in realms:
        realm_mask = realm_values.eq(realm).to_numpy()
        for driver, mapped_threats in mapping.items():
            driver_mask = realm_mask & driver_matrix[driver].to_numpy()
            n_driver_documents = int(driver_mask.sum())
            if n_driver_documents == 0:
                raise ThreatRealmError(
                    f"No publications carry {driver} in configured realm {realm}."
                )
            selected = threat_matrix.loc[
                driver_mask, list(mapped_threats)
            ].astype(float)
            n_mapped_per_document = selected.sum(axis=1)
            available = n_mapped_per_document.gt(0)
            n_available_documents = int(available.sum())
            mapped_coverage = n_available_documents / n_driver_documents
            if n_available_documents:
                fractional = selected.loc[available].div(
                    n_mapped_per_document.loc[available],
                    axis=0,
                )
                shares = fractional.mean(axis=0)
            else:
                shares = pd.Series(np.nan, index=mapped_threats)
            for threat in mapped_threats:
                rows.append(
                    {
                        "realm": realm,
                        "driver": driver,
                        "threat": threat,
                        "n_driver_documents": n_driver_documents,
                        "n_available_documents": n_available_documents,
                        "mapped_coverage": mapped_coverage,
                        "conditional_share": float(shares[threat]),
                        "conditional_share_pct": 100 * float(shares[threat]),
                    }
                )
    return pd.DataFrame(rows)


__all__ = [
    "DEFAULT_ANALYSIS_THREATS",
    "DEFAULT_DISPLAY_THREATS",
    "OUT_OF_SCOPE_THREATS",
    "THREAT_L0_CATEGORIES",
    "ThreatRealmError",
    "ThreatRealmEvidence",
    "prepare_threat_realm_evidence",
    "conditional_driver_threat_composition",
    "threat_realm_counts",
    "threat_realm_fractional_composition",
    "threat_realm_summary",
]
