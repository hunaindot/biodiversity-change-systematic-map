# Biodiversity Change Systematic Map

This repository implements the LLM-based screening and coding pipeline behind the systematic map: records from Web of Science are screened for evidence of biodiversity change, then coded across six dimensions — direct drivers, threats, geographic regions, ecosystems, study attributes, and taxa. Applied to 2.4 million WoS records, it produced 605,199 eligible, coded records, including a subset of 253,081 reporting biodiversity loss; that data is published on OSF at [osf.io/xg8yq](https://osf.io/xg8yq/overview). See the package READMEs linked below for task-specific detail, and the [registered protocol](https://doi.org/10.57808/proceed.2026.31) for the full methodology.

## Repository structure

```text
root/
├── labelling/              # Core package that applies the LLM screening and coding workflow to bibliographic records
├── evals_local/            # Checks whether the model outputs reproduce the reference labels and expected metrics
├── data_helpers/           # Prepares the labelling datasets, builds the analysis corpus, and holds the analysis and plotting modules
├── notebooks/              # Notebook workspace: consistency checks, corpus preparation, and the results analyses
├── checklists/             # Holds prompts, mappings, reference assets, design docs, and manuscript sources
└── data/                   # Carries the datasets and generated artifacts through preparation, labelling, and evaluation
```

The structure above is a quick orientation — most workflow folders have their own README with fuller usage and configuration detail.

The repository runs in two stages. The **labelling stage** screens and codes Web-of-Science records (`labelling/`, `evals_local/`, and the dataset-preparation half of `data_helpers/`). The **analysis stage** merges those coded outputs into a one-row-per-publication corpus and analyses it (`notebooks/`, using the analysis modules in `data_helpers/`) — see [Reproducing results](#reproducing-results).

---

## Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

This is enough to run the notebooks below. Labelling additionally needs an OpenAI key:

```bash
cp .env.sample .env               # then set OPENAI_API_KEY
```

Non-secret repository defaults live in `checklists/mappings/repo_config.json`.

---

## Labelling

`labelling/` reads each record's title and abstract, screens it for evidence of biodiversity change, and codes eligible records against the project prompts (`checklists/prompts/`). The repository already includes the input splits it runs on (`data/labels/`) and the reference labels `evals_local/` checks its output against.

```bash
python labelling/orchestrator.py data/labels/l1/train l1_train_170426_f1 --task driver
```

This reads the `l1` training split, runs the `driver` coding task, and saves outputs under the run name `l1_train_170426_f1`. The `taxa-with-api` task and taxa evaluation additionally need `checklists/mappings/gbif_lookup_cache.pkl`, downloaded from the [protocol supplementary data](https://osf.io/sna2g/overview) — nothing else in the repo, including the notebooks below, needs it.

See [`labelling/README.md`](labelling/README.md) and [`evals_local/README.md`](evals_local/README.md) for the full task list, run options, and evaluation workflow.

---

## Reproducing results

Everything reported in the manuscript is produced by notebooks in `notebooks/`, which holds three workspaces:

- **`consistency_checks/`** — validates the screening/coding methodology itself against reference and expert labels (the `CC1`/`CC2` experiments). Not a dependency of the other two.
- **`data_processing/`** — joins the screening and coding outputs into a single validated, one-row-per-publication corpus.
- **`results/`** — loads that corpus and produces every reported table and figure. The four manuscript findings are `01_evidence_growth.ipynb`, `02_income_composition.ipynb`, `03_realm_composition.ipynb`, and `04_taxonomic_lens.ipynb`; supporting and diagnostic notebooks sit alongside them.

To reproduce the manuscript's numbers, run the `data_processing/` notebooks, then `results/`, in filename order. Each notebook writes its own figures and tables to `outputs/<notebook-name>/` next to it (e.g. `notebooks/results/outputs/01_evidence_growth/`), so you can inspect what a run produced right after running it.

All reusable logic behind these notebooks — corpus construction, analysis, and plotting — lives in `data_helpers/`, documented module-by-module in [`data_helpers/README.md`](data_helpers/README.md).

---

## For more detail

- [`labelling/README.md`](labelling/README.md) — the orchestrator, available tasks, run outputs, and environment settings for screening and coding runs.
- [`evals_local/README.md`](evals_local/README.md) — how to rerun evals manually and how prediction-vs-truth metrics are written.
- [`data_helpers/README.md`](data_helpers/README.md) — how to rebuild datasets, recreate train/dev/test splits, sample review sets, and every corpus-construction, analysis, and plotting module (with which results notebook uses each).
- [`manifest.json`](notebooks/data_processing/outputs/04_dataset/manifest.json) — column-level schema for the corpus as built in this repo (the OSF dataset above documents its own record identifiers and licensing separately).
