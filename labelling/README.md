# Labelling Package

This package runs the main screening and coding workflow for the repository. It takes a folder of WoS-style records, applies one labelling task, writes the run outputs, and can automatically run evals against the reference labels afterward.

In the normal repo workflow, this package is used on the prepared splits under `data/labels/`. It can also be used on other input folders, such as screened partitions or manual-review / consistency-check samples, as long as the expected input fields are present.

## Package layout

| File | Role |
| --- | --- |
| `orchestrator.py` | Main entry point. Loads an input folder, runs one labelling task, writes run outputs, and optionally triggers evals. |
| `src/config.py` | Resolves runtime settings and artifact paths from `repo_config.json` and the environment. |
| `src/data_loader.py` | Reads WoS-style `.xls`/`.xlsx`/`.csv` exports into normalized dataset JSON, with flexible column matching. |
| `src/tasks.py` | Prompt assembly, response schemas, and parsing for every screening and coding task. |
| `src/batching.py` | Splits a dataset into request batches. |
| `src/batch_api.py` | Submits and downloads OpenAI Batch API jobs. |
| `src/live_api.py` | Submits requests synchronously when `submission_mode=live`. |
| `process_screening.py` | Post-run: extracts eligible records from screening outputs into partitioned Excel files. |
| `process_coding.py` | Post-run: turns coding batch outputs into per-partition label tables, and hosts the `taxa-with-api` GBIF enrichment task. |
| `taxa_api.py` | Resolves standardized L6 taxa names against the GBIF species-match API, with release-aware SQLite caching, rate limiting, and resumable per-partition outputs. |
| `taxa_groups.py` | Validates and applies the configurable multi-resolution grouping rules over matched GBIF hierarchies. |
| `tests/` | Tests for `taxa_api.py` and `taxa_groups.py`. Run with `venv/bin/python -m pytest labelling`. |

## Quick use

Before running:

- provide `OPENAI_API_KEY` through your shell environment or `.env`
- for the standard reproducibility workflow, make sure the prepared `data/labels/` splits are already present as described in the [root README](../README.md)

Run from the repo root:

```bash
python labelling/orchestrator.py <input_dir> <run_name> --task <task>
```

Example:

```bash
python labelling/orchestrator.py data/labels/l1/train l1_train_170426_f1 --task driver
```

To override the configured batch size for a single run:

```bash
python labelling/orchestrator.py data/labels/l1/train l1_train_170426_f1 --task driver --batch-size 5000
```

In plain English, this command:

- loads the `l1` train split from `data/labels/l1/train`
- runs the `driver` task on every record in that folder
- writes outputs under the run name `l1_train_170426_f1`
- then, if enabled in `checklists/mappings/repo_config.json`, runs evals against the reference labels

## Inputs

`input_dir` should be a folder containing `.xls`, `.xlsx`, or `.csv` WoS-style export files.

Common input locations in this repo include:

- `data/labels/l{0-6}/{train|dev|test}` for the prepared label splits
- `data/partitions-mock/...` for lightweight end-to-end checks
- manual-review, consistency-check, or screening-derived folders for custom runs

The loader requires a document ID column and accepts these common variants:

- `UT`
- `ut`
- `UT (Unique WOS ID)`
- `custom_id`

It also reads common metadata fields using flexible matching, including:

- title
- abstract
- authors
- publisher (stored as `source` in the normalized dataset)
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

## Post-run processing

The orchestrator writes model-response JSONL outputs. Two companion scripts turn those
outputs into the tabular partitions that the corpus builders in `data_helpers`
read. Both accept run names directly or through `--run-list`, and both support
`--print-missing` and `--skip-missing` for incomplete runs. When run names are
omitted, `process_coding.py` defaults to
`checklists/mappings/run_names.json`; `process_screening.py` requires either
positional run names or an explicit `--run-list`.

### Extract eligible records from screening runs

```bash
PYTHONPATH=. venv/bin/python labelling/process_screening.py \
  --run-list checklists/mappings/run_names.json \
  --run-key screening \
  --output-dir screened-partitions
```

`PYTHONPATH=.` makes both the package-local `src` modules and the repo-level
`evals_local` package importable with the script's current import layout.

This combines the named screening runs, fails loudly on duplicate `UT`s across
runs, and writes into `data/<output-dir>/`:

- `all/screening_all.csv` — every screened record with its stage scores and labels;
- `eligible/<n>/wos_<n>_<max>-<min>.xlsx` — eligible records only, partitioned at
  `--batch-size` (default 400,000) and named by publication-year range;
- `metadata.json` — per-run and total counts, plus the run list used; and
- `eligible/partition_metadata.json` — the eligible-partition manifest used by
  downstream corpus processing.

The `eligible/` partitions are the normal input folders for the L1–L6 coding runs.

### Build coding label tables

```bash
venv/bin/python labelling/process_coding.py --task driver
```

`--task` accepts `driver`, `threats` (or `threats_l0`/`_l1`/`_l2`), `geography`,
`ecosystems` (or `ecosystems_realm`/`_biome`/`_efg`), `study`, `taxa`, and
`taxa-with-api`. Outputs default to `data/coding-<task>/` (`data/coding-taxa/`
for `taxa-with-api`); override with `--output-dir`. The composite `threats` and
`ecosystems` tasks write all their levels in one pass, treating the optional
deeper levels as non-required.

### Build API-enriched taxa and broad groups

After the L6 batch outputs exist, resolve their standardized canonical names
against GBIF and write the enriched hierarchy under `data/coding-taxa`:

```bash
venv/bin/python labelling/process_coding.py --task taxa-with-api
```

The task writes XLSX partition checkpoints, combined CSV/Parquet tables, a
lossless lineage table, and grouping/inventory audits. Groups are assigned per
matched taxon item using
[`taxa_broad_groups.json`](../checklists/mappings/taxa_broad_groups.json), then
de-duplicated at the publication level into three ordered JSON-list columns:

- `broad_taxa_groups`: six headline groups;
- `taxa_analysis_groups`: nine compact analysis groups; and
- `taxa_detail_groups`: fourteen detailed analysis groups.

The same mapping stores fixed colors and one small representative clipart asset
for every label. `group_clipart` maps labels to reusable `clipart_assets`
records containing the source page, direct SVG/thumbnail links, license, and
attribution. Organism silhouettes are CC0 PhyloPic assets; Unresolved uses a
question-mark symbol rather than implying a taxonomic identity.

These columns do not change the data grain: every output remains one row per
`UT`. The item-level assignments and matching rules remain auditable in
`taxa_match_status_json` and the lineage output.

To rebuild outputs only from the existing release-aware SQLite cache, with all
GBIF requests disabled:

```bash
venv/bin/python labelling/process_coding.py --task taxa-with-api --cached-only
```

This mode fails before any lookup request if a required canonical name is absent
from the cache. Completed partitions are reusable only when the input,
taxonomy-build identity, pipeline schema, and grouping-config hash all match.

The remaining `taxa-with-api` options tune the GBIF request loop and cache. They
have no effect on any other task:

| Flag | Default | Purpose |
| --- | --- | --- |
| `--api-workers` | `4` | Concurrent GBIF request workers. |
| `--api-rate-limit` | `8.0` | Maximum request starts per second across workers. |
| `--api-timeout` | `5.0` | Connect and read timeout, in seconds. |
| `--api-max-attempts` | `4` | Attempts per transiently failing request. |
| `--api-retry-delay` | `5.0` | Delay between transient attempts, in seconds. |
| `--api-user-agent` | `biodiversity-evidence-synthesis/taxa-with-api` | User-Agent sent to GBIF. |
| `--force` | off | Rebuild completed partition files; cached matches are still reused. |
| `--refresh-api-cache` | off | Ignore cached matches and request every taxon again. |
| `--taxa-group-config` | `checklists/mappings/taxa_broad_groups.json` | Grouping-rule JSON to apply. |
| `--retry-final-failures` / `--no-retry-final-failures` | on | Enable or disable retrying cached terminal failures on a later invocation. |

## Outputs and evals

All run outputs are written under:

`<repo_config.orchestrator.paths.batch_outputs_dir>/<run_name>/`

With `submission_mode=batch`, every task downloads raw Batch API response
envelopes. With `submission_mode=live`, simple tasks (`screen`, `driver`,
`geography`, `study`, `taxa`) write batch-shaped response envelopes, while the
multi-step `threats_*` and `ecosystems_*` tasks write normalized parsed stage
records. The downstream loaders support both representations.

Evals run automatically after each task if `orchestrator.run_evals=true`.

Eval outputs are written under:

`<repo_config.evals.output_dir>/<run_name>/`

That folder typically contains:

- `data/` for joined truth and prediction outputs
- `metrics/` for metric files by truth column

For screening runs, automatic evals read the truth labels from `input_dir` directly. For the other tasks, evals resolve truth labels from `evals.labels_dir` in `checklists/mappings/repo_config.json`.

If no ground-truth labels are found, evals do not block the run. Set `orchestrator.run_evals=false` in `checklists/mappings/repo_config.json` if you want to skip evals entirely.

## Environment

Runtime defaults are controlled through [`checklists/mappings/repo_config.json`](../checklists/mappings/repo_config.json).
`OPENAI_API_KEY` remains environment-provided because it is a secret.

Key settings:

| Location                               | Key                            | Description                                                                                              |
| -------------------------------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------- |
| `checklists/mappings/repo_config.json` | `orchestrator.submission_mode` | `live` or `batch`; both are supported, but `batch` is the recommended default when you want to save cost |
| `checklists/mappings/repo_config.json` | `orchestrator.run_evals`       | Set `false` to skip automatic evals                                                                      |
| `checklists/mappings/repo_config.json` | `orchestrator.limit_docs`      | Cap documents per run (`null` for all)                                                                   |
| `checklists/mappings/repo_config.json` | `orchestrator.batch_size`      | Documents per JSONL batch; override per run with `--batch-size`                                          |

## Notes

- This README focuses on the normal workflow used in this repo.
- The root [README](../README.md) explains how this package fits into the full project flow.
- [`evals_local/README.md`](../evals_local/README.md) covers standalone eval usage in more detail.
- [`checklists/repo-readmes/others/taxa-grouping-and-benchmark.md`](../checklists/repo-readmes/others/taxa-grouping-and-benchmark.md) is the canonical specification for the taxon grouping rules and the GBIF described-diversity benchmark that `taxa-with-api` feeds.
- Run the package tests with `venv/bin/python -m pytest labelling`.
