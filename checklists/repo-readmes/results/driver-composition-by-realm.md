# Driver distributions and Threat-L0 research emphasis across ecosystem realms

## Question

How do IPBES L1 driver distributions and top-level IUCN-CMP threat emphasis vary
across the complete ecological-realm taxonomy?

This is a descriptive evidence-composition result. It does not estimate ecological
occurrence, severity, causal impact, or the fraction of biodiversity loss attributable
to a threat.

## Analysis universe

- Input: `data_helpers.corpus.build_merged_corpus()`.
- Unit: one unique publication (`UT`).
- Direction: `s2_dir == "negative"`.
- Complete publication years: 2000–2025.
- Realm rule: exactly one of the 10 ecological labels in the L4 coding schema.
- Exclusions: `Not Applicable`, `All realms`, empty/unknown outputs, and publications
  carrying multiple distinct realm labels.
- Driver labels: the five IPBES L1 direct drivers attached to each publication.
- Threat labels: the 12 in-scope Threat-L0 labels attached to the same publication
  universe. `Geological Events` is excluded because it was outside this map's coding
  scope.

The 10 mutually exclusive analysis labels are Terrestrial, Subterranean,
Subterranean-Freshwater, Subterranean-Marine, Freshwater-Terrestrial, Freshwater,
Freshwater-Marine, Marine, Marine-Terrestrial, and
Marine-Freshwater-Terrestrial. Transition categories are not redistributed into their
component realms.

Terrestrial, Freshwater, and Marine are marked in configuration as the three core
realms. The core-realm bar figure is a subset of the full 10-realm universe, not a
separate analysis.

## Measures

For realm \(r\) and label \(d\), document prevalence is:

\[
p_{rd} =
\frac{\#\{\text{publications in }r\text{ carrying }d\}}
     {\#\{\text{publications in }r\}}.
\]

Because labels are multi-label, prevalence does not sum to 100%.

Relative research emphasis is the location quotient:

\[
LQ_{rd} = \frac{p_{rd}}{p_{\cdot d}},
\]

where \(p_{\cdot d}\) is prevalence pooled across all 10 ecological realm categories.
An LQ above one means the label is more prevalent in that realm than in the pooled
evidence base.

The composition bars use a publication-weighted rule. For the L1 view, a publication
carrying \(k\) drivers contributes weight \(1/k\) to each driver. For the Threat-L0
view, the same rule is applied after restricting to the 10 substantive classes shown
in the figures. Publications carrying only `Other Options` or `Unclear` do not enter
the Threat-L0 composition denominator.

The nested core-realm view is conditional within each L1 driver. For a given
realm–driver block, it retains only publications carrying at least one directly mapped
substantive Threat-L0 label. Missing predictions, `Unclear`, `Other Options`,
Geological Events, and threats unrelated to that driver are excluded from this
conditional denominator. A publication carrying \(m\) related threats contributes
weight \(1/m\) to each. The thin strip therefore sums to 100% within the available
mapped labels; its mapped publication count and coverage are reported separately.

The pollution-nameability test uses the same core-realm publication universe and
complete years. Pollution and direct-exploitation attention are annual means of the
publication-fractional L1 weights. The plastics subset is the fraction of
pollution-tagged publications with available title/abstract text matching a
case-insensitive bounded vocabulary for plastics, microplastics, nanoplastics, plastic
debris/waste/litter/particles/fibres/pellets/fragments/pollution, or marine and
anthropogenic debris/litter. The word boundaries exclude `plasticity`.

Fractional-binomial logit models estimate the 2000 and 2025 fitted endpoints and odds
ratio per decade. False-discovery-rate adjustment is applied jointly to the nine
realm–outcome trend tests.

## Figures

Notebook 09 saves seven PDF figures:

1. L1 horizontal fractional-composition bars for all 10 realms.
2. L1 horizontal fractional-composition bars for the three core realms.
3. Nested L1 composition with available mapped Threat-L0 detail for the three core
   realms.
4. Pollution attention, plastics-within-pollution, and direct-exploitation annual
   trends for the three core realms.
5. Threat-L0 location-quotient heatmap for all 10 realms.
6. Threat-L0 horizontal fractional-composition bars for all 10 realms.
7. Threat-L0 horizontal fractional-composition bars for the three core realms.

The core-realm bar figure prints rounded percentages inside segments at least 6
percentage points wide. Narrower segments remain identifiable through the shared legend
without forcing overlapping text.

The heatmaps use color as the sole cell encoding. They do not repeat publication
percentages inside cells. Purple indicates prevalence below the pooled rate, white
indicates parity, and green indicates prevalence above the pooled rate.

Threat rows follow notebook 02's family-grouped stack order. A narrow strip beside
each row uses notebook 02's configured Threat-L0 color, while the heatmap cells remain
reserved for the location quotient.

The figures follow notebook 02's publication grammar: 7.4-inch width, clean sans-serif
type, zero-based bar axes, no grid, neutral 0.6-point axis rules, white separators, and
the shared colorblind-safe category palettes.

## Current descriptive result

The L1 fractional composition differs clearly across the core realms. Land/sea-use
change carries a larger share in Terrestrial evidence (33%) than in Freshwater (19%)
or Marine evidence (9%). Freshwater is dominated by pollution (57%), while Marine
assigns larger shares to direct exploitation (24%) and climate change (23%).

Within Land/sea-use publications carrying an available directly mapped Threat-L0
label, Terrestrial evidence is agriculture-heavy (52%). Freshwater evidence is
dominated by natural-system modification (46%), while Marine evidence is more evenly
distributed across natural-system modification (31%), agriculture/aquaculture (29%),
and residential/commercial development (25%). Mapped Land/sea-use coverage is 74% in
Terrestrial, 82% in Freshwater, and 52% in Marine evidence.

The plastics-topic wave does not coincide with rising aggregate pollution attention.
Fitted pollution attention falls from 31.5% to 27.4% in Terrestrial evidence and is
statistically flat in Freshwater and Marine evidence. Plastics/debris terminology
nevertheless rises from approximately 0.1% to 9.5% within Terrestrial pollution
evidence, 0.0% to 13.5% in Freshwater, and 0.3% to 26.7% in Marine evidence.
Direct-exploitation attention declines by 7.0, 3.7, and 15.3 percentage points,
respectively. This supports thematic reallocation within pollution, not the stronger
claim that the plastics wave increased pollution's overall L1 share.

The primary universe contains 232,383 publications. Relative to the pooled 10-realm
evidence base, the Threat-L0 map emphasizes agriculture in Terrestrial evidence, pollution
and natural-system modification in Freshwater evidence, and biological resource use
plus climate change and severe weather in Marine evidence.

The transition categories remain distinct and often show mixed profiles, including
pollution emphasis in Freshwater-Marine. The composition bars provide the complementary
absolute mix. Freshwater is
markedly pollution-heavy, Marine assigns larger shares to climate change and
biological resource use, and Terrestrial has a larger agriculture component.

Subterranean-Marine contains only 36 publications and is marked with a dagger. Its
color should be read as a sparse descriptive estimate.

## Literature context

- Sayer et al. (2025), threat prevalence among freshwater fauna:
  <https://doi.org/10.1038/s41586-024-08375-z>
