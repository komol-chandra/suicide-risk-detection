# Plan: Upgrade the Suicide-Risk-Detection Capstone into a Q1 Journal Submission

## Context

The team already has a 14-day plan (originally `suicide-risk-detection/SPRINT_PLAN.md`,
now archived at `_archive/SPRINT_PLAN.md` and superseded by this file, tracked in
`../SPRINT_TRACKER.md`) that converts the finished BUBT capstone thesis
(`prior-work/newly formated capstone report 2025.docx`) into a **6-page IEEE-style
conference paper**, reusing existing results with zero new analysis. That plan's window
was 2026-08-17 → 2026-08-30 — it ends in two days and was scoped for a different, much
shorter target.

The user now wants three things this plan must satisfy together:
1. **Update the paper** rather than just reformat it.
2. **Use more of the work already sitting in the repo** — specifically the team's
   literature folders and what looks like an expanded dataset.
3. **Prepare for a Q1 journal**, not a conference — a materially higher bar: longer,
   more rigorously argued related work, statistical justification for claims a
   6-page paper could get away with asserting, and a Data Availability /
   CRediT / ethics apparatus conference papers don't require.

Verified during exploration (2026-08-28):
- **Literature is richer than the sprint plan assumed.** It planned around 9 PDFs in a
  `literature/` folder. The repo now has `literature/komol/` (9 PDFs) and
  `literature/tomal/` (9 PDFs), with at least 2 overlapping titles between them
  (`Socially_Aware_Synthetic_Data_Generation...`, a South-Asia depression/suicide
  systematic review) — dedupe brings it to roughly 14–16 unique new papers, beyond the
  thesis's own 42-entry reference list.
  `literature/rinkey/` and `literature/simul/` are **empty** — two
  teammates haven't contributed yet. Per your answer, proceeding without them; note this
  as an open gap that's cheap to merge in later if they add papers before submission.
- **The dataset looks larger than what the thesis analyzed.**
  `prior-work/SuicideBD-dataset - SuicideBD-dataset.csv` has **1,797 data rows**, but the
  docx states the thesis's final analyzed dataset was **1,617 records**. That's a real,
  verified ~180-row gap that needs reconciling before any pipeline is re-run on it —
  Phase 2 below is dedicated to this.
- There's also a separate, early-stage **automated scraping pipeline** (at the time of
  this note, `doc/1_search_harvester.py` → `6_merge_export.py`, output currently only 2
  test rows in `data-collection/database/suicide_data.csv`) aimed at eventually covering
  2016–2026. **Update (2026-08-29):** this has since been built out — see
  `data-collection/codebase/download_phase1.py` +  `extract_suicide_data.py`, which
  harvested 10,066 articles into `data-collection/database/phase-1/suicide_data.csv`.
  The 2-row prototype is now archived at `_archive/legacy-prototype/`. The new phase-1
  dataset is still separate from `prior-work/`'s 1,617/1,797-row datasets discussed
  above — it doesn't resolve that reconciliation gap, it's an independent, much larger
  batch that needs its own relevance-filtering pass before use (many hits are general
  articles mentioning the word, not individual incident reports). It is not the source
  of the 1,617→1,797 gap and should be
  treated as **future work**, not a dependency — waiting on it would make this
  open-ended.
- Per your answer, scope is **"all of the above"**: fold in the literature, add the
  statistical rigor a Q1 reviewer will expect, and re-run the pipeline on the
  reconciled/expanded dataset. This is materially more work than the original 14-day
  conference plan and should be timeboxed in weeks, not days.

### Target journal — recommendation

You asked me to recommend rather than name one yourself. Verified quartile/impact-factor
status (web search, 2026):

| Journal | Quartile | Impact Factor | Fit |
|---|---|---|---|
| **Journal of Big Data** (Springer) | Q1 (JCR) | 10.8 | **Best methodological fit.** This is exactly a benchmarking study of imputation methods × clustering algorithms on a real messy dataset — the journal's core subject matter. The thesis already cites this journal's own papers on imputation surveys. Highest impact factor of the three by a wide margin. |
| **BMC Psychiatry** (Springer/BMC) | Q1 (SJR) | ~3.8 | **Best topical/public-health fit.** Open access, methodologically flexible, and the thesis's own reference list already cites a directly comparable BMC Psychiatry paper on Bangladesh suicide mortality (ref. [24] in the docx) — strong precedent that this journal publishes exactly this kind of LMIC suicide-surveillance study. |
| Scientific Reports (Nature Portfolio) | Q1 (multidisciplinary) | 4.9 | Broadest safety net — accepts solid methods papers without requiring a clinical-outcome angle, but less topical prestige than the two above and more competition volume. |

**Recommendation:** submit first to **Journal of Big Data** (best fit, highest IF), with
**BMC Psychiatry** as the fallback if reviewers there push for more epidemiological/
clinical framing than an unsupervised-clustering methods paper naturally provides.
Scientific Reports is the backup-backup. This choice also resolves the "how much new
statistical rigor is needed" question in Phase 3 — a data-science methods journal will
scrutinize the imputation/clustering benchmark rigor hardest, less the clinical
implications.

---

## ⚠️ Team alignment gap found — resolve before Phase 1

`planning/questions/` contains two photos of handwritten notes (dated 2026-08-28, today)
from a teammate, raising exactly the kind of scope confusion that will derail this plan
if left unresolved:

1. "This week if we build the dataset then preprocess it... what are we actually trying
   to do?"
2. "Are we doing something region-wise, or focused on suicide *reasons*? What's our
   actual goal?"
3. "We need a brief on what we're trying to do."
4. "We're picking a title before we've even collected data — that's confusing."
5. "Finalizing data collection is going to take more time — can it be automated?"
6. "Please explain how far the previous paper already got."

This reads as at least one teammate treating this as a **fresh study** (new title, new
data collection, an undecided region-wise-vs-reason-wise angle) rather than a **journal
upgrade of the finished thesis** (the framing this whole plan, and the original
`SPRINT_PLAN.md`, assumes). That's a real fork in direction, not a misunderstanding to
wave away — resolve it explicitly with the team before Phase 1 literature work starts,
since "what's relevant related work" depends on which framing wins.

**My recommendation, to put to the team as the answer to all 6 points:** stay with the
finished-thesis framing. The imputation-method × clustering-algorithm benchmark is
already done and produced a real result (see the briefing below) — restarting around a
new region-wise or reason-wise angle would mean abandoning that finished work and
starting a new research project from zero, which is a much bigger undertaking than
"prepare for a Q1 journal." The existing clusters already get interpreted across
demographic, geographic, *and* reason dimensions together, so a region- or reason-only
reframing isn't needed to make the paper richer — Phases 1–3 already do that.

**Suggested briefing to send the team (answers the 6 questions directly):**
- *(Q1, Q3)* This week's concrete goal is literature consolidation (Phase 1) and
  starting dataset reconciliation (Phase 2) — not building a new dataset from scratch.
- *(Q2)* Goal stays the same as the thesis: benchmark imputation × clustering pipelines
  on the Bangladesh newspaper-suicide dataset and interpret the winning clusters across
  demographic/geographic/reason dimensions together — not a new region-only or
  reason-only study.
- *(Q4)* The title stays anchored to the completed thesis work. If someone proposed a
  new title implying new scope, check with them directly whether they meant to extend
  this work or start something else — don't let a title decision silently commit the
  team to new data collection.
- *(Q5)* Yes, automatable — that's what `doc/1_search_harvester.py` →
  `6_merge_export.py` already is. But it's pilot-stage (2 test rows so far); per this
  plan, it's future work, not a dependency for this submission.
- *(Q6)* The thesis is fully complete: 6 chapters, 1,617 records × 34 columns, 32
  imputation×clustering pipelines benchmarked, winner = Agglomerative Clustering +
  MissForest (no-context), composite score 27.30/32, a two-cluster solution that
  separated cleanly by data-collection cohort (2020 vs. 2017–2025), 42 references.
  Nothing experimental is "unfinished" in the original scope — what's left is exactly
  Phases 1–5 of this plan.

---

## Working structure

Keep `../../prior-work/` untouched as the thesis archive. Create, inside this
paper's own folder (`papers/paper-1/`):

```
papers/paper-1/
├── paper/
│   ├── main.tex                 Journal of Big Data (or fallback) template
│   ├── refs.bib                 thesis's 42 + ~14-16 new lit-review papers, deduped
│   ├── sections/
│   │   ├── abstract.tex
│   │   ├── introduction.tex
│   │   ├── related-work.tex     now with a comparison table, not just prose
│   │   ├── data-and-methods.tex merged dataset section + pipeline description
│   │   ├── results.tex          re-run numbers, not the docx's original ones
│   │   ├── discussion.tex
│   │   ├── limitations-ethics.tex
│   │   └── conclusion.tex
│   ├── figures/
│   └── data-availability.tex    journal-required statement, thesis has no equivalent
└── analysis/
    ├── 00_dataset_reconciliation.ipynb   Phase 2
    ├── 01_rerun_pipeline_expanded.ipynb  Phase 2 (extends existing capstone notebooks)
    └── 02_stability_significance.ipynb   Phase 3 (new)
```

---

## Phase 0 — Decisions & setup (this week)

- [ ] **Send the team-alignment briefing above** and get explicit agreement that this is
      a journal upgrade of the finished thesis, not a new region-wise/reason-wise study
      — this is the one item that could silently invalidate everything below it.
- [ ] Confirm the Journal of Big Data / BMC Psychiatry choice with co-authors and
      supervisor (Md. Mamun Hossain) — this determines template, length, and required
      statements. Reuse author list/order from `Capstone_Project_Report.zip`'s
      `Declaration.tex` unless the team wants to revisit it.
- [x] Update/replace `SPRINT_PLAN.md` and the corresponding checklist in
      `../SPRINT_TRACKER.md` (lines ~86–104) to point at this plan instead — the old one
      is dated and scoped for a conference submission that isn't happening. Done as part
      of the 2026-08-29 project reorg: `SPRINT_PLAN.md` moved to `_archive/`, this file
      moved to `papers/paper-1/PLAN.md`, and `../SPRINT_TRACKER.md` updated to link here.
- [ ] Set up the `paper/` skeleton above with the chosen journal's template.

## Phase 1 — Literature consolidation ("use more work", literature half)

- [ ] Merge `literature/komol/` (9 PDFs) + `literature/tomal/` (9 PDFs),
      dedupe by title (at least 2 confirmed overlaps: the synthetic-data-generation LLM
      paper and the South-Asia depression/suicide systematic review) → ~14-16 unique new
      sources.
- [ ] Extend `refs.bib` from the thesis's 42 (still only 2 placeholder entries exist in
      `Capstone_Project_Report.zip`'s current `ref.bib` — build the real 42 from the
      docx's plain-text list first) plus these new ~14-16 → ~56-58 total entries.
- [ ] Draft `related-work.tex` at journal depth (not conference-compressed): synthesize
      docx §2.2–2.6 with the new literature, and add a **comparison table** (a Q1
      methods-journal norm) contrasting this study against (a) prior South-Asia suicide
      epidemiology studies and (b) prior imputation-clustering benchmark studies — table
      columns like dataset size, missingness handling, clustering method, validation
      approach. This directly operationalizes the novelty angle the original sprint plan
      already flagged as strongest: *this study clusters structured, incomplete
      newspaper records rather than mining free text*.
- [ ] Leave a placeholder subsection or footnote noting `rinkey`/`simul` may still
      contribute sources — cheap to slot in before submission, not blocking.

## Phase 2 — Dataset reconciliation ("use more work", data half)

- [ ] Reconcile the discrepancy: diff `prior-work/SuicideBD-dataset - SuicideBD-dataset.csv`
      (1,797 rows) against whatever exact file/version the thesis's 1,617-record analysis
      was run on, and check `prior-work/SuicideBD_ordered_by_year.xlsx` too — determine
      whether the extra ~180 rows are genuinely new cases, duplicates, or a different
      inclusion filter. **Do not proceed to re-running the pipeline until this is
      confirmed with whoever added the extra rows** (likely one of the 5 co-authors).
- [ ] Once reconciled, re-run the existing capstone notebooks
      (`prior-work/capstone-....zip` → `0_preprocessing` through `11_comparing-clustering`)
      on the confirmed dataset: same 3 imputation methods × 2 predictor strategies × 4
      clustering algorithms × validity indices → composite score, exactly as before, just
      on the corrected/expanded data.
- [ ] Sanity check: does the previously-best pipeline (`agg_rf_no_context`, composite
      27.30) still win on the expanded data? If the ranking changes, that's itself a
      result worth discussing, not a problem to hide.
- [ ] Regenerate the figures/tables that Day 6 of the old sprint plan intended to pull
      from the notebooks (composite-score ranking chart, PCA cluster scatter, missingness
      before/after) — now from the re-run, not the original docx numbers.

## Phase 3 — Added statistical rigor (Q1 bar)

A conference paper can assert "this pipeline won." A Q1 methods journal will ask "how
stable/significant is that." Add, reusing the re-run notebooks from Phase 2 rather than
rewriting them:
- [ ] **Stability analysis**: bootstrap/subsample the winning pipeline's cluster
      assignments and report agreement (e.g., Adjusted Rand Index across resamples).
      This directly answers the thesis's own Limitation 4 ("no external validation")
      with something concrete rather than leaving it as an acknowledged gap.
- [ ] **Uncertainty on the composite scores**: report variance/CIs across repeated runs
      for the stochastic algorithms (K-Means, DBSCAN), not single-run point estimates —
      Table S1's numbers currently look like single runs.
- [ ] **Sensitivity analysis on the balance-metric weight**: the composite score's 35%
      balance-metric weighting is presented as fixed in the thesis; show how the
      pipeline ranking shifts at, e.g., 20%/35%/50% weight. This turns "we introduced a
      novel balance metric" into a justified, reviewer-defensible design choice instead
      of an assertion — likely the single most common referee question for this metric.

## Phase 4 — Full section drafting

Same content backbone as the old sprint plan's Days 3–10, but at journal length/depth
and built on Phases 1–3's outputs instead of the docx's original numbers:
- [ ] Introduction — condense docx §1.1–1.4, contributions from §1.6.
- [ ] Data & Methods — dataset construction + reconciliation note from Phase 2,
      cleaning/enrichment (Geopy/Meteostat), imputation × clustering design, the
      balance-metric with its new sensitivity justification from Phase 3.
- [ ] Results — re-run numbers and figures from Phase 2, stability/CI results from
      Phase 3.
- [ ] Discussion — the cluster-separation-by-cohort finding against the newly expanded
      related work (Phase 1); keep the missingness-vs-free-text contrast as the headline
      novelty framing.
- [ ] Limitations/Ethics — condense docx §5.5/§6.4; Limitation 4 (no external
      validation) should now reference the Phase 3 stability analysis rather than stand
      as an open gap.
- [ ] Abstract + Conclusion — written last, once the above are stable.
- [ ] Journal-required apparatus the thesis has no equivalent for: **Data Availability
      Statement**, **CRediT author contributions**, **Conflict of Interest**,
      **funding statement** — check the chosen journal's exact required sections.

## Phase 5 — Formatting, review, submission

- [ ] Fit to the chosen journal's template.
- [ ] Circulate to all 5 co-authors + supervisor — flagged in the old plan as the
      biggest schedule risk; start this as soon as a stable full draft exists, not after
      every phase above is 100% polished.
- [ ] Self-plagiarism/prior-thesis disclosure: confirm the journal's policy on
      thesis-derived submissions and add a disclosure footnote if required (most
      publishers run similarity checking automatically — this is submission-blocking if
      skipped, not a formality).
- [ ] Full numeric proofread: every number in the paper must match the Phase 2 re-run
      outputs exactly, not the original docx/Table S1 numbers (easy to mix up since both
      will exist side by side during drafting).
- [ ] Cover letter, suggested reviewers, submission portal.
- [ ] Budget real weeks post-submission for a revision round — Q1 journals essentially
      always send at least one round of major-revision requests; this is normal, not a
      sign the submission was weak.

---

## Suggested pacing

Given the expanded scope, weekly milestones fit better than the old plan's daily ones
(analysis re-runs are compute/team-dependent, not writing-speed-dependent):

- **Week 1:** Phase 0 + Phase 1 (literature merge/dedupe, refs.bib, related-work draft).
- **Weeks 2–3:** Phase 2 (dataset reconciliation is the one hard dependency — don't let
  it slip, everything downstream needs it) + start of Phase 3.
- **Week 4:** Finish Phase 3, start Phase 4 drafting.
- **Weeks 5–6:** Finish Phase 4, Phase 5 formatting + co-author review cycle begins.
- **Weeks 7–8:** Buffer for co-author/supervisor review latency and self-plagiarism
  check, then submit.

## Verification

- `refs.bib` compiles with no missing/orphaned citation keys; every in-text `\cite{}`
  resolves and every entry is actually cited.
- Phase 2's re-run, on the original 1,617-record subset alone, reproduces the docx's
  original Table S1 numbers before trusting any numbers computed on the expanded
  dataset — this confirms the re-run pipeline is faithful to the original before
  changing what data it's fed.
- Every number quoted in `results.tex`/`discussion.tex` traceable to a specific output
  cell in the Phase 2/3 notebooks, not retyped from memory or from the docx.
- Final PDF compiles under the chosen journal's template with no overfull boxes/missing
  figures, and every journal-required section (Data Availability, CRediT, COI) present.
