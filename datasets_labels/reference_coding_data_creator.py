import os
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

SOURCE = os.path.join(ROOT, "data/consistency-check-datasets/data-coding/reference_coding_dataset.xlsx")

SHEETS = [
    "S1) Benitez lopez et al",
    "S2) Jaureguiberry et al",
    "S3) Moullec et al",
    "S4) Urban et al",
    "S5) Wright et al",
    "S6) Lowery et al",
    "S7) Ridley et al",
    "S8) Keck et al",
    "S9) Pulido-Chadid et al",
]

BASE_COLS = ["Article Title", "Abstract", "DOI", "source", "UT (Unique WOS ID)"]

LABELS = [
    {
        "name": "L1) Driver",
        "cols": BASE_COLS + ["driver"],
        "out": os.path.join(ROOT, "data/labels/l1/L1) driver set.csv"),
    },
    {
        "name": "L2) Threats",
        "cols": BASE_COLS + ["threats_l0", "threats_l1"],
        "out": os.path.join(ROOT, "data/labels/l2/L2) threats set.csv"),
    },
    {
        "name": "L3) Geography",
        "cols": BASE_COLS + ["region", "sub-region", "country"],
        "out": os.path.join(ROOT, "data/labels/l3/L3) geography set.csv"),
    },
    {
        "name": "L4) Ecosystems",
        "cols": BASE_COLS + ["realm", "biome"],
        "out": os.path.join(ROOT, "data/labels/l4/L4) ecosystem set.csv"),
    },
    {
        "name": "L5) Study",
        "cols": BASE_COLS + ["study_design"],
        "out": os.path.join(ROOT, "data/labels/l5/L5) study set.csv"),
    },
    {
        "name": "L6) Taxa",
        "cols": BASE_COLS + ["kingdom", "phylum", "class", "order", "genus", "specie"],
        "out": os.path.join(ROOT, "data/labels/l6/L6) taxa set.csv"),
    },
]


def load_sheets(needed_cols):
    frames = []
    for sheet in SHEETS:
        df = pd.read_excel(SOURCE, sheet_name=sheet)
        present = [c for c in needed_cols if c in df.columns]
        label_cols = [c for c in present if c not in BASE_COLS]
        mask = df[label_cols].notna().any(axis=1)
        sub = df[present][mask].copy()
        print(f"  {sheet}: {len(sub)} records with label data")
        frames.append(sub)
    combined = pd.concat(frames, ignore_index=True)
    before = len(combined)
    combined = combined.drop_duplicates(subset="UT (Unique WOS ID)", keep="first")
    print(f"  → {before} rows before dedup, {len(combined)} after dedup on UT")
    no_abstract = combined["Abstract"].isna() | combined["Abstract"].astype(str).str.strip().eq("")
    if no_abstract.any():
        print(f"  → dropped {no_abstract.sum()} rows with empty abstract, {(~no_abstract).sum()} remaining")
    combined = combined[~no_abstract]
    return combined


def main():
    import sys
    filter_arg = sys.argv[1] if len(sys.argv) > 1 else None
    labels = LABELS
    if filter_arg:
        labels = [l for l in LABELS if filter_arg.lower() in l["name"].lower()]
        if not labels:
            print(f"No label matching '{filter_arg}'. Available: {[l['name'] for l in LABELS]}")
            sys.exit(1)
    for label in labels:
        print(f"\n=== {label['name']} ===")
        df = load_sheets(label["cols"])
        df.to_csv(label["out"], index=False)
        print(f"Saved {len(df)} rows → {label['out']}")


if __name__ == "__main__":
    main()
