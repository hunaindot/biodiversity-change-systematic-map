# Building the curated GBIF taxonomy

`data/gbif/curated/gbif_curated.csv` is the project's fixed, enriched copy of
the GBIF Backbone Taxonomy. Its grain is **one row per name usage in the raw
`Taxon.tsv`**, identified by `taxonID`. It is not restricted to accepted taxa or
to species rank.

A prebuilt curated artifact is available on [OSF](https://osf.io/xg8yq). This
document describes the current pipeline for building it from the archived raw
data and saved GBIF Species API responses.

Selected columns from three representative rows illustrate the output:

| `taxonID` | `canonicalName` | `taxonRank` | `taxonomicStatus` | classification | example enrichment |
| ---: | --- | --- | --- | --- | --- |
| 1 | Animalia | kingdom | accepted | Animalia | vernacular names and descriptions when available |
| 1348468 | Leioproctus imitatus | species | accepted | Animalia · Arthropoda · Insecta · Hymenoptera | Species API source profile |
| 12179294 | Pictacollonia pseudotagaroae | species | accepted | Animalia · Mollusca · Gastropoda · Trochida | `marine_curated=True` |

## Pipeline overview

```text
GBIF Backbone archive (28 August 2023)
├── Taxon.tsv ─────────────────────────────── core rows ───┐
├── VernacularName.tsv ── group by taxonID ───────────────┤
├── Description.tsv ───── group by taxonID ───────────────┤
├── meta.xml ──────────── archive schema ─────────────────┤
└── eml.xml ───────────── provenance ─────────────────────┤
                                                           ├─ gbif_curated.csv
Saved GBIF Species API responses                           │
└── species.jsonl ─────── flatten and left-join by ID ────┘
```

The raw backbone determines the output rows and all 23 core taxonomy fields.
Vernacular names, descriptions, and species profiles only add values to those
rows; they never add, remove, filter, or duplicate a core taxon.

## 1. Obtain the raw GBIF Backbone snapshot

This project uses the **28 August 2023** GBIF Backbone Taxonomy Darwin Core
Archive, not the changing `current` archive.

| Property | Value |
| --- | --- |
| Dataset | GBIF Backbone Taxonomy |
| Snapshot | 2023-08-28 13:45:33 UTC |
| DOI | [10.15468/39omei](https://doi.org/10.15468/39omei) |
| Fixed archive | [2023-08-28/backbone.zip](https://hosted-datasets.gbif.org/datasets/backbone/2023-08-28/backbone.zip) |
| Dataset metadata | [`metadata-gbif-raw.xml`](../../mappings/metadata-gbif-raw.xml) |

Download and extract the fixed archive into `data/gbif/raw-2/`. For example:

```bash
mkdir -p data/gbif/raw-2
curl --fail --location \
  https://hosted-datasets.gbif.org/datasets/backbone/2023-08-28/backbone.zip \
  --output /tmp/gbif-backbone-2023-08-28.zip
unzip /tmp/gbif-backbone-2023-08-28.zip -d data/gbif/raw-2
```

The builder uses these extracted files:

```text
data/gbif/raw-2/
├── Taxon.tsv
├── VernacularName.tsv
├── Description.tsv
├── meta.xml
└── eml.xml
```

`meta.xml` is executable archive metadata: it declares file names, encodings,
delimiters, column positions, and Darwin Core terms. `eml.xml` records the
dataset citation, licence, and snapshot provenance. Other archive extensions
are not used to create dedicated curated columns.

The required raw record counts are:

| Raw table | Data records |
| --- | ---: |
| `Taxon.tsv` | 7,746,724 |
| `VernacularName.tsv` | 1,500,815 |
| `Description.tsv` | 1,755,793 |

The build stops if these counts or the relevant `meta.xml` declarations do not
match the fixed snapshot.

## 2. Provide the saved Species API responses

Species attributes were obtained from the GBIF Species API endpoint:

```text
GET https://api.gbif.org/v1/species/{usageKey}/speciesProfiles
```

The `usageKey` is the numeric GBIF `taxonID`. Responses are stored as JSON Lines
at:

```text
data/gbif/curated/species.jsonl
```

Each line contains the queried ID and the complete GBIF response:

```json
{"species_id":"1348468","record":{"offset":0,"limit":100,"endOfRecords":true,"results":[{"taxonKey":1348468,"extinct":false,"source":"Catalogue of Life","sourceTaxonKey":218152984}]}}
```

`species.jsonl` is an input snapshot; the curated builder does not make live
API requests. The current file contains 1,316,131 responses with 1,316,131
unique IDs. All of those IDs occur at species rank in the raw `Taxon.tsv`. The
builder reads the entire file, validates every JSON object, and rejects
duplicate `species_id` values.

## 3. Configure input and output locations

The paths are defined under `dataset_config.gbif_curated` in
`checklists/mappings/repo_config.json`:

```json
{
  "meta": "data/gbif/raw-2/meta.xml",
  "species_profiles": "data/gbif/curated/species.jsonl",
  "output": "data/gbif/curated/gbif_curated.csv"
}
```

## 4. Build the curated CSV

From the repository root, run:

```bash
python -m data_helpers.sources.build_gbif_curated
```

The command writes `data/gbif/curated/gbif_curated.csv`. It first creates an
adjacent `.part` file, validates the completed result, and only then atomically
replaces the existing output. At least 6 GiB of free disk space is required so
the existing and temporary files can coexist safely.

It also writes:

```text
data/gbif/curated/gbif_curated.manifest.json
```

The manifest records inputs, record counts, the ordered `taxonID` hash, and the
hash of all raw core field values.

## 5. How each curated row is created

### Copy the 23 core taxonomy fields

The builder copies every record from `Taxon.tsv`, in source order, including:

```text
taxonID, datasetID, parentNameUsageID, acceptedNameUsageID,
originalNameUsageID, scientificName, scientificNameAuthorship,
canonicalName, genericName, specificEpithet, infraspecificEpithet,
taxonRank, nameAccordingTo, namePublishedIn, taxonomicStatus,
nomenclaturalStatus, taxonRemarks, kingdom, phylum, class, order,
family, genus
```

The archive declares tab-separated fields with no enclosure character.
Consequently, the TSV files are read as UTF-8 with `csv.QUOTE_NONE`; literal
double quotes are data rather than CSV syntax.

### Aggregate vernacular names

`VernacularName.tsv` records are grouped by `taxonID`. The language code is
appended when present, such as `Plant (en)`. Values are retained in source
order, including repeats, joined with `, `, and stored in
`vernaculars_named`.

### Aggregate descriptions

`Description.tsv` records are grouped by `taxonID`. HTML markup is converted
to text, every value is prefixed with its Darwin Core description type, and
multiple values are joined with newlines in `curated_description`.

Because descriptions can contain embedded newlines, record counts for the
curated CSV must be calculated with a CSV parser rather than `wc -l`.

### Flatten and join Species API profiles

Every `species.jsonl` response is flattened and left-joined where the raw
`taxonID` equals `species_id`.

The output retains the complete `results` list and ordered `source` and
`sourceTaxonKey` lists. Text values are deduplicated, sorted, and joined with
semicolons. Comma-separated habitat values are split before this reduction.
Boolean fields contain `True` when at least one returned profile is true and
are otherwise empty.

| API content | Curated column | Non-empty rows |
| --- | --- | ---: |
| queried usage key | `species_id` | 1,316,131 |
| complete result list | `results` | 1,316,131 |
| `livingPeriod` | `livingPeriod_curated` | 74,387 |
| `lifeForm` | `lifeForm_curated` | 56,542 |
| `habitat` | `habitat_curated` | 37,832 |
| `marine` | `marine_curated` | 175,801 |
| `freshwater` | `freshwater_curated` | 45,079 |
| `terrestrial` | `terrestrial_curated` | 253,268 |
| `extinct` | `extinct_curated` | 137,327 |
| `hybrid` | `hybrid_curated` | 198 |
| source list | `source` | 1,316,131 |
| source taxon-key list | `sourceTaxonKey` | 1,316,131 |

`ageInDays_curated`, `sizeInMillimeter_curated`, and `massInGram_curated` are
part of the stable output schema but are empty for this saved response set.
Taxa without a saved response remain in the output with empty profile fields.

## 6. Raw-to-curated reconciliation

The build preserves the raw core grain exactly:

| Check | Raw `Taxon.tsv` | Curated CSV | Difference |
| --- | ---: | ---: | ---: |
| Records | 7,746,724 | 7,746,724 | 0 |
| Unique `taxonID` values | 7,746,724 | 7,746,724 | 0 |
| Columns defining the core taxonomy | 23 | same 23 values | 0 |
| Duplicate `taxonID` values | 0 | 0 | 0 |

Additional structural results are:

| Check | Result |
| --- | ---: |
| Curated columns | 40 |
| Raw IDs absent from curated | 0 |
| Curated IDs absent from raw | 0 |
| Saved species responses read | 1,316,131 |
| Saved species IDs matched to raw taxa | 1,316,131 |

The validated hashes for the current build are:

```text
ordered taxonID SHA-256
6560d9ba055f40635430c174b60bf254b4ad12177e5577ed5b09df5f770c9968

all 23 ordered core fields SHA-256
db9ef1ef7f89585ec5a2e30f70d18a50272e218a0a8681895e28d830cf9a9a70
```

These checks demonstrate that enrichment changes neither the row grain nor the
raw taxonomy values.

The rank and status distributions are therefore also identical. For the most
common ranks:

| `taxonRank` | Raw and curated rows |
| --- | ---: |
| species | 4,994,322 |
| unranked | 1,275,874 |
| genus | 547,518 |
| variety | 421,934 |
| subspecies | 380,481 |
| form | 87,936 |
| family | 34,356 |
| order | 3,092 |
| class | 845 |
| phylum | 347 |
| kingdom | 19 |

The status distribution is likewise preserved:

| `taxonomicStatus` | Raw and curated rows |
| --- | ---: |
| accepted | 4,152,023 |
| synonym | 2,933,225 |
| doubtful | 300,247 |
| homotypic synonym | 190,684 |
| heterotypic synonym | 151,999 |
| proparte synonym | 18,546 |

## 7. What the curated data represent

Each row is a GBIF **name usage**, not necessarily an accepted biological
species. The file includes accepted names, synonyms, doubtful usages, ranks
above and below species, and unranked records.

- `taxonID` identifies the name usage.
- `taxonomicStatus` records whether it is accepted, doubtful, or a synonym.
- `acceptedNameUsageID` links a synonym to its accepted usage when supplied.
- Classification fields preserve the fixed 2023 backbone.
- Vernacular, description, and profile fields are optional enrichments.

The file is not an occurrence dataset or a table containing only accepted
species. Analyses needing accepted species must apply that filter explicitly.

## 8. Build the downstream lookup cache

After rebuilding the curated CSV, rebuild the lookup used by taxa evaluation:

```bash
python -m data_helpers.sources.build_gbif
```

This creates `checklists/mappings/gbif_lookup_cache.pkl`. The lookup builder
reads only `canonicalName`, `taxonomicStatus`, `kingdom`, `phylum`, `class`,
`order`, and `genus`. Species-profile, vernacular, and description fields do
not affect it, so profile enrichment cannot change its grain or taxonomy.

The resulting dictionary maps each normalized canonical name to its available
lineage, preferring an accepted usage over a non-accepted usage with the same
name. The corrected cache contains 5,917,325 normalized names.

## Related live-API workflow

The separate `taxa-with-api` labelling workflow resolves supplied names through
GBIF's live Species Match endpoint (`/v2/species/match`) and keeps its own
SQLite response cache. It does not use `gbif_curated.csv`, `species.jsonl`, or
`gbif_lookup_cache.pkl`, and is not part of the fixed-snapshot build described
here.
