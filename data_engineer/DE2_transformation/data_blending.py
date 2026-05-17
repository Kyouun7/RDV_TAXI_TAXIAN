"""
DE2 - Data Blending (Taxi + Weather) — OPTIONAL
Joins transformed taxi data with hourly weather data on pickup_hour_key.
Only runs if weather data exists in data/raw/weather/.

Input:  data/intermediate/tlc_transformed.parquet
        data/raw/weather/nyc_weather_hourly.parquet  (optional)
Output: data/intermediate/tlc_with_weather.parquet
"""

import duckdb
from pathlib import Path

INTERMEDIATE_DIR = Path(__file__).parent.parent / "data" / "intermediate"
RAW_WEATHER_DIR = Path(__file__).parent.parent / "data" / "raw" / "weather"

TLC_FILE = INTERMEDIATE_DIR / "tlc_transformed.parquet"
WEATHER_FILE = RAW_WEATHER_DIR / "nyc_weather_hourly.parquet"
OUTPUT_FILE = INTERMEDIATE_DIR / "tlc_with_weather.parquet"


def blend_data():
    if not TLC_FILE.exists():
        raise FileNotFoundError(f"Run feature_engineering.py first. Missing: {TLC_FILE}")

    if not WEATHER_FILE.exists():
        print("[SKIP] Weather data not found — skipping blend. Run weather_ingestion.py to enable.")
        return False

    print("[BLEND] Joining taxi data with weather data...")
    con = duckdb.connect()

    query = f"""
        COPY (
            SELECT
                t.*,
                w.temperature_2m,
                w.apparent_temperature,
                w.precipitation,
                w.snowfall,
                w.windspeed_10m,
                w.weathercode,

                CASE
                    WHEN w.snowfall > 0 THEN 'snow'
                    WHEN w.precipitation > 5 THEN 'heavy_rain'
                    WHEN w.precipitation > 0 THEN 'light_rain'
                    WHEN w.temperature_2m < 0 THEN 'freezing'
                    ELSE 'clear'
                END AS weather_category

            FROM read_parquet('{TLC_FILE}') t
            LEFT JOIN read_parquet('{WEATHER_FILE}') w
                ON t.pickup_hour_key = w.datetime
        ) TO '{OUTPUT_FILE}' (FORMAT PARQUET)
    """

    con.execute(query)

    row_count = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{OUTPUT_FILE}')"
    ).fetchone()[0]
    print(f"[INFO] Blended rows: {row_count:,}")
    print(f"[DONE] Saved to {OUTPUT_FILE}")
    con.close()
    return True


if __name__ == "__main__":
    blend_data()
