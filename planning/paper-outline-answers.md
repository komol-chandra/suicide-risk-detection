# Paper outline — answers (capstone → paper conversion)

Answers to the 9-item outline, in plain language, pulled from
`prior-work/newly formated capstone report 2025.docx`, `SPRINT_PLAN.md`,
and the capstone notebooks/CSV. This is a reference note, not the paper
itself — the actual manuscript goes under `paper/sections/` per
`SPRINT_PLAN.md`.

## Open decisions (need the team, not derivable from the repo)

- **Record count mismatch**: thesis text says **1,617** records; the actual
  CSV (`prior-work/SuicideBD-dataset - SuicideBD-dataset.csv`) has **1,797**
  data rows. Confirm which number is correct before it goes in the paper.
- **Who writes which section** — not recorded anywhere in the repo. Suggest
  splitting by `SPRINT_PLAN.md`'s day-by-day tasks.

## 1. Title

*"A Machine Learning Approach to Identifying Influential Factors and
Clustering Patterns in Suicide Occurrences"* — the existing thesis title
(`Capstone_Project_Report.zip` → `cover_page.tex`).

Shorter paper-style alternative: *"Clustering Bangladeshi Suicide Incidents
from Incomplete Newspaper Data."*

## 2. Literature review

Prior work on Bangladesh/South Asia suicide either counts cases
(epidemiology) or detects risk from text (NLP on social media/notes).
Nobody had built a large, enriched Bangladeshi suicide dataset with proper
missing-data handling and clustering. This study fills that gap — structured
data, not free text.

## 3. Limitations of the review

1. Data source bias — newspaper-reported completed suicides only, misses
   rural/hidden cases.
2. 1,617 records is the largest curated dataset to date, but still small
   for ML, and heavily missing in places.
3. Didn't exhaustively test every hyperparameter setting for each algorithm.
4. No ground-truth labels — fully unsupervised, no external validation.
5. Bangla free-text columns (`profession_description`, `reason_description`)
   excluded, no NLP tooling used on them.
6. Weather data (Meteostat) is patchy for rural stations, so weather
   variables stayed substantially incomplete.

## 4. Algorithm & model used

Two stages: first, fill in missing data three different ways (MICE, KNN,
MissForest), each with two predictor strategies. Then group the records
four different ways (K-Means, Agglomerative, DBSCAN, Spectral). That's 32
combinations tested. Winner: **Agglomerative clustering on MissForest
(no-context) imputed data**.

## 5. Dataset

Bangladeshi suicide-incident records collected from newspapers
(Dhaka Tribune-based), covering 2017–2025, expanded from an earlier 760-case
dataset by adding 857 new cases and 9 new attributes. Thesis text reports
1,617 records; the CSV file has 1,797 rows (see open decision above).

## 6. Data processing

Raw newspaper data has heavy missingness (over 90% for some columns) before
clustering. Missing values were filled in three statistical ways, tried both
with and without extra context, producing 8 versions of the dataset to run
clustering on.

## 7. Working plan

Already written out day-by-day in `SPRINT_PLAN.md`. As of 2026-08-29, the
project is on **Day 13 of 14** — proofreading and checking the paper doesn't
count as duplicate publication of the thesis. Day 14 (2026-08-30) is final
polish and submission.

## 8. What we're going to do

Turn the already-finished thesis into a short, submittable conference paper.
No new experiments — the dataset and all 32 pipeline results already exist.
This is a writing and formatting job, not new research.

## 9. Team, tools, and expected outcome

**Team**: Mohammed Akash, Md Arifuzzan, Sajedul Islam, Komol Chandra
Devnath, Anisul Haque Bhuiyan — supervised by Md. Mamun Hossain (BUBT CSE).
Task split by paper section is not yet decided (see open decisions above).

**Tools & technology**: Google Colab notebooks, Python (pandas, numpy), and
scikit-learn for everything else — `KNNImputer` and `IterativeImputer`
(MICE) for filling missing values, `RandomForestRegressor`/`Classifier` for
MissForest, and `KMeans`, `AgglomerativeClustering`, `DBSCAN`,
`SpectralClustering` for grouping. The paper itself is written in LaTeX.

**Conclusion / expected outcome**: even messy, mostly-incomplete newspaper
data can still reveal real, meaningful patterns with the right combination
of missing-data-filling method and clustering algorithm. The goal isn't a
new method for its own sake — it's a step toward more evidence-based
suicide-prevention work in Bangladesh using data that already exists.
