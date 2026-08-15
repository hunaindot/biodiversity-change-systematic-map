# Data preparation and analysis helpers

`data_helpers` contains the reusable data code for the Biodiversity Change Systematic Map. It prepares labelled datasets, builds analysis-ready publication tables, maintains external reference data, and provides the calculations and plotting functions used by the results notebooks.

The package sits between the screening and coding outputs and the final analyses:

```text
reference workbooks ──> labelled train/dev/test data
screening and coding outputs ──> validated analysis tables
validated analysis tables + reference data ──> results and figures
```

The notebooks control the order of an analysis and display its results. The reusable work stays here so that data checks, calculations, and figures can be tested without running a notebook.

## How the package is organized

| Part | Purpose | Main users |
| --- | --- | --- |
| Package root | Shared configuration, label parsing, and figure settings | All workflows |
| `datasets/` | Builds L0–L6 reference-label files, train/dev/test splits, and manual-review samples | Dataset preparation and consistency checks |
| `sources/` | Builds reproducible external reference snapshots | World Bank, IPBES, and GBIF analyses |
| `prep/` | Turns screening and coding outputs into validated handoff files | `notebooks/data_processing/` |
| `analysis/` | Contains the calculations and plotting code for each result | `notebooks/results/` |
| `tests/` | Checks data contracts, calculations, plots, and notebook source boundaries | Development and reproducibility checks |

```text
data_helpers/
├── __main__.py
├── _config.py
├── labels.py
├── results_config.py
├── visualization.py
├── datasets/
├── sources/
├── prep/
├── analysis/
│   ├── geo/
│   ├── realm/
│   └── taxa/
└── tests/
```

## Shared modules

These files are used across more than one workflow.

| Module | Purpose |
| --- | --- |
| `__init__.py` | Exposes `run_from_config` and `SplitError` for programmatic dataset splitting. |
| `__main__.py` | Provides `python -m data_helpers`, the command for creating train/dev/test splits. |
| `_config.py` | Reads `dataset_config` from `repo_config.json` and resolves label paths, split ratios, sampling settings, and the merged-corpus contract. |
| `labels.py` | Provides `parse_list_labels`, a tolerant parser for list-valued fields such as drivers, threats, realms, countries, and taxa. It standardizes the container shape but does not decide whether a label is analytically valid. |
| `results_config.py` | Reads and validates `results_config.json`. It supplies shared paths, category order, display names, colors, and analysis settings, including helpers for Threat L0 and Driver L1 display order. |
| `visualization.py` | Applies repository-wide Matplotlib settings, provides semantic color palettes, chooses contrasting text colors, and saves publication figures through `save_figure`. |

Configuration is kept outside the Python modules:

- [`checklists/mappings/repo_config.json`](../checklists/mappings/repo_config.json) stores dataset preparation, corpus, and path settings.
- [`checklists/mappings/results_config.json`](../checklists/mappings/results_config.json) stores analysis-specific paths, category order, display labels, colors, and output settings.

## `datasets/`: build reference and consistency-check data

This subpackage prepares the labelled data used to develop and evaluate the screening and coding tasks.

| Module | Purpose |
| --- | --- |
| `build_screening.py` | Reads the configured screening workbook sheets, keeps the required bibliographic and eligibility fields, removes duplicate record IDs and rows without abstracts, and writes the combined L0 CSV. |
| `build_coding.py` | Reads the configured coding workbook sheets and writes separate L1–L6 CSV files containing the label columns needed by each task. |
| `splitter.py` | Deduplicates each label dataset, handles missing and multi-label strata, creates reproducible stratified train/dev/test splits, and writes split audits. |
| `sample_screening.py` | Draws the configured manual screening sample from the L0 training split while allocating records across source datasets. |
| `sample_coding.py` | Draws a manual sample from each L1–L6 training split in proportion to the task's configured strata. |

### Build the L0–L6 label files

Run commands from the repository root.

Build screening labels:

```bash
python -m data_helpers.datasets.build_screening
```

Build all coding labels:

```bash
python -m data_helpers.datasets.build_coding
```

Build one coding level by passing a matching label fragment:

```bash
python -m data_helpers.datasets.build_coding l2
```

The source workbooks, sheet names, bibliographic columns, task columns, and output paths come from `dataset_config.screening_dataset` and `dataset_config.coding_dataset` in [`repo_config.json`](../checklists/mappings/repo_config.json).

The prepared files are written to:

```text
data/labels/l0/L0) Screening.csv
data/labels/l1/L1) driver set.csv
data/labels/l2/L2) threats set.csv
data/labels/l3/L3) geography set.csv
data/labels/l4/L4) ecosystem set.csv
data/labels/l5/L5) study set.csv
data/labels/l6/L6) taxa set.csv
```

These files are already included in the repository. Rebuild them only when reproducing the preparation process or when the reference annotations change.

### Create train, development, and test splits

Split every configured label dataset:

```bash
python -m data_helpers
```

Split selected levels or override the random seed:

```bash
python -m data_helpers --labels l0,l2,l5
python -m data_helpers --seed 123
```

The default split is 60% training, 20% development, and 20% test with seed 42. Each task is split independently using its configured stratification field.

```text
data/labels/<level>/
├── train/
├── dev/
├── test/
└── in-process/
```

`in-process/` records the split audit, including duplicates, missing abstracts, excluded rows, stratum counts, and `split_summary.json`.

### Draw manual consistency-check samples

Sample 100 screening records from the L0 training split:

```bash
python -m data_helpers.datasets.sample_screening
```

Sample 100 records for every coding level:

```bash
python -m data_helpers.datasets.sample_coding
```

Sample one coding level:

```bash
python -m data_helpers.datasets.sample_coding l4
```

The sample size, seed, and stratification fields are configured under `dataset_config`. Each sampler writes the selected records and `sample_meta.json`, which records the source file, seed, sample size, and stratum allocation.

```text
data/consistency-check-datasets/screening/to-manual-label/
data/consistency-check-datasets/data-coding/to-manual-label/
```

## `sources/`: build external reference data

This subpackage turns external source data into fixed, auditable inputs for analysis.

| Module | Purpose |
| --- | --- |
| `build_gbif.py` | Streams the configured curated GBIF taxonomy file and builds the canonical-name lookup cache used by taxa preparation and evaluation. |
| `build_worldbank_data.py` | Downloads or reuses a World Bank WDI snapshot, collects API metadata, builds the IPBES–World Bank country crosswalk, keeps current and historical income classifications separate, validates the outputs, and writes acquisition metadata and checksums. |

Rebuild the GBIF lookup cache:

```bash
python -m data_helpers.sources.build_gbif
```

The GBIF source, cache path, chunk size, and taxonomic columns are configured under `dataset_config.gbif` in `repo_config.json`.

Build the World Bank snapshot:

```bash
python -m data_helpers.sources.build_worldbank_data
```

For a smaller check that skips the large WDI observation archive:

```bash
python -m data_helpers.sources.build_worldbank_data --metadata-only
```

The World Bank command also supports custom output and IPBES paths, snapshot IDs, forced downloads, chunk size, page size, timeouts, and source URLs. Run `python -m data_helpers.sources.build_worldbank_data --help` for the complete option list.

## `prep/`: build analysis-ready handoffs

Preparation modules form the boundary between raw screening/coding outputs and results analysis. They validate keys and schemas, record provenance, and write stable artifacts that results notebooks can load directly.

Results notebooks should not read raw `data/coding-*`, screening partitions, GBIF files, or other upstream sources. This rule prevents different results from silently building different versions of the corpus.

| Module | Purpose |
| --- | --- |
| `_provenance.py` | Creates repository-relative source paths and file signatures for portable manifests. |
| `corpus.py` | Joins eligible screening records to configured coding outputs. It enforces unique publication keys and one-to-one joins through `build_merged_corpus` and `build_merged_corpus_from_eligible_screening`. |
| `evidence_corpus_prep.py` | Builds the complete-screening handoff and the integrated one-row-per-eligible-publication dataset. It assigns stable numeric `id` values alongside external `UT` identifiers, standardizes list fields, audits screening exclusions and IPBES geography hierarchy, writes manifests, and exports the public dataset workbook. |
| `taxa_analysis_prep.py` | Builds the one-row-per-publication taxa table, typed taxon-match/lineage Parquet data, inclusion audits, grouping-rule fingerprint, manifest, and fixed GBIF broad-diversity benchmark. |
| `embeddings_prep.py` | Builds one local embedding per publication from title and abstract through an Ollama endpoint. It writes resumable Parquet shards, records errors, and compacts them into a validated `embeddings.parquet` artifact. |

The preparation notebooks are the normal entry points:

| Notebook | Main helper modules | Output purpose |
| --- | --- | --- |
| `notebooks/data_processing/02_taxa_analysis_prep.ipynb` | `prep.corpus`, `prep.taxa_analysis_prep` | Canonical taxa publications, matches, audits, and GBIF benchmark |
| `notebooks/data_processing/03_screening_analysis_prep.ipynb` | `prep.evidence_corpus_prep` | Complete screening table and exclusion summaries |
| `notebooks/data_processing/04_dataset.ipynb` | `prep.corpus`, `prep.evidence_corpus_prep`, `prep.taxa_analysis_prep` | Integrated analysis/public dataset and abstract sidecar |
| `notebooks/data_processing/05_embeddings.ipynb` | `prep.embeddings_prep` | Local publication embeddings and embedding manifest |

Embeddings can also be built from the command line when the local Ollama service and configured model are available:

```bash
python -m data_helpers.prep.embeddings_prep
```

Useful options include `--batch-size`, `--shard-size`, `--limit`, `--cache-dir`, `--no-compact`, `--allow-gaps`, and `--no-progress`. Run the command with `--help` for their exact behavior.

## `analysis/`: calculations and figures

Analysis modules receive prepared tables and return validated tables, audit objects, summaries, or Matplotlib figures. They do not prepare the shared corpus.

### General result modules

| Module | Result | Purpose |
| --- | --- | --- |
| `time_development.py` | Evidence growth | Selects the biodiversity-loss evidence base, produces annual publication and threat-composition tables, and calculates absolute and compound growth. |
| `driver_composition.py` | Income composition | Expands publication-country assignments, links historical World Bank income classes, builds fractional threat attributions, calculates composition and direct standardization, runs bootstrap contrasts and sensitivities, and exports manuscript tables and figures. |

### `analysis/geo/`: shared geographic analysis

| Module | Purpose |
| --- | --- |
| `geography.py` | Loads the IPBES crosswalk and polygons, maps publication geography onto them, calculates per-polygon document counts and Empirical-Bayes location quotients, and returns an audit of skipped or unresolved labels. |
| `count_plotting.py` | Builds fixed order-of-magnitude count bins, color scales, and class colorbars for publication-count choropleths. |
| `attention.py` | Produces publication-fractional observed-country and IPBES-region attention summaries from a country-complete evidence base. |
| `attention_plotting.py` | Draws the radial country-attention wheel, including region runs, country labels, and log-scaled attention bars. |

### `analysis/realm/`: drivers by ecosystem realm

| Module | Purpose |
| --- | --- |
| `driver.py` | Builds the exact-single-realm direct-driver evidence base, audits excluded realm values, calculates realm counts and driver prevalence, and prepares the pollution-nameability time series. |
| `driver_plotting.py` | Draws fractional driver-composition bars and pollution-nameability trend figures, including low-support annotation. |

### `analysis/taxa/`: taxonomic attention

| Module | Purpose |
| --- | --- |
| `benchmark.py` | Loads broad-taxon grouping rules and builds the GBIF described-diversity benchmark used to compare literature attention with known diversity. |
| `skew.py` | Builds and validates the publication-level taxonomic evidence base, estimates attention versus described diversity, calculates bootstrap intervals and allocation sensitivities, and summarizes temporal trends. |
| `skew_plotting.py` | Draws the representation and trend figure for literature attention versus described diversity. |
| `geography.py` | Loads publication-country assignments and calculates country specialization for each broad taxonomic group. |
| `threat_gap.py` | Compares country-level research evidence with threatened vertebrate counts, summarizes the gap by region, and calculates regional evidence trends. |
| `threat_gap_plotting.py` | Stores the shared region order and colors used by the threat-gap outputs. |
| `hierarchy.py` | Builds rank-aligned research and GBIF taxonomic hierarchies, audits exact taxonomic paths, compares rank distributions, and prepares the research-attention sunburst. |
| `hierarchy_plotting.py` | Calculates hierarchy colors and draws the multi-ring taxonomic research-attention sunburst and legend. |
| `clipart.py` | Downloads and caches the configured PhyloPic silhouettes, tints them for figures, and adds them to Matplotlib axes. Published figures using these assets should retain `CLIPART_CREDIT`. |

## Which modules the live results notebooks use

Every results notebook also uses `results_config`; most use `visualization`. The table lists the analysis-specific modules.

| Notebook | Main helper modules |
| --- | --- |
| `00_screening.ipynb` | `prep.evidence_corpus_prep` |
| `01_evidence_growth.ipynb` | `analysis.time_development`, `prep.evidence_corpus_prep` |
| `02_income_composition.ipynb` | `analysis.driver_composition`, `analysis.geo.geography`, `prep.evidence_corpus_prep` |
| `03_realm_composition.ipynb` | `analysis.realm.driver`, `analysis.realm.driver_plotting`, `prep.evidence_corpus_prep` |
| `04_taxonomic_lens.ipynb` | `prep.taxa_analysis_prep`, `analysis.taxa.skew`, `skew_plotting`, `geography`, `threat_gap`, `threat_gap_plotting`, `hierarchy`, `hierarchy_plotting`, and `analysis.geo.geography` |
| `05_geography_attention.ipynb` | `analysis.geo.attention`, `analysis.geo.attention_plotting`, `prep.evidence_corpus_prep` |
| `06_threats_choropleth.ipynb` | `analysis.geo.geography`, `analysis.geo.count_plotting`, `analysis.driver_composition`, `labels`, `prep.evidence_corpus_prep` |

The module inventory above follows the current package and live notebooks rather than older result designs.

## Main data contracts

Several rules apply across the package:

- `UT` is the external publication identifier used to join screening, coding, and prepared data.
- The integrated evidence dataset also has a stable numeric `id` used by public dataset artifacts and embeddings.
- Shared preparation outputs contain one row per publication unless a module explicitly documents a long attribution table.
- Coding joins must be one-to-one on the publication key; duplicate keys raise an error instead of being silently expanded.
- List-valued labels are parsed centrally, but each analysis decides how to handle `Unclear`, `Not Applicable`, missing values, and other special labels.
- Preparation steps write manifests, audits, or source signatures so the origin and exclusions of an artifact can be checked later.
- Results notebooks load prepared handoffs and apply only result-specific universes, estimators, tables, and figures.

## Configuration

The main dataset settings are under `dataset_config` in [`repo_config.json`](../checklists/mappings/repo_config.json):

- source workbook paths and sheet names
- required bibliographic and label columns
- raw L0–L6 output paths
- label-specific stratification fields
- train/dev/test ratios and random seed
- split and manual-review output directories
- consistency-check sample size
- GBIF source and cache settings
- merged screening/coding corpus sources and join columns

Shared result settings are in [`results_config.json`](../checklists/mappings/results_config.json). They include input/output paths, category orders, display names, palettes, analysis periods, bootstrap settings, geography sources, taxonomic groups, and result-specific options.

## Tests

Run the package tests from the repository root:

```bash
venv/bin/python -m pytest data_helpers
```

Tests cover dataset sources, prepared-data contracts, geographic calculations, temporal and income analyses, realm analyses, taxonomic analyses, and plotting functions.

`test_results_source_boundaries.py` also scans live results notebooks. It fails when a results notebook reads raw screening, coding, GBIF, or corpus-building sources directly instead of using the prepared handoffs.

## Related documentation

- [Root README](../README.md) explains the complete repository workflow.
- [Labelling README](../labelling/README.md) explains how screening and coding outputs are produced.
- [Evaluation README](../evals_local/README.md) explains how model outputs are compared with the prepared reference labels.
- [`checklists/repo-readmes/`](../checklists/repo-readmes/) contains execution records and supporting method notes for the repository workflows.
