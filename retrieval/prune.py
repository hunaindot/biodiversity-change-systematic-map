import re
from tantivy import Query

def _escape_quotes(s: str) -> str:
    return s.replace('"', '\\"')

def _clean_candidate(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s.strip(" \t\n\r,;:()[]{}")

def _scientific_like(s: str) -> bool:
    # keep scientific-looking ones even if index misses (optional)
    return bool(re.match(r"^[A-Z][a-z]{2,}\s+([a-z][a-z-]{1,}|sp\.|spp\.)$", s))

class CandidatePruner:
    def __init__(self, index, searcher):
        self.index = index
        self.searcher = searcher
        self.cache = {}

        self.exact_fields = ["canonical_name","scientific_name","generic_name","vernaculars","name_text"]
        self.edge_fields  = ["canonical_edge","scientific_edge","generic_edge","vernacular_edge"]

    def _query_for(self, cand: str) -> Query:
        cand = _clean_candidate(cand)
        if not cand:
            return None

        # Exact clause: phrase if multiword
        exact_qs = f"\"{_escape_quotes(cand)}\"" if " " in cand else cand
        q_exact = Query.boost_query(self.index.parse_query(exact_qs, self.exact_fields), 3.0)

        # Edge clause: AND over tokens (uppercase AND!)
        toks = re.findall(r"[A-Za-z0-9]+", cand.lower())
        toks = [t for t in toks if len(t) >= 3]
        if not toks:
            return q_exact

        edge_qs = " AND ".join(toks)
        q_edge = Query.boost_query(self.index.parse_query(edge_qs, self.edge_fields), 1.0)

        return Query.disjunction_max_query([q_exact, q_edge], tie_breaker=0.1)

    def keep(self, cand: str) -> bool:
        cand = _clean_candidate(cand)
        if not cand:
            return False

        key = cand.lower()
        if key in self.cache:
            return self.cache[key]

        # optional: keep scientific-looking strings for recall
        if _scientific_like(cand):
            self.cache[key] = True
            return True

        q = self._query_for(cand)
        if q is None:
            self.cache[key] = False
            return False

        ok = len(self.searcher.search(q, 1).hits) > 0
        self.cache[key] = ok
        return ok

    def filter(self, candidates, max_keep=200):
        out, seen = [], set()
        for c in candidates:
            c2 = _clean_candidate(c)
            k = c2.lower()
            if not c2 or k in seen:
                continue
            seen.add(k)
            if self.keep(c2):
                out.append(c2)
                if len(out) >= max_keep:
                    break
        return out
