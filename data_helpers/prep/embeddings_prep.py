"""Resumable per-publication embeddings via a local Ollama endpoint.

Builds one embedding vector per publication from ``title + abstract`` and writes a
single ``embeddings.parquet`` handoff artifact alongside the core dataset. The batch
run is checkpointed to a shard cache so an interrupted run resumes without
re-embedding already-completed publications.

Usage:
    python -m data_helpers.prep.embeddings_prep
    # or directly:
    python data_helpers/prep/embeddings_prep.py

Reads:  notebooks/data_processing/outputs/04_dataset/dataset.parquet
        notebooks/data_processing/outputs/04_dataset/dataset_abstracts.parquet
Writes: notebooks/data_processing/outputs/04_dataset/embeddings.parquet
        notebooks/data_processing/outputs/04_dataset/embeddings_manifest.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

from data_helpers import results_config
from data_helpers.prep._provenance import source_signature

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = 1
SHARD_PATTERN = "shard_{index:05d}.parquet"
ERRORS_FILENAME = "errors.jsonl"
SHARD_SCHEMA = pa.schema(
    [
        pa.field("id", pa.int64()),
        pa.field("UT", pa.string()),
        pa.field("embedding", pa.list_(pa.float32())),
        pa.field("model", pa.string()),
    ]
)


class EmbeddingsPrepError(RuntimeError):
    """Raised when the embedding build or its artifacts are invalid."""


# --------------------------------------------------------------------------
# Text mapping
# --------------------------------------------------------------------------


def build_embedding_texts(
    dataset: pd.DataFrame, abstracts: pd.DataFrame, *, prefix: str
) -> pd.DataFrame:
    """Return one row per publication: ``id``, ``UT``, and the prefixed embedding text."""
    missing_dataset_cols = {"id", "UT", "title"} - set(dataset.columns)
    if missing_dataset_cols:
        raise EmbeddingsPrepError(f"dataset is missing columns: {sorted(missing_dataset_cols)}")
    missing_abstract_cols = {"UT", "abstract"} - set(abstracts.columns)
    if missing_abstract_cols:
        raise EmbeddingsPrepError(
            f"abstracts is missing columns: {sorted(missing_abstract_cols)}"
        )

    left = dataset[["id", "UT", "title"]].copy()
    right = abstracts[["UT", "abstract"]].copy()
    if left["UT"].duplicated().any():
        raise EmbeddingsPrepError("dataset UT is not unique.")
    if right["UT"].duplicated().any():
        raise EmbeddingsPrepError("abstracts UT is not unique.")
    if set(left["UT"]) != set(right["UT"]):
        raise EmbeddingsPrepError("dataset and abstracts UT sets do not match.")

    merged = left.merge(right, on="UT", how="left", validate="1:1")
    if len(merged) != len(left):
        raise EmbeddingsPrepError("Text mapping did not preserve the dataset grain.")

    title = merged["title"].fillna("").astype(str).str.strip()
    abstract = merged["abstract"].fillna("").astype(str).str.strip()
    merged["text"] = prefix + title + ". " + abstract
    return merged[["id", "UT", "text"]]


# --------------------------------------------------------------------------
# HTTP client
# --------------------------------------------------------------------------


def build_session(*, max_retries: int = 5) -> requests.Session:
    retry = Retry(
        total=max_retries,
        connect=max_retries,
        read=max_retries,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"POST"}),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.headers.update({"User-Agent": "biodiversity-embeddings-builder/1.0"})
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


class EmbeddingClient:
    """Thin wrapper for Ollama's ``/api/embed`` batch endpoint."""

    def __init__(
        self,
        *,
        endpoint: str,
        model: str,
        session: requests.Session | None = None,
        timeout: int = 120,
    ) -> None:
        self.endpoint = endpoint
        self.model = model
        self.session = session or build_session()
        self.timeout = timeout

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self.session.post(
            self.endpoint,
            json={"model": self.model, "input": list(texts)},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        embeddings = payload.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            got = len(embeddings) if isinstance(embeddings, list) else type(embeddings).__name__
            raise EmbeddingsPrepError(
                f"Embedding endpoint returned {got} vectors for a batch of {len(texts)} texts."
            )
        dims = {len(vector) for vector in embeddings}
        if len(dims) != 1:
            raise EmbeddingsPrepError(
                f"Embedding endpoint returned inconsistent dimensionality within one batch: {sorted(dims)}"
            )
        return embeddings


# --------------------------------------------------------------------------
# Shard cache
# --------------------------------------------------------------------------


def _iter_shard_paths(cache_dir: Path) -> list[Path]:
    return sorted(cache_dir.glob("shard_*.parquet"))


def scan_cache(cache_dir: Path) -> tuple[set[int], int]:
    """Return (already-embedded ids, next free shard index) from valid shards.

    A shard file only exists under its final name once fully written (see
    ``_write_shard``), so a crash mid-shard leaves only a ``.part`` file, which this
    glob does not match — that shard's ids are correctly treated as not yet done.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    done_ids: set[int] = set()
    max_index = -1
    for path in _iter_shard_paths(cache_dir):
        index = int(path.stem.split("_")[1])
        max_index = max(max_index, index)
        ids = pq.read_table(path, columns=["id"]).column("id").to_pylist()
        if len(set(ids)) != len(ids):
            raise EmbeddingsPrepError(f"Shard {path.name} contains duplicate ids.")
        done_ids.update(ids)
    return done_ids, max_index + 1


def _write_shard(
    cache_dir: Path,
    index: int,
    ids: Sequence[int],
    uts: Sequence[str],
    embeddings: Sequence[Sequence[float]],
    model: str,
) -> Path:
    table = pa.table(
        {
            "id": pa.array(ids, type=pa.int64()),
            "UT": pa.array(uts, type=pa.string()),
            "embedding": pa.array(embeddings, type=pa.list_(pa.float32())),
            "model": pa.array([model] * len(ids), type=pa.string()),
        },
        schema=SHARD_SCHEMA,
    )
    cache_dir.mkdir(parents=True, exist_ok=True)
    final_path = cache_dir / SHARD_PATTERN.format(index=index)
    tmp_path = final_path.with_suffix(final_path.suffix + ".part")
    pq.write_table(table, tmp_path, compression="zstd")
    tmp_path.replace(final_path)
    return final_path


def _log_errors(cache_dir: Path, ids: Sequence[int], error: str) -> None:
    record = {
        "ids": list(ids),
        "error": error,
        "logged_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    with (cache_dir / ERRORS_FILENAME).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


# --------------------------------------------------------------------------
# Batch runner
# --------------------------------------------------------------------------


def run_embedding_build(
    *,
    texts: pd.DataFrame,
    cache_dir: Path,
    endpoint: str,
    model: str,
    batch_size: int,
    shard_size: int,
    timeout: int = 120,
    max_retries: int = 5,
    limit: int | None = None,
    max_consecutive_batch_errors: int = 10,
    client: EmbeddingClient | None = None,
    progress: bool = True,
) -> dict[str, Any]:
    """Embed every ``texts`` row not already present in ``cache_dir``'s shards.

    One failing batch is logged to ``errors.jsonl`` and skipped rather than aborting
    the run (its ids are simply retried on the next resumed run, since they were
    never written to a shard). ``max_consecutive_batch_errors`` guards against a
    fully-down endpoint silently burning through the whole remaining dataset.
    """
    if texts["id"].duplicated().any():
        raise EmbeddingsPrepError("texts frame has duplicate ids.")

    done_ids, shard_index = scan_cache(cache_dir)
    remaining = texts.loc[~texts["id"].isin(done_ids)]
    if limit is not None:
        remaining = remaining.head(limit)

    client = client or EmbeddingClient(
        endpoint=endpoint, model=model, timeout=timeout, session=build_session(max_retries=max_retries)
    )

    total_remaining = len(remaining)
    processed = 0
    errored = 0
    consecutive_errors = 0
    pending_ids: list[int] = []
    pending_uts: list[str] = []
    pending_embeddings: list[list[float]] = []
    batch: list[tuple[int, str, str]] = []

    progress_bar = tqdm(total=total_remaining, disable=not progress, unit="doc")
    start_time = time.monotonic()

    def flush_shard() -> None:
        nonlocal shard_index, pending_ids, pending_uts, pending_embeddings
        if not pending_ids:
            return
        _write_shard(cache_dir, shard_index, pending_ids, pending_uts, pending_embeddings, model)
        shard_index += 1
        pending_ids, pending_uts, pending_embeddings = [], [], []

    def flush_batch() -> None:
        nonlocal batch, processed, errored, consecutive_errors
        if not batch:
            return
        batch_ids = [row[0] for row in batch]
        batch_uts = [row[1] for row in batch]
        batch_texts = [row[2] for row in batch]
        try:
            embeddings = client.embed_batch(batch_texts)
        except (requests.RequestException, EmbeddingsPrepError) as exc:
            _log_errors(cache_dir, batch_ids, repr(exc))
            errored += len(batch_ids)
            consecutive_errors += 1
            if consecutive_errors > max_consecutive_batch_errors:
                raise EmbeddingsPrepError(
                    f"{consecutive_errors} consecutive batches failed against {endpoint} "
                    "— aborting rather than logging errors for the rest of the dataset. "
                    "Check the Ollama endpoint, then rerun to resume."
                ) from exc
        else:
            consecutive_errors = 0
            pending_ids.extend(batch_ids)
            pending_uts.extend(batch_uts)
            pending_embeddings.extend(embeddings)
            if len(pending_ids) >= shard_size:
                flush_shard()
        processed += len(batch_ids)
        progress_bar.update(len(batch_ids))
        batch = []

    try:
        for row in remaining.itertuples(index=False):
            batch.append((row.id, row.UT, row.text))
            if len(batch) >= batch_size:
                flush_batch()
        flush_batch()
    finally:
        flush_shard()
        progress_bar.close()

    return {
        "remaining_before_run": total_remaining,
        "processed": processed,
        "errored": errored,
        "elapsed_seconds": time.monotonic() - start_time,
    }


# --------------------------------------------------------------------------
# Compaction
# --------------------------------------------------------------------------


def compact_and_validate(
    *,
    texts: pd.DataFrame,
    cache_dir: Path,
    output_path: Path,
    manifest_path: Path,
    model: str,
    prefix: str,
    endpoint: str,
    sources: Mapping[str, Path],
    repository_root: Path,
    allow_gaps: bool = False,
) -> dict[str, Any]:
    """Concatenate shard files into one validated ``embeddings.parquet`` + manifest."""
    shard_paths = _iter_shard_paths(cache_dir)
    if not shard_paths:
        raise EmbeddingsPrepError(f"No shards found in {cache_dir}.")

    combined = pa.concat_tables([pq.read_table(path, schema=SHARD_SCHEMA) for path in shard_paths])
    ids = combined.column("id").to_pylist()
    if len(ids) != len(set(ids)):
        raise EmbeddingsPrepError("Compacted embeddings contain duplicate ids.")

    expected_ids = set(texts["id"])
    got_ids = set(ids)
    extra_ids = sorted(got_ids - expected_ids)
    if extra_ids:
        raise EmbeddingsPrepError(f"Compacted embeddings contain unexpected ids: {extra_ids[:10]}")
    missing_ids = sorted(expected_ids - got_ids)
    if missing_ids and not allow_gaps:
        raise EmbeddingsPrepError(
            f"{len(missing_ids):,} publication ids have no embedding yet "
            f"(first few: {missing_ids[:10]}); rerun the build to resume before "
            "compacting, or pass allow_gaps=True to document the gap explicitly."
        )

    dims = {len(vector) for vector in combined.column("embedding").to_pylist()}
    if len(dims) != 1:
        raise EmbeddingsPrepError(f"Inconsistent embedding dimensionality: {sorted(dims)}")
    embedding_dim = next(iter(dims))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".part")
    pq.write_table(combined, tmp_path, compression="zstd")
    tmp_path.replace(output_path)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "text_prefix": prefix,
        "endpoint": endpoint,
        "embedding_dim": embedding_dim,
        "grain": "one row per publication id, joinable to dataset.parquet by id or UT",
        "primary_key": "id",
        "source_key": "UT",
        "columns": ["id", "UT", "embedding", "model"],
        "rows": {
            "expected": len(expected_ids),
            "embedded": len(got_ids),
            "missing": len(missing_ids),
        },
        "missing_ids": missing_ids,
        "sources": {
            name: source_signature(path, repository_root=repository_root)
            for name, path in sources.items()
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--shard-size", type=int, default=None)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Embed at most N not-yet-embedded publications this invocation. Each run "
            "caps the *next* N still-pending ids, so repeated invocations with the "
            "same --limit keep advancing rather than re-covering the same subset; for "
            "a fixed bounded pilot universe, pre-slice the texts frame via the Python "
            "API instead (see notebooks/data_processing/05_embeddings.ipynb)."
        ),
    )
    parser.add_argument("--cache-dir", type=Path, default=None, help="Override the shard cache directory, e.g. for a throwaway pilot run.")
    parser.add_argument("--no-compact", action="store_true", help="Run the batch build without compacting into embeddings.parquet.")
    parser.add_argument("--allow-gaps", action="store_true", help="Compact even if some ids never embedded successfully.")
    parser.add_argument("--no-progress", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    config = results_config.load_results_config()["embeddings_prep"]
    output_dir = REPO_ROOT / config["output_directory"]
    dataset_path = output_dir / "dataset.parquet"
    abstracts_path = output_dir / "dataset_abstracts.parquet"
    cache_dir = args.cache_dir or (output_dir / config["cache_subdirectory"])

    print(f"Loading dataset from {dataset_path} …", flush=True)
    dataset = pd.read_parquet(dataset_path, columns=["id", "UT", "title"])
    abstracts = pd.read_parquet(abstracts_path, columns=["UT", "abstract"])
    texts = build_embedding_texts(dataset, abstracts, prefix=config["text_prefix"])
    print(f"{len(texts):,} publications to embed. Cache: {cache_dir}", flush=True)

    try:
        stats = run_embedding_build(
            texts=texts,
            cache_dir=cache_dir,
            endpoint=config["endpoint"],
            model=config["model"],
            batch_size=args.batch_size or config["batch_size"],
            shard_size=args.shard_size or config["shard_size"],
            timeout=config["request_timeout_seconds"],
            max_retries=config["max_retries"],
            limit=args.limit,
            progress=not args.no_progress,
        )
    except EmbeddingsPrepError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Batch run complete: {stats}", flush=True)

    if args.no_compact:
        return 0

    try:
        manifest = compact_and_validate(
            texts=texts,
            cache_dir=cache_dir,
            output_path=output_dir / "embeddings.parquet",
            manifest_path=output_dir / "embeddings_manifest.json",
            model=config["model"],
            prefix=config["text_prefix"],
            endpoint=config["endpoint"],
            sources={"dataset": dataset_path, "dataset_abstracts": abstracts_path},
            repository_root=REPO_ROOT,
            allow_gaps=args.allow_gaps,
        )
    except EmbeddingsPrepError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        f"Compacted {manifest['rows']['embedded']:,} embeddings -> {output_dir / 'embeddings.parquet'}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
