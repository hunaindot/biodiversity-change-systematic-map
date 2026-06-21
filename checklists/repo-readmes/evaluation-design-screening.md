# Screening Evaluation Notes

- Navigation
  - Scope: screening consistency checks and selected screening eval results
  - Metrics reference: [evaluation-metrics-overview.md](/Users/hunain/d/coding-projects/biodiversity/checklists/repo-readmes/evaluation-metrics-overview.md)
  - `CC1A`: human baseline recall from annotated abstract-only screening labels vs expert full-text labels
  - `CC1B`: LLM screening labels compared against the annotated/reference combined screening set
  - `CC2`: train, dev, and test screening eval runs used for prompt/config selection and final recall reporting

- Primary metric
  `TP / (TP + FN)` where `ELIGIBLE` is the positive class.

- Consistency Checks
  - `CC1`: Compare author-assigned labels based on abstracts only against expert full-text and LLM labels to establish a human recall baseline
    - `A)` What is human baseline recall when comparing author-assigned abstract labels against expert full-text labels? No LLM execution is required here.
    - `B)` How well do LLM screening labels align with the author-assigned abstract labels used in `CC1`?
    - Data: annotated screening sample
    - Data: combined annotated/reference screening set

  - `CC2`: Compare LLM labels against expert full-text labels across train, dev, and test splits of the reference screening dataset

# General Notes

- Status
  `Completed`: Implies that run is executed, data is downloaded, and evals are added

# Execution

## CC1 A

- Notebook: [screening_cc1a_recall.ipynb](/Users/hunain/d/coding-projects/biodiversity/notebooks/screening_cc1a_recall.ipynb)
- Input sources:
  - `data/consistency-check-datasets/screening/annotated_screening_dataset.xlsx` sheet `l0-sample`
  - `data/labels/l0/L0) Screening.csv`
- Current result on the annotated `l0-sample`:
  - `positive_support = 100`
  - `eligible_recall = 83`

## CC1 B

- `Completed` - `python labelling/orchestrator.py data/consistency-check-datasets/screening/combined-train-search l0_cc1_combined_010726_medium_f1 --task screen`

- Result:
  - `tp = 191`
  - `fn = 13`
  - `positive_support = 204`
  - `eligible_recall = 93.63`

## CC2 [Train, Dev, Test]

### Dev sets executed for different reasoning

- `Completed` - `python labelling/orchestrator.py data/labels/l0/dev l0_dev_010726_low_f1 --task screen`
- `Completed` - `python labelling/orchestrator.py data/labels/l0/dev l0_dev_010726_medium_f1 --task screen`
- `Completed` - `python labelling/orchestrator.py data/labels/l0/dev l0_dev_010726_high_f1 --task screen`

#### What performs well in dev?

- Recall for low/medium/high: `88.42 / 90.28 / 90.28`
- Final config = `medium`

### Train set executed - Reasoning = medium

- `Completed` - `python labelling/orchestrator.py data/labels/l0/train l0_train_010726_medium_f1 --task screen`
- Recall = `89.66`

### Test set executed for reasoning with highest recall

- `Completed` - `python labelling/orchestrator.py data/labels/l0/test l0_test_010726_medium_f1 --task screen`
- Recall = `90.45`
