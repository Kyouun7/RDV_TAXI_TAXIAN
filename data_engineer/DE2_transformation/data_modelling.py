"""
DE2 - Data Modelling (Star Schema)
Creates normalized dimension and fact tables from the transformed data.

Schema:
  dim_zones.parquet              -> zone dimension (265 zones, static reference)
  fact_trips.parquet             -> fact table TAXI ONLY (no weather)
  fact_trips_with_weather.parquet -> fact table TAXI + WEATHER (if blended data exists)

Input:  data/intermediate/tlc_transformed.parquet
        data/intermediate/tlc_with_weather.parquet  (optional)
        data/raw/zones/taxi_zone_lookup.csv
Output: data/intermediate/dim_zones.parquet
        data/intermediate/fact_trips.parquet
        data/intermediate/fact_trips_with_weather.parquet  (if weather data available)
"""

import duckdb
from pathlib import Path

INTERMEDIATE_DIR = Path(__file__).parent.parent / "data" / "intermediate"
ZONES_DIR        = Path(__file__).parent.parent / "data" / "raw" / "zones"

TRANSFORMED_FILE        = INTERMEDIATE_DIR / "tlc_transformed.parquet"
BLENDED_FILE            = INTERMEDIATE_DIR / "tlc_with_weather.parquet"
ZONE_FILE               = ZONES_DIR / "taxi_zone_lookup.csv"

DIM_ZONES_FILE          = INTERMEDIATE_DIR / "dim_zones.parquet"
FACT_TRIPS_FILE         = INTERMEDIATE_DIR / "fact_trips.parquet"
FACT_TRIPS_WEATHER_FILE = INTERMEDIATE_DIR / "fact_trips_with_weather.parquet"

BASE_COLS = """
                ROW_NUMBER() OVER ()        AS trip_id,
                t.pickup_location_id,
                t.dropoff_location_id,
                t.pickup_datetime,
                t.dropoff_datetime,
                t.pickup_hour_key,
                t.passenger_count,
                t.trip_distance,
                t.trip_duration_min,
                t.avg_speed_mph,
                t.fare_amount,
                t.tip_amount,
                t.total_amount,
                t.tip_rate_pct,
                t.payment_type,
                t.pickup_hour,
                t.pickup_day_of_week,
                t.pickup_month,
                t.time_of_day,
                t.is_rush_hour,
                t.is_weekend,
                t.pickup_zone,
                t.pickup_borough,
                t.pickup_service_zone,
                t.dropoff_zone,
                t.dropoff_borough
"""

WEATHER_COLS = """
                t.temperature_2m,
                t.apparent_temperature,
                t.precipitation,
                t.snowfall,
                t.windspeed_10m,
                t.weather_category,
"""


def create_dim_zones(con: duckdb.DuckDBPyConnection):
    print("[MODEL] Creating dim_zones...")
    con.execute(f"""
        COPY (
            SELECT
                CAST(LocationID AS INTEGER) AS zone_id,
                Zone                        AS zone_name,
                Borough                     AS borough,
                service_zone
            FROM read_csv_auto('{ZONE_FILE}')
            ORDER BY zone_id
        ) TO '{DIM_ZONES_FILE}' (FORMAT PARQUET)
    """)
    count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{DIM_ZONES_FILE}')").fetchone()[0]
    print(f"[DONE] dim_zones: {count} zones saved.")


def create_fact_trips(con: duckdb.DuckDBPyConnection):
    print("[MODEL] Creating fact_trips (taxi only)...")
    con.execute(f"""
        COPY (
            SELECT
                {BASE_COLS}
            FROM read_parquet('{TRANSFORMED_FILE}') t
            ORDER BY t.pickup_datetime
        ) TO '{FACT_TRIPS_FILE}' (FORMAT PARQUET)
    """)
    count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{FACT_TRIPS_FILE}')").fetchone()[0]
    print(f"[DONE] fact_trips: {count:,} rows saved.")


def create_fact_trips_with_weather(con: duckdb.DuckDBPyConnection):
    if not BLENDED_FILE.exists():
        print("[SKIP] tlc_with_weather.parquet not found — skipping fact_trips_with_weather.")
        return

    print("[MODEL] Creating fact_trips_with_weather (taxi + weather)...")
    con.execute(f"""
        COPY (
            SELECT
                {WEATHER_COLS}
                {BASE_COLS}
            FROM read_parquet('{BLENDED_FILE}') t
            ORDER BY t.pickup_datetime
        ) TO '{FACT_TRIPS_WEATHER_FILE}' (FORMAT PARQUET)
    """)
    count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{FACT_TRIPS_WEATHER_FILE}')").fetchone()[0]
    print(f"[DONE] fact_trips_with_weather: {count:,} rows saved.")


def run_modelling():
    if not TRANSFORMED_FILE.exists():
        raise FileNotFoundError(f"Run feature_engineering.py first. Missing: {TRANSFORMED_FILE}")
    if not ZONE_FILE.exists():
        raise FileNotFoundError(f"Run zone_ingestion.py first. Missing: {ZONE_FILE}")

    con = duckdb.connect()
    create_dim_zones(con)
    create_fact_trips(con)
    create_fact_trips_with_weather(con)
    con.close()

    print()
    print("[COMPLETE] Data model ready for analyst and ML engineer:")
    print(f"  dim_zones.parquet              -> {DIM_ZONES_FILE}")
    print(f"  fact_trips.parquet             -> {FACT_TRIPS_FILE}  (taxi only)")
    if BLENDED_FILE.exists():
        print(f"  fact_trips_with_weather.parquet -> {FACT_TRIPS_WEATHER_FILE}  (taxi + weather)")
    else:
        print(f"  fact_trips_with_weather.parquet -> [SKIPPED — run weather_ingestion.py first]")


if __name__ == "__main__":
    run_modelling()
