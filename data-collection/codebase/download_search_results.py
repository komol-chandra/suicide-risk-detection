# -*- coding: utf-8 -*-
"""
download_search_results.py

Given a Google Custom Search (CSE) results-page URL for one Bangladeshi
newspaper's site search (the kind produced by "site:prothomalo.com
আত্মহত্যা" style queries, e.g. prothomalo/thedailystar/banglanews24/
kalerkantho/jugantor/ittefaq/samakal/bd-pratidin's own search box), this
script:

  1. Renders the search-results widget with Playwright (it's a client-side
     Google CSE embed, not a plain URL/API like prothomalo's own search),
     paginates through every results page, and collects each hit's URL,
     title and snippet.
  2. Downloads each article's full HTML (plain HTTP first; falls back to a
     rendered fetch only if the plain fetch looks incomplete/JS-gated).
  3. Parses each article using the SAME rule-based keyword extraction as
     extract_suicide_data.py (imported, not duplicated) and writes a
     structured CSV using the extended multi-outlet schema in schema.py.

USAGE
-----
    python3 download_search_results.py "<google-cse-search-url>" <folder_name>

    folder_name is a short label for this run/source, e.g. "banglanews24"
    or "prothomalo-2025". It becomes:
      data-collection/input/<folder_name>/       raw HTML (gitignored)
      data-collection/database/<folder_name>/    suicide_data.csv + logs

Resumable: re-running skips articles already saved to disk. Delete
data-collection/input/<folder_name>/_index.csv to force a fresh harvest of
the search results (e.g. to pick up newly published articles).

A NOTE ON SITES THAT BLOCK AUTOMATED FETCHES
---------------------------------------------
Some of these outlets (banglanews24.com, kalerkantho.com, jugantor.com,
bd-pratidin.com at the time this was written) serve a bot-challenge page
("Just a moment...", HTTP 403, `<meta name="robots" content="noindex,
nofollow">`) to both plain HTTP clients and headless-browser requests for
their article pages. This script does NOT attempt to defeat that challenge
(no stealth/fingerprint-spoofing) — a case that hits it is recorded with
extraction_status="blocked" (case_id, source_name, article_url, title and
snippet from the search result are still kept) so you can see exactly what
needs a manual visit instead of it silently vanishing from the dataset.

ANONYMIZATION CONVENTION (see ../../CLAUDE.md) — unchanged from
extract_suicide_data.py: no victim names, no exact addresses. case_id is a
hash of the article URL; hometown is a district-level centroid only.
"""

import csv
import datetime
import hashlib
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema import FIELDNAMES  # noqa: E402
import extract_suicide_data as ext  # noqa: E402  (reused keyword-extraction logic)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

REQUEST_DELAY_SECONDS = 1.0     # politeness delay between article fetches
MAX_SEARCH_PAGES = 20           # Google CSE free tier tops out well below this
SEARCH_PAGE_LOAD_WAIT_MS = 2500

BLOCKED_TITLE_MARKERS = ["Just a moment", "Attention Required", "Access denied",
                          "403 Forbidden", "Are you a human"]

HERE = Path(__file__).resolve().parent
DATA_COLLECTION_DIR = HERE.parent

BODY_SELECTORS = [
    ".story-element-text",   # prothomalo (Quintype)
    ".story-content",
    ".dNewsDesc",             # samakal
    ".newsDetail", ".news-details", ".news_details",
    ".details-content", ".detailsContent",
    "[itemprop=articleBody]",
    "article",
]


# ---------------------------------------------------------------------------
# Search-results harvesting (Playwright — Google CSE is a client-rendered
# widget, no stable public JSON endpoint like prothomalo's own search).
# ---------------------------------------------------------------------------
def harvest_search_results(search_url):
    from playwright.sync_api import sync_playwright

    hits = {}  # url -> {"title": ..., "snippet": ...}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(user_agent=UA, viewport={"width": 1280, "height": 900})
        page.goto(search_url, timeout=45000, wait_until="domcontentloaded")
        page.wait_for_timeout(SEARCH_PAGE_LOAD_WAIT_MS)

        for page_num in range(1, MAX_SEARCH_PAGES + 1):
            soup = BeautifulSoup(page.content(), "html.parser")
            results = soup.select(".gsc-webResult")
            before = len(hits)
            for r in results:
                a = r.select_one("a.gs-title")
                if not a or not a.get("href"):
                    continue
                snippet_el = r.select_one(".gs-snippet")
                hits[a["href"]] = {
                    "title": a.get_text(" ", strip=True),
                    "snippet": snippet_el.get_text(" ", strip=True) if snippet_el else "",
                }
            print(f"[search] page {page_num}: {len(hits)} unique hits so far "
                  f"(+{len(hits) - before})")

            buttons = page.query_selector_all(".gsc-cursor-page")
            if page_num >= len(buttons) or not buttons:
                break
            buttons[page_num].click()  # buttons[0]=page1 ... click the next one
            page.wait_for_timeout(SEARCH_PAGE_LOAD_WAIT_MS)

        browser.close()
    return hits


# ---------------------------------------------------------------------------
# Article fetching
# ---------------------------------------------------------------------------
def looks_blocked(status_code, html):
    if status_code in (403, 429, 503):
        return True
    head = html[:2000]
    return any(marker in head for marker in BLOCKED_TITLE_MARKERS)


def fetch_article_html(url):
    """Returns (html_or_None, status) where status is 'ok' or 'blocked'."""
    try:
        r = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "bn,en;q=0.8"},
                          timeout=20)
        if not looks_blocked(r.status_code, r.text) and len(r.text) > 500:
            return r.text, "ok"
    except requests.RequestException:
        pass

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(user_agent=UA)
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()
        if not looks_blocked(200, html) and len(html) > 500:
            return html, "ok"
    except Exception:
        pass

    return None, "blocked"


# ---------------------------------------------------------------------------
# Parsing (reuses extract_suicide_data.py's keyword logic; body-selector
# chain extended to cover more outlets, with a generic <p>-tag fallback).
# ---------------------------------------------------------------------------
def load_article_generic(html, fallback_url):
    soup = BeautifulSoup(html, "html.parser")

    link = soup.find("link", rel="canonical")
    og_url = soup.find("meta", property="og:url")
    url = (link.get("href") if link else None) or \
          (og_url.get("content") if og_url else None) or fallback_url

    pub_date = None
    title = None
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string)
        except (TypeError, ValueError):
            continue
        candidates = data if isinstance(data, list) else [data]
        for d in candidates:
            if isinstance(d, dict) and d.get("datePublished"):
                pub_date = d["datePublished"]
                title = title or d.get("headline")
        if pub_date:
            break

    paragraphs = []
    for sel in BODY_SELECTORS:
        found = soup.select(sel)
        if found:
            paragraphs = [el.get_text(" ", strip=True) for el in found]
            break
    if not paragraphs:
        # last-resort generic fallback: every <p> on the page
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    full_text = "\n".join(t for t in paragraphs if t)

    if not title:
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

    return {"url": url, "pub_date": pub_date, "title": title, "text": full_text}


BANGLA_RE = re.compile(r"[ঀ-৿]")


def detect_language(text):
    if not text:
        return None
    bangla_chars = len(BANGLA_RE.findall(text))
    return "bn" if bangla_chars > len(text) * 0.05 else "en"


INCIDENT_DATE_HINTS = {"yesterday": ["গতকাল"], "today": ["আজ"]}


def extract_incident_date(text, pub_date):
    if not pub_date:
        return None, None
    try:
        pub_dt = datetime.datetime.fromisoformat(pub_date)
    except ValueError:
        return None, None
    for kind, phrases in INCIDENT_DATE_HINTS.items():
        for phrase in phrases:
            if phrase in text:
                delta = 1 if kind == "yesterday" else 0
                incident_dt = pub_dt - datetime.timedelta(days=delta)
                return incident_dt.date().isoformat(), ext.evidence_sentence(text, phrase)
    return None, None


def build_extended_row(article, source_name, search_query, raw_html_path, seen_hashes):
    text = article["text"]
    url = article["url"]

    age = ext.extract_age(text)
    victim_ctx = ext.victim_sentence(text)
    gender_cat, _ = ext.find_first(ext.GENDER_HINTS, victim_ctx)
    if gender_cat is None:
        gender_cat, _ = ext.find_first(ext.GENDER_HINTS, text)
    profession_cat, _ = ext.find_first(ext.PROFESSION_KEYWORDS, victim_ctx)
    if profession_cat is None:
        profession_cat, _ = ext.find_first(ext.PROFESSION_KEYWORDS, text)
    reason_cat, reason_kw = ext.find_first(ext.REASON_KEYWORDS, text)
    method_cat, method_kw = ext.find_first(ext.METHOD_KEYWORDS, text)
    district, lat, lon = ext.extract_location(text)

    prev_attempt = "yes" if any(p in text for p in ext.PREVIOUS_ATTEMPT_PHRASES) else "unclear"
    prev_attempt_kw = next((p for p in ext.PREVIOUS_ATTEMPT_PHRASES if p in text), None)

    unix_time = ext.to_unix(article["pub_date"])
    incident_date, incident_evidence = extract_incident_date(text, article["pub_date"])

    word_count = len(text.split())
    content_hash = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16] if text else ""
    case_id = ext.make_case_id(url)

    duplicate_of = ""
    if content_hash:
        if content_hash in seen_hashes:
            duplicate_of = seen_hashes[content_hash]
        else:
            seen_hashes[content_hash] = case_id

    extraction_status = "ok" if word_count >= 20 else "empty"

    return {
        "case_id": case_id,
        "source_name": source_name,
        "article_url": url,
        "article_title": article["title"],
        "language": detect_language(text),
        "search_query": search_query,
        "collected_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "age": age,
        "age_group": ext.age_group(age),
        "gender": gender_cat,
        "profession_group": profession_cat,
        "hometown": district,
        "latitude": lat,
        "longitude": lon,
        "reason": reason_cat,
        "reason_description": "",
        "method": method_cat,
        "previous_suicide_attempt": prev_attempt,
        "publication_date": article["pub_date"],
        "publication_unix_time": unix_time,
        "incident_date": incident_date,
        "family_members": "",
        "position_in_siblings": "",
        "marital_status": "",
        "duration_of_separation": "",
        "financial_condition": "",
        "previous_health_condition": "",
        "_evidence_reason": ext.evidence_sentence(text, reason_kw),
        "_evidence_method": ext.evidence_sentence(text, method_kw),
        "_evidence_previous_attempt": ext.evidence_sentence(text, prev_attempt_kw),
        "_evidence_incident_date": incident_evidence or "",
        "content_hash": content_hash,
        "word_count": word_count,
        "extraction_status": extraction_status,
        "duplicate_of": duplicate_of,
        "raw_html_path": raw_html_path,
        "coder_reviewed": "",
        "coder_name": "",
        "coder_reviewed_at": "",
    }


def blocked_row(url, title, snippet, source_name, search_query):
    return {
        "case_id": ext.make_case_id(url),
        "source_name": source_name,
        "article_url": url,
        "article_title": title,
        "language": None,
        "search_query": search_query,
        "collected_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "age": None, "age_group": None, "gender": None, "profession_group": None,
        "hometown": None, "latitude": None, "longitude": None,
        "reason": None, "reason_description": "",
        "method": None, "previous_suicide_attempt": None,
        "publication_date": None, "publication_unix_time": None, "incident_date": None,
        "family_members": "", "position_in_siblings": "", "marital_status": "",
        "duration_of_separation": "", "financial_condition": "",
        "previous_health_condition": "",
        "_evidence_reason": "", "_evidence_method": "",
        "_evidence_previous_attempt": "", "_evidence_incident_date": "",
        "content_hash": "", "word_count": 0, "extraction_status": "blocked",
        "duplicate_of": "", "raw_html_path": "",
        "coder_reviewed": "", "coder_name": "", "coder_reviewed_at": "",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def derive_source_name(search_url):
    netloc = urllib.parse.urlsplit(search_url).netloc.lower()
    netloc = re.sub(r"^www\.", "", netloc)
    domain = netloc.split(".")[0]
    return re.sub(r"[^a-z0-9]+", "_", domain).strip("_")


def decode_query(search_url):
    qs = urllib.parse.parse_qs(urllib.parse.urlsplit(search_url).query)
    if "q" in qs:
        return qs["q"][0]
    frag = urllib.parse.urlsplit(search_url).fragment
    m = re.search(r"gsc\.q=([^&]+)", frag)
    return urllib.parse.unquote_plus(m.group(1)) if m else ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) != 3:
        print("Usage: python3 download_search_results.py \"<google-cse-search-url>\" <folder_name>")
        sys.exit(1)

    search_url, folder_name = sys.argv[1], sys.argv[2]
    source_name = derive_source_name(search_url)
    search_query = decode_query(search_url)

    input_dir = DATA_COLLECTION_DIR / "input" / folder_name
    db_dir = DATA_COLLECTION_DIR / "database" / folder_name
    input_dir.mkdir(parents=True, exist_ok=True)
    db_dir.mkdir(parents=True, exist_ok=True)

    index_csv = input_dir / "_index.csv"
    download_log = db_dir / "_download.log"
    extract_log = db_dir / "_extract.log"
    out_csv = db_dir / "suicide_data.csv"

    # --- 1. harvest search results (resumable) ---
    if index_csv.exists():
        print(f"[harvest] {index_csv} exists, skipping harvest (delete it to re-harvest)")
        with open(index_csv, encoding="utf-8") as f:
            hits = {row["url"]: {"title": row["title"], "snippet": row["snippet"]}
                    for row in csv.DictReader(f)}
    else:
        print(f"[harvest] rendering search results: {search_url}")
        hits = harvest_search_results(search_url)
        with open(index_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["url", "title", "snippet"])
            w.writeheader()
            for url, meta in hits.items():
                w.writerow({"url": url, **meta})
        print(f"[harvest] wrote {len(hits)} unique hits to {index_csv}")

    # --- 2. download + parse each article (resumable) ---
    rows = []
    seen_hashes = {}
    dl_log_lines = []
    ok = blocked = skip = 0

    for i, (url, meta) in enumerate(hits.items(), 1):
        case_id = ext.make_case_id(url)
        dest = input_dir / f"{case_id}.html"

        if dest.exists() and dest.stat().st_size > 0:
            html = dest.read_text(encoding="utf-8")
            status = "ok"
            skip += 1
        else:
            html, status = fetch_article_html(url)
            time.sleep(REQUEST_DELAY_SECONDS)
            if status == "ok":
                dest.write_text(html, encoding="utf-8")
                ok += 1
            else:
                blocked += 1
            dl_log_lines.append(f"{status}\t{url}")

        if status == "ok":
            article = load_article_generic(html, url)
            article["title"] = article["title"] or meta["title"]
            raw_html_path = str(dest.relative_to(DATA_COLLECTION_DIR))
            rows.append(build_extended_row(article, source_name, search_query,
                                            raw_html_path, seen_hashes))
        else:
            rows.append(blocked_row(url, meta["title"], meta["snippet"],
                                     source_name, search_query))

        if i % 10 == 0 or i == len(hits):
            print(f"[download] {i}/{len(hits)} (ok={ok} blocked={blocked} skip={skip})")

    with open(download_log, "a", encoding="utf-8") as f:
        f.write("\n".join(dl_log_lines) + ("\n" if dl_log_lines else ""))

    # --- 3. write CSV ---
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(rows)

    blocked_rows = [r for r in rows if r["extraction_status"] == "blocked"]
    with open(extract_log, "w", encoding="utf-8") as f:
        f.write(f"total={len(rows)} ok={len(rows) - len(blocked_rows)} blocked={len(blocked_rows)}\n")
        for r in blocked_rows:
            f.write(f"blocked\t{r['article_url']}\n")

    print(f"\nWrote {len(rows)} row(s) to {out_csv}")
    if blocked_rows:
        print(f"[warn] {len(blocked_rows)} article(s) were blocked (bot-challenge / non-200) — "
              f"see {extract_log} for the list. These need a manual visit; the script does not "
              f"attempt to bypass site protections.")
    print("Columns needing manual review: family_members, position_in_siblings, "
          "marital_status, duration_of_separation, financial_condition, "
          "previous_health_condition, reason_description, incident_date "
          "(see the _evidence_* columns for the source sentence).")


if __name__ == "__main__":
    main()
