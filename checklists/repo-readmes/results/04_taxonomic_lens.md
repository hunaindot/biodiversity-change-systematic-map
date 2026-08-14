# Finding 4 — The taxonomic gap persists while the geographic gap narrows unevenly

## Finding and question

Does documented research attention track described taxonomic diversity and the regional
distribution of threatened vertebrates, and have either of those gaps narrowed since
2000?

Research attention is strongly concentrated on vertebrates relative to their share of
accepted species records, while invertebrates receive less than one third of the
attention their described-diversity share would imply. This taxonomic gap persists as
the evidence base grows. The geographic distribution of vertebrate evidence is also
misaligned with threatened birds and mammals, but that gap narrows unevenly: Asia and the
Pacific approaches its benchmark share by 2025, while Africa improves only modestly and
remains the deepest regional deficit.

## Live sources

- Finding notebook: `notebooks/results/04_taxonomic_lens.ipynb`.
- Taxonomic preparation:
  `notebooks/data_processing/02_taxa_analysis_prep.ipynb`.
- Integrated evidence input:
  `notebooks/data_processing/outputs/04_biodiversity_evidence_corpus_prep/biodiversity_evidence_corpus.parquet`.
- Shared grouping and benchmark specification:
  `checklists/repo-readmes/others/taxa-grouping-and-benchmark.md`.
- Result outputs: `notebooks/results/outputs/04_taxonomic_lens/`.
- Manuscript section: *The taxonomic gap in biodiversity evidence persists while the
  geographic one narrows unevenly*.

The live notebook contains some stale introductory prose left by the retirement of its
driver-conditioned and country-focus analyses. The executed cells, exported tables,
manifest, and current manuscript define the finding documented here.

## Analysis universe and taxonomic anchor

The taxonomic universe retains negative-direction evidence from complete publication
years 2000–2025, giving 245,168 unique publications. A publication enters the anchor
when at least one coded taxon resolves through the GBIF matching pipeline to one of five
benchmarkable broad groups: Vertebrates, Invertebrates, Plants, Fungi, or Other.
`Unresolved` is a data-quality state and does not enter the biological composition.

The anchor contains 171,791 publications, or 70.07% of the universe. The remaining
73,377 publications name no benchmarkable broad group and are excluded from every
taxonomic attention share.

If publication (i) carries (g_i) benchmarkable broad groups, each group receives
weight (1/g_i). Every included publication therefore contributes total weight one.
Unique-publication coverage counts are also reported, but they can overlap and are not
used as the 100% composition denominator.

The article-side comparison uses 1,000 whole-publication bootstrap replicates with seed
20260731. The intervals quantify publication sampling uncertainty; the described-
diversity benchmark is treated as fixed.

## Described-diversity benchmark

The benchmark is derived from the GBIF Backbone Taxonomy snapshot dated 28 August 2023.
It retains records whose rank is `species` and whose taxonomic status is `accepted`,
giving 2,598,208 accepted species-rank records. The same broad hierarchy rules used for
the publications are applied to each accepted species lineage.

The 7,376 records satisfying no broad-group rule are excluded symmetrically with
unresolved publications. Described shares are renormalized across the remaining
2,590,832 benchmarkable records. This is an accepted species-rank proxy for described
diversity, not a complete inventory of extant or undescribed diversity.

## Taxonomic result

| Broad group | Articles carrying group | Attention share | Accepted species | Described share | Attention / described share |
| --- | ---: | ---: | ---: | ---: | ---: |
| Vertebrates | 64,161 | 34.83% | 119,596 | 4.62% | 7.54× |
| Invertebrates | 39,952 | 19.71% | 1,683,461 | 64.98% | 0.30× |
| Plants | 65,412 | 33.99% | 443,824 | 17.13% | 1.98× |
| Fungi | 7,518 | 2.94% | 171,668 | 6.63% | 0.44× |
| Other | 18,673 | 8.54% | 172,283 | 6.65% | 1.28× |

Vertebrate attention exceeds the GBIF proxy by 30.21 percentage points; invertebrate
attention falls 45.27 points below it. The bootstrap interval is 34.59–35.05% for the
vertebrate attention share and 19.53–19.90% for the invertebrate share. These narrow
intervals do not capture incompleteness or taxonomic uncertainty in the backbone.

## Exploratory fixed-rank hierarchy

The notebook also builds one supplementary Kingdom → Phylum → Class → Order sunburst
without changing the broad-group finding. It reuses the accepted per-item GBIF lineages,
removes duplicate paths within a publication, and independently gives each article total
weight one at every rank it resolves to. It never pushes an upper-rank-only record into a
lower rank. The benchmark independently counts accepted species-rank records with a
complete path through the same rank.

The fixed research matches use a newer GBIF API classification than the 28-Aug-2023
benchmark. Bacterial and archaeal domains and viral realms can be mapped unambiguously
to the snapshot's `Bacteria`, `Archaea`, and `Viruses` kingdom containers; no lower-rank
rename is guessed. Rank-alignment diagnostics retain exact paths present on both sides
and report the removed evidence. The wheel uses that exact-path layer for its research
geometry and display selection, but its described-species percentages use the complete
benchmarkable GBIF base independently.

| Terminal rank | Research publications resolved | Share of 171,791 anchor | Research / GBIF paths | Exact shared paths | Pre-alignment research attention retained |
| --- | ---: | ---: | ---: | ---: | ---: |
| Kingdom | 171,791 | 100.0% | 8 / 9 | 8 | 100.0% |
| Phylum | 161,668 | 94.1% | 110 / 271 | 95 | 93.7% |
| Class | 158,500 | 92.3% | 310 / 705 | 223 | 75.9% |
| Order | 149,709 | 87.1% | 1,026 / 2,543 | 723 | 72.5% |

### Denominator reference: headline figure versus hierarchy wheel

The two figures use different, explicitly defined comparison bases. These are not two
estimates of the same species total:

| Figure or processing stage | Research denominator | GBIF described-species denominator | Meaning |
| --- | ---: | ---: | --- |
| Headline broad-group figure | 171,791 publications | 2,590,832 species | Complete benchmarkable broad-group base |
| Complete through Order, before exact alignment | 149,709 Order-resolved publications | 2,403,786 species | Records with a complete Kingdom → Phylum → Class → Order path on their respective side |
| Exact Order-alignment selection layer | 113,342 publications | 2,184,949 species | Diagnostic common-path base used to select and place the research hierarchy |
| Retained hierarchy wheel | 113,342 publications | 2,590,832 species | Exact-path research geometry paired with the independent complete benchmarkable GBIF base |

The headline figure starts from 2,598,208 accepted GBIF species-rank records. It removes
7,376 records that satisfy no broad-group rule, leaving **2,590,832** benchmarkable
species. Its described-species percentages are therefore independent of which detailed
taxa occur in the research corpus. Its research percentages independently use the full
**171,791-publication** taxonomic anchor; each publication contributes total weight one
across its benchmarkable broad groups.

The hierarchy wheel uses exact Order paths only to define its research geometry. The
species-side denominator is not narrowed to taxa observed in the corpus: every legend
species percentage is calculated over the same **2,590,832** benchmarkable accepted
GBIF records used by the headline figure.

The GBIF denominator narrows in two steps:

1. Of the 2,590,832 benchmarkable species, **187,046** lack a complete canonical path
   through Order in the fixed snapshot: 5,239 first lack Phylum, 102,818 first lack
   Class, and 78,989 reach Class but lack Order. This leaves **2,403,786** species with
   complete Order paths.
2. A further **218,837** species occur on 1,820 complete GBIF Order paths that are not
   exact members of the research-side path set. This leaves **2,184,949** species on the
   723 exact shared paths used by the research selection layer. Among the unmatched paths, 124 paths
   containing 29,799 species reuse an Order name under a different higher lineage,
   providing a strong cross-version/reclassification signal. For the remaining paths,
   absence can reflect no corpus observation, publications resolved only to a higher
   rank, a renamed taxon, or another cross-version difference; these causes cannot be
   separated safely without a formal taxonomy crosswalk.

The research denominator narrows independently. Of the 171,791 anchor publications,
149,709 resolve through Order and 113,342 have at least one of the 723 exact shared
Order paths. After filtering, each retained publication is rebalanced across only its
retained paths and again contributes total weight one. Research-attention percentages
in the wheel therefore use **113,342 publications**. Described-species percentages use
the independent **2,590,832-species** benchmark. These are deliberately different
denominators for different quantities; each is internally global and consistent.

The display reconciliation is local and exhaustive. Each named taxon receives the full
fixed-snapshot GBIF count at its exact path. Under an expanded parent, `Remaining` is
then calculated as the parent's full count minus all individually displayed child
counts. It therefore combines real but unshown child taxa and accepted species lacking
the next rank. `Remaining` and `Other` are presentation labels, not replacement taxa in
the source data. The export
`csv/04_rank_hierarchy_gbif_display_assignments.csv` retains every complete real child
taxon and its displayed destination, while
`csv/04_rank_hierarchy_full_gbif_counts.csv` retains the unaggregated rank counts.

GBIF-only or cross-version taxa do not receive named zero-research wedges. They enter the
relevant `Remaining` complement at the highest reliable displayed parent. This avoids
interpreting taxonomy-version absence as zero research attention. Three zero-angle
`Remaining` containers were added where the older research-selected layout had no
residual node: classes under Annelida and Nematoda, and orders under Pinopsida. The audit
also flags two complete GBIF Classes that exceed the original within-parent display
threshold but remain aggregated because they are not compatible named research paths:
Squamata under Chordata and Prasinophyceae under Chlorophyta. Their actual names and
counts remain in the assignment export.

Consequently, the wheel's research percentages remain a supplementary description of
the exact Order-aligned publication subset and must not be read as refinements of the
headline broad-group research percentages. Its described-species percentages, however,
now share the headline figure's complete benchmarkable GBIF base.

The reproducible summaries are
`csv/04_rank_hierarchy_resolution_audit.csv`,
`csv/04_rank_hierarchy_alignment_audit.csv`, and
`csv/04_rank_hierarchy_order_comparison.csv`.

The nine kingdom-level GBIF containers are Animalia, Archaea, Bacteria, Chromista,
Fungi, Plantae, Protozoa, Viruses, and `incertae sedis`. They are not 17 competing
biological kingdoms; `incertae sedis` is a placement state, and the API can expose
domains, kingdoms, and viral realms together if rank is ignored.

The retained wheel uses 113,342 publications on the 723 exact shared Order paths for
research geometry and all 2,590,832 benchmarkable accepted GBIF species for the legend's
described shares. Research attention alone controls angular span. The four-column
hierarchy below the wheel reports paired global percentages through Class; Order names
remain in the outer ring and their complete paired values remain in the exported tables. Every expanded parent
reconciles with its displayed children independently on both measures. The existing
named-node selection is frozen from the aligned research/GBIF screening layer to
preserve the reviewed geometry; the full-GBIF rebase changes counts and local
`Remaining` complements, not named biological wedges. Below-threshold or unavailable
detail is labelled `Remaining`, coloured within its parent palette, and terminal.
Terminal branches continue through unused rings as unlabelled tints without inventing
descendants. Only the combined top-level `Other kingdoms` branch remains neutral grey.

The sunburst remains supplementary because exact Order alignment excludes a material
part of the anchor. The complete-base comparison remains
`04_taxonomic_and_geographic_gap.pdf`; promoting the wheel would require re-matching the
research corpus and rebuilding the benchmark from the same GBIF release.

## Taxonomic trajectory

The number of anchor publications per year rises from 1,940 in 2000 to 13,734 in 2025,
a 7.08-fold increase. The taxonomic gap does not close during that expansion:

| Broad group | Attention in 2000 | Attention in 2025 | Slope per decade | Representation in 2000 → 2025 |
| --- | ---: | ---: | ---: | ---: |
| Vertebrates | 36.73% | 32.35% | −1.63 points | 7.96× → 7.01× |
| Invertebrates | 21.87% | 19.08% | −1.06 points | 0.34× → 0.29× |
| Plants | 32.10% | 35.07% | +0.59 points | 1.87× → 2.05× |
| Fungi | 2.55% | 3.37% | +0.25 points | 0.39× → 0.51× |
| Other | 6.75% | 10.13% | +1.86 points | 1.01× → 1.52× |

The fall in broad vertebrate attention is not an invertebrate catch-up: both animal
groups lose attention share while Plants, Fungi, and especially Other gain. The slope
pattern is checked after excluding and renormalizing over the residual `Other` group and
among single-group publications only.

Taxonomic resolution also declines over time. The share of in-scope publications with a
benchmarkable group falls from 76.7% in 2000 to 66.9% in 2025, so later composition
estimates rest on a smaller fraction of the complete evidence base.

## Geographic benchmark and result

The geographic half asks a separate question using an unrelated benchmark. It compares
each IPBES region's share of vertebrate evidence with its share of threatened birds and
mammals in the 2022 World Bank/WDI snapshot. Fish are held apart from this land-
vertebrate benchmark, and no comparable reptile or amphibian indicator is available.

The geographic comparison covers 96,664 publications, or 56.27% of the taxonomic anchor:
these are the publications carrying at least one mapped study country. Evidence is
counted as unique publications within each country and then summed to the region; a
multi-country article may therefore contribute to several countries. Threat counts also
represent country occurrences, so a threatened species can count in more than one range
state.

The evidence and threat tables match for 213 countries. At the pooled regional level:

| Region | Vertebrate-evidence share | Threatened bird-and-mammal share | Evidence / threat share |
| --- | ---: | ---: | ---: |
| Africa | 8.77% | 27.61% | 0.32× |
| Asia and the Pacific | 25.74% | 36.71% | 0.70× |
| Europe and Central Asia | 24.12% | 13.70% | 1.76× |
| Americas | 41.37% | 21.98% | 1.88× |

Africa has the largest regional shortfall. The trend, however, shows uneven geographic
convergence:

| Region | Evidence share, 2000 → 2025 | Slope per decade | Representation, 2000 → 2025 |
| --- | ---: | ---: | ---: |
| Africa | 6.9% → 9.7% | +1.21 points | 0.25× → 0.35× |
| Asia and the Pacific | 17.2% → 35.3% | +6.06 points | 0.47× → 0.96× |
| Europe and Central Asia | 25.5% → 20.3% | −2.99 points | 1.86× → 1.48× |
| Americas | 50.4% → 34.7% | −4.28 points | 2.29× → 1.58× |

China grows from 4.4% to 35.5% of Asia-Pacific vertebrate evidence over the same window,
so it contributes materially to the regional change. Excluding China reduces the
Asia-Pacific slope from +6.06 to +3.21 points per decade, but the direction remains
positive; Africa's slope increases from +1.21 to +1.64 points.

The geographic and taxonomic results are joined with “and,” not “therefore.” They use
different benchmarks and do not show that taxonomic and geographic gaps compound within
the same publications.

## Figure and outputs

The finding has one combined vector figure:

- `figures/04_taxonomic_and_geographic_gap.pdf` — Panel A compares attention with
  described diversity, Panel B shows annual taxonomic attention, Panel C compares
  regional vertebrate evidence with threatened birds and mammals, and Panel D shows the
  regional evidence trajectory.

The manuscript copies it to
`checklists/overleaf/main/attachments/taxonomic_and_geographic_gap.pdf`.

One additional vector figure is exploratory and is not a manuscript asset:

- `figures/04_rank_hierarchy_research_attention_sunburst_exploratory.pdf` — the
  Kingdom → Phylum → Class → Order wheel.
  Angular span is research attention only; a four-column hierarchy through Class below
  the enlarged wheel reports `(research attention, described species)`. Orders remain
  encoded and selectively labelled in the outer ring but are not repeated below. Each measure has one global denominator
  at every rank—113,342 publications for research and 2,590,832 accepted species for
  described diversity—so each displayed set of children sums to its parent. Eleven roomy wedges also
  carry an in-wheel name and representative PhyloPic silhouette as orientation aids;
  these annotations do not encode another measure.

The PDF is authored at Nature's maximum recommended double-column display size,
180 × 170 mm, rather
than being reduced from an oversized landscape canvas. All final-size lettering is
5.0–6.4 pt. The wheel occupies the upper band; the lower hierarchy keeps each Phylum
subtree intact while distributing Animalia first and Plantae thereafter across four
aligned columns. Kingdom, Phylum, and Class use fixed, equally spaced indentation tabs
in every column. This avoids both the approximately 3-pt effective lettering produced
by the former LaTeX reduction and collisions between long `Remaining` labels and their
percentage pairs. Omitting duplicate Order rows from this lower hierarchy releases
enough page area for a substantially larger wheel without changing its data or geometry.

The hierarchy resolution, cross-snapshot alignment, and GBIF-source audits are retained
as standalone CSVs because they document the sunburst's comparison boundary.
`csv/04_rank_hierarchy_sunburst_manifest.json` points to the 723-path exact Order
selection input, the complete fixed-snapshot GBIF rank counts, the real-taxon-to-display
assignment table, the plotted-node/colour table, and the reconciliation audit. The
reviewed named-node geometry is unchanged. Rebasing adds only three zero-angle
`Remaining` containers, giving 96 exported nodes: 4 Kingdoms, 11 Phyla, 38 Classes, and
43 Orders. Fungi remains a named terminal Kingdom because its lower-rank segments are
too small for this view. `Other` and `Remaining` are terminal at every rank.
The four rank rings use unequal radial widths: Kingdom 0.30, Phylum 0.34,
Class 0.46, and Order 0.72 plotting units. The wider outer rings reserve more radial
space for readable Class and Order labels while retaining the reviewed wheel diameter.
Rank colour separation is likewise explicit rather than relying on small incremental
lightening. Kingdom retains its dark saturated base hue. Descendants use fixed HLS
targets while preserving Kingdom-family hue and small sibling hue offsets: Phylum
lightness/saturation 0.58/0.64, Class 0.70/0.52, and Order 0.83/0.40. Thus every outward
step is both lighter and less saturated, making Kingdom–Phylum and Class–Order boundaries
legible even before reading separators. Descendant `Remaining` segments use their
parent Kingdom colour family; only `Other kingdoms` is neutral grey.
The Order-label pass now uses that space directly. Named, non-grey Order segments are
tested using each full taxonomic name laid along the radius; the word is drawn only if
its rendered box, including padding, remains inside the annular wedge. No abbreviation
is invented and there is no angular preselection beyond the fit itself. The current
Nature-sized render retains 26 full radial Order names. Poales keeps its existing curved icon/name treatment
and is excluded from the radial pass; `Other` and `Remaining orders` stay unlabelled in
the wheel. All retained Order names remain upright on both halves of the circle.
Ten Order landmarks have configured representative silhouettes. Each complete
icon–gap–name unit must pass the same padded wedge-boundary test; a failed icon candidate
falls back to its centered text-only name rather than losing the label. At the final
180-mm artwork size eight icon–name pairs fit: Rodentia, Primates, Artiodactyla,
Carnivora, Anura, Decapoda, Fabales, and Pinales. The other configured candidates retain their names
without silhouettes. The broader curved labels retain their silhouettes where they
fit. Assets are public-domain PhyloPic silhouettes under CC0 1.0 or
PDM 1.0, with exact source, creator, and license metadata in
`checklists/mappings/taxa_broad_groups.json`.
In-wheel annotations require at least 18° of angular span and must pass rendered
per-glyph and icon fit tests inside the wedge. Each word follows its circular arc;
the complete icon–gap–word unit is centered on the wedge's angular and radial midpoint.
The icon uses a depth-aware gap before the first letter, and broader inner ranks use
slightly larger type and silhouettes. The current fit retains Animalia,
Plantae, Chordata, Arthropoda, Tracheophyta, Mammalia, Aves, Insecta, Magnoliopsida,
Liliopsida, and Poales. Smaller sectors remain unlabelled rather than being crowded.
The manifest records both the retained taxa and their canonical clipart asset keys.

The manifest identifies the reported tables:

- `csv/04_denominators.csv`;
- `csv/04_attention_vs_described_diversity.csv`;
- `csv/04_attention_trend_by_year.csv`;
- `csv/04_attention_trend_summary.csv`;
- `csv/04_attention_trend_robustness.csv`;
- `csv/04_anchor_resolution_by_year.csv`;
- `csv/04_taxa_geography_coverage.csv`;
- `csv/04_vertebrates_evidence_vs_threatened_by_region.csv`;
- `csv/04_vertebrates_regional_evidence_trend.csv`;
- `csv/04_vertebrates_regional_evidence_trend_summary.csv`; and
- `csv/04_vertebrates_regional_evidence_trend_summary_excl_china.csv`.

Country-level evidence, threat, and matched tables are retained as transparent inputs to
the regional aggregation. No current manuscript claim names or ranks individual
countries.

## Retired analyses that are not part of Finding 4

- Driver-conditioned taxonomic location quotients and concentration claims.
- Realm-conditioned taxonomic attention.
- The archived animal-only temporal finding and integrated driver figure.
- Country focus scores, capacity tiers, and the retired 14-country deficit list.
- Per-group taxonomic-specialization choropleths.

These analyses remain recoverable under `notebooks/results/archive/` or its
`retired-helpers/` snapshots. They must not be reintroduced as current results without a
new analytical and manuscript decision.

## Interpretation boundaries

- Attention shares measure publication composition, not conservation need, extinction
  risk, ecological importance, population decline, or undescribed diversity.
- GBIF accepted species-rank records are a management-taxonomy proxy and are especially
  incomplete as a proxy for microbial diversity.
- The regional threat benchmark includes birds and mammals only; tropical deficits are
  likely floors because reptiles and amphibians are absent.
- Geographic coverage is 56% of the taxonomic anchor, and country occurrence counts are
  not globally additive.
- Temporal patterns are descriptive; they do not identify why attention changed.

## Refresh checklist

Start with `csv/04_manifest.json`. Verify the universe, anchor, taxonomic shares,
resolution endpoints, and geographic coverage against it, then check every detailed
value against the named CSV. Use 35.5%, not the retired 36.1% China endpoint, and confirm
that the combined 2×2 figure remains the only manuscript-facing asset. The six
fixed-rank hierarchy figures must remain explicitly exploratory unless both sides are
rebuilt from one GBIF release.
