# Biodiversity Labelling Pipeline

Command-line pipeline for turning Web of Science (WoS) Excel exports into OpenAI-ready classification jobs with reusable batches, prompts, and mapping lookups. The code lives under `labelling/` and writes all artifacts to `labelling/artifacts/`.

## Prerequisites
- Python 3.11+ (a ready-made env exists at `venv/`); install deps with `pip install -r labelling/requirements.txt`.
- WoS `.xls/.xlsx` exports containing the column `UT (Unique WOS ID)` plus the usual metadata (title, abstract, authors, year, DOI, WoS Categories).
- An OpenAI API key exported as `OPENAI_API_KEY`. Other env toggles live in `.env` (see below); avoid committing secrets.

## Environment toggles (defaults shown)
- `ORCHESTRATOR_LIMIT_DOCS=500` — cap documents ingested; use `none` to disable.
- `ORCHESTRATOR_BATCH_SIZE=100` — lines per batch JSONL.
- `ORCHESTRATOR_MODEL=gpt-5-nano-2025-08-07`
- `ORCHESTRATOR_REASONING=low`
- `ORCHESTRATOR_RUN_OPENAI=true` — set to `false` to only build request files.
- `ORCHESTRATOR_SUBMISSION_MODE=live|batch` — batch submits to `/v1/responses` via the batches API; live streams requests one-by-one.
- `ORCHESTRATOR_TASK` — fallback task name if `--task` is omitted.
- `ORCHESTRATOR_PROMPTS_FILE` — optional override for `mappings/prompts_zero.json`.

## Mappings and prompts
- `mappings/prompts_zero.json` — prompt + output schema for all tasks (driver, geography, taxa, study, ecosystems, threats).
- `mappings/ipbes_drivers.json`, `ipbes_regions.json`, `habitats_classification.json`, `study_types.json` — reference lookups used in prompts.
- `mappings/threats_classification.json` — required for the multi-stage threats workflow.
- `mappings/ecosystem_typology_1_3.json` — required for the multi-stage ecosystems workflow.

## How to run
1) Activate the env and set your key:
```bash
source venv/bin/activate
export OPENAI_API_KEY=sk-...
```
2) Point the orchestrator at a folder of WoS Excel files and choose a run name:
```bash
python labelling/orchestrator.py data/wos-data/2025 p25 --task driver
```
   Arguments:
   - `input_dir`: folder containing `.xls/.xlsx`.
   - `run_name`: label used for all artifacts.
   - `--task/-t`: one of `driver` (default), `geography`, `taxa`, `study`, `ecosystems` (live only), `threats` (live only).

3) What you get:
   - Combined dataset: `labelling/artifacts/datasets/<run_name>-dataset.json`
   - Batches: `labelling/artifacts/batches/<run_name>/data/*.jsonl`
   - Request files: `labelling/artifacts/batches/<run_name>/request/*.jsonl`
   - Live outputs (if `ORCHESTRATOR_SUBMISSION_MODE=live`): `labelling/artifacts/batch_outputs/<run_name>/<task>-*.jsonl`
   - Batch submissions (if `submission_mode=batch`): batch IDs are printed to stdout; fetch later with `openai_batches.download_batch_output`.

4) Offline / dry-run: set `ORCHESTRATOR_RUN_OPENAI=false` to only build datasets, batches, and request files; you can submit them later.

## Task-specific run examples
- Driver (default, batch submit): `python labelling/orchestrator.py data/wos-data/2025 p25 --task driver --submission_mode batch`
- Geography (live submit): `python labelling/orchestrator.py data/wos-data/2025 p25-geo --task geography --submission_mode live`
- Taxa (batch): `python labelling/orchestrator.py data/wos-data/2025 p25-taxa --task taxa --submission_mode batch`
- Study type (batch): `python labelling/orchestrator.py data/wos-data/2025 p25-study --task study --submission_mode batch`
- Ecosystems (live only): `python labelling/orchestrator.py data/wos-data/2025 p25-eco --task ecosystems --submission_mode live`
- Threats (live only): `python labelling/orchestrator.py data/wos-data/2025 p25-threats --task threats --submission_mode live`

## Tasks at a glance
- Driver, Geography, Taxa, Study — support batch or live submission; use the standard prompt schema.
- Ecosystems — live-only three-stage realm→biome→EFG flow; requires the ecosystem typology mapping file.
- Threats — live-only three-stage threat_l0→threat_l1→threat_l2 flow; uses `threats_classification.json`.

## Run-name conventions (helps when joining outputs later)
- `p<number>` — production WoS pulls (e.g., `p24` for the 24th run). Keep consistent across dataset/batches/batch_outputs.
- `wos-YYYY-q` — quarter-labeled pulls from the WoS source folders (matches existing `wos-2025-1..4` runs).
- `l<number>-<date>` — lightweight/local experiments; include ISO-ish date (`l1-05-01-2026`) to avoid collisions.
- `*-prompt-v<number>` — prompt-tuning experiments; keep the base run name (`l1`) and bump `v` when the prompt changes.
- Task suffixes when splitting the same source: append `-geo`, `-taxa`, `-study`, `-eco`, `-threats` (e.g., `p25-geo`, `p25-eco`).
- Keep the same base name when you intend to join results (dataset, request, and outputs) later; only the suffix should differ per task.

## Looking at past runs
- Datasets: `labelling/artifacts/datasets/` (e.g., `p24-dataset.json`).
- Batch manifests: `labelling/artifacts/batches/<run>/manifest.json` (counts, paths, timestamps).
- Sample live/batch outputs: see `labelling/artifacts/batch_outputs/l1-prompt-v4/` (batch output JSONL) or `.../p3/`, `.../p4/` for driver live runs. These files show the expected response shape for downstream parsing.

## Troubleshooting
- If you see “UT column not found,” confirm the WoS export includes `UT (Unique WOS ID)` and re-run.
- For very large exports, lower `ORCHESTRATOR_BATCH_SIZE` to keep individual request files manageable.