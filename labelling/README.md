# Labelling Package

Runs classification tasks against the OpenAI API (live or batch mode), writes JSONL outputs, and optionally runs evals automatically.

## Quick start

```bash
python -m labelling.orchestrator <input_dir> <run_name> -t <task> [-s live|batch]
```

- `input_dir` — directory containing WoS `.xls` export files
- `run_name` — name tag applied to all output files for this run
- `-t` / `--task` — task to run (see table below; defaults to `driver`)
- `-s` / `--submission-mode` — `live` (default) or `batch`

## Available tasks

### Simple tasks (single-turn, batch supported)

| Task name | Alias(es) | What it classifies |
|---|---|---|
| `driver` | `drivers`, `direct_driver` | Direct biodiversity drivers (L1) |
| `screening` | `screen`, `eligibility` | Paper eligibility (ELIGIBLE / NOT_ELIGIBLE) |
| `geography` | `geo`, `region` | Geographic scope, region, sub-region, country |
| `taxa` | — | Taxonomic ranks (kingdom → genus, species) |
| `study` | `studies` | Study design type |

### Threat tasks

| Task name | Mode | Description |
|---|---|---|
| `threats_l0` | live + **batch** | L0 threat classification only (article → top-level threats) |
| `threats_l1` | live + **batch** | L1 threats — reads `threats_l0` outputs from same run, builds L1 candidates |
| `threats_l2` | live + **batch** | L2 threats — reads `threats_l0` + `threats_l1` outputs, builds L2 candidates |
| `threats` *(legacy)* | live only | Integrated L0 → L1 → L2 in a single conversational loop |

The split tasks (`threats_l0/l1/l2`) reconstruct the prior conversation from saved outputs instead of using server-side response chaining, which allows batch mode and better prompt-cache locality (requests are sorted by candidate names before submission).

**Run order:**
```bash
python -m labelling.orchestrator <input_dir> <run_name> -t threats_l0 -s batch
python -m labelling.orchestrator <input_dir> <run_name> -t threats_l1 -s batch
python -m labelling.orchestrator <input_dir> <run_name> -t threats_l2 -s batch
```

All three must use the same `run_name` so each level can find the prior level's outputs in `batch_outputs/<run_name>/`.

### Ecosystem tasks

| Task name | Mode | Description |
|---|---|---|
| `ecosystems_realm` | live + **batch** | Realm classification only (article → realms) |
| `ecosystems_biome` | live + **batch** | Biome classification — reads `ecosystems_realm` outputs, builds biome candidates |
| `ecosystems_efg` | live + **batch** | EFG classification — reads realm + biome outputs, builds EFG candidates |
| `ecosystems` *(legacy)* | live only | Integrated realm → biome → EFG in a single conversational loop |

The split tasks follow the same pattern as the split threat tasks: each level reads prior outputs from the same run folder, reconstructs the conversation, and sorts requests by candidate names for cache locality.

**Run order:**
```bash
python -m labelling.orchestrator <input_dir> <run_name> -t ecosystems_realm -s batch
python -m labelling.orchestrator <input_dir> <run_name> -t ecosystems_biome -s batch
python -m labelling.orchestrator <input_dir> <run_name> -t ecosystems_efg  -s batch
```

## Output format

**Simple tasks** — standard OpenAI batch/live response JSONL:
```json
{"custom_id": "...", "response": {"body": {"output": [...]}}}
```

**Split threat and ecosystem tasks** — per-stage record:
```json
{
  "custom_id": "...",
  "response_text": "<raw model output text>",
  "results_payload": {"results": ["Label A", "Label B"], "stop_reason": "continue"},
  "candidates_passed": [{"name": "...", "desc": "..."}, ...],
  "error": null
}
```

**Legacy integrated tasks** (`threats`, `ecosystems`) — full workflow record with all stages:
```json
{
  "custom_id": "...",
  "results_payload": {
    "threat_l0": {"results": [...], "stop_reason": "continue"},
    "threat_l1": {"results": [...], "stop_reason": "continue"},
    "threat_l2": {"results": [...], "stop_reason": "stop"}
  },
  "responses": {"threat_l0": {...}, "threat_l1": {...}, "threat_l2": {...}},
  "iterations": 3,
  "error": null
}
```

## Output file naming

All outputs land in `batch_outputs/<run_name>/`:

| Task | Output file pattern |
|---|---|
| Simple tasks | `<task>-<request_stem>.jsonl` |
| `threats_l0/l1/l2` | `threats_l0-<request_stem>.jsonl` etc. |
| `ecosystems_realm/biome/efg` | `ecosystems_realm-<request_stem>.jsonl` etc. |
| `threats` (legacy) | `threats-<request_stem>.jsonl` |
| `ecosystems` (legacy) | `ecosystems-<request_stem>.jsonl` |

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
| `ORCHESTRATOR_SUBMISSION_MODE` | Default submission mode (`live` or `batch`) |
| `ORCHESTRATOR_TASK` | Default task if `-t` is not passed |
| `PROMPT_KEY_*` | Prompt config keys for each task (e.g. `PROMPT_KEY_THREATS`) |
