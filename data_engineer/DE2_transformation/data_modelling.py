"""
DE2 - Data Modelling (Star Schema)
Creates normalized dimension and fact tables from the transformed data.

Schema:
  dim_zones.parquet   -> zone dimension (265 zones, static reference)
  fact_trips.parquet  -> main fact table (FK references to dim_zones)

Input:  data/intermediate/tlc_transformed.parquet
        data/raw/zones/taxi_zone_lookup.csv
Output: data/intermediate/dim_zones.parquet
        data/intermediate/fact_trips.parquet
"""

import duckdb
from pathlib import Path

INTERMEDIATE_DIR = Path(__file__).parent.parent / "data" / "intermediate"
ZONES_DIR        = Path(__file__).parent.parent / "data" / "raw" / "zones"

TRANSFORMED_FILE = INTERMEDIATE_DIR / "tlc_transformed.parquet"
ZONE_FILE        = ZONES_DIR / "taxi_zone_lookup.csv"

DIM_ZONES_FILE   = INTERMEDIATE_DIR / "dim_zones.parquet"
FACT_TRIPS_FILE  = INTERMEDIATE_DIR / "fact_trips.parquet"


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
    print("[MODEL] Creating fact_trips...")

    # Check if weather-blended data exists, use it if available
    blended_file = INTERMEDIATE_DIR / "tlc_with_weather.parquet"
    source_file = blended_file if blended_file.exists() else TRANSFORMED_FILE
    print(f"[INFO] Source: {source_file.name}")

    has_weather = blended_file.exists()

    weather_cols = """
                t.temperature_2m,
                t.precipitation,
                t.snowfall,
                t.windspeed_10m,
                t.weather_category,
    """ if has_weather else ""

    con.execute(f"""
        COPY (
            SELECT
                -- Keys
                ROW_NUMBER() OVER ()        AS trip_id,
                t.pickup_location_id,
                t.dropoff_location_id,

                -- Timestamps
                t.pickup_datetime,
                t.dropoff_datetime,
                t.pickup_hour_key,

                -- Trip metrics
                t.passenger_count,
                t.trip_distance,
                t.trip_duration_min,
                t.avg_speed_mph,

                -- Financial
                t.fare_amount,
                t.tip_amount,
                t.total_amount,
                t.tip_rate_pct,
                t.payment_type,

                -- Time dimensions
                t.pickup_hour,
                t.pickup_day_of_week,
                t.pickup_month,
                t.time_of_day,
                t.is_rush_hour,
                t.is_weekend,

                {weather_cols}

                -- Denormalized zone info (for fast query without joins)
                t.pickup_zone,
                t.pickup_borough,
                t.pickup_service_zone,
                t.dropoff_zone,
                t.dropoff_borough

            FROM read_parquet('{source_file}') t
            ORDER BY t.pickup_datetime
        ) TO '{FACT_TRIPS_FILE}' (FORMAT PARQUET)
    """)

    count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{FACT_TRIPS_FILE}')").fetchone()[0]
    print(f"[DONE] fact_trips: {count:,} rows saved.")


def run_modelling():
    if not TRANSFORMED_FILE.exists():
        raise FileNotFoundError(f"Run feature_engineering.py first. Missing: {TRANSFORMED_FILE}")
    if not ZONE_FILE.exists():
        raise FileNotFoundError(f"Run zone_ingestion.py first. Missing: {ZONE_FILE}")

    con = duckdb.connect()
    create_dim_zones(con)
    create_fact_trips(con)
    con.close()

    print()
    print("[COMPLETE] Data model ready for analyst and ML engineer:")
    print(f"  dim_zones.parquet   -> {DIM_ZONES_FILE}")
    print(f"  fact_trips.parquet  -> {FACT_TRIPS_FILE}")


if __name__ == "__main__":
    run_modelling()
