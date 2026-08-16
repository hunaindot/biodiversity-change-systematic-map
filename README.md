This repository implements LLM-based screening and coding of bibliographic records retrieved from Web of Science for the Biodiversity Change Systematic Map. Records are first screened for eligibility (`L0`), then coded across six downstream label sets (`L1`-`L6`). For detailed label definitions and task-specific behavior, see the package READMEs linked below and the systematic mapping protocol.

## Repository structure

```
root/
├── labelling/              # Core package that applies the LLM screening and coding workflow to bibliographic records
├── evals_local/            # Checks whether the model outputs reproduce the reference labels and expected metrics
├── data_helpers/           # Prepares the labelling datasets, builds the analysis corpus, and holds the analysis and plotting modules
├── notebooks/              # Notebook workspace: consistency checks, corpus preparation, and the results analyses
├── checklists/             # Holds prompts, mappings, reference assets, design docs, and manuscript sources
└── data/                   # Carries the datasets and generated artifacts through preparation, labelling, and evaluation
```

The structure above is meant as a quick orientation. Several of the main workflow folders have their own README with fuller usage and configuration detail, while folders such as `data/` are included mainly to show how inputs, labels, and generated artifacts are organized across the repo.

Broadly, the repository runs in two stages. The **labelling stage** screens and codes Web-of-Science records (`labelling/`, `evals_local/`, and the dataset-preparation half of `data_helpers/`), and is what the Quick start below reproduces. The **analysis stage** merges those coded outputs into a one-row-per-publication corpus and analyses it (`notebooks/data_processing/`, then `notebooks/results/`, using the analysis modules in `data_helpers/`). See [Analysis and results](#analysis-and-results) for that second stage.

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

Only the OpenAI API key belongs in `.env`. Non-secret repository defaults are stored in `checklists/mappings/repo_config.json`.

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
- then, if evals are enabled in `checklists/mappings/repo_config.json`, compares the predicted labels against the true labels and writes metrics under `data/labels/eval/`

This same pattern is used across the repo: pick an input split, choose a task, run the labelling workflow, and optionally evaluate the outputs against the reference labels.

While Quick Start uses the provided `data/labels/` splits, the labelling package can also run on other folders of WoS-style export files as long as they contain the expected record fields. See [`labelling/README.md`](labelling/README.md) for those input requirements and the full task list.

---

## Analysis and results

Once records have been screened and coded, the analysis stage merges those outputs into a single analysis corpus and reports on it. This stage is notebook-driven, with all substantive logic living in importable modules under `data_helpers/` so it stays testable.

**1. Corpus preparation** — `notebooks/data_processing/` joins the screening and coding outputs into validated, one-row-per-publication artifacts, each written to its own folder under `notebooks/data_processing/outputs/<NN>_<notebook-name>/`. Each active corpus prep writes a `manifest.json` recording what was built.

| Notebook | Builds |
| --- | --- |
| `02_taxa_analysis_prep.ipynb` | Taxa publications table, typed nested match/lineage artifact, and fixed GBIF described-diversity benchmark |
| `03_screening_analysis_prep.ipynb` | Complete-screening table and exclusion-criteria overlap |
| `04_dataset.ipynb` | Core 37-column dataset in Parquet and Excel, plus a separate `id`/`UT`/`abstract` sidecar |

The retired climate prep notebook and its two prepared artifacts are preserved together under `notebooks/data_processing/archive/`; only archived climate analyses consume them.

**2. Results** — `notebooks/results/` loads those prepared artifacts and applies only analysis-specific filters, estimators, figures, and exports. `00_screening.ipynb` is the supporting screening audit. The four manuscript findings are implemented by `01_evidence_growth.ipynb`, `02_income_composition.ipynb`, `03_realm_composition.ipynb`, and `04_taxonomic_lens.ipynb`. `05_geography_attention.ipynb` is a supporting extension that summarizes country and IPBES-region concentration using publication-fractional attention and produces the supplementary geographic-attention wheel. `03_unchecked_realm_composition.ipynb` is an explicitly unchecked companion analysis, and `threats_supplementary.ipynb` contains supplementary diagnostics (publication-year and geography research-specialization); its realm × threat distribution section was archived on 2026-08-15. Superseded notebooks live under `notebooks/results/archive/`. Figures and tables are written to `notebooks/results/outputs/<section>/`.

Two conventions matter when reading any result:

- **Counting means unique documents.** A publication naming five countries adds one to each, not five, so ordinary country shares can sum to more than 100%. Result 05 additionally reports an explicitly publication-fractional attention composition that sums to 100%.
- **Non-mappable label values are handled explicitly.** General geography helpers audit values such as `[]`, `Not Applicable`, `Unclear`, and invalid ISO3 codes. Result 05 inherits a country-complete base, permits special tokens only alongside a mapped country, and fails if an unresolved token or unmapped publication appears.

Each manuscript finding, plus the exploratory Result 05 geography extension, has a canonical specification under [`checklists/repo-readmes/results/`](checklists/repo-readmes/results/) defining its universe, denominator, estimator, and caveats. Start there rather than reverse-engineering a notebook.

---

## For more detail

Quick start assumes the normal path for this repo: use the provided `data/labels/` splits, run a labelling task, and let evals run from that workflow. If you want to go beyond that default path, the package READMEs are the right place to look.

- [`labelling/README.md`](labelling/README.md) explains the orchestrator, available tasks, run outputs, and environment settings for screening and coding runs.
- [`evals_local/README.md`](evals_local/README.md) explains how to rerun evals manually and how prediction-vs-truth metrics are written.
- [`data_helpers/README.md`](data_helpers/README.md) explains how to rebuild datasets from the reference screening/coding workbooks under `data/consistency-check-datasets/`, recreate train/dev/test splits, and sample review sets. It also documents every corpus-construction, analysis, and plotting module, and which results notebook uses each one.
- [`checklists/repo-readmes/results/`](checklists/repo-readmes/results/) holds the canonical specification for each manuscript finding and the exploratory geography-attention result—the universe, denominator, estimator, and caveats behind every reported number. Supporting method notes cover [taxonomic grouping and the GBIF benchmark](checklists/repo-readmes/others/taxa-grouping-and-benchmark.md) and [geographic research specialization](checklists/repo-readmes/others/geography-research-specialization.md); the machine-readable Threat-L0 palette and order remain in [`checklists/mappings/results_config.json`](checklists/mappings/results_config.json).
- [`checklists/repo-readmes/others/evaluation-metrics-overview.md`](checklists/repo-readmes/others/evaluation-metrics-overview.md) explains the current screening and coding metrics, aggregation rules, and output files.
- [`checklists/repo-readmes/consistency-checks/screening.md`](checklists/repo-readmes/consistency-checks/screening.md) records the screening consistency-check and eval workflow, plus every experiment run (`CC1A/B`, `CC2` across train/dev/test) with its result summary.
- [`checklists/repo-readmes/consistency-checks/coding.md`](checklists/repo-readmes/consistency-checks/coding.md) records the coding consistency-check and eval workflow, plus every experiment run (`CC1` manual baseline and `CC2` for `L1`–`L6` across train/dev/test) with its result summary
- [`checklists/repo-readmes/data-corpus-execution/`](checklists/repo-readmes/data-corpus-execution/) contains execution logs for full data-corpus screening and coding runs.

Other valid workflows in this repo include running on `data/partitions-mock/` for lightweight checks or rebuilding from the reference and supplementary source data when fuller reproduction is needed, but those are better handled in the dedicated package READMEs than in the root guide.
