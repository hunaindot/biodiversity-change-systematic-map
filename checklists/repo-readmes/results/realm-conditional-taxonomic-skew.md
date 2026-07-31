# Realm-conditioned taxonomic attention

## Question and scope

Does the taxonomic composition of biodiversity-loss research change across
ecological realms? Vector 3 compares all 10 exact-singleton realm labels and
uses Terrestrial, Freshwater, and Marine for the main interpretation.
Transition and subterranean realms remain distinct and are never reassigned to
a component core realm.

The unit is one publication (`UT`). Results describe the composition of
research attention, not ecological abundance, species diversity, conservation
need, or causal realm effects.

## Reproducible implementation

- Data-processing input:
  `notebooks/data-processing/outputs/04-biodiversity-evidence-corpus-prep/biodiversity-evidence-corpus.parquet`.
- Notebook:
  `notebooks/results/13-realm-conditional-taxonomic-skew.ipynb`.
- Analysis helper: `data_helpers/analysis/taxa/realm_conditional.py`.
- Figure helper: `data_helpers/analysis/taxa/realm_conditional_plotting.py`.
- Configuration: `taxa_realm_conditional` and `driver_realm` in
  `checklists/mappings/results_config.json`.
- Taxonomic order and colors:
  `checklists/mappings/taxa_broad_groups.json`.

The results notebook does not reopen or join raw coding outputs. The integrated
loader validates schema, row count, columns, and the unique publication grain;
the notebook additionally checks the semantic taxonomic-rule fingerprint.

## Analytical denominator

The prepared eligible corpus contains 605,199 unique publications. The primary
negative-direction 2000–2025 window contains 245,168 publications. Of these,
232,383 have exactly one configured analysis realm, and 164,296 also carry at
least one resolved biological analysis group. The remaining 12,785 window
records fail the exact-singleton realm rule, while 68,087 exact-realm records
have no resolved biological analysis group.

The core-realm resolved denominator is 154,529 publications:

| Realm | Resolved / exact-realm publications | Resolution |
| --- | ---: | ---: |
| Terrestrial | 85,205 / 114,710 | 74.3% |
| Freshwater | 42,605 / 64,684 | 65.9% |
| Marine | 26,719 / 36,136 | 73.9% |

Resolution is reported before composition because the estimates are
conditional on at least one resolved taxon.

## Estimands

For a publication with (g_i) resolved groups, every group receives
(1/g_i) within its exact realm. Every included publication therefore
contributes total weight one. Realm specialization is:

\[
\log_2 LQ_{gr}=\log_2\left[\frac{p(g\mid r)}{p(g)}\right].
\]

The all-taxa estimand describes the complete resolved composition. The
animal-only estimand first restricts to papers carrying Vertebrates,
Arthropods, or Other invertebrates and then renormalizes only over those
groups. The latter prevents terrestrial plant attention from mechanically
diluting the animal allocation.

Whole-publication label patterns are resampled independently within realms for
1,000 multinomial bootstrap replicates with seed 20260731. Planned contrasts
are differences in conditional attention share, in percentage points.

## Primary result

All resolved taxonomic attention differs sharply across the three core realms:

| Group | Terrestrial | Freshwater | Marine |
| --- | ---: | ---: | ---: |
| Vertebrates | 24.7% | 49.9% | 40.1% |
| Arthropods | 10.0% | 13.6% | 11.2% |
| Other invertebrates | 3.1% | 6.2% | 31.7% |
| Vascular plants | 45.0% | 10.4% | 1.9% |

The all-taxa marine vertebrate share is 15.44 points above terrestrial
(95% bootstrap CI +14.86 to +16.12), primarily because terrestrial evidence is
plant-heavy. The animal-only comparison reverses the interpretation: marine
vertebrate attention is 47.6%, 14.36 points below terrestrial (95% CI −15.21
to −13.59) and 22.96 points below freshwater (95% CI −23.81 to −22.20).

At detail resolution, freshwater animal attention is 55.8% fishes. Marine
animal attention is 17.8% molluscs and 21.0% other invertebrates. Freshwater
fishes exceed marine fishes by 24.06 points (95% CI +23.23 to +24.84), and
marine molluscs exceed terrestrial molluscs by 16.89 points (95% CI +16.38 to
+17.37).

The class supplement makes ecological signatures more nameable without
changing the grain. `Anthozoa` occurs in 2,359 marine publications (8.83%), one
freshwater publication, and no terrestrial publication in the resolved primary
set.

## Robustness and interpretation

Vascular-plant dominance in terrestrial evidence, fish dominance in
freshwater evidence, and mollusc/other-invertebrate prominence in marine
evidence remain visible inside every IPBES direct-driver stratum. This does not
identify a causal realm effect, but it shows that the descriptive result is not
only the consequence of different driver mixtures.

The consolidated sensitivity table compares fractional weighting with full
counting, single-group publications, negative plus mixed directions, all
directions, and observational studies only. The observational restriction has
the largest cell-level change (10.40 points), so study-design composition
remains an explicit limitation.

## Outputs

All artifacts are written under:

`notebooks/results/outputs/13-realm-conditional-taxonomic-skew/`

The lean table bundle contains:

- denominator and taxonomic-resolution audits;
- all analysis/detail and all-taxa/animal-only composition estimates;
- six planned bootstrap contrasts;
- driver-stratified composition estimates;
- prespecified class-signature coverage;
- one consolidated sensitivity table; and
- a compact provenance manifest.

Six vector PDFs report realm resolution, core all-taxa composition, the
all-realm specialization heatmap, the two-resolution animal lens, class
signatures, and driver-stratified realm signatures. No publication-level CSV or
duplicate parquet is written by the results notebook.
