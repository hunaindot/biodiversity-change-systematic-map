import os
import sys
import zipfile
import sqlite3
import pandas as pd
import xml.etree.ElementTree as ET
from typing import Iterable, Optional

def _get_bool_env(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}

def _get_int_env(name: str, default: Optional[int]) -> Optional[int]:
    val = os.getenv(name)
    if val is None or str(val).strip() == "":
        return default
    try:
        return int(val)
    except ValueError:
        return default

def extract_dwc_archive(
    zip_path: Optional[str] = None,
    extract_to: Optional[str] = None,
    landing_url: Optional[str] = None,
    download_url: Optional[str] = None,
) -> str:
    """
    Unzips the GBIF Darwin Core archive.

    Defaults come from env:
      GBIF_ZIP_PATH, GBIF_EXTRACT_DIR, GBIF_BACKBONE_LANDING_URL, GBIF_BACKBONE_ZIP_URL
    """
    zip_path = zip_path or os.getenv("GBIF_ZIP_PATH", "gbif_taxonomy/source_files/backbone.zip")
    extract_to = extract_to or os.getenv("GBIF_EXTRACT_DIR", "gbif_taxonomy/extracted")
    landing_url = landing_url or os.getenv("GBIF_BACKBONE_LANDING_URL",
                                           "https://www.gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c#dataDescription")
    download_url = download_url or os.getenv("GBIF_BACKBONE_ZIP_URL",
                                             "https://hosted-datasets.gbif.org/datasets/backbone/current/backbone.zip")

    if not os.path.exists(zip_path):
        print("GBIF taxonomy backbone zip file not found.")
        print("Please download it manually from:")
        print(f"URL: {landing_url}")
        print(f"Direct download link: {download_url}")
        print(f"Expected location: {zip_path}")
        sys.exit(1)

    if os.path.exists(extract_to) and os.listdir(extract_to):
        print(f"Extraction folder '{extract_to}' already exists and is not empty. Skipping extraction.")
        return extract_to

    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"Extracted Darwin Core archive to: {extract_to}")
    return extract_to

def parse_meta_xml(meta_path: str):
    tree = ET.parse(meta_path)
    root = tree.getroot()
    core = root.find('{http://rs.tdwg.org/dwc/text/}core')

    location_element = core.find('{http://rs.tdwg.org/dwc/text/}files/{http://rs.tdwg.org/dwc/text/}location')
    file_location = location_element.text.strip()

    fields = core.findall('{http://rs.tdwg.org/dwc/text/}field')
    field_names = [field.attrib['term'].split('/')[-1] for field in fields]

    id_field = core.find('{http://rs.tdwg.org/dwc/text/}id')
    if id_field is not None:
        id_index = int(id_field.attrib['index'])
        field_names.insert(id_index, 'taxonID')  # Ensure ID column is preserved

    return file_location, field_names

def load_taxon_data(folder_path: Optional[str] = None) -> pd.DataFrame:
    """
    Reads the core taxon TSV described by meta.xml.
    Default folder_path from env: GBIF_EXTRACT_DIR
    """
    folder_path = folder_path or os.getenv("GBIF_EXTRACT_DIR", "gbif_taxonomy/extracted")
    meta_path = os.path.join(folder_path, 'meta.xml')
    data_file, _columns = parse_meta_xml(meta_path)
    file_path = os.path.join(folder_path, data_file)

    try:
        df = pd.read_csv(
            file_path,
            sep='\t',
            dtype=str,
            low_memory=False,
            on_bad_lines='skip'
        )
        print(f"Loaded {len(df)} rows from {data_file}")
    except Exception as e:
        print(f"Failed to load data: {e}")
        raise
    return df

def save_to_sqlite(
    df: pd.DataFrame,
    db_path: Optional[str] = None,
    table_name: Optional[str] = None,
    overwrite: Optional[bool] = None,
) -> None:
    """
    Writes the DataFrame into SQLite.

    Defaults from env:
      GBIF_DB_PATH, GBIF_TAXON_TABLE, GBIF_DB_OVERWRITE
    """
    db_path   = db_path or os.getenv("GBIF_DB_PATH", "gbif_taxonomy/database/taxon.db")
    table_name = table_name or os.getenv("GBIF_TAXON_TABLE", "taxon")
    if overwrite is None:
        overwrite = _get_bool_env("GBIF_DB_OVERWRITE", default=False)
        
    if os.path.exists(db_path) and not overwrite:
        print(f"Database already exists at '{db_path}'. Skipping save (set GBIF_DB_OVERWRITE=true to overwrite).")
        return

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        if_exists = 'replace' if overwrite else 'fail'
        if if_exists == 'fail' and os.path.exists(db_path):
            # If file exists and overwrite=False, we already returned above.
            pass
        df.to_sql(table_name, conn, if_exists='replace', index=False)  # replace to ensure a clean table
    finally:
        conn.close()
    print(f"Saved {len(df)} records to SQLite database: {db_path} (table '{table_name}')")

def load_taxonomy(
    zip_path: Optional[str] = None,
    extract_to: Optional[str] = None,
    db_path: Optional[str] = None,
    overwrite: Optional[bool] = None,
) -> None:
    """
    High-level: extract archive -> load taxon TSV -> save to SQLite.

    Defaults from env: GBIF_ZIP_PATH, GBIF_EXTRACT_DIR, GBIF_DB_PATH, GBIF_DB_OVERWRITE
    """
    extracted_folder = extract_dwc_archive(zip_path=zip_path, extract_to=extract_to)
    df = load_taxon_data(extracted_folder)
    save_to_sqlite(df, db_path=db_path, overwrite=overwrite)
    final_db_path = db_path or os.getenv("GBIF_DB_PATH", "gbif_taxonomy/database/taxon.db")
    print(f"SQLite database is available at '{final_db_path}' for use.")

def load_taxon_lineage_df(
    db_path: Optional[str] = None,
    taxonomic_status: Optional[str] = None,
    seed_rank: Optional[str] = None,
    name_prefix: Optional[str] = None,            # per-call filter (keep as arg)
    species_ids: Optional[Iterable[int]] = None,  # per-call filter (keep as arg)
    # order_by: Optional[str] = None,               # can be env-backed default
    limit: Optional[int] = None,                  # can be env-backed default
) -> pd.DataFrame:
    """
    Run a recursive lineage query and return a wide dataframe with:
      species_id, species_name, genus, family, "order", "class", phylum, kingdom, species

    Defaults from env:
      GBIF_DB_PATH, DEFAULT_TAXONOMIC_STATUS, DEFAULT_SEED_RANK, DEFAULT_ORDER_BY, DEFAULT_QUERY_LIMIT
    """
    db_path = db_path or os.getenv("GBIF_DB_PATH", "gbif_taxonomy/database/taxon.db")
    taxonomic_status = (taxonomic_status
                        or os.getenv("DEFAULT_TAXONOMIC_STATUS", "accepted"))
    seed_rank = seed_rank or os.getenv("DEFAULT_SEED_RANK", "species")
    # order_by = order_by or os.getenv("DEFAULT_ORDER_BY", "species_name")
    if limit is None:
        limit = _get_int_env("DEFAULT_QUERY_LIMIT", None)

    # allowed_order = {"species_name", "species_id"}
    # if order_by not in allowed_order:
    #     raise ValueError(f"order_by must be one of {allowed_order}")

    # Dynamic filters for the seed (species) set
    seed_filters_sql = ["s.taxonomicStatus = ?", "LOWER(s.taxonRank) = LOWER(?)"]
    params = [taxonomic_status, seed_rank]

    if name_prefix:
        seed_filters_sql.append("s.scientificName LIKE ?")
        params.append(f"{name_prefix}%")

    placeholders = ""
    if species_ids:
        species_ids = list(species_ids)
        if len(species_ids) == 0:
            return pd.DataFrame(columns=[
                "species_id","species_name","genus","family","order","class","phylum","kingdom","species"
            ])
        placeholders = ",".join(["?"] * len(species_ids))
        seed_filters_sql.append(f"s.taxonID IN ({placeholders})")
        params.extend(species_ids)

    limit_clause = ""
    if limit is not None:
        limit_clause = " LIMIT ?"
        params.append(int(limit))

    sql_query = f"""
    WITH RECURSIVE lineage AS (
      SELECT
          s.taxonID            AS species_id,
          s.scientificName     AS species_name,
          s.taxonID            AS taxonID,
          s.parentNameUsageID  AS parentNameUsageID,
          s.scientificName     AS scientificName,
          s.taxonRank          AS taxonRank,
          0                    AS depth,
          '/' || s.taxonID || '/' AS path
      FROM {os.getenv("GBIF_TAXON_TABLE", "taxon")} s
      WHERE {' AND '.join(seed_filters_sql)}

      UNION ALL

      SELECT
          l.species_id,
          l.species_name,
          p.taxonID,
          p.parentNameUsageID,
          p.scientificName,
          p.taxonRank,
          l.depth + 1,
          l.path || p.taxonID || '/'
      FROM {os.getenv("GBIF_TAXON_TABLE", "taxon")} p
      JOIN lineage l
        ON p.taxonID = l.parentNameUsageID
      WHERE INSTR(l.path, '/' || p.taxonID || '/') = 0
    )
    SELECT
      species_id,
      species_name,
      MAX(CASE WHEN LOWER(taxonRank) = 'genus'   THEN scientificName END) AS genus,
      MAX(CASE WHEN LOWER(taxonRank) = 'family'  THEN scientificName END) AS family,
      MAX(CASE WHEN LOWER(taxonRank) = 'order'   THEN scientificName END) AS "order",
      MAX(CASE WHEN LOWER(taxonRank) IN ('class','classis') THEN scientificName END) AS "class",
      MAX(CASE WHEN LOWER(taxonRank) IN ('phylum','division') THEN scientificName END) AS phylum,
      MAX(CASE WHEN LOWER(taxonRank) = 'kingdom' THEN scientificName END) AS kingdom,
      MAX(CASE WHEN LOWER(taxonRank) = 'species' THEN scientificName END) AS species
    FROM lineage
    GROUP BY species_id, species_name
    {limit_clause};
    """

    with sqlite3.connect(db_path) as conn:
        taxon_df = pd.read_sql_query(sql_query, conn, params=params)

    return taxon_df

