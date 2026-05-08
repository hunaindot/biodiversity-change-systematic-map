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

- `input_dir` — directory containing WoS export files (`.xls`, `.xlsx`, or `.csv`; all files are combined)
- `run_name` — tag applied to all outputs for this run (e.g. `l1_train_170426_f1`)
- `--task` — classification task (see below; defaults to `driver`)

**Suggested run naming:** `{label_level}_{split}_{date}_{run_index}` — e.g. `l2_train_170426_f1`

---

## Tasks in label order

### L0 — Screening

```bash
python labelling/orchestrator.py data/labels/l0/train l0_train_<date>_f1 --task screen
python labelling/orchestrator.py data/labels/l0/dev   l0_dev_<date>_f1   --task screen
python labelling/orchestrator.py data/labels/l0/test  l0_test_<date>_f1  --task screen
```

### L1 — Drivers

```bash
python labelling/orchestrator.py data/labels/l1/train l1_train_<date>_f1 --task driver
python labelling/orchestrator.py data/labels/l1/dev   l1_dev_<date>_f1   --task driver
python labelling/orchestrator.py data/labels/l1/test  l1_test_<date>_f1  --task driver
```

### L2 — Threats (3 sequential steps, same `run_name` across all three)

```bash
python labelling/orchestrator.py data/labels/l2/train l2_train_<date>_f1 --task threats_l0
python labelling/orchestrator.py data/labels/l2/train l2_train_<date>_f1 --task threats_l1
python labelling/orchestrator.py data/labels/l2/train l2_train_<date>_f1 --task threats_l2

python labelling/orchestrator.py data/labels/l2/dev   l2_dev_<date>_f1   --task threats_l0
python labelling/orchestrator.py data/labels/l2/dev   l2_dev_<date>_f1   --task threats_l1
python labelling/orchestrator.py data/labels/l2/dev   l2_dev_<date>_f1   --task threats_l2

python labelling/orchestrator.py data/labels/l2/test  l2_test_<date>_f1  --task threats_l0
python labelling/orchestrator.py data/labels/l2/test  l2_test_<date>_f1  --task threats_l1
python labelling/orchestrator.py data/labels/l2/test  l2_test_<date>_f1  --task threats_l2
```

Each level reads the prior level's outputs from `data/artifacts/batch_outputs/<run_name>/`. `threats_l1` and `threats_l2` will skip documents where the prior level has no valid output.

### L3 — Geography

```bash
python labelling/orchestrator.py data/labels/l3/train l3_train_<date>_f1 --task geography
python labelling/orchestrator.py data/labels/l3/dev   l3_dev_<date>_f1   --task geography
python labelling/orchestrator.py data/labels/l3/test  l3_test_<date>_f1  --task geography
```

### L4 — Ecosystems (3 sequential steps, same `run_name` across all three)

```bash
python labelling/orchestrator.py data/labels/l4/train l4_train_<date>_f1 --task ecosystems_realm
python labelling/orchestrator.py data/labels/l4/train l4_train_<date>_f1 --task ecosystems_biome
python labelling/orchestrator.py data/labels/l4/train l4_train_<date>_f1 --task ecosystems_efg

python labelling/orchestrator.py data/labels/l4/dev   l4_dev_<date>_f1   --task ecosystems_realm
python labelling/orchestrator.py data/labels/l4/dev   l4_dev_<date>_f1   --task ecosystems_biome
python labelling/orchestrator.py data/labels/l4/dev   l4_dev_<date>_f1   --task ecosystems_efg

python labelling/orchestrator.py data/labels/l4/test  l4_test_<date>_f1  --task ecosystems_realm
python labelling/orchestrator.py data/labels/l4/test  l4_test_<date>_f1  --task ecosystems_biome
python labelling/orchestrator.py data/labels/l4/test  l4_test_<date>_f1  --task ecosystems_efg
```

### L5 — Study

```bash
python labelling/orchestrator.py data/labels/l5/train l5_train_<date>_f1 --task study
python labelling/orchestrator.py data/labels/l5/dev   l5_dev_<date>_f1   --task study
python labelling/orchestrator.py data/labels/l5/test  l5_test_<date>_f1  --task study
```

### L6 — Taxa

```bash
python labelling/orchestrator.py data/labels/l6/train l6_train_<date>_f1 --task taxa
python labelling/orchestrator.py data/labels/l6/dev   l6_dev_<date>_f1   --task taxa
python labelling/orchestrator.py data/labels/l6/test  l6_test_<date>_f1  --task taxa
```

---

## All available tasks

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
