# Finding 2 — Biodiversity-loss evidence differs systematically across national income groups

## Finding and question

Does the documented-threat composition of biodiversity-loss evidence differ with the
income group of the country a study is about, and do the differences survive holding
region and publication period constant?

Lower-income-country evidence assigns larger shares of attention to agriculture and
aquaculture and to biological resource use. Higher-income-country evidence assigns
larger shares to pollution, invasive and problematic species, and climate change. The
agriculture, biological-resource-use, invasive-species, and climate contrasts persist
after standardizing the higher- and lower-income tiers to a common regional and temporal
composition. Pollution does not behave as a stable income contrast under region-only
adjustment and is interpreted more cautiously.

## Live sources

- Finding notebook: `notebooks/results/02_income_composition.ipynb`.
- Integrated evidence input:
  `notebooks/data_processing/outputs/04_biodiversity_evidence_corpus_prep/biodiversity_evidence_corpus.parquet`.
- Historical World Bank input:
  `data/world-bank/snapshots/wdi-2026-06-30/curated/classifications_historical.parquet`.
- Country crosswalk: `checklists/mappings/ipbes_world_bank_mapping.json`.
- Result outputs: `notebooks/results/outputs/02_income_composition/`.
- Manuscript section: *Biodiversity-loss evidence differs systematically across national
  income groups*.

## Analysis universe

The primary analysis retains publications that:

- report a negative biodiversity impact;
- have `pred_study_design == "Observational"`;
- identify at least one study country that maps to a World Bank economy;
- can be assigned one of the four standard World Bank income groups in the publication
  year; and
- were published in a complete year from 2000 through 2025.

There are 116,684 negative-direction observational publications before geographic and
income matching. Country linkage produces 107,929 publication–country assignments from
97,430 unique publications. The primary historical-income window contains 104,556
assignments from 94,443 unique publications across 213 countries.

Income is matched to the official classification in force in the publication year, not
to the current classification. This reclassifies 11.0% of comparable
publication–country assignments; the audit records 11,841 reclassified assignments.

The income-group coverage used in the manuscript figure is:

| Historical income group | Unique publications | Represented countries |
| --- | ---: | ---: |
| Low income | 4,973 | 69 |
| Lower middle income | 15,981 | 99 |
| Upper middle income | 30,808 | 89 |
| High income | 45,554 | 85 |

Publications that study countries in more than one income group contribute to each
relevant group, so these group counts sum above the 94,443-publication denominator.
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
| Agriculture & aquaculture | 25.04% | 9.01% | −16.03 points | −16.99 to −14.95 |
| Biological resource use | 21.40% | 9.19% | −12.21 points | −13.25 to −11.17 |
| Pollution | 13.63% | 22.98% | +9.34 points | +8.47 to +10.27 |
| Invasive & problematic species | 8.91% | 17.96% | +9.05 points | +8.25 to +9.92 |
| Climate change & severe weather | 8.98% | 14.95% | +5.96 points | +5.19 to +6.71 |
| Natural system modifications | 6.16% | 10.65% | +4.49 points | +3.88 to +5.05 |

### Higher-income minus lower-income standardized tiers

| Threat category | Raw | Region-standardized | Region-and-period standardized | 95% interval for joint standardization |
| --- | ---: | ---: | ---: | ---: |
| Invasive & problematic species | +6.23 | +5.28 | +5.23 | +4.38 to +6.01 |
| Climate change & severe weather | +3.23 | +3.91 | +2.96 | +1.11 to +3.90 |
| Pollution | +1.13 | −0.06 | +1.54 | +0.21 to +2.81 |
| Natural system modifications | +3.27 | +0.84 | +1.19 | +0.47 to +1.84 |
| Biological resource use | −6.97 | −5.56 | −5.38 | −6.35 to −4.42 |
| Agriculture & aquaculture | −6.46 | −5.98 | −6.99 | −7.93 to −5.89 |

Pooling the middle-income groups attenuates the tier contrasts relative to the extreme
high-versus-low comparison. Pollution is the exception to the stable pattern: its tier
contrast falls to approximately zero under region-only standardization. It is therefore
not interpreted as a robust income difference even though the joint-standardized
estimate is positive.

## Robustness

The notebook recalculates the extreme-group contrast under five alternatives:

- all negative-direction study designs;
- current rather than historical income classification;
- fiscal year equal to publication year plus one;
- inclusion of the partial 2026 year; and
- country-fractional weighting.

All specifications preserve the direction of every contrast. Spearman rank correlations
with the primary contrast range from 0.993 to 1.000, and the largest individual change is
4.22 percentage points under current income classification.

## Figures and outputs

The manuscript figure is `figures/income_composition.pdf`. Panel A shows within-group
composition; Panel B shows high-income-minus-low-income differences with bootstrap
intervals.

The current manuscript source references it as
`checklists/overleaf/main/attachments/income_composition.pdf`. That attachment is not
present in this checkout and must be synchronized from the live result output before a
local manuscript build.

Reported files are:

- `csv/historical_income_classification_audit.csv`;
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

Verify the 94,443-publication denominator, 213-country coverage, and reclassified share
against `historical_income_classification_audit.csv`. Recalculate all displayed contrasts
from the two exported contrast tables, then confirm that the manuscript still treats
pollution as unstable under region-only adjustment.
