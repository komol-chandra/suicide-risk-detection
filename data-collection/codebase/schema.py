# -*- coding: utf-8 -*-
"""
schema.py

Single source of truth for the suicide-incident dataset's column structure,
shared by download_search_results.py and (via the template CSV) documented
for human coders. Extends the original prothomalo-only schema
(extract_suicide_data.py's FIELDNAMES) to support multiple news outlets.

Changes from the original schema:
- `data_source` (which actually held the article URL) is split into
  `source_name` (outlet key, e.g. "prothomalo") and `article_url`.
- Typos fixed: maritual_status -> marital_status,
  duration_of_separataion -> duration_of_separation.
- `suicide_date`/`unix_time` (which were really the article's publish date,
  not necessarily the date of death) are renamed `publication_date` /
  `publication_unix_time`; a separate `incident_date` column is added for
  when the article explicitly states a different date, left blank
  otherwise rather than guessed (see `_evidence_incident_date`).
- New columns: article_title, language, search_query, collected_at
  (collection provenance); content_hash, word_count, extraction_status,
  duplicate_of (dedup/QA); raw_html_path (traceability to the saved HTML);
  coder_reviewed/coder_name/coder_reviewed_at (human review tracking).

Anonymization convention (unchanged from extract_suicide_data.py): no
victim names, no exact addresses — case_id is a hash, hometown is
district-level only. See ../../CLAUDE.md.
"""

FIELDNAMES = [
    # identity / provenance
    "case_id", "source_name", "article_url", "article_title", "language",
    "search_query", "collected_at",
    # victim demographics
    "age", "age_group", "gender", "profession_group", "hometown",
    "latitude", "longitude",
    # incident details
    "reason", "reason_description", "method", "previous_suicide_attempt",
    "publication_date", "publication_unix_time", "incident_date",
    # manual-coding columns (human-in-the-loop; left blank for a human coder)
    "family_members", "position_in_siblings", "marital_status",
    "duration_of_separation", "financial_condition",
    "previous_health_condition",
    # evidence snippets, to speed up manual coding
    "_evidence_reason", "_evidence_method", "_evidence_previous_attempt",
    "_evidence_incident_date",
    # dedup / QA
    "content_hash", "word_count", "extraction_status", "duplicate_of",
    # collection provenance
    "raw_html_path",
    # human review tracking
    "coder_reviewed", "coder_name", "coder_reviewed_at",
]
