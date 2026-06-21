# Screening Evaluation Notes

- Primary metric = Recall
  `TP / (TP + FN)` where `ELIGIBLE` is the positive class.

- CC1 = Compare author-assigned labels based on abstracts only against expert full-text and LLM labels to establish a human recall baseline
  - A) What is human baseline recall when comparing author-assigned abstract labels against expert full-text labels? No LLM execution is required here.
    - Data: annotated screening sample
  - B) How well do LLM screening labels align with the author-assigned abstract labels used in CC1?
    - Data: combined annotated/reference screening set

- CC2 = Compare LLM labels against expert full-text labels across train, dev, and test splits of the reference screening dataset

# General notes

- For metric definitions, formulas, aggregation behavior, and eval output files, see [evaluation-metrics-overview.md](/Users/hunain/d/coding-projects/biodiversity/checklists/repo-readmes/evaluation-metrics-overview.md)
- Status
  [Completed]: Implies that run is run is executed, data is download, and evals are added

# Execution

## CC1 A

## CC1 B

[Completed] python labelling/orchestrator.py data/consistency-check-datasets/screening/combined-train-search l0_cc1_combined_010726_medium_f1 --task screen

## CC2 [Train, Dev, Test] Commands to reproduce

### Dev sets executed for different reasoning [low, medium, high] (In order)

[Completed] python labelling/orchestrator.py data/labels/l0/dev l0_dev_010726_low_f1 --task screen
[Completed] python labelling/orchestrator.py data/labels/l0/dev l0_dev_010726_medium_f1 --task screen
[Completed] python labelling/orchestrator.py data/labels/l0/dev l0_dev_010726_high_f1 --task screen

#### What performs well in dev?

Recall for low/medium/high: 88.42/ 90.28/ 90.28
final config = [medium]

### Train set executed - Reasoning = medium

[Completed] python labelling/orchestrator.py data/labels/l0/train l0_train_010726_medium_f1 --task screen
Recall = 89.66

### Test set executed for reasoning with highest recall

[Completed] python labelling/orchestrator.py data/labels/l0/test l0_test_010726_medium_f1 --task screen
Recall = 90.45
