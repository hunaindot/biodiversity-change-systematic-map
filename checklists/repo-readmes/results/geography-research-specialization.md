# Geographic research specialization (Location Quotient) — metric design

Status: **implemented** in `notebooks/results/01-threats.ipynb` — log2-LQ diverging maps at IPBES subregion (primary) and country (supplementary) level, plus one standalone map per threat. Cells are stabilised with **Empirical-Bayes shrinkage (fixed `kappa = 30`)**, and the `D_c >= 100` country cutoff is kept for coverage (§6–§7). The maps display `log2_lq_eb`; raw `lq` is exported alongside. Later: apply the same metric to **threat x realm** for consistency.

---

## 1. What we measure, in one sentence

For each place and each IUCN threat: **does this place's literature study this threat more (or less) than the corpus does on average?** That is *research specialization* — **not** where the threat actually occurs (see the caption rule in §9).

It replaces the earlier "% share of a threat's documents" map, which was washed out (most places pale, because a few big producers — USA, China — dominate every share).

## 2. The metric: log2 Location Quotient

```
LQ = (threat's share WITHIN this place) / (threat's share GLOBALLY)
   = (n[c,t] / D[c]) / (T[t] / D)
```

We plot `log2(LQ)` (a symmetric "fold-change"):

| log2(LQ) | LQ | reading |
|---:|---:|---|
| +1 | 2x | studied twice as much as expected (specialized) |
| 0 | 1x | exactly the corpus average |
| −1 | 0.5x | studied half as much as expected (under-studied) |

log2 is used because the raw ratio is lopsided (1.5 vs 0.38 are "the same distance" from 1 but look different); log2 is symmetric around 0, giving a fair diverging map. "Fold-change" is also familiar to ecology / genomics readers.

**Worked example — China, Pollution (observational subset):**

- China has `D[c] = 12,872` documents; `n[c,t] = 4,674` mention Pollution -> within-China share = 4,674 / 12,872 = **36%**.
- Globally, Pollution is about **30%** of documents (`T[t] / D`).
- `LQ = 36% / 30% = 1.2` -> China studies pollution **1.2x** more than average (`log2 = +0.27`). Green, mild.

### Terms (every count is UNIQUE DOCUMENTS)

| term | meaning |
|---|---|
| `n[c,t]` | documents about threat `t` in place `c` |
| `D[c]` | documents in place `c` — the **support** for the LQ |
| `T[t]` | documents about threat `t` |
| `D` | documents in the universe (§4) |

## 3. Counting basis: unique documents (not mentions)

Every term counts **distinct documents** (`nunique("UT")`). A document naming five countries adds 1 to each country's `D[c]`, never 5 to a total — *no inflation by multi-label mentions.* Because a document can carry several threats, a place's threat shares can sum above 100%; that is fine — LQ is a ratio of two shares and stays well-defined even though the country x threat table is not additive.

## 4. Universe (the baseline everyone is compared against)

`D` = unique documents that are all of:

1. in the analytic subset — **negative impact** (`s2_dir == "negative"`) AND **Observational** (`pred_study_design == "Observational"`);
2. **geolocatable** — at least one country code that maps to the IPBES crosswalk;
3. carry at least one `pred_threat_l0` label.

The global baseline `T[t] / D` is computed **inside this same subset** (specialization relative to *this* corpus, not some external universe). On this subset the universe is **97,926 documents**. Non-mappable geography tokens (`[]`, `"Not Applicable"`, `"Unclear"`, `"All Countries"`, invalid ISO3) are skipped and reported in the audit.

Geography is always derived from `pred_countries` (ISO3) and then aggregated, so the country and subregion maps are one signal at two resolutions.

## 5. Why LQ and not standardized residuals

Standardized residuals `(O − E) / sqrt(E)` were considered (magnitude-aware, "come with a test", would match a residual-based Fig 1) but rejected as the map metric:

1. **The chi-square test is invalid on multi-label counts.** It assumes each document lands in exactly one cell; ours land in many, so cells are correlated and p-values would overstate significance.
2. **`E` needs an additive table**, which our unique-document counts are not — so `E = row*col/grand` is not coherent (residuals would not sum to zero per row).

LQ is a descriptive ratio of shares that tolerates the non-additive multi-label table. If a significance signal is ever needed, use a **document-level permutation test** (shuffle threat labels across documents, rebuild a null band) — not chi-square. The current realm x threat heatmap uses share-within-realm; for cross-figure coherence, move both to log2 LQ rather than to residuals.

## 6. Small samples — what we found

A bare ratio can blow up on tiny samples. Two things matter here.

**The support cutoff is on the place total, not the cell.** A country enters the maps only if `D[c] >= 100` documents (**108 of 237** countries clear it; the rest are grey). But that cutoff is on the country's *total* documents — an individual `country x threat` cell inside a qualifying country can still rest on very few documents.

**Per-cell counts (country map, cells that appear):** median `n = 37`, but the tail is thin — 10% of cells have `n < 7`, 20% have `n < 10`.

**The key finding: the small-sample risk is one-sided.** From the funnel of `log2(LQ)` vs `n`, tiny cells (`n = 1–4`) only ever produce strong **under**-representation (down to ~0.09x); they **cannot** produce a spurious **over**-representation. Reason: with `D[c] >= 100`, a place needs a meaningful `n` before its within-share can exceed the global share. So the few cells that reach the +4x cap are **genuine**, not noise:

| cell | n | LQ | is it noise? |
|---|---:|---:|---|
| Laos — Energy Production & Mining | 36 | 4.1x | No — real (Mekong dams) |
| Cambodia — Energy Production & Mining | 43 | 4.0x | No — real |
| New Caledonia — *Other Options* | 6 | 4.0x | small base — but "Other Options" is dropped from maps |

What small `n` *does* create is a shaky deep-purple **under**-representation tail (e.g. New Caledonia, Residential & Commercial, `n = 1`, `D = 108` -> `LQ = 0.09`, `log2 = −3.5`). That single-document cell should not read as "studies this 11x less than average" with confidence.

**On the subregion map this is a non-issue:** per-cell counts there have median `n = 319` and only 1 of 188 cells has `n < 10`. Small-sample stabilisation is really a *country-map* concern.

### Options to stabilise (pick one — this is the open decision)

1. **Do nothing extra.** The `D[c] >= 100` cutoff already keeps the *green* side honest; the cap cells are genuine. The only cost is a shaky purple tail.
2. **Add a per-cell minimum** `n[c,t] >= k` (grey cells below it). `k = 5` greys 7% of cells; `k = 10` greys 20%. Simple, but greying also hides *true* rare-topic under-representation, and it is a second arbitrary threshold.
3. **Empirical-Bayes shrinkage (§7) — this is what we implemented.** Pull each cell toward "average" by an amount set by its uncertainty; keep the cutoff for coverage.

**What is implemented:** option 3 (EB, fixed `kappa = 30`) layered on top of option's `D_c >= 100` cutoff. EB de-noises the cells; the cutoff still decides who is coloured vs grey (so coverage is unchanged — 108 countries coloured, the rest grey; all subregions coloured). EB is a de-noiser, not a coverage tool: a small country that concentrates its few documents on one threat still reads as signal, so the cutoff is what controls which places appear.

## 7. Empirical-Bayes (EB) shrinkage — implemented (fixed kappa = 30)

Idea: instead of greying small cells, **shrink** each cell's LQ toward 1 (the corpus average) by an amount proportional to how little data it has. Small cells collapse toward neutral; large cells barely move. Nothing is greyed, and `n = 0` is handled naturally.

**Model (fits our multi-label data cleanly).** Of a place's `D[c]` documents, `n[c,t]` mention threat `t`: `n ~ Binomial(D[c], p)`. Each threat is treated independently ("does this doc mention it?"), so multi-label is fine. Put a `Beta` prior centred on the global share `pi = T[t]/D`, with strength `kappa` (a pseudo-count). The stabilised estimate is:

```
LQ_EB = (n[c,t] + kappa * pi) / ((D[c] + kappa) * pi)
```

- `kappa` small -> LQ_EB ~ raw LQ.  `kappa` large or `D[c]` small -> LQ_EB -> 1.
- `kappa` can be a fixed number, or estimated per threat from the between-place spread (Beta-Binomial method of moments) — the "empirical" in EB.

**Worked examples (what shrinkage does):**

| cell | n | raw LQ | EB (kappa=30) |
|---|---:|---:|---:|
| USA — Pollution (huge cell) | 4,151 | 0.91 | **0.91** (unmoved) |
| China — Pollution | 4,674 | 1.20 | **1.20** (unmoved) |
| Laos — Energy (genuine, small-ish) | 36 | 4.09 | 3.64 (still specialized) |
| New Caledonia — Residential (`n=1`) | 1 | 0.09 (log2 −3.5) | **0.29** (log2 −1.8) |

Big genuine cells do not move; the shaky `n = 1` purple collapses toward neutral.

**Effect on the whole country map:**

| metric | raw | EB kappa=30 | EB kappa=100 | EB per-threat (MoM) |
|---|---:|---:|---:|---:|
| noise (std of log2 LQ) | 0.77 | 0.65 | 0.51 | 0.56 |
| deepest under (log2 min) | −3.46 | −2.29 | −1.87 | −2.20 |
| highest over (log2 max) | 2.03 | 1.86 | 1.64 | 1.67 |

Data-driven `kappa` per threat ranged 17 (Agriculture — real geographic signal, so little shrinkage) to 1,816 (Unclear — diffuse, so shrunk almost to neutral); median ~51.

**Trade-offs.** EB gives a model-based estimate, not the raw ratio, so it must be captioned ("Empirical-Bayes-stabilised LQ") and the raw `lq` exported alongside. It also mildly attenuates genuine strong signals (Laos 4.1 -> 3.6 at kappa=30, or -> 3.1 under per-threat MoM) — conservative, which is usually desirable for a map.

**Decision (implemented):** a gentle fixed `kappa = 30`. It tames the shaky purple tail (−3.5 -> ~−2.3) and roughly halves the noisy extremes, while barely touching genuine cells, and is easy to caption. In code it is `location_quotient(..., eb_kappa=30)`; the maps display `log2_lq_eb`, and raw `lq` / `log2_lq` are exported alongside. Per-threat MoM remains the fully-adaptive alternative if we ever want it (`eb_kappa` would take the per-threat values); change the single `LQ_EB_KAPPA` constant in the notebook to retune.

## 8. Visualization spec

- **Form:** small-multiple choropleth, one panel per threat, ordered by document count. "Other Options" omitted; panel titles are the threat label only.
- **Two combined maps + per-threat maps:** subregion (primary), country (supplementary), and one standalone figure per threat at each level for reuse.
- **Colour:** diverging **PRGn** (purple = under, green = over), **white at 0**.
- **Scale:** linear in `log2(LQ)`, symmetric, **capped at ±2** (1/4x .. 4x); beyond clamps to the end colour, exact value kept in the table.
- **Legend:** one shared colourbar; ticks at log2 = −2..+2 labelled 1/4x .. 4x.
- **Not included** (sub-cutoff or no data): **cross-hatched** (`hatch="xx"`, grey) on a
  light base, so "excluded" is not confused with a low value; the subregion map has
  none (all subregions clear the cutoff). Legend note: "hatched = not included".
- Layout: `load_polygons(simplify_tolerance=0.2, preserve_topology=False)`, subregion via `dissolve_by="Sub_Region"`, Antarctica trimmed, PDF via `save_figure_result` (routes by `geo-` prefix to `geography/pdf` and `geography/csv`).
  - **Note:** `save_figure_result` is a notebook-local helper defined only in the archived `-1-threats.ipynb`, where these maps were originally built; it does not exist in `data_helpers/`. If the geography maps are revived, export through the current convention instead — a result store or `visualization.save_publication_figure`, routed by `results_config.json` into `notebooks/results/outputs/<section>/{figures,csv}/`.
  - The metric code itself is live and unchanged at `data_helpers/analysis/parked/geography.py`.

## 9. Naming and the mandatory caption

- **Name:** "research specialization" / "relative research emphasis" (avoid the bare term "location quotient" in reader-facing captions).
- **Metric caption:** "Colour shows research specialization — log2 of each region's share of a threat's literature relative to the corpus average (0 = as expected, +1 = twice, −1 = half)."
- **Literature-not-nature wall (mandatory):** "This reflects where a threat is disproportionately **studied**, not where it **occurs** — research emphasis, not environmental severity." Without it, readers misread the map as an impact map.

## 10. Implementation and exports

`data_helpers/analysis/parked/geography.py`:

- `location_quotient(df, *, level, by, id_col, country_col, min_support, eb_kappa, verbose)` — parses/classifies geography, builds the universe (§4), aggregates to `country` / `subregion` / `region`, returns the long table + `GeoAudit`. With `eb_kappa` set it returns the **full place x class grid** (every combination, including `n = 0`) so each cell has a stabilised value.
- `load_polygons(..., dissolve_by=...)` — dissolves country polygons to subregion / region units for the coarser map.

**Export columns (LQ long table):** `<key>` (`iso3` / `subregion`), `pred_threat_l0`, `n`, `support` (`D[c]`), `class_total` (`T[t]`), `universe` (`D`), `within_share`, `global_share`, `lq`, `log2_lq`, `lq_eb`, `log2_lq_eb`, `sufficient`. The maps use `log2_lq_eb`; raw `lq` is kept for transparency.

Outputs live under `notebooks/results/outputs/01-threats/geography/{pdf,csv}/`. The raw `geo-country-threat-*` count tables are kept for the volume view.

## 11. Sanity check (real Observational subset)

Directions match ecological intuition:

| place | threat | LQ |
|---|---|---:|
| Australia | Invasive species | 1.50 (specialized) |
| Australia | Pollution | 0.59 (under) |
| China | Pollution | 1.20 (specialized) |
| China | Invasive species | 0.48 (under) |
| Oceania (subregion) | Invasive species | 1.62 |
| Laos / Cambodia | Energy Production & Mining | ~4.0 (Mekong dams) |

Universe 97,926 docs; all 17 subregions clear the cutoff; 108 of 237 countries do.
