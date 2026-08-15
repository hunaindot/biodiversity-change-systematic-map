"""Tests colocated with the resumable per-publication embeddings builder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence
from unittest.mock import MagicMock

import pandas as pd
import pytest
import requests

from data_helpers.prep import embeddings_prep as ep


# --------------------------------------------------------------------------
# Text mapping
# --------------------------------------------------------------------------


def test_build_embedding_texts_joins_and_prefixes() -> None:
    dataset = pd.DataFrame(
        {
            "id": [1, 2],
            "UT": ["WOS:1", "WOS:2"],
            "title": [" Title one ", "Title two"],
        }
    )
    abstracts = pd.DataFrame(
        {"UT": ["WOS:1", "WOS:2"], "abstract": ["Abstract one.", " Abstract two. "]}
    )
    texts = ep.build_embedding_texts(dataset, abstracts, prefix="search_document: ")
    assert list(texts.columns) == ["id", "UT", "text"]
    assert texts.loc[texts["id"] == 1, "text"].item() == "search_document: Title one. Abstract one."
    assert texts.loc[texts["id"] == 2, "text"].item() == "search_document: Title two. Abstract two."


def test_build_embedding_texts_raises_on_mismatched_ut_sets() -> None:
    dataset = pd.DataFrame({"id": [1, 2], "UT": ["WOS:1", "WOS:2"], "title": ["a", "b"]})
    abstracts = pd.DataFrame({"UT": ["WOS:1", "WOS:3"], "abstract": ["x", "y"]})
    with pytest.raises(ep.EmbeddingsPrepError, match="UT sets do not match"):
        ep.build_embedding_texts(dataset, abstracts, prefix="")


def test_build_embedding_texts_raises_on_duplicate_ut() -> None:
    dataset = pd.DataFrame({"id": [1, 2], "UT": ["WOS:1", "WOS:1"], "title": ["a", "b"]})
    abstracts = pd.DataFrame({"UT": ["WOS:1"], "abstract": ["x"]})
    with pytest.raises(ep.EmbeddingsPrepError, match="not unique"):
        ep.build_embedding_texts(dataset, abstracts, prefix="")


# --------------------------------------------------------------------------
# HTTP client
# --------------------------------------------------------------------------


def _mock_response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    return response


def test_embedding_client_embed_batch_happy_path() -> None:
    session = MagicMock()
    session.post.return_value = _mock_response({"embeddings": [[0.1, 0.2], [0.3, 0.4]]})
    client = ep.EmbeddingClient(endpoint="http://x/api/embed", model="m", session=session)
    result = client.embed_batch(["a", "b"])
    assert result == [[0.1, 0.2], [0.3, 0.4]]
    session.post.assert_called_once()
    _, kwargs = session.post.call_args
    assert kwargs["json"] == {"model": "m", "input": ["a", "b"]}


def test_embedding_client_embed_batch_shape_mismatch_raises() -> None:
    session = MagicMock()
    session.post.return_value = _mock_response({"embeddings": [[0.1, 0.2]]})
    client = ep.EmbeddingClient(endpoint="http://x/api/embed", model="m", session=session)
    with pytest.raises(ep.EmbeddingsPrepError, match="vectors for a batch"):
        client.embed_batch(["a", "b"])


def test_embedding_client_embed_batch_inconsistent_dims_raises() -> None:
    session = MagicMock()
    session.post.return_value = _mock_response({"embeddings": [[0.1, 0.2], [0.3, 0.4, 0.5]]})
    client = ep.EmbeddingClient(endpoint="http://x/api/embed", model="m", session=session)
    with pytest.raises(ep.EmbeddingsPrepError, match="inconsistent dimensionality"):
        client.embed_batch(["a", "b"])


def test_embedding_client_embed_batch_empty_returns_empty() -> None:
    session = MagicMock()
    client = ep.EmbeddingClient(endpoint="http://x/api/embed", model="m", session=session)
    assert client.embed_batch([]) == []
    session.post.assert_not_called()


# --------------------------------------------------------------------------
# Shard cache
# --------------------------------------------------------------------------


def test_scan_cache_empty_dir(tmp_path: Path) -> None:
    done_ids, next_index = ep.scan_cache(tmp_path / "cache")
    assert done_ids == set()
    assert next_index == 0


def test_scan_cache_reads_valid_shards_and_ignores_partial(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    ep._write_shard(cache_dir, 0, [1, 2], ["WOS:1", "WOS:2"], [[0.1, 0.2], [0.3, 0.4]], "m")
    # Simulate a crash mid-shard: only the .part file exists for shard 1.
    (cache_dir / "shard_00001.parquet.part").write_bytes(b"not a real parquet file")

    done_ids, next_index = ep.scan_cache(cache_dir)
    assert done_ids == {1, 2}
    assert next_index == 1  # the next shard reuses index 1; the crashed .part is ignored


def test_scan_cache_raises_on_duplicate_ids_within_a_shard(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    ep._write_shard(cache_dir, 0, [1, 1], ["WOS:1", "WOS:1"], [[0.1], [0.2]], "m")
    with pytest.raises(ep.EmbeddingsPrepError, match="duplicate ids"):
        ep.scan_cache(cache_dir)


# --------------------------------------------------------------------------
# Batch runner
# --------------------------------------------------------------------------


class _FakeClient:
    """Duck-typed stand-in for EmbeddingClient: no network, deterministic vectors."""

    def __init__(self, *, fail_texts: set[str] | None = None, always_fail: bool = False) -> None:
        self.fail_texts = fail_texts or set()
        self.always_fail = always_fail
        self.calls: list[list[str]] = []

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        if self.always_fail or (self.fail_texts & set(texts)):
            raise requests.RequestException("simulated failure")
        return [[float(len(text)), 0.0] for text in texts]


def _texts_frame(n: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": range(1, n + 1),
            "UT": [f"WOS:{i}" for i in range(1, n + 1)],
            "text": [f"text number {i}" for i in range(1, n + 1)],
        }
    )


def test_run_embedding_build_writes_shards_and_resumes(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    texts = _texts_frame(10)
    client = _FakeClient()

    stats = ep.run_embedding_build(
        texts=texts,
        cache_dir=cache_dir,
        endpoint="http://x",
        model="m",
        batch_size=3,
        shard_size=4,
        client=client,
        progress=False,
    )
    assert stats["remaining_before_run"] == 10
    assert stats["processed"] == 10
    assert stats["errored"] == 0
    done_ids, _ = ep.scan_cache(cache_dir)
    assert done_ids == set(range(1, 11))

    # A second run against the same cache with a fresh client processes nothing new.
    client_two = _FakeClient()
    stats_two = ep.run_embedding_build(
        texts=texts,
        cache_dir=cache_dir,
        endpoint="http://x",
        model="m",
        batch_size=3,
        shard_size=4,
        client=client_two,
        progress=False,
    )
    assert stats_two["remaining_before_run"] == 0
    assert stats_two["processed"] == 0
    assert client_two.calls == []


def test_run_embedding_build_logs_errors_and_continues(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    texts = _texts_frame(6)
    # batch_size=3 -> batches are ids [1,2,3] and [4,5,6]; fail only the first batch.
    client = _FakeClient(fail_texts={"text number 2"})

    stats = ep.run_embedding_build(
        texts=texts,
        cache_dir=cache_dir,
        endpoint="http://x",
        model="m",
        batch_size=3,
        shard_size=10,
        client=client,
        progress=False,
    )
    assert stats["errored"] == 3
    assert stats["processed"] == 6
    done_ids, _ = ep.scan_cache(cache_dir)
    assert done_ids == {4, 5, 6}

    errors_path = cache_dir / ep.ERRORS_FILENAME
    assert errors_path.exists()
    logged = [json.loads(line) for line in errors_path.read_text().splitlines()]
    assert logged[0]["ids"] == [1, 2, 3]

    # Resuming retries exactly the ids that never made it into a shard.
    client_two = _FakeClient()
    stats_two = ep.run_embedding_build(
        texts=texts,
        cache_dir=cache_dir,
        endpoint="http://x",
        model="m",
        batch_size=3,
        shard_size=10,
        client=client_two,
        progress=False,
    )
    assert stats_two["remaining_before_run"] == 3
    done_ids_after, _ = ep.scan_cache(cache_dir)
    assert done_ids_after == {1, 2, 3, 4, 5, 6}


def test_run_embedding_build_aborts_after_consecutive_errors(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    texts = _texts_frame(20)
    client = _FakeClient(always_fail=True)

    with pytest.raises(ep.EmbeddingsPrepError, match="consecutive batches failed"):
        ep.run_embedding_build(
            texts=texts,
            cache_dir=cache_dir,
            endpoint="http://x",
            model="m",
            batch_size=2,
            shard_size=10,
            client=client,
            max_consecutive_batch_errors=3,
            progress=False,
        )


def test_run_embedding_build_respects_limit(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    texts = _texts_frame(10)
    client = _FakeClient()
    stats = ep.run_embedding_build(
        texts=texts,
        cache_dir=cache_dir,
        endpoint="http://x",
        model="m",
        batch_size=3,
        shard_size=10,
        limit=4,
        client=client,
        progress=False,
    )
    assert stats["remaining_before_run"] == 4
    assert stats["processed"] == 4


# --------------------------------------------------------------------------
# Compaction
# --------------------------------------------------------------------------


def test_compact_and_validate_success(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    texts = _texts_frame(5)
    ep.run_embedding_build(
        texts=texts,
        cache_dir=cache_dir,
        endpoint="http://x",
        model="m",
        batch_size=2,
        shard_size=2,
        client=_FakeClient(),
        progress=False,
    )
    dataset_path = tmp_path / "dataset.parquet"
    abstracts_path = tmp_path / "dataset_abstracts.parquet"
    pd.DataFrame({"id": [1], "UT": ["WOS:1"], "title": ["t"]}).to_parquet(dataset_path)
    pd.DataFrame({"UT": ["WOS:1"], "abstract": ["a"]}).to_parquet(abstracts_path)

    manifest = ep.compact_and_validate(
        texts=texts,
        cache_dir=cache_dir,
        output_path=tmp_path / "embeddings.parquet",
        manifest_path=tmp_path / "embeddings_manifest.json",
        model="m",
        prefix="search_document: ",
        endpoint="http://x",
        sources={"dataset": dataset_path, "dataset_abstracts": abstracts_path},
        repository_root=tmp_path,
    )
    assert manifest["rows"] == {"expected": 5, "embedded": 5, "missing": 0}
    assert manifest["embedding_dim"] == 2
    assert manifest["columns"] == ["id", "UT", "embedding", "model"]

    combined = pd.read_parquet(tmp_path / "embeddings.parquet")
    assert sorted(combined["id"]) == [1, 2, 3, 4, 5]
    assert set(combined["UT"]) == {f"WOS:{i}" for i in range(1, 6)}


def test_compact_and_validate_missing_ids_raises_without_allow_gaps(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    texts = _texts_frame(5)
    ep.run_embedding_build(
        texts=texts,
        cache_dir=cache_dir,
        endpoint="http://x",
        model="m",
        batch_size=2,
        shard_size=2,
        limit=3,
        client=_FakeClient(),
        progress=False,
    )
    with pytest.raises(ep.EmbeddingsPrepError, match="have no embedding yet"):
        ep.compact_and_validate(
            texts=texts,
            cache_dir=cache_dir,
            output_path=tmp_path / "embeddings.parquet",
            manifest_path=tmp_path / "embeddings_manifest.json",
            model="m",
            prefix="search_document: ",
            endpoint="http://x",
            sources={},
            repository_root=tmp_path,
        )


def test_compact_and_validate_missing_ids_with_allow_gaps_documents_gap(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    texts = _texts_frame(5)
    ep.run_embedding_build(
        texts=texts,
        cache_dir=cache_dir,
        endpoint="http://x",
        model="m",
        batch_size=2,
        shard_size=2,
        limit=3,
        client=_FakeClient(),
        progress=False,
    )
    manifest = ep.compact_and_validate(
        texts=texts,
        cache_dir=cache_dir,
        output_path=tmp_path / "embeddings.parquet",
        manifest_path=tmp_path / "embeddings_manifest.json",
        model="m",
        prefix="search_document: ",
        endpoint="http://x",
        sources={},
        repository_root=tmp_path,
        allow_gaps=True,
    )
    assert manifest["rows"] == {"expected": 5, "embedded": 3, "missing": 2}
    assert manifest["missing_ids"] == [4, 5]


def test_compact_and_validate_no_shards_raises(tmp_path: Path) -> None:
    with pytest.raises(ep.EmbeddingsPrepError, match="No shards found"):
        ep.compact_and_validate(
            texts=_texts_frame(1),
            cache_dir=tmp_path / "empty_cache",
            output_path=tmp_path / "embeddings.parquet",
            manifest_path=tmp_path / "embeddings_manifest.json",
            model="m",
            prefix="",
            endpoint="http://x",
            sources={},
            repository_root=tmp_path,
        )
