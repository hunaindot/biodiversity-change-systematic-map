"""Fast synthetic tests for the reproducible GBIF curated-data builder."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from data_helpers.sources import build_gbif_curated as gbif


def _write_tsv(
    path: Path,
    columns: tuple[str, ...] | list[str],
    rows: list[dict[str, object]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(columns),
            delimiter="\t",
            lineterminator="\n",
            quoting=csv.QUOTE_NONE,
            quotechar=None,
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> list[bytes]:
    encoded = [
        (json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )
        for record in records
    ]
    path.write_bytes(b"".join(encoded))
    return encoded


def _taxon(taxon_id: str, **overrides: str) -> dict[str, str]:
    row = {column: "" for column in gbif.CORE_COLUMNS}
    row.update(
        {
            "taxonID": taxon_id,
            "scientificName": f"Species {taxon_id}",
            "canonicalName": f"Species {taxon_id}",
            "taxonRank": "SPECIES",
            "taxonomicStatus": "ACCEPTED",
            "kingdom": "Animalia",
        }
    )
    row.update(overrides)
    return row


def _term(column: str) -> str:
    dc_terms = {
        "type",
        "language",
        "description",
        "source",
        "creator",
        "contributor",
        "license",
    }
    if column in dc_terms:
        return f"http://purl.org/dc/terms/{column}"
    if column == "canonicalName":
        return "http://rs.gbif.org/terms/1.0/canonicalName"
    return f"http://rs.tdwg.org/dwc/terms/{column}"


def _table_xml(
    tag: str,
    location: str,
    columns: tuple[str, ...],
    row_type: str,
) -> str:
    id_tag = "id" if tag == "core" else "coreid"
    fields = "\n".join(
        f'    <field index="{index}" term="{_term(column)}"/>'
        for index, column in enumerate(columns[1:], start=1)
    )
    return f"""  <{tag} encoding="UTF-8" fieldsTerminatedBy="\\t"
      linesTerminatedBy="\\n" fieldsEnclosedBy="" ignoreHeaderLines="1"
      rowType="{row_type}">
    <files><location>{location}</location></files>
    <{id_tag} index="0"/>
{fields}
  </{tag}>"""


def _write_archive_metadata(raw_dir: Path) -> Path:
    tables = [
        _table_xml(
            "core",
            "Taxon.tsv",
            gbif.CORE_COLUMNS,
            "http://rs.tdwg.org/dwc/terms/Taxon",
        ),
        _table_xml(
            "extension",
            "VernacularName.tsv",
            gbif.VERNACULAR_COLUMNS,
            "http://rs.gbif.org/terms/1.0/VernacularName",
        ),
        _table_xml(
            "extension",
            "Description.tsv",
            gbif.DESCRIPTION_COLUMNS,
            "http://rs.gbif.org/terms/1.0/Description",
        ),
    ]
    path = raw_dir / "meta.xml"
    path.write_text(
        '<archive xmlns="http://rs.tdwg.org/dwc/text/" metadata="eml.xml">\n'
        + "\n".join(tables)
        + "\n</archive>\n",
        encoding="utf-8",
    )
    return path


def test_parse_archive_metadata_recovers_declared_schema(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    meta_path = _write_archive_metadata(raw_dir)

    tables = gbif.parse_archive_metadata(meta_path)

    assert set(tables) == {"Taxon.tsv", "VernacularName.tsv", "Description.tsv"}
    taxon = tables["Taxon.tsv"]
    assert taxon.location == "Taxon.tsv"
    assert taxon.row_type.endswith("/Taxon")
    assert taxon.encoding.upper() == "UTF-8"
    assert taxon.delimiter == "\t"
    assert taxon.line_terminator == "\n"
    assert taxon.fields_enclosed_by == ""
    assert taxon.ignore_header_lines == 1
    assert taxon.field_count == len(gbif.CORE_COLUMNS)
    assert taxon.columns == gbif.CORE_COLUMNS
    assert tables["Description.tsv"].columns == gbif.DESCRIPTION_COLUMNS


def test_quote_none_reader_preserves_literal_unmatched_quotes(tmp_path: Path) -> None:
    path = tmp_path / "Taxon.tsv"
    path.write_text(
        'taxonID\tnamePublishedIn\n1\tCatalogue "with unmatched quote\n'
        "2\tFollowing record\n",
        encoding="utf-8",
    )

    rows = list(gbif.iter_tsv_rows(path, ("taxonID", "namePublishedIn")))

    assert rows == [
        {"taxonID": "1", "namePublishedIn": 'Catalogue "with unmatched quote'},
        {"taxonID": "2", "namePublishedIn": "Following record"},
    ]


def test_quote_none_reader_rejects_any_wrong_field_count(tmp_path: Path) -> None:
    path = tmp_path / "Taxon.tsv"
    path.write_text("taxonID\tname\n1\tvalid\n2\textra\tfield\n", encoding="utf-8")

    with pytest.raises(gbif.InputFormatError, match=r"field|column"):
        list(gbif.iter_tsv_rows(path, ("taxonID", "name")))


def test_quote_none_reader_accepts_fields_larger_than_csv_default_limit(
    tmp_path: Path,
) -> None:
    path = tmp_path / "Description.tsv"
    description = "x" * 140_000
    path.write_text("taxonID\tdescription\n1\t" + description + "\n", encoding="utf-8")

    rows = list(gbif.iter_tsv_rows(path, ("taxonID", "description")))

    assert rows[0]["description"] == description


def test_vernacular_aggregation_preserves_order_and_duplicates(tmp_path: Path) -> None:
    path = tmp_path / "VernacularName.tsv"
    _write_tsv(
        path,
        gbif.VERNACULAR_COLUMNS,
        [
            {"taxonID": "1", "vernacularName": "Robin", "language": "en"},
            {"taxonID": "1", "vernacularName": "Robin", "language": "en"},
            {"taxonID": "2", "vernacularName": "Ignored", "language": "en"},
            {"taxonID": "1", "vernacularName": "Merle", "language": ""},
        ],
    )

    values, row_count = gbif.aggregate_vernaculars(path)

    assert row_count == 4
    assert values == {
        "1": "Robin (en), Robin (en), Merle",
        "2": "Ignored (en)",
    }


def test_description_aggregation_cleans_html_and_keeps_record_order(
    tmp_path: Path,
) -> None:
    path = tmp_path / "Description.tsv"
    _write_tsv(
        path,
        gbif.DESCRIPTION_COLUMNS,
        [
            {
                "taxonID": "1",
                "type": "Distribution",
                "description": "<p>First&nbsp;</p><p>Second &amp; more</p>",
            },
            {
                "taxonID": "2",
                "type": "Ignored",
                "description": "Not selected",
            },
            {
                "taxonID": "1",
                "type": "Biology",
                "description": "<b>Day</b><i>active</i>",
            },
        ],
    )

    values, row_count = gbif.aggregate_descriptions(path)

    assert row_count == 3
    assert values == {
        "1": "Distribution: First\N{NO-BREAK SPACE}Second & more\nBiology: Dayactive",
        "2": "Ignored: Not selected",
    }
    assert gbif.clean_description_html("A &lt; B<br>C") == "A < BC"


def test_profile_flattening_handles_empty_multiple_and_boolean_values() -> None:
    results = [
        {
            "source": "Checklist B",
            "sourceTaxonKey": "b",
            "habitat": "Wetland",
            "marine": False,
            "freshwater": False,
        },
        {
            "source": "Checklist A",
            "sourceTaxonKey": "a",
            "habitat": "Forest, Coastal",
            "marine": True,
            "freshwater": False,
            "livingPeriod": "Recent",
            "lifeForm": "Tree, Shrub",
        },
        {"habitat": "Wetland", "livingPeriod": "Recent"},
        {"habitat": "Rocky,Coastal"},
    ]

    flattened = gbif.flatten_species_record("1", {"results": results})

    assert flattened["species_id"] == "1"
    assert flattened["results"] == str(results)
    assert flattened["source"] == str(["Checklist B", "Checklist A"])
    assert flattened["sourceTaxonKey"] == str(["b", "a"])
    assert flattened["habitat_curated"] == "Coastal;Forest;Rocky;Wetland"
    assert flattened["livingPeriod_curated"] == "Recent"
    assert flattened["lifeForm_curated"] == "Tree, Shrub"
    assert flattened["marine_curated"] == "True"
    assert flattened["freshwater_curated"] == ""

    empty = gbif.flatten_species_record("2", {"results": []})
    assert empty["results"] == "[]"
    assert empty["source"] == "[]"
    assert empty["sourceTaxonKey"] == "[]"
    assert all(empty[f"{field}_curated"] == "" for field in gbif.PROFILE_FIELDS)


def test_species_loader_reads_and_hashes_every_record(tmp_path: Path) -> None:
    path = tmp_path / "species.jsonl"
    encoded = _write_jsonl(
        path,
        [
            {"species_id": "1", "record": {"results": []}},
            {"species_id": "2", "record": {"results": [{"marine": True}]}},
            {"species_id": "3", "record": {"results": []}},
        ],
    )
    expected_hash = hashlib.sha256(b"".join(encoded)).hexdigest()

    profiles, stats = gbif.load_species_profiles(path)

    assert set(profiles) == {"1", "2", "3"}
    assert stats["records_read"] == 3
    assert stats["unique_species_ids"] == 3
    assert stats["file_sha256"] == expected_hash

    duplicate_path = tmp_path / "duplicates.jsonl"
    _write_jsonl(
        duplicate_path,
        [
            {"species_id": "1", "record": {"results": []}},
            {"species_id": "1", "record": {"results": []}},
        ],
    )
    with pytest.raises(gbif.InputFormatError, match="Duplicate species_id"):
        gbif.load_species_profiles(duplicate_path)


def test_tiny_end_to_end_build_preserves_every_taxon_and_has_no_blank_column(
    tmp_path: Path,
) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    _write_archive_metadata(raw_dir)
    _write_tsv(
        raw_dir / "Taxon.tsv",
        gbif.CORE_COLUMNS,
        [
            _taxon("1", namePublishedIn='Catalogue "literal quote'),
            _taxon("2", scientificName="Second species"),
        ],
    )
    _write_tsv(
        raw_dir / "VernacularName.tsv",
        gbif.VERNACULAR_COLUMNS,
        [{"taxonID": "1", "vernacularName": "Robin", "language": "en"}],
    )
    _write_tsv(
        raw_dir / "Description.tsv",
        gbif.DESCRIPTION_COLUMNS,
        [{"taxonID": "2", "type": "Biology", "description": "<b>Active</b>"}],
    )
    species_path = tmp_path / "species.jsonl"
    _write_jsonl(
        species_path,
        [
            {
                "species_id": "1",
                "record": {
                    "results": [
                        {
                            "source": "Source",
                            "sourceTaxonKey": "key-1",
                            "habitat": "Forest",
                        }
                    ]
                },
            }
        ],
    )
    output = tmp_path / "gbif_curated_candidate.csv"
    output.write_text("stale output is replaced", encoding="utf-8")

    manifest = gbif.build_curated(
        raw_dir,
        species_path,
        output,
    )

    with output.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        assert tuple(reader.fieldnames or ()) == gbif.CURATED_COLUMNS
    assert "" not in (reader.fieldnames or ())
    assert [row["taxonID"] for row in rows] == ["1", "2"]
    assert len({row["taxonID"] for row in rows}) == 2
    assert rows[0]["namePublishedIn"] == 'Catalogue "literal quote'
    assert rows[0]["vernaculars_named"] == "Robin (en)"
    assert rows[0]["habitat_curated"] == "Forest"
    assert rows[1]["curated_description"] == "Biology: Active"
    assert manifest["core_rows"] == 2
    assert manifest["output_rows"] == 2
    assert manifest["missing_core_ids"] == 0
    assert manifest["duplicate_output_ids"] == 0
    assert len(manifest["validation"]["core_field_sha256"]) == 64
    gbif.validate_curated_csv(output, expected_ids=("1", "2"))

    expected_core_hash = manifest["validation"]["core_field_sha256"]
    rows[0]["canonicalName"] = "Changed after serialization"
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=gbif.CURATED_COLUMNS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(gbif.GbifCuratedError, match="core-field"):
        gbif.validate_curated_csv(
            output,
            expected_rows=2,
            expected_core_sha256=expected_core_hash,
        )


def test_output_path_rejects_a_directory(tmp_path: Path) -> None:
    with pytest.raises(gbif.OutputProtectionError, match=r"directory"):
        gbif.validate_output_path(tmp_path)
