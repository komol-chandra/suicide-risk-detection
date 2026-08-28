# Automated Prothom Alo suicide-data pipeline

## Context

The project currently has **two separate, unfinished attempts** at the same
goal (collecting Prothom Alo suicide-incident articles into a structured
database), plus a fully manual step in between:

1. **`doc/`** — a designed 6-step pipeline (`1_search_harvester.py` →
   `2_article_fetcher.py` → `3_field_extractor.py` → `4_geocode_enrich.py` →
   `5_weather_enrich.py` → `6_merge_export.py`). It assumes Prothom Alo's
   search results can only be read with a headless browser (Playwright)
   clicking "আরও" (load more), and **`2_article_fetcher.py` doesn't actually
   exist** even though the README and step 3 depend on it. Never run for
   real (`doc/data/` doesn't exist).
2. **`data-collection/`** — the one with real output. `codebase/extract_suicide_data.py`
   parses **manually saved** article HTML files from `input/` (`1.html`,
   `2.html` — saved one at a time via browser "Save As") with regex/keyword
   rules, producing `database/suicide_data.csv` (currently 2 rows).

You want to replace the manual save-one-article-at-a-time step with full
automation: crawl the search results for "আত্মহত্যা" (10,135 hits), paginate
through all of them, capture each article's title+link, and populate a
proper database — plus fix the database schema, which currently has typos
(`maritual_status`, `duration_of_separataion`) and no title/date/incident-flag
columns.

**Key discovery made while investigating (verified with live `curl` calls,
not assumed):** Prothom Alo's search page is server-rendered — a plain HTTP
GET to `https://www.prothomalo.com/search?q=...&offset=N&limit=100` returns
a `<script type="application/json" id="static-page">` blob containing, for
every result, the **full article body text already embedded** (`cards` →
`story-elements` → `text`), identical to what the individual article page
returns. This means:
- **No Playwright/headless browser is needed at all** — `doc/1_search_harvester.py`'s
  core premise is outdated/wrong. Plain `requests` + `json` is enough for both
  the listing *and* the article content, in one request per page of results.
- We likely don't need a separate per-article fetch step (`2_article_fetcher.py`)
  for the body text — one harvest pass gets title, link, date, section, and
  full text together.
- **Hard constraint found:** the endpoint 500s once `offset + limit` exceeds
  ~10,000 (classic Elasticsearch `max_result_window` default). Confirmed by
  bisection: `offset=9900&limit=100` → 200 OK, `offset=9950&limit=100` → 500.
  So plain offset paging can only ever reach ~9,900 of the 10,135 results —
  the last ~235+ (and it grows as more articles get published) are
  permanently unreachable that way.
- I tried to confirm the search page's date-filter query params (visible in
  the UI as "তারিখ") by guessing common names (`from-date`/`to-date`,
  `date-from`/`date-to`, `from`/`to`, epoch-ms variants, `sort=latest`, etc.)
  — **none of them changed the result `total`**, so the real param name is
  still unconfirmed. This is an open risk, addressed below.

## Problems this plan fixes

1. Fully manual per-article download → replace with automated harvesting.
2. Duplicate/abandoned `doc/` pipeline vs. the real `data-collection/` one →
   consolidate into one pipeline, reusing `doc/`'s good parts (the LLM
   extraction prompt in `3_field_extractor.py`, the controlled vocabularies
   and district gazetteer in `config.py`/`bd_districts.csv`) rather than
   throwing them away.
3. No title+link index file → add one, doubling as a resumability/dedup
   ledger.
4. `suicide_data.csv` schema is thin (24 cols, 2 rows), has typos, and no
   `title`/`published_date`/relevance flag → redesign the schema now, while
   there's only 2 rows to migrate.
5. 10,135 results but only ~9,900 reachable via plain paging → needs
   chunking (see Open risk below).
6. Not every one of the 10,135 hits is an actual suicide-incident report
   (court cases, movie reviews, opinion pieces will match too) → add a
   relevance filter so the database isn't noisy.
7. Regex/keyword field extraction (current `extract_suicide_data.py`) is
   fragile for scale → move to Claude-based extraction (adapting
   `doc/3_field_extractor.py`'s already-well-designed "never guess, null if
   not stated" prompt), which is far more robust to Bangla phrasing
   variation across 10k articles.

## Target pipeline (all new/changed files under `data-collection/`)

```
data-collection/
├── codebase/
│   ├── 01_harvest.py          # replaces doc/1_search_harvester.py — no Playwright
│   ├── 02_classify.py         # NEW — relevance filter
│   ├── 03_extract_fields.py   # adapted from doc/3_field_extractor.py, reads raw JSON not HTML
│   └── 04_build_database.py   # replaces doc/6_merge_export.py (weather/geocode stay out of scope for now)
├── input/
│   ├── search_index.csv       # NEW — the title+link CSV you asked for, one row per article
│   └── raw/<slug>.json        # NEW — full story JSON per article (replaces manually-saved .html)
└── database/
    └── suicide_data.csv       # rebuilt with the new schema below
```

`doc/` becomes redundant once this lands — recommend archiving it (e.g. into
`prior-work/`) rather than deleting outright, since `3_field_extractor.py`'s
prompt and `config.py`'s vocab/gazetteer get reused, not rewritten from
scratch.

### Step 1 — `01_harvest.py`
- Requests `https://www.prothomalo.com/search?q=<keyword>&offset=<N>&limit=100`
  in a loop (100 confirmed reliable; 200 also worked but is close to the
  502 failure seen at 500 — stick to 100 for headroom), parses the
  `#static-page` JSON, and for each story writes:
  - a row to `input/search_index.csv`: `url, slug, title, section, published_at, keyword_matched, fetched_at`
  - the full story object to `input/raw/<slug>.json` (title, body cards, tags,
    author, published date — everything needed by step 3, no re-fetch needed later)
- Dedupes by canonical URL (a story can appear under multiple keyword
  variants/date chunks) and is resumable — reruns skip URLs already in
  `search_index.csv` unless `--refresh` is passed.
- **Coverage chunking (open risk):** since date-filter params aren't
  confirmed yet, first sub-task is a short, isolated check — request the
  search page once with a candidate date param and eyeball the raw HTML/JS
  for the real param name (or, if that's a dead end quickly, don't burn more
  time on it). Fallback that's already confirmed to work: use `doc/config.py`'s
  existing keyword-variant list (`আত্মহত্যা করেছে`, `আত্মহত্যা করেন`, `আত্মহনন`,
  `গলায় ফাঁস দিয়ে`, `বিষপান করে`, `ফাঁস দিয়ে আত্মহত্যা`, ...) as separate harvest
  buckets — each bucket's own `total` will be well under 10,000, and
  `search_index.csv`'s URL-dedup naturally merges the overlap. Only add
  buckets while the plain `আত্মহত্যা` bucket is capped at ~9,900.
- Courtesy delay between requests (reuse `REQUEST_DELAY_SECONDS` idea from
  `doc/config.py`), single realistic User-Agent, sequential requests.

### Step 2 — `02_classify.py`
- Cheap heuristic pass over `search_index.csv`/raw JSON (section name,
  story-template, a short suicide-incident keyword check on the title) to
  set `is_incident_report` yes/no/maybe.
- `maybe` rows (ambiguous) get a second look in step 3 rather than being
  silently kept or dropped.

### Step 3 — `03_extract_fields.py`
- For rows not flagged `no`, sends the cached raw JSON's article text (already
  on disk, no network call) to Claude using an adapted version of
  `doc/3_field_extractor.py`'s system prompt — same "extract only what's
  explicitly stated, null otherwise" policy already validated in this repo's
  own design. Also has it confirm/override the relevance flag from step 2.
- Writes one JSON record per article to `input/extracted/<slug>.json`
  (checkpointed — a crashed/interrupted run resumes without re-billing
  already-processed articles).

### Step 4 — `04_build_database.py`
- Joins `search_index.csv` + `input/extracted/*.json` into
  `database/suicide_data.csv` with the new schema below. Fully
  regeneratable from the `input/` cache — never hand-edited.

## New `suicide_data.csv` schema

Based on `doc/config.py`'s `FINAL_COLUMNS` (which was already more complete
than the current CSV), with typos fixed and weather/geocode columns dropped
for now (out of scope until you decide to revisit steps 4–5 from `doc/`):

```
case_id, data_source, title, is_incident_report, published_date, unix_time,
full_name, age, age_group, gender, family_members, position_in_siblings,
marital_status, duration_of_separation, profession_group,
profession_description, workplace, religion, financial_condition,
hometown, latitude, longitude, reason, reason_description, time, method,
previous_health_condition, previous_suicide_attempt,
_evidence_reason, _evidence_method, _evidence_previous_attempt
```

(`latitude`/`longitude` stay populated only from the existing
`DISTRICT_CENTROIDS`/`bd_districts.csv` lookup — no weather enrichment.)

## Verification plan

1. Run `01_harvest.py` capped to ~200 articles first; confirm
   `search_index.csv` row count/content and spot-check 2–3 `raw/<slug>.json`
   files against the live article page.
2. Run `02_classify.py` + `03_extract_fields.py` on that same small batch;
   manually read 5 extracted records against their source text for accuracy.
3. Run `04_build_database.py`, open `suicide_data.csv`, confirm schema and
   that existing 2 rows' data would map cleanly under the new columns.
4. Only then remove the small-batch cap and run the full harvest (with
   `--refresh` off, so it resumes cleanly if interrupted).
