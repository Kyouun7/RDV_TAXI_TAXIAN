from __future__ import annotations

from config import FACT_TRIPS_PATH
from utils.data_loader import active_behavior_fact_path, build_filter_clause, run_query


def get_behavior_kpis(filters: dict):
    src = active_behavior_fact_path().as_posix()
    where = build_filter_clause(filters, table_alias="t", include_weather=False)

    sql = f"""
        SELECT
            COUNT(*) AS total_trips,
            ROUND(AVG(t.trip_distance), 2) AS avg_trip_distance,
            ROUND(AVG(t.trip_duration_min), 2) AS avg_trip_duration_min,
            ROUND(AVG(t.tip_rate_pct), 2) AS avg_tip_rate_pct,
            COUNT(DISTINCT t.pickup_location_id) AS active_pickup_zones
        FROM read_parquet('{src}') t
        {where}
    """
    return run_query(sql)


def get_borough_mobility_distribution(filters: dict, sort_direction: str = "DESC"):
    src = active_behavior_fact_path().as_posix()
    where = build_filter_clause(filters, table_alias="t", include_weather=False)
    sort_dir = sort_direction.upper()
    if sort_dir not in ("ASC", "DESC"):
        sort_dir = "DESC"

    sql = f"""
        SELECT
            t.pickup_borough,
            COUNT(*) AS trips,
            ROUND(AVG(t.tip_rate_pct), 2) AS avg_tip_rate_pct,
            ROUND(AVG(t.trip_duration_min), 2) AS avg_trip_duration_min
        FROM read_parquet('{src}') t
        {where}
        GROUP BY t.pickup_borough
        ORDER BY trips {sort_dir}
    """
    return run_query(sql)


def get_data_source_status() -> dict[str, bool]:
    return {
        "baseline_fact": FACT_TRIPS_PATH.exists(),
        "cluster_ready": active_behavior_fact_path().name.endswith("clustered.parquet"),
    }
