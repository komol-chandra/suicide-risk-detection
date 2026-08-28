"""
Step 6: Merge the enriched rows into the final CSV with the exact column order
you specified. Also derives `age_group` from `age`, and reports basic
completeness stats so you can spot-check the pilot before scaling up.

Usage:
    python 6_merge_export.py
Input:
    data/articles_weathered.jsonl
Output:
    data/bd_suicide_dataset_pilot.csv
"""
import json
from pathlib import Path

import pandas as pd

from config import FINAL_COLUMNS

IN_PATH = Path(__file__).parent / "data" / "articles_weathered.jsonl"
OUT_PATH = Path(__file__).parent / "data" / "bd_suicide_dataset_pilot.csv"


def age_group(age):
    if age is None:
        return None
    if age < 13:
        return "child"
    if age < 20:
        return "teen"
    if age < 60:
        return "adult"
    return "elderly"


def main():
    with open(IN_PATH, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]

    df = pd.DataFrame(rows)
    df["age_group"] = df.get("age", pd.Series(dtype="float")).apply(age_group)

    for col in FINAL_COLUMNS:
        if col not in df.columns:
            df[col] = None

    df = df[FINAL_COLUMNS]
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Saved final dataset to {OUT_PATH} ({len(df)} rows)")
    print("\nCompleteness (% non-null) per column:")
    print((df.notna().mean() * 100).round(1).to_string())


if __name__ == "__main__":
    main()
