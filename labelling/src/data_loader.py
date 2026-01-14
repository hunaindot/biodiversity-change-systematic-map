from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

import pandas as pd

from .config import DATASETS_DIR, DEFAULT_COLUMNS


def split_semicolon(value) -> List[str]:
    if pd.isna(value):
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def load_wos_excels(input_dir: Path, columns: Iterable[str] = DEFAULT_COLUMNS, limit: int | None = None) -> pd.DataFrame:
    """Read every .xls or .xlsx in a folder and return a combined dataframe."""
    paths = sorted(
        [path for pattern in ("*.xls", "*.xlsx") for path in Path(input_dir).glob(pattern)]
    )
    if not paths:
        raise FileNotFoundError(f"No .xls or .xlsx files found in {input_dir}")

    frames = []
    for path in paths:
        df = pd.read_excel(path)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    columns = [c for c in columns if c in combined.columns]
    subset = combined[columns].copy()
    subset.rename(columns={"UT (Unique WOS ID)": "UT"}, inplace=True)
    if "UT" not in subset.columns:
        raise KeyError("UT (Unique WOS ID) column not found in the input files.")
    subset["UT"] = subset["UT"].astype(str).str.strip()
    subset.drop_duplicates(subset=["UT"], inplace=True)
    if limit is not None:
        subset = subset.head(limit)
    return subset


def dataframe_to_documents(df: pd.DataFrame) -> list[dict]:
    documents = []
    for _, row in df.iterrows():
        documents.append(
            {
                "UT": str(row.get("UT", "")).strip(),
                "title": "" if pd.isna(row.get("Article Title")) else str(row["Article Title"]).strip(),
                "authors": split_semicolon(row.get("Authors")),
                "abstract": "" if pd.isna(row.get("Abstract")) else str(row["Abstract"]).strip(),
                "source": "" if pd.isna(row.get("Publisher")) else str(row["Publisher"]).strip(),
                "publication_year": "" if pd.isna(row.get("Publication Year")) else str(row["Publication Year"]).strip(),
                "wos_categories": split_semicolon(row.get("WoS Categories")),
                "doi": "" if pd.isna(row.get("DOI")) else str(row["DOI"]).strip(),
            }
        )
    return documents


def save_dataset(documents: list[dict], path: Path | None = None) -> Path:
    """Persist documents to JSON for downstream batch creation."""
    payload = {"documents": {doc["UT"]: doc for doc in documents}}
    path = path or DATASETS_DIR / "dataset.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return path


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
