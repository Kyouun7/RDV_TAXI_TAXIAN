from __future__ import annotations

from utils.data_loader import active_behavior_fact_path, build_filter_clause, run_query


def get_zone_behavior_intensity(filters: dict):
    src = active_behavior_fact_path().as_posix()
    where = build_filter_clause(filters, table_alias="t", include_weather=False)

    sql = f"""
        SELECT
            t.pickup_location_id AS zone_id,
            t.pickup_zone AS zone_name,
            t.pickup_borough AS borough,
            COUNT(*) AS trip_count,
            ROUND(AVG(t.tip_rate_pct), 2) AS avg_tip_rate,
            ROUND(AVG(t.trip_duration_min), 2) AS avg_duration_min
        FROM read_parquet('{src}') t
        {where}
        GROUP BY 1, 2, 3
        ORDER BY trip_count DESC
    """
    return run_query(sql)


def get_top_behavior_pickup_zones(filters: dict, limit: int = 15, sort_direction: str = "DESC"):
    src = active_behavior_fact_path().as_posix()
    where = build_filter_clause(filters, table_alias="t", include_weather=False)
    sort_dir = sort_direction.upper()
    if sort_dir not in ("ASC", "DESC"):
        sort_dir = "DESC"

    sql = f"""
        SELECT
            t.pickup_zone,
            t.pickup_borough,
            COUNT(*) AS trips,
            ROUND(AVG(t.tip_rate_pct), 2) AS avg_tip_rate,
            ROUND(AVG(t.trip_duration_min), 2) AS avg_duration_min
        FROM read_parquet('{src}') t
        {where}
        GROUP BY 1, 2
        ORDER BY trips {sort_dir}
        LIMIT {int(limit)}
    """
    return run_query(sql)


def get_zone_tip_behavior(filters: dict, limit: int = 20, sort_direction: str = "DESC"):
    src = active_behavior_fact_path().as_posix()
    where = build_filter_clause(filters, table_alias="t", include_weather=False)
    sort_dir = sort_direction.upper()
    if sort_dir not in ("ASC", "DESC"):
        sort_dir = "DESC"

    sql = f"""
        SELECT
            t.pickup_zone,
            t.pickup_borough,
            ROUND(AVG(t.tip_rate_pct), 2) AS avg_tip_rate,
            COUNT(*) AS trips
        FROM read_parquet('{src}') t
        {where}
        GROUP BY 1, 2
        HAVING COUNT(*) >= 1000
        ORDER BY avg_tip_rate {sort_dir}
        LIMIT {int(limit)}
    """
    return run_query(sql)


def get_airport_corridor_behavior(filters: dict):
    src = active_behavior_fact_path().as_posix()
    where = build_filter_clause(filters, table_alias="t", include_weather=False)

    sql = f"""
        SELECT
            CASE
                WHEN t.pickup_zone IN ('JFK Airport', 'LaGuardia Airport', 'EWR')
                    OR t.pickup_service_zone = 'Airports'
                THEN 'Airport corridor behavior'
                ELSE 'Non-airport behavior'
            END AS behavior_group,
            COUNT(*) AS trips,
            ROUND(AVG(t.trip_distance), 2) AS avg_distance,
            ROUND(AVG(t.trip_duration_min), 2) AS avg_duration_min,
            ROUND(AVG(t.tip_rate_pct), 2) AS avg_tip_rate
        FROM read_parquet('{src}') t
        {where}
        GROUP BY 1
        ORDER BY trips DESC
    """
    return run_query(sql)
