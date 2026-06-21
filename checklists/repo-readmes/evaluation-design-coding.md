# Coding Evaluation Notes

- Consistency Checks
  - `CC1`: Compare author-assigned coding labels based on abstracts only against expert full-text labels across all six label sets (`L1` to `L6`) to establish a human-performance baseline. No LLM execution is required here.
    - Data: `data/consistency-check-datasets/data-coding/annotated_coding_dataset.xlsx`
  - `CC2`: Compare LLM coding labels against expert full-text labels across train, dev, and test splits for all six label sets (`L1` to `L6`).

# General Notes

- For metric definitions, formulas, aggregation behavior, exclusions, and eval output files, see [evaluation-metrics-overview.md](/Users/hunain/d/coding-projects/biodiversity/checklists/repo-readmes/evaluation-metrics-overview.md)
- Status
  `Completed`: Implies that run is run is executed, data is download, and evals are added

- In execution noteso only weighted summaries are reported; inspect per label and micro + macro summaries in evals files for details

## CC1 Executions

- Notebook: [coding_cc1_manual_baseline.ipynb](/Users/hunain/d/coding-projects/biodiversity/notebooks/coding_cc1_manual_baseline.ipynb)
- Input workbook:
  - `data/consistency-check-datasets/data-coding/annotated_coding_dataset.xlsx`
- Reference truth files:
  - `data/labels/l1/L1) driver set.csv`
  - `data/labels/l2/L2) threats set.csv`
  - `data/labels/l3/L3) geography set.csv`
  - `data/labels/l4/L4) ecosystem set.csv`
  - `data/labels/l5/L5) study set.csv`
  - `data/labels/l6/L6) taxa set.csv`
- Metric implementation: reuses `evals_local` package

### CC1 Weighted Summaries

#### L1 - Driver

| Label Set | Precision | Recall |     F1 |  Kappa |
| --------- | --------: | -----: | -----: | -----: |
| `driver`  |    86.60% | 79.44% | 81.94% | 76.05% |

#### L2 - Threats

| Label Set    | Precision | Recall |     F1 |  Kappa |
| ------------ | --------: | -----: | -----: | -----: |
| `threats_l0` |    82.22% | 70.15% | 75.06% | 67.66% |

#### L3 - Geography

| Geography Level | Precision | Recall |     F1 |  Kappa |
| --------------- | --------: | -----: | -----: | -----: |
| `region`        |    95.02% | 90.20% | 92.38% | 89.54% |
| `sub-region`    |    96.35% | 91.40% | 93.33% | 90.81% |
| `country`       |    95.10% | 81.91% | 87.39% | 84.61% |

#### L4 - Ecosystems

| Label Set | Precision | Recall |     F1 |  Kappa |
| --------- | --------: | -----: | -----: | -----: |
| `realm`   |   100.00% | 93.07% | 96.14% | 93.65% |

#### L5 - Study Design

| Label Set      | Precision | Recall |     F1 |  Kappa |
| -------------- | --------: | -----: | -----: | -----: |
| `study_design` |    82.31% | 76.47% | 76.76% | 52.66% |

#### L6 - Taxa

| Taxa Level | Precision | Recall |     F1 |  Kappa |
| ---------- | --------: | -----: | -----: | -----: |
| `order`    |    92.65% | 93.55% | 93.06% | 80.85% |
| `genus`    |    96.72% | 94.25% | 95.31% | 94.57% |
| `specie`   |    78.48% | 76.03% | 76.65% | 76.42% |

# CC2 Executions

## L1 - Driver

`Completed` : Estimate the direct anthropogenic driver of biodiveristy change - 5 labels

- Coverage
  - Task covers the direct anthropogenic driver of biodiversity change
  - Label count = 5
  - Evaluated labels: `climate change`, `direct exploitation and resource extraction`, `invasive alien species`, `land/sea use change`, `pollution`

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

- Coverage
  - Broad IUCN threat families
  - Label count = 11
  - Evaluated labels: `agriculture & aquaculture`, `biological resource use`, `climate change & severe weather`, `energy production & mining`, `human intrusions & disturbance`, `invasive & other problematic species, genes & diseases`, `natural system modifications`, `other options`, `pollution`, `residential & commercial development`, `transportation & service corridors`

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

### threats_l1

`Completed`

- Coverage
  - Mid-level IUCN threat categories nested under the broader `threats_l0` families
  - Label count = 31
  - Evaluated values span categories such as crops, livestock, aquaculture, logging, fishing, mining, roads, utility lines, recreation, effluents, invasive species, diseases, droughts, storms, fire, temperature extremes, and other ecosystem modifications
  - Full label set is in the per-label eval workbook rather than repeated here because the list is longer: 31 values

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

`Completed`

Estimate the Region, Sub-region, and Country labels as defined by IPBES [See more at: https://zenodo.org/records/3928281 ]

- Coverage
  - Geography is evaluated at 3 levels: `region`, `sub-region`, and `country`
  - Region label count = 6
  - Region values in current eval outputs: `africa`, `americas`, `antarctica`, `asia and the pacific`, `europe and central asia`, `all region`.
  - Sub-region label count = 17
  - Sub-region values: `caribbean`, `central africa`, `central and western europe`, `central asia`, `east africa and adjacent islands`, `eastern europe`, `mesoamerica`, `north africa`, `north america`, `north-east asia`, `oceania`, `south america`, `south asia`, `south-east asia`, `southern africa`, `west africa`, `western asia`
  - Country label count = 59
  - Country values are mostly ISO3 country codes; current eval outputs also include `not applicable` and `unclear`

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

`Completed`

- Coverage
  - Current execution note covers `ecosystems_realm`
  - Realm label count = 10
  - Evaluated labels: `all realms`, `freshwater`, `freshwater-marine`, `freshwater-terrestrial`, `marine`, `marine-terrestrial`, `not applicable`, `subterranean`, `subterranean-freshwater`, `terrestrial`

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

`Completed`

- Coverage
  - This evaluations covers study-design classification
  - Label count = 5
  - Evaluated labels: `experimental`, `modelling`, `observational`, `review`, `unclear`

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

- Coverage
  - Taxa is evaluated at 6 ranks: `kingdom`, `phylum`, `class`, `order`, `genus`, `specie`
  - Each label can have multiple values
  - Task predicts the taxon rank and taxon value as lowest level; upstream values are inferred from GBIF Taxonomy look up.

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
