from __future__ import annotations

from utils.data_loader import build_filter_clause, run_query, segmented_behavior_fact_path

# NOTE: Segmentation queries are the only ones that opt into customer_segment filters.


def get_segment_profile(filters: dict, sort_direction: str = "DESC"):
    src = segmented_behavior_fact_path().as_posix()
    where = build_filter_clause(filters, table_alias="t", include_weather=True, include_segment=True)
    sort_dir = sort_direction.upper()
    if sort_dir not in ("ASC", "DESC"):
        sort_dir = "DESC"

    sql = f"""
        SELECT
            t.cluster_id,
            t.customer_segment,
            COUNT(*) AS trips,
            ROUND(AVG(t.trip_distance), 2) AS avg_trip_distance,
            ROUND(AVG(t.trip_duration_min), 2) AS avg_trip_duration_min,
            ROUND(AVG(t.tip_rate_pct), 2) AS avg_tip_rate_pct,
            ROUND(AVG(t.avg_speed_mph), 2) AS avg_speed_mph,
            ROUND(AVG(CASE WHEN t.is_rush_hour THEN 1 ELSE 0 END), 3) AS rush_hour_ratio,
            ROUND(AVG(CASE WHEN t.is_weekend THEN 1 ELSE 0 END), 3) AS weekend_ratio
        FROM read_parquet('{src}') t
        {where}
        GROUP BY 1, 2
        ORDER BY trips {sort_dir}
    """
    return run_query(sql)


def get_segment_borough_mix(filters: dict, sort_direction: str = "DESC"):
    src = segmented_behavior_fact_path().as_posix()
    where = build_filter_clause(filters, table_alias="t", include_weather=True, include_segment=True)
    sort_dir = sort_direction.upper()
    if sort_dir not in ("ASC", "DESC"):
        sort_dir = "DESC"

    sql = f"""
        SELECT
            t.cluster_id,
            t.customer_segment,
            t.pickup_borough,
            COUNT(*) AS trips
        FROM read_parquet('{src}') t
        {where}
        GROUP BY 1, 2, 3
        ORDER BY trips {sort_dir}
    """
    return run_query(sql)


def get_segment_hourly_pattern(filters: dict, sort_direction: str = "ASC"):
    src = segmented_behavior_fact_path().as_posix()
    where = build_filter_clause(filters, table_alias="t", include_weather=True, include_segment=True)
    sort_dir = sort_direction.upper()
    if sort_dir not in ("ASC", "DESC"):
        sort_dir = "ASC"

    sql = f"""
        SELECT
            t.cluster_id,
            t.customer_segment,
            t.pickup_hour,
            COUNT(*) AS trips
        FROM read_parquet('{src}') t
        {where}
        GROUP BY 1, 2, 3
        ORDER BY pickup_hour {sort_dir}, trips DESC
    """
    return run_query(sql)


def get_segment_weather_pattern(filters: dict, sort_direction: str = "DESC"):
    src = segmented_behavior_fact_path().as_posix()
    where = build_filter_clause(filters, table_alias="t", include_weather=True, include_segment=True)
    sort_dir = sort_direction.upper()
    if sort_dir not in ("ASC", "DESC"):
        sort_dir = "DESC"

    sql = f"""
        SELECT
            t.cluster_id,
            t.customer_segment,
            t.weather_category,
            COUNT(*) AS trips,
            ROUND(AVG(t.tip_rate_pct), 2) AS avg_tip_rate_pct,
            ROUND(AVG(t.trip_duration_min), 2) AS avg_trip_duration_min
        FROM read_parquet('{src}') t
        {where}
        GROUP BY 1, 2, 3
        ORDER BY trips {sort_dir}
    """
    return run_query(sql)


def get_segment_zone_dominance(filters: dict, limit: int = 20):
    src = segmented_behavior_fact_path().as_posix()
    where = build_filter_clause(filters, table_alias="t", include_weather=True, include_segment=True)

    sql = f"""
        WITH zone_cluster_counts AS (
            SELECT
                t.pickup_location_id AS zone_id,
                t.pickup_zone AS zone_name,
                t.pickup_borough AS borough,
                t.cluster_id,
                t.customer_segment,
                COUNT(*) AS trips
            FROM read_parquet('{src}') t
            {where}
            GROUP BY 1, 2, 3, 4, 5
        ), ranked AS (
            SELECT
                *,
                SUM(trips) OVER (PARTITION BY zone_id) AS zone_total_trips,
                ROW_NUMBER() OVER (PARTITION BY zone_id ORDER BY trips DESC, cluster_id ASC) AS rn
            FROM zone_cluster_counts
        )
        SELECT
            zone_id,
            zone_name,
            borough,
            cluster_id,
            customer_segment,
            trips AS dominant_segment_trips,
            zone_total_trips,
            ROUND(trips * 100.0 / NULLIF(zone_total_trips, 0), 2) AS dominant_share_pct
        FROM ranked
        WHERE rn = 1
        ORDER BY zone_total_trips DESC
        LIMIT {int(limit)}
    """
    return run_query(sql)
