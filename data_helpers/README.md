# data_helpers

At a high level, this package is the dataset-preparation layer for the repository. It takes the reference annotated screening and coding workbooks, turns them into per-label CSV datasets under `data/labels/`, splits those datasets into `train/dev/test`, and creates manual-review samples used for consistency checking. In the wider repo workflow, `data_helpers` sits upstream of the labelling and eval pipelines: it prepares the datasets that those later stages consume.

The code here is included mainly for reproducibility. In normal use, you usually do not need to rerun it because the prepared `data/labels/` datasets are already provided in the repository. If you do want to reproduce those datasets from the reference sources, you can run the build and split commands documented below.

## Package layout

```
data_helpers/
├── _config.py          # loads checklists/mappings/repo_config.json
├── splitter.py         # core train/dev/test split logic
├── build_screening.py  # create L0 screening CSV from Excel source
├── build_coding.py     # create L1–L6 coding CSVs from Excel source
├── build_gbif.py       # recreate the GBIF canonical-name lookup cache if needed
├── corpus.py           # merge eligible screening records with configured coding outputs
├── sample_screening.py # sample L0 train split for manual labelling
└── sample_coding.py    # sample L1–L6 train splits for manual labelling
```

Configuration lives under `dataset_config` in
[`checklists/mappings/repo_config.json`](../checklists/mappings/repo_config.json).
That section defines workbook sources, label metadata, sample size, manual-sample
output locations, split settings, and label-specific stratification metadata.

---

## Merged analysis corpus

Use `build_merged_corpus` when an analysis needs one eligible record per `UT`
with the configured coding outputs attached:

```python
from data_helpers.corpus import build_merged_corpus

corpus_df = build_merged_corpus()
```

The helper reads the screening CSV in chunks, keeps eligible records, and joins
only the configured columns from each coding source. Every input must have a
non-missing, unique `UT`, and each coding source must cover exactly the same
`UT` values as the eligible screening corpus. A mismatch raises
`CorpusMergeError` with counts and example identifiers.

The function returns a DataFrame and does not write a merged file. Paths,
columns, the eligibility field, and the screening chunk size live under
`dataset_config.merged_corpus` in `repo_config.json`. Repository-relative paths
are resolved from the repository root, so callers do not need to construct data
paths themselves.

---

## Split behavior

- Each label is split independently.
- For each label, the splitter uses the stratification column defined in `repo_config.json`.
- Rows are grouped by stratum first, then the configured `train` / `dev` / `test` ratios from `repo_config.json` are applied within each stratum.
- This means the overall split aims to preserve the label distribution of that stratification column across `train`, `dev`, and `test`, rather than assigning records completely at random.
- The default ratios are `60/20/20`, and the default seed is `42`, both configurable through `repo_config.json`.

## Usage

### 1. Build raw CSVs from Excel sources

Goal: convert the reference screening and coding workbooks into the per-label CSV files that the rest of the repo uses.

Expected outcome: raw label datasets appear under `data/labels/l0` through `data/labels/l6`.

```bash
# Screening dataset (L0)
python -m data_helpers.build_screening

# Coding datasets (L1–L6), optionally filter to one label
python -m data_helpers.build_coding
python -m data_helpers.build_coding l2
```

### 2. Split into train / dev / test

Goal: take the raw per-label CSVs and create reproducible `train`, `dev`, and `test` splits for each label.

Expected outcome: each label directory gets `train/`, `dev/`, `test/`, and `in-process/` outputs.

```bash
python -m data_helpers
```

Split ratios and label-root paths are read from `repo_config.json` (see [Configuration](#configuration)).
Run a subset of labels:

```bash
python -m data_helpers --labels l1,l2,l3
python -m data_helpers --seed 123
```

Each label writes to `data/labels/<label>/train|dev|test/` and an `in-process/` folder with deduplication logs, dropped rows, strata counts, and a `split_summary.json`.

### 3. Sample for manual labelling

Goal: draw a smaller subset from the training splits for manual review and current consistency-check workflows.

Expected outcome: sample files are written to the manual-labelling output directories configured in `repo_config.json`.

```bash
python -m data_helpers.sample_screening
python -m data_helpers.sample_coding

# Single label
python -m data_helpers.sample_coding l4
```

Samples 100 records from the train split (configurable via `repo_config.json`).
Sampler inputs are read from `<resolved label path>/train`, where `<resolved label path>` is configured in `repo_config.json`.

These samples feed the current consistency-check notes and notebooks rather than the default labelling path.
Outputs go to `data/consistency-check-datasets/*/to-manual-label/`.

### 4. Build GBIF lookup cache

Goal: recreate the GBIF taxonomic lookup cache used by taxa-related workflows.

Expected outcome: `checklists/mappings/gbif_lookup_cache.pkl` is written from the curated GBIF source file.

Only needed once (or when the GBIF source file changes):

```bash
python -m data_helpers.build_gbif
```

Reads `data/gbif/curated/gbif_curated.csv`, writes `checklists/mappings/gbif_lookup_cache.pkl`.

The code is provided so the cache can be recreated if needed. In normal use, it is recommended to download the prebuilt `gbif_lookup_cache.pkl` from the supplementary data and place it manually at `checklists/mappings/gbif_lookup_cache.pkl`.

---

## Configuration

`repo_config.json` keys read by the splitter and samplers:

| Key                         | Default           | Description                      |
| --------------------------- | ----------------- | -------------------------------- |
| `dataset_config.splits.ratios.train`       | `60`              | Train split %                    |
| `dataset_config.splits.ratios.dev`         | `20`              | Dev split %                      |
| `dataset_config.splits.ratios.test`        | `20`              | Test split %                     |
| `dataset_config.splits.seed`               | `42`              | Random seed                      |
| `dataset_config.splits.label_paths.<label>` | `data/labels/<l>` | Input path for label `<label>`   |
| `dataset_config.merged_corpus.key_column` | `UT` | Exact one-to-one join key |
| `dataset_config.merged_corpus.chunksize` | `250000` | Screening CSV read chunk size |
| `dataset_config.merged_corpus.screening` | — | Screening input, eligibility field, and retained columns |
| `dataset_config.merged_corpus.coding_sources` | — | Ordered coding input paths and retained columns |

Other dataset-preparation settings (sheet names, column names, label configs, sample size) are in
`dataset_config` in [`checklists/mappings/repo_config.json`](../checklists/mappings/repo_config.json).
