"""
DE1 - Open-Meteo Weather Data Ingestion
Fetches hourly historical weather data for NYC (Sept 2025 - Jan 2026).
Output: data/raw/weather/nyc_weather_hourly.parquet
"""

import requests
import pandas as pd
from pathlib import Path

RAW_WEATHER_DIR = Path(__file__).parent.parent / "data" / "raw" / "weather"
OUTPUT_FILE = RAW_WEATHER_DIR / "nyc_weather_hourly.parquet"

NYC_LAT = 40.7128
NYC_LON = -74.0060
START_DATE = "2025-09-01"
END_DATE = "2026-01-31"

WEATHER_VARIABLES = [
    "temperature_2m",
    "precipitation",
    "snowfall",
    "windspeed_10m",
    "weathercode",
]


def fetch_weather() -> pd.DataFrame:
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": NYC_LAT,
        "longitude": NYC_LON,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": ",".join(WEATHER_VARIABLES),
        "timezone": "America/New_York",
    }

    print(f"[FETCH] Open-Meteo API: {START_DATE} to {END_DATE}")
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    data = response.json()
    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    df = df.rename(columns={"time": "datetime"})

    return df


def run_ingestion():
    RAW_WEATHER_DIR.mkdir(parents=True, exist_ok=True)

    if OUTPUT_FILE.exists():
        print(f"[SKIP] {OUTPUT_FILE.name} already exists.")
        return

    df = fetch_weather()
    df.to_parquet(OUTPUT_FILE, index=False)
    print(f"[DONE] Weather data saved: {OUTPUT_FILE} ({len(df)} rows)")


if __name__ == "__main__":
    run_ingestion()
