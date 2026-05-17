"""
DE1 - TLC Yellow Taxi Data Ingestion
Reads Yellow Taxi Parquet files DIRECTLY from NYC TLC URLs using DuckDB httpfs.
No manual download needed — just run and it fetches from the web automatically.

Source: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
Output: data/raw/tlc/yellow_tripdata_YYYY-MM.parquet (one file per month)
"""

import duckdb
from pathlib import Path

RAW_TLC_DIR = Path(__file__).parent.parent / "data" / "raw" / "tlc"
BASE_URL    = "https://d37ci6vzurychx.cloudfront.net/trip-data"

MONTHS = [
    "2025-09",
    "2025-10",
    "2025-11",
    "2025-12",
    "2026-01",
]


def ingest_month(con: duckdb.DuckDBPyConnection, month: str):
    filename = f"yellow_tripdata_{month}.parquet"
    dest     = RAW_TLC_DIR / filename
    url      = f"{BASE_URL}/{filename}"

    if dest.exists():
        size_mb = dest.stat().st_size / (1024 * 1024)
        print(f"[SKIP] {filename} already exists ({size_mb:.1f} MB)")
        return

    print(f"[INGEST] {url}")
    con.execute(f"""
        COPY (
            SELECT
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
            FROM read_parquet('{url}')
        ) TO '{dest}' (FORMAT PARQUET)
    """)

    row_count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{dest}')").fetchone()[0]
    size_mb   = dest.stat().st_size / (1024 * 1024)
    print(f"[DONE] {filename} — {row_count:,} rows, {size_mb:.1f} MB")


def run_ingestion():
    RAW_TLC_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")

    print(f"[INGEST] Starting ingestion for {len(MONTHS)} months...")
    for month in MONTHS:
        ingest_month(con, month)

    total = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{RAW_TLC_DIR}/*.parquet')"
    ).fetchone()[0]
    print(f"[DONE] All months ingested. Total rows: {total:,}")
    con.close()


if __name__ == "__main__":
    run_ingestion()
