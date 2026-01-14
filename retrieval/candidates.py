import re
from collections import Counter

STOP = set("""
a an the and or but if while although though however therefore thus
in on at by for from with without
we i our us they their them he she it its this that these those
""".split())

# Avoid the worst false "Genus" tokens (keep SMALL so recall stays high)
BAD_GENUS = {
    "We","I","Our","The","A","An","This","That","These","Those",
    "In","On","At","By","For","From","With","Without","As","And","Or","But",
    "However","Moreover","Therefore","Thus","Does","Do","Did","Are","Is","Was","Were",
    "Although","While","When","Where","Currently","Widespread"
}

GENUS = r"[A-Z][a-z]{2,}"
EPITHET = r"[a-z][a-z-]{1,}"

re_trinomial = re.compile(rf"\b({GENUS})\s+({EPITHET})\s+({EPITHET})\b")
re_binomial  = re.compile(rf"\b({GENUS})\s+({EPITHET})\b")
re_genus_qual = re.compile(rf"\b({GENUS})\s+(sp\.?|spp\.?|cf\.?|aff\.?|nr\.?|subsp\.?|var\.?)\b", re.IGNORECASE)
re_abbrev    = re.compile(r"\b([A-Z])\.\s*([a-z][a-z-]{1,})\b")

# common name before parentheses containing a latin name: "ostrich (Struthio camelus)"
re_common_before_latin = re.compile(
    rf"\b([a-z][a-z-]+(?:\s+[a-z][a-z-]+){{0,3}})\s*\(\s*{GENUS}\s+{EPITHET}"
)

def _good_binomial(genus: str, epithet: str) -> bool:
    if genus in BAD_GENUS:
        return False
    if epithet in STOP:
        return False
    return True

def _keyphrases(text: str, max_phrases: int = 80) -> list[str]:
    """
    Lightweight RAKE-ish keyphrases:
    - split on stopwords
    - return 1–3 word phrases (ranked by frequency/length)
    High recall; pruning later removes general words.
    """
    tokens = re.findall(r"[a-z][a-z-]+", text.lower())
    chunks, buf = [], []
    for tok in tokens:
        if tok in STOP:
            if buf:
                chunks.append(buf); buf = []
        else:
            buf.append(tok)
            if len(buf) >= 6:
                chunks.append(buf); buf = []
    if buf:
        chunks.append(buf)

    phrases = []
    for ch in chunks:
        for n in (3, 2, 1):
            for i in range(0, max(0, len(ch) - n + 1)):
                p = " ".join(ch[i:i+n])
                if len(p) >= 4:
                    phrases.append(p)

    c = Counter(phrases)
    ranked = sorted(c.items(), key=lambda kv: (kv[1], len(kv[0])), reverse=True)
    return [k for k,_ in ranked[:max_phrases]]

def extract_taxon_candidates(text: str, max_terms: int = 250, add_keyphrases: bool = True) -> list[str]:
    """
    High-recall candidate extraction.
    Output is intentionally noisy; prune with Tantivy next.
    """
    if not text:
        return []

    found = []  # (priority, position, term)

    # 1) trinomial then binomial (highest value)
    for m in re_trinomial.finditer(text):
        g, s1, s2 = m.group(1), m.group(2), m.group(3)
        if _good_binomial(g, s1):
            found.append((0, m.start(), f"{g} {s1} {s2}"))

    for m in re_binomial.finditer(text):
        g, s = m.group(1), m.group(2)
        if _good_binomial(g, s):
            found.append((0, m.start(), f"{g} {s}"))

    # for abbrev expansion: keep seen genera in order
    seen_genera = [(pos, term.split()[0]) for _, pos, term in found]

    # 2) genus qualifiers: "Genus sp."
    for m in re_genus_qual.finditer(text):
        g = m.group(1)
        qual = m.group(2).replace(" ", "")
        if g not in BAD_GENUS:
            found.append((1, m.start(), f"{g} {qual}"))

    # 3) abbreviated genus: "S. camelus"
    for m in re_abbrev.finditer(text):
        pos = m.start()
        init, epit = m.group(1), m.group(2)
        if epit in STOP:
            continue

        expanded = None
        for gpos, g in reversed(seen_genera):
            if gpos < pos and g[0] == init:
                expanded = f"{g} {epit}"
                break

        found.append((2, pos, expanded if expanded else f"{init}. {epit}"))

    # 4) common name near latin: "ostrich (Struthio camelus)"
    for m in re_common_before_latin.finditer(text):
        phrase = m.group(1).strip().lower()
        if phrase and phrase not in STOP:
            found.append((3, m.start(), phrase))

    # 5) keyphrases (recall booster; pruner will remove junk)
    if add_keyphrases:
        for kp in _keyphrases(text, max_phrases=120):
            found.append((5, 10**9, kp))

    # sort + dedupe (keep best priority/earliest)
    found.sort(key=lambda x: (x[0], x[1]))
    out, seen = [], set()
    for _, _, term in found:
        key = term.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(term)
        if len(out) >= max_terms:
            break
    return out
