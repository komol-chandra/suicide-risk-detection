# Suicide Risk Detection

Part of the [ReviewLens](../README.md) workspace — see
[../SPRINT_TRACKER.md](../SPRINT_TRACKER.md) for cross-project status.

Builds on a finished BUBT capstone thesis ("A Machine Learning Approach to
Identifying Influential Factors and Clustering Patterns in Suicide
Occurrences") — an imputation × clustering benchmark on newspaper-reported
suicide incidents from Bangladesh. This project turns that thesis into one
or more published papers, starting with a Q1 journal upgrade
([papers/paper-1](papers/paper-1/)).

## Layout

```
suicide-risk-detection/
├── prior-work/           finished capstone thesis, dataset, slides — read-only archive
├── literature/           related-work PDFs, shared across all papers (per-reviewer subfolders)
├── data-collection/      scraping/extraction pipeline + database, shared across all papers
│   ├── codebase/         download_phase1.py (harvest+download) + extract_suicide_data.py (parse to CSV)
│   ├── input/phase-N/    raw article HTML per phase (large, gitignored)
│   └── database/phase-N/ extracted CSV per phase (the actual dataset)
├── papers/                one subfolder per paper
│   └── paper-1/           Q1 journal upgrade — see paper-1/README.md and PLAN.md
├── planning/questions/    clarification history with the team (Q&A, screenshots)
└── _archive/              superseded files, kept for reference — not deleted
```

See [CLAUDE.md](CLAUDE.md) for the full set of conventions this project
follows.

## Starting a new paper

Add `papers/paper-N/` with a `README.md` (title/venue/status) and a
`PLAN.md`. It can draw on the shared `literature/` and `data-collection/`
without duplicating either.
