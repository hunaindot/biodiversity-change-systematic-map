# Labelling Package

Runs classification tasks against the OpenAI API (live or batch mode), writes JSONL outputs, and optionally runs evals automatically.

## Quick start

```bash
python -m labelling.orchestrator <input_dir> <run_name> --task <task>
```

- `input_dir` — directory containing WoS export files (`.xls`, `.xlsx`, or `.csv`; all matching files are combined)
- `run_name` — name tag applied to all output files for this run
- `--task` — task to run (see table below; defaults to `driver`)

## Available tasks

All tasks are single-turn API calls and support both live and batch mode.

| Task | Alias(es) | What it classifies | Depends on |
|---|---|---|---|
| `driver` | `drivers`, `direct_driver` | Direct biodiversity drivers (L1) | — |
| `screening` | `screen`, `eligibility` | Paper eligibility (ELIGIBLE / NOT_ELIGIBLE) | — |
| `geography` | `geo`, `region` | Geographic scope, region, sub-region, country | — |
| `taxa` | — | Taxonomic ranks (kingdom → genus, species) | — |
| `study` | `studies` | Study design type | — |
| `threats_l0` | — | Top-level threats (L0) | — |
| `threats_l1` | — | L1 threats — builds candidates from L0 labels | `threats_l0` |
| `threats_l2` | — | L2 threats — builds candidates from L0 + L1 labels | `threats_l1` |
| `ecosystems_realm` | `ecosystem_realm` | Realm classification | — |
| `ecosystems_biome` | `ecosystem_biome` | Biome classification — builds candidates from realm labels | `ecosystems_realm` |
| `ecosystems_efg` | `ecosystem_efg` | EFG classification — builds candidates from realm + biome labels | `ecosystems_biome` |

Dependent tasks read the prior level's outputs from `batch_outputs/<run_name>/` and reconstruct the conversation as a self-contained prompt — no server-side response chaining. Requests are sorted by candidate names before submission for prompt-cache locality.

**Threat run order** (same `run_name` required across all three):
```bash
python -m labelling.orchestrator <input_dir> <run_name> --task threats_l0
python -m labelling.orchestrator <input_dir> <run_name> --task threats_l1
python -m labelling.orchestrator <input_dir> <run_name> --task threats_l2
```

**Ecosystem run order** (same `run_name` required across all three):
```bash
python -m labelling.orchestrator <input_dir> <run_name> --task ecosystems_realm
python -m labelling.orchestrator <input_dir> <run_name> --task ecosystems_biome
python -m labelling.orchestrator <input_dir> <run_name> --task ecosystems_efg
```

## Evals

Evals run automatically after a task completes (both live and batch), unless disabled. They compare model outputs against ground-truth labels and write metrics to disk.

**Output location:** `$EVALS_OUTPUT_DIR/<run_name>/`
- `data/` — joined truth + prediction CSV per task
- `metrics/` — metric files per truth column

**Control via `.env`:**
- `ORCHESTRATOR_RUN_EVALS=false` — skip evals entirely
- For the `screening` task, ground-truth labels are read from `input_dir` (the same folder as the input files); all other tasks look up labels from their configured label path

Evals will silently no-op if no ground-truth labels are found for the run — they don't block or fail the pipeline.

## Output format

**`driver`, `screening`, `geography`, `taxa`, `study`** — raw OpenAI response envelope:
```json
{"custom_id": "...", "response": {"body": {"output": [...]}}}
```

**`threats_*` and `ecosystems_*`** — parsed record with labelling metadata:
```json
{
  "custom_id": "...",
  "response_text": "<raw model output>",
  "results_payload": {"results": ["Label A", "Label B"], "stop_reason": "continue"},
  "candidates_passed": [{"name": "...", "desc": "..."}, ...],
  "error": null
}
```

## Output file naming

All outputs land in `batch_outputs/<run_name>/`:

| Task | Output file pattern |
|---|---|
| `driver`, `screening`, `geography`, `taxa`, `study` | `<task>-<request_stem>.jsonl` |
| `threats_l0/l1/l2` | `threats_l0-<request_stem>.jsonl` etc. |
| `ecosystems_realm/biome/efg` | `ecosystems_realm-<request_stem>.jsonl` etc. |

The level-specific prefix (`threats_l0-`, `ecosystems_biome-`, etc.) is what lets the next level in the chain find the right files when building candidates.

## Environment variables

Configured via `.env` in the repo root.

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `ORCHESTRATOR_MODEL` | Model to use (e.g. `o4-mini`) |
| `ORCHESTRATOR_REASONING` | Reasoning effort (`low`, `medium`, `high`) |
| `ORCHESTRATOR_BATCH_OUTPUTS_DIR` | Where outputs are written |
| `ORCHESTRATOR_BATCHES_DIR` | Where request JSONL files are staged |
| `ORCHESTRATOR_DATASETS_DIR` | Where parsed document datasets are saved |
| `ORCHESTRATOR_MAPPINGS_DIR` | Location of taxonomy/typology mapping JSON files |
| `ORCHESTRATOR_PROMPTS_DIR` | Location of prompt config JSON files |
| `ORCHESTRATOR_LIMIT_DOCS` | Max documents to process (default 500, `None` for all) |
| `ORCHESTRATOR_BATCH_SIZE` | Documents per batch file (default 100) |
| `ORCHESTRATOR_RUN_OPENAI` | Set `false` to skip API submission (dry run) |
| `ORCHESTRATOR_RUN_EVALS` | Set `false` to skip automatic evals after run |
| `ORCHESTRATOR_SUBMISSION_MODE` | Submission mode: `live` (default) or `batch` |
| `ORCHESTRATOR_TASK` | Default task if `--task` is not passed |
| `PROMPT_KEY_*` | Prompt config keys for each task (e.g. `PROMPT_KEY_THREATS`) |
