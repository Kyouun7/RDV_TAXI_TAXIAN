"""
DE2 - Feature Engineering & Transformation
Adds derived columns needed for clustering and analysis.
Also joins taxi zone lookup to decode PULocationID/DOLocationID into
human-readable zone names and boroughs for geographic analysis.

Input:  data/intermediate/tlc_cleaned.parquet
        data/raw/zones/taxi_zone_lookup.csv
Output: data/intermediate/tlc_transformed.parquet
"""

import duckdb
from pathlib import Path

INTERMEDIATE_DIR = Path(__file__).parent.parent / "data" / "intermediate"
ZONES_DIR        = Path(__file__).parent.parent / "data" / "raw" / "zones"

INPUT_FILE  = INTERMEDIATE_DIR / "tlc_cleaned.parquet"
ZONE_FILE   = ZONES_DIR / "taxi_zone_lookup.csv"
OUTPUT_FILE = INTERMEDIATE_DIR / "tlc_transformed.parquet"


def transform_tlc():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Run cleaning.py first. Missing: {INPUT_FILE}")
    if not ZONE_FILE.exists():
        raise FileNotFoundError(f"Run zone_ingestion.py first. Missing: {ZONE_FILE}")

    print(f"[TRANSFORM] Reading cleaned data from {INPUT_FILE}")
    con = duckdb.connect()

    query = f"""
        COPY (
            SELECT
                -- Original columns with proper types
                CAST(t.tpep_pickup_datetime AS TIMESTAMP)  AS pickup_datetime,
                CAST(t.tpep_dropoff_datetime AS TIMESTAMP) AS dropoff_datetime,
                CAST(t.passenger_count AS INTEGER)         AS passenger_count,
                CAST(t.trip_distance AS DOUBLE)            AS trip_distance,
                CAST(t.PULocationID AS INTEGER)            AS pickup_location_id,
                CAST(t.DOLocationID AS INTEGER)            AS dropoff_location_id,
                CAST(t.payment_type AS INTEGER)            AS payment_type,
                CAST(t.fare_amount AS DOUBLE)              AS fare_amount,
                CAST(t.tip_amount AS DOUBLE)               AS tip_amount,
                CAST(t.total_amount AS DOUBLE)             AS total_amount,

                -- Zone names decoded from PULocationID / DOLocationID
                pu.Zone    AS pickup_zone,
                pu.Borough AS pickup_borough,
                pu.service_zone AS pickup_service_zone,
                doz.Zone    AS dropoff_zone,
                doz.Borough AS dropoff_borough,

                -- Derived: trip duration in minutes
                ROUND(
                    EXTRACT(EPOCH FROM (t.tpep_dropoff_datetime - t.tpep_pickup_datetime)) / 60.0, 2
                ) AS trip_duration_min,

                -- Derived: tip rate as percentage of fare
                ROUND(
                    CASE WHEN t.fare_amount > 0
                         THEN (t.tip_amount / t.fare_amount) * 100.0
                         ELSE 0 END, 2
                ) AS tip_rate_pct,

                -- Derived: average speed in mph
                ROUND(
                    CASE WHEN EXTRACT(EPOCH FROM (t.tpep_dropoff_datetime - t.tpep_pickup_datetime)) > 0
                         THEN t.trip_distance / (EXTRACT(EPOCH FROM (t.tpep_dropoff_datetime - t.tpep_pickup_datetime)) / 3600.0)
                         ELSE 0 END, 2
                ) AS avg_speed_mph,

                -- Derived: time features
                EXTRACT(HOUR  FROM t.tpep_pickup_datetime) AS pickup_hour,
                EXTRACT(DOW   FROM t.tpep_pickup_datetime) AS pickup_day_of_week,
                EXTRACT(MONTH FROM t.tpep_pickup_datetime) AS pickup_month,

                -- Derived: time of day category
                CASE
                    WHEN EXTRACT(HOUR FROM t.tpep_pickup_datetime) BETWEEN 6  AND 11 THEN 'morning'
                    WHEN EXTRACT(HOUR FROM t.tpep_pickup_datetime) BETWEEN 12 AND 16 THEN 'afternoon'
                    WHEN EXTRACT(HOUR FROM t.tpep_pickup_datetime) BETWEEN 17 AND 20 THEN 'evening'
                    ELSE 'night'
                END AS time_of_day,

                -- Derived: is rush hour (7-9am or 5-7pm on weekdays)
                CASE
                    WHEN EXTRACT(DOW FROM t.tpep_pickup_datetime) BETWEEN 1 AND 5
                        AND (EXTRACT(HOUR FROM t.tpep_pickup_datetime) BETWEEN 7 AND 9
                          OR EXTRACT(HOUR FROM t.tpep_pickup_datetime) BETWEEN 17 AND 19)
                    THEN TRUE ELSE FALSE
                END AS is_rush_hour,

                -- Derived: is weekend
                CASE
                    WHEN EXTRACT(DOW FROM t.tpep_pickup_datetime) IN (0, 6) THEN TRUE
                    ELSE FALSE
                END AS is_weekend,

                -- Key for joining with weather (date + hour)
                DATE_TRUNC('hour', t.tpep_pickup_datetime) AS pickup_hour_key

            FROM read_parquet('{INPUT_FILE}') t

            -- Join pickup zone info
            LEFT JOIN read_csv_auto('{ZONE_FILE}') pu
                ON t.PULocationID = pu.LocationID

            -- Join dropoff zone info
            LEFT JOIN read_csv_auto('{ZONE_FILE}') doz
                ON t.DOLocationID = doz.LocationID

        ) TO '{OUTPUT_FILE}' (FORMAT PARQUET)
    """

    con.execute(query)

    row_count = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{OUTPUT_FILE}')"
    ).fetchone()[0]
    print(f"[INFO] Transformed rows: {row_count:,}")
    print(f"[DONE] Transformed data saved to {OUTPUT_FILE}")

    con.close()


if __name__ == "__main__":
    transform_tlc()
