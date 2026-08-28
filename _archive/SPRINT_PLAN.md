# 14-Day Sprint Plan — Suicide Risk Detection Paper

**Goal:** convert the finished BUBT capstone thesis into a submittable
conference/journal paper. **No new experiments, no new data collection** —
the dataset (1,617 records), all 32 imputation×clustering pipelines, and the
results are already done. This sprint is a writing, sourcing, and formatting
job, scoped in [SPRINT_TRACKER.md](../SPRINT_TRACKER.md#3-suicide-risk-detection).

Start: **2026-08-17** · End: **2026-08-30** (14 calendar days). Adjust dates
if you start on a different day — the day numbers matter more than the dates.

## What already exists (verified this session)

| Source | Location | Contains |
|---|---|---|
| Full thesis text | `prior-work/newly formated capstone report 2025.docx` | All 6 chapters, ~147k chars, **authoritative content** — intro, lit review, methodology, results, discussion, limitations, future work, and a **42-entry reference list** (plain text, end of doc) |
| LaTeX thesis skeleton | `prior-work/Capstone_Project_Report.zip` | BUBT thesis template: `main.tex`, `chapter1.tex`, `chapter2.tex`, `chapter3.tex` (chapters 4–6 were never converted to LaTeX — docx is ahead of the tex), `cover_page.tex`, `ref.bib` (only 2 placeholder entries — advisor's own papers, not the real 42), `image/methodology.png`, `image/method.png` |
| Notebooks + raw results | `prior-work/capstone-....zip` → `capstone/` | 12 numbered notebooks (`0_preprocessing` → `11_comparing-clustering`), all imputed datasets (`.xlsx`), and `capstone/report/11_comparing-clustering.ipynb - Colab.pdf` (3.6 MB, PDF export of the final comparison notebook — likely already has publication-candidate figures rendered) |
| New literature (uncited by thesis) | `literature/*.pdf` | 9 papers: 3 South Asia suicide-epidemiology reviews, 1 suicide-risk-detection perspective piece, 5 NLP/ML suicide/ideation-detection papers. None of these are in the thesis's own 42-ref list — they're a second, newer batch. |
| Author/team info | `cover_page.tex` / `Declaration.tex` | Title: *"A Machine Learning Approach to Identifying Influential Factors and Clustering Patterns in Suicide Occurrences"*. Authors: Mohammed Akash, Md Arifuzzan, Sajedul Islam, Komol Chandra Devnath, Anisul Haque Bhuiyan. Supervisor: Md. Mamun Hossain (BUBT CSE) |
| Best result | docx §6.1–6.2 | Best pipeline = Agglomerative Clustering + MissForest (no-context), composite score 27.30/32, two-cluster solution that organically separated by data-collection cohort (2020 vs 2017–2025) |
| Full metrics table | docx Appendix, Table S1 | All 32 pipelines' raw scores (balance, silhouette, Calinski-Harabasz, Dunn, Davies-Bouldin, Xie-Beni, composite) — ready to become a paper table |

The `ref.bib` gap is real: the 42 sources exist only as plain-text citations
at the end of the docx, not as BibTeX. Building the real `.bib` is on the
critical path (Day 2).

## Working structure for this sprint

Create a `paper/` folder inside `suicide-risk-detection/` (kept separate
from `prior-work/`, which stays as the untouched thesis archive):

```
suicide-risk-detection/paper/
├── main.tex               venue template (chosen Day 1)
├── refs.bib                real bibliography, built Day 2
├── sections/
│   ├── abstract.tex
│   ├── introduction.tex
│   ├── related-work.tex
│   ├── methodology.tex
│   ├── results.tex
│   ├── discussion.tex
│   └── conclusion.tex
└── figures/                 extracted/regenerated, publication-ready
```

---

## Day-by-day

**Day 1 — Scope, venue, skeleton**
- Pick target venue/template and page limit. `ref.bib`'s two placeholder
  entries are the supervisor's own ICCIT/IJACSA papers — a strong hint the
  usual target is an IEEE double-column conference (e.g. ICCIT-style, ~6
  pages). Confirm with the team/supervisor rather than assuming.
- Set up `paper/` with the chosen template's `main.tex` and empty
  `sections/*.tex` stubs.
- Write a bullet-point abstract skeleton (problem → gap → method → best
  result → contribution) to pin the paper's scope before drafting prose.
- Confirm author order and affiliations against `Declaration.tex`.

**Day 2 — Bibliography**
- Transcribe all 42 references from the docx's plain-text reference list
  into `refs.bib` as real BibTeX entries (replace the 2 placeholders).
- Cross-check numbering against in-text citations in the docx (`[1]`,
  `[2]`, `[12,13]`, etc.) so citation keys map 1:1 — the docx's own bracket
  numbers got mangled by the .docx→text extraction in a few spots, so verify
  each one against context, not just position.

**Day 3 — Related work: fold in the new literature**
- Read the 9 PDFs in `literature/`. Group them: (a) South Asia
  epidemiology — Arafat (Global Mental Health), Rahman et al. (BMJ Open
  protocol), Borah & Jose (F1000 protocol) — use these to strengthen the
  "burden of suicide in Bangladesh/South Asia" framing already in docx
  §2.2. (b) NLP/ML suicide-detection — Zhang et al. (transformer suicide
  notes), Fernandes et al. (NLP on clinical records), Ezerceli & Dehkharghani
  (deep nets on social media), Li et al. (visual behaviour pipeline),
  Ghanadian et al. (LLM synthetic data), Parsapoor et al. (perspective) —
  use these to sharpen the paper's novelty claim: *this study clusters
  structured, incomplete newspaper records rather than mining free text*,
  a genuinely different (and complementary) angle worth stating explicitly.
- Add these 9 as new `refs.bib` entries (now ~51 total).
- Draft `related-work.tex` — condense docx Chapter 2 (2.2–2.6) down from a
  thesis-length review to a paper-length one (roughly 500–800 words),
  positioned around the gap statement already in docx §2.6/§1.3.

**Day 4 — Introduction**
- Condense docx §1.1–1.4 (background, problem statement, objectives) into
  `introduction.tex` (~400–600 words). Keep the 6 research objectives as a
  tight paragraph, not a bulleted list, to fit paper conventions.
- State the paper's contributions explicitly (docx §1.6 already has these
  pre-written as 5 bullets — trim to 3–4).

**Day 5 — Methodology**
- Condense docx Chapter 3 into `methodology.tex`: dataset construction
  (760→1,617 records, 9 new attributes), cleaning + Geopy/Meteostat
  conditional filling, the 3 imputation methods × 2 predictor strategies
  (6 variants + 2 baselines = 8 datasets), the 4 clustering algorithms (32
  pipelines total), and the composite balance-aware scoring metric.
- Reuse `image/methodology.png` and `image/method.png` from the tex archive
  if they're still accurate; otherwise redraw a compact pipeline diagram.

**Day 6 — Extract figures & tables from notebooks**
- Pull embedded output images directly from
  `capstone/11_comparing-clustering.ipynb` and/or
  `capstone/report/11_comparing-clustering.ipynb - Colab.pdf` — no need to
  re-run any notebook. Target: composite-score ranking chart, PCA cluster
  scatter for the winning pipeline (`agg_rf_no_context`), missingness
  before/after comparison.
- Turn the appendix Table S1 (already in the docx, all 32 rows) into a
  proper LaTeX table — full table as a supplementary table, a top-10
  condensed version in the main results section.

**Day 7 — Results**
- Draft `results.tex` from docx Chapter 4/6.2: pipeline comparison summary,
  why MissForest > MICE/KNN, why imputed >> non-imputed baselines, why the
  balance metric mattered (the DBSCAN-noise-majority finding is a strong,
  concrete example — keep it), and the winning two-cluster solution.

**Day 8 — Discussion**
- Interpret the cluster-separation-by-cohort finding (docx §6.2 Finding 4)
  against the newly added related work: what does it imply given the NLP
  literature detects risk from *text*, while this study detects structure
  from *missingness patterns and metadata*? This contrast is the paper's
  most defensible novelty angle — make it explicit here, not just implied.

**Day 9 — Limitations, ethics, future work**
- Condense docx §5.5/§6.4 (6 limitations) to the 3–4 a reviewer will
  actually push on: data-source bias, no external validation, exclusion of
  Bangla free-text columns.
- Ethics: docx Chapter 5 already discusses societal impact/ethics for the
  thesis version — adapt for a paper-length ethics/data-statement paragraph
  (newspaper-sourced, publicly reported cases, no individually identifying
  claims made).
- Future work: trim docx §6.5's 6 directions to 2–3, prioritizing ones a
  reviewer would find most credible as immediate next steps (feature-driven
  cluster interpretation, Bangla NLP on the excluded free-text columns).

**Day 10 — Abstract + conclusion + first full assembly**
- Write final abstract (150–250 words, venue-dependent limit) from the Day
  1 skeleton, now grounded in the actually-written sections.
- Write `conclusion.tex` from docx §6.6, cut to paper length.
- Assemble `main.tex` end to end; get a compiling draft with placeholder
  figure files if any extraction is still pending from Day 6.

**Day 11 — Fit-to-venue pass**
- Apply the chosen template precisely (columns, fonts, margins per Day-1
  decision). Trim prose until the paper is under the page limit — this
  version is being cut down from a 147k-character thesis, so expect this
  pass to be substantial, not cosmetic.
- Finalize all figure/table captions and cross-references.

**Day 12 — Internal review**
- Circulate to co-authors and the supervisor (Md. Mamun Hossain) for a
  read-through — plan for this to take a day even if your own edits are
  done, since 5 co-authors is where most schedule slippage tends to happen.
- Specifically ask the supervisor to sanity-check the novelty framing
  against the new literature (Day 3) — that framing is new relative to the
  thesis and hasn't been vetted by them yet.

**Day 13 — Self-plagiarism / duplicate-publication check**
- Because this paper is substantially derived from an already-submitted
  university thesis, confirm the target venue's policy on prior-thesis
  material (most conferences allow it but expect a disclosure footnote,
  e.g. "based on the first author's undergraduate thesis at BUBT"). Add
  that disclosure if required. This is a real submission-blocking risk if
  skipped, not a formality.
- Full proofreading pass; verify every number in the paper (composite
  scores, missingness percentages, record counts) matches the docx/Table S1
  source exactly — condensing 147k characters by hand is where transcription
  errors creep in.

**Day 14 — Final polish + submission**
- Final compile, reference check (all `refs.bib` entries actually cited,
  no orphaned citations), file-naming per venue's submission instructions.
- Cover letter (if required) and submission-portal upload.
- Keep this day as buffer — if Day 12's co-author review surfaces
  substantive change requests, they land here.

---

## Biggest risks to this timeline

1. **Co-author/supervisor review latency (Day 12)** — 5 authors + 1
   supervisor is the most likely place the 14 days slip. Send the draft
   for review as early as a stable draft exists, not literally on Day 12.
2. **Reference transcription (Day 2)** — 42 hand-typed citations from a
   docx, several missing their bracket numbers in the raw text, is fiddly
   and error-prone. Budget real time for it rather than treating it as
   mechanical.
3. **Venue page limit vs. thesis depth (Day 11)** — a 6-page IEEE format
   from a 147k-character, 6-chapter thesis is an aggressive cut. If the
   chosen venue allows 8–10 pages instead of 6, Day 11 gets much easier —
   worth factoring into the Day 1 venue decision.
