"""Utilities for building and querying the Tantivy-backed taxonomy index."""

from .config import FilterConfig, IndexConfig, maybe_load_dotenv
from .indexing import build_index
from .search import SearchResult, TaxonSearcher
from .candidates import extract_taxon_candidates
from .schema import build_schema
from .utils import edge_ngrams, make_name_text, norm_keyword, split_vernaculars

__all__ = [
    "FilterConfig",
    "IndexConfig",
    "TaxonSearcher",
    "SearchResult",
    "build_index",
    "build_schema",
    "extract_taxon_candidates",
    "edge_ngrams",
    "make_name_text",
    "norm_keyword",
    "split_vernaculars",
    "maybe_load_dotenv",
]
