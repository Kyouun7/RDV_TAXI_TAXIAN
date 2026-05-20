from __future__ import annotations

from utils.data_loader import active_temporal_fact_path, build_filter_clause, run_query, temporal_has_weather_context


def get_hourly_mobility_trends(filters: dict):
    src = active_temporal_fact_path().as_posix()
    where = build_filter_clause(filters, table_alias="t", include_weather=temporal_has_weather_context())

    sql = f"""
        SELECT
            t.pickup_hour,
            COUNT(*) AS trips,
            ROUND(AVG(t.tip_rate_pct), 2) AS avg_tip_rate,
            ROUND(AVG(t.trip_duration_min), 2) AS avg_duration_min
        FROM read_parquet('{src}') t
        {where}
        GROUP BY t.pickup_hour
        ORDER BY t.pickup_hour
    """
    return run_query(sql)


def get_rush_hour_behavior_comparison(filters: dict):
    src = active_temporal_fact_path().as_posix()
    where = build_filter_clause(filters, table_alias="t", include_weather=temporal_has_weather_context())

    sql = f"""
        SELECT
            CASE WHEN t.is_rush_hour THEN 'Jam sibuk' ELSE 'Non-jam sibuk' END AS period,
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
