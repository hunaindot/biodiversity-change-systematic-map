from __future__ import annotations

import tantivy
from tantivy import SchemaBuilder


def build_schema() -> tantivy.Schema:
    sb = SchemaBuilder()

    # Primary ID
    sb.add_integer_field("taxon_id", indexed=True, stored=True, fast=True)

    # Optional numeric fields
    sb.add_integer_field("species_id", indexed=False, stored=True, fast=True)

    # Analyzed name fields (tokenized)
    sb.add_text_field("canonical_name", stored=True, tokenizer_name="default")
    sb.add_text_field("scientific_name", stored=True, tokenizer_name="default", fast=True)
    sb.add_text_field("generic_name", stored=True, tokenizer_name="default")
    sb.add_text_field("vernaculars", stored=True, tokenizer_name="default")
    sb.add_text_field("name_text", tokenizer_name="default")  # not stored

    # Edge prefix fields (indexed; not stored)
    sb.add_text_field("canonical_edge", tokenizer_name="default")
    sb.add_text_field("scientific_edge", tokenizer_name="default")
    sb.add_text_field("generic_edge", tokenizer_name="default")
    sb.add_text_field("vernacular_edge", tokenizer_name="default")

    # Keyword-ish fields (exact-ish) using raw tokenizer
    sb.add_text_field("taxon_rank", stored=True, tokenizer_name="raw", fast=True)
    sb.add_text_field("taxonomic_status", stored=True, tokenizer_name="raw", fast=True)
    for fld in ["kingdom", "phylum", "class", "order", "family", "genus", "source"]:
        sb.add_text_field(fld, stored=True, tokenizer_name="raw", fast=True)

    # Flags / numeric curated
    for fld in ["marine", "freshwater", "terrestrial", "extinct", "hybrid"]:
        sb.add_integer_field(fld, indexed=False, stored=True, fast=True)
    for fld in ["age_days", "size_mm", "mass_g"]:
        sb.add_integer_field(fld, indexed=False, stored=True, fast=True)

    # Stored text fields
    sb.add_text_field("curated_description", stored=True, tokenizer_name="default")
    sb.add_text_field("scientific_name_authorship", stored=True, tokenizer_name="default")
    sb.add_text_field("lifeform_curated", stored=True, tokenizer_name="default")
    sb.add_text_field("habitat_curated", stored=True, tokenizer_name="default")
    sb.add_text_field("livingperiod_curated", stored=True, tokenizer_name="default")
    sb.add_text_field("nomenclatural_status", stored=True, tokenizer_name="default")

    return sb.build()
