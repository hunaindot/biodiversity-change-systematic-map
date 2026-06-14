# Labelling Package

This package runs the main screening and coding workflow for the repository. It takes a folder of WoS-style records, applies one labelling task, writes the run outputs, and can automatically run evals against the reference labels afterward.

In the normal repo workflow, this package is used on the prepared splits under `data/labels/`. It can also be used on other input folders, such as screened partitions or consistency-checking samples, as long as the expected input fields are present.

## Quick use

Before running:

- configure `.env` using [`.env.sample`](../.env.sample)
- for the standard reproducibility workflow, make sure the prepared `data/labels/` splits are already present as described in the [root README](../README.md)

Run from the repo root:

```bash
python labelling/orchestrator.py <input_dir> <run_name> --task <task>
```

Example:

```bash
python labelling/orchestrator.py data/labels/l1/train l1_train_170426_f1 --task driver
```

In plain English, this command:

- loads the `l1` train split from `data/labels/l1/train`
- runs the `driver` task on every record in that folder
- writes outputs under the run name `l1_train_170426_f1`
- then, if enabled in `.env`, runs evals against the reference labels

## Inputs

`input_dir` should be a folder containing `.xls`, `.xlsx`, or `.csv` WoS-style export files.

Common input locations in this repo include:

- `data/labels/l{0-6}/{train|dev|test}` for the prepared label splits
- `data/partitions-mock/...` for lightweight end-to-end checks
- consistency-checking or screening-derived folders for custom runs

The loader requires a document ID column and accepts these common variants:

- `UT`
- `ut`
- `UT (Unique WOS ID)`
- `custom_id`

It also reads common metadata fields using flexible matching, including:

- title
- abstract
- authors
- source or publisher
- publication year
- WoS categories
- DOI

## Run naming

`run_name` is the tag used across datasets, batch files, outputs, and eval artifacts for a run.

In this repo, runs are typically named like:

- `l1_train_170426_f1`
- `l3_dev_170426_f2`

The trailing `f1`, `f2`, `f3`, and so on are simple version markers. For multi-step tasks, reuse the same `run_name` across all steps so later stages can find earlier outputs.

## Tasks

Use these task names with `--task`:

| Label | Task name          | Depends on         |
| ----- | ------------------ | ------------------ |
| L0    | `screen`           | —                  |
| L1    | `driver`           | —                  |
| L2    | `threats_l0`       | —                  |
| L2    | `threats_l1`       | `threats_l0`       |
| L2    | `threats_l2`       | `threats_l1`       |
| L3    | `geography`        | —                  |
| L4    | `ecosystems_realm` | —                  |
| L4    | `ecosystems_biome` | `ecosystems_realm` |
| L4    | `ecosystems_efg`   | `ecosystems_biome` |
| L5    | `study`            | —                  |
| L6    | `taxa`             | —                  |

For `L2` and `L4`, run the steps in order and keep the same `run_name` throughout.

## Outputs and evals

All run outputs are written under:

`$ORCHESTRATOR_BATCH_OUTPUTS_DIR/<run_name>/`

Simple tasks (`screen`, `driver`, `geography`, `study`, `taxa`) write the raw response envelope. Multi-step tasks (`threats_*`, `ecosystems_*`) write parsed records that also include intermediate labelling metadata needed by downstream levels.

Evals run automatically after each task if `ORCHESTRATOR_RUN_EVALS=true`.

Eval outputs are written under:

`$EVALS_OUTPUT_DIR/<run_name>/`

That folder typically contains:

- `data/` for joined truth and prediction outputs
- `metrics/` for metric files by truth column

For screening runs, automatic evals read the truth labels from `input_dir` directly. For the other tasks, evals resolve truth labels from `EVALS_LABELS_DIR`.

If no ground-truth labels are found, evals do not block the run. Set `ORCHESTRATOR_RUN_EVALS=false` if you want to skip evals entirely.

## Environment

Most runtime behavior is controlled through `.env`. See [`.env.sample`](../.env.sample) for the full reference.

Key variables:

| Variable                       | Description                                                                                              |
| ------------------------------ | -------------------------------------------------------------------------------------------------------- |
| `ORCHESTRATOR_SUBMISSION_MODE` | `live` or `batch`; both are supported, but `batch` is the recommended default when you want to save cost |
| `ORCHESTRATOR_RUN_EVALS`       | Set `false` to skip automatic evals                                                                      |
| `ORCHESTRATOR_LIMIT_DOCS`      | Cap documents per run (`none` for all)                                                                   |

## Notes

- This README focuses on the normal workflow used in this repo.
- The root [README](../README.md) explains how this package fits into the full project flow.
- [`evals_local/README.md`](../evals_local/README.md) covers standalone eval usage in more detail.
