# embeddings_pipeline.py
import os, json, hashlib, pathlib
from datetime import datetime
from typing import Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import requests

def _env():
    defaults = {
        "OUT_DIR": os.getenv("OUT_DIR", "./local_embedding_db"),
        "ID_COLUMN": os.getenv("EMBED_ID_COLUMN", "species_id"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        "OPENAI_EMBED_MODEL": os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"),
        "TEXT_FIELDS": [t.strip() for t in os.getenv(
            "TEXT_FIELDS", "species_name,species,genus,family,order,class,phylum,kingdom"
        ).split(",") if t.strip()],
        "FIELD_WEIGHTS": json.loads(os.getenv("FIELD_WEIGHTS_JSON", "{}") or "{}") or {
            "species_name": 1.3, "species": 1.3, "genus": 1.15, "family": 1.0,
            "order": 1.0, "class": 0.95, "phylum": 0.95, "kingdom": 0.9
        },
        "STAGING_BATCH_SIZE": int(os.getenv("STAGING_BATCH_SIZE", "512")),
        "API_BATCH_SIZE": int(os.getenv("API_BATCH_SIZE", "256")),
    }
    return defaults


# ----------------------------
# Minimal OpenAI client
# ----------------------------
def embed_texts_batch(
    texts: Union[str, Sequence[str]],
    *,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: int = 60,
) -> List[List[float]]:
    
    env = _env()
    items = [texts] if isinstance(texts, str) else list(texts)
    url = f"{(base_url or env['OPENAI_BASE_URL']).rstrip('/')}/embeddings"
    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {(api_key or env['OPENAI_API_KEY'])}",
            "Content-Type": "application/json",
        },
        json={"model": (model or env["OPENAI_EMBED_MODEL"]), "input": items},
        timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()
    return [d["embedding"] for d in data["data"]]

def _batched(seq: Sequence, n: int) -> Iterable[Sequence]:
    for i in range(0, len(seq), n):
        yield seq[i:i + n]

def _row_key(id_val, field, text) -> str:
    return hashlib.sha1(
        json.dumps([id_val, field, str(text)], ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

def _batch_hash(row_keys: Sequence[str]) -> str:
    h = hashlib.sha1()
    for k in sorted(row_keys):
        h.update(k.encode("utf-8"))
    return h.hexdigest()

# ----------------------------
# PHASE 1: Stage fixed batches (no API calls)
# ----------------------------
def stage_batches_from_df(
    df: pd.DataFrame,
    *,
    out_dir: Optional[str] = None,
    id_col: Optional[str] = None,
    text_fields: Optional[List[str]] = None,
    field_weights: Optional[dict] = None,
    include_labels: bool = True,
    batch_size: Optional[int] = None,
    skip_existing: bool = True,
) -> pathlib.Path:
    
    env = _env()
    out = pathlib.Path(out_dir or env["OUT_DIR"])
    batches_dir = out / "batches"
    batches_dir.mkdir(parents=True, exist_ok=True)

    id_col = id_col or env["ID_COLUMN"]
    text_fields = text_fields or env["TEXT_FIELDS"]
    field_weights = field_weights or env["FIELD_WEIGHTS"]
    batch_size = batch_size or env["STAGING_BATCH_SIZE"]

    long_df = _longify_df_for_embeddings(
        df, id_col=id_col, text_fields=text_fields,
        field_weights=field_weights, include_labels=include_labels
    )
    print(f"Staging {len(long_df)} rows into batches of size {batch_size}...")
    long_df["row_key"] = [_row_key(r[id_col], r["field"], r["text"]) for _, r in long_df.iterrows()]
    long_df = long_df.sort_values("row_key").reset_index(drop=True)

    for s in range(0, len(long_df), batch_size):
        part = long_df.iloc[s:s + batch_size].copy()
        b_hash = _batch_hash(part["row_key"].tolist())
        part["batch"] = b_hash
        dest = batches_dir / f"batch-{b_hash}.parquet"
        if skip_existing and dest.exists():
            continue
        part.to_parquet(dest, index=False)

    return batches_dir


# ----------------------------
# PHASE 2: Embed staged batches (skips ones already embedded)
# ----------------------------
def embed_staged_batches(
    *,
    out_dir: Optional[str] = None,
    openai_model: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    api_batch_size: Optional[int] = None,
    force: bool = False,
) -> pathlib.Path:
    
    env = _env()
    out = pathlib.Path(out_dir or env["OUT_DIR"])
    batches_dir = out / "batches"
    results_dir = out / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    api_batch_size = api_batch_size or env["API_BATCH_SIZE"]

    for bf in sorted(batches_dir.glob("batch-*.parquet")):
        b_hash = bf.stem.split("batch-")[-1]
        dest = results_dir / f"emb-{b_hash}.parquet"
        if dest.exists() and not force:
            continue

        part = pd.read_parquet(bf)
        texts = part["text"].tolist()

        all_vecs: List[List[float]] = []
        for chunk in _batched(texts, api_batch_size):
            all_vecs.extend(
                embed_texts_batch(
                    chunk,
                    model=openai_model or env["OPENAI_EMBED_MODEL"],
                    api_key=openai_api_key or env["OPENAI_API_KEY"],
                    base_url=openai_base_url or env["OPENAI_BASE_URL"],
                )
            )

        out_df = part.copy()
        out_df["embedding"] = all_vecs
        out_df.to_parquet(dest, index=False)

    return results_dir

# ----------------------------
# PHASE 3: Build DB from results
# ----------------------------
def finalize_database_from_results(
    *,
    out_dir: Optional[str] = None,
    id_col: Optional[str] = None,
    build_faiss: bool = True,
    rows_df: Optional[pd.DataFrame] = None,
    deduplicate: bool = True,
) -> Tuple[pathlib.Path, Optional[pathlib.Path]]:
    
    env = _env()
    out = pathlib.Path(out_dir or env["OUT_DIR"])
    id_col = id_col or env["ID_COLUMN"]

    parts = sorted((out / "results").glob("emb-*.parquet"))
    dfs = [pd.read_parquet(p) for p in parts]
    all_df = pd.concat(dfs, ignore_index=True)

    if deduplicate and "row_key" in all_df.columns:
        all_df = all_df.drop_duplicates(subset=["row_key"], keep="last").reset_index(drop=True)

    embeddings = np.asarray(all_df["embedding"].tolist(), dtype=np.float32)
    meta = all_df.drop(columns=["embedding"]).copy()
    meta["_vec_id"] = np.arange(len(meta), dtype=np.int64)

    meta_path = out / "meta.parquet"
    npy_path = out / "embeddings.npy"
    index_meta_path = out / "index.meta.json"
    faiss_path = out / "index.faiss"

    meta.to_parquet(meta_path, index=False)
    np.save(npy_path, embeddings)
    with open(index_meta_path, "w") as f:
        json.dump(
            {"dimension": int(embeddings.shape[1]),
             "model": env["OPENAI_EMBED_MODEL"],
             "created": datetime.utcnow().isoformat() + "Z",
             "vectors": int(embeddings.shape[0])},
            f, indent=2,
        )

    if rows_df is not None and id_col in rows_df.columns:
        rows_df.drop_duplicates(subset=[id_col]).to_parquet(out / "rows.parquet", index=False)

    faiss_index_path = None
    if build_faiss:
        import faiss 
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12
        vec_norm = embeddings / norms
        index = faiss.IndexFlatIP(vec_norm.shape[1])
        index.add(vec_norm)
        faiss.write_index(index, str(faiss_path))
        faiss_index_path = faiss_path

    return out, faiss_index_path

# ----------------------------
# Search helper (env-first)
# ----------------------------
def search(
    query_text: str,
    *,
    out_dir: Optional[str] = None,
    k_rows: int = 5,
    knn_candidates: int = 200,
    openai_model: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    id_col: Optional[str] = None,
) -> pd.DataFrame:
    
    env = _env()
    out = pathlib.Path(out_dir or env["OUT_DIR"])
    id_col = id_col or env["ID_COLUMN"]

    q = np.asarray(
        embed_texts_batch(
            query_text,
            model=openai_model or env["OPENAI_EMBED_MODEL"],
            api_key=openai_api_key or env["OPENAI_API_KEY"],
            base_url=openai_base_url or env["OPENAI_BASE_URL"],
        )[0],
        dtype=np.float32,
    )
    q = q / (np.linalg.norm(q) + 1e-12)
    q = q.reshape(1, -1)

    import faiss
    index = faiss.read_index(str(out / "index.faiss"))
    D, I = index.search(q, knn_candidates)

    meta = pd.read_parquet(out / "meta.parquet")
    rows_path = out / "rows.parquet"
    rows = pd.read_parquet(rows_path) if rows_path.exists() else pd.DataFrame()

    vec_idxs = I[0].tolist()
    scores = D[0].tolist()

    hits = meta.iloc[vec_idxs].copy().reset_index(drop=True)
    hits["score"] = scores
    hits["adj_score"] = hits["score"] * hits["weight"]

    best = (
        hits.sort_values("adj_score", ascending=False)
            .groupby(id_col, as_index=False).first()
            .rename(columns={"adj_score": "adj_score_final", "field": "match_field", "text": "match_text"})
            .sort_values("adj_score_final", ascending=False)
            .head(k_rows)
    )

    leading = [id_col, "score", "match_field", "match_text"]
    result = best.merge(rows, on=id_col, how="left") if not rows.empty else best
    other = [c for c in result.columns if c not in leading]
    return result[leading + other].reset_index(drop=True)


# ----------------------------
# Longify helper
# ----------------------------
def _longify_df_for_embeddings(
    df: pd.DataFrame,
    *,
    id_col: str,
    text_fields: List[str],
    field_weights: Optional[dict] = None,
    include_labels: bool = True,
) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        sid = r[id_col]
        for f in text_fields:
            val = r.get(f, None)
            if pd.isna(val) or str(val).strip() == "":
                continue
            text = f"{f}: {val}" if include_labels else str(val)
            w = (field_weights or {}).get(f, 1.0)
            rows.append((sid, f, text, float(w)))
    return pd.DataFrame(rows, columns=[id_col, "field", "text", "weight"])


# ----------------------------
# Compatibility function for legacy notebooks
# ----------------------------
def build_local_embedding_db_from_df(
    df,
    out_dir=None,
    batch_size=None,
    build_faiss=None,
    id_col=None,
    text_fields=None,
    field_weights=None,
    openai_model=None,
    openai_api_key=None,
    openai_base_url=None,
    host=None,
    model=None,
    **kwargs
):
    """
    Compatibility function for legacy notebooks that expect the old API.
    
    This function combines the three-phase embedding pipeline:
    1. stage_batches_from_df
    2. embed_staged_batches
    3. finalize_database_from_results
    
    Parameters are flexible to support both calling conventions from labels.ipynb and setup.ipynb.
    """
    import os
    from pathlib import Path
    
    # Handle parameter mappings for different calling conventions
    if out_dir is None:
        out_dir = os.getenv("OUT_DIR", "./local_embedding_db")
    
    # For setup.ipynb calling convention, map host/model to openai equivalents
    if host is not None and openai_base_url is None:
        openai_base_url = host
    if model is not None and openai_model is None:
        openai_model = model
        
    # Set defaults from environment or function defaults
    env = _env()
    if batch_size is None:
        batch_size = env["STAGING_BATCH_SIZE"]
    if build_faiss is None:
        build_faiss = True
    if id_col is None:
        id_col = env["ID_COLUMN"]
    if text_fields is None:
        text_fields = env["TEXT_FIELDS"]
    if field_weights is None:
        field_weights = env["FIELD_WEIGHTS"]
    if openai_model is None:
        openai_model = env["OPENAI_EMBED_MODEL"]
    if openai_api_key is None:
        openai_api_key = env["OPENAI_API_KEY"]
    if openai_base_url is None:
        openai_base_url = env["OPENAI_BASE_URL"]
    
    # Phase 1: Stage batches
    print("Phase 1: Staging batches...")
    stage_batches_from_df(
        df=df,
        out_dir=out_dir,
        id_col=id_col,
        text_fields=text_fields,
        field_weights=field_weights,
        batch_size=batch_size
    )
    
    # Phase 2: Embed staged batches
    print("Phase 2: Embedding batches...")
    embed_staged_batches(
        out_dir=out_dir,
        openai_model=openai_model,
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        api_batch_size=batch_size
    )
    
    # Phase 3: Finalize database
    print("Phase 3: Finalizing database...")
    result = finalize_database_from_results(
        out_dir=out_dir,
        id_col=id_col,
        build_faiss=build_faiss,
        rows_df=df
    )
    
    print("Embedding database built successfully.")
    return result
