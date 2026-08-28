"""Shared configuration for the pilot pipeline."""

# --- Search scope -----------------------------------------------------------

# Keyword variants — Prothom Alo search matches literal phrases, so one keyword
# ("আত্মহত্যা করেছে") misses many valid articles. Broaden coverage with variants.
KEYWORDS = [
    "আত্মহত্যা করেছে",
    "আত্মহত্যা করেন",
    "আত্মহত্যা",
    "আত্মহনন",
    "গলায় ফাঁস দিয়ে",
    "বিষপান করে",
    "ফাঁস দিয়ে আত্মহত্যা",
]

# Pilot: small, recent date window to validate the pipeline end-to-end first.
# Format: YYYY-MM-DD. Widen / move back once validated.
PILOT_START_DATE = "2026-06-01"
PILOT_END_DATE = "2026-08-25"

# Prothom Alo repeats results after ~5-6 days of results on one search page
# (observed by prior scrapers), so chunk the date range into short windows.
DATE_CHUNK_DAYS = 5

PILOT_TARGET_ARTICLE_COUNT = 100

# --- Networking ---------------------------------------------------------

BASE_SEARCH_URL = "https://www.prothomalo.com/search"
REQUEST_DELAY_SECONDS = 1.5
PLAYWRIGHT_HEADLESS = True
LOAD_MORE_CLICK_LIMIT = 30  # safety cap per date-chunk search

# --- Output schema (exact column order requested) ---------------------------

FINAL_COLUMNS = [
    "data_source", "full_name", "age", "age_group", "family_members",
    "position_in_siblings", "gender", "maritual_status",
    "duration_of_separataion", "profession_group", "profession_description",
    "workplace", "religion", "financial_condition", "hometown",
    "latitude", "longitude", "reason", "reason_description", "time",
    "method", "previous_health_condition", "previous_suicide_attempt",
    "suicide_date", "unix_time", "feels_like", "temp_min", "temp_max",
    "air_pressure", "air_humidity", "wind_speed", "wind_deg",
    "clouds_sky", "weather_main", "weather_description",
]

# Controlled vocabularies used by the extraction prompt (edit to taste)
REASON_CATEGORIES = [
    "dowry", "marital_conflict", "exam_failure", "financial_distress",
    "harassment", "love_failure", "domestic_violence", "workplace_issue",
    "mental_health", "family_conflict", "sexual_abuse", "unknown", "other",
]

METHOD_CATEGORIES = [
    "hanging", "poisoning", "jumping", "self_immolation", "firearm",
    "drowning", "cutting", "other", "unknown",
]

PROFESSION_GROUPS = [
    "student", "housewife", "farmer", "business", "service_holder",
    "day_laborer", "unemployed", "government_employee", "garment_worker",
    "other", "unknown",
]
