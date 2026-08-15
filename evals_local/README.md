# Evaluating screening and coding runs

This package checks a completed labelling run against reference labels. It matches predictions and reference records by ID, normalizes the labels, and writes Excel files containing the matched data and evaluation metrics.

The [registered protocol](../checklists/overleaf/protocol-submitted/protocol_published_doi_10.57808.pdf) describes how the reference datasets were assembled to evaluate automated screening and coding. Prepared versions of these datasets are included under [`data/labels/`](../data/labels/): 2,418 records for screening (L0), and task-specific coding sets containing 4,193 records for direct drivers (L1), 624 for threats (L2), 2,350 for geography (L3), 4,205 for ecosystems (L4), 4,758 for study attributes (L5), and 735 for taxa (L6). The coding counts should not be added together because the task datasets overlap and label availability differs by task.

`evals_local` lets you compare a labelling run against these curated reference labels. Only records with matching IDs can be evaluated, so predictions for entirely new records need their own reference labels before metrics can be calculated.

Use it when you want to:

- evaluate an existing screening or coding run
- rerun metrics without calling the OpenAI API again
- evaluate predictions against a different reference file
- inspect which labels were correct, missed, or added by the model

## Quick test

Run commands from the repository root. For example, to evaluate the direct-driver predictions from `l1_train_test`:

```bash
python -m evals_local l1_train_test --tasks driver
```

This command reads predictions from `data/artifacts/batch_outputs/l1_train_test/`, compares them with the provided L1 reference labels, and writes the results to `data/labels/eval/l1_train_test/`.

Running an evaluation does not make any OpenAI API requests.

## What is needed

An evaluation needs two inputs:

1. A completed labelling run containing `.jsonl` model outputs under `data/artifacts/batch_outputs/<run_name>/`.
2. Reference labels containing the same record IDs and the label columns needed for the selected task.

The repository already includes reference labels for screening and L1–L6 under [`data/labels/`](../data/labels/). The default files and required label columns are listed in [Supported tasks](#supported-tasks).

Record IDs must match between the predictions and reference data. The provided coding files use `UT (Unique WOS ID)`. Screening labels also accept `ut_unique_wos_id_` or `custom_id`.

Taxa evaluation has one extra requirement: `checklists/mappings/gbif_lookup_cache.pkl`. The cache expands predicted taxon names into kingdom, phylum, class, order, genus, and species before comparison. Download it from the [protocol supplementary data](https://osf.io/sna2g/overview) if it is not already present.

## Normal workflow

You can run evaluations in either of two ways.

### Run an evaluation separately

Use this when the model outputs already exist:

```bash
python -m evals_local <run_name> --tasks <task>
```

For example:

```bash
python -m evals_local l3_test_run --tasks geography
```

### Run an evaluation after labelling

Set `orchestrator.run_evals` to `true` in [`checklists/mappings/repo_config.json`](../checklists/mappings/repo_config.json). The labelling orchestrator will then evaluate a run after its model outputs are ready.

The current repository default is `false`, so evaluations do not run automatically unless this setting is changed.

For screening, the orchestrator uses the labelling command's input folder as the reference-label source. Coding tasks use the reference files under `evals.labels_dir`.

## Supported tasks

Pass one or more of these names after `--tasks`.

| Task | What is compared | Default reference source | Reference columns |
| --- | --- | --- | --- |
| `screening` | Final eligible/ineligible decision | `data/labels/l0/` | `eligbility` or `eligibility` |
| `driver` | IPBES direct drivers | `data/labels/l1/L1) driver set.csv` | `driver` |
| `threats` | IUCN threat levels available in the reference data | `data/labels/l2/L2) threats set.csv` | `threats_l0`, `threats_l1` |
| `threats_l0` | Broad IUCN threat level | `data/labels/l2/L2) threats set.csv` | `threats_l0` |
| `threats_l1` | Intermediate IUCN threat level | `data/labels/l2/L2) threats set.csv` | `threats_l1` |
| `threats_l2` | Saves matched data only; no L2 reference labels are provided | `data/labels/l2/L2) threats set.csv` | None |
| `geography` | IPBES region, sub-region, and country | `data/labels/l3/L3) geography set.csv` | `region`, `sub-region`, `country` |
| `ecosystems` | GET realm and biome | `data/labels/l4/L4) ecosystem set.csv` | `realm`, `biome` |
| `ecosystems_realm` | GET realm | `data/labels/l4/L4) ecosystem set.csv` | `realm` |
| `ecosystems_biome` | GET biome | `data/labels/l4/L4) ecosystem set.csv` | `biome` |
| `ecosystems_efg` | Saves matched data only; no EFG reference labels are provided | `data/labels/l4/L4) ecosystem set.csv` | None |
| `study` | Study design | `data/labels/l5/L5) study set.csv` | `study_design` |
| `taxa` | Taxonomic ranks | `data/labels/l6/L6) taxa set.csv` | `kingdom`, `phylum`, `class`, `order`, `genus`, `specie` |

The task aliases `threat`, `threat_l0`, `threat_l1`, `threat_l2`, `ecosystem`, `ecosystem_realm`, `ecosystem_biome`, and `ecosystem_efg` are also accepted. The names in the table are preferred because they match the saved task names.

If `--tasks` is omitted, the command tries to evaluate every configured task. This is usually useful only with `--per-task-run-names` or `--use-default-suffixes`, because tasks are often stored under different run names.

## Evaluating a data split

The default coding reference paths point to the complete label files. Predictions are matched by record ID, so a run containing only train, development, or test records can still be evaluated against those complete files.

You can also pass the split folder directly. This is especially useful for screening:

```bash
python -m evals_local l0_train_run --tasks screening \
  --per-task-label-paths screening=data/labels/l0/train
```

The path may be a supported reference file or a screening directory containing CSV files.

## Using custom reference labels

Use `--per-task-label-paths` to replace a task's default reference source:

```bash
python -m evals_local l1_custom_run --tasks driver \
  --per-task-label-paths driver=path/to/reference_labels.csv
```

Custom coding labels can be stored in `.csv`, `.xls`, or `.xlsx` files. They need a matching record ID and the reference columns listed in the task table.

If the reference data are in a multi-sheet Excel workbook, also select the sheet with `--per-task-label-sheets`:

```bash
python -m evals_local l1_manual_sample_run --tasks driver \
  --per-task-label-paths driver=data/consistency-check-datasets/data-coding/annotated_coding_dataset.xlsx \
  --per-task-label-sheets driver=l1_manual_sample
```

`--per-task-label-sheets` has no effect unless a custom workbook is supplied with `--per-task-label-paths`.

## Evaluating several tasks

If several tasks were saved under the same run name, list them together:

```bash
python -m evals_local shared_run --tasks driver geography study
```

If they use different run names, map each task explicitly:

```bash
python -m evals_local \
  --tasks driver geography study \
  --per-task-run-names driver=l1_run geography=l3_run study=l5_run
```

The positional `run_name` is optional when every selected task is included in `--per-task-run-names`.

The CLI can also build run names from a shared base and the repository's default suffixes:

```bash
python -m evals_local experiment_1 \
  --tasks driver geography taxa \
  --use-default-suffixes
```

This looks for:

| Task | Run name used |
| --- | --- |
| `driver` | `experiment_1` |
| `screening` | `experiment_1-screen` |
| `geography` | `experiment_1-geography` |
| `threats*` | `experiment_1-threats` |
| `ecosystems*` | `experiment_1-ecosystem` |
| `study` | `experiment_1-study` |
| `taxa` | `experiment_1-taxa` |

Explicit values passed through `--per-task-run-names` take priority over these generated names.

## Outputs

Each evaluated run is written under:

```text
data/labels/eval/<run_name>/
├── data/
│   └── <task>.xlsx
└── metrics/
    ├── <task>_<label>_label_metrics.xlsx
    └── <task>_<label>_confusion.xlsx
```

The file under `data/` contains the matched reference and predicted labels, their normalized forms, and record-level comparison fields. Use it to inspect individual disagreements.

The files under `metrics/` summarize performance. A separate metric workbook is written for every reference column supported by the task.

### Screening metrics

`screening_eligibility_label_metrics.xlsx` reports the confusion counts and precision, recall, and F1 for `ELIGIBLE` as the positive class:

- precision: of the records predicted eligible, how many were eligible in the reference data
- recall: of the eligible reference records, how many the model kept
- F1: the balance between precision and recall

`screening_eligibility_confusion.xlsx` contains the 2 × 2 confusion table. The matched `screening.xlsx` also includes `tp`, `fp`, `fn`, and `tn` for each record with a reference label.

### Coding metrics

Coding tasks are treated as multi-label classification problems. Their metric workbooks report precision, recall, F1, and Cohen's kappa for each label, followed by `_macro`, `_weighted`, and `_micro` summaries.

Some placeholder values are excluded from particular metric calculations. These include `Unclear` and missing-child messages in the threat hierarchy, missing-candidate messages for ecosystem biome/EFG, and `Not Applicable` or `Unclear` for taxa ranks. The matched data workbook is still available for auditing these records. See the [evaluation metrics overview](../checklists/repo-readmes/others/evaluation-metrics-overview.md) for the exact formulas, aggregation rules, and exclusions.

Tasks without reference columns (`threats_l2` and `ecosystems_efg`) write the matched data workbook but do not produce ground-truth metric workbooks.

## Configuration

Evaluation paths are set in [`checklists/mappings/repo_config.json`](../checklists/mappings/repo_config.json).

| Config key | Current default | Purpose |
| --- | --- | --- |
| `evals.labels_dir` | `data/labels` | Root folder containing the reference labels |
| `evals.output_dir` | `data/labels/eval` | Folder where evaluation results are written |
| `evals.gbif_cache_path` | `checklists/mappings/gbif_lookup_cache.pkl` | GBIF cache used to expand taxa predictions |
| `orchestrator.paths.batch_outputs_dir` | `data/artifacts/batch_outputs` | Folder from which model outputs are read |
| `orchestrator.paths.batches_dir` | `data/artifacts/batches` | Folder from which screening input records are read |
| `orchestrator.run_evals` | `false` | Whether the orchestrator evaluates a completed run automatically |

Changing these paths changes where both direct and orchestrator-triggered evaluations read or write data.

## All command options

| Option | Meaning |
| --- | --- |
| `run_name` | Positional name of the saved labelling run; optional when all names are mapped explicitly |
| `--tasks [TASK ...]` | Tasks to evaluate; if omitted, tries all configured tasks |
| `--per-task-run-names task=run_name [...]` | Use a different saved run for each task |
| `--use-default-suffixes` | Treat `run_name` as a base and append the task suffixes shown above |
| `--per-task-label-paths task=path [...]` | Use a custom reference file or folder for a task |
| `--per-task-label-sheets task=sheet [...]` | Select a sheet from a custom Excel reference workbook |
| `-h`, `--help` | Show the command help |

Mappings use the form `task=value`. Multiple mappings are separated by spaces.

## More detail

- [Labelling README](../labelling/README.md) explains how to produce the model outputs evaluated here.
- [Evaluation metrics overview](../checklists/repo-readmes/others/evaluation-metrics-overview.md) gives the metric formulas, aggregations, exclusions, and interpretation.
- [Screening consistency checks](../checklists/repo-readmes/consistency-checks/screening.md) records the screening evaluation experiments.
- [Coding consistency checks](../checklists/repo-readmes/consistency-checks/coding.md) records the L1–L6 evaluation experiments and selected configurations.
- [Full-corpus execution logs](../checklists/repo-readmes/data-corpus-execution/) records the commands used for final screening and coding runs.
