# `data_helpers`

`data_helpers` contains repository-support code for preparing labelled datasets,
building consistency-checking samples, joining shared analysis data, and keeping
results notebooks reproducible.

Its main command-line workflow converts the reference screening and coding
workbooks into per-label CSV files, creates reproducible train/dev/test splits,
and samples records for manual consistency checking. The remaining modules are
support libraries used by notebooks and other repository workflows.

Raw screening and coding joins belong in `notebooks/data_processing`. Results
notebooks load the validated prepared stores (or another explicit processing
artifact) and apply only analysis-specific filters, estimators, plots, and
exports. This keeps every substantive result on the same one-row-per-eligible-
`UT` starting corpus.

Configuration is stored in
[`checklists/mappings/repo_config.json`](../checklists/mappings/repo_config.json)
and
[`checklists/mappings/results_config.json`](../checklists/mappings/results_config.json).

## Package layout

Shared core sits at the package root; everything else is grouped by the job it does.
Modules moved into subpackages keep their public API unchanged.

```text
data_helpers/
├── _config.py, results_config.py, visualization.py, labels.py   shared core
├── datasets/     reference workbooks -> label datasets, splits, CC samples (CLI)
├── sources/      external reference snapshots (GBIF, World Bank/IPBES)
├── prep/         handoffs built by notebooks/data_processing
├── analysis/     results analysis, one module or subpackage per finding
│   ├── time_development.py        F1 evidence growth
│   ├── driver_composition.py      F2 national income groups
│   ├── realm/                     F3 drivers x ecosystem realm
│   ├── taxa/                      F4 taxonomic attention
│   └── geo/                       shared geographic aggregation and reference data
└── tests/
```

### Shared core (package root)

| File | Role |
| --- | --- |
| `__init__.py` | Marks `data_helpers` as an importable Python package. |
| `__main__.py` | Command-line entry point for configured train/dev/test splitting. |
| `_config.py` | Loads and validates dataset paths, labels, split settings, sampling settings, and the merged-corpus contract from `repo_config.json`. |
| `results_config.py` | Loads and validates shared results semantics, colors, analysis settings, and output paths from `results_config.json`. Also exposes the display/order helpers for Threats L0 and Drivers L1. |
| `visualization.py` | Repository plotting defaults, semantic colors (`BIODIVERSITY`), and publication-figure export (`save_figure`, PDF by default). |
| `labels.py` | `parse_list_labels`, the tolerant reader for every list-valued coding column (drivers, threats, realms, taxa, geography). Used by most analysis modules; it only normalises shape, and deciding which label values are meaningful stays with the caller. |

### `datasets/` — dataset preparation (command line)

| File | Role |
| --- | --- |
| `build_screening.py` | Converts the reference screening workbook into the raw L0 screening CSV. |
| `build_coding.py` | Converts the reference coding workbook into raw L1-L6 label CSVs. |
| `splitter.py` | Deduplicates, stratifies, splits, audits, and writes label datasets. |
| `sample_screening.py` | Draws the configured L0 manual consistency-check sample from the training split. |
| `sample_coding.py` | Draws configured L1-L6 manual consistency-check samples from the training splits. |

### `sources/` — external reference snapshots

| File | Role |
| --- | --- |
| `build_gbif.py` | Rebuilds the curated GBIF taxonomic lookup cache used by taxa workflows. |
| `build_worldbank_data.py` | Builds and validates the versioned World Bank/IPBES data snapshot and public crosswalk. |

### `prep/` — corpus construction (consumed by `notebooks/data_processing`)

| File | Role |
| --- | --- |
| `corpus.py` | Builds the one-row-per-publication eligible analysis corpus from either raw screening (`build_merged_corpus`) or a prepared eligible-screening artifact (`build_merged_corpus_from_eligible_screening`), with strict one-to-one coding joins. |
| `evidence_corpus_prep.py` | Builds and validates the complete-screening handoff and the integrated one-row-per-eligible-UT corpus containing screening, driver, threats, geography, realm, study, and taxa fields. |
| `taxa_analysis_prep.py` | Builds and validates the canonical one-row-per-UT taxa handoff, compact processing audits, semantic rule fingerprint, and fixed GBIF broad benchmark shared by taxa results. |

### `analysis/` — results analysis

| File | Finding | Role |
| --- | --- | --- |
| `time_development.py` | F1 | Annual publication, threat-composition, and growth analyses. |
| `driver_composition.py` | F2 | Historical-income threat composition, standardization, bootstrap checks, figures, and exports. |
| `realm/driver.py` | F3 | Exact-single-realm driver evidence base (negative impacts, complete years 2000-2025), realm counts, multi-label driver prevalence, the complementary fractional composition, and the pollution-nameability trend tests. Administrative/aggregate and multi-realm outputs are excluded and audited. |
| `realm/threat.py` | F3 | Attaches the parallel Threat-L0 taxonomy to the exact publication universe prepared by `realm/driver.py`: counts, summaries, fractional composition, and driver-conditional threat composition. Missing or unusable threat labels stay in the denominator; Geological Events is recognized but excluded as outside this map's coding scope. |
| `realm/driver_plotting.py` | F3 | Driver location-quotient heatmap, fractional-composition bars, nested driver x threat bars, and pollution-nameability trend figures. |
| `realm/threat_plotting.py` | F3 | Standalone Threat-L0 location-quotient heatmap and fractional-composition bars by realm. |
| `taxa/benchmark.py` | F4 | Broad-group mapping loader (`load_broad_group_mapping`) plus the GBIF described-diversity benchmark (`DescribedDiversity`, `build_described_diversity_benchmark`). Article-side broad groups come from the precomputed `broad_taxa_groups` enrichment field. The superseded driver-attention estimator that once lived here was removed; the current estimator is `taxa/driver_conditional.py`. |
| `taxa/skew.py` | F4 | One-row-per-UT taxonomic-skew evidence table, exclusion and match audits, GBIF comparison, bootstrap intervals, allocation sensitivities, and rebalanced focal-group comparisons such as the animal-only literature check. |
| `taxa/driver_conditional.py` | F4 | Eight-group driver-conditioned taxonomic-attention analysis, complete-pattern bootstrap, planned contrasts, and sensitivity estimators. |
| `taxa/skew_plotting.py` | F4 | Connected-dot and representation-ratio figure for taxonomic attention versus described diversity. |
| `taxa/driver_conditional_plotting.py` | F4 | Resolution audit, specialization heatmap, focal interval plot, and detail-group supplement. |
| `taxa/clipart.py` | F4 | Caches the PhyloPic taxon silhouettes declared in `taxa_broad_groups.json` under `data/taxa-clipart/` and embeds them into axes, tinted to each group's own color. Assets use public-domain CC0/PDM 1.0 terms; keep `CLIPART_CREDIT` on any published figure that uses them. |

### `analysis/geo/` — shared geographic analysis

| File | Role |
| --- | --- |
| `geography.py` | Maps predicted geography labels onto the IPBES reference: per-polygon counts (`geo_counts`), the Empirical-Bayes Location Quotient (`location_quotient`), and reference loading (`load_crosswalk`, `load_polygons`). Special label values are skipped but always reported in an audit. F1 uses the counts and polygons for study-volume choropleths; F4 reaches the location quotient through `analysis/taxa/geography.py`; the archived `threats_supplementary.ipynb` uses both. |
| `attention.py` | Builds Result 05's complete IPBES hierarchy, unique publication–country assignments, publication-fractional attention composition, low/zero/no-key states, and geography-resolution audits. |
| `attention_plotting.py` | Draws Result 05's simplified equal-slot region → country wheel and log-scaled attention bars, including the large all-place reference version. Regions and positive-attention countries read clockwise from 12 o'clock in descending fractional-attention order; zero and no-key leaves finish each region block. |

### `tests/`

Run with `venv/bin/python -m pytest data_helpers`.

## Which module a results notebook uses

Notebooks import with an alias where the leaf name changed, so the name used in the
notebook body is stable — for example
`from data_helpers.analysis.taxa import skew as taxa_skew`.

Every results notebook also imports `results_config` and `visualization`; only the
analysis-specific modules are listed here.

These are the seven live analysis notebooks under `notebooks/results/` (excluding the
archived supplementary notebook).

| Notebook | Modules |
| --- | --- |
| `00_screening.ipynb` | `prep.evidence_corpus_prep` |
| `01_evidence_growth.ipynb` | `analysis.time_development`, `analysis.geo.geography`, `prep.evidence_corpus_prep` |
| `02_income_composition.ipynb` | `analysis.driver_composition`, `prep.evidence_corpus_prep` |
| `03_realm_composition.ipynb` | `analysis.realm.driver`, `analysis.realm.driver_plotting`, `analysis.realm.claims`, `prep.evidence_corpus_prep` |
| `03_unchecked_realm_composition.ipynb` | `analysis.realm.driver`, `analysis.realm.driver_plotting`, `analysis.realm.threat`, `analysis.realm.threat_plotting`, `prep.evidence_corpus_prep` |
| `04_taxonomic_lens.ipynb` | `prep.taxa_analysis_prep`, `analysis.geo.geography`, `analysis.taxa.geography`, `analysis.taxa.skew`, `analysis.taxa.skew_plotting`, `analysis.taxa.driver_conditional`, `analysis.taxa.driver_conditional_plotting`, `analysis.taxa.claims` |
| `05_geography_attention.ipynb` | `prep.evidence_corpus_prep`, `analysis.geo.attention`, `analysis.geo.attention_plotting` |

Archived notebooks and the modules they still need are documented in
`notebooks/results/archive/README.md` and
`notebooks/results/archive/retired-helpers/README.md`. `analysis.realm.threat` and
`threat_plotting` are live **only** through `03_unchecked_realm_composition.ipynb`; if
that companion is ever archived, they become archive-only.

The `notebooks/data_processing` notebooks build the artifacts these results read:
`02_taxa_analysis_prep` (`prep.taxa_analysis_prep`, `prep.corpus`),
`03_screening_analysis_prep` (`prep.evidence_corpus_prep`), and
`04_biodiversity_evidence_corpus_prep` (`prep.evidence_corpus_prep`,
`prep.taxa_analysis_prep`, `prep.corpus`). The retired `01-climate-data-prep` notebook
and its outputs are kept together under `notebooks/data_processing/archive/`; its helper
is preserved in `notebooks/results/archive/retired-helpers/`.

`threats_supplementary.ipynb` is archived, not active.

## Build consistency-checking data

Run commands from the repository root. The reference workbooks and all output
locations are configured under `dataset_config` in `repo_config.json`.

### 1. Build the raw label CSVs

Build the L0 screening dataset:

```bash
python -m data_helpers.datasets.build_screening
```

Build every coding dataset from L1 through L6:

```bash
python -m data_helpers.datasets.build_coding
```

To rebuild only one coding level, pass a matching label fragment:

```bash
python -m data_helpers.datasets.build_coding l2
```

The builders:

- read the configured sheets from the reference screening and coding workbooks;
- retain rows containing the relevant label data;
- deduplicate records by `UT (Unique WOS ID)`;
- remove records without an abstract; and
- write one raw CSV beneath `data/labels/l0` through `data/labels/l6`.

### 2. Create train/dev/test splits

Split all configured label datasets:

```bash
python -m data_helpers
```

Run only selected labels or override the configured random seed:

```bash
python -m data_helpers --labels l0,l2,l5
python -m data_helpers --seed 123
```

Each label is split independently using its configured stratification column.
The default split is 60% train, 20% dev, and 20% test with seed 42.

Outputs are written below each configured label directory:

```text
data/labels/<label>/
├── train/
├── dev/
├── test/
└── in-process/
```

The `in-process/` directory records relevant audit information such as duplicate
rows, rows without abstracts, dropped rows, stratum counts, and
`split_summary.json`.

### 3. Draw manual consistency-check samples

Sample screening records from the L0 training split:

```bash
python -m data_helpers.datasets.sample_screening
```

Sample every coding level from L1 through L6:

```bash
python -m data_helpers.datasets.sample_coding
```

Sample only one coding level:

```bash
python -m data_helpers.datasets.sample_coding l4
```

The default sample size is 100 records per label. L0 is allocated across source
strata, while coding samples are allocated proportionally across each label’s
configured stratum. The samplers also write `sample_meta.json` with the seed,
source file, sample size, and stratum breakdown.

Final manual-review files are written to:

```text
data/consistency-check-datasets/screening/to-manual-label/
data/consistency-check-datasets/data-coding/to-manual-label/
```

## Relevant configuration

The consistency-data workflow reads these settings from `dataset_config` in
`repo_config.json`:

- reference workbook paths and sheet names;
- base bibliographic columns and label-specific columns;
- raw output paths for L0–L6;
- label stratification columns;
- train/dev/test ratios and random seed;
- label split directories;
- manual sample size; and
- manual-review output directories.

The prepared datasets are normally committed or distributed with the project,
so rerunning this workflow is mainly useful for reproducibility or when the
reference annotations change.

## Tests

Tests for this package live in `data_helpers/tests/` and run from the
repository root:

```bash
venv/bin/python -m pytest data_helpers
```

The analysis and plotting modules are covered module-by-module
(`test_taxa_skew.py`, `test_driver_realm.py`, and so on).
`test_results_source_boundaries.py` enforces the source boundary described
above by scanning `notebooks/results/*.ipynb` for direct raw-source access
(`build_merged_corpus`, `data/coding-*`, `data/gbif/`, and similar): results
notebooks must read the prepared stores rather than re-deriving the corpus.
