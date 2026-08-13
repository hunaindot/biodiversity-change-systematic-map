# Result 06 — Research attention, national income, and biodiversity hotspots

## Status and question

This is a live exploratory supporting analysis. It asks whether country-level
publication-fractional research attention is associated with presence in at least one
of Conservation International/CEPF's 36 biodiversity hotspots, whether the categorical
contrast is visible within World Bank income groups, and whether attention rank varies
with the number of overlapping hotspots.

## Live sources

- Result notebook: `notebooks/results/06_research_capacity_and_hotspots.ipynb`.
- Research attention: Result 05's
  `outputs/05_geography_attention/csv/country_attention.csv`.
- World Bank country linkage:
  `data/world-bank/snapshots/wdi-2026-06-30/curated/ipbes_world_bank_crosswalk.parquet`.
- Current World Bank income classification:
  `data/world-bank/snapshots/wdi-2026-06-30/curated/classifications_current.parquet`.
- Hotspot membership: `checklists/mappings/biodiversity_hotspots.json`.
- Result outputs: `notebooks/results/outputs/06_research_capacity_and_hotspots/`.

## Analysis universe and measures

The universe is Result 05's exact 213 observed, valid-ISO3 countries. Research attention
is each country's percentage of the 146,631-publication fractional denominator: a paper
naming `k` resolved countries contributes `1/k` to each. These 213 shares sum to 100%.

Result 02's historical income group is a publication-year attribute, so it cannot provide
one unambiguous stratum per country over 2000–2025. Following Result 02's linkage
workflow, this analysis joins each attention ISO3 through the curated IPBES–World Bank
crosswalk and then to the current World Bank classification. All 213 countries link to a
World Bank entity and FY2027 income group. The country-level export retains World Bank
code, name, region, GNI reference year, effective dates, and a country-API URL. Labels and
order are the same four groups used by Result 02. This is a descriptive capacity
stratifier rather than a direct measure of research capacity.

## Country reconciliation

The hotspot JSON contains 173 hotspot-country entries, 136 distinct source-country names,
and 36 distinct hotspots. A direct anti-join against Result 05 finds 21 unmatched source
names. The notebook requires the manual-rule keys to equal this complete unmatched set:
20 rules harmonize canonical naming variants and one rule folds `Réunion (France)` into
`France`. Réunion has no captured row in the 213-country attention universe. New
Caledonia remains separate because it has its own observed attention row. Puerto Rico is
not present in the supplied JSON.

After mapping, the hotspot-to-attention anti-join is empty. The mapping represents 135
distinct attention countries because France and Réunion collapse to one unit. The reverse
anti-join contains 78 countries; these are the expected non-hotspot controls and receive
`is_hotspot_country = 0` and `n_hotspots = 0`, not missing values. The complete two-way
audit is exported.

## Descriptive analysis and figure

The comparison reports country counts, medians, and means for hotspot versus non-hotspot
countries. Median leads the prose because country attention is strongly right-skewed;
mean remains in the table and is shown as a diamond in the box plot. Current World Bank
income groups provide qualitative context through the same median and mean summaries.
No additional World Bank indicator is introduced.

The primary figure is a pooled two-group box plot. A second 2 × 2 faceted figure repeats
the same hotspot/non-hotspot comparison within each current World Bank income group as
coarse research-capacity context. Boxes show the interquartile range, central lines show
medians, whiskers extend to 1.5 times the interquartile range, points beyond the whiskers
remain visible, and diamonds show arithmetic means. Both vertical display scales are
logarithmic because every observed country has positive attention and shares span several
orders of magnitude. Summary values remain on their original percentage scale.

`n_hotspots` remains in the hotspot and merged country exports for provenance but is not
used in this simplified categorical analysis.

## Current result

Hotspot countries have median attention of 0.076% and mean attention of 0.604% (`n=135`),
versus a median of 0.041% and mean of 0.237% among non-hotspot countries (`n=78`). The
same descriptive pattern appears within all four World Bank income groups, with the
largest median contrast among high-income countries.

## Outputs

- `country_hotspot_categorical_and_graded.csv` — one row for each of the 135 represented
  hotspot countries, with binary presence, hotspot count, and hotspot names;
- `country_world_bank_linkage.csv` — all 213 attention countries linked to World Bank
  entity metadata, FY2027 income group, and country-API URL;
- `country_research_attention_hotspot_analysis.csv` — all 213 countries with attention,
  World Bank linkage, binary exposure, graded exposure, and hotspot names;
- `country_name_match_audit.csv` — every hotspot-source name and every reverse attention
  check;
- `country_name_reconciliation_summary.csv` — anti-join counts before and after rules;
- `hotspot_attention_descriptive_summary.csv` — hotspot and non-hotspot country counts,
  medians, means, and total attention shares;
- `hotspot_attention_descriptive_by_income_group.csv` — the same descriptive contrast
  within each current World Bank income group;
- `discussion_summary.csv` — generated number-first reporting text;
- `figures/hotspot_attention_boxplot.pdf` — the primary pooled two-group box plot;
- `figures/hotspot_attention_boxplot_by_income_group.pdf` — 2 × 2 descriptive facets by
  current World Bank income group; and
- `manifest.json` — parameters, input hashes, reconciliation counts, and artifact list.

## Interpretation boundaries

- Hotspot coding is country presence within a biogeographic boundary, not the proportion
  of national territory within that boundary.
- Folding Réunion into France assigns the parent both Mediterranean Basin and
  Madagascar/Indian Ocean Islands membership.
- `n_hotspots` is retained but deliberately unused; the result is categorical only.
- Country shares are compositional and strongly right-skewed. The summaries describe
  differences in the coded evidence base, not biodiversity-loss occurrence, mechanism,
  or causation.

## Refresh checklist

Run the World Bank preparation and Results 02 and 05 first, then execute Result 06 end to
end. Confirm 213 attention countries and 213 unique World Bank links using one current
classification year, 36 hotspots, 136 distinct hotspot-source names, 21 exhaustive manual
rules, zero post-rule hotspot-to-attention mismatches, 135 hotspot countries, and 78
non-hotspot countries. Confirm all income groups contain both exposure classes, attention
sums to 100%, `n_hotspots` spans 0–4, the full analysis contains no missing exposure or
income values, the income-group medians show the stated qualitative pattern, exactly two PDFs are
exported, no graded measure enters a calculation, and all exported paths appear in the
manifest.
