"""
Step 4: Map each row's `hometown` text to latitude/longitude using a static
district-level gazetteer (bd_districts.csv). This is coarse (district centroid,
not exact village) — good enough for a weather join, since weather doesn't vary
meaningfully within a district on a given day.

If you need thana/upazila-level precision, extend bd_districts.csv with more
rows and match logic in `match_district()`.

Usage:
    python 4_geocode_enrich.py
Input:
    data/articles_extracted.jsonl
Output:
    data/articles_geocoded.jsonl
"""
import csv
import json
from pathlib import Path

IN_PATH = Path(__file__).parent / "data" / "articles_extracted.jsonl"
GAZETTEER_PATH = Path(__file__).parent / "bd_districts.csv"
OUT_PATH = Path(__file__).parent / "data" / "articles_geocoded.jsonl"


def load_gazetteer():
    with open(GAZETTEER_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def match_district(hometown, gazetteer):
    if not hometown:
        return None
    hometown_norm = hometown.strip()
    for row in gazetteer:
        if row["district_bn"] in hometown_norm or row["district_en"].lower() in hometown_norm.lower():
            return row
    return None


def main():
    gazetteer = load_gazetteer()

    with open(IN_PATH, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]

    unmatched = 0
    with open(OUT_PATH, "w", encoding="utf-8") as out:
        for row in rows:
            match = match_district(row.get("hometown"), gazetteer)
            if match:
                row["latitude"] = float(match["latitude"])
                row["longitude"] = float(match["longitude"])
            else:
                row["latitude"] = None
                row["longitude"] = None
                unmatched += 1
            out.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Saved geocoded rows to {OUT_PATH} ({unmatched} unmatched hometowns — "
          f"review these and extend bd_districts.csv as needed)")


if __name__ == "__main__":
    main()
