from __future__ import annotations

import streamlit as st

from config import (
    DEFAULT_BOROUGH_SELECTION,
    DEFAULT_DAY_OF_WEEK_SELECTION,
    DEFAULT_GEOJSON_PRECISION,
    DEFAULT_HOUR_RANGE,
    DEFAULT_MAP_INTERACTION_MODE,
    DEFAULT_RUSH_HOUR_MODE,
    DEFAULT_WEEKEND_MODE,
    DEFAULT_WEATHER_SELECTION,
    MAP_MODE_DESCRIPTIONS,
)
from utils.data_loader import (
    active_behavior_fact_path,
    cluster_file_available,
    get_borough_options,
    get_day_of_week_options,
    get_weather_options,
)


def _init_session_state(key: str, value) -> None:
    if key not in st.session_state:
        st.session_state[key] = value


def render_sidebar_filters() -> dict:
    st.sidebar.subheader("Navigasi Halaman")
    st.sidebar.page_link("app.py", label="Beranda")
    st.sidebar.page_link("pages/01_Ringkasan_Perilaku.py", label="Ringkasan Perilaku")
    st.sidebar.page_link("pages/02_Analisis_Perilaku_Spasial.py", label="Analisis Perilaku Spasial")
    st.sidebar.page_link("pages/03_Analisis_Perilaku_Temporal.py", label="Analisis Perilaku Temporal")
    st.sidebar.page_link("pages/04_Analisis_Cuaca_dan_Perilaku.py", label="Analisis Cuaca dan Perilaku")
    st.sidebar.page_link("pages/05_Segmentasi_Perilaku.py", label="Segmentasi Perilaku")

    st.sidebar.markdown("---")
    st.sidebar.header("Filter Perilaku")

    borough_options = get_borough_options()
    weather_options = get_weather_options()
    cluster_ready = cluster_file_available()

    _init_session_state("filter_boroughs", DEFAULT_BOROUGH_SELECTION[:])
    _init_session_state("filter_hour_range", DEFAULT_HOUR_RANGE)
    _init_session_state("filter_rush_hour_mode", DEFAULT_RUSH_HOUR_MODE)
    _init_session_state("filter_weather_categories", DEFAULT_WEATHER_SELECTION[:])
    _init_session_state("filter_weekend_mode", DEFAULT_WEEKEND_MODE)
    _init_session_state("filter_pickup_days", DEFAULT_DAY_OF_WEEK_SELECTION[:])
    _init_session_state("map_interaction_mode", DEFAULT_MAP_INTERACTION_MODE)
    _init_session_state("geojson_precision", DEFAULT_GEOJSON_PRECISION)
    _init_session_state("debug_perf_mode", False)

    st.sidebar.subheader("Filter Spasial")
    boroughs = st.sidebar.multiselect(
        "Borough penjemputan",
        options=borough_options,
        key="filter_boroughs",
        help="Filter untuk melihat mobilitas berdasarkan borough penjemputan.",
    )
    if not boroughs:
        boroughs = ["All"]

    hour_range = st.sidebar.slider(
        "Rentang jam penjemputan",
        min_value=0,
        max_value=23,
        key="filter_hour_range",
        help="Pilih rentang jam untuk analisis perilaku mobilitas.",
    )

    st.sidebar.subheader("Filter Temporal")

    rush_hour_mode = st.sidebar.radio(
        "Mode jam sibuk",
        options=["All", "Rush only", "Non-rush only"],
        key="filter_rush_hour_mode",
        format_func=lambda x: {"All": "Semua", "Rush only": "Hanya jam sibuk", "Non-rush only": "Non-jam sibuk"}.get(x, x),
    )

    day_options = get_day_of_week_options()
    pickup_days = st.sidebar.multiselect(
        "Hari penjemputan",
        options=day_options,
        key="filter_pickup_days",
        help="Filter perilaku berdasarkan hari dalam sepekan.",
    )
    if not pickup_days:
        pickup_days = ["Semua"]

    weekend_mode = st.sidebar.radio(
        "Kategori hari",
        options=["Semua", "Hari Kerja", "Akhir Pekan"],
        key="filter_weekend_mode",
        help="Pisahkan pola mobilitas antara hari kerja dan akhir pekan.",
    )

    st.sidebar.subheader("Filter Cuaca")
    weather_categories = st.sidebar.multiselect(
        "Kategori cuaca",
        options=weather_options,
        key="filter_weather_categories",
        help="Filter untuk halaman analisis cuaca dan perilaku.",
    )
    if not weather_categories:
        weather_categories = ["All"]

    st.sidebar.markdown("---")
    st.sidebar.subheader("Eksperimen Peta")
    map_interaction_mode = st.sidebar.selectbox(
        "Mode interaksi peta",
        options=["Pasif", "Seimbang", "Interaktif", "Klik Detail", "Hover Ringan"],
        key="map_interaction_mode",
        help="Pilih mode interaksi berdasarkan kebutuhan kelancaran dan kedalaman eksplorasi.",
    )
    st.sidebar.caption(MAP_MODE_DESCRIPTIONS.get(map_interaction_mode, ""))

    geojson_precision = st.sidebar.selectbox(
        "Ketelitian GeoJSON",
        options=[5, 4, 3],
        index=[5, 4, 3].index(st.session_state.get("geojson_precision", DEFAULT_GEOJSON_PRECISION)),
        key="geojson_precision",
        help="Semakin kecil nilainya, semakin ringan payload geometri tetapi semakin kasar batas poligon.",
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Konteks Dataset")
    active_fact = active_behavior_fact_path().name
    st.sidebar.caption(f"Sumber fakta aktif: {active_fact}")
    st.sidebar.caption(f"Status cluster-ready: {'Ya' if cluster_ready else 'Belum'}")

    st.sidebar.subheader("Catatan Analitis")
    st.sidebar.caption("Dashboard ini menyorot perilaku mobilitas, konsentrasi spasial, jam sibuk, dan pengaruh cuaca.")

    st.sidebar.subheader("Debug & Performa")
    st.sidebar.checkbox("Tampilkan timing kueri", key="debug_perf_mode")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Lapisan Segmentasi (kedepan)")
    st.sidebar.selectbox(
        "Segmen pelanggan",
        options=["Semua segmen", "Segmen A", "Segmen B", "Segmen C"],
        index=0,
        disabled=not cluster_ready,
        help="Cadangan untuk integrasi `cluster_label` di fase berikutnya.",
    )
    if not cluster_ready:
        st.sidebar.caption("Output cluster belum tersedia. Filter segmentasi disimpan untuk integrasi berikutnya.")

    return {
        "boroughs": boroughs,
        "hour_range": hour_range,
        "rush_hour_mode": rush_hour_mode,
        "weekend_mode": weekend_mode,
        "pickup_days": pickup_days,
        "weather_categories": weather_categories,
        "cluster_ready": cluster_ready,
        "map_interaction_mode": map_interaction_mode,
        "geojson_precision": geojson_precision,
        "debug_perf_mode": st.session_state.get("debug_perf_mode", False),
    }
