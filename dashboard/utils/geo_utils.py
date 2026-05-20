from __future__ import annotations

from copy import deepcopy
from typing import Any

import pandas as pd

from utils.cache import cache_data


def _round_coordinates(value: Any, precision: int) -> Any:
    if isinstance(value, list):
        return [_round_coordinates(item, precision) for item in value]
    if isinstance(value, tuple):
        return [_round_coordinates(item, precision) for item in value]
    if isinstance(value, float):
        return round(value, precision)
    return value


def simplify_geojson_precision(geojson: dict[str, Any], precision: int = 5) -> dict[str, Any]:
    """Reduce coordinate precision to lighten map rendering without changing geometry shape."""
    simplified = deepcopy(geojson)
    for feature in simplified.get("features", []):
        geometry = feature.get("geometry", {})
        if "coordinates" in geometry:
            geometry["coordinates"] = _round_coordinates(geometry["coordinates"], precision)
    return simplified


@cache_data
def build_behavior_map_payload(
    zone_df: pd.DataFrame,
    geojson: dict[str, Any],
    value_columns: list[str],
    precision: int = 5,
) -> tuple[dict[str, Any], list[int]]:
    simplified = simplify_geojson_precision(geojson, precision=precision)
    return attach_zone_metrics(simplified, zone_df, value_columns=value_columns)


def build_popup_text(zone_name: str, borough: str, trip_count: int, avg_tip_rate: float) -> str:
    return (
        f"<strong>{zone_name}</strong><br>"
        f"Borough: {borough}<br>"
        f"Perjalanan: {int(trip_count):,}<br>"
        f"Tip rata-rata: {avg_tip_rate:.2f}%"
    )


def attach_zone_metrics(
    geojson: dict[str, Any],
    zone_df: pd.DataFrame,
    value_columns: list[str],
) -> tuple[dict[str, Any], list[int]]:
    """Attach aggregated zone metrics to GeoJSON feature properties.

    Missing zone IDs (for example 264 and 265) remain excluded naturally because
    they do not have polygon features in the GeoJSON source.
    """
    geojson_copy = deepcopy(geojson)
    metric_lookup = zone_df.set_index("zone_id").to_dict("index") if not zone_df.empty else {}

    seen_ids: set[int] = set()
    for feature in geojson_copy.get("features", []):
        props = feature.get("properties", {})
        raw_id = props.get("LocationID")
        try:
            zone_id = int(raw_id)
        except (TypeError, ValueError):
            continue

        seen_ids.add(zone_id)
        metrics = metric_lookup.get(zone_id, {})
        for col in value_columns:
            props[col] = metrics.get(col, 0)

        zone_name = props.get("zone", "zona tidak diketahui")
        borough = props.get("borough", "borough tidak diketahui")
        trip_count = metrics.get("trip_count", metrics.get("trips", 0))
        avg_tip_rate = metrics.get("avg_tip_rate", 0)
        props["popup_html"] = build_popup_text(zone_name, borough, trip_count, avg_tip_rate)

    missing_polygons = sorted(set(metric_lookup.keys()) - seen_ids)
    return geojson_copy, missing_polygons
