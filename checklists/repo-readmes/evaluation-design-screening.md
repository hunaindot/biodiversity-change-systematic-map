# Review of protocol consistency checks

- Primary metric = Recall
  `TP / (TP + FN)` where `ELIGIBLE` is the positive class.

- CC1 = Compare LLM Labels and Expert v. Manual Labels assigned based on abstract reading
  - A) What is human baseline recall when comparing manually assigned labels v. expert labels? (No LLM execution required) [Data: l0-sample]
  - B) How well does LLM replicate human baseline labelling? (Manual labelling v. LLM execution required) [Data: combined]
    See executions: [l0_cc1_combined_010726_medium_f1]

- CC2 = Compare LLM Labels v. Reference Expert Labels in forms of Train, Dev, Test sets

# General notes

- Cmd to run eval: python -m evals_local <execution-name> --tasks screening
- Screening eval outputs to inspect:
  - `metrics/screening_eligibility_confusion.xlsx`
  - `metrics/screening_eligibility_label_metrics.xlsx` with confusion counts plus `ELIGIBLE` recall only

## CC1 B

python labelling/orchestrator.py data/consistency-check-datasets/screening/combined-train-search l0_cc1_combined_010726_medium_f1 --task screen

## CC2 [Train, Dev, Test] Commands to reproduce

### Dev sets executed for different reasoning [low, medium, high] (In order)

python labelling/orchestrator.py data/labels/l0/dev l0_dev_010726_low_f1 --task screen
python labelling/orchestrator.py data/labels/l0/dev l0_dev_010726_medium_f1 --task screen
python labelling/orchestrator.py data/labels/l0/dev l0_dev_010726_high_f1 --task screen

#### What performs well in dev?

[TBA]

### Train set executed for reasoning with highest recall

python labelling/orchestrator.py data/labels/l0/train l0_train_010726_medium_f1 --task screen

### Test set executed for reasoning with highest recall

python labelling/orchestrator.py data/labels/l0/test l0_test_010726_medium_f1 --task screen
