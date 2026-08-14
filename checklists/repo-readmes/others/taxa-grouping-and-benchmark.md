# Taxonomic grouping and described-diversity benchmark

Shared technical note for the taxonomic result. This page defines the
validated-GBIF grouping rules and the accepted species-rank benchmark; it does
not add a fifth finding.

Current producers and consumers:

- prep: `notebooks/data_processing/02_taxa_analysis_prep.ipynb`;
- versioned rules: `checklists/mappings/taxa_broad_groups.json`;
- result: `notebooks/results/04_taxonomic_lens.ipynb`; and
- finding specification: `checklists/repo-readmes/results/04_taxonomic_lens.md`.

## Prepared handoff

The prep notebook starts from the canonical eligible corpus and the validated
taxa coding. It groups each accepted taxon item from its own hierarchy before
deduplicating publication-level lists; hierarchy columns are never zipped
positionally.

It writes only three durable artifacts to
`notebooks/data_processing/outputs/02_taxa_analysis_prep/`:

- `taxa_publications.parquet`: one row per eligible `UT`, with `broad_groups`,
  `analysis_groups`, and `detail_groups` plus audit/state columns;
- `gbif_broad_benchmark.csv`: the accepted species-rank broad-group benchmark;
  and
- `manifest.json`: sources, schema, row counts, group audits, and the grouping-rules
  SHA-256 fingerprint.

The current manifest has 605,199 rows and 605,199 unique `UT`s. Results
notebooks should read this handoff rather than reopen raw coding outputs or
rebuild the hierarchy.

## Grouping schemes

The mapping produces three ordered schemes without changing the one-row-per-UT
grain:

- **Broad (6):** Vertebrates, Invertebrates, Plants, Fungi, Other, Unresolved.
- **Analysis (9):** Vertebrates, Arthropods, Other invertebrates, Vascular
  plants, Other or unspecified plants, Fungi, Bacteria & archaea, Other taxa,
  Unresolved.
- **Detail (14):** Mammals, Birds, Fishes, Reptiles & amphibians, Arthropods,
  Molluscs, Other invertebrates, Vascular plants, Non-vascular plants & Plantae
  algae, Plants—phylum unspecified, Fungi, Bacteria & archaea, Other taxa,
  Unresolved.

Only `exact` and `fuzzy_accepted` matches are eligible for grouping. The rules
are applied independently to each matched taxon and the configured order is
retained when publication-level lists are deduplicated.

Important boundaries:

- In the broad scheme, `KINGDOM = Animalia` plus `PHYLUM = Chordata` defines
  Vertebrates. The benchmark contains phylum but not subphylum, so this is the
  common broad rule.
- The analysis and detail schemes use the stricter `SUBPHYLUM = Vertebrata`
  rule. Chordates with a present, non-Vertebrata subphylum enter Other
  invertebrates; chordates without enough subphylum information remain unresolved.
- Other Animalia require a present phylum before entering Invertebrates.
- `DOMAIN = Bacteria` or `Archaea` enters Other in the broad scheme and the
  dedicated Bacteria & archaea group in the finer schemes.
- `PHYLUM = Tracheophyta` defines vascular plants. At detail level, Plantae
  with a present non-Tracheophyta phylum enters Non-vascular plants & Plantae
  algae; missing plant phylum remains Plants—phylum unspecified.
- No rule uses genus or species names directly. Those predictions are used to
  obtain a validated higher hierarchy.
- Not-applicable values and non-accepted matches receive no biological group.
  `Unresolved` is an audit state, not a biological group, and is excluded from
  biological compositions.

The current broad audit across all 605,199 eligible publications is:

| State | Publications |
| --- | ---: |
| At least one included broad group | 444,800 |
| Not applicable only | 119,503 |
| Unclear only | 4,501 |
| Accepted match but unresolved group only | 4,446 |
| Reported taxon but no accepted match | 31,949 |

These states are mutually exclusive in the prepared manifest.

## Described-diversity benchmark

The local source is `data/gbif/curated/gbif_curated.csv`, derived from the GBIF
Backbone Taxonomy snapshot dated 28 August 2023. Dataset metadata are retained
in `data/gbif/extracted/eml.xml`; the DOI is
[10.15468/39omei](https://doi.org/10.15468/39omei).

The separately supplied `data/gbif/raw-2/eml.xml` reports the same snapshot date and
DOI, so it is additional raw provenance rather than a newer classification release.

A backbone row enters the benchmark only when `taxonRank`, case-insensitive,
equals `species` and `taxonomicStatus`, case-insensitive, equals `accepted`.
The same broad grouping rules are then applied to its lineage.

| Broad group | Accepted species-rank rows | Share of all accepted |
| --- | ---: | ---: |
| Vertebrates | 119,596 | 4.60% |
| Invertebrates | 1,683,461 | 64.79% |
| Plants | 443,824 | 17.08% |
| Fungi | 171,668 | 6.61% |
| Other | 172,283 | 6.63% |
| Unresolved | 7,376 | 0.28% |
| **Total** | **2,598,208** | **100.00%** |

Finding 4 excludes the 7,376 unresolved benchmark rows and renormalizes over
2,590,832 benchmarkable rows. The resulting comparison shares are 4.62%
Vertebrates, 64.98% Invertebrates, 17.13% Plants, 6.63% Fungi, and 6.65% Other.

This denominator is an **accepted species-rank backbone-record proxy for
described diversity**, not a complete inventory of extant described species.
The benchmark is treated as fixed: bootstrap intervals quantify publication
sampling uncertainty, not uncertainty or incompleteness in the backbone.

## Exploratory fixed-rank comparison

Result 04 additionally constructs Kingdom → Phylum → Class → Order evidence from the prepared
accepted item matches and the same accepted species-rank snapshot. Publication paths
are de-duplicated within article and weighted `1/p` across the article's `p` complete
paths independently at each rank. Partial resolution is audited and never imputed.

Because the research matches use a newer GBIF API hierarchy, fixed-rank research
geometry keeps exact shared paths only. The sole cross-release bridges are unambiguous
upper containers: bacterial and archaeal domains map to the corresponding snapshot
kingdoms, and viral realms map to `Viruses`. No lower-rank crosswalk is inferred.
Research articles are rebalanced after the shared-path filter. Described-species shares
are not restricted to research-observed paths: they use the complete 2,590,832-record
benchmark and reconcile through auditable local `Remaining` complements. The detailed
method and assignment exports are in the Result 04 specification.

The retained bar-free sunburst uses exact Order-aligned publication paths for research
geometry and the independent complete benchmarkable GBIF base for described diversity.
Segment angle encodes article-balanced research attention only; described-species shares
appear in the hierarchical colour legend. Named taxa retain the reviewed aligned-path
selection, while every named node takes its full GBIF count. Under each expanded parent,
all other complete taxa and species lacking the next rank are combined into one terminal
parent-coloured `Remaining` complement, so the wheel and legend remain exhaustive on
both measures. The unaggregated actual taxa and their visible destinations are exported
for audit. Only the combined top-level `Other kingdoms` branch stays neutral grey. Fungi
is a named terminal Kingdom because its lower-rank segments are too small for the
compact figure.

The wheel adds labels only where the sector can carry them comfortably: named wedges
must span at least 18° and the complete silhouette/name pair must remain inside the
rendered annular wedge with padding. Qualifying labels follow the arc character by
character. The complete silhouette–gap–name unit is centered on both the angular and
radial midpoint of its wedge and uses an automatically selected light or dark
foreground. Icon gaps and label sizes adapt by hierarchy depth so broad inner wedges
are used more effectively. The chart
omits a pair instead of shrinking it when the final fit fails. These labels are
navigational; the hierarchy legend remains the complete key for names and paired
percentages.

## Figure assets and interpretation

The mapping fixes colors and representative clipart for each scheme and for the
sunburst's roomy named wedges. Assets and license metadata live in the mapping and are
cached under `data/taxa-clipart/`.
Silhouettes are visual representatives, not group definitions; SVG is preferred
for publication figures.

All comparisons describe **research attention**. They do not estimate
conservation need, ecological importance, threat severity, population decline,
or the fraction of biodiversity loss attributable to a taxonomic group.
