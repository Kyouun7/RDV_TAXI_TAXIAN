from __future__ import annotations

import time
from copy import deepcopy

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from config import MAP_CENTER, MAP_TILE, MAP_ZOOM, SEGMENT_DISPLAY_NAMES
from utils.geo_utils import simplify_geojson_precision

SEGMENT_COLORS = {
    0: "#2aa893",
    1: "#1d8fbd",
    2: "#7a5ca8",
}


def _normalize_center(center_value):
    if isinstance(center_value, dict):
        lat = center_value.get("lat")
        lng = center_value.get("lng")
        if lat is not None and lng is not None:
            return [lat, lng]
    if isinstance(center_value, (list, tuple)) and len(center_value) == 2:
        return [center_value[0], center_value[1]]
    return MAP_CENTER


def _enrich_geojson_with_cluster_metrics(geojson: dict, zone_df: pd.DataFrame) -> dict:
    geojson_copy = deepcopy(geojson)
    metric_lookup = zone_df.set_index("zone_id").to_dict("index") if not zone_df.empty else {}

    for feature in geojson_copy.get("features", []):
        props = feature.get("properties", {})
        raw_id = props.get("LocationID")
        try:
            zone_id = int(raw_id)
        except (TypeError, ValueError):
            continue

        metrics = metric_lookup.get(zone_id, {})
        props["dominant_cluster_id"] = metrics.get("cluster_id")
        props["dominant_segment"] = metrics.get("customer_segment", "Segmen tidak diketahui")
        props["dominant_segment_trips"] = metrics.get("dominant_segment_trips", 0)
        props["zone_total_trips"] = metrics.get("zone_total_trips", 0)
        props["dominant_share_pct"] = metrics.get("dominant_share_pct", 0)
        props["zone"] = metrics.get("zone_name", props.get("zone", "zona tidak diketahui"))
        props["borough"] = metrics.get("borough", props.get("borough", "borough tidak diketahui"))

    return geojson_copy


def render_segment_cluster_map(
    zone_df: pd.DataFrame,
    geojson: dict,
    interaction_mode: str = "Seimbang",
):
    if zone_df.empty:
        st.info("Belum ada data klaster per zona untuk filter saat ini.")
        return

    mode = (interaction_mode or "Seimbang").strip().lower()
    st.session_state.setdefault("segment_map_center", MAP_CENTER)
    st.session_state.setdefault("segment_map_zoom", MAP_ZOOM)

    simplify_start = time.perf_counter()
    geojson_simplified = simplify_geojson_precision(geojson, precision=5)
    geojson_with_metrics = _enrich_geojson_with_cluster_metrics(geojson_simplified, zone_df)
    payload_ms = int((time.perf_counter() - simplify_start) * 1000)

    map_center = _normalize_center(st.session_state.get("segment_map_center", MAP_CENTER))
    map_zoom = st.session_state.get("segment_map_zoom", MAP_ZOOM)

    map_start = time.perf_counter()
    m = folium.Map(location=map_center, zoom_start=map_zoom, tiles=MAP_TILE)

    def style_function(feature):
        cluster_id = feature["properties"].get("dominant_cluster_id")
        fill_color = SEGMENT_COLORS.get(cluster_id, "#d9d9d9")
        return {
            "fillColor": fill_color,
            "color": "#2b2b2b",
            "weight": 0.6,
            "fillOpacity": 0.7,
        }

    tooltip = None
    popup = None
    if mode == "klik detail":
        popup = folium.GeoJsonPopup(
            fields=["zone", "borough", "dominant_segment", "dominant_share_pct", "zone_total_trips"],
            aliases=["Zona", "Borough", "Segmen Dominan", "Proporsi Dominan (%)", "Total Perjalanan Zona"],
            localize=True,
            sticky=False,
            labels=True,
        )
    elif mode == "pasif":
        tooltip = None
        popup = None
    else:
        tooltip = folium.GeoJsonTooltip(
            fields=["zone", "borough", "dominant_segment", "dominant_share_pct", "zone_total_trips"],
            aliases=["Zona", "Borough", "Segmen Dominan", "Proporsi Dominan (%)", "Total Perjalanan Zona"],
            localize=True,
            sticky=mode == "interaktif",
        )

    folium.GeoJson(
        geojson_with_metrics,
        style_function=style_function,
        tooltip=tooltip,
        popup=popup,
        name="Dominasi segmen zona",
    ).add_to(m)

    legend_html = """
    <div style="position: fixed; bottom: 25px; left: 25px; z-index: 9999; background: white; padding: 12px 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); color: #222;">
        <div style="font-weight: 600; margin-bottom: 8px;">Legenda Segmen</div>
    """
    cluster_name_lookup = {
        0: "Short Daily Commute",
        1: "Mid-Range Travel",
        2: "Long-Distance / Airport",
    }
    for cluster_id, color in SEGMENT_COLORS.items():
        raw_segment_name = cluster_name_lookup.get(cluster_id, "Segmen")
        segment_name = SEGMENT_DISPLAY_NAMES.get(raw_segment_name, raw_segment_name)
        legend_html += f"<div style='color:#222;'><span style='display:inline-block;width:12px;height:12px;background:{color};margin-right:8px;border-radius:2px;'></span>{segment_name}</div>"
    legend_html += "</div>"
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl(collapsed=True).add_to(m)

    map_result = st_folium(
        m,
        key="segment_cluster_map",
        height=560,
        use_container_width=True,
        returned_objects=["center", "zoom"],
        render=True,
        debug=False,
    )
    render_ms = int((time.perf_counter() - map_start) * 1000)

    if isinstance(map_result, dict):
        if map_result.get("center"):
            st.session_state["segment_map_center"] = _normalize_center(map_result["center"])
        if map_result.get("zoom") is not None:
            st.session_state["segment_map_zoom"] = map_result["zoom"]

    st.session_state["last_segment_map_payload_ms"] = payload_ms
    st.session_state["last_segment_map_render_ms"] = render_ms

    if st.session_state.get("debug_perf_mode"):
        st.caption(f"Eksperimen peta segmen: payload={payload_ms} ms, render={render_ms} ms")
