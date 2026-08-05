# F4 — Taxonomic and geographic mismatch in biodiversity evidence

Working note for Result 4, current as of **2026-08-02**. Written before the prose, so the
section can be drafted from here rather than from the notebook.

Notebook: `notebooks/results/04-taxonomic-lens.ipynb` (15 cells, runs clean).
Outputs: `notebooks/results/outputs/04-taxonomic-lens/`.

---

## DONE (2026-08-02, later still) — two figures combined into one 2x2; "Result 5" deleted

Two more changes, same day, after everything below. Both are current.

**Figure merge.** The taxonomic figure (panels a,b) and the geographic figure (panels a,b) are
now one combined 2x2 figure — `figure:taxonomic_and_geographic_gap`, panels a,b taxonomic on
top, c,d geographic below, `attachments/taxonomic_and_geographic_gap.pdf` ←
`04-taxonomic-and-geographic-gap.pdf`. This **reverses** the "Two sibling figures, not one 2x2"
decision recorded in `decisions-log.md` — flagged to the user before proceeding; they confirmed
combining anyway, and a rendered check beforehand showed no crowding at figsize (7.4, 6.5). The
old separate labels `figure:taxonomic_lens` / `figure:geographic_gap` and their attachment files
no longer exist. `plot_representation_and_trend()` in
`data_helpers/analysis/taxa/skew_plotting.py` grew optional `regional`/`regional_trend`
parameters to build the 2x2; `results_config.json`'s two old figure-filename keys became one
`combined_figure_filename`. Full detail in `decisions-log.md` (2026-08-02).

**"Result 5" deleted.** The driver-conditional subsection this doc's "Manuscript placement"
section (below) spent a long time planning around — *"The drivers assessed to matter most have
the most vertebrate-concentrated evidence"* — is gone from `main-28.tex` outright, at the user's
explicit request ("we dont need it"). That makes the entire "Manuscript placement" section below
moot: there is no more Result 5 to place F4 before. Discussion still has three passages that
assumed this section existed; left dangling at the user's explicit instruction ("leave
discussion for now") — do not fix without being asked again.

**Also fixed:** a real transcription error in the taxonomic anchor count (171,791 in Results vs.
171,761 in the figure caption and Discussion) — verified against the notebook's own CSVs and
corrected both to 171,791. Added `troudet2017taxonomic` as a closing citation for the "taxonomic
gap isn't narrowing" sentence, after fetching the actual paper to confirm the claim rather than
trusting the title.

---

## REVERTED (2026-08-02, later same day) — the "14 countries" country-level result was cut entirely

Everything in the section immediately below ("DONE — Supplementary Results subsection for the
'14 countries'") **was built, then removed** a few hours later in the same session, on the
judgment that it read as reaching for a result rather than reporting one. Kept here as a
historical record — do not resurrect without a fresh discussion of whether the underlying
country-level score is actually load-bearing.

**What went:** F4 Results ¶3 (the "Not evenly... 14 still publish far less..." paragraph), the
Supplementary subsection `Identifying country-level deficits`, its table
(`tab:taxonomic_country_profile`), and Extended Data Table 2 (`tab:country_deficits`) — all
removed from `main-28.tex`. In code: `focus_score`, `explain_focus_score`,
`estimate_dispersion_kappa`, `research_base_tiers` (and their ~29 tests) moved out of
`data_helpers/analysis/taxa/threat_gap.py` / `threat_gap_plotting.py`; the notebook's cell 10
lost everything from "(4) The single bounded score" onward, and its markdown+code cell pair for
"2c. Supplementary — is the geographic gap just research capacity?" was deleted outright.
Snapshot: `notebooks/results/archive/retired-helpers/2026-08-02-f4-country-focus-score/`
(README there has the full before/after). Decision recorded in `decisions-log.md` (2026-08-02).

**What survived:** the region-level geographic-gap comparison (Africa 8.8% vs 27.6%;
Asia-Pacific 17.2% → 35.3%) is a separate, independently-cited claim and is untouched —
`match_evidence_and_threat`, `summarise_gap_by_region`, `regional_evidence_trend`, and the
regional figure all stay live. F4's Results text is now two paragraphs: magnitude of both gaps,
then their trajectory over time, closing on "Unlike the geographic gap, the taxonomic gap shows
no sign of closing at all" — no country-level material, no Supplementary pointer.

**Consequently stale below, kept as history only:** "Claim 3" (the named-countries table
mentions Peru, which was never in the final 14 even before this reversion — that table predates
the percentile-threshold switch and was never reconciled), "The focus score (Supplementary
method note)", and "Supplementary §2c — 'is it just research capacity?'". None of these describe
anything currently in the manuscript or the live notebook.

---

## DONE, then reverted (2026-08-02) — Supplementary Results subsection for the "14 countries"

**Built.** `\subsubsection*{Identifying country-level deficits}` — title went through three
rounds: "Derivation of the capacity-controlled country list" (original) →
"Ruling out capacity for the 14-country list" (dropped the jargon "capacity-controlled" via
/scientific-writing-reviewer, but "for the... list" read ambiguously) →
**"Identifying country-level deficits"** (final — the capacity filter is only the last of
five narrowing steps, not the section's primary purpose; the title now names the actual
core analysis, matching the user's own framing: "isn't the analysis more about simply
finding gaps where they exist, country-wise?"). Opener also had two leaks from our own
conversation fixed: "starting from the full evidence base rather than an already-narrowed
subset" (a note about my writing process, not paper content) and "Result 4" (not a real,
citable thing in this paper — it has no `\label`, only exists in tracking comments) both
removed; the section now describes the finding in plain language the way the income
section's own opener does. `\label{sresults:taxonomic_country_deficit}`, inserted into
`main-28.tex`'s
`\subsection*{Supplementary Results}` right after the income-composition subsection
(before the `\newpage` into Supplementary methods). **Expanded to start from the map total,
not mid-pipeline** — the user asked for full transparency, so it now walks all seven steps:
253,081 (full loss dataset) → 245,168 (complete years) → 171,791 (taxonomic anchor) → 236
(countries with ≥1 vertebrate-evidence publication, of the 64,161 Vertebrates-tagged
anchor articles) → 213 (matched against 215 countries with World Bank threat data) → 203
(conclusive) → 165 (under-studied) → 14 (after the top-quartile capacity filter). The
focus-score paragraph was also rewritten to explain the mechanism in plain terms (expected
count under proportionality, shrinkage toward "no signal" for thin data, bounded to
±1) rather than just naming the technique and citing Methods. Every number re-verified
against its source CSV/notebook output before insertion. Plus a new table,
`\label{tab:taxonomic_country_profile}` — Country, Region, Focus
score, GDP per capita, R&D % GDP, Researchers per million for all 14 — and a short
interpretive paragraph (Singapore/Israel wealthy-but-deficit; Nigeria clears the output
bar despite lowest GDP/researcher-density of the 14; Iraq flagged honestly as the one case
where capacity reads differently by covariate, R&D% lowest of the 14 at 0.04% despite
clearing the output threshold). ¶3's `(Supplementary Results \TODO{TBA})` pointer now
reads `(see Supplementary Results)`, matching the income section's own no-`\ref` style.

**Also trimmed `EXPORT_COLUMNS["focus-score"]`** in `threat_gap.py` — dropped
`focus_score_low`/`focus_score_high` from the CSV export (per the user: no CI in the new
table, "extra baggage" requiring methodological defense; verified they're not cited
anywhere in the manuscript and not hardcoded in any test before removing). The internal
computation and `signal_is_conclusive` derivation are untouched — only the on-disk CSV
lost 2 columns (19 → 17). Notebook rerun from a wiped output directory, 129 tests pass.

Full plan (context, investigation, and exact rationale for each choice) is preserved at
`/Users/hunain/.claude/plans/hazy-pondering-walrus.md` if any of this needs revisiting.

Still true: **the 23-row `tab:country_deficits` in Extended Data is a *different* cut**
than this new 14-row Supplementary table — same pipeline logic, but built once before and
once after the flat-5,000 → 75th-percentile threshold switch, then both kept in sync
manually. If the threshold or pipeline changes again, **both tables need regenerating**,
not just one — this is a standing trap for future edits.

### Everything currently in the live F4 manuscript text (verbatim, so nothing is lost)

Title (`\subsection*`, line 249):
> The taxonomic gap in biodiversity evidence persists while the geographic one narrows unevenly

¶1 (line 258):
> Biodiversity research is known to be biased toward vertebrates and toward well-studied regions,
> relative to described diversity and threatened-species counts~\cite{titley_scientific_2017,
> troudet2017taxonomic}. Our map confirms both patterns across 171,791 documented cases of
> biodiversity loss linked to a resolvable taxon. The taxonomic gap is starkest for vertebrates:
> they account for 34.8% of documented research attention against 4.6% of species accepted in the
> GBIF Backbone Taxonomy (Figure 4a). The geographic gap is starkest for Africa: it accounts for
> 8.8% of vertebrate evidence against 27.6% of IUCN-listed threatened birds and mammals
> (Figure 5a).

¶2 (line 260):
> The taxonomic gap has not narrowed even as the evidence base has grown (Figure 4b). The
> geographic gap, by contrast, narrowed unevenly over the same period: Asia and the Pacific's
> share of vertebrate evidence rose from 17.2% to 35.3%, while Africa's rose only from 6.9% to
> 9.7% (Figure 5b). The taxonomic gap therefore persists, raising the question of whether the
> geographic gap closes evenly within regions too, not just across them.

¶3 (line 262) — **this is the paragraph the new Supplementary subsection backs**:
> Not evenly. To rule out a lack of capacity as the explanation, we consider only countries in the
> top quartile of national scientific output; even among these, 14 still publish far less
> vertebrate evidence than their share of threatened land vertebrates would predict (Supplementary
> Results \TODO{TBA}). Unlike the geographic gap, the taxonomic gap shows no sign of closing at
> all.

**The `\TODO{TBA}` at "(Supplementary Results \TODO{TBA})" in ¶3 is what this task resolves** —
once the new subsubsection exists, per house style (confirmed against how the income section's
own main-text pointer reads) this becomes plain **"(see Supplementary Results)"**, no `\ref` —
the existing income-section precedent doesn't cross-reference a specific label from the main
text either, it just says "(see Supplementary Results)" in prose.

### The full identification pipeline (verified numbers, reproducible from the notebook)

1. **213 matched countries** — present on both sides: vertebrate-evidence publications AND World
   Bank threatened-species counts (birds + mammals). Built by `match_evidence_and_threat` in
   `data_helpers/analysis/taxa/threat_gap.py`.
2. **Score each one** — `focus_score()` in the same module. Compares observed vertebrate-evidence
   publications to what the country's *share of threatened land vertebrates* would predict under
   proportionality, using Empirical-Bayes shrinkage (κ=5, method-of-moments fits 0.23 so κ=5
   deliberately under-claims) so thin-data countries don't generate noise-driven extreme scores.
   Bounded to (−1, +1) via `tanh(½ ln R_eb)`.
3. **203 of 213 are "conclusive"** — `signal_is_conclusive`: the 95% credible interval
   (`focus_score_low`/`focus_score_high`) doesn't straddle zero.
4. **165 of 203 are under-studied** — `focus_score < 0`.
5. **NEW capacity filter (added 2026-08-02, replacing an earlier flat 5,000 threshold)**: restrict
   to the **top quartile of national scientific output** — World Bank indicator `IP.JRN.ARTC.SC`
   (`scientific_articles` column), **all fields of science, nothing to do with biodiversity or our
   map**. Threshold is **data-derived, computed live in the notebook**:
   `gap_focus["scientific_articles"].quantile(0.75)` = **8,259.9**, i.e. **>8,260 articles/yr**.
   This replaced a flat `NAMED_MIN_ARTICLES = 5_000` after the user asked "is there any reference
   behind [5,000], is it median or what" — 5,000 turned out to sit at only the ~69th percentile of
   this same distribution (median is 501.5), i.e. an unexplained round number, not derived from
   anything. The percentile is *stricter* than the old flat cutoff (8,260 > 5,000), so this is a
   more conservative test, not a weaker one.
6. **Result: 14 countries.** These are under-studied on vertebrates specifically, statistically
   conclusive, and in the top 25% of countries globally by overall scientific output — so a lack
   of general research capacity cannot be why they haven't studied their own threatened species
   more.

**Notebook mechanics**: `notebooks/results/04-taxonomic-lens.ipynb`, cell containing
`capacity_deficits` (search for `NAMED_MIN_ARTICLE_PERCENTILE = 0.75`). Exports
`04-vertebrates-named-deficits.csv` (now 14 rows, was 23 before the percentile switch). The
`research_base_tiers()` function in `threat_gap.py` (added earlier same session) also reflects
the new threshold automatically in its bucket labels
(`04-vertebrates-research-base-tiers.csv`: tiers are now "< 1,000", "1,000-8,260", ">= 8,260",
"Not reported").

### ⚠️ Two different country lists — do not conflate them

- **`tab:country_deficits`** (Extended Data Table 2, already built, line ~1230 of `main-28.tex`) —
  same underlying selection logic (conclusive + under-studied + capacity filter) but was built
  and captioned **before** the percentile switch landed in the notebook, then **updated in place**
  when the threshold changed. It is currently **14 rows**, matching the current pipeline. Columns:
  Country, Region, Observed, Expected, Deficit, National output (articles/yr). Caption already
  says "top quartile... 8,260... 75th percentile."
- **The new ask** is a **second, different table** for Supplementary Results — same 14 countries,
  but "what we know about them" implies a **different column set** (see below), not a repeat of
  the Extended Data columns.

### What "what we know about them" can draw on — full data available per country

From `04-vertebrates-focus-score.csv` (19 columns total), for these 14 countries specifically, the
covariates NOT already in the Extended Data table are:
- `region`, `subregion` (Extended Data only has `region`)
- `focus_score`, `focus_score_low`, `focus_score_high`, `prob_understudied` — the actual scored
  statistic and its uncertainty (Extended Data table only shows observed/expected/deficit, not the
  bounded score itself)
- `evidence_to_threat_ratio_raw`, `evidence_to_threat_ratio_eb` — raw vs. shrunk ratio
- **Capacity covariates beyond `scientific_articles`**: `gdp_per_capita_usd`,
  `rd_expenditure_pct_gdp`, `researchers_per_million` — full values pulled below, and there is
  real texture here (e.g. Nigeria: GDP/capita \$1,224 vs. Singapore \$98,814 — both in the 14;
  Israel has `researchers_per_million` = NaN, a real null, not a zero)

**Full data for the 14, sorted by deficit** (from `04-vertebrates-focus-score.csv`, verified
2026-08-02 after the percentile-threshold rerun):

| ISO3 | Country | Region | Subregion | Pubs (obs) | Threatened land vert. | Expected pubs | Deficit | Focus score | 95% CI | GDP/capita (USD) | R\&D (% GDP) | Researchers/million | Sci. articles/yr |
|---|---|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| IDN | Indonesia | Asia and the Pacific | South-East Asia | 484 | 373 | 1,933 | −1,449 | −0.597 | [−0.625, −0.568] | 5,060 | 0.28 | 395 | 38,992 |
| COL | Colombia | Americas | South America | 250 | 165 | 855 | −605 | −0.543 | [−0.586, −0.499] | 8,562 | 0.29 | 90 | 9,184 |
| MYS | Malaysia | Asia and the Pacific | South-East Asia | 280 | 147 | 762 | −482 | −0.458 | [−0.504, −0.412] | 13,125 | 1.01 | 1,218 | 23,691 |
| THA | Thailand | Asia and the Pacific | South-East Asia | 202 | 130 | 674 | −472 | −0.533 | [−0.581, −0.484] | 8,057 | 0.94 | 1,592 | 16,656 |
| VNM | Viet Nam | Asia and the Pacific | South-East Asia | 220 | 114 | 591 | −371 | −0.452 | [−0.504, −0.400] | 5,066 | 0.41 | 836 | 10,644 |
| SGP | Singapore | Asia and the Pacific | South-East Asia | 63 | 40 | 207 | −144 | −0.515 | [−0.602, −0.428] | 98,814 | 1.81 | 8,782 | 11,894 |
| IRQ | Iraq | Asia and the Pacific | Western Asia | 22 | 31 | 161 | −139 | −0.720 | [−0.806, −0.626] | 5,410 | 0.04 | 164 | 16,724 |
| NGA | Nigeria | Africa | West Africa | 194 | 58 | 301 | −107 | −0.211 | [−0.279, −0.146] | 1,224 | 0.28 | 22 | 9,799 |
| SAU | Saudi Arabia | Asia and the Pacific | Western Asia | 53 | 30 | 155 | −102 | −0.469 | [−0.569, −0.370] | 34,537 | 0.64 | 1,235 | 24,595 |
| MAR | Morocco | Africa | North Africa | 118 | 41 | 213 | −95 | −0.278 | [−0.361, −0.198] | 4,672 | 0.66 | 1,083 | 9,725 |
| ROU | Romania | Europe and Central Asia | Central/Western Europe | 83 | 32 | 166 | −83 | −0.320 | [−0.415, −0.228] | 22,538 | 0.52 | 1,082 | 10,713 |
| ISR | Israel | Europe and Central Asia | Central/Western Europe | 106 | 35 | 181 | −75 | −0.254 | [−0.342, −0.169] | 60,337 | 6.35 | NaN | 13,844 |
| UKR | Ukraine | Europe and Central Asia | Eastern Europe | 95 | 31 | 161 | −66 | −0.247 | [−0.341, −0.158] | 5,866 | 0.37 | 586 | 15,498 |
| HUN | Hungary | Europe and Central Asia | Central/Western Europe | 78 | 20 | 104 | −26 | −0.134 | [−0.243, −0.033] | 25,907 | 1.38 | 4,567 | 8,260 |

Notable texture for the "what we know about them" narrative, if wanted: Singapore and Israel have
very high GDP/capita and R&D spend yet still show a deficit (so this isn't just a poor-country
pattern within the 14 either); Nigeria has by far the lowest GDP/capita and researcher density of
the 14 but still cleared the *scientific-output* quartile bar (output ≠ GDP — Nigeria's national
journal-article count is high in absolute terms even though per-capita wealth/research-intensity
is low); Iraq has the most severe focus score (−0.72) despite modest capacity metrics otherwise,
worth a second look before highlighting it as a clean "capacity-rich but ignores vertebrates" case
(R&D% is only 0.04, lowest of the 14 — flag this tension if drafting prose about Iraq
specifically).

### House style to match (confirmed from the existing income-composition Supplementary subsection)

Location: `\subsection*{Supplementary Results}` starts at **line 422**; first existing
subsubsection is `\subsubsection*{Robustness of the income-composition contrast}` at **line 425**,
ends before `\newpage` at line 436 (Supplementary methods start after). New F4 subsubsection
should likely go **after** the income one (or wherever fits the paper's Results ordering — F4 is
now Result 4, before old-F4/Result 5, so arguably this Supplementary subsection should sit before
any Result-5-specific Supplementary content, if that gets added later; check ordering once more
subsections exist).

Pattern to replicate exactly (from the income section):
```latex
\newpage
\subsubsection*{<Title>}
\phantomsection\label{sresults:<slug>}

<Opening paragraph: what this documents / which main-text finding it backs, unit of analysis.>

\paragraph*{<Bold lead-in>:} <prose, can include a \ref'd table>

% tab:<slug>
\begin{table}[H]
\renewcommand{\arraystretch}{1.3}
\setlength{\tabcolsep}{6pt}
\centering
\small
\begin{tabularx}{\linewidth}{...column spec...}
\hline
\textbf{Col1} & \textbf{Col2} & ... \\
\hline
<rows>
\hline
\end{tabularx}
\caption{...}
\label{tab:<slug>}
\end{table}
```
Note: the income table uses `tabularx` in a `table[H]` (not `longtable`), appropriate for a short
table (6 rows). For 14 rows this should still comfortably fit as a plain `table[H]`/`tabularx`
too — no need for `longtable` (that was only needed for the 23-row Extended Data version;
already dropped to 14, and Extended Data still separately uses `longtable`, which is fine to
leave as is there since it's already built and correct).

### Open questions to resolve when planning (do not silently decide)

1. **Exact column set for the new Supplementary table** — likely candidates beyond what Extended
   Data already shows: `focus_score` (+ CI), `subregion`, and the three non-output capacity
   covariates (GDP/capita, R&D%, researchers/million). Probably too many columns for one table if
   all included — may need two tables, or a wider `landscape` table like the GUIDE-LLM one, or a
   trimmed column set. **Ask the user which covariates they actually want shown** rather than
   dumping all of them.
2. **Whether to narrate any individual countries in prose** (e.g. the Singapore/Israel
   "not just poor countries" point, or the Iraq R&D-tension caveat above) or keep the subsection
   purely mechanical (pipeline + table, no per-country interpretation) — matches the main-text
   guardrail "no causal attribution in Results," but Supplementary Results in this paper (see the
   income section) does sometimes narrate specific numbers, so some interpretation may be fine
   *here* even if it was cut from main text.
3. **Table placement relative to other Supplementary subsections** — confirm ordering once
   decided (see house-style note above).
4. Still true from before (see "Still open" section below, unchanged): Methods has no subsection
   for the focus-score procedure yet, so `(Methods)` in ¶3 still points at nothing — **out of
   scope for this task** unless the user asks to fold it in.

---

---

## The finding in one sentence

> Biodiversity evidence tracks neither the diversity that exists nor the threat that is
> documented — and where it has corrected, it corrected geographically, not taxonomically.

Two independent benchmarks, both failed. That is what makes the pair worth reporting
together: either alone invites a "your benchmark is wrong" reply.

---

## Claim 1 — Taxonomic skew

Vertebrates take **34.8%** of research attention against **4.6%** of described species
(**7.5×**). Invertebrates take **19.7%** against **65.0%** (**0.30×**).

| | |
| --- | --- |
| Where | §2 (comparison), §2b (figure) |
| Figure | `04-representation-and-trend.pdf` **panel A** |
| Tables | `04-attention-vs-described-diversity.csv`, `04-denominators.csv` |
| Benchmark | GBIF accepted species-rank counts (`analysis/taxa/benchmark.py`) |
| Weighting | Article-balanced, 1/g — a publication naming two groups gives half to each |

---

## Claim 2 — The taxonomic skew has not corrected; the geographic one has

**Taxonomic.** Annual output grew **7.1×** (1,940 → 13,734) while composition barely moved.
Invertebrate representation went *backwards*: **0.34× → 0.29×**.

**Geographic.** The gap narrowed markedly.

| Region | Evidence share 2000 → 2025 | pp/decade | Representation |
| --- | --- | --- | --- |
| Asia and the Pacific | 17.2% → 35.3% | **+6.06** | 0.47× → **0.96×** |
| Africa | 6.9% → 9.7% | +1.21 | 0.25× → **0.35×** |
| Europe and Central Asia | 25.5% → 20.3% | −2.99 | 1.86× → 1.48× |
| Americas | 50.4% → 34.7% | −4.28 | 2.29× → 1.58× |

**The contrast is the argument.** The field demonstrably corrected on one axis while the
other stood still, so taxonomic stasis is not an inevitability of how research grows.

| | |
| --- | --- |
| Where | Taxonomic §2b; geographic §2a |
| Figures | `04-representation-and-trend.pdf` **panel B**; `04-vertebrate-evidence-vs-threat-by-region.pdf` **panel B** |
| Tables | `04-attention-trend-summary.csv`, `04-attention-trend-robustness.csv`, `04-vertebrates-regional-evidence-trend{,-summary}.csv` |
| Robustness | Taxonomic: residual-excluded, single-group-only. Geographic: **excluding China → +3.21 vs +6.06 pp/decade** |

**Two caveats that must travel with Claim 2.** Anchor resolution falls **77% → 67%** over the
window, so later years rest on a smaller share of the corpus. And **China is 4.4% → 36.1% of
Asia-Pacific vertebrate evidence** — WoS coverage of Chinese journals expanded over the same
period, so roughly half the Asia-Pacific correction is one country. Excluding China the rise
holds (+3.21 pp/decade) and Africa's strengthens (+1.64), so the correction is real; the
magnitude is not all what it looks like.

---

## Claim 3 (RETIRED 2026-08-02 — see banner near the top) — Geographic mismatch, on an unrelated benchmark

Africa holds **27.6%** of threatened land vertebrates and **8.8%** of the evidence
(**0.32×**); the Americas 22.0% and 41.4% (**1.88×**). The **165** conclusively under-studied
countries hold **72.9%** of the threat and **19.6%** of the evidence.

**Named cases** — selected on a large *absolute* deficit in a country that is not short of a
research base (>5,000 articles/year), never on a ratio:

| Country | Papers | Threatened | Expected | Deficit | Articles/yr |
| --- | --- | --- | --- | --- | --- |
| Indonesia | 484 | 373 | 1,933 | **−1,449** | 38,992 |
| Colombia | 250 | 165 | 855 | −605 | 9,184 |
| Peru | 221 | 144 | 746 | −525 | 5,242 |
| Malaysia | 280 | 147 | 762 | −482 | 23,691 |
| Thailand | 202 | 130 | 674 | −472 | 16,656 |
| Viet Nam | 220 | 114 | 591 | −371 | 10,644 |

| | |
| --- | --- |
| Where | §2a |
| Figure | `04-vertebrate-evidence-vs-threat-by-region.pdf` **panel A** |
| Tables | `04-vertebrates-evidence-vs-threatened-by-region.csv` (Results); `04-vertebrates-focus-score.csv`, `04-vertebrates-named-deficits.csv` (Supplementary) |
| Benchmark | IUCN threatened **birds + mammals**, WDI 2022 snapshot |
| Coverage | **56.3%** of anchor scope carries a mapped country; 213 of 236 countries matched |

**Cross-cutting nuance worth a sentence.** All six named countries sit in Asia-Pacific and
Latin America — the regions whose *aggregate* trend looks best. The regional correction is
real but unevenly distributed within regions.

---

## The focus score (RETIRED 2026-08-02 — see banner near the top) (Supplementary method note)

`focus_score ∈ (−1, +1)`; −1 needs more study, 0 proportional, +1 already over-studied.

1. **Expected** — `E[c] = N · T[c] / ΣT`, publications under proportionality to threat.
2. **Shrink** — `R_eb = (n + κ) / (E + κ)`, Gamma-Poisson with κ in publication-equivalents.
   **κ = 5, not the location quotient's 30** (a binomial-share constant on a different scale;
   at 30 it flattens real signal). Method of moments fits 0.23, so 5 deliberately under-claims.
   Spearman across κ ∈ {1, 5, 30} = **0.90**, so the ranking is not an artefact.
3. **Bound** — `(R_eb − 1)/(R_eb + 1)`, which is `tanh(½ ln R_eb)`: bounded, antisymmetric
   (a 3× surplus is +0.5, a 3× deficit −0.5), no clipping.

Reliability travels with it: `focus_score_low/_high` (95% credible), `prob_understudied`,
`signal_is_conclusive` (203 of 213 clear). `explain_focus_score()` prints the five-step
arithmetic for any country from the exported frame, so the worked example cannot go stale.

---

## Guardrails

- **"And", not "therefore."** The gaps are additive, not multiplicative — vert:invert 2.35 in
  the under-studied tropics vs 1.96 in over-studied temperate countries. No "doubly invisible".
- **Studied ≠ needed.** Publication counts, not conservation priority.
- **Benchmark is birds + mammals only.** No reptile or amphibian indicator exists in WDI;
  amphibians are the most threatened vertebrate class, so tropical deficits are **floors**.
- **Fish are held apart** — FishBase-sourced, not Red List, and they scale with marine area.
- **Threat counts are not additive across countries.** A species counts once per range state
  (for birds, breeding *or* wintering), so birds sum to 4,684 against a global unique figure
  near 1,400. Never quote a column sum as a world total.
- **No causal attribution in Results.** Capacity gets one hedged Supplementary paragraph.
- **`audit_class` / `allocation_score` are gone** — see below.

---

## Supplementary §2c (RETIRED 2026-08-02 — see banner near the top) — "is it just research capacity?"

The objection every geographic evidence-gap claim attracts, answered pre-emptively.

It partly is: `focus_score` correlates with national output (Spearman **0.64**, n=195). It does
not absorb the gap: among the **17** countries publishing 20,000–80,000 articles a year, focus
scores span **−0.60 to +0.86**. Indonesia and Spain produce comparable total output; Indonesia
holds nearly nine times the threatened land vertebrates (373 vs 42) and contributes 484
vertebrate publications against Spain's 1,262.

**Disclose the mismatch**: national output counts publications *authored by* a country while
the evidence counts publications *about* one. Separating priorities from capacity needs
author-affiliation data this corpus does not carry — the raw WoS `.xls` files hold
`Addresses` / `Reprint Addresses`, but the corpus prep dropped them.

Figure: `04-vertebrate-focus-vs-output.pdf`.

---

## Retired on 2026-08-02

Snapshot: `notebooks/results/archive/retired-helpers/2026-08-02-f4-cleanup/`.

- **Per-group specialization choropleths** (`geography_plotting.py`, `specialization_extremes`).
  They answer a within-country taxon-specialization question with no external benchmark, and
  support no F4 claim. The LQ frame itself survives — `evidence_by_country` consumes it.
- **The capacity-adjusted allocation audit** (`capacity_adjusted_audit`, `allocation_score`,
  `audit_class`, `audit_note`). Two reasons, either sufficient: its denominator mixes papers
  *about* a country with papers *by* one, so "allocation" is not what it measures; and its
  ranking puts Qatar (14 threatened species) above Indonesia (373), classing Colombia, Peru
  and Viet Nam as "capacity-explained" despite their carrying the largest absolute deficits
  after Indonesia.

---

## Manuscript placement (RETIRED 2026-08-02 — see banner near the top) — the decision this needs first

The .tex already carries a Result 4: **"The drivers assessed to matter most have the most
vertebrate-concentrated evidence"** (`main-28.tex` L249–256). It is driver-conditional taxonomic
skew, and its source notebook (`archive/12-driver-conditional-taxonomic-skew.ipynb`) was
**archived on 2026-08-01** — so a written manuscript claim rests on archived outputs. That is
fine as a record but must be known before anything is moved.

**Recommendation: the new material becomes Result 4; the driver-conditional section shifts to
Result 5.** Its opening sentence (L250) *already is* the new finding in miniature — "vertebrates
account for a third of documented attention but under 5% of species … (see Supplementary
Results)". The new section gives that setup its own evidence, benchmarks, and figures; L250 then
collapses to a back-reference. Ordering also builds: the general mismatch first, then "and it is
worst exactly where impact is greatest."

**Do not replace the driver-conditional section.** Four places depend on it: the Main preview
(L200), the Discussion's compounding argument (L261), the OECD-ecotoxicology / fisheries /
land-use three-way explanation (L265), and the Abstract. Adding costs one preview clause; replacing
costs the paper's most developed piece of reasoning.

---

## Draft — title and main arguments

### Title — settled 2026-08-02

**Live in `main-28.tex`:** *"The taxonomic gap in biodiversity evidence persists while the
geographic one narrows unevenly"*

Superseded the earlier double-benchmark title (*"Research attention tracks neither described
diversity nor documented threat"*) once the trajectory contrast became most of the section's
content (¶2–¶3), not just ¶1. First trajectory-forward draft — *"...is correcting while the
taxonomic gap is not"* — was rejected: it overclaims, since Africa specifically does not correct
(¶2: "barely moved"). "Narrows unevenly" reuses ¶2's own closing wording rather than coining new
terminology, and doesn't assert geographic correction where the regional data doesn't support it
for every region.

### ¶1 — Two independent benchmarks, both missed

*Thesis: F1–F3 described the evidence's internal composition; this asks what it looks like against
external denominators, and it fails two unrelated ones.*

- Setup: attention shares mean little without a benchmark for what could be studied.
- **Described diversity (GBIF).** Anchor 171,791 articles = 70.1% of the 245,168-article
  negative 2000–2025 universe. Vertebrates **34.8%** of attention vs **4.6%** of described species
  (**7.5×**); invertebrates **19.7%** vs **65.0%** (**0.30×**); plants 34.0% vs 17.1% (1.98×);
  fungi 2.9% vs 6.6% (0.44×).
- **Documented threat (IUCN threatened birds + mammals).** On the 96,664 articles (56.3% of the
  anchor) with a mapped study country: Africa **27.6%** of threatened land vertebrates and
  **8.8%** of evidence (**0.32×**); Asia-Pacific 36.7% / 25.7% (0.70×); Americas 22.0% / 41.4%
  (1.88×); Europe & Central Asia 13.7% / 24.1% (1.76×).
- **Stress position:** the two benchmarks are independent — one counts what exists, the other what
  is at risk — and neither is tracked. Either alone invites "your benchmark is wrong."
- Figures: `04-representation-and-trend.pdf` **a**; `04-vertebrate-evidence-vs-threat-by-region.pdf` **a**.

### ¶2 — One gap is closing; the other is not

*Thesis: the field demonstrably redistributes attention — just not taxonomically.*

- **Taxonomic, static.** Anchored annual output grew **7.1×** (1,940 → 13,734) while composition
  barely moved. Invertebrate representation went *backwards*, **0.34× → 0.29×** (−1.06 pp/decade);
  vertebrates 7.96× → 7.01×.
- **Geographic, closing.** Asia-Pacific **17.2% → 35.3%** (+6.06 pp/decade), representation
  **0.47× → 0.96×**; Africa 6.9% → 9.7% (+1.21), 0.25× → 0.35×; Americas 2.29× → 1.58×;
  Europe & Central Asia 1.86× → 1.48×.
- **The contrast is the argument.** Taxonomic stasis is therefore not an inevitable property of how
  a research field grows — this field corrected one axis over the same 26 years.
- Caveats that must travel: **China is 4.4% → 36.1% of Asia-Pacific vertebrate evidence**, and WoS
  expanded its coverage of Chinese journals over the window; excluding China the rise holds at
  **+3.21 pp/decade** and Africa's strengthens to +1.64. Anchor resolution falls **76.7% → 66.9%**.
- Figures: `04-representation-and-trend.pdf` **b**; `…-by-region.pdf` **b**.

### ¶3 — Within regions, the deficit concentrates in nameable countries

*Thesis: the regional correction is real but unevenly distributed, so aggregates conceal where the
evidence is actually missing.*

- **165** of the 203 countries with a conclusive signal are under-studied relative to threat; they
  hold **72.9%** of threatened land vertebrates and **19.6%** of the evidence.
- Named on absolute deficit plus a real research base (>5,000 articles/yr), never on a ratio:
  Indonesia 484 observed vs 1,933 expected (**−1,449**), Colombia −605, Peru −525, Malaysia −482,
  Thailand −472, Viet Nam −371.
- **The sting:** all six sit in Asia-Pacific and Latin America — the regions whose *aggregate*
  trend looks best in ¶2.
- **Not simply capacity** (one hedged sentence; detail to Supplementary): focus correlates with
  national output (Spearman **0.64**, n=195) but does not absorb the gap — among the **17**
  countries publishing 20,000–80,000 articles/yr, scores span **−0.60 to +0.86**. Spain and
  Indonesia produce comparable output; Indonesia holds ~9× the threatened land vertebrates
  (373 vs 42) yet 484 vertebrate publications against Spain's 1,262.
- Tables: `04-vertebrates-named-deficits.csv` (Results); `04-vertebrates-focus-score.csv`
  (Supplementary, full 213-country listing).

### Positioning against Titley et al. 2017 — **settled**

`titley_scientific_2017` **is already in `literature.bib` and already cited four times**
(L224, L239, L263, L267). Its abstract states the geographic result directly: *"for a given level
of species or threatened species, tropical countries were understudied relative to temperate
countries."*

**So Claim 3 is confirmation at scale, not novelty, and must be written that way.** What is new
here is scale (526 screened papers → 96,664 country-mapped articles), the **trajectory** (Titley
is a single cross-section and cannot say whether the gap is closing), the **paired** taxonomic and
threat benchmarks in one corpus, and **named, quantified country deficits**. Framing it as
confirmation strengthens the paper; overclaiming invites the obvious referee objection.

### Discussion hook this opens

The paper now carries three "is it correcting?" tests: driver imbalance **not** correcting (F3
L237), taxonomic **not** correcting, geographic **correcting**. The pattern is that the field
corrected on the axis that requires no change in expertise — *where* you work — and not on the
axes that would require studying different organisms. That is a claim about how research effort
redistributes, and it is available to no single-dimension review.

---

## Drafted into `main-28.tex` — 2026-08-02, revised through several review rounds

The text is live in `checklists/overleaf/main/main-28.tex`, inserted as a new `\subsection*`
immediately before the driver-conditional section (placement recommendation applied). It went
through several rounds of tightening after the first draft — cut fold-change/"x" notation in
favor of plain percentages, fixed a "threat" vs. F1–F3's "documented-threat" (IUCN Threat
Classification category) terminology collision throughout, added an explicit pivot sentence
between the static-benchmark paragraph and the trajectory paragraph, restructured the
country-level paragraph so each statistic states why it's there instead of appearing as a bare
number, and split it into 4 paragraphs (added a dedicated Indonesia/Spain worked example, with
the full 23-country capacity-controlled list moved to a new **Extended Data Table 2**
(`tab:country_deficits`) rather than spelled out in text). Current text is the fourth substantially
different version — treat the paragraph text above in this doc as historical, not current; read
`main-28.tex` directly for the live wording.

Two figures were copied from notebook output into `attachments/` and given real
`\includegraphics` blocks:

- `attachments/taxonomic_attention_vs_diversity.pdf` ← `04-representation-and-trend.pdf`,
  `\label{figure:taxonomic_lens}`
- `attachments/vertebrate_evidence_vs_threatened_species.pdf` ← `04-vertebrate-evidence-vs-threat-by-region.pdf`,
  `\label{figure:geographic_gap}` (renamed from `..._vs_threat.pdf` during the terminology fix)

**Main preview (L200) updated 2026-08-02** to add a fourth clause — *"research attention tracks
neither described diversity nor threatened-species counts"* — alongside the income, realm, and
driver-taxon clauses. **Discussion (L291) and Abstract (L169) are still unsynced** — Discussion's
opening still frames the paper as three axes (income, realm, taxon) and has no interpretation yet
for either new F4 claim; deferred at the user's explicit instruction ("just update findings text
for now"), not forgotten.

The old section's opening (was L250) — which repeated the vertebrate/GBIF numbers and the
Troudet/Titley citation as if new — was trimmed to a one-line backreference: *"The taxonomic
skew reported above is not a constant property of the field: it depends on which driver of loss
is being studied."*

**Every number in the drafted prose is now reproducible from the notebook**, closing three gaps
found while writing:

1. **`04-vertebrates-focus-score.csv` and `04-taxa-geography-coverage.csv` had no `save_table`
   call** — see the 2026-08-02 log entry above. Fixed before this draft was written.
2. **The tier breakdown ¶3 needed (widespread-but-capacity-limited vs. persists-with-capacity)
   did not exist as code** — added `research_base_tiers()` in `threat_gap.py`, wired into
   notebook §2a, exported as `04-vertebrates-research-base-tiers.csv`. Also computes the
   specialization check the user asked for directly (*"are these countries just biased toward
   other taxa?"*) — `n_specialized` per tier, `lq_eb` carried through `focus_score`.
3. **The China-exclusion sensitivity was only in this document, not in the notebook** — added
   `exclude_iso3` to `regional_evidence_trend()`, wired a same-region split
   (China vs. rest of Asia-Pacific) into §2a using the existing helper rather than a bespoke
   computation, exported `04-vertebrates-regional-evidence-trend-summary-excl-china.csv`. The
   reproducible number is **China 4.4% → 35.5%** of Asia-Pacific vertebrate evidence (supersedes
   the 36.1% cited earlier in conversation, which was computed ad hoc and not saved anywhere).

All additions have tests (`test_taxa_threat_gap.py`, 45 tests) and the notebook was rerun from a
fully deleted `csv/` directory — 18 tables, manifest and disk agree exactly, 129 tests pass
repo-wide.

**The 165-country statistic is confirmed correctly unfiltered.** Sanity-checked against the
user's concern this session: it carries no capacity or specialization filter, which is exactly
why ¶3 now reports it in two tiers rather than as one number.

## Still open

1. ~~Titley et al. 2017~~ — **resolved 2026-08-02**.
2. **Placement confirmation** — the .tex edit applied the recommendation (new section = Result 4,
   driver-conditional = Result 5) rather than waiting, per "we'll fix on the go." Still not
   updated to match: the Main preview (L200), Discussion §§ referencing "the drivers assessed to
   matter most" framing (L261, L265), and the Abstract. None of these break as-is — they just
   don't yet mention the new finding.
3. **Methods gap.** The focus-score procedure (Empirical-Bayes shrinkage, κ=5, credible interval)
   has no Methods subsection to cite. The drafted text marks this with
   `\TODO{cite Methods subsection once written}` rather than pointing at nothing.
4. **Supplementary country table** — `04-vertebrates-focus-score.csv` exports a clean 19-column
   selection sorted by focus score; still needs a formatted `.tex` table. The drafted prose points
   at it via `\TODO{Supplementary Results TBA}`.
5. **Figure caption panel-letter case** — new captions use `(\textbf{a})`/`(\textbf{b})` (lowercase)
   matching `figure:realm_composition`; confirm this is still current house style before final
   submission, since `figure:income_composition` also uses lowercase but the panel letters drawn
   *inside* the taxonomic figures are uppercase (`A`/`B`, per `skew_plotting.py`). This mismatch
   pre-dates this session — same pattern in the existing income and realm figures — so it is not
   a new inconsistency, just an existing one worth a single pass before submission.
