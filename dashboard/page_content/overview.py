from __future__ import annotations

import streamlit as st

from components.charts import borough_distribution_chart, top_zones_chart
from components.kpi_cards import render_behavior_kpis
from components.map_component import render_behavior_choropleth
from queries.overview_queries import get_behavior_kpis, get_borough_mobility_distribution
from queries.spatial_queries import get_top_behavior_pickup_zones, get_zone_behavior_intensity, get_zone_tip_behavior
from queries.temporal_queries import get_hourly_mobility_trends
from queries.weather_queries import get_weather_behavior_comparison
from utils.data_loader import load_geojson
from utils.insights import (
    dominant_borough_sentence,
    peak_hour_sentence,
    top_tip_zone_sentence,
    weather_sensitive_sentence,
    mobility_inequality_sentence,
    high_tip_anomaly_sentence,
)


def render(filters: dict):
    st.header("Ringkasan Perilaku")
    st.markdown(
        "Ringkasan ini menyajikan indikator utama perilaku mobilitas penumpang taksi sebagai konteks sebelum integrasi segmentasi."
    )

    kpi_df = get_behavior_kpis(filters)
    render_behavior_kpis(kpi_df.iloc[0])

    st.subheader("Peta Hotspot Mobilitas Perilaku")
    st.caption("Peta berfokus pada konsentrasi pergerakan dan pola tipping per zona.")
    zone_df = get_zone_behavior_intensity(filters)
    render_behavior_choropleth(
        zone_df,
        load_geojson(precision=int(filters.get("geojson_precision", 5))),
        value_col="trip_count",
        interaction_mode=filters.get("map_interaction_mode", "Seimbang"),
    )

    col1, col2 = st.columns(2)
    with col1:
        borough_order = st.radio(
            "Urutkan borough",
            options=["Tampilkan dari Nilai Terbesar", "Tampilkan dari Nilai Terkecil"],
            index=0,
            key="overview_borough_sort_order",
        )
        borough_sort_dir = "DESC" if borough_order == "Tampilkan dari Nilai Terbesar" else "ASC"
        borough_df = get_borough_mobility_distribution(filters, sort_direction=borough_sort_dir)
        st.plotly_chart(borough_distribution_chart(borough_df), width="stretch")
    with col2:
        zone_order = st.radio(
            "Urutkan hotspot",
            options=["Tampilkan dari Nilai Terbesar", "Tampilkan dari Nilai Terkecil"],
            index=0,
            key="overview_zone_sort_order",
        )
        zone_sort_dir = "DESC" if zone_order == "Tampilkan dari Nilai Terbesar" else "ASC"
        top_zones_df = get_top_behavior_pickup_zones(filters, limit=12, sort_direction=zone_sort_dir)
        st.plotly_chart(top_zones_chart(top_zones_df), width="stretch")

    hourly = get_hourly_mobility_trends(filters)
    weather = get_weather_behavior_comparison(filters)

    insights = [
        dominant_borough_sentence(borough_df),
        peak_hour_sentence(hourly),
        top_tip_zone_sentence(top_zones_df),
    ]
    if weather is not None:
        insights.append(weather_sensitive_sentence(weather))
    # add mobility concentration and tip anomaly checks (lightweight)
    insights.append(mobility_inequality_sentence(zone_df))
    tip_df = get_zone_tip_behavior(filters, limit=50)
    insights.append(high_tip_anomaly_sentence(tip_df))

    st.subheader("Interpretasi Singkat")
    st.caption("Ringkasan berikut menafsirkan hasil agregasi, bukan menarik kesimpulan kausal yang berlebihan.")
    for note in insights:
        st.info(note)

    st.divider()
    st.markdown(
        "Catatan: Semua temuan bersifat konteks perilaku — menunjukkan area dan periode yang berpotensi mewakili profil pelanggan berbeda."
    )

    if st.session_state.get("debug_perf_mode"):
        payload_ms = st.session_state.get("last_map_payload_ms")
        render_ms = st.session_state.get("last_map_render_ms")
        if payload_ms is not None or render_ms is not None:
            st.caption(
                "Timing peta: "
                + ", ".join(
                    part
                    for part in [
                        f"payload {payload_ms} ms" if payload_ms is not None else None,
                        f"render {render_ms} ms" if render_ms is not None else None,
                    ]
                    if part is not None
                )
            )