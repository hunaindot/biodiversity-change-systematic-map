from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

from src import batching, data_loader, openai_batches, tasks
from src.config import (
    BATCHES_DIR,
    BATCH_OUTPUTS_DIR,
    DATASETS_DIR,
    DEFAULT_MODEL,
    DEFAULT_REASONING_EFFORT,
    ensure_artifact_dirs,
)

ENV_FILE = Path(".env")
ENV_LIMIT_DOCS = "ORCHESTRATOR_LIMIT_DOCS"
ENV_BATCH_SIZE = "ORCHESTRATOR_BATCH_SIZE"
ENV_MODEL = "ORCHESTRATOR_MODEL"
ENV_REASONING = "ORCHESTRATOR_REASONING"
ENV_RUN_OPENAI = "ORCHESTRATOR_RUN_OPENAI"
ENV_SUBMISSION_MODE = "ORCHESTRATOR_SUBMISSION_MODE"
ENV_TASK = "ORCHESTRATOR_TASK"


def load_env_file(path: Path = ENV_FILE) -> None:
    """Populate os.environ with values from a .env file without overriding existing variables."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value[:1] == value[-1:] and value.startswith(("'", '"')):
            value = value[1:-1]
        if key not in os.environ:
            os.environ[key] = value


def env_int(name: str, default: int | None) -> int | None:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    if raw.lower() == "none":
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer or 'None'.") from exc


def env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    lowered = raw.lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Environment variable {name} must be a boolean (true/false).")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run batching and OpenAI submission pipeline.")
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing WoS .xls files.",
    )
    parser.add_argument(
        "run_name",
        help="Name to tag dataset, batches, and outputs.",
    )
    parser.add_argument(
        "--task",
        "-t",
        dest="task",
        help="Classification task to run (e.g., driver, screening, geography, taxa, study, ecosystems, threats). Defaults to driver.",
    )
    parser.add_argument(
        "--submission-mode",
        "-s",
        dest="submission_mode",
        choices=["live", "batch"],
        help="Submission mode: 'live' (default) or 'batch'. Overrides ORCHESTRATOR_SUBMISSION_MODE.",
    )
    return parser.parse_args()


def main() -> None:
    load_env_file()
    ensure_artifact_dirs()

    args = parse_args()
    input_dir: Path = args.input_dir
    run_name: str = args.run_name
    task_name: str = args.task or os.getenv(ENV_TASK) or "driver"
    task = tasks.get_task(task_name)

    limit_docs = env_int(ENV_LIMIT_DOCS, 500)
    batch_size = env_int(ENV_BATCH_SIZE, 100)
    model = os.getenv(ENV_MODEL, DEFAULT_MODEL) or DEFAULT_MODEL
    reasoning = os.getenv(ENV_REASONING, DEFAULT_REASONING_EFFORT) or DEFAULT_REASONING_EFFORT
    run_openai = env_bool(ENV_RUN_OPENAI, True)
    submission_mode = (args.submission_mode or os.getenv(ENV_SUBMISSION_MODE) or "live").lower()
    if submission_mode not in {"live", "batch"}:
        raise ValueError(f"{ENV_SUBMISSION_MODE} must be 'live' or 'batch'.")
    if submission_mode == "batch" and not task.supports_batch:
        raise ValueError(f"Task '{task.name}' only supports live submission.")

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    df = data_loader.load_wos_excels(input_dir, limit=limit_docs)
    documents = data_loader.dataframe_to_documents(df)
    dataset_path = data_loader.save_dataset(documents, path=DATASETS_DIR / f"{run_name}-dataset.json")

    print(f"Loaded {len(documents)} documents from {input_dir}")
    print(f"Dataset saved to {dataset_path}")

    manifest = batching.write_batches(documents, batch_size=batch_size, run_name=run_name, output_dir=BATCHES_DIR)
    print(f"Wrote {len(manifest['batches'])} batches to {manifest['data_dir']}")

    prompts = openai_batches.load_prompts()
    request_files: list[Path] = []
    for entry in manifest["batches"]:
        data_path = Path(entry.get("data_path") or entry["path"])
        docs = data_loader.load_jsonl(data_path)
        if entry.get("request_path"):
            dest = Path(entry["request_path"])
        else:
            request_dir = Path(manifest["request_dir"])
            dest = request_dir / f"{data_path.stem}-requests.jsonl"
        dest.parent.mkdir(parents=True, exist_ok=True)
        built_path = task.build_requests_file(
            docs,
            dest,
            prompts=prompts,
            model=model,
            reasoning_effort=reasoning,
        )
        request_files.append(built_path)
    print(f"Prepared {len(request_files)} request files in {manifest['request_dir']}")

    submitted: list[dict] = []
    if run_openai:
        client = openai_batches.build_client()
        if submission_mode == "live":
            output_dir = BATCH_OUTPUTS_DIR / run_name
            submitted.extend(
                task.run_live(
                    request_files,
                    output_dir=output_dir,
                    client=client,
                    default_model=model,
                    default_reasoning=reasoning,
                    prompts=prompts,
                )
            )
        else:
            for req_path in request_files:
                info = openai_batches.submit_batch(
                    Path(req_path),
                    client=client,
                    metadata=task.batch_metadata(run_name),
                )
                info["mode"] = "batch"
                info["request_path"] = str(req_path)
                info["task"] = task.name
                submitted.append(info)
    else:
        print("Skipping OpenAI submission; set ORCHESTRATOR_RUN_OPENAI=true to submit.")

    if submitted:
        print("Submission summary:")
        for entry in submitted:
            entry.setdefault("task", task.name)
            label = entry.get("task") or task.name
            mode = entry.get("mode") or "batch"
            if mode == "live":
                print(f"  [{label}] Live outputs for {entry.get('request_path')}: {entry.get('output_path')}")
            else:
                print(f"  [{label}] Batch submitted: id={entry.get('batch_id')}, request={entry.get('request_path')}")

    # Poll and download batch outputs
    batch_entries = [e for e in submitted if e.get("mode") == "batch" and e.get("batch_id")]
    if batch_entries:
        poll_interval = 90
        print(f"\nPolling {len(batch_entries)} batch(es) every {poll_interval}s until complete ...")
        pending = list(batch_entries)
        completed = []
        failed = []

        while pending:
            still_pending = []
            for entry in pending:
                status = openai_batches.poll_batch(entry["batch_id"], client=client)
                state = status["status"]
                label = entry.get("task") or task.name

                if state == "completed":
                    print(f"  [{label}] Batch {entry['batch_id']} completed.")
                    entry["output_file_id"] = status.get("output_file_id")
                    completed.append(entry)
                elif state in ("failed", "cancelled", "expired"):
                    print(f"  [{label}] Batch {entry['batch_id']} {state}.")
                    failed.append(entry)
                else:
                    still_pending.append(entry)

            pending = still_pending
            if pending:
                print(f"  ... {len(pending)} batch(es) still running, waiting {poll_interval}s")
                time.sleep(poll_interval)

        if completed:
            output_dir = BATCH_OUTPUTS_DIR / run_name
            output_dir.mkdir(parents=True, exist_ok=True)
            print(f"\nDownloading {len(completed)} batch output(s) to {output_dir}")
            for entry in completed:
                dest = output_dir / f"{entry['batch_id']}-output.jsonl"
                try:
                    openai_batches.download_batch_output(entry["batch_id"], dest, client=client)
                    print(f"  [{entry.get('task')}] Saved {dest}")
                except Exception as exc:
                    print(f"  [{entry.get('task')}] Download failed: {exc}")

        if failed:
            print(f"\n{len(failed)} batch(es) failed/cancelled/expired:")
            for entry in failed:
                print(f"  [{entry.get('task')}] {entry['batch_id']}")


if __name__ == "__main__":
    main()
