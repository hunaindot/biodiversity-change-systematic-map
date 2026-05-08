from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

from src import batching, batch_api, data_loader, tasks

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evals_local.run import run_tasks
from src.config import (
    BATCHES_DIR,
    BATCH_OUTPUTS_DIR,
    DATASETS_DIR,
    DEFAULT_MODEL,
    DEFAULT_REASONING_EFFORT,
    ensure_artifact_dirs,
)

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
ENV_LIMIT_DOCS = "ORCHESTRATOR_LIMIT_DOCS"
ENV_BATCH_SIZE = "ORCHESTRATOR_BATCH_SIZE"
ENV_SUBMISSION_MODE = "ORCHESTRATOR_SUBMISSION_MODE"
ENV_RUN_EVALS = "ORCHESTRATOR_RUN_EVALS"


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
        help="Directory containing WoS export files (.xls, .xlsx, or .csv).",
    )
    parser.add_argument(
        "run_name",
        help="Name to tag dataset, batches, and outputs.",
    )
    parser.add_argument(
        "--task",
        dest="task",
        required=True,
        help="Classification task to run (e.g., screening, driver, threats_l0, geography, ecosystems_realm, study, taxa).",
    )
    return parser.parse_args()


def main() -> None:
    load_env_file()
    ensure_artifact_dirs()

    args = parse_args()
    input_dir: Path = args.input_dir
    run_name: str = args.run_name
    task_name: str = args.task
    task = tasks.get_task(task_name)

    limit_docs = env_int(ENV_LIMIT_DOCS, 500)
    batch_size = env_int(ENV_BATCH_SIZE, 100)
    model = DEFAULT_MODEL
    reasoning = DEFAULT_REASONING_EFFORT
    run_evals = env_bool(ENV_RUN_EVALS, True)
    submission_mode = (os.getenv(ENV_SUBMISSION_MODE) or "live").lower()
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

    prompts = batch_api.load_prompts()
    request_files: list[Path] = []
    for entry in manifest["batches"]:
        data_path = Path(entry.get("data_path") or entry["path"])
        docs = data_loader.load_jsonl(data_path)
        if entry.get("request_path"):
            raw_dest = Path(entry["request_path"])
            dest = raw_dest.parent / f"{task.name}-{raw_dest.name}"
        else:
            request_dir = Path(manifest["request_dir"])
            dest = request_dir / f"{task.name}-{data_path.stem}-requests.jsonl"
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

    outputs_ready = False
    submitted: list[dict] = []
    client = batch_api.build_client()
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
        outputs_ready = True
    else:
        for req_path in request_files:
            info = batch_api.submit_batch(
                Path(req_path),
                client=client,
                metadata=task.batch_metadata(run_name),
            )
            info["mode"] = "batch"
            info["request_path"] = str(req_path)
            info["task"] = task.name
            submitted.append(info)

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
                status = batch_api.poll_batch(entry["batch_id"], client=client)
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
                label = entry.get("task") or task.name
                dest = output_dir / f"{label}-{entry['batch_id']}-output.jsonl"
                try:
                    batch_api.download_batch_output(entry["batch_id"], dest, client=client)
                    print(f"  [{label}] Saved {dest}")
                except Exception as exc:
                    print(f"  [{label}] Download failed: {exc}")
            outputs_ready = True

        if failed:
            print(f"\n{len(failed)} batch(es) failed/cancelled/expired:")
            for entry in failed:
                print(f"  [{entry.get('task')}] {entry['batch_id']}")

    if outputs_ready and run_evals:
        print(f"\nRunning evals for task '{task_name}' on run '{run_name}' ...")
        try:
            per_task_label_paths = None
            if task.name == "screening":
                per_task_label_paths = {task.name: str(input_dir)}
            summaries = run_tasks(
                run_name,
                tasks=[task.name],
                per_task_label_paths=per_task_label_paths,
            )
            for s in summaries:
                print(f"  [{s['task']}] rows={s['rows']} data={s['data_path']}")
                for truth, path in s["metric_paths"].items():
                    print(f"    metrics {truth}: {path}")
        except Exception as exc:
            print(f"  Evals failed: {exc}")


if __name__ == "__main__":
    main()
