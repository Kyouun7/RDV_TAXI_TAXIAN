"""
MASTER PIPELINE — NYC Taxi Customer Behavior Segmentation
Kelompok 1 | MK Rekayasa Data dan Visualisasi

Pipeline stages:
  1.  [INGEST]    Read TLC Yellow Taxi Parquet directly from NYC TLC URLs (no manual download)
  1b. [ZONES]     Download taxi zone lookup CSV + shapefile/GeoJSON for geographic decoding
  2.  [CLEAN]     Remove anomalies: nulls, negative fares, impossible GPS, bad durations
  3.  [TRANSFORM] Add derived features: duration, tip rate, speed, zone names, time categories
  4.  [BLEND]     Join with weather data (optional, only if weather data exists)
  5.  [MODEL]     Build star schema: dim_zones + fact_trips

Run once:
  python pipeline.py

Run on a schedule (automated, every day at midnight):
  python pipeline.py --schedule

Output (data/intermediate/):
  tlc_cleaned.parquet      -> after cleaning
  tlc_transformed.parquet  -> after feature engineering + zone join
  tlc_with_weather.parquet -> after weather blend (optional)
  dim_zones.parquet        -> zone dimension table (265 zones)
  fact_trips.parquet       -> final fact table (ready for analyst + ML)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "DE1_ingestion"))
sys.path.insert(0, str(Path(__file__).parent / "DE2_transformation"))

from prefect import flow, task
from tlc_ingestion import run_ingestion
from zone_ingestion import run_ingestion as zone_run
from cleaning import clean_tlc
from feature_engineering import transform_tlc
from data_blending import blend_data
from data_modelling import run_modelling


@task(name="1-ingest-tlc", retries=2, retry_delay_seconds=60)
def task_ingest():
    run_ingestion()


@task(name="1b-ingest-zones", retries=2, retry_delay_seconds=15)
def task_ingest_zones():
    zone_run()


@task(name="2-clean-tlc", retries=1)
def task_clean():
    clean_tlc()


@task(name="3-feature-engineering", retries=1)
def task_transform():
    transform_tlc()


@task(name="4-blend-weather")
def task_blend():
    blend_data()


@task(name="5-data-modelling", retries=1)
def task_model():
    run_modelling()


@flow(name="nyc-taxi-pipeline", log_prints=True)
def full_pipeline():
    print("=" * 60)
    print("NYC Taxi Customer Behavior Segmentation — Pipeline Start")
    print("=" * 60)

    ingest      = task_ingest()
    ingest_zone = task_ingest_zones()
    clean       = task_clean(wait_for=[ingest, ingest_zone])
    transform   = task_transform(wait_for=[clean])
    blend       = task_blend(wait_for=[transform])
    task_model(wait_for=[blend])

    print("=" * 60)
    print("Pipeline complete. Data ready for analyst and ML engineer.")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    if "--schedule" in sys.argv:
        # Automated mode: runs every day at midnight (cron: 0 0 * * *)
        # Keeps checking for new TLC data monthly
        print("Starting scheduled pipeline (daily at midnight)...")
        full_pipeline.serve(
            name="nyc-taxi-pipeline-scheduled",
            cron="0 0 * * *",
        )
    else:
        # Manual one-time run
        full_pipeline()
