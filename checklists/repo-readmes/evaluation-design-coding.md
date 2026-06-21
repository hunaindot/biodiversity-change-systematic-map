# Review of protocol consistency checks

- Primary metrics:
  - Per label and aggregated: Precision, Recall, F1, Cohen's Keppa
  - Aggregated summaries: [macro, micro, weighted]

  - Tp/ Fp/ Fn/ Tn defintions
    tp = |truth ∩ pred|
    fp = |pred - truth|
    fn = |truth - pred|
    tn = |label_universe - (truth ∪ pred)|

  - Support = TP + FN = All rows wehre the labels is truly present - Used for weight in summaries

  - Keppa-per-label and interpretations:
    Raw agreement to be very high: tp+tn/N where TN is quite large
    A lot of that agreement comes from the label being absent in many rows
    kappa corrects for that chance/background agreement using Pe:
    P(True positives)_ P(Predicted positives) + P(True negatives)_ P(Predicted negatives)
    Pe exepected to be lower

    Final Keppa being Po - Pe / (1-Pe)

- Consistency Checks
  CC1: What are human labelled baseline metrics when comparing abstract based labelling v. expert labels? (No LLM execution required here)
  [Data: data/consistency-check-datasets/data-coding/annotated_coding_dataset.xlsx]

  CC2: Compare LLM Labels v. Reference Expert Labels in forms of Train, Dev, Test sets

# General Notes

- Status
  [Completed]: Implies that run is run is executed, data is download, and evals are added

- In execution noteso only weighted summaries are reported; inspect per label and micro + macro summaries in evals files for details

# CC2 Executions (For each Label)

## L1 - Driver [Completed]

Estimate the direct anthropogenic driver of biodiveristy change - 5 labels

### Dev set execution

[Completed] python labelling/orchestrator.py data/labels/l1/dev l1_dev_010726_low_f1 --task driver
[Completed] python labelling/orchestrator.py data/labels/l1/dev l1_dev_010726_medium_f1 --task driver
[Completed] python labelling/orchestrator.py data/labels/l1/dev l1_dev_010726_high_f1 --task driver

### What performs well in dev (based on F1) [= Low]

| Run                       | Precision | Recall |     F1 |  Kappa |
| ------------------------- | --------: | -----: | -----: | -----: |
| `l1_dev_010726_low_f1`    |    81.75% | 88.96% | 85.06% | 79.73% |
| `l1_dev_010726_medium_f1` |    80.92% | 87.43% | 83.79% | 78.11% |
| `l1_dev_010726_high_f1`   |    80.09% | 86.67% | 82.97% | 76.95% |

### Train set execution

[Completed] python labelling/orchestrator.py data/labels/l1/train l1_train_010726_low_f1 --task driver

| Run                      | Precision | Recall |     F1 |  Kappa |
| ------------------------ | --------: | -----: | -----: | -----: |
| `l1_train_010726_low_f1` |    80.89% | 87.58% | 84.01% | 78.23% |

### Test set execution

[Completed] python labelling/orchestrator.py data/labels/l1/test l1_test_010726_low_f1 --task driver

| Run                     | Precision | Recall |     F1 |  Kappa |
| ----------------------- | --------: | -----: | -----: | -----: |
| `l1_test_010726_low_f1` |    81.02% | 87.05% | 83.85% | 78.18% |

## L2 - Threats

Estimate the threats hierarchy Level 1 and Level 2 as defined by IUCN threats classification. Over 10+ labels with nested hierarchy [See more at: https://www.iucnredlist.org/resources/threat-classification-scheme ]

### threats_l0 (Broadest level) [In-progress]

### Dev set execution

[Completed] python labelling/orchestrator.py data/labels/l2/dev l2_dev_010726_low_f1 --task threats_l0
[Completed] python labelling/orchestrator.py data/labels/l2/dev l2_dev_010726_medium_f1 --task threats_l0
[Completed] python labelling/orchestrator.py data/labels/l2/dev l2_dev_010726_high_f1 --task threats_l0

### What performs well in dev (based on F1) [= medium]

| Run                       | Precision | Recall |     F1 |  Kappa |
| ------------------------- | --------: | -----: | -----: | -----: |
| `l2_dev_010726_low_f1`    |    80.57% | 69.88% | 73.43% | 66.29% |
| `l2_dev_010726_medium_f1` |    82.31% | 70.56% | 73.67% | 66.66% |
| `l2_dev_010726_high_f1`   |    79.70% | 70.17% | 72.84% | 65.32% |

### Train set execution

python labelling/orchestrator.py data/labels/l2/train l2_train_010726_medium_f1 --task threats_l0

### Test set execution

python labelling/orchestrator.py data/labels/l2/test l2_test_010726_medium_f1 --task threats_l0

| Run                        | Precision | Recall |     F1 |  Kappa |
| -------------------------- | --------: | -----: | -----: | -----: |
| `l2_test_010726_medium_f1` |    72.99% | 65.73% | 68.43% | 58.22% |

### threats_l1 (Mid level) [not-started]

### Dev set execution

python labelling/orchestrator.py data/labels/l2/dev l2_dev_010726_low_f1 --task threats_l1
python labelling/orchestrator.py data/labels/l2/dev l2_dev_010726_medium_f1 --task threats_l1
python labelling/orchestrator.py data/labels/l2/dev l2_dev_010726_high_f1 --task threats_l1

### What performs well in dev (based on F1) [= ??]

See weighted summaries below; inspect per label and micro + macro summaries in evals files

### Train set execution

python labelling/orchestrator.py data/labels/l2/train l2_train_010726_medium_f1 --task threats_l1

### Test set execution

python labelling/orchestrator.py data/labels/l2/test l2_test_010726_medium_f1 --task threats_l1
