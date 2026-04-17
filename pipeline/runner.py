from __future__ import annotations

import subprocess
from pathlib import Path


def run_orchestrator(
    input_path: str | Path,
    run_name: str,
    task: str,
    submission_mode: str | None = None,
) -> bool:
    """
    Run labelling/orchestrator.py for one partition.
    Returns True on success, False on failure.

    submission_mode: 'live' or 'batch'. When given, passes --submission-mode
    explicitly so the CLI arg takes priority over any inherited env var or .env.
    When None, the orchestrator reads ORCHESTRATOR_SUBMISSION_MODE from .env as usual.
    """
    cmd = f"python labelling/orchestrator.py {input_path} {run_name} --task {task}"
    if submission_mode is not None:
        cmd += f" --submission-mode {submission_mode}"
    print(f"\n{'='*60}")
    print(f"Running [{task}] {run_name}: {cmd}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"STDERR: {result.stderr}")
    if result.returncode != 0:
        print(f"FAILED with return code {result.returncode}")
        return False
    print(f"Done: {run_name}")
    return True
