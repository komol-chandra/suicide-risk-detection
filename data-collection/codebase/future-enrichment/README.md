# Future enrichment steps — not yet built

This folder holds the *original* design for a 6-step scraping + LLM-extraction
+ weather-enrichment pipeline. Steps 1-2 of that design are superseded and
should not be run — see below for what actually replaced them. Steps 3-6 were
never built and are kept here as a reference design for later, if the project
decides it needs LLM-based field extraction or geocode/weather enrichment on
top of what `../extract_suicide_data.py` already does.

## What actually replaced steps 1-2

The original assumption was that Prothom Alo's search results require a
headless browser (Playwright) to enumerate, because the search page is
client-rendered. That's true for the *rendered page*, but the search is
backed by a plain public JSON API
(`https://www.prothomalo.com/api/v1/search?q=...`), discovered while building
phase-1 of the dataset. `../download_phase1.py` uses that API directly —
year-bucketed to work around Elasticsearch's ~10,000-result pagination
window — and downloads each article's HTML with a plain HTTP GET (article
detail pages are server-rendered, unlike the search results page). No
Playwright, no browser, no `1_search_harvester.py` / `2_article_fetcher.py`.
`../extract_suicide_data.py` then does rule-based (not LLM-based) field
extraction straight from the downloaded HTML.

Both of those live in `../` (`data-collection/codebase/`), not here — that's
the actual working pipeline. See `../../../CLAUDE.md` for the full
data-collection convention.

## Steps kept here as future-work reference (not built, not run)

3. `3_field_extractor.py` — sends each article's text to Claude with a strict
   JSON schema to pull the ~20 incident-level fields, leaving a field `null`
   rather than guessing. Would be an *alternative or supplement* to
   `extract_suicide_data.py`'s rule-based keyword extraction — worth
   revisiting if the rule-based approach's fill rates (see the phase-1
   extraction run — `reason`/`method` were only ~26-36% filled) turn out too
   low for the paper's needs.
4. `4_geocode_enrich.py` — maps `hometown` text to `latitude`/`longitude`
   using a static Bangladesh district/division gazetteer (`bd_districts.csv`).
   Extend this table if a hometown is at thana/upazila level and needs finer
   coordinates. Note `extract_suicide_data.py` already does its own coarse
   district-centroid lookup — this would replace/extend that.
5. `5_weather_enrich.py` — for each row, calls OpenWeatherMap's historical
   **timemachine** endpoint (One Call API 3.0) using `suicide_date` +
   `latitude`/`longitude`. **Note:** historical timemachine calls require a
   paid/subscribed One Call 3.0 key even within the 1,000-calls/day free
   tier — confirm your key has that product enabled, since the plain
   free-tier current-weather key won't work for past dates.
6. `6_merge_export.py` — joins everything into a final CSV with a specific
   column order (`config.py`'s `FINAL_COLUMNS`).

## Setup (only needed if you actually run steps 3-6)

```bash
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Set environment variables (or put them in a `.env` file and
`pip install python-dotenv`):
```
ANTHROPIC_API_KEY=sk-ant-...
OPENWEATHER_API_KEY=...
```

## Assumptions on ambiguous columns (adjust in `3_field_extractor.py` if wrong)

- `age_group`: derived bucket from `age` (child <13, teen 13-19, adult 20-59,
  elderly 60+), not separately extracted.
- `duration_of_separataion`: time since a stated divorce/separation from
  spouse/partner, only filled when the article explicitly ties the incident
  to that. Null otherwise.
- `reason` vs `reason_description`: `reason` is a short controlled category
  (e.g. dowry, marital_conflict, exam_failure, financial_distress,
  harassment, love_failure, domestic_violence, unknown); `reason_description`
  is a short free-text gloss of what the article actually said.
- `method`: a short category (hanging, poisoning, jumping, self_immolation,
  firearm, drowning, other, unknown) — purely descriptive classification of
  what was reported, not instructional detail.
- `financial_condition` / `religion`: only filled when explicitly stated in
  the article; left null otherwise (no inference from names, area, etc.).
- `data_source`: article URL.

## Ethics / rate limiting

- Respects a delay between requests by default (see `REQUEST_DELAY` in
  `config.py`).
- Only public news content is scraped; no personal data beyond what's
  already published.
- Recommend checking Prothom Alo's terms of use for your research use case
  before scaling further.
