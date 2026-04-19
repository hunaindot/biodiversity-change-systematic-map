# consistency-checking

Shared Python helpers for inter-rater agreement and consistency-checking notebooks. Used from Jupyter notebooks (`screening.ipynb`, `coding.ipynb`) to compare a model or human annotator's labels against a reference set.

## Module layout

```
consistency-checking/
├── cc.py             # all public helpers (load, merge, metrics)
├── screening.ipynb   # notebook: screening (single-label) consistency checks
└── coding.ipynb      # notebook: coding (multi-label L1–L6) consistency checks
```

## Public API

### Screening (single-label)

```python
from consistency_checking.cc import load_df, merge_left, limited_metrics, full_metrics
```

| Function | Description |
|---|---|
| `load_df(path, *, sheet, id_col, label_col)` | Load CSV or Excel; returns DataFrame with `_id` and `_label` columns |
| `merge_left(left, right)` | LEFT JOIN on `_id`; produces `y_pred` (left) and `y_true` (right) |
| `limited_metrics(y_true, y_pred)` | For one-sided datasets (all-positive ground truth): agreement, PABAK, recall, FNR |
| `full_metrics(y_true, y_pred)` | For balanced datasets: kappa, confusion matrix, P/R/F1 binary + macro |

### Coding (multi-label)

```python
from consistency_checking.cc import load_coding_df, multilabel_metrics
```

| Function | Description |
|---|---|
| `load_coding_df(path, *, sheet, id_col, label_col)` | Like `load_df` but `_label` is a `frozenset` of normalised strings |
| `multilabel_metrics(y_true, y_pred, special=(...))` | Returns `(summary_df, per_label_df)` with Jaccard, kappa, P/R/F1 (macro/micro/weighted) |

`multilabel_metrics` excludes records symmetrically: a record is dropped from all metrics if the true label **or** the pred label is empty after stripping special values (`"not applicable"`, `"unclear"`). Exclusion counts are always reported in the summary.

## Typical notebook workflow

```python
import sys; sys.path.insert(0, "..")
from consistency_checking.cc import load_df, merge_left, full_metrics

# Load the two annotation sets
human = load_df("path/to/human_labels.xlsx", id_col="UT", label_col="eligibility")
model = load_df("path/to/model_outputs.xlsx", id_col="UT", label_col="eligibility")

# Merge and evaluate
merged = merge_left(model, human)   # model is left (pred), human is right (truth)
display(full_metrics(merged["y_true"], merged["y_pred"]))
```

For multi-label coding tasks:

```python
from consistency_checking.cc import load_coding_df, multilabel_metrics

human  = load_coding_df("human.xlsx",  id_col="UT", label_col="driver")
model  = load_coding_df("model.xlsx",  id_col="UT", label_col="driver")
merged = merge_left(model, human)
summary, per_label = multilabel_metrics(merged["y_true"], merged["y_pred"])
display(summary)
display(per_label)
```
