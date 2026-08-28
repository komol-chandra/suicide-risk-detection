# suicide-risk-detection — project memory

Part of the `ReviewLens` workspace (`../README.md`, `../SPRINT_TRACKER.md`
track all three sibling projects there). This project turns a finished BUBT
capstone thesis on Bangladesh newspaper-reported suicide incidents
(imputation × clustering benchmark) into one or more published papers.

## Structure and what each folder is for

- **`prior-work/`** — the original capstone: thesis docx, dataset, slides,
  the LaTeX report source and analysis notebooks (as zips). **Read-only
  archive** — don't edit in place; if something needs updating, do it in a
  paper's own `analysis/`/`paper/` folder instead.
- **`literature/`** — related-work PDFs. **Shared corpus across all papers**
  in this project, not per-paper — the same literature informs multiple
  papers on the same topic. Organized by reviewer subfolder
  (`komol/`, `tomal/`, `rinkey/`, `simul/`).
- **`data-collection/`** — the scraping/extraction pipeline and its output,
  **shared across all papers**. See "Data-collection convention" below.
- **`papers/paper-N/`** — one per paper. See "Multi-paper convention" below.
- **`planning/questions/`** — clarification/scoping history with the team
  (answers.md + screenshots of handwritten notes). Cross-paper, not tied to
  one paper specifically.
- **`_archive/`** — a graveyard, not a recycle bin. Files land here because
  they're *superseded* (e.g. a PDF export whose .md source still exists, a
  prototype a later phase fully replaced), not because someone was unsure.
  Don't casually resurrect something from here without checking why it was
  archived.

## Multi-paper convention

Each paper gets its own `papers/paper-N/`:
```
papers/paper-N/
├── README.md    one-line: title, target venue, status
├── PLAN.md       the paper's own plan/phases
├── paper/        LaTeX source (main.tex, sections/, figures/, refs.bib)
└── analysis/     notebooks specific to this paper
```
Papers draw on the shared `literature/` and `data-collection/` rather than
duplicating them. `papers/paper-1/` is the in-flight Q1 journal upgrade of
the capstone thesis — read `papers/paper-1/PLAN.md` before picking up work
on it.

## Data-collection convention

Phases are numbered (`phase-1`, `phase-2`, ...). Each phase is:
- `data-collection/input/phase-N/` — raw downloaded article HTML (large,
  **gitignored** — never `git add -A` blindly in this repo, check `git
  status` for surprises first).
- `data-collection/database/phase-N/` — the extracted structured CSV (the
  actual dataset asset, tracked in git) plus `_download.log`/`_extract.log`
  provenance from the run that produced it.

`data-collection/codebase/download_phase1.py` harvests and downloads
articles by talking to Prothom Alo's public search API directly
(`https://www.prothomalo.com/api/v1/search`) — **no headless browser
needed**, despite what older docs assumed. It buckets by publication year to
work around Elasticsearch's ~10,000-result pagination window, and is
resumable (delete a phase's `_index.csv` to force a re-harvest; already-
downloaded HTML files are skipped).

`data-collection/codebase/extract_suicide_data.py` parses any folder of
article HTML into the structured CSV — rule-based keyword extraction, not
an LLM. It's designed for human-in-the-loop coding: fields it can't extract
reliably (family structure, marital status, financial condition, etc.) are
left blank with an `_evidence_<column>` sentence for a human coder to read,
rather than guessed.

`data-collection/codebase/future-enrichment/` holds an unbuilt future-work
design (LLM-based field extraction, geocoding, weather enrichment) — kept as
reference, not part of the working pipeline. See its own README for what it
would add and why it isn't built yet.

Starting a new phase (e.g. `phase-2` to pick up newly published articles, or
a broadened query): copy the pattern above, don't create a new one-off
script per phase — `download_phase1.py`'s harvest/download logic is meant to
be reused, just point it at a fresh output folder.

## Sensitive data — anonymization convention

This is data about real people's deaths, sourced from public news reports.
`extract_suicide_data.py` already anonymizes: a `case_id` hash instead of
names, district-level centroid coordinates instead of exact addresses, and
it deliberately leaves fields blank rather than fabricating personal details
that aren't explicitly stated in the source article. **Keep this convention**
for any future extraction work (including the future-enrichment scripts, if
they're ever built) — don't add name extraction, exact addresses, or
inferred personal details.

## Cross-references

- `../README.md` and `../SPRINT_TRACKER.md` (one level up, in `ReviewLens/`)
  describe this project alongside its two siblings — keep their
  descriptions of this project's layout in sync if the structure changes
  again.
