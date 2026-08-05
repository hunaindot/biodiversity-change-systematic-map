# Finding 1 — Scientific evidence on biodiversity loss is extensive and rapidly expanding

## Finding and question

How fast has the scientific evidence base on biodiversity loss grown since 2000, and
how has its composition across broad IUCN threat categories changed?

Screening identified 253,081 scientific articles reporting negative biodiversity
impacts. Across the complete publication years used for temporal analysis, annual output
rose from 2,530 articles in 2000 to 20,520 in 2025, an 8.73% compound annual growth rate.
Climate change and severe weather grew fastest among the broad threat categories, while
pollution remained the largest category but declined as a share of all threat
attributions.

## Live sources

- Screening audit: `notebooks/results/00_screening.ipynb`.
- Finding notebook: `notebooks/results/01_evidence_growth.ipynb`.
- Integrated input:
  `notebooks/data_processing/outputs/04_biodiversity_evidence_corpus_prep/biodiversity_evidence_corpus.parquet`.
- Result outputs: `notebooks/results/outputs/01_evidence_growth/`.
- Manuscript section: *Scientific evidence on biodiversity loss is extensive and rapidly
  expanding*.

## Analysis universe

The screening preparation contains 2,414,191 unique, non-missing publication identifiers
(`UT`). Screening classified 605,199 records as eligible and 1,808,992 as not eligible.
Among the eligible records, 253,081 report a negative biodiversity impact; the remaining
352,118 have a positive, mixed, unclear, or missing direction and do not enter the
loss-focused results. Of the eligible records, 121,707 were assumed eligible despite at
least one unclear screening step.

The temporal analysis then retains:

- `s2_dir == "negative"`;
- complete publication years 2000–2025; and
- one row per unique publication before any threat labels are expanded.

This gives 245,168 publications. A further 7,913 negative-direction records fall outside
the complete-year window or have no usable year. All 245,168 in-window publications have
at least one usable Threat-L0 label.

The configured partial year is 2026, but it is excluded from the finding, its figure, and
the live exported annual table. The manuscript result is exclusively a complete-year
2000–2025 comparison.

## Counting and composition

Annual publication volume counts unique `UT` values. Threat composition first reduces
the data to one distinct publication × year × Threat-L0 assignment. A publication
carrying several threats therefore contributes once to each distinct threat it names.
The annual composition denominator is the number of document–threat assignments, not the
number of publications, and annual shares sum to 100% across threat categories.

The complete-year table contains 315,636 unique document–threat assignments across 12
observed threat classes. `Other Options` and `Unclear` remain in composition and growth
tables but are omitted from the category lines in the rolling-growth panel.

## Manuscript-facing results

| Measure | 2000 | 2025 | Change or growth |
| --- | ---: | ---: | ---: |
| Annual biodiversity-loss publications | 2,530 | 20,520 | 8.73% CAGR |
| Climate change & severe weather share | 5.30% | 19.28% | +13.98 points |
| Pollution share | 36.31% | 28.57% | −7.74 points |

Climate change and severe weather publications grew at 14.75% annually over 2000–2025.
Pollution remained the largest single Threat-L0 category throughout the period even as
its share of the expanding evidence base declined.

These values support the manuscript's three-panel argument: rapid growth in publication
volume, changing threat composition, and category-specific rolling growth. Policy and
assessment milestones are plotted only as temporal context and are not treated as causal
interventions.

## Figures and outputs

The live manuscript-supporting figure is:

- `figures/combined_time_development.pdf` — annual volume, annual threat composition,
  and rolling five-year CAGR.

The current manuscript source references this figure as
`checklists/overleaf/main/attachments/combined-time-development.pdf`. That attachment is
not present in this checkout, so it must be synchronized from the live result output
before a local manuscript build.

Reported tables are:

- `csv/evidence_audit.csv`;
- `csv/annual_publication_counts.csv`;
- `csv/threat_year_shares.csv`;
- `csv/threat_cagr_by_period.csv`; and
- `csv/rolling_five_year_cagr.csv`.

The country-level total and per-threat choropleths and their three supporting CSVs are
unreported diagnostics. They count where the literature is geolocated; they neither map
where threats occur nor support a geographic claim in Finding 1.

The screening notebook writes one result artifact:
`notebooks/results/outputs/00_screening/screening_criteria_overlap.pdf`. Its underlying
overlap and audit tables remain preparation outputs under
`notebooks/data_processing/outputs/03_screening_analysis_prep/` rather than being
duplicated in the result directory.

## Interpretation boundaries

- Publication counts measure the size of the indexed evidence base, not the amount or
  severity of biodiversity loss.
- Threat shares describe the distribution of scientific attention among coded
  attributions. They do not estimate each threat's contribution to biodiversity loss.
- WoS coverage, indexing practices, and the search strategy can influence temporal
  growth; plotted policy milestones do not identify their effects.
- The incomplete 2026 publication year must not be compared with complete annual counts.

## Refresh checklist

Verify the screening counts against the preparation manifest, the 245,168 denominator
against `evidence_audit.csv`, endpoint values against the annual and threat-share tables,
and the figure filename against the live output directory. Confirm that the manuscript
still reports complete years 2000–2025 before changing the time window here.
