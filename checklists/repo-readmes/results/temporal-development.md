# Temporal development and the integrated evidence corpus

## Shared processing contract

`notebooks/data-processing/04-biodiversity-evidence-corpus-prep.ipynb` creates
`biodiversity-evidence-corpus.parquet`, the shared analytical starting point for
substantive biodiversity results.

The artifact contains exactly 605,199 screening-eligible publications and 57
columns. Its grain is one row per unique, non-missing `UT`. It combines:

- screening and bibliographic fields;
- IPBES direct drivers and Threats L0;
- regions, subregions, countries, locales, and locale coordinates;
- ecosystem realm;
- study design, collection/analysis methods, and comparison fields; and
- broad, analysis, and detail taxa groups plus match/grouping states.

List-valued labels are stored as nested Parquet lists and normalized to tuples
by `BiodiversityEvidenceStore.load`. No direction, year, threat, geography,
realm, study, or taxa filter is applied during preparation. The manifest records
the full column contract, source signatures, direction counts, upstream schema
versions, and taxonomic grouping-rule fingerprint.

## Temporal results

`notebooks/results/02-time-development.ipynb` loads the integrated corpus and
then applies the unchanged temporal estimand:

- `s2_dir == "negative"`;
- complete years 2000–2025 for the primary series;
- a separately labelled partial/projection row for 2026; and
- unique publication counting, with one assignment per distinct publication ×
  Threat-L0 label for composition.

All annual, composition, CAGR, rolling-growth, and geography outputs remain
under `notebooks/results/outputs/02-map/`. The refactor changes only the data
source boundary; it does not alter the analytical filters, denominators,
weighting, tables, or figures.

## Reuse

Future results notebooks should load the corpus through
`data_helpers.prep.evidence_corpus_prep.BiodiversityEvidenceStore`, establish their
one-row-per-UT analytical denominator, and only then explode any multi-label
dimensions needed for attribution analyses.
