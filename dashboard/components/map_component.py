from __future__ import annotations

import time

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from branca.colormap import LinearColormap

from config import MAP_CENTER, MAP_TILE, MAP_ZOOM
from utils.geo_utils import build_behavior_map_payload


def _normalize_center(center_value):
    if isinstance(center_value, dict):
        lat = center_value.get("lat")
        lng = center_value.get("lng")
        if lat is not None and lng is not None:
            return [lat, lng]
    if isinstance(center_value, (list, tuple)) and len(center_value) == 2:
        return [center_value[0], center_value[1]]
    return MAP_CENTER


def render_behavior_choropleth(
    zone_df: pd.DataFrame,
    geojson: dict,
    value_col: str = "trip_count",
    interaction_mode: str = "Seimbang",
):
    if zone_df.empty:
        st.info("Belum ada data tingkat zona untuk filter saat ini.")
        return

    mode = (interaction_mode or "Seimbang").strip().lower()

    st.session_state.setdefault("behavior_map_center", MAP_CENTER)
    st.session_state.setdefault("behavior_map_zoom", MAP_ZOOM)

    working_df = zone_df[["zone_id", "zone_name", "borough", value_col, "avg_tip_rate"]].copy()
    payload_start = time.perf_counter()
    geojson_with_metrics, missing_polygons = build_behavior_map_payload(
        working_df,
        geojson,
        value_columns=[value_col, "avg_tip_rate", "zone_name", "borough"],
    )
    payload_duration_ms = int((time.perf_counter() - payload_start) * 1000)

    map_center = _normalize_center(st.session_state.get("behavior_map_center", MAP_CENTER))
    map_zoom = st.session_state.get("behavior_map_zoom", MAP_ZOOM)

    map_start = time.perf_counter()
    m = folium.Map(location=map_center, zoom_start=map_zoom, tiles=MAP_TILE)

    # choropleth_start = time.perf_counter()
    # folium.Choropleth(
    #     geo_data=geojson_with_metrics,
    #     data=working_df,z
    #     columns=["zone_id", value_col],
    #     key_on="feature.properties.LocationID",
    #     fill_color="BuGn",
    #     fill_opacity=0.75,
    #     line_opacity=0.2,
    #     nan_fill_color="#f0f0f0",
    #     legend_name="Intensitas Pergerakan (Jumlah Perjalanan)",
    # ).add_to(m)
    # choropleth_duration_ms = int((time.perf_counter() - choropleth_start) * 1000)

    choropleth_start = time.perf_counter()

    # Custom colormap dengan warna yang lebih lembut dan kontras yang baik untuk aksesibilitas
    custom_colormap = LinearColormap(
        colors=[
            # Hijau
            #"#d8efb2",
            #"#a9dc96",
            #"#74bf8f",
            #"#3d8d84",
            #"#0f5b6e",

            # Orange
            #"#f3e79b",
            #"#fabd84",
            #"#f39482",
            #"#db708e",
            #"#a85c9d",

            # Blue
            "#eef7bf",
            "#8fd08f",
            "#5eae8c",
            "#2f857f",
            "#0b4f63",
        ],
        vmin=working_df[value_col].min(),
        vmax=working_df[value_col].max(),
    )

    # Styling function untuk tiap polygon zona
    def style_function(feature):
        value = feature["properties"].get(value_col)

        return {
            "fillColor": (
                custom_colormap(value)
                if value is not None
                else "#f0f0f0"
            ),
            "color": "#2b2b2b",
            "weight": 0.5,
            "fillOpacity": 0.75,
        }

    # Konfigurasi interaksi berdasarkan mode
    tooltip = None
    popup = None
    style_weight = 0.3
    highlight_weight = 1.5
    highlight_fill = "#ffffff"
    # "Seimbang" & default: returned_objects=[] agar tidak trigger rerun saat pan/zoom
    returned_objects = []

    if mode == "klik detail":
        popup = folium.GeoJsonPopup(
            fields=["popup_html"],
            aliases=[""],
            labels=False,
            localize=True,
            sticky=False,
            parse_html=True,
        )
        returned_objects = ["last_object_clicked"]
    elif mode == "hover ringan":
        tooltip = folium.GeoJsonTooltip(
            fields=["zone", value_col],
            aliases=["Zona", "Jumlah Perjalanan"],
            localize=True,
            sticky=False,
        )
    elif mode == "pasif":
        style_weight = 0.2
        highlight_weight = 0.2
        highlight_fill = "transparent"
        returned_objects = []
    elif mode == "interaktif":
        tooltip = folium.GeoJsonTooltip(
            fields=["zone", "borough", value_col, "avg_tip_rate"],
            aliases=["Zona", "Borough", "Jumlah Perjalanan", "Rata-rata Tip (%)"],
            localize=True,
            sticky=True,
        )
        returned_objects = ["center", "zoom", "last_object_clicked"]
    else:
        tooltip = folium.GeoJsonTooltip(
            fields=["zone", "borough", value_col, "avg_tip_rate"],
            aliases=["Zona", "Borough", "Jumlah Perjalanan", "Rata-rata Tip (%)"],
            localize=True,
            sticky=False,
        )

    # Render GeoJSON SATU layer (warna + interaksi sekaligus — sebelumnya 2x render = 2x data ke browser)
    folium.GeoJson(
        geojson_with_metrics,
        name="Zone behavior",
        style_function=style_function,
        highlight_function=lambda _x: {
            "weight": highlight_weight,
            "fillColor": highlight_fill,
            "color": "#111111",
        },
        tooltip=tooltip,
        popup=popup,
    ).add_to(m)

    # Tambahkan legend
    custom_colormap.caption = "Intensitas Pergerakan (Jumlah Perjalanan)"
    custom_colormap.add_to(m)

    choropleth_duration_ms = int(
        (time.perf_counter() - choropleth_start) * 1000
    )
    geojson_duration_ms = 0  # merged into single layer above

    st.session_state["last_choropleth_ms"] = choropleth_duration_ms
    st.session_state["last_geojson_overlay_ms"] = geojson_duration_ms
    map_result = st_folium(
        m,
        key="behavior_choropleth",
        height=560,
        use_container_width=True,
        returned_objects=returned_objects,
        debug=False,
    )
    map_render_duration_ms = int((time.perf_counter() - map_start) * 1000)

    # Hanya update session_state jika nilai BENAR-BENAR berubah
    # → mencegah rerun loop: session_state write → rerun → map render → write lagi
    if isinstance(map_result, dict):
        new_center = _normalize_center(map_result.get("center"))
        new_zoom = map_result.get("zoom")
        if new_center and new_center != st.session_state.get("behavior_map_center"):
            st.session_state["behavior_map_center"] = new_center
        if new_zoom is not None and new_zoom != st.session_state.get("behavior_map_zoom"):
            st.session_state["behavior_map_zoom"] = new_zoom

    st.session_state["last_map_payload_ms"] = payload_duration_ms
    st.session_state["last_map_render_ms"] = map_render_duration_ms
    st.session_state["last_map_mode"] = interaction_mode

    if missing_polygons:
        st.caption(
            "Beberapa zona pada analisis tidak memiliki poligon pada GeoJSON dan dikecualikan dari peta: "
            + ", ".join(str(z) for z in missing_polygons)
        )

    if st.session_state.get("debug_perf_mode"):
        st.caption(
            "Eksperimen peta: "
            f"mode={interaction_mode}, payload={payload_duration_ms} ms, choropleth={choropleth_duration_ms} ms, "
            f"overlay={geojson_duration_ms} ms, render={map_render_duration_ms} ms"
        )
