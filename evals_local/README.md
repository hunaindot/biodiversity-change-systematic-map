# evals_local

Computes evaluation metrics from labelling run outputs, comparing model predictions against ground-truth label CSVs. Runs automatically at the end of each `orchestrator.py` run, or can be invoked standalone.

## Package layout

```
evals_local/
├── config.py       # paths, task registry, default run-name suffixes
├── loaders.py      # joins truth CSVs with prediction JSONL outputs
├── metrics.py      # per-label and binary metric computations
├── normalizers.py  # label normalisation (geography, threats, taxa, …)
└── run.py          # CLI entry point + run_tasks() API
```

## Usage

### Standalone CLI

```bash
python -m evals_local <run_name> [--tasks <task> …]
```

Examples from recent eval runs:

```bash
# Single task
python -m evals_local l1_train_170426_f1 --tasks driver

# Multiple tasks from one run
python -m evals_local l3_train_170426_f2 --tasks geography

# Screening (label path must be the input dir used during labelling)
python -m evals_local l0_cc2a_train_170426_f1 --tasks screening \
    --per-task-label-paths screening=data/labels/l0/train
```

### Per-task run names (when outputs are spread across multiple run names)

```bash
python -m evals_local --per-task-run-names \
    driver=l1_train_170426_f1 \
    geography=l3_train_170426_f1
```

### Default suffix mode (shared base name)

```bash
# Expects batch_outputs/<base>/, batch_outputs/<base>-screen/, etc.
python -m evals_local my_base_run --use-default-suffixes
```

Default suffixes: `driver=""`, `screening="-screen"`, `geography="-geography"`, `threats="-threats"`, `ecosystems="-ecosystem"`, `study="-study"`, `taxa="-taxa"`.

## Output

All outputs land in `data/labels/eval/<run_name>/`:

```
data/labels/eval/<run_name>/
├── data/
│   └── <task>.xlsx          # merged truth + prediction rows with confusion columns
└── metrics/
    ├── <task>_<col>_label_metrics.xlsx
    └── <task>_<col>_confusion.xlsx   # screening only
```

## Available tasks

| Task | Truth CSV (default) | Metrics columns |
|---|---|---|
| `driver` | `data/labels/l1/L1) driver set.csv` | `driver` |
| `screening` | `data/labels/l0/` (directory) | `eligibility` |
| `threats` / `threats_l0/l1/l2` | `data/labels/l2/L2) threats set.csv` | `threats_l0`, `threats_l1` |
| `geography` | `data/labels/l3/L3) geography set.csv` | `region`, `sub-region`, `country` |
| `ecosystems` / `ecosystems_realm/biome/efg` | `data/labels/l4/L4) ecosystem set.csv` | `realm`, `biome` |
| `study` | `data/labels/l5/L5) study set.csv` | `study_design` |
| `taxa` | `data/labels/l6/L6) taxa set.csv` | `kingdom`, `phylum`, `class`, `order`, `genus`, `specie` |

## Configuration

Paths are read from `.env` via `evals_local/config.py`:

| Key | Description |
|---|---|
| `EVALS_LABELS_DIR` | Root directory for ground-truth CSVs (default: `data/labels`) |
| `EVALS_OUTPUT_DIR` | Where eval output Excel files are written (default: `data/labels/eval`) |
| `EVALS_GBIF_CACHE_PATH` | Pickle cache for GBIF taxon lookups (default: `checklists/mappings/gbif_lookup_cache.pkl`) |
| `ORCHESTRATOR_BATCH_OUTPUTS_DIR` | Where labelling JSONL outputs are read from |
