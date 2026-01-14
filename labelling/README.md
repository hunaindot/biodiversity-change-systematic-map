Labelling pipeline for consolidating WoS exports, slicing batches, and submitting them to OpenAI for configurable classification tasks (drivers, geography, taxa, study, ecosystem typology, threats).

Contents
- src/data_loader.py – ingest .xls exports and turn them into document dicts.
- src/batching.py – split documents into JSONL batches with manifests; batches live under `artifacts/batches/<run>/data` and manifest also records the paired `request` dir.
- src/openai_batches.py – build batch-ready request files and submit/poll/download via OpenAI (requests saved under `artifacts/batches/<run>/request`).
- src/openai_live.py – optional live submission helper mirroring batch responses format.
- src/tasks.py – task definitions and request builders for driver, geography, taxa, study, ecosystem, and threat workflows.
- artifacts/ – datasets, batches, and batch outputs are written here.

Quick start
1) Activate the existing venv if needed: `source venv/bin/activate`.
2) Export your key: `export OPENAI_API_KEY=...`.
3) Run the orchestrator: `python labelling/orchestrator.py <input_dir_with_xls> <run_name> [--task driver|geography|taxa|study|ecosystems|threats]`.
   - Optional env vars (see `.env`): `ORCHESTRATOR_LIMIT_DOCS`, `ORCHESTRATOR_BATCH_SIZE`, `ORCHESTRATOR_MODEL`, `ORCHESTRATOR_REASONING`, `ORCHESTRATOR_RUN_OPENAI`, `ORCHESTRATOR_SUBMISSION_MODE`, `ORCHESTRATOR_TASK`, `ORCHESTRATOR_PROMPTS_FILE`.
4) The script will:
   - Read and dedupe all .xls/.xlsx files.
   - Persist the combined dataset to `artifacts/datasets/`.
   - Split into batch JSONL files under `artifacts/batches/<RUN_NAME>/`.
   - Generate OpenAI-ready request JSONL for the chosen task.
   - (Optional) Submit/poll/download outputs if you want to call the API.

Tasks
- driver (default) – supports live or batch submission against `classify_direct_driver`.
- geography – supports live or batch submission against `classify_region`.
- taxa – supports live or batch submission against `classify_taxa`.
- study – supports live or batch submission against `classify_study`.
- ecosystems – live-only multi-step flow (realm → biome → EFG) using `classify_ecosystem_typology` and ecosystem typology mappings.
- threats – live-only multi-step flow (threat_l0 → threat_l1 → threat_l2) using `classify_threats`, `threats_classification.json` lookups, and prompt-cache sharding per custom_id.

Notes
- The OpenAI steps are safe to skip if you are offline; they raise if no key is set.
- Batch files are JSONL, one document or request per line, so they can be inspected or re-used directly with the OpenAI batches endpoint.
