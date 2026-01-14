from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import pandas as pd
import tantivy
from tantivy import Document, Index

from .config import FilterConfig, IndexConfig
from .schema import build_schema
from .utils import (
    edge_ngrams,
    make_name_text,
    norm_keyword,
    split_vernaculars,
    to_bool01,
    to_int_or_none,
)


def _filter_chunk(df: pd.DataFrame, filters: FilterConfig) -> pd.DataFrame:
    out = df
    if filters.allowed_ranks and "taxonRank" in out.columns:
        out = out[out["taxonRank"].isin(filters.allowed_ranks)]
    if filters.allowed_statuses and "taxonomicStatus" in out.columns:
        out = out[out["taxonomicStatus"].isin(filters.allowed_statuses)]
    selected = filters.select_columns(out.columns)
    if selected:
        out = out[selected]
    return out


def row_to_document(row: dict, cfg: IndexConfig) -> Optional[Document]:
    taxon_id = to_int_or_none(row.get("taxonID"))
    if taxon_id is None:
        return None

    doc = Document()
    doc.add_integer("taxon_id", taxon_id)

    # Name fields + edge prefixes
    canonical = row.get("canonicalName")
    if canonical is not None and not (hasattr(pd, "isna") and pd.isna(canonical)):
        canonical = str(canonical)
        doc.add_text("canonical_name", canonical)
        for gram in edge_ngrams(canonical, cfg.edge_min, cfg.edge_max):
            doc.add_text("canonical_edge", gram)

    scientific = row.get("scientificName")
    if scientific is not None and not (hasattr(pd, "isna") and pd.isna(scientific)):
        scientific = str(scientific)
        doc.add_text("scientific_name", scientific)
        for gram in edge_ngrams(scientific, cfg.edge_min, cfg.edge_max):
            doc.add_text("scientific_edge", gram)

    generic = row.get("genericName")
    if generic is not None and not (hasattr(pd, "isna") and pd.isna(generic)):
        generic = str(generic)
        doc.add_text("generic_name", generic)
        for gram in edge_ngrams(generic, cfg.edge_min, cfg.edge_max):
            doc.add_text("generic_edge", gram)

    vern_list = split_vernaculars(row.get("vernaculars_named"))
    for v in vern_list:
        doc.add_text("vernaculars", v)
        for gram in edge_ngrams(v, cfg.edge_min, cfg.edge_max):
            doc.add_text("vernacular_edge", gram)

    doc.add_text("name_text", make_name_text(row))

    rank = norm_keyword(row.get("taxonRank"))
    if rank:
        doc.add_text("taxon_rank", rank)
    status = norm_keyword(row.get("taxonomicStatus"))
    if status:
        doc.add_text("taxonomic_status", status)

    for fld in ["kingdom", "phylum", "class", "order", "family", "genus", "source"]:
        v = norm_keyword(row.get(fld))
        if v:
            doc.add_text(fld, v)

    authorship = row.get("scientificNameAuthorship")
    if authorship is not None and not (hasattr(pd, "isna") and pd.isna(authorship)):
        doc.add_text("scientific_name_authorship", str(authorship))

    description = row.get("curated_description")
    if description is not None and not (hasattr(pd, "isna") and pd.isna(description)):
        doc.add_text("curated_description", str(description))

    for src_col, dst in [
        ("lifeForm_curated", "lifeform_curated"),
        ("habitat_curated", "habitat_curated"),
        ("livingPeriod_curated", "livingperiod_curated"),
        ("nomenclaturalStatus", "nomenclatural_status"),
    ]:
        val = row.get(src_col)
        if val is not None and not (hasattr(pd, "isna") and pd.isna(val)):
            doc.add_text(dst, str(val))

    sid = to_int_or_none(row.get("species_id"))
    if sid is not None:
        doc.add_integer("species_id", sid)

    doc.add_integer("marine", to_bool01(row.get("marine_curated")))
    doc.add_integer("freshwater", to_bool01(row.get("freshwater_curated")))
    doc.add_integer("terrestrial", to_bool01(row.get("terrestrial_curated")))
    doc.add_integer("extinct", to_bool01(row.get("extinct_curated")))
    doc.add_integer("hybrid", to_bool01(row.get("hybrid_curated")))

    age = to_int_or_none(row.get("ageInDays_curated"))
    if age is not None:
        doc.add_integer("age_days", age)
    size = to_int_or_none(row.get("sizeInMillimeter_curated"))
    if size is not None:
        doc.add_integer("size_mm", size)
    mass = to_int_or_none(row.get("massInGram_curated"))
    if mass is not None:
        doc.add_integer("mass_g", mass)

    return doc


def build_index(
    config: IndexConfig | None = None,
    filters: FilterConfig | None = None,
    reset: bool = True,
) -> Index:
    """
    Build a Tantivy index from the curated CSV.

    A new index directory is created at config.index_dir. Set reset=False to
    avoid deleting an existing index folder.
    """
    cfg = config or IndexConfig.from_env()
    fil = filters or FilterConfig()

    if reset:
        shutil.rmtree(cfg.index_dir, ignore_errors=True)
    cfg.index_dir.mkdir(parents=True, exist_ok=True)

    schema = build_schema()
    index = tantivy.Index(schema=schema, path=str(cfg.index_dir))
    writer = index.writer(heap_size=cfg.heap_size_bytes, num_threads=cfg.num_threads)

    for chunk in pd.read_csv(cfg.csv_path, chunksize=cfg.chunksize):
        filtered = _filter_chunk(chunk, fil)
        for row in filtered.to_dict(orient="records"):
            doc = row_to_document(row, cfg)
            if doc is None:
                continue
            writer.add_document(doc)

    writer.commit()
    writer.wait_merging_threads()
    index.reload()
    return index
