"""
DE2 - Data Cleaning
Reads raw TLC monthly Parquet files, removes anomalies, outputs cleaned Parquet.
Input:  data/raw/tlc/*.parquet  (one file per month)
Output: data/intermediate/tlc_cleaned.parquet
"""

import duckdb
from pathlib import Path

RAW_TLC_DIR      = Path(__file__).parent.parent / "data" / "raw" / "tlc"
INTERMEDIATE_DIR = Path(__file__).parent.parent / "data" / "intermediate"
OUTPUT_FILE      = INTERMEDIATE_DIR / "tlc_cleaned.parquet"

NEEDED_COLUMNS = """
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    passenger_count,
    trip_distance,
    PULocationID,
    DOLocationID,
    payment_type,
    fare_amount,
    tip_amount,
    total_amount
"""


def clean_tlc():
    raw_files = list(RAW_TLC_DIR.glob("*.parquet"))
    if not raw_files:
        raise FileNotFoundError(f"Run ingestion first. No parquet files in: {RAW_TLC_DIR}")

    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
    glob_path = str(RAW_TLC_DIR / "*.parquet")
    print(f"[CLEAN] Reading {len(raw_files)} monthly files from {RAW_TLC_DIR}")
    for f in sorted(raw_files):
        print(f"  -> {f.name} ({f.stat().st_size/1024/1024:.1f} MB)")

    con = duckdb.connect()

    raw_count = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{glob_path}')"
    ).fetchone()[0]
    print(f"[INFO] Raw row count: {raw_count:,}")

    query = f"""
        COPY (
            SELECT {NEEDED_COLUMNS}
            FROM read_parquet('{glob_path}')
            WHERE
                -- Remove null values on critical columns
                tpep_pickup_datetime IS NOT NULL
                AND tpep_dropoff_datetime IS NOT NULL
                AND passenger_count IS NOT NULL
                AND trip_distance IS NOT NULL
                AND PULocationID IS NOT NULL
                AND DOLocationID IS NOT NULL
                AND fare_amount IS NOT NULL
                AND tip_amount IS NOT NULL

                -- Remove impossible fares and distances
                AND fare_amount > 0
                AND trip_distance > 0
                AND tip_amount >= 0
                AND total_amount > 0

                -- Remove trips with 0 passengers
                AND passenger_count > 0
                AND passenger_count <= 6

                -- Remove trips where dropoff is before or same as pickup
                AND tpep_dropoff_datetime > tpep_pickup_datetime

                -- Keep only trips within the data period
                AND tpep_pickup_datetime >= '2025-09-01'
                AND tpep_pickup_datetime < '2026-02-01'

                -- Remove trips with unrealistically long duration (> 5 hours)
                AND EXTRACT(EPOCH FROM (tpep_dropoff_datetime - tpep_pickup_datetime)) <= 18000

                -- Remove trips with unrealistic distance (> 100 miles for NYC)
                AND trip_distance <= 100

                -- Remove invalid location IDs (TLC zones are 1-263)
                AND PULocationID BETWEEN 1 AND 263
                AND DOLocationID BETWEEN 1 AND 263
        ) TO '{OUTPUT_FILE}' (FORMAT PARQUET)
    """

    con.execute(query)

    clean_count = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{OUTPUT_FILE}')"
    ).fetchone()[0]
    removed = raw_count - clean_count
    print(f"[INFO] Clean row count: {clean_count:,}")
    print(f"[INFO] Removed rows: {removed:,} ({removed/raw_count*100:.1f}%)")
    print(f"[DONE] Cleaned data saved to {OUTPUT_FILE}")

    con.close()


if __name__ == "__main__":
    clean_tlc()
