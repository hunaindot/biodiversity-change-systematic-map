# evals_local

This package evaluates labelling runs by comparing predicted labels against the reference labels and writing metric files. In the normal repo workflow, it runs automatically at the end of `labelling/orchestrator.py`. You only need to call it directly when you want to rerun evals for an existing run.

## Quick use

Standalone evals are run from the repo root:

```bash
python -m evals_local <run_name> --tasks <task>
```

Example:

```bash
python -m evals_local l1_train_170426_f1 --tasks driver
```

In plain English, this command:

- loads the saved outputs for the run `l1_train_170426_f1`
- compares the predicted `driver` labels against the reference labels
- writes merged prediction-vs-truth files and metric spreadsheets under `data/labels/eval/l1_train_170426_f1/`

For screening, manual eval reruns may need the original input folder passed again as the truth-label path:

```bash
python -m evals_local l0_cc2a_train_170426_f1 --tasks screening \
    --per-task-label-paths screening=data/labels/l0/train
```

For coding tasks, you can also point evals at a multi-sheet workbook by passing both the workbook path and the sheet name for that task:

```bash
python -m evals_local l1_manual_sample_run --tasks driver \
    --per-task-label-paths driver=data/consistency-check-datasets/data-coding/annotated_coding_dataset.xlsx \
    --per-task-label-sheets driver=l1_manual_sample
```

If you do not pass a custom label path, evals continue to use the default truth sources under `data/labels/`.

## Normal workflow

Most users do not need to run this package separately. The usual flow is:

- run a labelling task with `labelling/orchestrator.py`
- let evals run automatically if `orchestrator.run_evals=true`
- inspect the outputs written under `data/labels/eval/<run_name>/`

Direct use of `evals_local` is mainly helpful when:

- an earlier labelling run finished but evals failed
- you changed eval logic and want to rerun metrics
- you want to point a task at a custom label path or workbook sheet

## Supported tasks

Use these task names with `--tasks`:

| Task               | Default truth source                                  | Metrics produced                                         |
| ------------------ | ----------------------------------------------------- | -------------------------------------------------------- |
| `driver`           | `data/labels/l1/L1) driver set.csv`                   | `driver`                                                 |
| `screening`        | `data/labels/l0/` or custom screening label directory | `eligibility`                                            |
| `threats`          | `data/labels/l2/L2) threats set.csv`                  | `threats_l0`, `threats_l1`                               |
| `threats_l0`       | `data/labels/l2/L2) threats set.csv`                  | `threats_l0`                                             |
| `threats_l1`       | `data/labels/l2/L2) threats set.csv`                  | `threats_l1`                                             |
| `threats_l2`       | `data/labels/l2/L2) threats set.csv`                  | no ground-truth metrics                                  |
| `geography`        | `data/labels/l3/L3) geography set.csv`                | `region`, `sub-region`, `country`                        |
| `ecosystems`       | `data/labels/l4/L4) ecosystem set.csv`                | `realm`, `biome`                                         |
| `ecosystems_realm` | `data/labels/l4/L4) ecosystem set.csv`                | `realm`                                                  |
| `ecosystems_biome` | `data/labels/l4/L4) ecosystem set.csv`                | `biome`                                                  |
| `ecosystems_efg`   | `data/labels/l4/L4) ecosystem set.csv`                | no ground-truth metrics                                  |
| `study`            | `data/labels/l5/L5) study set.csv`                    | `study_design`                                           |
| `taxa`             | `data/labels/l6/L6) taxa set.csv`                     | `kingdom`, `phylum`, `class`, `order`, `genus`, `specie` |

The CLI also accepts a few convenience aliases internally, but this README only lists the main task names used in the repo workflow.

## Outputs

All eval outputs are written under:

`data/labels/eval/<run_name>/`

That folder contains:

- `data/` for merged truth-and-prediction spreadsheets
- `metrics/` for per-column metric spreadsheets

Typical file structure:

```text
data/labels/eval/<run_name>/
├── data/
│   └── <task>.xlsx
└── metrics/
    ├── <task>_<col>_label_metrics.xlsx
    └── <task>_<col>_confusion.xlsx
```

Confusion spreadsheets are only written for the screening-style binary metrics.

For `screening`, the summary workbook `screening_eligibility_label_metrics.xlsx`
is intentionally compact. It contains confusion-derived counts plus `ELIGIBLE`
precision (`TP / (TP + FP)`), recall (`TP / (TP + FN)`), and F1. The separate
`screening_eligibility_confusion.xlsx` workbook still contains the 2x2 confusion
table.

For non-screening tasks, the `*_label_metrics.xlsx` workbooks still contain the
per-label precision/recall/F1/Kappa metrics plus aggregate rows such as
`_macro`, `_weighted`, and `_micro`.

## Related notes

For repo-level evaluation notes and interpretation guides, see:

- [`checklists/repo-readmes/evaluation-metrics-overview.md`](../checklists/repo-readmes/evaluation-metrics-overview.md) for the canonical explanation of screening and coding-task metrics, formulas, aggregations, exclusions, and output files
- [`checklists/repo-readmes/evaluation-design-screening.md`](../checklists/repo-readmes/evaluation-design-screening.md) for screening execution notes and chosen run configurations
- [`checklists/repo-readmes/evaluation-design-coding.md`](../checklists/repo-readmes/evaluation-design-coding.md) for coding-task execution notes, weighted summaries, and selected configs by task

## Other CLI modes

The normal manual pattern is one `run_name` plus one `--tasks` value. The CLI also supports some advanced modes:

- `--per-task-run-names` when different tasks live under different run names
- `--use-default-suffixes` when several task outputs share a common base run name
- `--per-task-label-paths` when a task should evaluate against a non-default truth path
- `--per-task-label-sheets` when that custom truth path is a multi-sheet workbook and the task should use a specific sheet

`--per-task-label-sheets` is only meaningful together with `--per-task-label-paths`.

Those modes are mainly there for flexible reruns and older run layouts rather than day-to-day use.

## Environment

Eval-specific paths and the labelling output paths that evals read are stored in
[`checklists/mappings/repo_config.json`](../checklists/mappings/repo_config.json).

Key settings:

| Location                                      | Key                              | Description                                           |
| --------------------------------------------- | -------------------------------- | ----------------------------------------------------- |
| `checklists/mappings/repo_config.json`        | `evals.labels_dir`               | Root directory for ground-truth labels                |
| `checklists/mappings/repo_config.json`        | `evals.output_dir`               | Directory where eval output files are written         |
| `checklists/mappings/repo_config.json`        | `evals.gbif_cache_path`          | GBIF lookup cache used by taxa-related eval logic     |
| `checklists/mappings/repo_config.json`        | `orchestrator.paths.batch_outputs_dir` | Directory from which labelling JSONL outputs are read |
