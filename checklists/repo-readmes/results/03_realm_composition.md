# Finding 3 — Research attention and assessed driver impact are misaligned across ecosystem realms

## Finding and question

How are the five IPBES direct drivers distributed across biodiversity-loss articles in
different ecosystem realms, and does the distribution follow the realm-specific driver
hierarchy reported by global assessments?

The evidence departs from the assessed hierarchy in the same broad direction across the
three core realms. Pollution receives the largest share of attention in freshwater and
marine evidence, while direct exploitation remains a comparatively small share despite
its assessed importance. Land/sea-use change leads in attention only in terrestrial
evidence.

## Live sources

- Finding notebook: `notebooks/results/03_realm_composition.ipynb`.
- Unreported companion: `notebooks/results/03_unchecked_realm_composition.ipynb`.
- Integrated input:
  `notebooks/data_processing/outputs/04_biodiversity_evidence_corpus_prep/biodiversity_evidence_corpus.parquet`.
- Finding outputs: `notebooks/results/outputs/03_realm_composition/`.
- Companion outputs: `notebooks/results/outputs/03_unchecked_realm_composition/`.
- Manuscript section: *The misalignment between research attention and driver impact is
  consistent across ecosystem realms*.

## Analysis universe

The analysis retains:

- `s2_dir == "negative"`;
- complete publication years 2000–2025; and
- publications carrying exactly one of the 10 configured ecological L4 realm labels.

`Not Applicable`, `All realms`, and publications carrying several distinct realm labels
are excluded. Transition and subterranean labels remain separate categories and are not
redistributed into Terrestrial, Freshwater, or Marine.

Of the 245,168 negative-direction publications in complete years, 232,383 satisfy the
exact-singleton realm rule. The excluded records comprise 11,858 `Not Applicable`, 613
`All realms`, and 314 multi-realm publications.

The core-realm denominators reported in the manuscript figure are:

| Realm | Publications |
| --- | ---: |
| Terrestrial | 114,710 |
| Freshwater | 64,684 |
| Marine | 36,136 |

The remaining exact-singleton publications belong to seven transition or subterranean
categories. The smallest is Subterranean-Marine with 36 publications, so its unreported
estimates are sparse descriptive values.

## Weighting and measures

The unit is one publication. If publication (i) carries (k_i) distinct IPBES L1
drivers, each driver receives weight (1/k_i). Every publication therefore contributes
total weight one within its realm, and the five driver shares sum to 100%.

The main figure reports fractional driver composition for the three core realms. The
trend analysis calculates annual publication-fractional attention to pollution and
direct exploitation. It also measures the share of pollution-tagged publications whose
available title or abstract uses bounded plastics or debris terminology; word boundaries
prevent `plasticity` from matching.

Fractional-binomial logit models estimate fitted 2000 and 2025 endpoints and an odds
ratio per decade. False-discovery-rate adjustment is applied jointly to the nine
realm–outcome tests.

The comparison with assessed driver impact comes from external global assessments cited
in the manuscript. The notebook estimates research composition only; it does not compute
ecological impact or test equality with an impact dataset.

## Manuscript-facing results

### Core-realm driver composition

| Driver | Terrestrial | Freshwater | Marine |
| --- | ---: | ---: | ---: |
| Land/sea-use change | 32.73% | 19.31% | 9.25% |
| Direct exploitation | 10.53% | 6.66% | 24.45% |
| Climate change | 19.09% | 8.70% | 22.95% |
| Pollution | 28.62% | 57.35% | 38.34% |
| Invasive alien species | 9.02% | 7.97% | 5.01% |

Land/sea-use change is the largest component only in terrestrial evidence. Pollution is
the largest component in freshwater and marine evidence. Direct exploitation is
especially low in freshwater evidence and does not lead even in marine evidence, where
external assessments identify it as the leading driver.

### Temporal result

| Outcome | Terrestrial | Freshwater | Marine |
| --- | ---: | ---: | ---: |
| Pollution fitted change, 2000–2025 | −4.13 points | +0.98 points | −0.92 points |
| Direct-exploitation fitted change | −7.01 points | −3.73 points | −15.29 points |
| Plastics within pollution fitted change | +9.37 points | +13.49 points | +26.38 points |

Pollution attention declines significantly in terrestrial evidence but is statistically
flat in freshwater and marine evidence after false-discovery-rate adjustment. Direct
exploitation declines in all three realms. Meanwhile, plastics or debris terminology
rises from approximately 0.1% to 9.5% of terrestrial pollution evidence, 0.0% to 13.5%
in freshwater, and 0.3% to 26.7% in marine evidence.

The plastics wave therefore reflects thematic reallocation within pollution research,
not evidence that pollution's aggregate L1 share increased.

## Figures and outputs

The finding notebook writes:

- `figures/l1_driver_composition_core_realms.pdf` — manuscript Figure 3;
- `figures/pollution_plastics_exploitation_trends_core_realms.pdf` — supplementary
  realm-trends figure;
- `csv/realm_article_counts.csv`;
- `csv/realm_exclusion_audit.csv`;
- `csv/core_realm_driver_composition.csv`;
- `csv/driver_realm_summary.csv`;
- `csv/realm_trend_tests.csv`; and
- `csv/realm_trend_annual.csv`.

The current manuscript source references the two figures as
`checklists/overleaf/main/attachments/realm_composition.pdf` and
`checklists/overleaf/main/attachments/realm_trends.pdf`. Neither attachment is present
in this checkout, so they must be synchronized from the live result outputs before a
local manuscript build.

## Unreported companion material

`03_unchecked_realm_composition.ipynb` reproduces the same realm universe for diagnostic
analyses that support no manuscript sentence:

- L1 driver composition across all 10 exact-singleton realms;
- L1 composition with available directly mapped Threat-L0 detail;
- Threat-L0 location quotients across realms; and
- Threat-L0 fractional composition for all and core realms.

These outputs are retained for checking and exploration. They are not additional
findings and should not be used to expand the manuscript claim without a deliberate
review.

## Interpretation boundaries

- The result describes what is studied, not which driver occurs most often or causes the
  most biodiversity loss.
- External impact rankings provide interpretive context; the notebook does not estimate
  the size or statistical significance of an attention–impact gap.
- Exact transition realms are not reassigned to core realms, and excluded or multi-realm
  publications do not contribute to the denominator.
- Plastics matching measures whether a topic is nameable from title or abstract text, not
  the ecological prevalence of plastic pollution.

## Refresh checklist

Reconcile the 232,383-publication universe from the realm counts and exclusion audit,
verify the five composition rows against `core_realm_driver_composition.csv`, and verify
all fitted changes against `realm_trend_tests.csv`. Keep companion-only values explicitly
labelled as unreported.
