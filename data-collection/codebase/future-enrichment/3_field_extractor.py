"""
Step 3: Send each article's text to Claude and extract the incident-level
structured fields as strict JSON. Never guesses — every field is null unless
the article explicitly states it.

Usage:
    python 3_field_extractor.py
Input:
    data/articles_raw.jsonl
Output:
    data/articles_extracted.jsonl
"""
import json
import os
import time
from pathlib import Path

from anthropic import Anthropic
from tqdm import tqdm

from config import REASON_CATEGORIES, METHOD_CATEGORIES, PROFESSION_GROUPS

IN_PATH = Path(__file__).parent / "data" / "articles_raw.jsonl"
OUT_PATH = Path(__file__).parent / "data" / "articles_extracted.jsonl"

MODEL = "claude-sonnet-5"  # swap if you want a cheaper/faster model for the pilot

SYSTEM_PROMPT = f"""You are a careful data-extraction assistant building a research
dataset from published Bangla news articles about suicide incidents in Bangladesh.

Extract ONLY facts that are explicitly stated in the article text. Do not infer,
guess, or estimate anything (age, religion, financial condition, reason, etc.)
from names, locations, tone, or general assumptions. If a field is not stated,
its value MUST be null.

Respond with ONLY a single JSON object (no markdown fences, no commentary) with
exactly these keys:

- full_name: string or null (only if named; do not fabricate)
- age: integer or null
- family_members: string or null (e.g. "family of 5", only if stated)
- position_in_siblings: string or null (e.g. "eldest of 3 siblings")
- gender: one of "male", "female", "other", null
- maritual_status: one of "married", "unmarried", "divorced", "widowed", null
- duration_of_separataion: string or null (time since divorce/separation from
  spouse/partner, ONLY if the article ties the incident to that separation)
- profession_group: one of {PROFESSION_GROUPS} or null
- profession_description: string or null (specific stated role/title)
- workplace: string or null
- religion: string or null (ONLY if explicitly stated in the article text)
- financial_condition: string or null (ONLY if explicitly described, e.g. "poor family")
- hometown: string or null (district/upazila/village as stated)
- reason: one of {REASON_CATEGORIES}
- reason_description: string or null (short quote/gloss of the stated reason)
- time: string or null (time of day of the incident, as stated, e.g. "রাতে")
- method: one of {METHOD_CATEGORIES}
- previous_health_condition: string or null (ONLY if explicitly mentioned)
- previous_suicide_attempt: one of "yes", "no", null (null if not mentioned)
- suicide_date: string or null, ISO format YYYY-MM-DD if determinable from the
  article's own text or its published date
"""


def build_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Set ANTHROPIC_API_KEY environment variable first.")
    return Anthropic(api_key=api_key)


def extract_fields(client, article):
    user_content = (
        f"Article URL: {article['url']}\n"
        f"Title: {article['title']}\n"
        f"Published date (raw, may help infer suicide_date): {article.get('published_date_raw', '')}\n\n"
        f"Article text:\n{article['body_text']}"
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    text = resp.content[0].text.strip()
    # Defensive: strip accidental code fences
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def main():
    client = build_client()

    with open(IN_PATH, encoding="utf-8") as f:
        articles = [json.loads(line) for line in f]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as out:
        for article in tqdm(articles, desc="extracting fields"):
            if not article.get("body_text"):
                continue
            try:
                fields = extract_fields(client, article)
                fields["data_source"] = article["url"]
                out.write(json.dumps(fields, ensure_ascii=False) + "\n")
            except Exception as e:
                print(f"FAILED {article['url']}: {e}")
            time.sleep(0.5)  # light throttle; adjust to your rate limits

    print(f"Saved extracted fields to {OUT_PATH}")


if __name__ == "__main__":
    main()
