from __future__ import annotations

import streamlit as st

from components.charts import top_zones_chart
from components.map_component import render_behavior_choropleth
from queries.spatial_queries import (
    get_airport_corridor_behavior,
    get_top_behavior_pickup_zones,
    get_zone_behavior_intensity,
    get_zone_tip_behavior,
)
from utils.data_loader import load_geojson
from utils.insights import high_tip_anomaly_sentence, mobility_inequality_sentence, zone_hotspot_sentence


def render(filters: dict):
    st.header("Analisis Perilaku Spasial")
    st.markdown("Menggambarkan karakter zona berdasarkan intensitas pergerakan dan pola pemberian tip.")

    st.subheader("Peta Konsentrasi Perilaku per Zona")
    zone_df = get_zone_behavior_intensity(filters)
    render_behavior_choropleth(
        zone_df,
        load_geojson(precision=int(filters.get("geojson_precision", 5))),
        value_col="trip_count",
        interaction_mode=filters.get("map_interaction_mode", "Seimbang"),
    )

    col1, col2 = st.columns(2)
    with col1:
        zone_order = st.radio(
            "Urutkan hotspot zona",
            options=["Tampilkan dari Nilai Terbesar", "Tampilkan dari Nilai Terkecil"],
            index=0,
            key="spatial_zone_sort_order",
        )
        zone_sort_dir = "DESC" if zone_order == "Tampilkan dari Nilai Terbesar" else "ASC"
        top_zone_df = get_top_behavior_pickup_zones(filters, limit=15, sort_direction=zone_sort_dir)
        st.plotly_chart(top_zones_chart(top_zone_df), width="stretch")
    with col2:
        tip_order = st.radio(
            "Urutkan tip zona",
            options=["Tampilkan dari Nilai Tertinggi", "Tampilkan dari Nilai Terendah"],
            index=0,
            key="spatial_tip_sort_order",
        )
        tip_sort_dir = "DESC" if tip_order == "Tampilkan dari Nilai Tertinggi" else "ASC"
        tip_df = get_zone_tip_behavior(filters, limit=15, sort_direction=tip_sort_dir)
        st.subheader("Dinamika Pemberian Tip per Zona")
        st.dataframe(tip_df, width="stretch", hide_index=True)

    st.subheader("Analisis Koridor Bandara")
    st.caption("Melihat apakah area bandara menunjukkan perilaku pelanggan yang berbeda.")
    airport_df = get_airport_corridor_behavior(filters)
    st.dataframe(airport_df, width="stretch", hide_index=True)

    if not zone_df.empty:
        st.markdown("**Pengamatan utama:**")
        st.info(zone_hotspot_sentence(zone_df))
        inequality_note = mobility_inequality_sentence(zone_df)
        if inequality_note:
            st.info(inequality_note)
        tip_anomaly_note = high_tip_anomaly_sentence(tip_df)
        if tip_anomaly_note:
            st.info(tip_anomaly_note)

    st.divider()
    st.caption("Peta dan tabel dirancang untuk saling melengkapi: hotspot menunjukkan konsentrasi, tabel menunjukkan perilaku rata-rata.")

    if st.session_state.get("debug_perf_mode"):
        diagnostics = []
        for label, key in [
            ("payload", "last_map_payload_ms"),
            ("choropleth", "last_choropleth_ms"),
            ("overlay", "last_geojson_overlay_ms"),
            ("render", "last_map_render_ms"),
        ]:
            value = st.session_state.get(key)
            if value is not None:
                diagnostics.append(f"{label} {value} ms")
        if diagnostics:
            st.caption("Diagnostik peta: " + ", ".join(diagnostics))