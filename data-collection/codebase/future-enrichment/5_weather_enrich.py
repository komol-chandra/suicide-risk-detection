"""
Step 5: For each row with a suicide_date + latitude/longitude, fetch historical
weather from OpenWeatherMap's One Call 3.0 "timemachine" endpoint.

IMPORTANT: This endpoint requires a One Call API 3.0 subscription (it has a free
1,000-calls/day tier, but you must explicitly subscribe to that product in your
OpenWeatherMap account — a plain legacy free-tier key will get a 401). Confirm
this before running at scale.

Usage:
    python 5_weather_enrich.py
Input:
    data/articles_geocoded.jsonl
Output:
    data/articles_weathered.jsonl
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from tqdm import tqdm

IN_PATH = Path(__file__).parent / "data" / "articles_geocoded.jsonl"
OUT_PATH = Path(__file__).parent / "data" / "articles_weathered.jsonl"

TIMEMACHINE_URL = "https://api.openweathermap.org/data/3.0/onecall/timemachine"

WEATHER_FIELDS = [
    "unix_time", "feels_like", "temp_min", "temp_max", "air_pressure",
    "air_humidity", "wind_speed", "wind_deg", "clouds_sky", "weather_main",
    "weather_description",
]


def date_to_unix_noon_utc(date_str):
    """Use local noon as a representative timestamp for the day (BD is UTC+6)."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dt = dt.replace(hour=6, minute=0, tzinfo=timezone.utc)  # ~noon in Dhaka
    return int(dt.timestamp())


def fetch_weather(lat, lon, unix_ts, api_key):
    resp = requests.get(TIMEMACHINE_URL, params={
        "lat": lat, "lon": lon, "dt": unix_ts, "appid": api_key, "units": "metric",
    }, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("data"):
        return None
    d = data["data"][0]
    weather = (d.get("weather") or [{}])[0]
    return {
        "unix_time": d.get("dt"),
        "feels_like": d.get("feels_like"),
        "temp_min": d.get("temp"),  # timemachine gives a single temp, not min/max
        "temp_max": d.get("temp"),
        "air_pressure": d.get("pressure"),
        "air_humidity": d.get("humidity"),
        "wind_speed": d.get("wind_speed"),
        "wind_deg": d.get("wind_deg"),
        "clouds_sky": d.get("clouds"),
        "weather_main": weather.get("main"),
        "weather_description": weather.get("description"),
    }


def main():
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENWEATHER_API_KEY environment variable first.")

    with open(IN_PATH, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]

    with open(OUT_PATH, "w", encoding="utf-8") as out:
        for row in tqdm(rows, desc="fetching weather"):
            for field in WEATHER_FIELDS:
                row.setdefault(field, None)

            if row.get("latitude") and row.get("suicide_date"):
                try:
                    unix_ts = date_to_unix_noon_utc(row["suicide_date"])
                    weather = fetch_weather(row["latitude"], row["longitude"], unix_ts, api_key)
                    if weather:
                        row.update(weather)
                except Exception as e:
                    print(f"FAILED weather for {row.get('data_source')}: {e}")
                time.sleep(1)  # stay well under rate limits

            out.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Saved weather-enriched rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
