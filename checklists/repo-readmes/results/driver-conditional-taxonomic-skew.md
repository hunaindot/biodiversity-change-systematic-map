# Driver-conditioned taxonomic attention

> **Archived.** The notebook this document specifies was retired on 2026-08-01 and
> now lives at `notebooks/results/archive/`, with its outputs under
> `notebooks/results/archive/outputs/`. No manuscript claim rests on it. The
> live result-04 notebook is `notebooks/results/04-taxonomic-lens.ipynb`;
> see `taxa-grouping-and-benchmark.md` for the shared grouping and benchmark rules.
> The specification below is retained as the record of how the analysis was built.
> Its estimator — conditional `1/g` weighting and log2 location quotient — is
> unchanged in result 04; only the reporting surface was reduced to what the
> manuscript states.

## Question and scope

Does the taxonomic composition of biodiversity-loss research change across
the five IPBES direct drivers? The primary analysis uses the current eight
biological `analysis` groups. `Unresolved` remains a separate data-quality
state and never enters the biological composition.

The unit is one publication (`UT`). The primary universe is restricted to
negative-direction records in the complete years 2000–2025. Results describe
research attention, not ecological impact, conservation need, or the number of
species affected by a driver.

## Reproducible implementation

- Notebook: `notebooks/results/12-driver-conditional-taxonomic-skew.ipynb`.
- Shared preparation notebook:
  `notebooks/data-processing/02-taxa-analysis-prep.ipynb`.
- Preparation helper: `data_helpers/prep/taxa_analysis_prep.py`.
- Analysis helper: `data_helpers/analysis/taxa/driver_conditional.py`.
- Figure helper: `data_helpers/analysis/taxa/driver_conditional_plotting.py`.
- Configuration: `taxa_driver_conditional` in
  `checklists/mappings/results_config.json`.
- Taxonomic order and colors:
  `checklists/mappings/taxa_broad_groups.json`, scheme `analysis`.

The results notebook performs analytical selection, weighting, bootstrap
inference, sensitivities, exports, and plotting. Source linkage, list parsing,
taxonomic grouping states, and match accounting are performed once in the
preparation notebook and loaded through a validated artifact contract.

## Grain and inclusion

The canonical prepared handoff contains 605,199 unique, non-missing `UT`
values. Its manifest records that the eligible merged corpus and taxa-with-API
source have matching one-to-one key sets. Loading checks the schema, semantic
taxonomic-rule fingerprint, row count, and unique key before analysis.

The negative 2000–2025 universe contains 245,168 publications. Every record
has at least one configured driver; 171,761 have at least one resolved
biological analysis taxon and enter the primary composition. The 73,407
excluded records contain no resolved biological analysis group. There are
21,878 multi-driver and 23,340 multi-taxon publications in the primary set.

Taxonomic resolution differs by driver:

| Driver | Resolved / driver publications | Resolution |
| --- | ---: | ---: |
| Land/sea-use change | 43,490 / 74,992 | 58.0% |
| Direct exploitation | 27,496 / 39,073 | 70.4% |
| Climate change | 34,394 / 51,003 | 67.4% |
| Pollution | 80,398 / 109,705 | 73.3% |
| Invasive alien species | 22,995 / 25,709 | 89.4% |

These denominators are reported before the composition because the result is
conditional on having at least one resolved taxon.

## Conditional estimator

If publication \(i\) has \(g_i\) resolved taxon groups, every group receives
weight \(1/g_i\) inside every driver carried by the publication. Thus a
multi-driver paper counts once in each relevant driver condition, while its
taxonomic contribution sums to one within that condition.

The primary comparison is:

\[
\log_2 LQ_{gd}=\log_2\left[\frac{p(g\mid d)}{p(g)}\right].
\]

The superseded \(1/(g_i d_i)\) partition is retained only as a sensitivity. It
answers how publications divide across the complete group × driver table, not
the conditional question.

Whole-publication bootstrapping collapses identical taxon × driver label
vectors and draws 1,000 multinomial replicates with seed 20260731. This retains
multi-label dependence and avoids treating exploded assignments as independent.

## Primary result

| Driver | Vertebrates | Arthropods |
| --- | ---: | ---: |
| Land/sea-use change | 40.6% | 9.1% |
| Direct exploitation | 50.5% | 7.5% |
| Climate change | 25.9% | 8.9% |
| Pollution | 31.0% | 12.2% |
| Invasive alien species | 30.2% | 13.4% |
| Overall resolved corpus | 34.6% | 11.0% |

The motivating claim is only partly supported. Pollution does carry more
arthropod attention than climate change: +3.27 percentage points, 95% bootstrap
CI +2.94 to +3.61. Invasive alien species is a further +1.20 points above
pollution, 95% CI +0.75 to +1.62.

## Concentration of the taxonomic lens

The reported finding is stated as two sign patterns counted directly off the
log2 location quotients already plotted in the heatmap. No additional metric is
introduced. Each pattern carries a **margin**: the location quotient nearest
zero among the groups being counted, which is how close the pattern sits to
failing.

| Driver | Vertebrate log2 LQ | Other groups below | All below | Margin | Inclusive groups above | All above | Margin |
| --- | ---: | ---: | :---: | ---: | ---: | :---: | ---: |
| Direct exploitation | +0.54 | **7 / 7** | **yes** | **−0.15** | 0 / 4 | no | −1.51 |
| Land/sea-use change | +0.23 | 5 / 7 | no | +0.48 | 0 / 4 | no | −1.19 |
| Climate change | −0.42 | 3 / 7 | no | +0.51 | 1 / 4 | no | −0.88 |
| Invasive alien species | −0.20 | 3 / 7 | no | +0.29 | 2 / 4 | no | −1.34 |
| Pollution | −0.16 | 2 / 7 | no | +0.88 | **4 / 4** | **yes** | **+0.15** |

Two statements follow:

- **Direct exploitation is the only driver that over-represents vertebrates
  while every one of the seven other groups falls below its corpus-wide share.**
- **Pollution is the only driver that over-represents all four invertebrate,
  fungal, and microbial groups** (arthropods, other invertebrates, fungi, and
  bacteria & archaea).

Read together with the driver-composition finding, the two drivers assessed to
have the largest global impact — land/sea-use change and direct exploitation —
are the two whose evidence is most concentrated on vertebrates, while pollution,
the driver most over-attended relative to assessed impact, is the most
taxonomically inclusive.

Both statements rest on one group sitting only about 10% from parity — other or
unspecified plants at −0.15 for exploitation, arthropods at +0.15 for pollution.
That is the honest limitation, and it should be reported alongside the counts.

The estimator is `driver_taxonomic_concentration` in
`data_helpers/analysis/taxa/driver_conditional.py`, a pure function of the conditional
composition; the focal and inclusive group sets are configured as
`concentration_focal_group` and `concentration_inclusive_groups`. The margin
alone determines each flag, so the two cannot disagree, and an undefined cell
propagates rather than being skipped.

**No bootstrap is reported for these two statements.** With 171,761 publications
the sign patterns are many standard errors from flipping, so resampling returned
100% and 0% and carried no information; the margin answers the useful question
instead. This does not extend to the planned contrasts, whose percentage-point
differences retain their bootstrap intervals.

The counts are tallies over point estimates. These remain research-attention
statements and say nothing about ecological impact.

Climate change is not primarily a birds-and-mammals lens. Its vertebrate share
is 5.11 points below pollution, 95% CI −5.64 to −4.61, and 24.55 points below
direct exploitation, 95% CI +23.91 to +25.17 for exploitation minus climate.
The detail labels show that direct exploitation is especially fish- and
mammal-oriented, while climate is plant-oriented. Pollution elevates fishes,
arthropods, other invertebrates, and bacteria/archaea.

## Sensitivities

The notebook reports:

- the partitioned \(1/(g_i d_i)\) estimator;
- negative plus mixed directions;
- all direction states;
- observational studies only;
- single-driver publications only; and
- five fixed publication periods from 2000–2004 through 2020–2025.

Absolute magnitudes change, especially when all direction states are admitted,
but the focal driver ordering is stable. This supports a result about changing
research specialization while preserving caution about direction scope, study
design, and overlapping drivers.

## Outputs

All artifacts are written under:

`notebooks/results/outputs/12-driver-conditional-taxonomic-skew/`

The lean result bundle contains six CSV/JSON handoffs:

- `driver-taxa-resolution.csv`;
- `driver-conditional-taxonomic-attention.csv`, containing both analysis and
  detail resolutions plus analysis-group rank probabilities;
- `planned-driver-contrasts.csv`;
- `driver-taxonomic-concentration.csv`, the two sign-pattern counts and their
  margins;
- `taxonomic-attention-sensitivities.csv`, consolidating scope, weighting, and
  publication-period checks; and
- `manifest.json`, which links the estimates to the prepared artifact and
  fixed analytical parameters.

It also contains four vector PDFs:

- `taxonomic-resolution-by-driver.pdf`;
- `taxonomic-specialization-by-driver.pdf`;
- `vertebrate-arthropod-specialization-by-driver.pdf`; and
- `focal-detail-groups-by-driver.pdf`.

The heatmap uses color for log2 LQ and prints conditional attention share in
every cell. The focal interval plot reports 95% publication-bootstrap intervals.
Figures follow the repository scientific-visualization and Tufte guidance.
Processing audits and publication evidence are not duplicated here; they live
once in `notebooks/data-processing/outputs/02-taxa-analysis-prep/`.

## Figure design

- **Color: `PuOr` (orange–purple), not the project's default diverging `PRGn`.**
  This is a deliberate exception, not a silent deviation. `Vertebrates`
  already carries `#2E7D32` — the same hex as `BIODIVERSITY["primary"]` — as
  its identity color throughout this notebook family (panel titles, dot
  colors, icon tint). A green pole on the heatmap would read as "Vertebrates"
  regardless of sign, overloading green with two conflicting meanings in the
  same figure. `PuOr` keeps the diverging-deviation convention (two hues +
  neutral midpoint) without colliding with the categorical taxon palette.
- **The heatmaps use `pcolormesh`.** Cells therefore remain vector-native in
  the PDF rather than being embedded as a low-resolution raster. Conditional
  shares are printed in every cell, so the color scale carries specialization
  while the labels carry composition.
- **The four diagnostic exports are manuscript-clean.** Titles, headlines,
  decorative silhouettes, and caveat footers are omitted because those belong
  in the surrounding text or caption. The resolution and focal-interval plots
  use compact single- or two-panel layouts; the detail composition uses one
  dense group-colored matrix rather than five repeated small multiples.
- **Notebook 14 assembles the reporting figure.** Panel B reuses the analysis
  table behind `taxonomic-specialization-by-driver.pdf`, preserving the same
  estimator and color semantics while integrating it with the baseline and
  temporal results in `taxon-driver-composition.pdf`.
- **`Arthropods` now has one color across schemes.** The `analysis` scheme
  previously colored `Arthropods` `#4E79A7` (blue) while the `detail` scheme
  colored it `#E15759` (red) — the same label read differently in adjacent
  figures within this notebook (the specialization heatmap/interval plots vs.
  the detail-composition plot). `analysis.Arthropods` now matches
  `detail.Arthropods` (`#E15759`); nothing else in either scheme used that
  hex, so this was a contained fix local to `taxa_broad_groups.json`. Notebook
  10 uses an older, unrelated flat color mapping and is unaffected.
