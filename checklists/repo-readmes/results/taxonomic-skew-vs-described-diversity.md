# Taxonomic attention versus described diversity

> **Archived.** The notebook this document specifies was retired on 2026-08-01 and
> now lives at `notebooks/results/archive/`, with its outputs under
> `notebooks/results/archive/outputs/`. No manuscript claim rests on it. The
> live result-04 notebook is `notebooks/results/04-taxonomic-lens.ipynb`;
> see `taxa-grouping-and-benchmark.md` for the shared grouping and benchmark rules.
> The specification below is retained as the record of how the analysis was built.

## Question

How does the broad taxonomic distribution of publication attention compare
with accepted species-rank records in the archived GBIF Backbone Taxonomy?

This is the foundation for later driver, threat, realm, geography, and time
cuts. It describes research attention. It does not estimate conservation need,
threat, ecological importance, population decline, or the distribution of
undescribed species.

## Notebook and shared code

- Notebook:
  `notebooks/results/11-taxonomic-skew-vs-described-diversity.ipynb`.
- Shared preparation notebook:
  `notebooks/data-processing/02-taxa-analysis-prep.ipynb`.
- Preparation helper: `data_helpers/prep/taxa_analysis_prep.py`.
- Analysis helper: `data_helpers/analysis/taxa/skew.py`.
- Figure helper: `data_helpers/analysis/taxa/skew_plotting.py`.
- Configuration: `taxonomic_skew` in
  `checklists/mappings/results_config.json`.
- Broad-group rules and colors:
  `checklists/mappings/taxa_broad_groups.json`.

The results notebook only performs analytical inclusion, estimation,
sensitivity checks, exports, and plotting. Source linkage, list parsing,
taxonomic grouping states, match audits, and GBIF benchmark construction are
performed once in the preparation notebook.

## Source grain

The preparation notebook loads the minimum required columns from:

- `data/coding-taxa/all/taxa_all.csv`;
- `data/coding-driver/all/driver_all.csv`;
- `data/coding-threats_l0/all/threats_l0_all.csv`; and
- `data/coding-ecosystems_realm/all/ecosystems_realm_all.csv`.

Each source contains 605,199 rows, 605,199 unique non-missing `UT` values, and
zero duplicate keys. All four have the identical key set and row order.
One-to-one joins therefore retain exactly 605,199 rows. Driver, Threats L0, and
realm are attached for future cross-cuts but do not filter this baseline. The
validated handoff is
`notebooks/data-processing/outputs/02-taxa-analysis-prep/taxa-publications.parquet`.
It remains one row per `UT`; list-valued labels are not exploded.

## Analytical scope

The analysis is restricted to the **biodiversity-loss dataset**: negative
direction of change (`s2_dir == "negative"`) in complete publication years
2000–2025. This gives **245,168** publications and is the same universe used by
notebooks 12, 13, and 14, so the baseline and every conditional cut are directly
comparable.

The scope is declared in `taxonomic_skew` (`direction`, `primary_start_year`,
`primary_end_year`) and applied in `prepare_taxa_skew_from_prepared`.

Two adjacent universes exist and must not be confused with it:

| Universe | Publications | Use |
| --- | ---: | --- |
| All screened-eligible records | 605,199 | Screening/ROSES only; spans every direction |
| Eligible + negative, any year | 253,081 | The paper's headline dataset |
| **Eligible + negative, 2000–2025** | **245,168** | **This analysis** |

The 7,913-record difference between 253,081 and 245,168 is pre-2000 and partial
2026 records; excluding them moves the reported vertebrate share by less than
0.1 pp. **An earlier version of this analysis ran on all 605,199 eligible
records**, which admitted positive-, mixed-, and unclear-direction evidence and
is not biodiversity loss; see History.

## Publication inclusion

The broad mapping has six outputs, but `Unresolved` is a data-quality state
rather than a biological group. The benchmarkable groups are Vertebrates,
Invertebrates, Plants, Fungi, and Other.

A publication enters the primary denominator when it has at least one
benchmarkable group derived from an exact or accepted-fuzzy GBIF match.
Publication states are mutually exclusive:

| Publication state | Publications | Share of all |
| --- | ---: | ---: |
| Included: at least one benchmarkable broad group | 171,791 | 70.07% |
| Excluded: Not applicable only | 57,725 | 23.55% |
| Excluded: reported taxon but no accepted benchmarkable match | 12,136 | 4.95% |
| Excluded: accepted taxon but broad hierarchy unresolved | 1,922 | 0.78% |
| Excluded: Unclear only | 1,594 | 0.65% |

These categories sum to 245,168. Publications containing both a benchmarkable
group and an unresolved item remain included through their benchmarkable
groups. The included count of 171,791 matches the broad-resolved denominator
reported by notebook 14 on the same scope.

The following match audit is a **preparation-stage** figure and spans all
605,199 eligible publications, not the 245,168 analysed here. Across 1,046,968
LLM taxon items, 815,975 are exact matches and 3,019 are accepted fuzzy matches.
All other states remain auditable but are ineligible for grouping: 128,841
special values, 41,727 rank mismatches, 24,059 ambiguous matches, 22,087 no
matches, 10,695 higher-rank matches, and 565 fuzzy-review matches.

## Publication allocation

For publication \(i\) linked to \(g_i\) benchmarkable groups, each group
receives:

\[
w_{ig} = \frac{1}{g_i}.
\]

Every included publication therefore contributes total weight one. The
195,716 distinct publication-group rows sum to 171,791 effective publications,
and each publication's weight is exactly one. 21,471 publications carry more
than one benchmarkable group.

The primary table also reports the actual unique publication count for every
group. Those coverage counts are not mutually exclusive and are not used
directly as a 100% composition. Two alternative allocations are reported as
sensitivities:

- full counting of each distinct publication-group assignment; and
- the 150,320 publications with exactly one benchmarkable group.

The largest group-specific difference from the article-balanced primary share
is 2.34 percentage points. The broad conclusion is not an allocation artifact.

## GBIF benchmark

The local source is `data/gbif/curated/gbif_curated.csv`, derived from the
GBIF Backbone Taxonomy snapshot dated 28 August 2023. Its EML is stored at
`data/gbif/extracted/eml.xml`; the dataset DOI is
[10.15468/39omei](https://doi.org/10.15468/39omei).

The 7,694,321 backbone rows are streamed with PyArrow. A row enters only when
`taxonRank`, case-insensitive, equals `species` and `taxonomicStatus` equals
`accepted`. This yields 2,598,208 accepted species-rank rows. No accepted row
is missing `taxonID`.

The same current broad hierarchy rules are applied to the species lineage.
There are 7,376 accepted species-rank rows assigned only to `Unresolved`;
these are excluded symmetrically with unresolved publications. The remaining
2,590,832 benchmarkable rows are renormalized:

| Broad group | Accepted species-rank rows | Share |
| --- | ---: | ---: |
| Vertebrates | 119,596 | 4.62% |
| Invertebrates | 1,683,461 | 64.98% |
| Plants | 443,824 | 17.13% |
| Fungi | 171,668 | 6.63% |
| Other | 172,283 | 6.65% |

GBIF describes this backbone as a synthetic management classification built
from many sources. It also includes OTUs from iBOL and UNITE and names from the
Paleobiology Database. The denominator is therefore labelled an accepted
species-rank backbone-record proxy for described diversity, not a complete
inventory of extant described species.

## Measures and uncertainty

The comparison reports:

- unique publications carrying each group;
- article-balanced effective publication counts and shares;
- accepted species-rank counts and renormalized shares;
- expected effective publications under proportional attention;
- attention minus described-diversity share in percentage points;
- attention divided by described-diversity share; and
- percentile 95% bootstrap intervals.

The nonparametric bootstrap resamples whole publication label patterns with
replacement. The 31 possible multi-group patterns are collapsed before drawing
1,000 multinomial replicates with seed 20260731. This exactly preserves the
publication-level estimand and avoids materializing 1,000 copies of the
171,791-row evidence table. The GBIF benchmark is treated as fixed.

## Result

Primary denominator: 171,791 publications, 245,168 in scope.

| Broad group | Attention | 95% CI | GBIF share | Gap | Representation |
| --- | ---: | ---: | ---: | ---: | ---: |
| Vertebrates | 34.83% | 34.59–35.05% | 4.62% | +30.21 pp | **7.54×** |
| Plants | 33.99% | 33.77–34.21% | 17.13% | +16.86 pp | 1.98× |
| Invertebrates | 19.71% | 19.53–19.90% | 64.98% | −45.27 pp | **0.30×** |
| Other | 8.54% | 8.41–8.65% | 6.65% | +1.89 pp | 1.28× |
| Fungi | 2.94% | 2.87–3.01% | 6.63% | −3.69 pp | 0.44× |

Vertebrates are strongly over-attended and invertebrates strongly
under-attended relative to the GBIF proxy. Plants are also over-attended. The
bootstrap intervals are narrow because the publication denominator is large;
they do not capture backbone incompleteness or taxonomic uncertainty.

Restricting to biodiversity-loss evidence **strengthens** the vertebrate result
and weakens the plant result relative to the earlier corpus-wide run
(vertebrates 6.10× → 7.54×; plants 2.43× → 1.98×). Positive-, mixed-, and
unclear-direction evidence is markedly more plant-oriented, which had diluted
the loss-specific signal.

## Literature-aligned animal-only sensitivity

Titley et al. (2017) is the closest publication-composition analogue, but its
sample is restricted to 526 primary animal studies with `biodiversity` in the
title and its described-species denominator comes from IUCN. Troudet et al.
(2017) primarily models GBIF occurrence coverage across 24 classes; its Web of
Science counts are an explanatory proxy for research activity rather than the
publication-composition response used here.

The sensitivity therefore retains the 100,206 in-scope publications containing
Vertebrates or Invertebrates and rebalances every publication across only those
animal groups.

| Animal group | Unique-publication coverage | Article-balanced attention | Animal GBIF share | Gap | Representation |
| --- | ---: | ---: | ---: | ---: | ---: |
| Vertebrates | 64.03% | 62.08% | 6.63% | +55.45 pp | 9.36× |
| Invertebrates | 39.87% | 37.92% | 93.37% | −55.45 pp | 0.41× |

Both the 100,206 denominator and the 9.36× ratio agree exactly with notebook
14's independently computed animal expression on the same scope.

Coverage can sum above 100% because one publication can carry both animal
labels. The article-balanced shares sum to 100% and are used for the gap and
ratio. This sensitivity confirms that the headline animal contrast is not an
artifact of including plants, fungi, or `Other` in the primary composition.

## Relationship to prior work and next vectors

Vector 1 is a large-scale confirmation and pipeline-validating benchmark, not
the standalone novelty claim.

- A separate time analysis should test persistence. Titley reports a roughly
  stable animal-publication bias over 1995–2015. Troudet reports that most
  occurrence-data biases persisted since the 1950s but also that the overall
  gap increased as bird observations accumulated faster; these are related,
  not identical, hypotheses.
- Driver- and ecosystem-realm-conditioned representation ratios are the main
  extensions. Ecosystem realms (terrestrial, freshwater, marine) are not a
  reproduction of Titley's tropical-versus-temperate geographic contrast.
- Donaldson et al. (2016) is the more direct later comparator for realm cuts,
  but it concerns threatened animals and conservation papers per species.
- The current versioned WoS source export has no citation-count field, so the
  Titley highly-cited-paper sensitivity requires a separate citation source.
  Its title-phrasing test is also not directly comparable because the present
  taxon extraction uses title and abstract together.

## Figure design

The two-panel figure follows the repository scientific-visualization and Tufte
guidance and the typography used in notebook 02:

- Panel A is a connected-dot comparison with direct percentages and
  publication-bootstrap intervals.
- Panel B is a sorted representation-ratio dot plot on a log2 scale, with 1×
  marked as proportional attention.
- Group colors come from the versioned broad mapping.
- Position, direct labels, and filled versus open markers make the comparison
  interpretable without relying on color alone.
- Axes are neutral, grid lines are absent, and the output is vector PDF.
- The manuscript export is deliberately compact: the caption carries the
  finding and interpretation boundary, so the PDF does not repeat a title,
  headline, footer, or decorative silhouette.
- Group order is identical in both panels. Direct values, filled versus open
  markers, and representation ratios preserve meaning in grayscale and at
  final-page scale.
- Notebook 14 reuses this result table as panel A of the integrated manuscript
  figure; it does not re-estimate the baseline.

## Outputs

All artifacts are written under:

`notebooks/results/outputs/11-taxonomic-skew-vs-described-diversity/`

The lean result bundle contains:

- `csv/taxonomic-attention-vs-diversity.csv`, the headline reported table;
- `csv/taxonomic-skew-sensitivities.csv`, consolidating allocation and
  animal-only checks;
- `csv/manifest.json`, linking the analysis to the prepared schema, grouping
  fingerprint, denominator, bootstrap seed, and reported artifacts; and
- `figures/taxonomic-attention-vs-described-diversity.pdf`.

Processing audits and the complete publication grain are not duplicated in the
results directory. They live once in the three-file prepared bundle:
`taxa-publications.parquet`, `gbif-broad-benchmark.csv`, and `manifest.json`.

## Methodological anchors

- Troudet et al. (2017), *Taxonomic bias in biodiversity data and societal
  preferences*, [doi:10.1038/s41598-017-09084-6](https://doi.org/10.1038/s41598-017-09084-6).
- Titley et al. (2017), *Scientific research on animal biodiversity is
  systematically biased towards vertebrates and temperate regions*,
  [doi:10.1371/journal.pone.0189577](https://doi.org/10.1371/journal.pone.0189577).
- Donaldson et al. (2016), *Taxonomic bias and international biodiversity
  conservation research*,
  [doi:10.1139/facets-2016-0011](https://doi.org/10.1139/facets-2016-0011).
- Eisenhauer et al. (2021), *Invertebrate biodiversity and conservation*,
  [doi:10.1016/j.cub.2021.06.058](https://doi.org/10.1016/j.cub.2021.06.058).

## History

**2026-07-31 — analytical scope corrected.** This baseline previously ran on all
605,199 screened-eligible publications, with no direction and no year filter,
giving a primary denominator of 444,800. That universe includes positive-,
mixed-, and unclear-direction evidence and is therefore not the biodiversity-loss
dataset the paper reports, and it was not comparable with notebooks 12, 13, and
14, which all scope to negative-direction evidence in 2000–2025.

`prepare_taxa_skew_from_prepared` now accepts `direction`, `start_year`, and
`end_year`; the scope is declared in the `taxonomic_skew` config block and
covered by regression tests in `data_helpers/tests/test_taxa_skew.py`. Leaving the
arguments unset still yields the corpus-wide universe, which remains available
but must not be reported as a loss result.

Effect on the headline figures:

| Group | Corpus-wide (superseded) | Loss-scoped (current) |
| --- | ---: | ---: |
| Vertebrates | 6.10× | **7.54×** |
| Plants | 2.43× | 1.98× |
| Invertebrates | 0.25× | 0.30× |
| Fungi | 0.58× | 0.44× |
| Other | 1.47× | 1.28× |

Any text, figure, or table quoting 444,800, 28.18%, or 6.10× predates this
correction.
