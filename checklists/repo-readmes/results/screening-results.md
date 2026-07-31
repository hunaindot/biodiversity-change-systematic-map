# Screening results preparation and analysis

## Grain separation

The screening workflow has two explicit grains:

- all 2,414,191 screened records, one row per non-missing unique `UT`; and
- all 605,199 screening-eligible records, also one row per `UT`.

`notebooks/data-processing/03-screening-analysis-prep.ipynb` reads the 5.3 GB
consolidated screening CSV once. It writes a compact complete-screening Parquet,
the 15-row exclusion-intersection table, and a manifest containing eligibility,
unclear-step, direction, source-column, and row-reconciliation audits.

The notebook also creates an eligible bibliographic/screening build cache used
by the integrated-corpus notebook. That cache is removed after successful
integration unless `retain_eligible_build_cache` is enabled.

## Results notebook

`notebooks/results/00-screening-results.ipynb` loads only the preparation
manifest and exclusion-overlap table. It does not load either record-level
Parquet or the raw screening CSV.

The established counts remain:

- 605,199 eligible and 1,808,992 not eligible;
- 121,707 eligible records with at least one unclear screening step;
- 253,081 eligible negative-direction records; and
- 352,118 eligible positive, mixed, unclear, or missing-direction records.

Its only result artifact remains
`notebooks/results/outputs/00-screening/screening-criteria-overlap.pdf`.

## Durable preparation outputs

Under `notebooks/data-processing/outputs/03-screening-analysis-prep/`:

- `screening-publications.parquet` — complete compact screening grain;
- `screening-exclusion-overlap.csv` — figure-supporting intersection table;
- `manifest.json` — summary, direction, source, grain, and cache provenance.

No screening result CSV duplicates these processing outputs.
