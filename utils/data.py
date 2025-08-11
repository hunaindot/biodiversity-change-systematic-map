import os
import pandas as pd
import random
import textwrap
from typing import Optional
from osfclient import OSF

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
    csv_path: str = "osf-data/data.csv",
    sample_n: int = 1000,
    sample: bool = True,
    required_text_col: str = "Abstract",
    random_seed: int = 42,
    drop_duplicates: bool = True,
    verbose: bool = True,
) -> tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Load the curated dataset from local CSV at osf-data/data.csv (by default).
    If the file is missing, download it from OSF and cache locally.
    """
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)

    # Load (or OSF download + cache)
    if os.path.exists(csv_path):
        if verbose: print(f"Loading dataset from local file: {csv_path}")
        df = pd.read_csv(csv_path, low_memory=False)
    else:
        if verbose:
            print("Local file not found. Downloading dataset from OSF…")

        # OSF setup
        try:
            from osfclient import OSF
        except Exception as e:
            raise ImportError(
                "The 'osfclient' package is required for OSF downloads. "
                "Install it with: pip install osfclient"
            ) from e

        token = os.getenv("OSF_TOKEN", None)
        project_id = os.getenv("OSF_PROJECT", "sna2g")
        if verbose:
            print(f"OSF project: {project_id} (auth={'token' if token else 'anonymous'})")

        osf = OSF(token=token) if token else OSF()
        project = osf.project(project_id)
        store = project.storage("osfstorage")

        target_osf_path = "/web-of-science/curated/data.csv"

        # Find the CSV in OSF and write directly to csv_path
        csv_node = None
        for f in store.files:
            if f.path == target_osf_path:
                csv_node = f
                break

        if csv_node is None:
            raise FileNotFoundError(
                f"Couldn't find '{target_osf_path}' in OSF project '{project_id}'. "
                "Verify the path or project id."
            )

        if verbose:
            size = getattr(csv_node, "size", None)
            print(f"Downloading: {target_osf_path} ({size or 'unknown'} bytes)")

        with open(csv_path, "wb") as out:
            csv_node.write_to(out)

        if verbose: print(f"Dataset saved to {csv_path}")
        df = pd.read_csv(csv_path, low_memory=False)

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