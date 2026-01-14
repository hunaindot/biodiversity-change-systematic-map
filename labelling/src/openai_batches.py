from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

from openai import OpenAI

from .config import DEFAULT_MODEL, DEFAULT_REASONING_EFFORT, MAPPINGS_DIR
from .config import get_openai_api_key

DEFAULT_PROMPTS_FILE = "prompts_zero.json"
ENV_PROMPTS_FILE = "ORCHESTRATOR_PROMPTS_FILE"


def _resolve_prompts_path(path: Path | None) -> Path:
    if path:
        return Path(path)
    env_value = os.getenv(ENV_PROMPTS_FILE)
    if env_value:
        candidate = Path(env_value)
        if not candidate.is_absolute():
            candidate = MAPPINGS_DIR / candidate
    else:
        candidate = MAPPINGS_DIR / DEFAULT_PROMPTS_FILE
    if not candidate.exists():
        raise FileNotFoundError(f"Prompt file not found: {candidate}")
    return candidate


def load_prompts(path: Path | None = None) -> dict:
    prompt_path = _resolve_prompts_path(path)
    return json.loads(prompt_path.read_text(encoding="utf-8"))


def format_article(doc: dict) -> str:
    parts = [doc.get("title", "").strip(), doc.get("abstract", "").strip()]
    return "\n\n".join(p for p in parts if p)


def build_direct_driver_request(
    doc: dict,
    prompts: dict,
    model: str = DEFAULT_MODEL,
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
) -> dict:
    system_prompt = prompts["classify_direct_driver"]["system_prompt"]
    structured_output = prompts["classify_direct_driver"].get("structured_output")
    text_format = None
    if isinstance(structured_output, dict):
        text_format = structured_output.get("text") or structured_output.get("format")
    prompt = format_article(doc)
    body: dict = {
        "model": model,
        "reasoning": {"effort": reasoning_effort},
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    }
    if text_format:
        body["text"] = {"format": text_format} if "format" not in text_format else text_format
    return {
        "custom_id": doc.get("UT") or doc.get("id") or "",
        "method": "POST",
        "url": "/v1/responses",
        "body": body,
    }


def build_requests_file(
    documents: Iterable[dict],
    dest: Path,
    prompts: dict | None = None,
    model: str = DEFAULT_MODEL,
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
) -> Path:
    prompts = prompts or load_prompts()
    # If the caller accidentally points to the data dir, automatically switch to sibling request dir.
    if dest.parent.name.lower() == "data":
        dest = dest.parent.parent / "request" / dest.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as f:
        for doc in documents:
            req = build_direct_driver_request(doc, prompts, model=model, reasoning_effort=reasoning_effort)
            f.write(json.dumps(req, ensure_ascii=False) + "\n")
    return dest


def build_client(api_key: str | None = None) -> OpenAI:
    key = api_key or get_openai_api_key()
    return OpenAI(api_key=key)


def submit_batch(requests_path: Path, client: OpenAI | None = None, completion_window: str = "24h", metadata: dict | None = None) -> dict:
    client = client or build_client()
    with requests_path.open("rb") as f:
        upload = client.files.create(file=f, purpose="batch")
    batch = client.batches.create(
        input_file_id=upload.id,
        endpoint="/v1/responses",
        completion_window=completion_window,
        metadata=metadata or {},
    )
    return {"batch_id": batch.id, "input_file_id": upload.id, "status": batch.status}


def poll_batch(batch_id: str, client: OpenAI | None = None) -> dict:
    client = client or build_client()
    batch = client.batches.retrieve(batch_id)
    return {
        "id": batch.id,
        "status": batch.status,
        "output_file_id": getattr(batch, "output_file_id", None),
        "error_file_id": getattr(batch, "error_file_id", None),
        "completion_window": getattr(batch, "completion_window", None),
    }


def download_batch_output(batch_id: str, dest: Path, client: OpenAI | None = None) -> Path:
    client = client or build_client()
    batch = client.batches.retrieve(batch_id)
    output_file_id = getattr(batch, "output_file_id", None)
    if not output_file_id:
        raise RuntimeError(f"Batch {batch_id} has no output file yet (status: {batch.status}).")

    content = client.files.content(output_file_id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content.read())
    return dest
