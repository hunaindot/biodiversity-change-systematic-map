# Taxonomic grouping rules and the described-diversity benchmark

Shared reference for every taxonomic analysis (notebooks 11–14). It documents
how validated GBIF hierarchies are collapsed into reporting groups and how the
described-diversity benchmark is constructed. It reports no result of its own.

Analyses that consume this reference:

- `notebooks/results/11-taxonomic-skew-vs-described-diversity.ipynb`
  (`taxonomic-skew-vs-described-diversity.md`);
- `notebooks/results/12-driver-conditional-taxonomic-skew.ipynb`
  (`driver-conditional-taxonomic-skew.md`);
- `notebooks/results/13-realm-conditional-taxonomic-skew.ipynb`
  (`realm-conditional-taxonomic-skew.md`); and
- `notebooks/results/14-temporal-taxonomic-shift.ipynb`
  (`temporal-taxonomic-shift.md`).

Grouping and benchmark construction happen once in
`notebooks/data-processing/02-taxa-analysis-prep.ipynb`. Results notebooks never
reopen raw coding outputs or rebuild the hierarchy.

## Source grain

The L6 rank and group columns are list-valued. Taxa are enriched through the
release-aware GBIF API cache. Every LLM taxon item is grouped from its own
hierarchy before publication-level lists are de-duplicated; class, phylum, and
kingdom lists are never zipped positionally.

The cache is not used to count described species. It does not retain the
taxon-rank and taxonomic-status fields needed to distinguish accepted
species-rank records, and canonical-name homonyms can occur across ranks. The
benchmark is instead streamed directly from the curated backbone with rank and
status filters.

## Multi-resolution group mapping

The versioned mapping is `checklists/mappings/taxa_broad_groups.json`. It
produces three list-valued columns without changing the one-row-per-`UT` grain:

- `broad_taxa_groups` (6): Vertebrates, Invertebrates, Plants, Fungi, Other,
  and Unresolved.
- `taxa_analysis_groups` (9): Vertebrates, Arthropods, Other invertebrates,
  Vascular plants, Other or unspecified plants, Fungi, Bacteria & archaea,
  Other taxa, and Unresolved.
- `taxa_detail_groups` (14): Mammals, Birds, Fishes, Reptiles & amphibians,
  Arthropods, Molluscs, Other invertebrates, Vascular plants, Non-vascular
  plants & Plantae algae, Plants—phylum unspecified, Fungi, Bacteria & archaea,
  Other taxa, and Unresolved.

Rules are applied independently to each exact or accepted-fuzzy GBIF match. In
the six-group broad scheme, Animalia + Chordata identifies Vertebrates. This
phylum-level rule is also usable for the curated described-species benchmark,
which has phylum but no subphylum field. Other Animalia with a present phylum
enters Invertebrates. The analysis and detail schemes retain the stricter
SUBPHYLUM = Vertebrata definition; their non-vertebrate Chordata records enter
Other invertebrates.

DOMAIN = Bacteria or Archaea explicitly enters Other in the broad scheme,
including when KINGDOM is absent, and receives the dedicated Bacteria & archaea
label in the analysis and detail schemes. Tracheophyta identifies vascular
plants. At the detailed level, Plantae with a present non-Tracheophyta phylum
forms the non-vascular/Plantae algae category; missing plant phylum remains
explicit rather than being misclassified as non-vascular. Animalia with
insufficient hierarchy and any other accepted hierarchy that matches no rule
enters Unresolved.

Not applicable values and non-accepted matches receive no group. Publications
with no eligible group remain in the one-row-per-`UT` output and are reported in
the grouping audits.

No grouping rule uses genus or species names; those predictions are used only to
obtain their validated higher hierarchy.

`Unresolved` is a data-quality state, not a biological group. It never enters a
biological composition; each analysis reports it separately in its resolution
audit.

## Described-diversity benchmark

The local source is `data/gbif/curated/gbif_curated.csv`, derived from the GBIF
Backbone Taxonomy snapshot dated 28 August 2023. Its EML is stored at
`data/gbif/extracted/eml.xml`; the dataset DOI is
[10.15468/39omei](https://doi.org/10.15468/39omei).

The 3.4 GB curated backbone is streamed with PyArrow. A row enters the benchmark
only when:

- `taxonRank`, case-insensitive, equals `species`; and
- `taxonomicStatus`, case-insensitive, equals `accepted`.

The same broad-group mapping is applied to the accepted species lineage. The
current file contains 7,694,321 rows, including 4,961,031 species-rank rows and
2,598,208 accepted species-rank rows. No accepted species record is missing its
`taxonID`.

| Broad group | Accepted species-rank rows | Share of all accepted |
| --- | ---: | ---: |
| Vertebrates | 119,596 | 4.60% |
| Invertebrates | 1,683,461 | 64.79% |
| Plants | 443,824 | 17.08% |
| Fungi | 171,668 | 6.61% |
| Other | 172,283 | 6.63% |
| Unresolved | 7,376 | 0.28% |

Analyses that compare attention with described diversity exclude the 7,376
`Unresolved` rows symmetrically with unresolved publications and renormalize
over the remaining 2,590,832 benchmarkable rows; see
`taxonomic-skew-vs-described-diversity.md` for the renormalized shares actually
reported.

GBIF describes this backbone as a synthetic management classification built from
many sources. It also includes OTUs from iBOL and UNITE and names from the
Paleobiology Database. The denominator is therefore labelled an accepted
species-rank backbone-record proxy for described diversity, not a complete
inventory of extant described species.

The benchmark is treated as fixed. Bootstrap intervals quantify publication
sampling uncertainty, not incompleteness or taxonomic uncertainty in the GBIF
backbone.

## Figure assets

The mapping stores a fixed color and representative clipart reference for every
label in every scheme. `group_clipart` maps each label to a reusable record in
`clipart_assets`, which provides the source page, direct SVG and thumbnail
links, license, and attribution. Assets are cached locally under
`data/taxa-clipart/` (gitignored, downloaded on first run) and applied through
`data_helpers/analysis/taxa/clipart.py`.

All organism silhouettes are CC0 1.0 assets from PhyloPic. They are visual
representatives rather than taxonomic definitions: for example, a carp
represents the heterogeneous Vertebrates group, and a frog represents the
combined Reptiles & amphibians label. Unresolved uses a neutral question-mark
symbol from Font Awesome under CC BY 4.0, because assigning an organism
silhouette would falsely imply taxonomic resolution. SVG should be preferred for
publication figures.

Group colors are fixed across schemes and figures. `Arthropods` carries the same
hex (`#E15759`) in both the `analysis` and `detail` schemes so that the same
label never reads as two different colors in adjacent figures.

## Interpretation boundary

Every analysis built on this reference describes **research attention**. None of
them estimates conservation need, threatened-species diversity, ecological
importance, threat severity, population decline, coverage of undescribed
species, or the fraction of biodiversity loss attributable to any driver.

## History

This file replaces `taxa-by-driver.md`, the design doc for the retired notebook
`10-taxa-by-driver.ipynb`. That analysis partitioned each publication as
`1/(g·d)` across the whole taxon × driver grid, which estimates the joint
distribution rather than the taxonomic composition *within* a driver. It was
superseded by notebook 12, which uses the conditional `1/g` weighting and
log2 LQ; notebook 12 retains the partitioned estimator as a sensitivity, and
notebook 11 took over the described-diversity comparison. The grouping and
benchmark sections above were shared infrastructure and are preserved here
unchanged.
