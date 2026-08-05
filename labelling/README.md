# Labelling Package

This package runs the LLM screening and coding workflow at the heart of the
repository. It reads a folder of Web-of-Science (WoS) style export files, sends
every record through one labelling task (screening, or one of the L1-L6 coding
tasks), writes the raw model outputs, and — if enabled — evaluates them against
reference labels.

In the normal repo workflow it runs against the prepared splits under
`data/labels/` (see the [root README](../README.md)). It can also run against
any other folder of WoS-style files with the same input requirements —
full corpus partitions, consistency-check samples, or manual-review folders.

## Package layout

| Path | Role |
| --- | --- |
| `orchestrator.py` | Entry point. Loads an input folder, runs one task, writes outputs, optionally triggers evals. |
| `src/config.py` | Reads `repo_config.json` and resolves runtime settings + artifact paths. |
| `src/data_loader.py` | Reads `.xls`/`.xlsx`/`.csv` WoS exports into normalized document JSON, with flexible column matching. |
| `src/tasks.py` | Every task's prompt assembly, response schema, and output parsing. |
| `src/batching.py` | Splits documents into request batches. |
| `src/batch_api.py` | Builds requests, and submits/polls/downloads OpenAI Batch API jobs. |
| `src/live_api.py` | Sends requests synchronously to the OpenAI Responses API (`submission_mode=live`). |
| `process_screening.py` | Post-run: turns screening outputs into eligible-record partitions. |
| `process_coding.py` | Post-run: turns coding outputs into per-partition label tables; also hosts `taxa-with-api`. |
| `taxa_api.py` | Resolves L6 taxa names against the GBIF species-match API (cached, rate-limited, resumable). |
| `taxa_groups.py` | Applies the configurable multi-resolution taxon grouping rules. |
| `tests/` | Tests for `taxa_api.py` / `taxa_groups.py`. Run with `venv/bin/python -m pytest labelling`. |

## Setup

- Provide `OPENAI_API_KEY` via `.env` or the shell environment.
- Runtime defaults (model, reasoning effort, batch size, submission mode, eval
  toggle, artifact paths) all live in
  [`checklists/mappings/repo_config.json`](../checklists/mappings/repo_config.json)
  under the `orchestrator` and `evals` keys — nothing else needs editing to run
  a task.

## Running a task

Every run is one command from the repo root:

```bash
python labelling/orchestrator.py <input_dir> <run_name> --task <task>
```

- `input_dir` — a folder of `.xls`/`.xlsx`/`.csv` WoS exports. The loader needs
  a document-ID column (`UT`, `ut`, `UT (Unique WOS ID)`, or `custom_id`) and
  picks up title/abstract/authors/publisher/year/WoS-categories/DOI by
  flexible name matching.
- `run_name` — tags the dataset, batch files, outputs, and eval artifacts for
  this run. Reuse the same name across the steps of a multi-step task (see L2
  / L4 below) so later steps can find earlier output.
- `--task` — one of the task names below. `--model`, `--reasoning`, and
  `--batch-size` override the config defaults for a single run.

Quick-start example, run against the repo's prepared training split:

```bash
python labelling/orchestrator.py data/labels/l1/train l1_train_170426_f1 --task driver
```

## Screening (L0)

```bash
python labelling/orchestrator.py data/partitions/1 partition_1_l0_f1 --task screen --reasoning medium
```

This is a real command from a full-corpus run
([`checklists/repo-readmes/data-corpus-execution/screening-task-l0.md`](../checklists/repo-readmes/data-corpus-execution/screening-task-l0.md)):
`data/partitions/1` holds one partition of the WoS export, and the run writes
eligibility scores/labels for every record in it.

## Coding tasks (L1-L6)

| Label | Task name(s) | Depends on | Typical reasoning |
| --- | --- | --- | --- |
| L1 | `driver` | — | `low` |
| L2 | `threats_l0` → `threats_l1` → `threats_l2` | each previous step | `medium` |
| L3 | `geography` | — | `low` |
| L4 | `ecosystems_realm` → `ecosystems_biome` → `ecosystems_efg` | each previous step | `high` |
| L5 | `study` | — | `low` |
| L6 | `taxa` | — | `high` |

For L2 and L4, run the steps in order with the same `run_name` throughout.
Example, from the full-corpus L1 and L6 execution logs
([`coding-task-l1.md`](../checklists/repo-readmes/data-corpus-execution/coding-task-l1.md),
[`coding-task-l6.md`](../checklists/repo-readmes/data-corpus-execution/coding-task-l6.md)):

```bash
python labelling/orchestrator.py data/screened-partitions/eligible/1 coding_l1_partition_1_f1 --task driver --reasoning low
python labelling/orchestrator.py data/screened-partitions/eligible/1 coding_l6_partition_1_f1 --task taxa --reasoning high
```

`data/screened-partitions/eligible/` is produced by the L0 post-processing
step below.

## Batch vs. live submission

Submission mode is not a CLI flag — it's the `orchestrator.submission_mode`
key in `repo_config.json`, set to `batch` or `live`, and it applies to every
run until changed:

- **`batch`** (repo default) — submits an OpenAI Batch API job per request
  file, polls until complete, and downloads the raw response envelopes. Cheaper,
  but not instant.
- **`live`** — sends requests synchronously to the Responses API. Simple tasks
  (`screen`, `driver`, `geography`, `study`, `taxa`) write batch-shaped
  response envelopes; the multi-step `threats_*`/`ecosystems_*` tasks write
  normalized per-stage records instead. Useful for small or urgent runs.

Both modes write to the same place and both are read by the same downstream
loaders, so switching modes doesn't change anything downstream of the run.

## Post-processing model outputs

The orchestrator only writes raw model-response JSONL. Two scripts turn that
into the tabular partitions `data_helpers` builds the analysis corpus from.
Both take run names positionally or via `--run-list <json> --run-key <key>`,
and both support `--print-missing` / `--skip-missing` for incomplete runs.

**Extract eligible records from screening runs:**

```bash
python labelling/process_screening.py \
  --run-list checklists/mappings/run_names.json \
  --run-key screening \
  --output-dir screened-partitions
```

Combines the named screening runs, fails on duplicate `UT`s across runs, and
writes into `data/screened-partitions/`: `all/screening_all.csv` (every
screened record), `eligible/<n>/wos_<n>_<max>-<min>.xlsx` (eligible records,
partitioned by `--batch-size`, default 400,000), plus `metadata.json` and a
partition manifest. `eligible/` is the input for the L1-L6 coding runs above.

**Build a coding task's label table:**

```bash
python labelling/process_coding.py --task driver
```

`--task` accepts `driver`, `threats` (folds `threats_l0/l1/l2` into one pass),
`geography`, `ecosystems` (folds the three ecosystem levels), `study`, `taxa`,
and `taxa-with-api`. Writes to `data/coding-<task>/`: one file per input
partition, `all/<task>_all.csv` combined, and `metadata.json`.

`taxa-with-api` additionally resolves L6's standardized names against GBIF and
writes the enriched hierarchy plus broad-group assignments to
`data/coding-taxa/`. It has its own set of GBIF request/cache flags (workers,
rate limit, `--cached-only`, `--force`, `--refresh-api-cache`, ...) — see
`process_coding.py --help` for the full list, and
[`checklists/repo-readmes/others/taxa-grouping-and-benchmark.md`](../checklists/repo-readmes/others/taxa-grouping-and-benchmark.md)
for what the grouping rules and benchmark mean.

## Outputs and evals

Raw run outputs land under `<orchestrator.paths.batch_outputs_dir>/<run_name>/`
(default `data/artifacts/batch_outputs/`). If `orchestrator.run_evals=true`,
each run is automatically scored against reference labels afterward, writing
to `<evals.output_dir>/<run_name>/` (default `data/labels/eval/`). Screening
evals read truth from `input_dir` directly; other tasks read from
`evals.labels_dir`. Missing ground truth doesn't block the run — see
[`evals_local/README.md`](../evals_local/README.md) for the eval workflow
itself.

## See also

- [Root README](../README.md) — how this package fits into the full project.
- [`evals_local/README.md`](../evals_local/README.md) — standalone eval usage.
- [`checklists/repo-readmes/data-corpus-execution/`](../checklists/repo-readmes/data-corpus-execution/) — full execution logs (command history) for every screening/coding level.
- [`checklists/repo-readmes/others/taxa-grouping-and-benchmark.md`](../checklists/repo-readmes/others/taxa-grouping-and-benchmark.md) — taxon grouping rules and the GBIF benchmark.
- Run the package tests: `venv/bin/python -m pytest labelling`.
