"""
DE1 - Prefect Pipeline: Ingestion Flow
Run: python prefect_flow.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "DE1_ingestion"))

from prefect import flow, task
from tlc_ingestion import run_ingestion as tlc_run
from weather_ingestion import run_ingestion as weather_run


@task(name="ingest-tlc", retries=2, retry_delay_seconds=60)
def ingest_tlc():
    tlc_run()


@task(name="ingest-weather", retries=2, retry_delay_seconds=30)
def ingest_weather():
    weather_run()


@flow(name="ingestion-pipeline", log_prints=True)
def ingestion_pipeline(include_weather: bool = False):
    ingest_tlc()
    if include_weather:
        ingest_weather()


if __name__ == "__main__":
    ingestion_pipeline(include_weather=False)
