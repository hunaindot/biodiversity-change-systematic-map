# Temporal persistence of taxonomic attention

## Question

Did the rapid growth of the biodiversity-loss evidence base between 2000 and
2025 rebalance publication attention from vertebrates towards invertebrates?

This is Vector 6 of the taxonomic-attention analysis. It links the broad
taxonomic baseline to the temporal-development finding. It measures publication
attention, not organism abundance, extinction risk, ecological importance,
research quality, or coverage of undescribed species.

## Notebook and shared code

- Notebook: `notebooks/results/14-temporal-taxonomic-shift.ipynb`.
- Integrated preparation notebook:
  `notebooks/data-processing/04-biodiversity-evidence-corpus-prep.ipynb`.
- Taxa preparation and benchmark notebook:
  `notebooks/data-processing/02-taxa-analysis-prep.ipynb`.
- Analysis helper: `data_helpers/analysis/taxa/temporal.py`.
- Figure helper: `data_helpers/analysis/taxa/temporal_plotting.py`.
- Configuration: `taxa_temporal` in
  `checklists/mappings/results_config.json`.
- Broad grouping rules and colors:
  `checklists/mappings/taxa_broad_groups.json`.

The results notebook opens no coding source and reconstructs no taxonomic
hierarchy. It consumes the integrated one-row-per-UT artifact and the prepared
GBIF broad benchmark. Both handoffs must match the current grouping-rules
fingerprint.

## Grain, scope, and inclusion

The integrated source contains 605,199 unique eligible publications. The
primary temporal universe retains:

- negative biodiversity impacts;
- complete years 2000–2025; and
- all study designs.

This gives 245,168 unique publications. Of these, 171,791 have at least one
benchmarkable broad group and 100,206 contain Vertebrates or Invertebrates.
Broad taxonomic inclusion states account back to the full temporal universe:

| State | Publications | Share |
| --- | ---: | ---: |
| At least one benchmarkable broad group | 171,791 | 70.07% |
| Not applicable only | 57,725 | 23.55% |
| Unclear only | 1,594 | 0.65% |
| Accepted taxon but broad hierarchy unresolved | 1,922 | 0.78% |
| Reported taxon but no accepted benchmarkable match | 12,136 | 4.95% |

The broad-resolved share falls from 76.7% in 2000 to 66.9% in 2025. This is
mainly the rise of `Not applicable only` from 17.0% to 27.2%; all other
taxonomic exclusions together remain 5.9% in 2025.

## Estimands and weighting

For broad composition, publication \(i\) linked to \(g_i\) benchmarkable broad
groups contributes \(1/g_i\) to every group it carries. The five groups are
Vertebrates, Invertebrates, Plants, Fungi, and Other.

The primary animal expression retains publications carrying Vertebrates or
Invertebrates and rebalances each publication over those two labels only. A
publication carrying both contributes one half to each. This is the closest
analogue to Titley et al. (2017).

Annual estimates cover every complete year. The prespecified period estimates
use 2000–04, 2005–09, 2010–14, 2015–19, and 2020–25. Whole-publication label
patterns are resampled in 2,000 multinomial bootstrap replicates with seed
20260731. The first-to-last contrast subtracts independently resampled period
estimates. Annual trends use publication-count-weighted least squares with
HAC(2) intervals.

## Primary result

Annual negative-impact publication volume grows from 2,530 in 2000 to 20,520
in 2025, an 8.11-fold increase. The animal balance does not materially change:

| Animal group | 2000–04 | 2020–25 | Change | 95% bootstrap interval |
| --- | ---: | ---: | ---: | ---: |
| Vertebrates | 62.35% | 62.11% | -0.24 pp | -1.51 to +0.98 pp |
| Invertebrates | 37.65% | 37.89% | +0.24 pp | -0.98 to +1.51 pp |

The annual vertebrate trend is -0.04 percentage points per decade (HAC 95% CI
-0.58 to +0.50; p = 0.878). Vertebrate and invertebrate animal-attention counts
grow 6.28-fold and 6.36-fold, respectively.

The fixed animal GBIF proxy assigns 6.63% of described species to vertebrates
and 93.37% to invertebrates. In 2020–25, vertebrates therefore receive 9.36
times their proxy share and invertebrates receive 0.41 times theirs. Publication
growth expanded the established animal taxonomic lens rather than rebalancing
it.

## Broad-group nuance

The five-group composition is not static:

| Broad group | 2000–04 | 2020–25 | Change |
| --- | ---: | ---: | ---: |
| Vertebrates | 37.12% | 33.53% | -3.59 pp |
| Invertebrates | 20.96% | 18.85% | -2.11 pp |
| Plants | 33.01% | 34.49% | +1.48 pp |
| Fungi | 2.72% | 3.16% | +0.44 pp |
| Other | 6.19% | 9.97% | +3.78 pp |

The declining broad vertebrate share is not an invertebrate catch-up. Both
animal groups lose broad share as Plants, Fungi, and especially Other gain.
The paper claim should therefore concern the persistent animal split, not a
fully static five-group composition.

## Robustness and conditional diagnostics

The animal result remains flat across all directions and among publications
with one broad group only. Observational studies are the exception:
vertebrate attention rises from 66.85% to 69.23%, a +2.38 percentage-point
contrast with a bootstrap interval of +0.64 to +4.04 points. Its annual trend
is +1.16 points per decade.

Exploratory publication-level models use fractional vertebrate attention as the
outcome and cluster standard errors by year. Adjustment for complete driver
patterns changes the slope to +1.17 points per decade; joint adjustment for
driver, realm, and study-design patterns gives +1.04 points per decade. This
indicates that the changing composition of the evidence base conceals modest
within-context worsening. Driver-stratified estimates locate the clearest rise
in pollution research, at +1.52 points per decade. These are secondary bridges
to Vector 2 rather than replacements for the prespecified aggregate result.

## Literature framing

Titley et al. (2017) is the direct publication-composition comparator. It uses
526 Web of Science primary animal studies with `biodiversity` in the title and
reports a roughly stable vertebrate bias from 1995–2015. The present corpus is
much larger, impact-specific, and extends through 2025.

Troudet et al. (2017) primarily analyses GBIF occurrence accumulation. Its Web
of Science publication counts are an explanatory research-activity proxy, not
the response analysed here. Troudet reports persistent broad occurrence-data
bias alongside a widening bird-occurrence gap. The current result is therefore
complementary rather than an exact replication.

## Reported outputs

The notebook saves only files that support the reported figures or inference:

- `csv/temporal-taxonomic-attention.csv`: annual and period composition plus
  the annual resolution series;
- `csv/temporal-taxonomic-inference.csv`: contrasts, trends, growth, scope
  sensitivities, adjusted models, and driver-stratified diagnostics;
- `csv/manifest.json`: compact provenance;
- `figures/temporal-animal-taxonomic-skew.pdf`: main three-panel result; and
- `figures/broad-taxonomic-composition-over-time.pdf`: five broad-group small
  multiples against the fixed GBIF proxy.
