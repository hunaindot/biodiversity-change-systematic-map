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
  `checklists/repo-readmes/reference/taxa-grouping-and-benchmark.md`.
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
that only the combined 2×2 figure is present before updating manuscript-facing text.
