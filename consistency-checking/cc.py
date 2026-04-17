"""
Shared helpers for consistency-checking notebooks (screening, coding, …).

Public API
----------
Screening (single-label)
  load_df(path, *, sheet=None, id_col, label_col)
  merge_left(left, right)
  limited_metrics(y_true, y_pred, pos_label="ELIGIBLE")
  full_metrics(y_true, y_pred, pos_label="ELIGIBLE")

Coding (multi-label)
  load_coding_df(path, *, sheet=None, id_col, label_col)
      Like load_df but parses each label column into a frozenset of
      normalised (lowercased, stripped) label strings.
  multilabel_metrics(y_true, y_pred, special=("not applicable", "unclear"))
      Returns (summary_df, per_label_df).
      • Both sides are treated symmetrically: a record is excluded from ALL
        metrics if the true label OR the pred label is empty after stripping
        special values.  Exclusion counts are reported separately in the summary
        as "Records excluded (true)" and "Records excluded (pred)".
      • Per-label precision / recall / F1 are computed only on the evaluated set.
"""

import ast
import re

import pandas as pd
from sklearn.metrics import (
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    jaccard_score,
    precision_score,
    recall_score,
    accuracy_score,
)
from sklearn.preprocessing import MultiLabelBinarizer


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_label(val):
    parsed = ast.literal_eval(str(val))
    return parsed[0] if isinstance(parsed, list) else parsed


def _parse_multilabel(val):
    """Parse a JSON-list label string into a frozenset of normalised strings.

    Normalisation: lowercase + strip.  Handles empty lists and NaN (→ empty
    frozenset).  Both single-quoted and double-quoted JSON are accepted since
    ast.literal_eval handles both.  Truncated list strings missing the closing
    bracket (e.g. ``["Americas"``) are repaired automatically.
    """
    if pd.isna(val):
        return frozenset()
    s = str(val).strip()
    if s.startswith('['):
        # Remove stray non-string characters just before the closing bracket
        # e.g. '["foo":]' → '["foo"]'
        s = re.sub(r'[^"\'a-zA-Z0-9\s()_,\[\]-]+\]$', ']', s)
        # Append missing closing bracket e.g. '["foo"' → '["foo"]'
        if not s.endswith(']'):
            s = s + ']'
    if not s.startswith('['):
        # Plain string (not a list literal) — treat as single label
        return frozenset([s.strip().lower()])
    parsed = ast.literal_eval(s)
    if isinstance(parsed, list):
        return frozenset(item.strip().lower() for item in parsed if isinstance(item, str))
    return frozenset([str(parsed).strip().lower()])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_df(path, *, sheet=None, id_col, label_col):
    """Load a CSV or Excel file and normalise ID / label columns.

    Parameters
    ----------
    path : str or Path
        File path.  ``.csv`` is read with ``pd.read_csv``; anything else with
        ``pd.read_excel``.
    sheet : str, optional
        Sheet name (Excel only).
    id_col : str
        Column that holds the record identifier (e.g. WOS ID).
    label_col : str
        Column that holds the eligibility / coding label.

    Returns
    -------
    DataFrame with extra columns ``_id`` (str) and ``_label`` (parsed str).
    Rows where either column is NaN are dropped.
    """
    if str(path).endswith(".csv"):
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path, sheet_name=sheet if sheet is not None else 0)

    df = df.dropna(subset=[id_col, label_col]).copy()
    df["_id"]    = df[id_col].astype(str)
    df["_label"] = df[label_col].apply(_parse_label)
    return df


def merge_left(left, right):
    """LEFT JOIN *left* onto *right* on ``_id``.

    Rows in *left* that have no match in *right* are silently dropped (and
    counted).  The returned frame contains:

    * ``y_pred`` — label from *left* (the "estimate")
    * ``y_true`` — label from *right* (the "truth")

    All original columns from *left* are preserved.
    """
    merged = (
        left
        .merge(
            right[["_id", "_label"]].rename(columns={"_label": "y_true"}),
            on="_id",
            how="left",
        )
        .dropna(subset=["y_true"])
        .rename(columns={"_label": "y_pred"})
    )
    n_dropped = len(left) - len(merged)
    if n_dropped:
        print(f"  [{n_dropped} left-side rows not found in right — dropped]")
    print(f"  Matched: {len(merged)}")
    return merged


def limited_metrics(y_true, y_pred, pos_label="ELIGIBLE"):
    """Metrics for one-sided datasets (ground truth is all-positive).

    Reports Observed Agreement, PABAK, Recall, False Negative Rate, TP, FN.
    TN / FP are structurally zero and are omitted.
    """
    neg_label = f"NOT_{pos_label}"
    n         = len(y_true)
    cm        = confusion_matrix(y_true, y_pred, labels=[pos_label, neg_label])
    tp, fn    = int(cm[0, 0]), int(cm[0, 1])
    obs       = accuracy_score(y_true, y_pred)
    return pd.DataFrame({
        "Metric": [
            "Records evaluated",
            "Observed Agreement", "PABAK",
            f"Recall ({pos_label})", "False Negative Rate",
            "TP", "FN",
        ],
        "Value": [
            n,
            round(obs, 4), round(2 * obs - 1, 4),
            round(recall_score(y_true, y_pred, pos_label=pos_label), 4),
            round(fn / (tp + fn), 4),
            tp, fn,
        ],
    })


def full_metrics(y_true, y_pred, pos_label="ELIGIBLE"):
    """Full metrics for datasets with both positive and negative examples.

    Reports Observed Agreement, Cohen's Kappa, PABAK, confusion-matrix
    counts, and binary + macro precision / recall / F1.
    """
    neg_label = f"NOT_{pos_label}"
    n         = len(y_true)
    labels    = [pos_label, neg_label]
    cm        = confusion_matrix(y_true, y_pred, labels=labels)
    tp, fn, fp, tn = int(cm[0,0]), int(cm[0,1]), int(cm[1,0]), int(cm[1,1])
    obs   = accuracy_score(y_true, y_pred)
    kappa = cohen_kappa_score(y_true, y_pred)
    return pd.DataFrame({
        "Metric": [
            "Records evaluated",
            "Observed Agreement", "Cohen's Kappa", "PABAK",
            "TP", "FP", "FN", "TN",
            f"Precision ({pos_label})", f"Recall ({pos_label})", f"F1 ({pos_label})",
            "Precision (macro)", "Recall (macro)", "F1 (macro)",
        ],
        "Value": [
            n,
            round(obs, 4), round(kappa, 4), round(2 * obs - 1, 4),
            tp, fp, fn, tn,
            round(precision_score(y_true, y_pred, pos_label=pos_label, average="binary"), 4),
            round(recall_score(y_true, y_pred, pos_label=pos_label, average="binary"), 4),
            round(f1_score(y_true, y_pred, pos_label=pos_label, average="binary"), 4),
            round(precision_score(y_true, y_pred, average="macro"), 4),
            round(recall_score(y_true, y_pred, average="macro"), 4),
            round(f1_score(y_true, y_pred, average="macro"), 4),
        ],
    })


# ---------------------------------------------------------------------------
# Coding: multi-label support
# ---------------------------------------------------------------------------

def load_coding_df(path, *, sheet=None, id_col, label_col):
    """Load a CSV or Excel file and normalise ID / multi-label columns.

    Identical to ``load_df`` except the ``_label`` column contains a
    **frozenset** of normalised (lowercased, stripped) label strings rather
    than a single string.  Rows where ``id_col`` is NaN are dropped; rows
    where ``label_col`` is NaN produce an empty frozenset.
    """
    if str(path).endswith(".csv"):
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path, sheet_name=sheet if sheet is not None else 0)

    df = df.dropna(subset=[id_col]).copy()
    df["_id"]    = df[id_col].astype(str)
    df["_label"] = df[label_col].apply(_parse_multilabel)
    return df


def multilabel_metrics(y_true, y_pred, special=("not applicable", "unclear")):
    """Compute multi-label consistency metrics.

    Parameters
    ----------
    y_true, y_pred : pd.Series of frozensets
        Labels from the truth and estimate sides (output of ``merge_left``).
        Special labels ("not applicable", "unclear") are matched
        case-insensitively and whether stored as a plain string or inside a
        list — ``_parse_multilabel`` normalises both forms to lowercase before
        the frozenset is constructed.
    special : tuple of str
        Label values that indicate an annotation decision rather than a
        content label.  Matched after lowercasing.

    Both sides are treated symmetrically.  A record is excluded from ALL
    metrics when the true label OR the pred label is empty after stripping
    special values.  Exclusion counts are mutually exclusive and always shown:

    * ``Records excluded (true)``  — true was empty/special (unevaluatable).
    * ``Records excluded (pred)``  — pred abstained on an evaluatable record.

    Returns
    -------
    summary : pd.DataFrame
        Aggregate metrics (counts, Jaccard, Kappa, P/R/F1 — macro/micro/weighted).
    per_label : pd.DataFrame
        Per-label TP/FP/FN/TN, Support, Kappa, Precision, Recall, F1.
    """
    special = frozenset(s.strip().lower() for s in special)
    n = len(y_true)

    # --- Strip special labels from both sides ---
    y_true_clean = [s - special for s in y_true]
    y_pred_clean = [s - special for s in y_pred]

    # --- Exclusion counts (mutually exclusive buckets) ---
    # true-empty: record is unevaluatable regardless of pred
    # pred-empty: pred abstained on a record that has a valid true label
    n_excluded_true = sum(1 for s in y_true_clean if not s)
    n_excluded_pred = sum(
        1 for t, p in zip(y_true_clean, y_pred_clean) if t and not p
    )
    n_evaluatable   = n - n_excluded_true          # records with a valid ground truth
    abstention_rate = (
        round(n_excluded_pred / n_evaluatable, 4) if n_evaluatable else float("nan")
    )

    _keep       = [bool(t) and bool(p) for t, p in zip(y_true_clean, y_pred_clean)]
    y_true_eval = [s for s, k in zip(y_true_clean, _keep) if k]
    y_pred_eval = [s for s, k in zip(y_pred_clean, _keep) if k]
    n_eval      = len(y_true_eval)

    exact_matches = sum(t == p for t, p in zip(y_true_eval, y_pred_eval))

    all_labels = sorted(set().union(*y_true_eval, *y_pred_eval))

    if not all_labels:
        summary = pd.DataFrame({
            "Metric": [
                "Records matched",
                "Records excluded (true)",
                "Records excluded (pred)",
                "Abstention rate",
                "Records evaluated",
                "Exact Match Rate",
            ],
            "Value": [
                n, n_excluded_true,
                n_excluded_pred, abstention_rate, n_eval,
                round(exact_matches / n_eval, 4) if n_eval else float("nan"),
            ],
        })
        return summary, pd.DataFrame(columns=["Label", "Support (true)", "Support (pred)",
                                               "TP", "FP", "FN", "TN",
                                               "Kappa", "Precision", "Recall", "F1"])

    mlb    = MultiLabelBinarizer(classes=all_labels)
    Y_true = mlb.fit_transform(y_true_eval)
    Y_pred = mlb.transform(y_pred_eval)

    # --- Per-label Kappa and confusion counts ---
    kappas = []
    tp_list, fp_list, fn_list, tn_list = [], [], [], []
    for i in range(len(all_labels)):
        col_t, col_p = Y_true[:, i], Y_pred[:, i]
        cm_i = confusion_matrix(col_t, col_p, labels=[1, 0])
        tp_list.append(int(cm_i[0, 0]))
        fn_list.append(int(cm_i[0, 1]))
        fp_list.append(int(cm_i[1, 0]))
        tn_list.append(int(cm_i[1, 1]))
        if col_t.sum() == 0 and col_p.sum() == 0:
            k = 1.0   # both sides agree: label never appears
        else:
            try:
                k = cohen_kappa_score(col_t, col_p)
            except Exception:
                k = float("nan")
        kappas.append(k)

    supports_true = [tp + fn for tp, fn in zip(tp_list, fn_list)]
    supports_pred = [tp + fp for tp, fp in zip(tp_list, fp_list)]

    # --- Labels with Support (true) == 0 are pred-only phantom labels.
    #     They are kept in per_label for transparency but excluded from all
    #     aggregate summary metrics (macro/micro/weighted averages and sums). ---
    eval_mask  = [s > 0 for s in supports_true]
    Y_true_ev  = Y_true[:, eval_mask]
    Y_pred_ev  = Y_pred[:, eval_mask]
    kappas_ev  = [k for k, m in zip(kappas,       eval_mask) if m]
    sup_ev     = [s for s, m in zip(supports_true, eval_mask) if m]
    tp_ev      = [v for v, m in zip(tp_list,       eval_mask) if m]
    fp_ev      = [v for v, m in zip(fp_list,       eval_mask) if m]
    fn_ev      = [v for v, m in zip(fn_list,       eval_mask) if m]
    tn_ev      = [v for v, m in zip(tn_list,       eval_mask) if m]

    total_support = sum(sup_ev)

    # --- Kappa: macro, micro, weighted (over supported labels only) ---
    kappa_macro    = sum(k for k in kappas_ev if k == k) / len(kappas_ev) if kappas_ev else float("nan")
    kappa_micro    = cohen_kappa_score(Y_true_ev.flatten(), Y_pred_ev.flatten()) if Y_true_ev.size else float("nan")
    kappa_weighted = (
        sum(k * s for k, s in zip(kappas_ev, sup_ev) if k == k) / total_support
        if total_support else float("nan")
    )

    # --- Aggregate P/R/F1/Jaccard computed from per-label confusion matrix lists.
    #     Using sklearn's metric functions on Y_true_ev is unreliable when
    #     eval_mask selects only 1 label: sklearn's is_multilabel() requires
    #     shape[1] > 1, so a (N, 1) matrix is misclassified as binary and macro
    #     averages are computed over 2 "classes" (0 and 1) rather than 1 label. ---
    def _sdiv(num, den):
        return num / den if den > 0 else 0.0

    n_ev_labels = len(tp_ev)

    prec_ev = [_sdiv(tp, tp + fp)        for tp, fp     in zip(tp_ev, fp_ev)]
    rec_ev  = [_sdiv(tp, tp + fn)        for tp, fn     in zip(tp_ev, fn_ev)]
    f1_ev   = [_sdiv(2 * p * r, p + r)  for p,  r      in zip(prec_ev, rec_ev)]
    jacc_ev = [_sdiv(tp, tp + fp + fn)   for tp, fp, fn in zip(tp_ev, fp_ev, fn_ev)]

    # macro
    prec_macro = sum(prec_ev) / n_ev_labels if n_ev_labels else float("nan")
    rec_macro  = sum(rec_ev)  / n_ev_labels if n_ev_labels else float("nan")
    f1_macro   = sum(f1_ev)   / n_ev_labels if n_ev_labels else float("nan")
    jacc_macro = sum(jacc_ev) / n_ev_labels if n_ev_labels else float("nan")

    # micro
    tp_s = sum(tp_ev); fp_s = sum(fp_ev); fn_s = sum(fn_ev)
    prec_micro = _sdiv(tp_s, tp_s + fp_s)
    rec_micro  = _sdiv(tp_s, tp_s + fn_s)
    f1_micro   = _sdiv(2 * tp_s, 2 * tp_s + fp_s + fn_s)
    jacc_micro = _sdiv(tp_s, tp_s + fp_s + fn_s)

    # weighted (by true support)
    prec_weighted = _sdiv(sum(p * s for p, s in zip(prec_ev, sup_ev)), total_support) if total_support else float("nan")
    rec_weighted  = _sdiv(sum(r * s for r, s in zip(rec_ev,  sup_ev)), total_support) if total_support else float("nan")
    f1_weighted   = _sdiv(sum(f * s for f, s in zip(f1_ev,   sup_ev)), total_support) if total_support else float("nan")
    jacc_weighted = _sdiv(sum(j * s for j, s in zip(jacc_ev, sup_ev)), total_support) if total_support else float("nan")

    def _r(v): return round(v, 4) if v == v else float("nan")  # NaN-safe round

    summary = pd.DataFrame({
        "Metric": [
            "Records matched",
            "Records excluded (true)",
            "Records excluded (pred)",
            "Abstention rate",
            "Records evaluated",
            "Exact Match Rate",
            "Jaccard (macro)",    "Jaccard (micro)",    "Jaccard (weighted)",
            "Kappa (macro)",      "Kappa (micro)",      "Kappa (weighted)",
            "TP (sum)", "FP (sum)", "FN (sum)", "TN (sum)",
            "Precision (macro)",    "Recall (macro)",    "F1 (macro)",
            "Precision (micro)",    "Recall (micro)",    "F1 (micro)",
            "Precision (weighted)", "Recall (weighted)", "F1 (weighted)",
        ],
        "Value": [
            n,
            n_excluded_true,
            n_excluded_pred,
            abstention_rate,
            n_eval,
            round(exact_matches / n_eval, 4),
            _r(jacc_macro),    _r(jacc_micro),    _r(jacc_weighted),
            round(kappa_macro,   4), round(kappa_micro,   4), round(kappa_weighted, 4),
            sum(tp_ev), sum(fp_ev), sum(fn_ev), sum(tn_ev),
            _r(prec_macro),    _r(rec_macro),    _r(f1_macro),
            _r(prec_micro),    _r(rec_micro),    _r(f1_micro),
            _r(prec_weighted), _r(rec_weighted), _r(f1_weighted),
        ],
    })

    # --- Per-label: all labels retained (including pred-only phantoms) ---
    per_label_prec = precision_score(Y_true, Y_pred, average=None, zero_division=0)
    per_label_rec  = recall_score(   Y_true, Y_pred, average=None, zero_division=0)
    per_label_f1   = f1_score(       Y_true, Y_pred, average=None, zero_division=0)

    per_label_jacc = [
        round(_sdiv(tp, tp + fp + fn), 4)
        for tp, fp, fn in zip(tp_list, fp_list, fn_list)
    ]

    per_label = pd.DataFrame({
        "Label":              all_labels,
        "Support (true)":     supports_true,
        "Support (pred)":     supports_pred,
        "TP":                 tp_list,
        "FP":                 fp_list,
        "FN":                 fn_list,
        "TN":                 tn_list,
        "Kappa":              [round(k, 4) for k in kappas],
        "Jaccard Similarity": per_label_jacc,
        "Precision":          per_label_prec.round(4).tolist(),
        "Recall":             per_label_rec.round(4).tolist(),
        "F1":                 per_label_f1.round(4).tolist(),
    })

    return summary, per_label
