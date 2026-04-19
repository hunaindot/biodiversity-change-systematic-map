# Biodiversity Literature Labelling Pipeline

Automated classification of biodiversity literature (Web of Science exports) across seven label dimensions using the OpenAI API, with built-in evaluation metrics and consistency-checking tools.

## Repository structure

```
biodiversity/
├── labelling/              # Main pipeline: orchestrator + OpenAI tasks
│   ├── orchestrator.py     # Entry point — run from here
│   └── src/                # Batching, API calls, task definitions, config
├── evals_local/            # Metric computation (auto-runs after each labelling run)
├── data_helpers/           # Dataset building, train/dev/test splitting, sampling
├── consistency-checking/   # Inter-rater agreement helpers + notebooks
├── checklists/
│   ├── mappings/           # Taxonomy/typology JSONs + GBIF cache
│   └── prompts/            # Prompt config JSON files
└── data/
    ├── labels/             # Ground-truth CSVs + eval outputs
    │   ├── l0/ … l6/       # Per-label train/dev/test splits
    │   └── eval/           # Eval outputs written here
    └── artifacts/          # Intermediate pipeline files
        ├── datasets/       # Parsed document datasets (.json)
        ├── batches/        # Request JSONL files staged for submission
        └── batch_outputs/  # Model responses (JSONL) — one folder per run
```

---

## Label dimensions

| Label | Task name(s) | What is classified |
|---|---|---|
| L0 | `screen` | Paper eligibility (`ELIGIBLE` / `NOT_ELIGIBLE`) |
| L1 | `driver` | Direct biodiversity drivers |
| L2 | `threats_l0`, `threats_l1`, `threats_l2` | IUCN threat classification (3-level hierarchy) |
| L3 | `geography` | Geographic scope, region, sub-region, country |
| L4 | `ecosystems_realm`, `ecosystems_biome`, `ecosystems_efg` | IUCN RLE ecosystem typology (3-level hierarchy) |
| L5 | `study` | Study design type |
| L6 | `taxa` | Taxonomic ranks (kingdom → genus/species) |

---

## Quick start

### 1. Download required data

The `data/` and `checklists/` directories are not included in the repository. Download them from Zenodo before running anything:

**[https://zenodo.org/records/19655124](https://zenodo.org/records/19655124)**

Download `data.zip` and `checklists.zip`, then extract them into the project root so the layout matches the structure above:

```bash
unzip data.zip        # produces data/ at project root
unzip checklists.zip  # produces checklists/ at project root
```

Without these, labelling runs will fail (missing train/dev/test splits) and evals will fail (missing ground-truth CSVs and taxonomy mappings).

### 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.sample .env
```

Open `.env` and replace the placeholder with your OpenAI API key:

```
OPENAI_API_KEY=<ADD YOUR OPENAI API KEY HERE>  →  OPENAI_API_KEY=sk-...
```

All other values in `.env.sample` are pre-configured with sensible defaults and can be left as-is to get started.

### 4. Run a labelling task

All runs are launched from the repo root using `labelling/orchestrator.py`:

```bash
python labelling/orchestrator.py <input_dir> <run_name> --task <task> [--submission-mode live|batch]
```

- **`input_dir`** — directory containing Web of Science `.xls` / `.xlsx` / `.csv` export files
- **`run_name`** — a short tag used to name all outputs for this run (e.g. `l1_train_170426_f1`)
- **`--task`** — classification task to run (see table above; default `driver`)
- **`--submission-mode`** — `live` (synchronous, default) or `batch` (async, cheaper, ~50 % cost)

After the run completes, evals run automatically and write results to `data/labels/eval/<run_name>/`.

### 3. Example commands

Single-label tasks (live or batch):

```bash
# Driver classification — batch mode
python labelling/orchestrator.py data/labels/l1/train l1_train_170426_f1 --task driver -s batch

# Screening
python labelling/orchestrator.py data/labels/l0/train l0_cc2a_train_170426_f1 --task screen -s batch

# Geography
python labelling/orchestrator.py data/labels/l3/train l3_train_170426_f1 --task geography -s batch

# Study design
python labelling/orchestrator.py data/labels/l5/train l5_train_170426_f1 --task study -s batch

# Taxa
python labelling/orchestrator.py data/labels/l6/train l6_train_170426_f1 --task taxa -s batch
```

Multi-level tasks (each level must use the **same** `run_name`):

```bash
# Threats — three sequential passes, each reads the prior level's outputs
python labelling/orchestrator.py data/labels/l2/train my_run --task threats_l0 -s batch
python labelling/orchestrator.py data/labels/l2/train my_run --task threats_l1 -s batch
python labelling/orchestrator.py data/labels/l2/train my_run --task threats_l2 -s batch

# Ecosystems — same pattern
python labelling/orchestrator.py data/labels/l4/train my_run --task ecosystems_realm -s batch
python labelling/orchestrator.py data/labels/l4/train my_run --task ecosystems_biome -s batch
python labelling/orchestrator.py data/labels/l4/train my_run --task ecosystems_efg   -s batch
```

---

## Input format

The orchestrator reads any `.xls`, `.xlsx`, or `.csv` files found in `input_dir`. These are Web of Science export files. Key columns used:

| Column | Description |
|---|---|
| `UT` | Unique WoS record ID (used as `custom_id` in all outputs) |
| `TI` | Title |
| `AB` | Abstract |
| `AU` | Authors |
| `PY` | Publication year |
| `SO` | Journal name |

The loader is tolerant of missing columns — only `UT`, `TI`, and `AB` are strictly required for most tasks.

---

## Configuration (`.env`)

Copy `.env.sample` to `.env` and set at minimum `OPENAI_API_KEY`. Key variables:

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | **Required.** Your OpenAI API key |
| `ORCHESTRATOR_MODEL` | `gpt-5-nano-2025-08-07` | Model to use |
| `ORCHESTRATOR_REASONING` | `high` | Reasoning effort (`low` / `medium` / `high`) |
| `ORCHESTRATOR_SUBMISSION_MODE` | `batch` | Default submission mode |
| `ORCHESTRATOR_LIMIT_DOCS` | `none` | Cap on documents per run (`none` for all) |
| `ORCHESTRATOR_BATCH_SIZE` | `10000` | Documents per request file |
| `ORCHESTRATOR_RUN_EVALS` | `true` | Auto-run evals after each run |
| `EVALS_LABELS_DIR` | `data/labels` | Root of ground-truth label CSVs |
| `EVALS_OUTPUT_DIR` | `data/labels/eval` | Where eval Excel files are written |

---

## Running evals manually

Evals run automatically after each orchestrator run. To re-run them separately:

```bash
python -m evals_local <run_name> --tasks <task>

# Examples
python -m evals_local l1_train_170426_f1 --tasks driver
python -m evals_local l3_dev_170426_f2 --tasks geography
python -m evals_local l0_cc2a_train_170426_f1 --tasks screening \
    --per-task-label-paths screening=data/labels/l0/train
```

Output lands in `data/labels/eval/<run_name>/metrics/` as Excel files.

---

## Building / updating the dataset

Before running labelling, ground-truth label CSVs need to be built from source Excel files and split into train/dev/test. See [`data_helpers/README.md`](data_helpers/README.md) for the full workflow.

Short version:

```bash
python -m data_helpers.build_screening     # build L0 CSV
python -m data_helpers.build_coding        # build L1–L6 CSVs
python -m data_helpers                     # split all labels into train/dev/test
```

---

## Consistency checking

The `consistency-checking/` package provides helpers for inter-rater agreement analysis used in Jupyter notebooks. See [`consistency-checking/README.md`](consistency-checking/README.md).

---

## Package READMEs

Each active package has its own README with full API and configuration details:

- [`labelling/README.md`](labelling/README.md) — orchestrator, all task names, output formats, env vars
- [`data_helpers/README.md`](data_helpers/README.md) — dataset building, splitting, sampling
- [`evals_local/README.md`](evals_local/README.md) — standalone eval CLI, metric outputs
- [`consistency-checking/README.md`](consistency-checking/README.md) — inter-rater agreement helpers
