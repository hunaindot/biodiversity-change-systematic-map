#!/usr/bin/env python3
"""
Run labelling evals from the terminal.

Usage:
    python run_evals.py --iteration 1
    python run_evals.py --iteration 1 --tasks screening driver --splits train dev
    python run_evals.py --iteration 1 --mode batch --limit 10
    python run_evals.py --iteration 1 --no-local-evals
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

EVALS_JSON_PATH = "mappings/evals.json"

# Orchestrator task names → evals_local task names (only where they differ)
TASK_NAME_MAP = {
    "threat": "threats",
    "ecosystem": "ecosystems",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Run labelling evals")
    parser.add_argument("--iteration", type=int, required=True, help="Iteration ID")
    parser.add_argument(
        "--tasks",
        nargs="+",
        default=None,
        metavar="TASK",
        help="Tasks to run (default: all). e.g. --tasks screening driver",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["train", "dev", "test"],
        metavar="SPLIT",
        help="Splits to run (default: train dev test)",
    )
    parser.add_argument(
        "--mode",
        default="live",
        choices=["live", "batch"],
        help="Submission mode (default: live)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Limit number of docs per run (default: no limit)",
    )
    parser.add_argument(
        "--evals-json",
        default=EVALS_JSON_PATH,
        help=f"Path to evals config (default: {EVALS_JSON_PATH})",
    )
    parser.add_argument(
        "--no-local-evals",
        action="store_true",
        help="Skip running evals_local metrics after each completed run",
    )
    return parser.parse_args()


def load_iteration(evals_json_path, iteration_id):
    with open(evals_json_path) as f:
        config = json.load(f)
    for it in config["iterations"]:
        if it["iteration_id"] == iteration_id:
            return it
    available = [it["iteration_id"] for it in config["iterations"]]
    raise ValueError(f"Iteration {iteration_id} not found. Available: {available}")


def run_orchestrator(task_name, data_path, run_name, model, reasoning, mode, limit):
    env = os.environ.copy()
    env["ORCHESTRATOR_MODEL"] = model
    env["ORCHESTRATOR_REASONING"] = reasoning
    env["ORCHESTRATOR_SUBMISSION_MODE"] = mode
    env["ORCHESTRATOR_LIMIT_DOCS"] = str(limit) if limit is not None else "none"

    cmd = [
        "python", "labelling/orchestrator.py",
        data_path,
        run_name,
        "--task", task_name,
    ]

    print(f"  CMD: {' '.join(cmd)}")
    print(f"  ENV: MODEL={model}, REASONING={reasoning}, MODE={mode}, LIMIT={limit}")
    print()

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    batch_ids = re.findall(r"Batch submitted: id=(batch_[^,\s]+)", result.stdout or "")

    if result.returncode != 0:
        print(f"  FAILED (exit code {result.returncode})")
    else:
        print(f"  DONE")
        if batch_ids:
            print(f"  Batch IDs: {batch_ids}")

    return result.returncode, batch_ids


def run_local_eval(task_name, run_name):
    """Run evals_local metrics for a completed orchestrator run."""
    from evals_local.run import run_task
    from evals_local.config import TASK_CONFIG

    local_task = TASK_NAME_MAP.get(task_name, task_name)
    if local_task not in TASK_CONFIG:
        print(f"  [local-eval] No evals_local config for task '{local_task}', skipping.")
        return None

    print(f"  [local-eval] Running metrics for task={local_task}, run={run_name} ...")
    try:
        summary = run_task(local_task, run_name)
        print(f"  [local-eval] rows={summary['rows']}  data={summary['data_path']}")
        for truth, path in summary["metric_paths"].items():
            print(f"  [local-eval]   metrics {truth}: {path}")
        return summary
    except Exception as e:
        print(f"  [local-eval] ERROR: {e}")
        return None


def main():
    args = parse_args()

    sys.path.insert(0, "labelling")

    iteration = load_iteration(args.evals_json, args.iteration)
    model = iteration["model"]
    reasoning = iteration["reasoning"]["effort"]
    tasks = iteration["tasks"]

    if args.tasks is not None:
        tasks = {k: v for k, v in tasks.items() if k in args.tasks}

    print(f"Iteration:  {args.iteration} — {iteration['description']}")
    print(f"Model:      {model}")
    print(f"Reasoning:  {reasoning}")
    print(f"Tasks:      {list(tasks.keys())}")
    print(f"Splits:     {args.splits}")
    print(f"Mode:       {args.mode}")
    print(f"Limit:      {args.limit}")
    print()

    # Build runs
    runs = []
    for task_name, splits in tasks.items():
        for split in args.splits:
            if split not in splits:
                print(f"  WARNING: split '{split}' not found for task '{task_name}', skipping")
                continue
            cfg = splits[split]
            runs.append((task_name, split, cfg["data_path"], cfg["run_name"]))

    print(f"Total runs: {len(runs)}")
    for task_name, split, data_path, run_name in runs:
        print(f"  {task_name:12s} {split:5s}  {data_path}  →  {run_name}")
    print()

    results = []
    all_batches = []

    for i, (task_name, split, data_path, run_name) in enumerate(runs, 1):
        print(f"{'='*60}")
        print(f"[{i}/{len(runs)}] task={task_name}  split={split}")
        print(f"{'='*60}")
        rc, batch_ids = run_orchestrator(
            task_name, data_path, run_name, model, reasoning, args.mode, args.limit
        )
        results.append({"task": task_name, "split": split, "run_name": run_name, "exit_code": rc})
        for bid in batch_ids:
            all_batches.append({"batch_id": bid, "task": task_name, "split": split, "run_name": run_name})

        if rc == 0 and not args.no_local_evals:
            run_local_eval(task_name, run_name)

        print()

    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    for r in results:
        status = "OK" if r["exit_code"] == 0 else f"FAIL({r['exit_code']})"
        print(f"  {r['task']:12s} {r['split']:5s}  {status}  {r['run_name']}")

    if all_batches:
        print(f"\nCollected {len(all_batches)} batch submission(s):")
        for b in all_batches:
            print(f"  {b['task']:12s} {b['split']:5s}  {b['batch_id']}  ({b['run_name']})")

    failed = [r for r in results if r["exit_code"] != 0]
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
