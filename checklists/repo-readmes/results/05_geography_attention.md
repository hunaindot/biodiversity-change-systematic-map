# Result 05 — Geographic research attention includes large coverage gaps

## Status and question

This is a live exploratory result, not yet a manuscript-backed finding. It asks two
questions together: where is country-resolved biodiversity-loss research concentrated,
and which IPBES places have little or no captured evidence?

The figure is a compact radial wheel of the shared-base evidence distribution. It draws
the 213 observed countries, grouped into contiguous IPBES region sectors. The 36 valid-ISO3
countries with zero evidence and eight structurally unresolvable no-key leaves are omitted
from the wheel but remain explicit in the analytical exports. The visual shows region and
place rings; the subregion level remains available in the tables but is omitted from the figure.

## Live sources

- Result notebook: `notebooks/results/05_geography_attention.ipynb`.
- Integrated evidence input:
  `notebooks/data_processing/outputs/04_biodiversity_evidence_corpus_prep/biodiversity_evidence_corpus.parquet`.
- Shared Result 02 publication base:
  `notebooks/results/outputs/02_income_composition/data/historical_income_publication_country_assignments.parquet`.
- Geography hierarchy: `checklists/mappings/ipbes_regions.json`.
- Analysis modules: `data_helpers/analysis/geo/attention.py` and
  `data_helpers/analysis/geo/attention_plotting.py`.
- Result outputs: `notebooks/results/outputs/05_geography_attention/`.

## Analysis universe

The analysis uses the exact 146,631-publication base retained by Result 02 after its
country complete-case rule, World Bank linkage, historical-income classification, and
2000–2025 window. Result 05 reads those publication identifiers from Result 02's exported
classified assignments and verifies that all 146,631 enter the IPBES country hierarchy.
This makes the two results share a source publication base while leaving Result 02
otherwise unchanged.

Country labels are expanded and de-duplicated to one row per publication × ISO3 pair.
This produces 165,216 unique publication–country assignments. Region and subregion are
always derived from the resolved country through the IPBES mapping. Direct predicted
region or subregion labels are not mixed into the hierarchy because they are distinct
resolution signals and need not nest consistently with country labels.

The complete IPBES mapping contains 257 leaves, five regions, and 18 subregions. Of the
257 leaves:

- 213 have a valid ISO3 code and at least one captured publication in the shared base;
- 36 have a valid ISO3 code but zero captured publications in the shared base; and
- eight have no ISO3 join key and therefore cannot be assigned an evidence count.

The last group is not treated as zero. It is labelled `unresolvable_key` throughout,
with nullable counts, weights, shares, and below-threshold flag in the leaf export.

## Measures and weighting

The ordinary country count is the number of unique publications naming that country. It
is retained for interpretation and defines low evidence as fewer than 100 publications.
A multi-country publication counts once within each named country, so these whole counts
are not additive across countries.

For the additive attention composition, publication `i` naming `k_i` mapped countries
gives each country weight `1 / k_i`. Each country-resolved publication therefore
contributes total weight one across the hierarchy. Country weights sum to 146,631
publication-equivalents, and region and subregion weights are exact sums of their country
children. `attention_share_pct` is the fractional publication-equivalent divided by
146,631.

This distinction is deliberate:

- `whole_publications` answers how many unique papers name a place and defines the
  `<100` flag;
- `fractional_publication_equivalent` and `attention_share_pct` form the additive
  research-attention composition.

## Radial figure

The compact solid centre acts only as a visual anchor. The rings show IPBES region and one
equal-angle slot for every displayed IPBES place. Region angular widths depend on the number
of displayed descendant leaves, not evidence volume. Region labels use compact, upright
names. Antarctica is absent because its only mapped leaf has zero captured evidence and is
retained in the exports rather than drawn. Subregion metadata remains in
`hierarchy_attention.csv`, but the subregion ring is not drawn.

Read clockwise from the 12 o'clock seam. Regions are ordered by descending fractional
attention: Asia & the Pacific (34.34%), Americas (33.96%), Europe & Central Asia (22.67%),
then Africa (9.03%). Within each region, positive-attention countries descend by fractional
attention; exact ties use whole-publication count descending and then country name
alphabetically.

Country attention is shown by an outward log-scaled bar. A logarithmic scale is necessary
because positive country shares span more than five orders of magnitude; a linear scale
would visually collapse nearly all places. Reference guides and the caption state the
nonlinear transform explicitly.

Color encodes IPBES region and flags very small shares:

- positive country shares at or above 0.1% use the saturated parent-region colour;
- positive country shares below 0.1% use a pale version of that region colour;
- zero captured: omitted from the figure and retained in the tables; and
- no ISO3 join key: omitted from the figure and retained in the tables.

The figure omits an internal legend to conserve page space; these encodings belong in
the manuscript caption.

The publication PDF labels all 213 displayed countries on one line with a concise display form
of the name supplied by the IPBES mapping. Parenthetical qualifiers are omitted
only while rendering, as are trailing source footnote asterisks that have no figure note;
conventional short names and compact constituent-territory labels keep every rendered
name to 20 characters and four words or fewer while preserving distinct entries. Labels
for countries with more than 1% fractional attention are bold, while labels below 0.1%
are italic; labels exactly at either threshold remain regular.
Zero-evidence-in-the-shared-base names remain available in the exports. Original
names, ISO3 codes, and exact country counts remain available in `country_attention.csv`;
the complete leaf table is the authoritative source for all names and values.

## Outputs

- `data/publication_country_assignments.parquet` — one unique mapped publication ×
  country assignment, with publication-fractional weight;
- `csv/country_attention.csv` — all 257 IPBES leaves, including zero and no-key states;
- `csv/hierarchy_attention.csv` — root, region, subregion, and country nodes;
- `csv/geography_coverage.csv` — verifies 100% country resolution of the inherited base;
- `csv/geography_coverage_reasons.csv` — zero-count reason rows retained for schema stability;
- `csv/geography_status_by_region.csv` — counts of ≥100, 1–99, zero, and no-key leaves by
  IPBES region;
- `csv/geography_gap_inventory.csv` — all 132 leaves outside the ≥100 band: 88 with
  1–99 publications, 36 valid-key shared-base zeroes, and eight no-key entries;
- `csv/geography_attention_audit.csv` — reconciliation metrics and mention buckets;
- `csv/unresolved_country_tokens.csv` — schema-stable unresolved-token audit, expected
  empty after inheriting Result 02's complete cases;
- `csv/excluded_unresolved_publications.csv` — schema-stable exclusion audit, expected
  empty because exclusions occurred upstream in Result 02;
- `figures/geography_attention_hierarchy_reference.pdf` — publication radial figure
  with labels for 213 observed countries.
- `manifest.json` — analysis parameters, input hashes, grains, headline reconciliation,
  and artifact inventory.

## Interpretation boundaries

- Attention measures where biodiversity-loss research is geolocated, not where loss
  occurs, how severe it is, or where conservation need is greatest.
- `zero_captured` means zero within the Result 02 income-classifiable base under the
  current country coding and crosswalk, not proof that no relevant literature exists.
- Unresolved and income-ineligible records were removed upstream by Result 02; Result 05
  verifies that it makes no further publication exclusions.
- Parent whole-publication counts can overlap because one paper may name countries in
  multiple branches. Only the fractional attention measure is additive.
- Angular width represents membership among displayed leaves, color represents IPBES region
  and the below-0.1% attention class, and radial extent represents attention. Wedge area is
  not an additional quantitative measure.
- Clockwise position represents regional and within-region attention rank, not geography or
  subregion adjacency. This within-region ranking is why the subregion ring is omitted.

## Refresh checklist

Verify the exact 146,631-publication Result 02 base, zero additional exclusions, 165,216
unique assignments, and the 257 = 213 + 36 + 8 leaf reconciliation. Within the 213
observed leaves, verify 125 at ≥100 and 88 at 1–99 publications. Confirm that each
publication's fractional country weights sum to one, all hierarchy parents equal the sum
of their children, attention shares sum to 100%, zero/no-key leaves survive the joins,
and the Result 02 input hash is recorded. Confirm clockwise region ordering and descending
country ordering within each region, that zero-evidence and no-key leaves are absent, and
that no subregion ring is drawn. Render the PDF and
inspect its labels, region separators, pale below-0.1% fills, reference guides, and clipping
at final display size.
