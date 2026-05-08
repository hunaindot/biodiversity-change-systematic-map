# Labelling Package

Orchestrates OpenAI classification runs over train/dev/test label sets, writes JSONL outputs, and automatically runs evals on completion.

**Assumes:**
- Label data is already present under `data/labels/` (built by the `data_helpers` package — see the [root README](../README.md) for setup)
- `.env` is configured with your API key, model, submission mode, and paths — see [`.env.sample`](../.env.sample)

---

## Usage

Run from the repo root:

```bash
python labelling/orchestrator.py <input_dir> <run_name> --task <task>
```

- `input_dir` — a directory of WoS export files. Typically one of:
  - `data/labels/l{0-6}/{train|dev|test}` — label splits for a specific label level (built by `data_helpers`)
  - a raw screening or coding dataset folder for running against unannotated inputs
- `run_name` — tag applied to all outputs for this run. Follow the convention `{partition}-{type}-{label_level}-v{n}`, e.g.:
  - `train-screening-l0-v1`
  - `dev-coding-l2-v1`
  - `test-coding-l4-v2`
- `--task` — classification task to run (required; see table below)

---

## Available tasks

Run tasks in label order. L2 and L4 are multi-step — all steps must share the same `run_name` so each level can find the prior level's outputs.

| Label | Task | Alias(es) | Depends on |
|---|---|---|---|
| L0 | `screening` | `screen`, `eligibility` | — |
| L1 | `driver` | `drivers`, `direct_driver` | — |
| L2 | `threats_l0` | — | — |
| L2 | `threats_l1` | — | `threats_l0` |
| L2 | `threats_l2` | — | `threats_l1` |
| L3 | `geography` | `geo`, `region` | — |
| L4 | `ecosystems_realm` | `ecosystem_realm` | — |
| L4 | `ecosystems_biome` | `ecosystem_biome` | `ecosystems_realm` |
| L4 | `ecosystems_efg` | `ecosystem_efg` | `ecosystems_biome` |
| L5 | `study` | `studies` | — |
| L6 | `taxa` | — | — |

---

## Evals

Evals run automatically after each task completes and write metrics to `$EVALS_OUTPUT_DIR/<run_name>/`:
- `data/` — joined truth + prediction CSV
- `metrics/` — metric files per truth column

For `screening`, ground-truth labels are read from `input_dir` directly. All other tasks resolve labels from the configured `EVALS_LABELS_DIR`.

Evals silently no-op if no ground-truth labels are found — they don't block the pipeline. Set `ORCHESTRATOR_RUN_EVALS=false` to skip entirely.

---

## Output format

**L0, L1, L3, L5, L6** (`screening`, `driver`, `geography`, `study`, `taxa`) — raw OpenAI response envelope:
```json
{"custom_id": "...", "response": {"body": {"output": [...]}}}
```

**L2, L4** (`threats_*`, `ecosystems_*`) — parsed record with labelling metadata:
```json
{
  "custom_id": "...",
  "response_text": "<raw model output>",
  "results_payload": {"results": ["Label A", "Label B"], "stop_reason": "continue"},
  "candidates_passed": [{"name": "...", "desc": "..."}, ...],
  "error": null
}
```

All outputs land in `$ORCHESTRATOR_BATCH_OUTPUTS_DIR/<run_name>/`. The level-specific prefix on L2/L4 output files (e.g. `threats_l0-`, `ecosystems_biome-`) is how each subsequent step finds the prior level's outputs.

---

## Environment variables

See [`.env.sample`](../.env.sample) for all variables and defaults. Key toggles:

| Variable | Description |
|---|---|
| `ORCHESTRATOR_SUBMISSION_MODE` | `live` (synchronous) or `batch` (async, ~50% cheaper) |
| `ORCHESTRATOR_RUN_EVALS` | Set `false` to skip automatic evals |
| `ORCHESTRATOR_LIMIT_DOCS` | Cap documents per run (`none` for all) |
