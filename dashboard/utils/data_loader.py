from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from config import (
    DOW_LABELS,
    FACT_TRIPS_CLUSTERED_PATH,
    FACT_TRIPS_PATH,
    FACT_TRIPS_WEATHER_PATH,
    SEGMENTED_TRIPS_PATH,
    TAXI_ZONES_GEOJSON_PATH,
)
from utils.cache import cache_data
from utils.duckdb_connection import get_duckdb_connection
from utils.geo_utils import simplify_geojson_precision
import time


def _record_query_time(duration_s: float) -> None:
    try:
        import streamlit as st

        st.session_state['last_query_time_ms'] = int(duration_s * 1000)
    except Exception:
        # Not running inside Streamlit or session not available
        pass


def _as_posix(path: Path) -> str:
    return path.as_posix()


def cluster_file_available() -> bool:
    return SEGMENTED_TRIPS_PATH.exists() or FACT_TRIPS_CLUSTERED_PATH.exists()


def active_behavior_fact_path() -> Path:
    # Base dashboard should use the stable, non-segmented fact table.
    return FACT_TRIPS_PATH


def segmented_behavior_fact_path() -> Path:
    # Segmentation page should use clustered artifacts only.
    if SEGMENTED_TRIPS_PATH.exists():
        return SEGMENTED_TRIPS_PATH
    if FACT_TRIPS_CLUSTERED_PATH.exists():
        return FACT_TRIPS_CLUSTERED_PATH
    return FACT_TRIPS_PATH


def active_temporal_fact_path() -> Path:
    # Temporal analysis should use weather-enriched facts when available so weather filters are effective.
    if FACT_TRIPS_WEATHER_PATH.exists():
        return FACT_TRIPS_WEATHER_PATH
    return active_behavior_fact_path()


def temporal_has_weather_context() -> bool:
    return FACT_TRIPS_WEATHER_PATH.exists()


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_filter_clause(
    filters: dict[str, Any],
    table_alias: str = "t",
    include_weather: bool = False,
    include_segment: bool = False,
) -> str:
    conditions: list[str] = []

    boroughs = filters.get("boroughs", ["All"])
    if boroughs and "All" not in boroughs:
        borough_list = ", ".join(sql_literal(b) for b in boroughs)
        conditions.append(f"{table_alias}.pickup_borough IN ({borough_list})")

    hour_min, hour_max = filters.get("hour_range", (0, 23))
    conditions.append(f"{table_alias}.pickup_hour BETWEEN {int(hour_min)} AND {int(hour_max)}")

    rush_mode = filters.get("rush_hour_mode", "All")
    if rush_mode == "Rush only":
        conditions.append(f"{table_alias}.is_rush_hour = TRUE")
    elif rush_mode == "Non-rush only":
        conditions.append(f"{table_alias}.is_rush_hour = FALSE")

    weekend_mode = filters.get("weekend_mode", "Semua")
    if weekend_mode == "Hari Kerja":
        conditions.append(f"{table_alias}.is_weekend = FALSE")
    elif weekend_mode == "Akhir Pekan":
        conditions.append(f"{table_alias}.is_weekend = TRUE")

    selected_days = filters.get("pickup_days", ["Semua"])
    if selected_days and "Semua" not in selected_days:
        day_to_dow = {v: k for k, v in DOW_LABELS.items()}
        selected_dow = [day_to_dow[d] for d in selected_days if d in day_to_dow]
        if selected_dow:
            dow_list = ", ".join(str(int(d)) for d in selected_dow)
            conditions.append(f"{table_alias}.pickup_day_of_week IN ({dow_list})")

    segment_filter = filters.get("segment_filter", "Semua Segmen")
    # Segmentation filters are opt-in for segmentation-aware queries only.
    if include_segment and segment_filter and segment_filter != "Semua Segmen":
        conditions.append(f"{table_alias}.customer_segment = {sql_literal(str(segment_filter))}")

    if include_weather:
        weather_categories = filters.get("weather_categories", ["All"])
        if weather_categories and "All" not in weather_categories:
            weather_list = ", ".join(sql_literal(w) for w in weather_categories)
            conditions.append(f"{table_alias}.weather_category IN ({weather_list})")

    if not conditions:
        return ""

    return "WHERE " + " AND ".join(conditions)


@cache_data
def run_query(sql: str) -> pd.DataFrame:
    con = get_duckdb_connection()
    start = time.perf_counter()
    df = con.execute(sql).fetchdf()
    duration = time.perf_counter() - start
    _record_query_time(duration)
    return df


@cache_data
def load_geojson(precision: int = 3) -> dict[str, Any]:
    with TAXI_ZONES_GEOJSON_PATH.open(encoding="utf-8") as handle:
        return simplify_geojson_precision(json.load(handle), precision=precision)


@cache_data
def get_borough_options() -> list[str]:
    sql = f"""
        SELECT DISTINCT pickup_borough
        FROM read_parquet('{_as_posix(active_behavior_fact_path())}')
        WHERE pickup_borough IS NOT NULL
        ORDER BY pickup_borough
    """
    boroughs = run_query(sql)["pickup_borough"].tolist()
    return ["All", *boroughs]


@cache_data
def get_weather_options() -> list[str]:
    if not FACT_TRIPS_WEATHER_PATH.exists():
        return ["All"]

    sql = f"""
        SELECT DISTINCT weather_category
        FROM read_parquet('{_as_posix(FACT_TRIPS_WEATHER_PATH)}')
        WHERE weather_category IS NOT NULL
        ORDER BY weather_category
    """
    categories = run_query(sql)["weather_category"].tolist()
    return ["All", *categories]


@cache_data
def get_day_of_week_options() -> list[str]:
    src = _as_posix(active_behavior_fact_path())
    sql = f"""
        SELECT DISTINCT pickup_day_of_week
        FROM read_parquet('{src}')
        WHERE pickup_day_of_week IS NOT NULL
        ORDER BY pickup_day_of_week
    """
    df = run_query(sql)
    ordered_labels = [DOW_LABELS[int(d)] for d in df["pickup_day_of_week"].tolist() if int(d) in DOW_LABELS]
    # Ensure the visual order remains Senin..Minggu when all values exist.
    canonical = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    available = [d for d in canonical if d in ordered_labels]
    return ["Semua", *available]


@cache_data
def get_segment_options() -> list[str]:
    if not cluster_file_available():
        return ["Semua Segmen"]

    src = _as_posix(segmented_behavior_fact_path())
    sql = f"""
        SELECT DISTINCT cluster_id, customer_segment
        FROM read_parquet('{src}')
        WHERE cluster_id IS NOT NULL AND customer_segment IS NOT NULL
        ORDER BY cluster_id
    """
    df = run_query(sql)
    segments = df["customer_segment"].tolist()
    return ["Semua Segmen", *segments]
