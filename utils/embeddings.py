# embeddings_pipeline.py
import os, json, hashlib, pathlib
from datetime import datetime
from typing import Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import requests

# ----------------------------
# Minimal OpenAI client
# ----------------------------
def embed_texts_batch(
    texts: Union[str, Sequence[str]]
) -> List[List[float]]:
    
    items = [texts] if isinstance(texts, str) else list(texts)
    url = f"{(os.getenv('OPENAI_BASE_URL')).rstrip('/')}/embeddings"
    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {(os.getenv('OPENAI_API_KEY'))}",
            "Content-Type": "application/json",
        },
        json={"model": (os.getenv('OPENAI_EMBED_MODEL')), "input": items}
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
    text_fields: List[str],
    field_weights: dict,
    out_dir: str = "osf-data/gbif-taxonomy-backbone/database/embedding_db",
    id_col: str = "species_id",
    include_labels: bool = True,
    batch_size: int = 512,
    skip_existing: bool = True,
) -> pathlib.Path:
    
    cnt= 0
    out = pathlib.Path(out_dir)
    batches_dir = out / "batches"
    batches_dir.mkdir(parents=True, exist_ok=True)

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
            print('Skipping batch ', dest)
            cnt = cnt + 1
            continue
        part.to_parquet(dest, index=False)

    print('Skipped batches = ', cnt)
    return batches_dir


# ----------------------------
# PHASE 2: Embed staged batches (skips ones already embedded)
# ----------------------------
def embed_staged_batches(
    out_dir: str = "osf-data/gbif-taxonomy-backbone/database/embedding_db",
    api_batch_size: int = 256,
    force: bool = False,
) -> pathlib.Path:
    
    cnt=0
    out = pathlib.Path(out_dir)
    batches_dir = out / "batches"
    results_dir = out / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    for bf in sorted(batches_dir.glob("batch-*.parquet")):
        b_hash = bf.stem.split("batch-")[-1]
        dest = results_dir / f"emb-{b_hash}.parquet"
        if dest.exists() and not force:
            print('Skipping batch: ', dest)
            cnt = cnt + 1
            continue

        part = pd.read_parquet(bf)
        texts = part["text"].tolist()

        all_vecs: List[List[float]] = []
        for chunk in _batched(texts, api_batch_size):
            all_vecs.extend(
                embed_texts_batch(
                    chunk
                )
            )
        out_df = part.copy()
        out_df["embedding"] = all_vecs
        out_df.to_parquet(dest, index=False)
    print('Skipped batches = ', cnt)
    return results_dir

# ----------------------------
# PHASE 3: Build DB from results
# ----------------------------
def finalize_database_from_results(
    out_dir: str = "osf-data/gbif-taxonomy-backbone/database/embedding_db",
    id_col: str = "species_id",
    build_faiss: bool = True,
    rows_df: Optional[pd.DataFrame] = None,
    deduplicate: bool = True,
) -> Tuple[pathlib.Path, Optional[pathlib.Path]]:
    
    out = pathlib.Path(out_dir)
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
             "model": os.getenv('OPENAI_EMBED_MODEL'),
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
    id_col: str = "species_id",
    out_dir: str = "osf-data/gbif-taxonomy-backdone/database/embedding_db",
    k_rows: int = 5,
    knn_candidates: int = 200
) -> pd.DataFrame:
    
    out = pathlib.Path(out_dir)
    q = np.asarray(
        embed_texts_batch(
            query_text,
            model=os.getenv('OPENAI_EMBED_MODEL'),
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENAI_BASE_URL'),
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
