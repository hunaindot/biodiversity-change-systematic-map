from __future__ import annotations

import pandas as pd


def col_examples(df: pd.DataFrame, max_len: int = 80) -> dict:
    """Return {col: first_non_null_value} for each column, truncated for readability."""
    out = {}
    for col in df.columns:
        vals = df[col].dropna()
        if vals.empty:
            out[col] = None
            continue
        v = vals.iloc[0]
        if hasattr(v, "item"):  # numpy scalar → Python native
            v = v.item()
        if not isinstance(v, (str, int, float, bool, type(None))):
            v = str(v)
        if isinstance(v, str) and len(v) > max_len:
            v = v[:max_len] + "..."
        out[col] = v
    return out
