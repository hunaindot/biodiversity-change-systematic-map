"""
Set up - Required data, embeddings,

1) Load environment (.env)
2) Load WOS data
3) Download/prepare taxonomy store
4) Build embeddings (stage -> embed)
5) Finalize and save to FAISS database

This uses different methods from utils:
- utils.data: load_data
- utils.taxonomy: load_taxonomy, load_taxon_lineage_df
- utils.embeddings: stage_batches_from_df, embed_staged_batches, finalize_database_from_results
"""

from dotenv import load_dotenv
from utils.data import load_data
from utils.taxonomy import load_taxonomy, load_taxon_lineage_df
from utils.embeddings import (
    stage_batches_from_df,
    embed_staged_batches,
    finalize_database_from_results,
)

import os
import json
import sys
from typing import Dict, List


DEFAULT_FIELD_WEIGHTS: Dict[str, float] = {
    "species": 1.0,
    "genus": 1.0,
    "family": 1.0,
    "order": 1.0,
    "class": 1.0,
    "phylum": 1.0,
    "kingdom": 1.0,
}


def get_text_fields_from_env() -> List[str]:
    """Read TEXT_FIELDS from env or fall back to taxonomy name columns."""
    fields_raw = os.getenv("TEXT_FIELDS", "species,genus,family,order,class,phylum,kingdom")
    fields = [t.strip() for t in fields_raw.split(",") if t.strip()]
    if not fields:
        fields = list(DEFAULT_FIELD_WEIGHTS.keys())
    return fields


def get_field_weights_from_env() -> Dict[str, float]:
    """Read FIELD_WEIGHTS_JSON from env, with a safe fallback."""
    raw = os.getenv("FIELD_WEIGHTS_JSON", "{}") or "{}"
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            return DEFAULT_FIELD_WEIGHTS
        # Coerce values to float when possible
        weights: Dict[str, float] = {}
        for k, v in parsed.items():
            try:
                weights[k] = float(v)
            except Exception:
                continue
        return weights or DEFAULT_FIELD_WEIGHTS
    except Exception:
        return DEFAULT_FIELD_WEIGHTS


def main() -> int:
    # 0) Environment
    load_dotenv()
    print("Environment loaded (.env)")

    # 1) Downloads / Data
    print("Loading WOS data...")
    df, df_sample = load_data()
    try:
        print(f"Loaded WOS rows: {len(df)} | sample rows: {len(df_sample)}")
    except Exception:
        print("Loaded WOS data.")

    print("Ensuring taxonomy store is available...")
    load_taxonomy()

    # 2) Build Embeddings
    print("Loading taxonomy lineage view...")
    taxon_df = load_taxon_lineage_df()
    print("Taxonomy species loaded:", len(taxon_df))

    # Filter to Mammalia class within Animalia/Chordata
    print("Filtering taxonomy to Mammalia within Animalia/Chordata...")
    taxon_df = taxon_df[
        (taxon_df["kingdom"] == "Animalia") &
        (taxon_df["phylum"] == "Chordata") &
        (taxon_df["class"] == "Mammalia")
    ].copy()
    print("Taxonomy species sampled for Mammalia class:", len(taxon_df))

    text_fields = get_text_fields_from_env()
    field_weights = get_field_weights_from_env()
    print("Using text fields:", text_fields)
    print("Using field weights:", field_weights)

    print("Staging taxonomy batches...")
    stage_batches_from_df(
        df=taxon_df,
        text_fields=text_fields,
        field_weights=field_weights,
    )

    print("Embedding staged batches...")
    embed_staged_batches()

    # 3) Save embeddings into database
    print("Finalizing and saving embeddings to FAISS database...")
    finalize_database_from_results(rows_df=df, build_faiss=True)

    print("""
        - WOS data loaded
        - Taxonomy ensured and filtered
        - Batches staged and embedded
        - FAISS database built
"""
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.")
        raise
