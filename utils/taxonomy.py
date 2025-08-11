import os
import sys
import zipfile
import sqlite3
import pandas as pd
import xml.etree.ElementTree as ET
from typing import Iterable, Optional, Tuple, List
from osfclient import OSF

def extract_dwc_archive() -> str:
    """
    Unzips the GBIF Darwin Core archive.

    Uses OSF as the single source of truth.
    - Looks for:   osf-data/gbif-taxonomy-backbone/backbone.zip
    - If missing:  suggests and downloads via OSF client (project 'sna2g', storage 'osfstorage')
    - Extracts to: osf-data/gbif-taxonomy-backbone/extracted/

    OSF auth token is read from the environment variable OSF_TOKEN (optional for public read).
    """
    # ---- Local OSF layout (your working place) ----
    download_root = "osf-data"
    subdir = "gbif-taxonomy-backbone"
    zip_name = "backbone.zip"

    default_zip = os.path.join(download_root, subdir, zip_name)
    default_extract = os.path.join(download_root, subdir, "extracted")

    zip_path = default_zip
    extract_to = default_extract

    # ---- If the zip isn't present locally, suggest and download from OSF ----
    if not os.path.exists(zip_path):
        print(
            "GBIF taxonomy backbone zip file not found locally.\n"
            f"Expected location: {zip_path}\n"
            "Suggesting download from OSF and proceeding to fetch via OSF client..."
        )

        # Your exact OSF setup as given
        osf_token = os.getenv("OSF_TOKEN")  # can be None for public projects (lower rate limit)
        osf = OSF(token=osf_token) if osf_token else OSF()
        project = osf.project("sna2g")
        store = project.storage("osfstorage")

        wanted_osf_path = "/gbif-taxonomy-backbone/backbone.zip"

        # Ensure parent dir exists
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)

        # Find + download the single file, with your size-check behavior
        found = False
        for f in store.files:
            if f.path == wanted_osf_path:
                found = True
                remote_size = getattr(f, "size", None)
                if os.path.exists(zip_path) and remote_size is not None:
                    if os.path.getsize(zip_path) == remote_size:
                        print(f"Skipping existing (size match): {zip_path}")
                        break
                    else:
                        print(f"Size mismatch — re-downloading: {zip_path}")

                print(f"Downloading: {f.path} ({remote_size or 'unknown'} bytes)")
                with open(zip_path, "wb") as out:
                    f.write_to(out)
                break

        if not found or not os.path.exists(zip_path):
            print("Could not obtain the GBIF backbone zip from OSF.")
            print(f"OSF path expected: {wanted_osf_path} (project 'sna2g', storage 'osfstorage')")
            print("Please check access or try again.")
            sys.exit(1)

    # ---- Extraction behavior unchanged ----
    if os.path.exists(extract_to) and os.listdir(extract_to):
        print(f"Extraction folder '{extract_to}' already exists and is not empty. Skipping extraction.")
        return extract_to

    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"Extracted Darwin Core archive to: {extract_to}")
    return extract_to


def load_taxonomy() -> None:
    """
    One-stop:
      1) extract archive (uses your OSF-backed extract_dwc_archive)
      2) read core taxon TSV as defined by meta.xml
      3) save to SQLite
    """

    db_path = "osf-data/gbif-taxonomy-backbone/database/taxon.db"
    table_name = "taxon"

    # 1) Ensure/extract
    extracted_folder = extract_dwc_archive()

    # 2) Resolve and read the core file via meta.xml
    meta_path = os.path.join(extracted_folder, "meta.xml")
    data_file, _columns = parse_meta_xml(meta_path)
    file_path = os.path.join(extracted_folder, data_file)

    try:
        df = pd.read_csv(
            file_path,
            sep="\t",
            dtype=str,
            low_memory=False,
            on_bad_lines="skip",
        )
        print(f"Loaded {len(df)} rows from {data_file}")
    except Exception as e:
        print(f"Failed to load data: {e}")
        raise

    # 3) Save to SQLite (inlined save_to_sqlite logic)
    if os.path.exists(db_path):
        print(f"Database already exists at '{db_path}'")
        return

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    finally:
        conn.close()

    print(f"Saved {len(df)} rows to table '{table_name}' in SQLite DB: '{db_path}'")
    print(f"SQLite database is available at '{db_path}' for use.")

def load_taxon_lineage_df(
    db_path: str = "osf-data/gbif-taxonomy-backbone/database/taxon.db",
    taxonomic_status: str = "accepted",
    seed_rank: str = "species",
    name_prefix: Optional[str] = None,      
    species_ids: Optional[Iterable[int]] = None
) -> pd.DataFrame:
    """
    Run a recursive lineage query and return a wide dataframe with:
      species_id, species_name, genus, family, "order", "class", phylum, kingdom, species
    """
       
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
      FROM taxon s
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
      FROM taxon p
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
    """

    with sqlite3.connect(db_path) as conn:
        taxon_df = pd.read_sql_query(sql_query, conn, params=params)

    return taxon_df

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