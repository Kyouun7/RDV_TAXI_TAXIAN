from __future__ import annotations

from config import FACT_TRIPS_WEATHER_PATH
from utils.data_loader import build_filter_clause, run_query


def get_weather_behavior_comparison(filters: dict):
    if not FACT_TRIPS_WEATHER_PATH.exists():
        return None

    src = FACT_TRIPS_WEATHER_PATH.as_posix()
    where = build_filter_clause(filters, table_alias="t", include_weather=True)

    sql = f"""
        SELECT
            t.weather_category,
            COUNT(*) AS trips,
            ROUND(AVG(t.trip_distance), 2) AS avg_distance,
            ROUND(AVG(t.trip_duration_min), 2) AS avg_duration_min,
            ROUND(AVG(t.tip_rate_pct), 2) AS avg_tip_rate
        FROM read_parquet('{src}') t
        {where}
        GROUP BY t.weather_category
        ORDER BY trips DESC
    """
    return run_query(sql)


def get_weather_tip_behavior(filters: dict):
    if not FACT_TRIPS_WEATHER_PATH.exists():
        return None

    src = FACT_TRIPS_WEATHER_PATH.as_posix()
    where = build_filter_clause(filters, table_alias="t", include_weather=True)

    sql = f"""
        SELECT
            t.weather_category,
            ROUND(AVG(t.tip_rate_pct), 2) AS avg_tip_rate,
            ROUND(AVG(t.trip_duration_min), 2) AS avg_duration_min,
            COUNT(*) AS trips
        FROM read_parquet('{src}') t
        {where}
        GROUP BY t.weather_category
        ORDER BY avg_tip_rate DESC
    """
    return run_query(sql)
