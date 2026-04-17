# datasets_labels

Utilities for building, splitting, and sampling the biodiversity literature label datasets (L0–L6).

## Package layout

```
datasets_labels/
├── _config.py          # loads checklists/mappings/dataset_config.json
├── env.py              # .env file parser
├── splitter.py         # core train/dev/test split logic
├── build_screening.py  # create L0 screening CSV from Excel source
├── build_coding.py     # create L1–L6 coding CSVs from Excel source
├── build_gbif.py       # build GBIF canonical-name lookup cache
├── sample_screening.py # sample L0 train split for manual labelling
└── sample_coding.py    # sample L1–L6 train splits for manual labelling
```

All dataset paths, label configs, sheet names, and special keys live in one place:
[`checklists/mappings/dataset_config.json`](../checklists/mappings/dataset_config.json)

---

## Labels

| Label | Task | Stratification column |
|-------|------|-----------------------|
| L0 | Screening (eligibility) | `source` |
| L1 | Driver | `driver` |
| L2 | Threats | `threats_l0` |
| L3 | Geography | `region` |
| L4 | Ecosystems | `realm` |
| L5 | Study design | `study_design` |
| L6 | Taxa | `phylum` |

---

## Usage

### 1. Build raw CSVs from Excel sources

```bash
# Screening dataset (L0)
python -m datasets_labels.build_screening

# Coding datasets (L1–L6), optionally filter to one label
python -m datasets_labels.build_coding
python -m datasets_labels.build_coding l2
```

### 2. Split into train / dev / test

```bash
python -m datasets_labels
```

Split ratios and paths are read from `.env` (see [Configuration](#configuration)).
Run a subset of labels:

```bash
python -m datasets_labels --labels l1,l2,l3
python -m datasets_labels --seed 123
```

Each label writes to `data/labels/<label>/train|dev|test/` and an `in-process/` folder with deduplication logs, dropped rows, strata counts, and a `split_summary.json`.

### 3. Sample for manual labelling

```bash
python -m datasets_labels.sample_screening
python -m datasets_labels.sample_coding

# Single label
python -m datasets_labels.sample_coding l4
```

Samples 100 records from the train split (configurable via `dataset_config.json`).
Outputs go to `data/consistency-check-datasets/*/to-manual-label/`.

### 4. Build GBIF lookup cache

Only needed once (or when the GBIF source file changes):

```bash
python -m datasets_labels.build_gbif
```

Reads `data/gbif/curated/gbif_curated.csv`, writes `checklists/mappings/gbif_lookup_cache.pkl`.

---

## Configuration

`.env` keys read by the splitter:

| Key | Default | Description |
|-----|---------|-------------|
| `train` | `60` | Train split % |
| `dev` | `20` | Dev split % |
| `test` | `20` | Test split % |
| `DATASETS_LABELS_SEED` | `42` | Random seed |
| `LABELS_<L>_PATH` | `data/labels/<l>` | Override input path for label `<l>` (e.g. `LABELS_L0_PATH`) |

Everything else (sheet names, column names, label configs, source weights, sample size) is in
[`checklists/mappings/dataset_config.json`](../checklists/mappings/dataset_config.json).
