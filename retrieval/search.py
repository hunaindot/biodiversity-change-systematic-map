# retrieval/search.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Sequence

import tantivy
from tantivy import Query

from .candidates import extract_taxon_candidates
from .prune import CandidatePruner


def _first(doc, field: str, default=None):
    """tantivy==0.25.1: doc[field] is always a list (multi-valued)."""
    try:
        vals = doc[field]
        return vals[0] if vals else default
    except KeyError:
        return default


def _escape_quotes(s: str) -> str:
    return s.replace('"', '\\"')


def build_or_query(cands: Sequence[str]) -> str:
    """
    Build a query string for Tantivy QueryParser.
    IMPORTANT: use uppercase OR, and quote multiword phrases.
    """
    parts = []
    for c in cands:
        c = (c or "").strip()
        if not c:
            continue
        parts.append(f"\"{_escape_quotes(c)}\"" if " " in c else c)
    return " OR ".join(parts)

@dataclass
class SearchResult:
    raw_candidates: List[str]
    kept_candidates: List[str]
    hits: List[Dict[str, Any]]


STORED_FIELDS = [
    "taxon_id",
    "species_id",
    "canonical_name",
    "scientific_name",
    "generic_name",
    "vernaculars",
    "taxon_rank",
    "taxonomic_status",
    "kingdom",
    "phylum",
    "class",
    "order",
    "family",
    "genus",
    "source",
    "marine",
    "freshwater",
    "terrestrial",
    "extinct",
    "hybrid",
    "age_days",
    "size_mm",
    "mass_g",
    "curated_description",
    "scientific_name_authorship",
    "lifeform_curated",
    "habitat_curated",
    "livingperiod_curated",
    "nomenclatural_status",
]


@dataclass
class SearchConfig:
    # Fields to search normally (strong)
    exact_fields: List[str]
    # Edge-gram fields (weak fallback)
    edge_fields: List[str]

    exact_boost: float = 3.0
    edge_boost: float = 1.0
    tie_breaker: float = 0.1

    max_candidates: int = 300       # from extractor
    max_keep_candidates: int = 200  # after pruning
    add_keyphrases: bool = True     # extractor knob


DEFAULT_CFG = SearchConfig(
    exact_fields=["canonical_name", "scientific_name", "generic_name", "vernaculars", "name_text"],
    edge_fields=["canonical_edge", "scientific_edge", "generic_edge", "vernacular_edge"],
)


class TaxonSearcher:
    """
    End-to-end:
      (title+abstract) -> extract candidates -> prune using Tantivy -> query -> hits -> docs
    """

    def __init__(self, index_dir: str, cfg: SearchConfig = DEFAULT_CFG):
        self.cfg = cfg

        # tantivy==0.25.1 requires str paths (not Path objects)
        self.index = tantivy.Index.open(str(index_dir))
        self.index.reload()
        self.searcher = self.index.searcher()

        # Keep one pruner instance so its cache speeds up over many docs
        self.pruner = CandidatePruner(self.index, self.searcher)

    def refresh(self):
        """Call if you re-built / updated the index and want newest data."""
        self.index.reload()
        self.searcher = self.index.searcher()
        # pruner needs the new searcher too
        self.pruner = CandidatePruner(self.index, self.searcher)

    def extract_candidates(self, text: str) -> List[str]:
        return extract_taxon_candidates(
            text or "",
            max_terms=self.cfg.max_candidates,
            add_keyphrases=self.cfg.add_keyphrases,
        )


    def prune_candidates(self, candidates: List[str]) -> List[str]:
        return self.pruner.filter(candidates, max_keep=self.cfg.max_keep_candidates)

    def build_query(self, candidates: List[str]) -> Query:
        qs = build_or_query(candidates)
        if not qs:
            raise ValueError("No candidates to search after pruning.")

        q_exact = Query.boost_query(
            self.index.parse_query(qs, self.cfg.exact_fields),
            self.cfg.exact_boost,
        )
        q_edge = Query.boost_query(
            self.index.parse_query(qs, self.cfg.edge_fields),
            self.cfg.edge_boost,
        )
        return Query.disjunction_max_query([q_exact, q_edge], tie_breaker=self.cfg.tie_breaker)

    def search_from_candidates(self, candidates: List[str], limit: int = 40) -> List[Dict[str, Any]]:
        q = self.build_query(candidates)
        hits = self.searcher.search(q, limit).hits

        results = []
        for score, addr in hits:
            doc = self.searcher.doc(addr)
            results.append({
                "score": score,
                **{fld: _first(doc, fld) for fld in STORED_FIELDS},
            })
        return results
    
    def search(self, text: str,  limit: int = 40) -> SearchResult:
        raw = self.extract_candidates(text)
        kept = self.prune_candidates(raw)
        hits = self.search_from_candidates(kept, limit=limit) if kept else []
        return SearchResult(raw_candidates=raw, kept_candidates=kept, hits=hits)
