# Geographic research specialization (log2 location quotient)

Shared metric note for geographic and realm specialization diagnostics.
This is supplementary methodology, not one of the four main findings.

The current geographic implementation is
`notebooks/results/threats_supplementary.ipynb`; its metric helper is parked at
`data_helpers/analysis/parked/geography.py`. The exact same research-emphasis
interpretation also applies when the metric is used for threat-by-realm
comparisons in `notebooks/results/03_unchecked_realm_composition.ipynb`.

## Question and estimand

For each place and threat, the metric asks whether that place's literature
studies the threat more or less often than the analytic corpus does on average.
It measures **relative research emphasis**, not the geographic occurrence or
severity of the threat.

For place `c` and threat `t`:

```text
LQ(c,t) = (n[c,t] / D[c]) / (T[t] / D)
```

where every term counts unique documents:

- `n[c,t]`: documents about threat `t` in place `c`;
- `D[c]`: documents in place `c`;
- `T[t]`: documents about threat `t` in the analytic universe; and
- `D`: documents in that same universe.

The plotted scale is `log2(LQ)`: 0 is the corpus average, +1 is twice the
average emphasis, and -1 is half the average emphasis.

A document naming multiple places counts once in each relevant place, never
once per mention within a place. A document may also carry multiple threats, so
shares across threats need not sum to 100%. LQ remains a descriptive ratio of
within-place to corpus-wide document shares.

## Geographic universe and coverage

The supplementary geography notebook uses documents that are all:

1. negative-impact;
2. observational;
3. geolocatable through the ISO3-to-IPBES crosswalk; and
4. assigned at least one Threat-L0 label.

The executed universe is 97,926 unique documents. Non-mappable tokens such as
not-applicable, unclear, all-countries, or invalid ISO3 values are excluded and
audited. Country and subregion results derive from the same `pred_countries`
signal.

Countries require `D[c] >= 100`; 108 of 237 countries meet that support rule.
The output contains 17 displayed IPBES subregions after Antarctica is omitted
from the mapped extent.

## Empirical-Bayes stabilization

The maps display a fixed-strength, Beta-prior shrinkage estimate with
`kappa = 30`:

```text
LQ_EB(c,t) = (n[c,t] + kappa * pi[t]) /
             ((D[c] + kappa) * pi[t])

pi[t] = T[t] / D
```

This pulls low-support cells toward LQ = 1 while leaving large cells almost
unchanged. The support cutoff decides which countries appear; shrinkage
stabilizes the displayed cells. Exports retain raw `lq` and `log2_lq` alongside
`lq_eb` and `log2_lq_eb`.

## Map convention

- Small-multiple choropleths use PRGn: purple below the corpus average, green
  above it, and white at zero.
- The scale is symmetric and clipped at `log2(LQ_EB) = +/-2`, corresponding to
  one-quarter through four times the average emphasis.
- Places below the support threshold or without data are cross-hatched on a
  light base, not assigned a low value.
- Reader-facing text should say "research specialization" or "relative
  research emphasis" and state explicitly that the map does not show threat
  occurrence or severity.

The live notebook writes geographic PDFs and CSVs under
`notebooks/results/outputs/threats_supplementary/geography/`. Its
`save_figure_result` routine is notebook-local; it is not a shared helper.

## Statistical boundary

Do not attach chi-square p-values to this multi-label table. Documents may
contribute to several threats and places, so cells are correlated and the table
is not additive in the way a standard contingency-table test assumes. If an
inferential extension is needed, use a document-level resampling or permutation
procedure that preserves the multi-label structure.
