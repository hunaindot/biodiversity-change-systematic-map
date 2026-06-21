This folder holds the main datasets and generated artifacts used across the repository.

At a high level, the default repo workflow is:

- start from the prepared label datasets under `data/labels/`
- run screening or coding with `labelling/`
- write generated run artifacts under `data/artifacts/`
- evaluate predictions against the reference labels

This README focuses only on the core data folders used in that workflow.

## Main folders

```text
data/
├── consistency-check-datasets/   # core reference and annotated datasets used for validation and dataset reconstruction
├── labels/                       # prepared per-label datasets and train/dev/test splits used in the main workflow
└── artifacts/                    # generated datasets, requests, and model outputs from labelling runs
```

## consistency-check-datasets

This folder contains the core reference and annotated datasets used for validation workflows in the project.

It is split into:

- `screening/`
- `data-coding/`

### Reference datasets

The reference datasets are based on previously published evidence syntheses. They serve two important roles:

- they are the source datasets used by `data_helpers` to build the raw `data/labels/l0-l6` datasets
- they provide the full/reference side used in consistency-check comparisons

These reference workbooks are:

- `screening/reference_screening_dataset.xlsx`
- `data-coding/reference_coding_dataset.xlsx`

Those workbooks feed the raw label files:

- `data/labels/l0/L0) Screening.csv`
- `data/labels/l1/L1) driver set.csv`
- `data/labels/l2/L2) threats set.csv`
- `data/labels/l3/L3) geography set.csv`
- `data/labels/l4/L4) ecosystem set.csv`
- `data/labels/l5/L5) study set.csv`
- `data/labels/l6/L6) taxa set.csv`

Those raw label datasets are then split into `train`, `dev`, and `test`.

### Annotated datasets

The annotated datasets contain abstract-level annotations created by the authors of this map for consistency-check workflows.

These annotated workbooks are:

- `screening/annotated_screening_dataset.xlsx`
- `data-coding/annotated_coding_dataset.xlsx`

For screening, the annotated workbook includes:

- `train-sample` with `100`
- `search-sample` with `400`

What we verified:

- `screening/search-sample/search-sample.csv` is an exact export of the workbook `search-sample` sheet
- the workbook `train-sample` sheet is fully drawn from `data/labels/l0/train` once identifier formatting is normalized

The annotated datasets are used in consistency-check workflows rather than the default labelling path. More detail on the current CC1 and CC2 workflow lives in the protocol, the repo-readmes under `checklists/repo-readmes/`, and the current notebooks under `notebooks/`.

## labels

This is the main prepared dataset area used in the default repo workflow.

It contains one folder per label level:

- `l0`
- `l1`
- `l2`
- `l3`
- `l4`
- `l5`
- `l6`

Each label folder typically contains:

- the raw label CSV for that label
- `train/`
- `dev/`
- `test/`
- `in-process/` split artifacts such as summaries and strata counts

This area also contains:

- `eval/`
  - saved evaluation outputs for labelling runs

In normal use:

- `labelling/` reads input data from these splits
- `evals_local/` uses these datasets as the default truth source

Although `data_helpers` can rebuild these datasets from the reference workbooks, most users do not need to rerun that process because `data/labels/` is already provided.

### labels/eval

`data/labels/eval/` stores the evaluation outputs produced for labelling runs.

In the normal workflow:

- `labelling/` runs a task and writes its model outputs under `data/artifacts/`
- `evals_local/` then compares those outputs against the reference labels
- the resulting evaluation files are written under `data/labels/eval/<run_name>/`

At a broad level, this folder is organized by run name. Each run folder typically contains:

- `data/`
  - merged prediction-vs-truth outputs for that run
- `metrics/`
  - evaluation summaries derived from those outputs

This README only describes the role and layout of `data/labels/eval/`. The detailed meaning of the evaluation files belongs in `evals_local/README.md`.

## artifacts

This folder stores generated outputs from labelling runs.

The main subfolders are:

- `datasets/`
  - normalized dataset JSON produced before request generation
- `batches/`
  - request manifests, request JSONL files, and batch input files
- `batch_outputs/`
  - model outputs written or downloaded for each run

In normal use:

- `labelling/` writes to `data/artifacts/`
- `evals_local/` reads prediction outputs back from here when computing metrics

## Scope note

This README intentionally does not document every folder under `data/`.

It leaves out the raw data retrieved from the WoS search query, along with the larger partitioned, screened, and labelled map-processing data derived from it. Those materials are better treated as supplementary data rather than documented in detail here, so this README can stay focused on the active datasets that matter most for understanding and using the repository.
