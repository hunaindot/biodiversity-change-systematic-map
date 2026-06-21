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
  `Completed`: Implies that run is run is executed, data is download, and evals are added

- In execution noteso only weighted summaries are reported; inspect per label and micro + macro summaries in evals files for details

# CC2 Executions (For each Label)

## L1 - Driver

`Completed` : Estimate the direct anthropogenic driver of biodiveristy change - 5 labels

### Dev set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l1/dev l1_dev_010726_low_f1 --task driver`
- `Completed` - `python labelling/orchestrator.py data/labels/l1/dev l1_dev_010726_medium_f1 --task driver`
- `Completed` - `python labelling/orchestrator.py data/labels/l1/dev l1_dev_010726_high_f1 --task driver`

### What performs well in dev (based on F1) [= Low]

| Run                       | Precision | Recall |     F1 |  Kappa |
| ------------------------- | --------: | -----: | -----: | -----: |
| `l1_dev_010726_low_f1`    |    81.75% | 88.96% | 85.06% | 79.73% |
| `l1_dev_010726_medium_f1` |    80.92% | 87.43% | 83.79% | 78.11% |
| `l1_dev_010726_high_f1`   |    80.09% | 86.67% | 82.97% | 76.95% |

### Train set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l1/train l1_train_010726_low_f1 --task driver`

| Run                      | Precision | Recall |     F1 |  Kappa |
| ------------------------ | --------: | -----: | -----: | -----: |
| `l1_train_010726_low_f1` |    80.89% | 87.58% | 84.01% | 78.23% |

### Test set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l1/test l1_test_010726_low_f1 --task driver`

| Run                     | Precision | Recall |     F1 |  Kappa |
| ----------------------- | --------: | -----: | -----: | -----: |
| `l1_test_010726_low_f1` |    81.02% | 87.05% | 83.85% | 78.18% |

## L2 - Threats

Estimate the threats hierarchy Level 1 and Level 2 as defined by IUCN threats classification. Over 10+ labels with nested hierarchy [See more at: https://www.iucnredlist.org/resources/threat-classification-scheme ]

### threats_l0 (Broadest level)

`Completed`

#### Dev set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l2/dev l2_dev_010726_low_f1 --task threats_l0`
- `Completed` - `python labelling/orchestrator.py data/labels/l2/dev l2_dev_010726_medium_f1 --task threats_l0`
- `Completed` - `python labelling/orchestrator.py data/labels/l2/dev l2_dev_010726_high_f1 --task threats_l0`

#### What performs well in dev (based on F1) [= medium]

| Run                       | Precision | Recall |     F1 |  Kappa |
| ------------------------- | --------: | -----: | -----: | -----: |
| `l2_dev_010726_low_f1`    |    80.57% | 69.88% | 73.43% | 66.29% |
| `l2_dev_010726_medium_f1` |    82.31% | 70.56% | 73.67% | 66.66% |
| `l2_dev_010726_high_f1`   |    79.70% | 70.17% | 72.84% | 65.32% |

#### Train set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l2/train l2_train_010726_medium_f1 --task threats_l0`

| Run                         | Precision | Recall |     F1 |  Kappa |
| --------------------------- | --------: | -----: | -----: | -----: |
| `l2_train_010726_medium_f1` |    77.76% | 65.77% | 70.84% | 63.19% |

#### Test set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l2/test l2_test_010726_medium_f1 --task threats_l0`

| Run                        | Precision | Recall |     F1 |  Kappa |
| -------------------------- | --------: | -----: | -----: | -----: |
| `l2_test_010726_medium_f1` |    72.99% | 65.73% | 68.43% | 58.22% |

### threats_l1 (Mid level) [not-started]

#### Dev set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l2/dev l2_dev_010726_low_f1 --task threats_l1`
- `Completed` - `python labelling/orchestrator.py data/labels/l2/dev l2_dev_010726_medium_f1 --task threats_l1`
- `Completed` - `python labelling/orchestrator.py data/labels/l2/dev l2_dev_010726_high_f1 --task threats_l1`

#### What performs well in dev (based on F1) [= High]

| Run                       | Precision | Recall |     F1 |  Kappa |
| ------------------------- | --------: | -----: | -----: | -----: |
| `l2_dev_010726_low_f1`    |    63.68% | 56.12% | 56.42% | 51.42% |
| `l2_dev_010726_medium_f1` |    65.27% | 56.49% | 57.58% | 51.98% |
| `l2_dev_010726_high_f1`   |    64.94% | 58.97% | 58.60% | 53.34% |

#### Train set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l2/train l2_train_010726_medium_f1 --task threats_l1`
- Named medium for consistency with earlier run and path mgt; in reality, high reasoning parameters is passed in request files

| Run                         | Precision | Recall |     F1 |  Kappa |
| --------------------------- | --------: | -----: | -----: | -----: |
| `l2_train_010726_medium_f1` |    69.63% | 54.32% | 59.09% | 54.54% |

#### Test set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l2/test l2_test_010726_medium_f1 --task threats_l1`
- Named medium for consistency with earlier run and path mgt; in reality, high reasoning parameters is passed in request files

| Run                        | Precision | Recall |     F1 |  Kappa |
| -------------------------- | --------: | -----: | -----: | -----: |
| `l2_test_010726_medium_f1` |    63.58% | 56.13% | 57.52% | 51.71% |

## L3 - Geography

Estimate the Region, Sub-region, and Country labels as defined by IPBES [See more at: https://zenodo.org/records/3928281 ]

### Dev set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l3/dev l3_dev_010726_low_f1 --task geography`
- `Completed` - `python labelling/orchestrator.py data/labels/l3/dev l3_dev_010726_medium_f1 --task geography`
- `Completed` - `python labelling/orchestrator.py data/labels/l3/dev l3_dev_010726_high_f1 --task geography`

### What performs well in dev [= Low]

Results for `l3_dev_010726_low_f1`

| Geography Level | Precision | Recall |     F1 |  Kappa |
| --------------- | --------: | -----: | -----: | -----: |
| `region`        |    92.22% | 89.60% | 90.53% | 85.99% |
| `sub-region`    |    84.32% | 89.50% | 86.31% | 80.12% |
| `country`       |    94.23% | 75.53% | 82.57% | 76.68% |

Results for `l3_dev_010726_medium_f1`

| Geography Level | Precision | Recall |     F1 |  Kappa |
| --------------- | --------: | -----: | -----: | -----: |
| `region`        |    90.23% | 87.53% | 88.54% | 82.47% |
| `sub-region`    |    83.83% | 89.98% | 86.18% | 80.24% |
| `country`       |    94.69% | 74.12% | 82.15% | 75.84% |

Results for `l3_dev_010726_high_f1`

| Geography Level | Precision | Recall |     F1 |  Kappa |
| --------------- | --------: | -----: | -----: | -----: |
| `region`        |    91.33% | 89.19% | 89.74% | 84.16% |
| `sub-region`    |    83.59% | 91.41% | 86.65% | 81.42% |
| `country`       |    94.37% | 74.35% | 82.15% | 75.84% |

### Train set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l3/train l3_train_010726_low_f1 --task geography`

| Geography Level | Precision | Recall |     F1 |  Kappa |
| --------------- | --------: | -----: | -----: | -----: |
| `region`        |    92.25% | 90.08% | 90.76% | 86.10% |
| `sub-region`    |    86.04% | 91.28% | 88.13% | 83.85% |
| `country`       |    92.20% | 77.52% | 83.57% | 78.92% |

### Test set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l3/test l3_test_010726_low_f1 --task geography`

| Geography Level | Precision | Recall |     F1 |  Kappa |
| --------------- | --------: | -----: | -----: | -----: |
| `region`        |    91.76% | 90.02% | 90.38% | 85.64% |
| `sub-region`    |    86.99% | 91.21% | 88.41% | 83.49% |
| `country`       |    91.05% | 77.08% | 82.97% | 77.47% |

## L4 Ecosystems

### Dev set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l4/dev l4_dev_010726_low_f1 --task ecosystems_realm`
- `Completed` - `python labelling/orchestrator.py data/labels/l4/dev l4_dev_010726_medium_f1 --task ecosystems_realm`
- `Completed` - `python labelling/orchestrator.py data/labels/l4/dev l4_dev_010726_high_f1 --task ecosystems_realm`

### What performs well in dev

| Run                       | Precision | Recall |     F1 |  Kappa |
| ------------------------- | --------: | -----: | -----: | -----: |
| `l4_dev_010726_low_f1`    |    94.58% | 85.31% | 89.49% | 80.39% |
| `l4_dev_010726_medium_f1` |    93.93% | 86.84% | 90.02% | 81.60% |
| `l4_dev_010726_high_f1`   |    94.57% | 86.84% | 90.44% | 82.66% |

### Train set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l4/train l4_train_010726_high_f1 --task ecosystems_realm`

| Run                       | Precision | Recall |     F1 |  Kappa |
| ------------------------- | --------: | -----: | -----: | -----: |
| `l4_train_010726_high_f1` |    96.00% | 89.13% | 92.30% | 85.61% |

### Test set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l4/test l4_test_010726_high_f1 --task ecosystems_realm`

| Run                      | Precision | Recall |     F1 |  Kappa |
| ------------------------ | --------: | -----: | -----: | -----: |
| `l4_test_010726_high_f1` |    95.85% | 89.73% | 92.61% | 85.83% |

## L5 Study Design

- `Completed`
- Assigned study design among: experimental, modelling, observational, review

### Dev set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l5/dev l5_dev_010726_low_f1 --task study`
- `Completed` - `python labelling/orchestrator.py data/labels/l5/dev l5_dev_010726_medium_f1 --task study`
- `Completed` - `python labelling/orchestrator.py data/labels/l5/dev l5_dev_010726_high_f1 --task study`

### What performs well in dev (=Low)

| Run                       | Precision | Recall |     F1 |  Kappa |
| ------------------------- | --------: | -----: | -----: | -----: |
| `l5_dev_010726_low_f1`    |    86.74% | 82.89% | 84.30% | 66.75% |
| `l5_dev_010726_medium_f1` |    86.32% | 82.06% | 83.63% | 65.17% |
| `l5_dev_010726_high_f1`   |    86.10% | 81.34% | 83.06% | 64.05% |

### Train set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l5/train l5_train_010726_low_f1 --task study`

| Run                      | Precision | Recall |     F1 |  Kappa |
| ------------------------ | --------: | -----: | -----: | -----: |
| `l5_train_010726_low_f1` |    88.36% | 84.99% | 86.37% | 70.48% |

### Test set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l5/test l5_test_010726_low_f1 --task study`

| Run                     | Precision | Recall |     F1 |  Kappa |
| ----------------------- | --------: | -----: | -----: | -----: |
| `l5_test_010726_low_f1` |    86.94% | 82.97% | 84.60% | 67.27% |

## L6 Taxa

`completed`

### Dev set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l6/dev l6_dev_010726_low_f1 --task taxa`
- `Completed` - `python labelling/orchestrator.py data/labels/l6/dev l6_dev_010726_medium_f1 --task taxa`
- `Completed` - `python labelling/orchestrator.py data/labels/l6/dev l6_dev_010726_high_f1 --task taxa`

### What performs well in dev

Results for `l6_dev_010726_low_f1`

| Taxa Level | Precision | Recall |     F1 |  Kappa |
| ---------- | --------: | -----: | -----: | -----: |
| `order`    |    91.85% | 88.15% | 89.71% | 86.35% |
| `genus`    |    96.03% | 96.55% | 96.02% | 95.31% |
| `specie`   |    75.68% | 69.23% | 70.35% | 69.98% |

Results for `l6_dev_010726_medium_f1`

| Taxa Level | Precision | Recall |     F1 |  Kappa |
| ---------- | --------: | -----: | -----: | -----: |
| `order`    |    91.91% | 86.76% | 89.09% | 77.55% |
| `genus`    |    95.97% | 95.69% | 95.51% | 94.69% |
| `specie`   |    74.56% | 69.74% | 70.95% | 70.50% |

Results for `l6_dev_010726_high_f1`

| Taxa Level | Precision | Recall |     F1 |  Kappa |
| ---------- | --------: | -----: | -----: | -----: |
| `order`    |    91.11% | 88.15% | 89.43% | 83.12% |
| `genus`    |    96.77% | 97.39% | 96.85% | 96.30% |
| `specie`   |    74.32% | 70.26% | 71.22% | 70.92% |

### Train set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l6/train l6_train_010726_high_f1 --task taxa`

| Taxa Level | Precision | Recall |     F1 |  Kappa |
| ---------- | --------: | -----: | -----: | -----: |
| `order`    |    90.93% | 88.75% | 89.36% | 75.28% |
| `genus`    |    93.92% | 92.43% | 92.67% | 91.67% |
| `specie`   |    61.27% | 53.42% | 55.03% | 54.57% |

### Test set execution

- `Completed` - `python labelling/orchestrator.py data/labels/l6/test l6_test_010726_high_f1 --task taxa`

| Taxa Level | Precision | Recall |     F1 |  Kappa |
| ---------- | --------: | -----: | -----: | -----: |
| `order`    |    95.96% | 93.55% | 94.54% | 63.62% |
| `genus`    |    92.27% | 95.76% | 93.88% | 93.37% |
| `specie`   |    59.77% | 58.29% | 57.95% | 57.69% |
