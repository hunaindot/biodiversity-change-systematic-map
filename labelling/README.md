# Labelling package for screening and coding literature

This package automates the screening and coding of literature for the Biodiversity Change Systematic Map. It reads the title and abstract of each record and applies the project prompts.

Screening checks whether a record reports biodiversity change, its direction, a direct anthropogenic driver, and a link between the driver and the change. The full criteria and decision rules are in the [screening prompt](../checklists/prompts/screen.md).

Eligible records can then be coded for:

- [IPBES direct drivers (L1)](../checklists/prompts/classify_direct_driver.md)
- [IUCN threats (L2)](../checklists/prompts/classify_threats.md)
- [geographic scope (L3)](../checklists/prompts/classify_region.md)
- [Global Ecosystem Typology (L4)](../checklists/prompts/classify_ecosystem_typology.md)
- [study attributes (L5)](../checklists/prompts/classify_study.md)
- [taxa (L6)](../checklists/prompts/classify_taxa.md)

These links point to the prompts used by the code. They are also the best place to understand exactly how screening and coding decisions are made.

## Quick test

Run commands from the repository root. After installing the dependencies and adding `OPENAI_API_KEY` to `.env`, try:

```bash
python labelling/orchestrator.py data/labels/l1/train l1_train_test --task driver
```

This command reads the provided L1 training data, codes its records for direct drivers, and saves everything under the run name `l1_train_test`.

## Provided data

The repository includes [training, development, and test data](../data/labels/) for screening (`l0`) and all six coding tasks (`l1` to `l6`).

For example:

```text
data/labels/l1/train/
data/labels/l1/dev/
data/labels/l1/test/
```

Input folders may contain `.csv`, `.xls`, or `.xlsx` files. To run the pipeline, each record needs these three fields:

| Required field | Accepted column names | Why it is needed |
| --- | --- | --- |
| Record ID | `UT`, `ut`, `UT (Unique WOS ID)`, or `custom_id` | Connects each model response to the original record and removes duplicate records |
| Article title | `Article Title`, `article_title`, `Title`, or `title` | Passed to the model as part of the article text |
| Abstract | `Abstract` or `abstract` | Passed to the model as part of the article text |

The title and abstract are the only article text sent to the model. Other fields, such as authors, publisher, publication year, Web of Science categories, and DOI, are optional and are not used to make the labelling decision.

The files under `data/labels/` also contain reference-label columns. These are needed only when evaluating predictions against existing labels; they are not needed when screening or coding new records.

## What a run saves

Every run keeps the intermediate data as well as the model responses. This makes it possible to inspect what was sent and returned for each record.

With the default paths, a run named `l1_train_test` writes:

```text
data/artifacts/datasets/l1_train_test-dataset.json
data/artifacts/batches/l1_train_test/
data/artifacts/batch_outputs/l1_train_test/
```

The dataset file contains the normalized input. The batches folder contains a manifest, the input batches, and the API request files. The batch outputs folder contains the raw model responses. Each request and response keeps the record ID as `custom_id`, so an output can be traced back to its input.

If evaluations are enabled, results are also written to:

```text
data/labels/eval/l1_train_test/
```

## Available tasks

The value in the **Run key** column is passed to `--task`.

| Level | What it does | Run key | Prompt |
| --- | --- | --- | --- |
| L0 | Decides whether a record meets the screening criteria | `screening` | [Screening](../checklists/prompts/screen.md) |
| L1 | Assigns broad IPBES direct drivers | `driver` | [Direct drivers](../checklists/prompts/classify_direct_driver.md) |
| L2 | Assigns the three levels of the IUCN threat hierarchy | `threats_l0`, then `threats_l1`, then `threats_l2` | [Core rules](../checklists/prompts/classify_threats_core.md), [L0](../checklists/prompts/classify_threats.md), [L1](../checklists/prompts/classify_threats_l1.md), [L2](../checklists/prompts/classify_threats_l2.md) |
| L3 | Extracts country, IPBES sub-region and IPBES region | `geography` | [Geography](../checklists/prompts/classify_region.md) |
| L4 | Assigns Global Ecosystem Typology realm, biome and ecosystem functional group | `ecosystems_realm`, then `ecosystems_biome`, then `ecosystems_efg` | [Core rules](../checklists/prompts/classify_ecosystem_typology_core.md), [realm](../checklists/prompts/classify_ecosystem_typology_realm.md), [biome](../checklists/prompts/classify_ecosystem_typology_biome.md), [EFG](../checklists/prompts/classify_ecosystem_typology_efg.md) |
| L5 | Codes study design, methods, comparisons and taxonomic focus | `study` | [Study attributes](../checklists/prompts/classify_study.md) |
| L6 | Extracts the taxa studied in the record | `taxa` | [Taxa](../checklists/prompts/classify_taxa.md) |

L2 and L4 are hierarchical tasks. Run their three steps in order and use the same run name for every step. A later step reads the earlier output and limits the labels to valid children of the selected parent labels.

For example:

```bash
python labelling/orchestrator.py data/labels/l2/dev l2_dev_test --task threats_l0
python labelling/orchestrator.py data/labels/l2/dev l2_dev_test --task threats_l1
python labelling/orchestrator.py data/labels/l2/dev l2_dev_test --task threats_l2
```

Short aliases such as `screen`, `drivers`, `geo`, and `region` are accepted, but the run keys in the table are clearer for saved commands and logs.

## Running your own data

The general command is:

```bash
python labelling/orchestrator.py <input_dir> <run_name> --task <run_key>
```

- `input_dir` is a folder containing the input files.
- `run_name` identifies the saved dataset, requests, responses, and evaluation.
- `--task` selects one task from the table above.

Use a new, descriptive run name for a new dataset or experiment. Reuse that name only for the successive stages of L2 or L4.

## API and run options

Non-secret defaults are in [`checklists/mappings/repo_config.json`](../checklists/mappings/repo_config.json), under `orchestrator`. The API key is the exception: set `OPENAI_API_KEY` in `.env` or in the shell environment.

| Option | Current default | Where to set it | Meaning |
| --- | --- | --- | --- |
| Model | `gpt-5-nano-2025-08-07` | `orchestrator.model` or `--model` | OpenAI model used for the run |
| Reasoning effort | `medium` | `orchestrator.reasoning` or `--reasoning` | Reasoning effort sent with each request |
| Request batch size | `10000` records | `orchestrator.batch_size` or `--batch-size` | Number of records written to each request file |
| Submission mode | `batch` | `orchestrator.submission_mode` | Use `batch` for the Batch API or `live` for synchronous Responses API calls |
| Document limit | `null` | `orchestrator.limit_docs` | Limit the records loaded; `null` means all records |
| Run evaluations | `false` | `orchestrator.run_evals` | Evaluate outputs after a completed run |

`--model`, `--reasoning`, and `--batch-size` change one command only. The values in `repo_config.json` remain the defaults for later runs. `submission_mode`, `limit_docs`, and `run_evals` are config-only options.

Both submission modes use the OpenAI Responses API and produce outputs that the same downstream scripts can read:

- `batch` submits request files through the Batch API, waits for completion, and downloads the responses. This is the repository default.
- `live` sends the requests synchronously. It is useful for small checks where an immediate response matters more than batch pricing.

The artifact locations can also be changed under `orchestrator.paths` in the same [run configuration](../checklists/mappings/repo_config.json). The defaults are `data/artifacts/datasets`, `data/artifacts/batches`, and `data/artifacts/batch_outputs`. Evaluation label and output paths are under the `evals` section.

## Turning raw responses into tables

The orchestrator saves raw JSONL responses. After screening the full corpus, combine the named runs and write the eligible records with:

```bash
python labelling/process_screening.py \
  --run-list checklists/mappings/run_names.json \
  --run-key screening \
  --output-dir screened-partitions
```

This writes all screening decisions to `data/screened-partitions/all/` and the eligible records to `data/screened-partitions/eligible/`. The eligible folders can then be used as input for L1–L6.

After a coding run, build its table with:

```bash
python labelling/process_coding.py --task driver
```

The accepted processing tasks are `driver`, `threats`, `geography`, `ecosystems`, `study`, `taxa`, and `taxa-with-api`. Outputs are written under `data/coding-<task>/`, including one file per input partition, a combined CSV in `all/`, and `metadata.json`.

`taxa-with-api` additionally checks taxon names against GBIF and assigns broad taxonomic groups. 

## More detail

- [Evaluation README](../evals_local/README.md) explains the metrics and how to run evaluations separately.
- [Full-corpus execution logs](../checklists/repo-readmes/data-corpus-execution/) record the commands used for the final screening and coding runs.
- [Systematic mapping protocol](https://doi.org/10.57808/proceed.2026.31) This is registered protocol contain further details on the purpose of these screening and coding tasks for the systematic map.
