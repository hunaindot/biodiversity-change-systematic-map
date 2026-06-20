from __future__ import annotations

import pandas as pd
from typing import Callable

LabelNormalizer = Callable[[object], set[str]]


def record_confusion(
    df: pd.DataFrame,
    truth_col: str,
    pred_col: str,
    base: str,
    normalizer: LabelNormalizer,
    include_mask: pd.Series | None = None,
) -> pd.DataFrame:
    """Add per-record tp/fp/fn columns.

    include_mask: optional boolean Series aligned to df; rows set to False
    are skipped (metrics columns are left as None for those records).
    """
    if truth_col not in df or pred_col not in df:
        raise KeyError(f"Missing columns: {truth_col} or {pred_col}")

    truth_sets = df[truth_col].apply(normalizer)
    pred_sets = df[pred_col].apply(normalizer)
    mask_values = include_mask.loc[truth_sets.index].values if include_mask is not None else None

    tps, fps, fns = [], [], []
    for idx, (t, p) in enumerate(zip(truth_sets, pred_sets)):
        included = True if mask_values is None else bool(mask_values[idx])
        if not included:
            tp = fp = fn = None
        elif not t:  # skip metrics when truth is empty
            tp = fp = fn = None
        else:
            tp = len(t & p)
            fp = len(p - t)
            fn = len(t - p)
        tps.append(tp)
        fps.append(fp)
        fns.append(fn)

    df[f"{base}_tp"] = tps
    df[f"{base}_fp"] = fps
    df[f"{base}_fn"] = fns
    return df


def _safe_series(values) -> pd.Series:
    if isinstance(values, pd.Series):
        return values
    return pd.Series(values)


def screening_summary_metrics(
    truth,
    pred,
    pos_label: str = "ELIGIBLE",
    neg_label: str = "NOT_ELIGIBLE",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return a screening-only summary plus the binary confusion table.

    The summary is intentionally compact: confusion counts and positive-class
    recall for the ELIGIBLE class. Rows with empty truth labels are excluded.
    """
    truth = _safe_series(truth).fillna("").astype(str)
    pred = _safe_series(pred).fillna("").astype(str)
    mask = truth.str.len() > 0
    truth = truth[mask].reset_index(drop=True)
    pred = pred[mask].reset_index(drop=True)

    labels = [pos_label, neg_label]
    confusion_rows = []
    for actual in labels:
        for predicted in labels:
            count = int(((truth == actual) & (pred == predicted)).sum())
            confusion_rows.append({"actual": actual, "predicted": predicted, "count": count})
    confusion_df = pd.DataFrame(confusion_rows)

    tp = int(((truth == pos_label) & (pred == pos_label)).sum())
    fp = int(((truth != pos_label) & (pred == pos_label)).sum())
    fn = int(((truth == pos_label) & (pred != pos_label)).sum())
    tn = int(((truth == neg_label) & (pred == neg_label)).sum())
    positive_support = int((truth == pos_label).sum())
    scored_rows = int(len(truth))
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    summary_df = pd.DataFrame(
        [
            {
                "positive_label": pos_label,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
                "eligible_recall": recall,
                "positive_support": positive_support,
                "scored_rows": scored_rows,
            }
        ]
    )
    return summary_df, confusion_df


def label_metrics(
    df: pd.DataFrame,
    truth_col: str,
    pred_col: str,
    normalizer: LabelNormalizer,
    include_mask: pd.Series | None = None,
) -> pd.DataFrame:
    """Return per-label precision/recall/F1 plus macro/weighted/micro rows."""
    truth_sets = df[truth_col].apply(normalizer)
    pred_sets = df[pred_col].apply(normalizer)
    # Exclude rows with empty truth from scoring; optionally skip via include_mask
    mask = truth_sets.apply(len) > 0
    if include_mask is not None:
        include_mask = include_mask.loc[truth_sets.index]
        mask = mask & include_mask
    truth_sets = truth_sets[mask]
    pred_sets = pred_sets[mask]
    if truth_sets.empty:
        return pd.DataFrame(columns=["label", "tp", "fp", "fn", "precision", "recall", "f1", "support"])

    labels = sorted(set().union(*truth_sets, *pred_sets))

    rows = []
    for label in labels:
        tp = sum((label in t) and (label in p) for t, p in zip(truth_sets, pred_sets))
        fp = sum((label not in t) and (label in p) for t, p in zip(truth_sets, pred_sets))
        fn = sum((label in t) and (label not in p) for t, p in zip(truth_sets, pred_sets))
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        rows.append(
            {"label": label, "tp": tp, "fp": fp, "fn": fn, "precision": prec, "recall": rec, "f1": f1, "support": tp + fn}
        )

    support_sum = sum(r["support"] for r in rows) or 1
    weighted = {
        "label": "_weighted",
        "tp": None,
        "fp": None,
        "fn": None,
        "precision": sum(r["precision"] * r["support"] for r in rows) / support_sum,
        "recall": sum(r["recall"] * r["support"] for r in rows) / support_sum,
        "f1": sum(r["f1"] * r["support"] for r in rows) / support_sum,
        "support": support_sum,
    }
    macro = {
        "label": "_macro",
        "tp": None,
        "fp": None,
        "fn": None,
        "precision": sum(r["precision"] for r in rows) / len(rows),
        "recall": sum(r["recall"] for r in rows) / len(rows),
        "f1": sum(r["f1"] for r in rows) / len(rows),
        "support": support_sum,
    }
    # micro: sum tp/fp/fn across labels
    tp_sum = sum(r["tp"] for r in rows)
    fp_sum = sum(r["fp"] for r in rows)
    fn_sum = sum(r["fn"] for r in rows)
    micro_precision = tp_sum / (tp_sum + fp_sum) if (tp_sum + fp_sum) else 0.0
    micro_recall = tp_sum / (tp_sum + fn_sum) if (tp_sum + fn_sum) else 0.0
    micro_f1 = 2 * micro_precision * micro_recall / (micro_precision + micro_recall) if (micro_precision + micro_recall) else 0.0
    micro = {
        "label": "_micro",
        "tp": tp_sum,
        "fp": fp_sum,
        "fn": fn_sum,
        "precision": micro_precision,
        "recall": micro_recall,
        "f1": micro_f1,
        "support": support_sum,
    }
    rows.extend([macro, weighted, micro])
    return pd.DataFrame(rows)
