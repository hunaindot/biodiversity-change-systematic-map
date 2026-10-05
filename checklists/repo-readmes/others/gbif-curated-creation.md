# Creation and meaning of the curated GBIF taxonomy

## Purpose

`data/gbif/curated/gbif_curated.csv` is an enriched copy of a fixed
GBIF Backbone Taxonomy snapshot (Not available in git & OSF repo atm. will be added). It combines the backbone's taxonomic name and
classification table with vernacular names, free-text descriptions, and a
subset of species-profile attributes retrieved from the GBIF Species API.

The curated file is a fixed project artifact rather than a current view of GBIF
taxonomy. It preserves the 28 August 2023 classification.

## Example records

The examples below show selected columns from the curated CSV. Empty fields and
long description text are omitted for readability.

An accepted kingdom record contains its canonical name, status, classification,
and aggregated vernacular names:

```yaml
taxonID: 6
scientificName: Plantae
canonicalName: Plantae
taxonRank: kingdom
taxonomicStatus: accepted
kingdom: Plantae
vernaculars_named: Plant (en), Plants (en), planten (nl), 植物界 (ja), ...
```

An accepted genus record carries its complete available lineage:

```yaml
taxonID: 2877951
scientificName: Quercus L.
canonicalName: Quercus
taxonRank: genus
taxonomicStatus: accepted
kingdom: Plantae
phylum: Tracheophyta
class: Magnoliopsida
order: Fagales
family: Fagaceae
genus: Quercus
vernaculars_named: Acorn (en), Oak (en), Oaks (en), Eiche (de), ...
```

An accepted species record can additionally contain attributes and source
provenance returned by the GBIF Species API:

```yaml
taxonID: 4311678
scientificName: Tisea grandis Forest & Morgan, 1991
canonicalName: Tisea grandis
taxonRank: species
taxonomicStatus: accepted
kingdom: Animalia
phylum: Arthropoda
class: Malacostraca
order: Decapoda
family: Diogenidae
genus: Tisea
species_id: 4311678
marine_curated: true
source: [World Register of Marine Species, Catalogue of Life]
```

The full CSV also includes synonym links, authorship, nomenclatural information,
typed descriptions, and the other optional species-profile fields documented
below.

## Source snapshot

The source is the **GBIF Backbone Taxonomy** Darwin Core Archive:

| Property | Value |
| --- | --- |
| Dataset | GBIF Backbone Taxonomy |
| Snapshot timestamp | 2023-08-28 13:45:33 UTC |
| DOI | [10.15468/39omei](https://doi.org/10.15468/39omei) |
| Archive location advertised by GBIF | `https://hosted-datasets.gbif.org/datasets/backbone/` |

In the raw data extract, `eml.xml` records the dataset-level citation, snapshot
date, license, and provenance. `meta.xml` defines the archive layout and the
mapping between file columns and Darwin Core terms.

The relevant archive tables are:

| File | Role in the curation process |
| --- | --- |
| `Taxon.tsv` | Core name usage, status, and fixed-rank classification |
| `VernacularName.tsv` | Common names associated with a core `taxonID` |
| `Description.tsv` | Typed descriptions associated with a core `taxonID` |
| `eml.xml` | Snapshot-level provenance and citation |
| `meta.xml` | Darwin Core Archive schema and field definitions |

Other raw archive extensions, including distributions, references, multimedia,
and type specimens, are not represented as dedicated columns in
`gbif_curated.csv`.

## Transformation

```text
GBIF Backbone Darwin Core Archive (28 August 2023)
├── Taxon.tsv ───────────────────────────────┐
├── VernacularName.tsv ── aggregate by ID ──┤
├── Description.tsv ───── aggregate by ID ──┤
└── eml.xml + meta.xml (provenance/schema)   │
                                              ├─> gbif_curated.csv
GBIF Species API                              │
└── /v1/species/{usageKey}/speciesProfiles ──┘
```

### 1. Load the core taxonomy

`Taxon.tsv` contains 7,746,724 data records and 7,746,724 unique `taxonID`
values. Its 23 fields form the first 23 named columns of the curated CSV:

```text
taxonID, datasetID, parentNameUsageID, acceptedNameUsageID,
originalNameUsageID, scientificName, scientificNameAuthorship,
canonicalName, genericName, specificEpithet, infraspecificEpithet,
taxonRank, nameAccordingTo, namePublishedIn, taxonomicStatus,
nomenclaturalStatus, taxonRemarks, kingdom, phylum, class, order,
family, genus
```

The TSV is read as UTF-8 with a tab delimiter, no CSV quote processing, and the
field names defined in `meta.xml` (`quoting=csv.QUOTE_NONE`). See the known-loss
section below.

### 2. Aggregate vernacular names

Records from `VernacularName.tsv` are grouped by `taxonID` and combined into
`vernaculars_named`. Values include the vernacular name followed by its language
code, for example `Plant (en)`, and multiple values are joined into one string.
The output can contain repeated names.

`vernaculars_named` is non-empty for 222,092 curated taxa (2.89%).

### 3. Aggregate descriptions

Records from `Description.tsv` are grouped by `taxonID`. Each description is
prefixed with its Darwin Core description type and the values are joined with
newlines, producing content such as:

```text
description: ...
discussion: ...
type_taxon: ...
```

The combined value was stored in `curated_description`. It is non-empty for
545,413 curated taxa (7.09%). Some values are very large and contain embedded
newlines, so the curated file must be read with a real CSV parser; physical line
counts from `wc -l` are not record counts.

### 4. Add GBIF species profiles

Species-profile attributes come from the GBIF Species API endpoint:

```text
GET https://api.gbif.org/v1/species/{usageKey}/speciesProfiles
```

The endpoint is queried with the GBIF `taxonID`/usage key from the backbone.
GBIF returns zero, one, or several profiles because profile information can be
contributed by multiple source checklists. The returned profiles are
consolidated by usage key and left-joined to the taxonomy, preserving one
curated row per retained backbone name usage. Taxa without a returned profile
remain in the curated table with empty profile fields.

When several profiles exist, `results` retains the complete result list, while
fields such as `source` and `sourceTaxonKey` contain parallel lists. The
following API values are added to the curated taxonomy:

| Species-profile field | Curated column | Non-empty curated rows |
| --- | --- | ---: |
| queried usage key | `species_id` | 879,087 |
| complete profile-result list | `results` | 879,087 |
| `livingPeriod` | `livingPeriod_curated` | 49,787 |
| `lifeForm` | `lifeForm_curated` | 37,691 |
| `habitat` | `habitat_curated` | 25,130 |
| `marine` | `marine_curated` | 117,264 |
| `freshwater` | `freshwater_curated` | 30,142 |
| `terrestrial` | `terrestrial_curated` | 168,945 |
| `extinct` | `extinct_curated` | 91,538 |
| `hybrid` | `hybrid_curated` | 135 |
| `source` | `source` | 879,087 |
| `sourceTaxonKey` | `sourceTaxonKey` | 879,087 |

The output also contains `ageInDays_curated`, `sizeInMillimeter_curated`, and
`massInGram_curated`, but all three are empty and are not populated by the
retained species-profile responses.

### 5. Export the curated CSV

The final file contains 7,694,321 parsed records and the same number of unique
`taxonID` values. No taxon IDs occur in the curated file that are absent from
the raw core. In addition to the 23 core columns and the enrichment columns,
the CSV has one unnamed column. It is empty except in one malformed record and
is a parsing/export artifact rather than a data field.

## What one curated row represents

A row represents one GBIF **name usage** from the fixed 2023 backbone, not
necessarily an accepted biological species. The file includes accepted names,
synonyms, doubtful usages, ranks above and below species, and unranked records.
Therefore:

- `taxonID` identifies the backbone name usage;
- `taxonomicStatus` determines whether it is accepted, doubtful, or a synonym;
- `acceptedNameUsageID` links a synonym to an accepted usage when supplied;
- the rank columns describe the 2023 backbone classification;
- vernaculars and descriptions are optional archive extensions;
- species-profile fields are optional attributes contributed by underlying
  checklist sources and retrieved later through the API.

The file is not an occurrence dataset, a complete species inventory, or a table
containing only accepted species. Downstream described-diversity analyses apply
their own explicit filter: case-insensitive `taxonRank == "species"` and
`taxonomicStatus == "accepted"`.

## Known loss during conversion

The raw-to-curated reconciliation is:

| Metric | Records |
| --- | ---: |
| Raw `Taxon.tsv` | 7,746,724 |
| Curated CSV | 7,694,321 |
| Raw IDs absent from curated | 52,403 (0.676%) |
| IDs added by curation | 0 |

The 52,403 absent rows are treated as malformed records lost during parsing,
not as an intentional biological filter. They occur in contiguous blocks,
consistent with quote-aware CSV parsing consuming several tab-separated records
after encountering an unclosed literal quote. The archive declares no field
enclosure character. Rebuilding therefore uses `quoting=csv.QUOTE_NONE` and
verifies that all 7,746,724 unique core IDs survive before enrichment.

The sources contributing the most absent records are:

| Source dataset | Dataset UUID | Absent rows |
| --- | --- | ---: |
| Catalogue of Life Checklist | `7ddf754f-d193-4cc9-b351-99906754a03b` | 31,064 |
| iBOL Barcode Index Numbers | `4cec8fef-f129-4966-89b7-4f8439aba058` | 6,531 |
| UNITE fungal species hypotheses | `61a5f178-b5fb-4484-b6d8-9b129739e59d` | 2,537 |
| Paleobiology Database | `c33ce2f2-c3cc-43a5-a380-fe4526d63650` | 1,870 |
| World Register of Marine Species | `2d59e5db-57ad-41ff-97d6-11f5fb264527` | 1,310 |
| World Checklist of Vascular Plants | `f382f0ce-323a-4091-bb9f-add557f3a9a2` | 874 |
| TAXREF | `0e61f8fe-7d25-4f81-ada7-d970bbb2c6d6` | 797 |

These counts do not indicate that those datasets were deliberately excluded.
Catalogue of Life alone supplies 4,766,428 of the raw backbone's names; its
31,064 absent rows correspond to a 0.652% loss rate, similar to the overall
0.676% rate.

The absent records include 33,291 species-rank usages and 27,924 accepted
usages. Analyses requiring the complete backbone use `Taxon.tsv`; the curated
file is not lossless.

## Downstream canonical-name lookup cache

`checklists/mappings/gbif_lookup_cache.pkl` is built directly from
`data/gbif/curated/gbif_curated.csv`. It is a compact lookup used by the
taxa evaluation workflow; it is not another source of GBIF data and it does not
add taxa that are absent from the curated CSV.

Build it with:

```bash
python -m data_helpers.sources.build_gbif
```

The paths and build settings are defined under `dataset_config.gbif` in
`checklists/mappings/repo_config.json`:

```json
{
  "source": "data/gbif/curated/gbif_curated.csv",
  "cache": "checklists/mappings/gbif_lookup_cache.pkl",
  "chunksize": 200000,
  "taxonomic_columns": ["kingdom", "phylum", "class", "order", "genus"]
}
```

`data_helpers/sources/build_gbif.py` streams the curated CSV in chunks and reads
only `canonicalName`, `taxonomicStatus`, `kingdom`, `phylum`, `class`, `order`,
and `genus`. Vernacular names, descriptions, species-profile attributes, and
the other curated columns do not affect this cache.

For each usable row, the builder:

1. removes rows whose `canonicalName` is missing;
2. strips and lowercases the canonical name to form the dictionary key;
3. removes rows whose five stored lineage fields are all missing;
4. keeps the first occurrence of each normalized name within the accepted and
   non-accepted groups; and
5. overlays accepted records on the fallback records, so an accepted usage has
   priority over a non-accepted usage with the same normalized name.

The serialized Python dictionary has this shape:

```python
{
    "felis catus": {
        "kingdom": "Animalia",
        "phylum": "Chordata",
        "class": "Mammalia",
        "order": "Carnivora",
        "genus": "Felis",
    }
}
```

The artifact contains 5,879,221 normalized canonical-name entries.

Because the builder uses the curated CSV, the cache inherits its known parsing
losses. A missing `taxonID` does not necessarily remove a lookup entry, since a
different retained row can have the same normalized canonical name. It matters
when no retained row supplies that name, or when the missing row would have
provided the preferred accepted lineage. Names with several accepted rows are
also resolved by input order: the first accepted occurrence wins.

### Use in taxa evaluation

`evals_local/loaders.py` loads this pickle lazily when evaluating the `taxa`
task. For every LLM-produced pair of `taxon_rank` and `canonical_name`, it adds
the canonical name to the prediction column for the stated rank and uses the
cache to fill the other available lineage levels. For example:

```json
{"taxon_rank": "species", "canonical_name": "Felis catus"}
```

is expanded to the equivalent of:

```text
pred_species = ["Felis catus"]
pred_genus   = ["Felis"]
pred_order   = ["Carnivora"]
pred_class   = ["Mammalia"]
pred_phylum  = ["Chordata"]
pred_kingdom = ["Animalia"]
```

This permits a species prediction to be checked against reference labels at
kingdom, phylum, class, order, genus, and species levels. Missing lineage values
are represented as `Not Applicable`; the special predictions `Not Applicable`
and `Unclear` bypass the lookup. Values are deduplicated within each evaluated
publication.

The cache is therefore required to reproduce the taxa evaluation. If it is
absent, `evals_local` stops the taxa evaluation and directs the user to download
the supplementary artifact.

## Alternative live GBIF API workflow

The `taxa-with-api` labelling task provides a separate way to obtain taxonomic
details without using `gbif_curated.csv` or `gbif_lookup_cache.pkl`. It sends
the taxon names extracted during labelling to GBIF's Species Match API:

```text
https://api.gbif.org/v2/species/match
```

The API resolves each supplied name against the configured GBIF checklist and
returns the matched usage, match status, taxonomic status, and classification.
The workflow converts accepted matches into rank-specific lineages and applies
the project's broad taxonomic grouping rules.

Responses are stored in a separate SQLite cache so repeated names do not
require repeated API requests. The output metadata records the GBIF checklist
and taxonomy-build identity used for the run, and cached-only execution can
reproduce a completed run without contacting the API.

The two approaches serve different purposes:

| Approach | Taxonomy source | Use |
| --- | --- | --- |
| Curated CSV and `gbif_lookup_cache.pkl` | Fixed 28 August 2023 backbone snapshot | Expand canonical names into lineage fields during taxa evaluation |
| `taxa-with-api` | GBIF Species Match API and the taxonomy build recorded for the run | Resolve extracted taxon names and attach accepted classifications during labelling |
