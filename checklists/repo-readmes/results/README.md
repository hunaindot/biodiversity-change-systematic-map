# Results documentation

This directory documents the four findings reported in the manuscript. Each finding has
one live results notebook and one matching document here.

| Finding | Results notebook | Primary figure | Documentation |
| --- | --- | --- | --- |
| 1. Evidence growth | `notebooks/results/01_evidence_growth.ipynb` | `combined_time_development.pdf` | `01_evidence_growth.md` |
| 2. Income composition | `notebooks/results/02_income_composition.ipynb` | `income_composition.pdf` | `02_income_composition.md` |
| 3. Realm composition | `notebooks/results/03_realm_composition.ipynb` | `l1_driver_composition_core_realms.pdf` | `03_realm_composition.md` |
| 4. Taxonomic lens | `notebooks/results/04_taxonomic_lens.ipynb` | `04_taxonomic_and_geographic_gap.pdf` | `04_taxonomic_lens.md` |

## Supporting analysis

| Analysis | Results notebook | Primary figure | Documentation |
| --- | --- | --- | --- |
| Complete IPBES geography attention and coverage | `notebooks/results/05_geography_attention.ipynb` | `geography_attention_hierarchy_reference.pdf` | `05_geography_attention.md` |

Result 05 is a live exploratory diagnostic, not a fifth manuscript finding. It is kept
separate because it extends the geographic evidence-volume analysis to every IPBES
mapping leaf, including low, zero-captured, and currently unresolvable places.

`notebooks/results/00_screening.ipynb` supplies the screening audit used to introduce
Finding 1. It is not a fifth substantive finding. Similarly,
`03_unchecked_realm_composition.ipynb` and `threats_supplementary.ipynb` contain useful
diagnostics, but no result is promoted from them unless a finding document explicitly
labels it as supporting or unreported material.

## Source hierarchy

When sources differ, use this order:

1. Executed tables and manifests under `notebooks/results/outputs/` for numerical values.
2. Live notebook code for filters, denominators, weighting, and estimators.
3. The current `checklists/overleaf/main/main-*.tex` manuscript for which claims are
   reported and how figures are presented.
4. Unchecked and archived notebooks only for material explicitly identified as
   diagnostic or historical.

Archived notebooks under `notebooks/results/archive/` do not define current findings.
Their design history remains recoverable from the notebooks, archived outputs, and Git;
it is intentionally not duplicated in this directory.

## Shared rules

- The analytical unit is a unique publication (`UT`) unless a finding explicitly states
  a publication–country or publication–label attribution grain.
- Multi-label dimensions are exploded only after establishing the publication
  denominator. Weighting rules are stated in each finding document.
- Reported percentages describe scientific attention in the mapped evidence, not the
  ecological occurrence, severity, or causal importance of a driver, threat, realm, or
  taxonomic group.
- Threat-L0 labels, display colors, codes, families, and stack order must be loaded from
  `checklists/mappings/results_config.json` through `data_helpers/results_config.py`;
  do not copy a local palette into a new result. The supplementary threats notebook
  retains an older local map palette as a documented exception.
- Supporting taxonomic and geographic method notes that are not findings live under
  `checklists/repo-readmes/others/`.

## Refreshing these documents

After rerunning a result, verify the document against the exported CSVs and manifest,
confirm that every named artifact exists, and compare the manuscript-facing claim with
the latest `main-*.tex`. Do not copy values from notebook prose when the executed output
or exported table differs.
