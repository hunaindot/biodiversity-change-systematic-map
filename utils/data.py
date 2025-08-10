import os
import pandas as pd
import random
import textwrap
from typing import Optional, Iterable

def _get_bool_env(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None: return default
    return str(v).strip().lower() in {"1","true","yes","y","on"}

def _get_int_env(name: str, default: Optional[int]) -> Optional[int]:
    v = os.getenv(name)
    if v is None or str(v).strip()=="":
        return default
    try:
        return int(v)
    except ValueError:
        return default

def print_random_record(df):
    idx = random.randint(0, len(df) - 1)
    row = df.iloc[idx]
    fields = [
        ("UT (Unique WOS ID)", row.get("UT (Unique WOS ID)", "")),
        ("Article Title", row.get("Article Title", "")),
        ("Abstract", row.get("Abstract", "")),
        ("message.content", row.get("message.content", ""))
    ]
    for label, value in fields:
        print(f"{label}:")
        print(textwrap.fill(str(value), width=80))
        print("-" * 40)

def load_data(
    csv_path: Optional[str] = None,
    sample_n: Optional[int] = None,
    sample: Optional[bool] = None,
    required_text_col: Optional[str] = None,
    allow_download: Optional[bool] = True,
    download_url: Optional[str] = None,
    random_seed: Optional[int] = None,
    drop_duplicates: Optional[bool] = None,
    verbose: Optional[bool] = None,
) -> tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Load the curated dataset from local CSV; if missing and allowed, download and cache.

    Env-backed defaults:
      DATA_CSV_PATH, DATA_DOWNLOAD_URL, DATA_ALLOW_DOWNLOAD
      DATA_REQUIRED_TEXT_COL, DATA_DROP_DUPLICATES
      DATA_SAMPLE, DATA_SAMPLE_N, DATA_RANDOM_SEED, DATA_VERBOSE
    """
    # Resolve defaults from env
    csv_path         = csv_path or os.getenv("DATA_CSV_PATH", "data/curated_data.csv")
    download_url     = download_url or os.getenv("DATA_DOWNLOAD_URL",
                         "https://huggingface.co/datasets/Hunain505/biodiversity-research-text/resolve/main/dataset/curated_data/data.csv")
    allow_download   = allow_download if allow_download is not None else _get_bool_env("DATA_ALLOW_DOWNLOAD", True)
    required_text_col= required_text_col or os.getenv("DATA_REQUIRED_TEXT_COL", "Abstract")
    drop_duplicates  = drop_duplicates if drop_duplicates is not None else _get_bool_env("DATA_DROP_DUPLICATES", True)
    sample           = sample if sample is not None else _get_bool_env("DATA_SAMPLE", True)
    sample_n         = sample_n if sample_n is not None else _get_int_env("DATA_SAMPLE_N", 1000)
    random_seed      = random_seed if random_seed is not None else _get_int_env("DATA_RANDOM_SEED", 42)
    verbose          = verbose if verbose is not None else _get_bool_env("DATA_VERBOSE", True)

    # Ensure directory exists
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)

    # Load (or download+cache)
    if os.path.exists(csv_path):
        if verbose: print(f"Loading dataset from local file: {csv_path}")
        df = pd.read_csv(csv_path, low_memory=False)
    else:
        if not allow_download:
            raise FileNotFoundError(
                f"Local file not found at {csv_path} and DATA_ALLOW_DOWNLOAD=false. "
                f"Either place the file locally or enable download."
            )
        if verbose:
            print("Local file not found. Downloading dataset…")
            print(f"Source: {download_url}")
        df = pd.read_csv(download_url, low_memory=False)
        df.to_csv(csv_path, index=False)
        if verbose: print(f"Dataset saved to {csv_path}")

    # Quick summary (robust to missing column)
    wos_col = "UT (Unique WOS ID)"
    row_count = len(df)
    wos_count = df[wos_col].count() if wos_col in df.columns else None
    wos_distinct = df[wos_col].nunique() if wos_col in df.columns else None
    dup_count = df.duplicated().sum()
    if verbose:
        print(f"Dataset shape: {df.shape}")
        print(" Count Summary :", {
            "row_count": row_count,
            "web_of_science_record_count": wos_count,
            "web_of_science_record_distinct_count": wos_distinct,
            "duplicated_row_count": dup_count
        })

    # De-dup (optional)
    if drop_duplicates:
        before = len(df)
        df = df.drop_duplicates()
        if verbose:
            print(f"Dropped {before - len(df)} duplicated rows. Remaining rows: {len(df)}")

    # Require non-null text column (if present)
    if required_text_col:
        if required_text_col in df.columns:
            before = len(df)
            df = df.dropna(subset=[required_text_col])
            if verbose:
                print(f"Dropped {before - len(df)} rows without {required_text_col}. Remaining rows: {len(df)}")
        else:
            if verbose:
                print(f"Warning: required_text_col '{required_text_col}' not found; skipping null filter.")

    # Optional sampling
    df_sample = None
    if sample:
        n = min(sample_n or 0, len(df)) if sample_n else min(1000, len(df))
        if n > 0:
            if verbose: print(f"Sampling {n} rows from the dataset of length {len(df)} (seed={random_seed}).")
            df_sample = df.sample(n=n, random_state=random_seed)

    # Null profile (verbose only)
    if verbose:
        null_counts = df.isnull().sum()
        null_cols = null_counts[null_counts > 0].sort_values(ascending=False)
        print(f" {len(null_cols)} Columns with null values:\n{null_cols}")

    return df, df_sample
