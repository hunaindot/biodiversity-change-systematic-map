# retrieval

Helpers to build and query the Tantivy taxonomy index that currently lives in `tantivy_gbif_index_setup.ipynb`. Everything stays in code so it is easier to reuse in scripts or batch jobs.

## Layout
- `config.py`: defaults + env loading (`IndexConfig`, `FilterConfig`).
- `schema.py`: Tantivy schema definition.
- `indexing.py`: chunked CSV reader and index builder (`build_index`).
- `search.py`: lightweight search wrapper (`TaxonSearcher`, `SearchResult`).
- `candidates.py`: text helper to pull likely taxon mentions.
- `cli.py`: small CLI (`python -m retrieval.cli ...`).

## Environment
Defaults match the notebook. Override via `.env` or real env vars:
- `RETRIEVAL_CSV_PATH`: `data/gbif/curated/gbif_curated.csv`
- `RETRIEVAL_INDEX_DIR`: `data/retrieval/tantivy_gbif_taxa_index`
- `RETRIEVAL_EDGE_MIN`: `3`
- `RETRIEVAL_EDGE_MAX`: `10`
- `RETRIEVAL_NUM_THREADS`: `min(6, cpu-2)`
- `RETRIEVAL_HEAP_SIZE_BYTES`: `1500000000`
- `RETRIEVAL_CHUNKSIZE`: `50000`

Status/rank filters and selected columns mirror the notebook constants.

## Quick use
- Build (cleans the index dir by default):
  ```
  python -m retrieval.cli build-index
  ```
- Search:
  ```
  python -m retrieval.cli search '"mammal" OR panthe'
  ```
- Extract candidate taxa from text:
  ```
  python -m retrieval.cli candidates --file path/to/text.txt
  ```

Programmatic usage:
```python
from retrieval import IndexConfig, FilterConfig, build_index, TaxonSearcher, extract_taxon_candidates

cfg = IndexConfig.from_env()
build_index(cfg, FilterConfig())

searcher = TaxonSearcher(cfg.index_dir)
results = searcher.search("Panthera leo", limit=5)

abstract = "..."
candidates = extract_taxon_candidates(abstract)
```
