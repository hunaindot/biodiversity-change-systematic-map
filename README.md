This repository implements LLM-based screening and coding of bibliographic records retrieved from Web of Science for the Biodiversity Change Systematic Map. Records are first screened for eligibility (`L0`), then coded across six downstream label sets (`L1`-`L6`). For detailed label definitions and task-specific behavior, see the package READMEs linked below and the systematic mapping protocol.

## Repository structure

```
root/
├── labelling/              # Core package that applies the LLM screening and coding workflow to bibliographic records
├── evals_local/            # Checks whether the model outputs reproduce the reference labels and expected metrics
├── data_helpers/           # Creates the prepared datasets and splits that make the labelling workflow reproducible
├── notebooks/              # Broad notebook workspace used across the codebase, mostly for validation and data analysis
├── checklists/             # Holds prompts, mappings, and reference assets the classification workflow depends on
└── data/                   # Carries the datasets and generated artifacts through preparation, labelling, and evaluation
```

The structure above is meant as a quick orientation. Several of the main workflow folders have their own README with fuller usage and configuration detail, while folders such as `data/` are included mainly to show how inputs, labels, and generated artifacts are organized across the repo.

---

## Quick start

Quick start assumes the default and recommended path: use the provided label splits in `data/labels/` and run the labelling pipeline directly on them. You do not need to rebuild datasets first.

### 1. Add the GBIF lookup cache

Download the prebuilt `gbif_lookup_cache.pkl` from the [supplementary data of the protocol](https://osf.io/sna2g/overview) and place it at:

`checklists/mappings/gbif_lookup_cache.pkl`

The repository already includes the prepared `data/labels/` splits and the `checklists/` assets needed for normal runs. The GBIF cache is the main extra file you need before running labelling and evals.

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
OPENAI_API_KEY=<ADD YOUR OPENAI API KEY HERE>  ->  OPENAI_API_KEY=sk-...
```

Most of the repository behavior is driven by `.env`. For a normal first run, you usually only need to set `OPENAI_API_KEY`; the remaining defaults in `.env.sample` are set up to work with the provided `data/labels/` splits. The inline comments in `.env.sample` are the detailed reference for what each variable controls.

### 4. Reproduce one labelling run

All runs are launched from the repo root using `labelling/orchestrator.py`.

Example:

```bash
python labelling/orchestrator.py data/labels/l1/train l1_train_170426_f1 --task driver
```

Simply, this command:

- loads the provided `l1` training split from `data/labels/l1/train`
- runs the `driver` coding task over every record in that split
- saves the run outputs under the name `l1_train_170426_f1`
- then, if evals are enabled in `.env`, compares the predicted labels against the true labels and writes metrics under `data/labels/eval/`

This same pattern is used across the repo: pick an input split, choose a task, run the labelling workflow, and optionally evaluate the outputs against the reference labels.

While Quick Start uses the provided `data/labels/` splits, the labelling package can also run on other folders of WoS-style export files as long as they contain the expected record fields. See [`labelling/README.md`](labelling/README.md) for those input requirements and the full task list.

---

## For more detail

Quick start assumes the normal path for this repo: use the provided `data/labels/` splits, run a labelling task, and let evals run from that workflow. If you want to go beyond that default path, the package READMEs are the right place to look.

- [`labelling/README.md`](labelling/README.md) explains the orchestrator, available tasks, run outputs, and environment settings for screening and coding runs.
- [`evals_local/README.md`](evals_local/README.md) explains how to rerun evals manually and how prediction-vs-truth metrics are written.
- [`data_helpers/README.md`](data_helpers/README.md) explains how to rebuild datasets from the reference screening/coding workbooks under `data/consistency-check-datasets/`, recreate train/dev/test splits, and sample review sets.
- [`checklists/repo-readmes/evaluation-metrics-overview.md`](checklists/repo-readmes/evaluation-metrics-overview.md) explains the current screening and coding metrics, aggregation rules, and output files.
- [`checklists/repo-readmes/evaluation-design-screening.md`](checklists/repo-readmes/evaluation-design-screening.md) records the screening consistency-check and eval workflow, plus every experiment run (`CC1A/B`, `CC2` across train/dev/test) with its result summary.
- [`checklists/repo-readmes/evaluation-design-coding.md`](checklists/repo-readmes/evaluation-design-coding.md) records the coding consistency-check and eval workflow, plus every experiment run (`CC1` manual baseline and `CC2` for `L1`–`L6` across train/dev/test) with its result summary.

Other valid workflows in this repo include running on `data/partitions-mock/` for lightweight checks or rebuilding from the reference and supplementary source data when fuller reproduction is needed, but those are better handled in the dedicated package READMEs than in the root guide.
