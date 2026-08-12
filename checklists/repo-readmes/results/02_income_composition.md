# Finding 2 — Biodiversity-loss evidence differs systematically across national income groups

## Finding and question

Does the documented-threat composition of biodiversity-loss evidence differ with the
income group of the country a study is about, and do the differences survive holding
region and publication period constant?

Lower-income-country evidence assigns larger shares of attention to agriculture and
aquaculture and to biological resource use. Higher-income-country evidence assigns
larger shares to pollution, invasive and problematic species, and climate change. All
five contrasts persist after jointly standardizing the higher- and lower-income tiers to
a common regional and temporal composition. Pollution attenuates after region-only
standardization (+0.68 percentage points) but remains positive after joint
region-and-period standardization (+2.83 points; 95% bootstrap interval +1.70 to +3.88).

## Live sources

- Finding notebook: `notebooks/results/02_income_composition.ipynb`.
- Integrated evidence input:
  `notebooks/data_processing/outputs/04_biodiversity_evidence_corpus_prep/biodiversity_evidence_corpus.parquet`.
- Historical World Bank input:
  `data/world-bank/snapshots/wdi-2026-06-30/curated/classifications_historical.parquet`.
- Country crosswalk: `checklists/mappings/ipbes_world_bank_mapping.json`.
- Geographic map crosswalk: `checklists/mappings/ipbes_regions.json`.
- Country polygons:
  `data/ipbes-polygons/ipbes_regions_subregions_shape_1.1/IPBES_Regions_Subregions2.shp`.
- Result outputs: `notebooks/results/outputs/02_income_composition/`.
- Manuscript section: *Biodiversity-loss evidence differs systematically across national
  income groups*.

## Analysis universe

All three panels retain publications that:

- report a negative biodiversity impact;
- identify at least one study country that maps to a World Bank economy;
- can be assigned one of the four standard World Bank income groups in the publication
  year; and
- were published in a complete year from 2000 through 2025.

There is no primary study-design restriction. The observational subset is retained only
as a sensitivity comparison. Across all available publication years, the
negative-direction evidence contains 253,081 publications; World Bank linkage produces
171,595 publication–country assignments from 151,541 unique publications. The complete
2000–2025 historical-income window used by every panel contains 166,282 assignments from
146,892 unique publications across 213 countries. The largest country count is 25,689
for the United States.

Income is matched to the official classification in force in the publication year, not
to the current classification. This reclassifies 10.6% of comparable in-window
publication–country assignments; the audit records 17,709 reclassified assignments.

The income-group coverage used in the manuscript figure is:

| Historical income group | Unique publications | Represented countries |
| --- | ---: | ---: |
| Low income | 6,986 | 70 |
| Lower middle income | 23,659 | 101 |
| Upper middle income | 48,284 | 90 |
| High income | 73,385 | 85 |

Publications that study countries in more than one income group contribute to each
relevant group, so these group counts sum above the 146,892-publication denominator.
Multiple countries in the same income group do not multiply a publication's contribution
to that group.

## Weighting and contrasts

Country expansion is used to assign income group, region, and period; the publication
remains the evidentiary unit. Within each publication × income-group block, a publication
carrying (k) distinct Threat-L0 labels gives weight (1/k) to each label. Each block
therefore contributes total weight one, and each income group's threat shares sum to
100%.

The primary contrast is the high-income share minus the low-income share, in percentage
points. Uncertainty comes from 1,000 publication-level bootstrap replicates with seed
20260719.

The adjusted comparison pools low and lower-middle income countries into a lower-income
tier and upper-middle and high income countries into a higher-income tier. Both tiers are
directly standardized to the same distribution over the 28 World Bank region ×
publication-period strata observed in both tiers. These are descriptive adjustments, not
causal estimates.

## Manuscript-facing results

### High-income minus low-income composition

| Threat category | Low-income share | High-income share | Difference | 95% bootstrap interval |
| --- | ---: | ---: | ---: | ---: |
| Agriculture & aquaculture | 24.23% | 8.55% | −15.68 points | −16.61 to −14.79 |
| Biological resource use | 18.78% | 8.62% | −10.16 points | −10.95 to −9.29 |
| Pollution | 14.55% | 24.31% | +9.75 points | +8.95 to +10.53 |
| Invasive & problematic species | 8.63% | 17.07% | +8.45 points | +7.80 to +9.08 |
| Climate change & severe weather | 11.40% | 17.33% | +5.93 points | +5.18 to +6.63 |
| Natural system modifications | 6.73% | 9.97% | +3.24 points | +2.73 to +3.75 |

### Higher-income minus lower-income standardized tiers

| Threat category | Raw | Region-standardized | Region-and-period standardized | 95% interval for joint standardization |
| --- | ---: | ---: | ---: | ---: |
| Invasive & problematic species | +5.76 | +4.74 | +5.01 | +4.34 to +5.64 |
| Pollution | +1.88 | +0.68 | +2.83 | +1.70 to +3.88 |
| Climate change & severe weather | +3.06 | +4.38 | +2.24 | +1.07 to +3.26 |
| Natural system modifications | +2.44 | −0.04 | +0.30 | −0.35 to +0.86 |
| Biological resource use | −5.70 | −4.77 | −4.24 | −4.97 to −3.53 |
| Agriculture & aquaculture | −6.40 | −6.70 | −7.56 | −8.38 to −6.67 |

Pooling the middle-income groups attenuates the tier contrasts relative to the extreme
high-versus-low comparison. Agriculture, biological resource use, invasive species,
climate change, and pollution retain joint-standardized intervals excluding zero.
Natural system modifications attenuates to +0.30 points, with an interval spanning zero.

## Robustness

The notebook recalculates the extreme-group contrast under five alternatives:

- observational studies only;
- current rather than historical income classification;
- fiscal year equal to publication year plus one;
- inclusion of the partial 2026 year; and
- country-fractional weighting.

All ten categories displayed in panel c preserve their direction across the alternatives.
Spearman rank correlations across all 12 categories range from 0.993 to 1.000, and the
largest individual change is 5.01 percentage points under current income classification.

## Figures and outputs

The manuscript figure is `figures/income_composition.pdf`. All panels use the same
146,892 country-resolved biodiversity-loss publications from all study designs across
213 countries. Countries are coloured with fixed 1--3--10 count classes from 1 through
30,000 using a nine-step yellow-green-to-blue biodiversity ramp; grey denotes zero
publications in this shared subset. Panel b shows composition across the
four historical income groups, abbreviated LIC, LMIC, UMIC, and HIC, with each article
count in parentheses beneath its abbreviation. All 12 observed threat
categories are retained in the legend. Its ten contrasted categories are stacked
bottom-up in panel c's signed order, followed by `Other threats` and `Unclear` as a
residual block at the top. The legend reads in the reverse direction, matching panel c
from top to bottom (pollution through agriculture), before listing `Other threats` and
`Unclear`. Panel c
shows the raw HIC-minus-LIC differences with bootstrap intervals, ordered from the most
negative to the most positive contrast.

The current manuscript source references it as
`checklists/overleaf/main/attachments/income_composition.pdf`; keep that manuscript copy
synchronized with the live result output before compiling the paper.

Reported files are:

- `csv/historical_income_classification_audit.csv`;
- `csv/country_article_counts.csv`;
- `csv/income_group_article_counts.csv`;
- `csv/income_group_threat_composition.csv`;
- `csv/high_minus_low_income_bootstrap.csv`;
- `csv/region_period_standardized_tier_contrast.csv`;
- `csv/sensitivity_summary.csv`;
- `data/historical_income_publication_country_assignments.parquet`; and
- `data/historical_income_threat_attributions.parquet`.

The older unchecked income-composition notebook and its outputs are archived. They do not
define an additional finding.

## Interpretation boundaries

- Income refers to the country a study is about, not author affiliation or funding
  origin.
- Threat shares measure documented scientific attention, not ecological threat
  prevalence or severity.
- Standardization controls the observed regional and period composition descriptively;
  it does not identify a causal effect of national income.
- A publication may contribute to several income groups when it studies countries in
  different groups, but it contributes only once within any one group.

## Refresh checklist

Verify the shared 146,892-publication denominator, 213-country coverage, 166,282 unique
publication–country assignments, maximum country count of 25,689, and 10.6% reclassified
share against the notebook assertions and exported audit tables. Recalculate all
displayed contrasts from the two exported contrast tables, including pollution's
region-only point estimate (+0.68; no interval calculated) and joint estimate (+2.83;
95% bootstrap interval +1.70 to +3.88).
