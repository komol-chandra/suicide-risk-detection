# -*- coding: utf-8 -*-
"""
download_phase1.py

Harvests every Prothom Alo search-result hit for a query and downloads each
article's full HTML page to a local folder, one .html file per article —
the raw input that extract_suicide_data.py then parses.

WHY THIS DOESN'T NEED A HEADLESS BROWSER
-----------------------------------------
Prothom Alo's search results *page* is client-rendered, but it's backed by a
plain public JSON endpoint (Quintype's search API):

    GET https://www.prothomalo.com/api/v1/search?q=<query>&size=<n>&from=<n>

`size`+`from` only works up to Elasticsearch's default 10,000-result window,
so for a query with more hits than that, this script buckets requests by
publication year (via published-after/published-before, epoch ms) — each
year's bucket is small enough to page through fully.

Article *detail* pages are server-rendered (they include the full body text
in the initial HTML, confirmed via `.story-element-text` / JSON-LD), so they
can be fetched with plain HTTP GETs too — no Playwright needed anywhere in
this script.

USAGE
-----
    python3 download_phase1.py

Resumable: re-running skips articles already saved to disk and reuses the
existing index CSV if present. Delete data-collection/input/phase-1/_index.csv
to force a fresh harvest (e.g. to pick up newly published articles).
"""

import csv
import datetime
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

QUERY = "আত্মহত্যা"  # "suicide" — same query as the user-provided search URL
FIRST_YEAR = 2009  # archive has 0 hits before this (verified)
API_BASE = "https://www.prothomalo.com/api/v1/search"
PAGE_SIZE = 100

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

API_DELAY_SECONDS = 0.4          # between sequential harvest API calls
DOWNLOAD_DELAY_SECONDS = 0.5     # per-thread delay between article fetches
DOWNLOAD_WORKERS = 4             # ~8 req/s aggregate — considerate default

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE.parent / "input" / "phase-1"
INDEX_CSV = OUT_DIR / "_index.csv"
INDEX_FIELDS = ["id", "slug", "url", "headline", "published_at", "story_template"]


def api_get(params):
    url = API_BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def year_bounds_ms(year):
    a = int(datetime.datetime(year, 1, 1).timestamp() * 1000)
    b = int(datetime.datetime(year + 1, 1, 1).timestamp() * 1000)
    return a, b


def current_year():
    return datetime.datetime.now().year


def harvest_index():
    if INDEX_CSV.exists():
        print(f"[harvest] {INDEX_CSV} already exists — skipping harvest "
              f"(delete it to re-harvest)")
        return

    seen = {}
    for year in range(FIRST_YEAR, current_year() + 1):
        after, before = year_bounds_ms(year)
        frm = 0
        year_count = 0
        while True:
            data = api_get({
                "q": QUERY, "size": PAGE_SIZE, "from": frm,
                "published-after": after, "published-before": before,
            })
            results = data["results"]
            stories = results["stories"]
            total = results["total"] or 0
            if not stories:
                break
            for s in stories:
                sid = s["id"]
                if sid in seen:
                    continue
                seen[sid] = {
                    "id": sid,
                    "slug": s["slug"],
                    "url": f"https://www.prothomalo.com/{s['slug']}",
                    "headline": s.get("headline", ""),
                    "published_at": s.get("published-at", ""),
                    "story_template": s.get("story-template", ""),
                }
                year_count += 1
            frm += PAGE_SIZE
            time.sleep(API_DELAY_SECONDS)
            if frm >= total:
                break
        print(f"[harvest] {year}: +{year_count} (running total {len(seen)})")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(INDEX_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=INDEX_FIELDS)
        w.writeheader()
        w.writerows(seen.values())
    print(f"[harvest] wrote {len(seen)} unique articles to {INDEX_CSV}")


def request_safe_url(url):
    """Percent-encode the path (some slugs contain raw Bangla characters),
    since urllib can't build a request line with non-ASCII bytes."""
    parts = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(parts.path)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))


def download_one(row):
    dest = OUT_DIR / f"{row['id']}.html"
    if dest.exists() and dest.stat().st_size > 0:
        return "skip"
    req = urllib.request.Request(request_safe_url(row["url"]), headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            html = r.read()
        dest.write_bytes(html)
        time.sleep(DOWNLOAD_DELAY_SECONDS)
        return "ok"
    except urllib.error.HTTPError as e:
        return f"error: HTTP {e.code}"
    except Exception as e:
        return f"error: {e}"


def download_all():
    with open(INDEX_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"[download] {len(rows)} articles indexed, checking {OUT_DIR} ...")

    ok = skip = err = 0
    with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as ex:
        futures = {ex.submit(download_one, row): row for row in rows}
        for i, fut in enumerate(as_completed(futures), 1):
            result = fut.result()
            if result == "ok":
                ok += 1
            elif result == "skip":
                skip += 1
            else:
                err += 1
                print(f"[download] {futures[fut]['id']} ({futures[fut]['url']}): {result}")
            if i % 200 == 0 or i == len(rows):
                print(f"[download] progress {i}/{len(rows)} (ok={ok} skip={skip} err={err})")
    print(f"[download] done: ok={ok} skip={skip} err={err}")


if __name__ == "__main__":
    harvest_index()
    download_all()
