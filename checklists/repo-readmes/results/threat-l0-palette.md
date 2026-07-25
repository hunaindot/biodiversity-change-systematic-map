# IUCN threat L0 palette (colour-blind-optimised)

Canonical colours for the 12 IUCN-CMP threat L0 classes (+ `Unclear`). Use these
**verbatim** for any figure that colours by threat, so every panel in the paper is
consistent. This palette is also mirrored in the Tufte skill preset
(`.claude/skills/tufte-claude-skill/presets/biodiversity.md`).

> **Note:** this is the colour-blind-optimised palette adopted 2026-07-19. It
> **intentionally diverges** from the older categorical palette still in
> `notebooks/results/01-threats.ipynb` (to be reconciled there separately).

## Design: hue families + graded lightness

Twelve hues cannot all be told apart under colour-blindness or in grayscale (~6–8 is the
practical ceiling for categorical colour). So the palette does **not** rely on hue alone.
Threats are grouped into four **hue families**, and within each family every class gets a
distinct **lightness**. Lightness survives colour-blindness, so bands stay separable even
when hue collapses (verified against a deuteranopia simulation: the headline
Pollution↔Climate boundary is dark-blue vs medium-blue and stays clear).

Shades are **hand-tuned in HSL** (not sampled from a sequential colormap, which
desaturates as it lightens and washes out the light end). Two rules keep every band
visible: shades stay **saturated** and within a **mid lightness band** (no near-white),
and the **largest member of each family gets the prominent mid shade** (so Pollution,
Climate, Agriculture, Invasive are all strong — only the thin slivers get the lightest
shades).

| Family (hue) | Meaning | Classes |
| --- | --- | --- |
| **Oranges** | Land-use & development pressures | 1 Residential, 2 Agriculture, 3 Energy, 4 Transport |
| **Greens** | Biotic pressures | 5 Biological resource use, 6 Human intrusions, 8 Invasive species |
| **Blues** | Physical / system pressures | 7 Natural system mod., 9 Pollution, 11 Climate change |
| **Greys** | Residual / uncertain | 10 Geological, 12 Other, U Unclear |

## The colours

| Code | Threat L0 class | Hex | Family | Luminance |
| --- | --- | --- | --- | --- |
| 1 | Residential & Commercial Development | `#B04611` | Oranges | 0.38 |
| 2 | Agriculture & Aquaculture | `#ED7E1D` | Oranges | 0.58 |
| 3 | Energy Production & Mining | `#EEA353` | Oranges | 0.69 |
| 4 | Transportation & Service Corridors | `#F1C183` | Oranges | 0.79 |
| 5 | Biological Resource Use | `#238B49` | Greens | 0.39 |
| 6 | Human Intrusions & Disturbance | `#81CF8C` | Greens | 0.69 |
| 7 | Natural System Modifications | `#87B8D9` | Blues | 0.68 |
| 8 | Invasive & Other Problematic Species, Genes & Diseases | `#4ABF67` | Greens | 0.57 |
| 9 | Pollution | `#1D66AF` | Blues | 0.35 |
| 10 | Geological Events | `#8F8F8F` | Greys | 0.56 |
| 11 | Climate Change & Severe Weather | `#4594D9` | Blues | 0.52 |
| 12 | Other Options | `#A8A8A8` | Greys | 0.66 |
| U | Unclear | `#757575` | Greys | 0.46 |

`Geological Events` has 0 documents in the biodiversity-loss corpus but is kept in the
palette for completeness.

```python
THREAT_L0_COLORS = {
    "Residential & Commercial Development": "#B04611",
    "Agriculture & Aquaculture": "#ED7E1D",
    "Energy Production & Mining": "#EEA353",
    "Transportation & Service Corridors": "#F1C183",
    "Biological Resource Use": "#238B49",
    "Human Intrusions & Disturbance": "#81CF8C",
    "Natural System Modifications": "#87B8D9",
    "Invasive & Other Problematic Species, Genes & Diseases": "#4ABF67",
    "Pollution": "#1D66AF",
    "Geological Events": "#8F8F8F",
    "Climate Change & Severe Weather": "#4594D9",
    "Other Options": "#A8A8A8",
    "Unclear": "#757575",
}
```

## Conventions for threat figures (so colour is never the only channel)

Because hue is redundant under CB, the *structure* carries the information:

- **Stacked composition — order by family, not by raw %:** group bands into their **hue
  families** and stack the family **blocks bottom→top by total share** (Greys / residual,
  incl. `Unclear`, forced to the **top**); **within a family order dark→light**
  (luminance ascending). This yields clean gradient blocks whose every boundary keeps
  lightness contrast (CB-safe), and it puts the largest family (blues: Pollution, Natural
  system mod., Climate) on the flat baseline where magnitude reads most accurately. The
  order is **fixed across all years** (never re-sorted per year, which would destroy
  trend reading). Order the legend **top→bottom to match the visual stack**.
- **Code labels:** stamp each band's IUCN **code** (1–12, `U`) on it where it is widest
  (threshold ≥ 4.5% share), text white/ink by band luminance — a redundant, CB-safe
  identifier.
- **White separators:** draw stacked segments with a thin white edge
  (`edgecolor="#FFFFFF", linewidth=0.4`); the luminance break survives CB/grayscale.
- **Y-axis wording:** shares are over document–threat **attributions** (a doc with *k*
  threats counts once toward each), so label the axis **"Share of threat attributions
  (%)"**, never "% of documents". See the composition tables under
  `notebooks/results/outputs/02-map/threat-composition/`.

Reference implementation: `notebooks/results/02-time-development.ipynb`
(Deliverable 2 figure, `composition-threat-year-stacked`).

## Focused composition-panel variant

When the editorial goal is to foreground one trend rather than present all classes with
equal visual weight, retain the family grouping but use lower-intensity family colours
for context bands. The context shades must remain clearly distinguishable from one
another; do not wash them into near-identical tints. Reserve one saturated,
colour-blind-safe accent for the focal threat. In the temporal-development figure,
Climate change & severe weather uses Okabe-Ito blue (`#0072B2`).

Use a complete labelled legend to identify every band. Do not stamp IUCN codes or other
labels inside the bars. This focused display palette is panel-specific;
`THREAT_L0_COLORS` above remains the canonical identity palette.
