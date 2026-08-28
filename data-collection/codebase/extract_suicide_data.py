# -*- coding: utf-8 -*-
"""
extract_suicide_data.py

Parses locally-saved Bangladeshi news article HTML files (Prothom Alo,
Daily Star, etc.) about suicide incidents and extracts a structured CSV
for research purposes.

USAGE
-----
    python3 extract_suicide_data.py /path/to/html_folder output.csv

    /path/to/html_folder should contain one .html file per article
    (e.g. saved with "Save Page As" or downloaded via requests/wget).

WHAT THIS SCRIPT DOES AND DOES NOT DO
--------------------------------------
- It extracts fields that are usually stated explicitly in the article
  text (date, age, method, a coarse reason category, district-level
  location, profession category, mental-health / prior-attempt flags
  IF the article states them).
- It does NOT extract the victim's name, family members' names, or an
  exact street address / GPS point for the residence. Instead it emits
  an anonymous `case_id` and a district-level lat/long (centroid), plus
  the source URL so a specific case can always be traced back to its
  original public article if needed.
- Many of the requested columns (family_members, position_in_siblings,
  marital_status, duration_of_separation, financial_condition,
  previous_health_condition, previous_suicide_attempt) are rarely
  stated explicitly in a news report in a machine-parseable way.
  Rather than guessing and silently writing something that *looks*
  like a fact about a real dead person, the script leaves these blank
  and instead writes the most relevant sentence it found into an
  `_evidence_<column>` companion column, so a human coder can read
  the sentence and fill in the value. This is standard practice in
  media-content-analysis suicide research (a human-in-the-loop coding
  step) and avoids fabricating personal details about real people.
"""

import csv
import glob
import hashlib
import json
import os
import re
import sys
from datetime import datetime

from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# 1. District-level centroid lookup (approximate, public geographic data —
#    NOT an exact home address). Extend this as needed.
# ---------------------------------------------------------------------------
DISTRICT_CENTROIDS = {
    "ঢাকা": (23.8103, 90.4125), "মানিকগঞ্জ": (23.8617, 90.0047),
    "গাজীপুর": (24.0022, 90.4264), "নারায়ণগঞ্জ": (23.6238, 90.4990),
    "টাঙ্গাইল": (24.2513, 89.9167), "মুন্শিগঞ্জ": (23.5422, 90.5305),
    "চট্টগ্রাম": (22.3569, 91.7832), "কুমিল্লা": (23.4607, 91.1809),
    "কক্সবাজার": (21.4272, 92.0058), "রাজশাহী": (24.3745, 88.6042),
    "খুলনা": (22.8456, 89.5403), "বরিশাল": (22.7010, 90.3535),
    "সিলেট": (24.8949, 91.8687), "রংপুর": (25.7439, 89.2752),
    "ময়মনসিংহ": (24.7471, 90.4203),
    # add remaining districts as your dataset needs them
}

# ---------------------------------------------------------------------------
# 2. Keyword dictionaries used for coarse, category-level extraction only.
# ---------------------------------------------------------------------------
METHOD_KEYWORDS = {
    "hanging": ["ফাঁস দিয়ে", "ঝুলন্ত", "গলায় ফাঁস"],
    "poison": ["বিষপান", "বিষ খেয়ে", "কীটনাশক"],
    "train": ["ট্রেনে কাটা", "রেললাইনে"],
    "jump_water": ["নদীতে ঝাঁপ", "পুকুরে ঝাঁপ", "খালে ঝাঁপ"],
    "jump_height": ["ছাদ থেকে", "ভবন থেকে লাফ", "উঁচু থেকে লাফ"],
    "firearm": ["গুলি করে"],
    "self_immolation": ["আগুনে পুড়ে", "গায়ে আগুন"],
}

REASON_KEYWORDS = {
    "mental_health": ["মানসিক সমস্যা", "মানসিক অসুস্থতা", "বিষণ্নতা"],
    "family_conflict": ["পারিবারিক কলহ", "পারিবারিক অশান্তি"],
    "relationship": ["প্রেমঘটিত", "প্রেমের সম্পর্ক"],
    "exam_result": ["পরীক্ষার ফলাফল", "ফলাফল প্রকাশের পর"],
    "financial": ["আর্থিক সংকট", "ঋণের কারণে"],
    "domestic_abuse": ["যৌতুক", "নির্যাতনের"],
}

PROFESSION_KEYWORDS = {
    "student": ["ছাত্র", "ছাত্রী", "শিক্ষার্থী"],
    "teacher": ["শিক্ষক", "শিক্ষিকা"],
    "housewife": ["গৃহবধূ"],
    "business": ["ব্যবসায়ী"],
    "service_holder": ["চাকরিজীবী", "কর্মকর্তা"],
    "farmer": ["কৃষক"],
    "garments_worker": ["পোশাক শ্রমিক", "গার্মেন্টস কর্মী"],
}

GENDER_HINTS = {
    "female": ["শিক্ষিকা", "গৃহবধূ", "ছাত্রী", "স্ত্রী", "কন্যা", "নারী", "মেয়ে"],
    "male": ["শিক্ষক", "ছাত্র", "স্বামী", "পুত্র", "পুরুষ", "ছেলে"],
}

PREVIOUS_ATTEMPT_PHRASES = ["পূর্বে আত্মহত্যার চেষ্টা", "আগেও আত্মহত্যার চেষ্টা", "বারবার আত্মহত্যার চেষ্টা"]

BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def bn_to_en_digits(s):
    return s.translate(BN_DIGITS)


# ---------------------------------------------------------------------------
# 3. Core parsing
# ---------------------------------------------------------------------------
def load_article(path):
    with open(path, encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")

    # canonical URL (used as data_source, and as the seed for case_id)
    link = soup.find("link", rel="canonical")
    og_url = soup.find("meta", property="og:url")
    url = (link.get("href") if link else None) or (og_url.get("content") if og_url else None) or os.path.basename(path)

    # published date, from JSON-LD if present
    pub_date = None
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string)
        except (TypeError, ValueError):
            continue
        if isinstance(data, dict) and data.get("datePublished"):
            pub_date = data["datePublished"]
            break

    # article body text — adjust selectors per outlet if you add new sources
    body_selectors = [".story-element-text", ".story-content", "article", "[itemprop=articleBody]"]
    paragraphs = []
    for sel in body_selectors:
        found = soup.select(sel)
        if found:
            paragraphs = [p.get_text(" ", strip=True) for p in found]
            break
    full_text = "\n".join(paragraphs)

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    return {"url": url, "pub_date": pub_date, "title": title, "text": full_text}


def find_first(keyword_dict, text):
    """Return (category, matched_keyword) for the first hit, or (None, None)."""
    for category, keywords in keyword_dict.items():
        for kw in keywords:
            if kw in text:
                return category, kw
    return None, None


def evidence_sentence(text, keyword):
    """Return the sentence containing `keyword`, for human review."""
    if not keyword:
        return ""
    # naive Bangla sentence split on দাঁড়ি (।) and periods
    sentences = re.split(r"(?<=[।.!?])\s+", text)
    for s in sentences:
        if keyword in s:
            return s.strip()
    return ""


def extract_age(text):
    # common pattern: নাম (৭১) — an age in parentheses right after a name
    m = re.search(r"\(([০-৯0-9]{1,3})\)", text)
    if m:
        return int(bn_to_en_digits(m.group(1)))
    m = re.search(r"বয়স[ঃ:]?\s*([০-৯0-9]{1,3})", text)
    if m:
        return int(bn_to_en_digits(m.group(1)))
    return None


def age_group(age):
    if age is None:
        return None
    bands = [(0, 12, "child"), (13, 19, "teen"), (20, 29, "20s"),
             (30, 39, "30s"), (40, 59, "40-59"), (60, 200, "60+")]
    for lo, hi, label in bands:
        if lo <= age <= hi:
            return label
    return None


def victim_sentence(text):
    """Return the sentence introducing the victim (the one holding the
    age-in-parentheses), since gender/profession keywords found elsewhere
    in the article often describe other people (spouse, child, witness)."""
    m = re.search(r"\([০-৯0-9]{1,3}\)", text)
    if not m:
        return text.split("\n", 1)[0] if text else ""
    sentences = re.split(r"(?<=[।.!?])\s+", text)
    pos = 0
    for s in sentences:
        pos += len(s) + 1
        if pos >= m.start():
            return s
    return sentences[0] if sentences else text


def extract_location(text):
    for district in DISTRICT_CENTROIDS:
        if district in text:
            lat, lon = DISTRICT_CENTROIDS[district]
            return district, lat, lon
    return None, None, None


def make_case_id(url):
    return "case_" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]


def to_unix(pub_date):
    if not pub_date:
        return None
    try:
        dt = datetime.fromisoformat(pub_date)
        return int(dt.timestamp())
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# 4. Row builder
# ---------------------------------------------------------------------------
FIELDNAMES = [
    "case_id", "data_source", "age", "age_group", "gender",
    "profession_group", "hometown", "latitude", "longitude",
    "reason", "reason_description", "method",
    "previous_suicide_attempt", "suicide_date", "unix_time",
    # manual-coding columns (left for a human coder to fill in)
    "family_members", "position_in_siblings", "maritual_status",
    "duration_of_separataion", "financial_condition",
    "previous_health_condition",
    # evidence snippets to speed up manual coding
    "_evidence_reason", "_evidence_method", "_evidence_previous_attempt",
]


def build_row(article):
    text = article["text"]
    url = article["url"]

    age = extract_age(text)
    victim_ctx = victim_sentence(text)
    gender_cat, _ = find_first(GENDER_HINTS, victim_ctx)
    if gender_cat is None:
        gender_cat, _ = find_first(GENDER_HINTS, text)
    profession_cat, _ = find_first(PROFESSION_KEYWORDS, victim_ctx)
    if profession_cat is None:
        profession_cat, _ = find_first(PROFESSION_KEYWORDS, text)
    reason_cat, reason_kw = find_first(REASON_KEYWORDS, text)
    method_cat, method_kw = find_first(METHOD_KEYWORDS, text)
    district, lat, lon = extract_location(text)

    prev_attempt = "yes" if any(p in text for p in PREVIOUS_ATTEMPT_PHRASES) else "unclear"
    prev_attempt_kw = next((p for p in PREVIOUS_ATTEMPT_PHRASES if p in text), None)

    unix_time = to_unix(article["pub_date"])

    return {
        "case_id": make_case_id(url),
        "data_source": url,
        "age": age,
        "age_group": age_group(age),
        "gender": gender_cat,
        "profession_group": profession_cat,
        "hometown": district,
        "latitude": lat,
        "longitude": lon,
        "reason": reason_cat,
        "reason_description": "",  # leave for human coder — free text
        "method": method_cat,
        "previous_suicide_attempt": prev_attempt,
        "suicide_date": article["pub_date"],
        "unix_time": unix_time,
        "family_members": "",
        "position_in_siblings": "",
        "maritual_status": "",
        "duration_of_separataion": "",
        "financial_condition": "",
        "previous_health_condition": "",
        "_evidence_reason": evidence_sentence(text, reason_kw),
        "_evidence_method": evidence_sentence(text, method_kw),
        "_evidence_previous_attempt": evidence_sentence(text, prev_attempt_kw),
    }


# ---------------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) != 3:
        print("Usage: python3 extract_suicide_data.py <html_folder_or_file> <output.csv>")
        sys.exit(1)

    src, out_csv = sys.argv[1], sys.argv[2]
    paths = [src] if os.path.isfile(src) else sorted(glob.glob(os.path.join(src, "*.html")))

    rows = []
    for path in paths:
        try:
            article = load_article(path)
            rows.append(build_row(article))
        except Exception as e:
            print(f"[warn] failed on {path}: {e}")

    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} row(s) to {out_csv}")
    print("Columns needing manual review: family_members, position_in_siblings, "
          "maritual_status, duration_of_separataion, financial_condition, "
          "previous_health_condition, reason_description "
          "(see the _evidence_* columns for the source sentence).")


if __name__ == "__main__":
    main()
