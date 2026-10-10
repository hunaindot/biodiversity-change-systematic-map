"""Rebuild the curated GBIF taxonomy from its archived raw inputs.

The raw GBIF Darwin Core Archive declares tab-separated, unquoted fields.  It
is important that these files are read with ``csv.QUOTE_NONE``: interpreting a
literal double quote as CSV syntax is what caused records to be swallowed by
the historical conversion.

Typical usage::

    python -m data_helpers.sources.build_gbif_curated

The builder writes to an adjacent ``.part`` file, validates row counts, IDs,
all 23 raw core fields, and output structure, and only then atomically moves it
to the requested output path.
"""

from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import os
import shutil
import sys
from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


REPO_ROOT = Path(__file__).resolve().parents[2]
_REPO_CONFIG_PATH = REPO_ROOT / "checklists" / "mappings" / "repo_config.json"


class GbifCuratedError(RuntimeError):
    """Base class for errors raised by this builder."""


class InputFormatError(GbifCuratedError, ValueError):
    """An input does not match the declared GBIF archive format."""


class OutputProtectionError(GbifCuratedError, ValueError):
    """An output path violates a builder safety rule."""


def _load_builder_config() -> dict[str, Any]:
    """Load optional repository defaults without making import depend on them."""
    try:
        with _REPO_CONFIG_PATH.open(encoding="utf-8") as handle:
            root = json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}

    dataset_config = root.get("dataset_config")
    if not isinstance(dataset_config, dict):
        return {}
    config = dataset_config.get("gbif_curated")
    return config if isinstance(config, dict) else {}


_CONFIG = _load_builder_config()


def _configured_path(key: str, fallback: str) -> Path:
    raw = _CONFIG.get(key, fallback)
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(
            f"dataset_config.gbif_curated.{key} must be a non-empty path string"
        )
    path = Path(raw.strip())
    return path if path.is_absolute() else REPO_ROOT / path


DEFAULT_META_PATH = _configured_path("meta", "data/gbif/raw-2/meta.xml")
DEFAULT_RAW_DIR = DEFAULT_META_PATH.parent
DEFAULT_SPECIES_PATH = _configured_path(
    "species_profiles", "data/gbif/curated/species.jsonl"
)
CURATED_OUTPUT_PATH = _configured_path("output", "data/gbif/curated/gbif_curated.csv")
CORE_COLUMNS = (
    "taxonID",
    "datasetID",
    "parentNameUsageID",
    "acceptedNameUsageID",
    "originalNameUsageID",
    "scientificName",
    "scientificNameAuthorship",
    "canonicalName",
    "genericName",
    "specificEpithet",
    "infraspecificEpithet",
    "taxonRank",
    "nameAccordingTo",
    "namePublishedIn",
    "taxonomicStatus",
    "nomenclaturalStatus",
    "taxonRemarks",
    "kingdom",
    "phylum",
    "class",
    "order",
    "family",
    "genus",
)

VERNACULAR_COLUMNS = (
    "taxonID",
    "vernacularName",
    "language",
    "country",
    "countryCode",
    "sex",
    "lifeStage",
    "source",
)

DESCRIPTION_COLUMNS = (
    "taxonID",
    "type",
    "language",
    "description",
    "source",
    "creator",
    "contributor",
    "license",
)

PROFILE_FIELDS = (
    "livingPeriod",
    "lifeForm",
    "habitat",
    "marine",
    "freshwater",
    "terrestrial",
    "extinct",
    "hybrid",
    "ageInDays",
    "sizeInMillimeter",
    "massInGram",
)
BOOLEAN_PROFILE_FIELDS = frozenset(
    {"marine", "freshwater", "terrestrial", "extinct", "hybrid"}
)
PROFILE_OUTPUT_COLUMNS = tuple(f"{field}_curated" for field in PROFILE_FIELDS)
SPECIES_COLUMNS = (
    "species_id",
    "results",
    *PROFILE_OUTPUT_COLUMNS,
    "source",
    "sourceTaxonKey",
)
CURATED_COLUMNS = (
    *CORE_COLUMNS,
    "vernaculars_named",
    "curated_description",
    *SPECIES_COLUMNS,
)

EXPECTED_ARCHIVE_ROWS = {
    "Taxon.tsv": 7_746_724,
    "VernacularName.tsv": 1_500_815,
    "Description.tsv": 1_755_793,
}

# A rebuild has to coexist with the current CSV until the validated
# ``.part`` file is atomically promoted.  Six GiB covers the observed ~3.4 GiB
# output plus growth from restored records and a useful filesystem margin.
MIN_BUILD_FREE_BYTES = 6 * 1024**3

_EXPECTED_COLUMNS = {
    "Taxon.tsv": CORE_COLUMNS,
    "VernacularName.tsv": VERNACULAR_COLUMNS,
    "Description.tsv": DESCRIPTION_COLUMNS,
}


def _raise_csv_field_size_limit() -> int:
    """Allow the archive's ~303 KB description fields on every platform."""
    candidate = sys.maxsize
    while candidate > 10_000_000:
        try:
            csv.field_size_limit(candidate)
            return candidate
        except OverflowError:
            candidate //= 10
    csv.field_size_limit(10_000_000)
    return 10_000_000


CSV_FIELD_SIZE_LIMIT = _raise_csv_field_size_limit()


@dataclass(frozen=True, slots=True)
class ArchiveTable:
    """A core or extension table declared by Darwin Core ``meta.xml``."""

    location: str
    row_type: str
    columns: tuple[str, ...]
    encoding: str
    delimiter: str
    line_terminator: str
    fields_enclosed_by: str
    ignore_header_lines: int
    field_count: int


def _xml_local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _decode_archive_character(value: str) -> str:
    replacements = {r"\t": "\t", r"\n": "\n", r"\r": "\r"}
    return replacements.get(value, value)


def _term_name(term: str) -> str:
    return term.rstrip("/").rsplit("/", 1)[-1]


def parse_archive_metadata(meta_path: Path | str) -> dict[str, ArchiveTable]:
    """Parse Darwin Core table declarations, keyed by archive location."""
    path = Path(meta_path)
    try:
        root = ElementTree.parse(path).getroot()
    except (OSError, ElementTree.ParseError) as exc:
        raise InputFormatError(
            f"Cannot parse Darwin Core metadata {path}: {exc}"
        ) from exc

    tables: dict[str, ArchiveTable] = {}
    for element in root:
        kind = _xml_local_name(element.tag)
        if kind not in {"core", "extension"}:
            continue

        locations = [
            child.text.strip()
            for child in element.iter()
            if _xml_local_name(child.tag) == "location"
            and child.text
            and child.text.strip()
        ]
        if len(locations) != 1:
            raise InputFormatError(
                f"Each metadata table must declare exactly one location in {path}"
            )
        location = locations[0]

        indexed_columns: dict[int, str] = {}
        for child in element:
            child_kind = _xml_local_name(child.tag)
            if child_kind not in {"id", "coreid", "field"}:
                continue
            try:
                index = int(child.attrib["index"])
            except (KeyError, ValueError) as exc:
                raise InputFormatError(
                    f"Invalid field index for {location} in {path}"
                ) from exc
            if index in indexed_columns:
                raise InputFormatError(
                    f"Duplicate field index {index} for {location} in {path}"
                )
            if child_kind in {"id", "coreid"}:
                column = "taxonID"
            else:
                term = child.attrib.get("term", "")
                if not term:
                    raise InputFormatError(
                        f"Field {index} for {location} has no term in {path}"
                    )
                column = _term_name(term)
            indexed_columns[index] = column

        if not indexed_columns:
            raise InputFormatError(f"No fields declared for {location} in {path}")
        field_count = max(indexed_columns) + 1
        expected_indexes = set(range(field_count))
        if set(indexed_columns) != expected_indexes:
            missing = sorted(expected_indexes.difference(indexed_columns))
            raise InputFormatError(
                f"Non-contiguous fields for {location} in {path}; missing {missing}"
            )

        try:
            ignore_header_lines = int(element.attrib.get("ignoreHeaderLines", "0"))
        except ValueError as exc:
            raise InputFormatError(
                f"Invalid ignoreHeaderLines for {location} in {path}"
            ) from exc

        table = ArchiveTable(
            location=location,
            row_type=element.attrib.get("rowType", ""),
            columns=tuple(indexed_columns[index] for index in range(field_count)),
            encoding=element.attrib.get("encoding", ""),
            delimiter=_decode_archive_character(
                element.attrib.get("fieldsTerminatedBy", "")
            ),
            line_terminator=_decode_archive_character(
                element.attrib.get("linesTerminatedBy", "")
            ),
            fields_enclosed_by=element.attrib.get("fieldsEnclosedBy", ""),
            ignore_header_lines=ignore_header_lines,
            field_count=field_count,
        )
        if location in tables:
            raise InputFormatError(f"Duplicate table location {location!r} in {path}")
        tables[location] = table

    if not tables:
        raise InputFormatError(f"No core or extension tables found in {path}")
    return tables


def _validate_used_archive_tables(raw_dir: Path) -> dict[str, ArchiveTable]:
    meta_path = raw_dir / "meta.xml"
    tables = parse_archive_metadata(meta_path)
    for location, expected_columns in _EXPECTED_COLUMNS.items():
        try:
            table = tables[location]
        except KeyError as exc:
            raise InputFormatError(
                f"{location} is not declared by {meta_path}"
            ) from exc
        problems: list[str] = []
        if table.encoding.upper().replace("_", "-") != "UTF-8":
            problems.append(f"encoding={table.encoding!r}")
        if table.delimiter != "\t":
            problems.append(f"delimiter={table.delimiter!r}")
        if table.line_terminator != "\n":
            problems.append(f"line terminator={table.line_terminator!r}")
        if table.fields_enclosed_by != "":
            problems.append(f"fieldsEnclosedBy={table.fields_enclosed_by!r}")
        if table.ignore_header_lines != 1:
            problems.append(f"ignoreHeaderLines={table.ignore_header_lines!r}")
        if table.columns != tuple(expected_columns):
            problems.append(f"columns={table.columns!r}")
        if table.field_count != len(expected_columns):
            problems.append(f"field_count={table.field_count!r}")
        if problems:
            raise InputFormatError(
                f"Unsupported archive declaration for {location}: "
                + ", ".join(problems)
            )
    return tables


def iter_tsv_rows(
    path: Path | str,
    expected_columns: Sequence[str] | ArchiveTable,
) -> Iterator[dict[str, str]]:
    """Yield every unquoted TSV row, failing on any header or width mismatch."""
    input_path = Path(path)
    columns = (
        expected_columns.columns
        if isinstance(expected_columns, ArchiveTable)
        else tuple(expected_columns)
    )
    if isinstance(expected_columns, ArchiveTable):
        table = expected_columns
        if (
            table.encoding.upper().replace("_", "-") != "UTF-8"
            or table.delimiter != "\t"
            or table.fields_enclosed_by != ""
            or table.ignore_header_lines != 1
        ):
            raise InputFormatError(
                f"Unsupported metadata declaration for {table.location}"
            )

    try:
        handle = input_path.open(encoding="utf-8", newline="")
    except OSError as exc:
        raise InputFormatError(f"Cannot open TSV input {input_path}: {exc}") from exc

    with handle:
        reader = csv.reader(
            handle,
            delimiter="\t",
            quoting=csv.QUOTE_NONE,
            strict=True,
        )
        try:
            header = next(reader)
        except StopIteration as exc:
            raise InputFormatError(f"TSV input is empty: {input_path}") from exc
        except csv.Error as exc:
            raise InputFormatError(
                f"Cannot read TSV header {input_path}: {exc}"
            ) from exc

        if tuple(header) != columns:
            raise InputFormatError(
                f"Unexpected header in {input_path}; expected {columns!r}, got {tuple(header)!r}"
            )

        try:
            for row_number, row in enumerate(reader, start=2):
                if len(row) != len(columns):
                    raise InputFormatError(
                        f"{input_path}:{row_number} has {len(row)} fields; "
                        f"expected {len(columns)}"
                    )
                yield dict(zip(columns, row, strict=True))
        except csv.Error as exc:
            raise InputFormatError(
                f"Invalid TSV record in {input_path} near physical line "
                f"{reader.line_num}: {exc}"
            ) from exc


class _PlainTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def clean_description_html(value: str) -> str:
    """Return HTML text with entity decoding and no inserted tag separator."""
    parser = _PlainTextParser()
    try:
        parser.feed(value)
        parser.close()
    except Exception as exc:  # HTMLParser can surface malformed declarations.
        raise InputFormatError(f"Cannot parse description HTML: {exc}") from exc
    return "".join(parser.parts)


def aggregate_vernaculars(
    path: Path | str,
) -> tuple[dict[str, str], int]:
    """Aggregate vernacular labels in archive order; duplicates are retained."""
    grouped: defaultdict[str, list[str]] = defaultdict(list)
    row_count = 0
    for row in iter_tsv_rows(path, VERNACULAR_COLUMNS):
        row_count += 1
        taxon_id = row["taxonID"]
        label = row["vernacularName"]
        if row["language"]:
            label += f" ({row['language']})"
        grouped[taxon_id].append(label)
    return {
        taxon_id: ", ".join(values) for taxon_id, values in grouped.items()
    }, row_count


def aggregate_descriptions(
    path: Path | str,
) -> tuple[dict[str, str], int]:
    """Aggregate typed, plain-text descriptions in archive order."""
    grouped: defaultdict[str, list[str]] = defaultdict(list)
    row_count = 0
    for row in iter_tsv_rows(path, DESCRIPTION_COLUMNS):
        row_count += 1
        taxon_id = row["taxonID"]
        cleaned = clean_description_html(row["description"])
        grouped[taxon_id].append(f"{row['type']}: {cleaned}")
    return {
        taxon_id: "\n".join(values) for taxon_id, values in grouped.items()
    }, row_count


def flatten_species_record(
    species_id: str, record: Mapping[str, Any]
) -> dict[str, str]:
    """Flatten one saved GBIF species-profile response into curated columns."""
    raw_results = record.get("results")
    if not isinstance(raw_results, list):
        raise InputFormatError(
            f"Species profile {species_id!r} has no list-valued record.results"
        )
    if not all(isinstance(result, dict) for result in raw_results):
        raise InputFormatError(
            f"Species profile {species_id!r} contains a non-object result"
        )
    results: list[dict[str, Any]] = raw_results

    flattened: dict[str, str] = {
        "species_id": species_id,
        "results": repr(results),
    }
    for field in PROFILE_FIELDS:
        output_name = f"{field}_curated"
        if field in BOOLEAN_PROFILE_FIELDS:
            flattened[output_name] = (
                "True" if any(bool(result.get(field)) for result in results) else ""
            )
            continue
        # The historical transformation treated comma-separated habitat text
        # as multiple values before applying its set reduction.  Preserve that
        # field-specific contract, but sort members so rebuilt output is
        # deterministic across Python processes.
        distinct_values: set[str] = set()
        for result in results:
            if field not in result or not bool(result[field]):
                continue
            value = str(result[field])
            if field == "habitat":
                distinct_values.update(
                    member.strip() for member in value.split(",") if member.strip()
                )
            else:
                distinct_values.add(value)
        distinct = sorted(distinct_values)
        flattened[output_name] = ";".join(distinct)

    flattened["source"] = repr(
        [result["source"] for result in results if result.get("source")]
    )
    flattened["sourceTaxonKey"] = repr(
        [result["sourceTaxonKey"] for result in results if result.get("sourceTaxonKey")]
    )
    return flattened


def load_species_profiles(
    path: Path | str,
) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    """Load and validate every saved GBIF species-profile response."""
    input_path = Path(path)
    profiles: dict[str, dict[str, str]] = {}
    file_digest = hashlib.sha256()
    records_read = 0

    try:
        handle = input_path.open("rb")
    except OSError as exc:
        raise InputFormatError(
            f"Cannot open species profiles {input_path}: {exc}"
        ) from exc

    with handle:
        for line_number, raw_line in enumerate(handle, start=1):
            records_read += 1
            file_digest.update(raw_line)
            if not raw_line.strip():
                raise InputFormatError(
                    f"Blank JSONL record at {input_path}:{line_number}"
                )
            try:
                payload = json.loads(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise InputFormatError(
                    f"Invalid JSONL record at {input_path}:{line_number}: {exc}"
                ) from exc
            if not isinstance(payload, dict):
                raise InputFormatError(
                    f"JSONL record at {input_path}:{line_number} is not an object"
                )
            raw_species_id = payload.get("species_id")
            if raw_species_id is None or str(raw_species_id) == "":
                raise InputFormatError(
                    f"JSONL record at {input_path}:{line_number} has no species_id"
                )
            species_id = str(raw_species_id)
            record = payload.get("record")
            if not isinstance(record, dict):
                raise InputFormatError(
                    f"JSONL record at {input_path}:{line_number} has no record object"
                )
            if species_id in profiles:
                raise InputFormatError(
                    f"Duplicate species_id {species_id!r} at {input_path}:{line_number}"
                )
            profiles[species_id] = flatten_species_record(species_id, record)

    stats: dict[str, Any] = {
        "records_read": records_read,
        "unique_species_ids": len(profiles),
        "file_sha256": file_digest.hexdigest(),
    }
    return profiles, stats


def validate_output_path(
    path: Path | str,
) -> Path:
    """Resolve and validate an output path."""
    output = Path(path).expanduser().resolve()
    if output.is_dir():
        raise OutputProtectionError(f"Output is a directory: {output}")
    return output


def _enforce_snapshot_row_counts(observed: Mapping[str, int]) -> None:
    mismatches = []
    for location, expected in EXPECTED_ARCHIVE_ROWS.items():
        actual = observed.get(location)
        if actual != expected:
            rendered = "not scanned" if actual is None else f"{actual:,}"
            mismatches.append(f"{location}: expected {expected:,}, got {rendered}")
    if mismatches:
        raise InputFormatError(
            "Raw files do not match the pinned GBIF snapshot row counts: "
            + "; ".join(mismatches)
        )


def _output_size_estimate() -> int:
    if not CURATED_OUTPUT_PATH.is_file():
        return MIN_BUILD_FREE_BYTES
    # Allow for input growth, CSV quoting changes, and sidecar metadata.
    return int(CURATED_OUTPUT_PATH.stat().st_size * 1.25)


def preflight_output_disk_space(output_dir: Path | str) -> dict[str, int]:
    """Fail before a full build if its temporary CSV cannot fit."""
    directory = Path(output_dir).expanduser().resolve()
    usage = shutil.disk_usage(directory)
    estimated_output_bytes = _output_size_estimate()
    required_free_bytes = max(
        MIN_BUILD_FREE_BYTES,
        estimated_output_bytes + 1024**3,
    )
    if usage.free < required_free_bytes:
        raise OutputProtectionError(
            "Insufficient disk space for GBIF rebuild: "
            f"{usage.free / 1024**3:.1f} GiB free, "
            f"at least {required_free_bytes / 1024**3:.1f} GiB required"
        )
    return {
        "free_bytes": usage.free,
        "required_free_bytes": required_free_bytes,
        "estimated_output_bytes": estimated_output_bytes,
    }


def _update_values_digest(digest: Any, values: Iterable[str]) -> None:
    """Hash a sequence of text fields without delimiter ambiguity."""
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)


def _update_id_digest(digest: Any, taxon_id: str) -> None:
    _update_values_digest(digest, (taxon_id,))


def validate_curated_csv(
    path: Path | str,
    *,
    expected_rows: int | None = None,
    expected_id_sha256: str | None = None,
    expected_core_sha256: str | None = None,
    expected_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Validate output structure, IDs, and all raw Taxon field values."""
    output_path = Path(path)
    expected_id_values = (
        tuple(str(value) for value in expected_ids)
        if expected_ids is not None
        else None
    )
    if expected_id_values is not None:
        if expected_rows is not None and expected_rows != len(expected_id_values):
            raise ValueError("expected_rows and expected_ids disagree")
        expected_rows = len(expected_id_values)
        expected_digest = hashlib.sha256()
        for taxon_id in expected_id_values:
            _update_id_digest(expected_digest, taxon_id)
        derived_sha256 = expected_digest.hexdigest()
        if expected_id_sha256 is not None and expected_id_sha256 != derived_sha256:
            raise ValueError("expected_id_sha256 and expected_ids disagree")
        expected_id_sha256 = derived_sha256
    seen_ids: set[str] = set()
    duplicate_ids: list[str] = []
    id_digest = hashlib.sha256()
    core_digest = hashlib.sha256()
    row_count = 0
    try:
        handle = output_path.open(encoding="utf-8", newline="")
    except OSError as exc:
        raise GbifCuratedError(f"Cannot validate output {output_path}: {exc}") from exc
    with handle:
        reader = csv.reader(handle, strict=True)
        try:
            header = next(reader)
        except (StopIteration, csv.Error) as exc:
            raise GbifCuratedError(
                f"Cannot read output header {output_path}: {exc}"
            ) from exc
        if tuple(header) != CURATED_COLUMNS:
            raise GbifCuratedError(
                f"Unexpected output header in {output_path}; got {tuple(header)!r}"
            )
        try:
            for row_number, row in enumerate(reader, start=2):
                if len(row) != len(CURATED_COLUMNS):
                    raise GbifCuratedError(
                        f"{output_path}:{row_number} has {len(row)} fields; "
                        f"expected {len(CURATED_COLUMNS)}"
                    )
                taxon_id = row[0]
                if taxon_id in seen_ids and len(duplicate_ids) < 20:
                    duplicate_ids.append(taxon_id)
                seen_ids.add(taxon_id)
                _update_id_digest(id_digest, taxon_id)
                _update_values_digest(core_digest, row[: len(CORE_COLUMNS)])
                row_count += 1
        except csv.Error as exc:
            raise GbifCuratedError(
                f"Invalid CSV output near record {reader.line_num}: {exc}"
            ) from exc

    if duplicate_ids:
        raise GbifCuratedError(
            f"Output has duplicate taxonID values, including {duplicate_ids!r}"
        )
    if expected_rows is not None and row_count != expected_rows:
        raise GbifCuratedError(
            f"Output has {row_count:,} rows; expected {expected_rows:,}"
        )
    id_sha256 = id_digest.hexdigest()
    if expected_id_sha256 is not None and id_sha256 != expected_id_sha256:
        raise GbifCuratedError(
            f"Output taxonID/order SHA-256 mismatch: expected "
            f"{expected_id_sha256}, got {id_sha256}"
        )
    core_sha256 = core_digest.hexdigest()
    if expected_core_sha256 is not None and core_sha256 != expected_core_sha256:
        raise GbifCuratedError(
            "Output core-field SHA-256 mismatch: expected "
            f"{expected_core_sha256}, got {core_sha256}"
        )
    return {
        "rows": row_count,
        "unique_taxon_ids": len(seen_ids),
        "duplicate_taxon_ids": 0,
        "column_count": len(CURATED_COLUMNS),
        "unnamed_columns": 0,
        "taxon_id_order_sha256": id_sha256,
        "core_field_sha256": core_sha256,
    }


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    try:
        with part.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(part, path)
    except Exception:
        try:
            part.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def build_curated(
    raw_dir: Path | str,
    species_path: Path | str,
    output_path: Path | str,
    *,
    enforce_snapshot_counts: bool = False,
) -> dict[str, Any]:
    """Build, validate, and atomically publish a curated GBIF CSV."""
    archive_dir = Path(raw_dir)
    tables = _validate_used_archive_tables(archive_dir)
    output = validate_output_path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    part = output.with_name(output.name + ".part")
    if part.exists():
        part.unlink()

    disk_preflight: dict[str, int] | None = None
    if output == CURATED_OUTPUT_PATH.resolve():
        disk_preflight = preflight_output_disk_space(output.parent)

    vernaculars, vernacular_rows = aggregate_vernaculars(
        archive_dir / "VernacularName.tsv"
    )
    descriptions, description_rows = aggregate_descriptions(
        archive_dir / "Description.tsv"
    )
    profiles, species_stats = load_species_profiles(species_path)
    raw_rows = 0
    output_rows = 0
    id_digest = hashlib.sha256()
    core_digest = hashlib.sha256()

    try:
        with part.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=CURATED_COLUMNS,
                extrasaction="raise",
                lineterminator="\n",
            )
            writer.writeheader()
            for core in iter_tsv_rows(archive_dir / "Taxon.tsv", tables["Taxon.tsv"]):
                raw_rows += 1
                taxon_id = core["taxonID"]

                row = {column: "" for column in CURATED_COLUMNS}
                row.update(core)
                row["vernaculars_named"] = vernaculars.get(taxon_id, "")
                row["curated_description"] = descriptions.get(taxon_id, "")
                if taxon_id in profiles:
                    row.update(profiles[taxon_id])
                writer.writerow(row)
                output_rows += 1
                _update_id_digest(id_digest, taxon_id)
                _update_values_digest(
                    core_digest, (core[column] for column in CORE_COLUMNS)
                )

        if output_rows != raw_rows:
            raise GbifCuratedError(
                f"Core row loss while writing: read {raw_rows:,}, wrote {output_rows:,}"
            )
        if enforce_snapshot_counts:
            _enforce_snapshot_row_counts(
                {
                    "Taxon.tsv": raw_rows,
                    "VernacularName.tsv": vernacular_rows,
                    "Description.tsv": description_rows,
                }
            )

        expected_id_sha256 = id_digest.hexdigest()
        expected_core_sha256 = core_digest.hexdigest()
        del vernaculars, descriptions, profiles
        gc.collect()
        validation = validate_curated_csv(
            part,
            expected_rows=output_rows,
            expected_id_sha256=expected_id_sha256,
            expected_core_sha256=expected_core_sha256,
        )
        raw_unique_ids = validation["unique_taxon_ids"]

        os.replace(part, output)
    except Exception:
        try:
            part.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    created_at = datetime.now(timezone.utc).isoformat()
    manifest: dict[str, Any] = {
        "kind": "gbif_curated_build_manifest",
        "version": 2,
        "created_at": created_at,
        "command": "build",
        "inputs": {
            "raw_dir": str(archive_dir.resolve()),
            "meta": str((archive_dir / "meta.xml").resolve()),
            "taxon": str((archive_dir / "Taxon.tsv").resolve()),
            "vernacular_name": str((archive_dir / "VernacularName.tsv").resolve()),
            "description": str((archive_dir / "Description.tsv").resolve()),
            "species_profiles": str(Path(species_path).resolve()),
        },
        "output": str(output),
        "settings": {
            "encoding": "utf-8",
            "delimiter": "tab",
            "raw_quoting": "QUOTE_NONE",
            "snapshot_row_counts_enforced": enforce_snapshot_counts,
        },
        "counts": {
            "taxon_rows_read": raw_rows,
            "taxon_unique_ids_read": raw_unique_ids,
            "vernacular_rows_read": vernacular_rows,
            "description_rows_read": description_rows,
            "output_rows": output_rows,
        },
        "species_profiles": species_stats,
        "validation": validation,
        # Concise top-level reconciliation fields are convenient for callers and
        # make the no-loss contract explicit without navigating nested metadata.
        "core_rows": raw_rows,
        "output_rows": output_rows,
        "missing_core_ids": 0,
        "duplicate_output_ids": validation["duplicate_taxon_ids"],
    }
    if disk_preflight is not None:
        manifest["disk_preflight"] = disk_preflight
    manifest_path = output.with_suffix(".manifest.json")
    _atomic_write_json(manifest_path, manifest)
    return manifest


def _build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Build the curated GBIF taxonomy from the pinned raw snapshot"
    )


def _print_json(payload: Mapping[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        manifest = build_curated(
            DEFAULT_RAW_DIR,
            DEFAULT_SPECIES_PATH,
            CURATED_OUTPUT_PATH,
            enforce_snapshot_counts=True,
        )
        _print_json(manifest)
        return 0
    except (GbifCuratedError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
