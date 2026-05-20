from __future__ import annotations

import pandas as pd
import streamlit as st

from components.charts import (
    segment_distribution_chart,
    segment_hourly_chart,
    segment_profile_comparison_chart,
    segment_weather_chart,
)
from components.segment_map_component import render_segment_cluster_map
from config import SEGMENT_DISPLAY_NAMES
from queries.segmentation_queries import (
    get_segment_borough_mix,
    get_segment_hourly_pattern,
    get_segment_profile,
    get_segment_weather_pattern,
    get_segment_zone_dominance,
)
from utils.data_loader import cluster_file_available, get_segment_options, load_geojson
from utils.insights import (
    segment_contrast_sentence,
    segment_mix_sentence,
    segment_profile_sentence,
    segment_weather_sentence,
)


def _format_pct(value: float) -> str:
    return f"{value:.1f}%"


def render(filters: dict):
    st.header("Segmentasi Perilaku")
    st.markdown(
        "Halaman ini menerjemahkan hasil clustering menjadi segmen perilaku yang dapat dieksplorasi secara analitis. Tujuan ML: menemukan pola mobilitas tersembunyi—mengelompokkan perjalanan berdasarkan karakteristik rute, durasi, waktu, dan respons terhadap cuaca—sebagai bahan interpretasi operasi dan kebijakan."
    )
    st.markdown(
        "**Apa yang dimaksud dengan setiap segmen (ringkasan perilaku):**"
    )
    st.markdown(
        "- **Mobilitas Urban Menengah**: perjalanan berjarak menengah, sering terjadi di area perkotaan dengan durasi sedang; cenderung terjadi pada jam kerja dan menunjukkan tip rate sedang sampai tinggi.\n"
        "- **Perjalanan Urban Bernilai Tinggi**: perjalanan singkat hingga menengah yang menunjukkan pola nilai (tip) lebih tinggi; umumnya terkait dengan rute bernilai ekonomi atau penumpang bisnis di jam-jam sibuk.\n"
        "- **Mobilitas Jarak Jauh / Bandara**: perjalanan panjang dengan durasi lebih lama, sering terhubung ke bandara atau rute lintas-borough; mempengaruhi distribusi zona dan pola waktu berbeda (mis. lebih banyak di luar jam sibuk)."
    )
    st.markdown(
        "**Tujuan analitis ML:** mengelompokkan pelanggan berdasarkan perilaku perjalanan (jarak, durasi, frekuensi, sensitivitas cuaca, dan tip) untuk membantu tim operasional dan analitik memahami profil mobilitas berbeda, merancang layanan yang sesuai, dan memprioritaskan pengujian hipotesis lebih lanjut."
    )

    if not cluster_file_available():
        st.warning(
            "Output segmented_trips_final.parquet belum ditemukan. Jalankan notebook ML_Clustering.ipynb untuk mengaktifkan halaman segmentasi."
        )
        st.caption("Saat artefak tersedia, halaman ini akan menampilkan distribusi segmen, peta dominasi, dan profil perilaku per segmen.")
        return

    st.markdown("**Filter segmentasi (khusus halaman ini)**")
    segment_options = get_segment_options()
    selected_segment = st.selectbox(
        "Segmen pelanggan",
        options=segment_options,
        format_func=lambda value: SEGMENT_DISPLAY_NAMES.get(value, value),
        key="segment_filter_local",
        help="Filter ini hanya memengaruhi halaman Segmentasi Perilaku.",
    )
    filters = {**filters, "segment_filter": selected_segment}

    summary_df = get_segment_profile(filters)
    borough_mix_df = get_segment_borough_mix(filters)
    hourly_df = get_segment_hourly_pattern(filters)
    weather_df = get_segment_weather_pattern(filters)
    zone_df = get_segment_zone_dominance(filters, limit=24)

    if summary_df.empty:
        st.info("Tidak ada data segmen untuk filter yang dipilih saat ini.")
        return

    dominant_row = summary_df.sort_values("trips", ascending=False).iloc[0]
    total_trips = int(summary_df["trips"].sum())
    active_segments = int(summary_df["customer_segment"].nunique())
    avg_tip = float(summary_df["avg_tip_rate_pct"].mean())

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total perjalanan", f"{total_trips:,}")
    kpi2.metric("Segmen aktif", active_segments)
    kpi3.metric(
        "Segmen dominan",
        SEGMENT_DISPLAY_NAMES.get(dominant_row.get("customer_segment", "-"), dominant_row.get("customer_segment", "-")),
        help="Segmen dengan jumlah perjalanan terbesar pada filter saat ini.",
    )
    kpi4.metric("Rata-rata tip segmen", _format_pct(avg_tip))

    st.subheader("Distribusi Segmen")
    st.caption("Komposisi klaster memperlihatkan bagaimana perjalanan terkonsentrasi ke segmen perilaku tertentu.")
    st.plotly_chart(segment_distribution_chart(summary_df), width="stretch")

    st.subheader("Profil Perbandingan Segmen")
    st.caption("Perbandingan ini membantu membaca perbedaan mobilitas, durasi, tip, kecepatan, dan intensitas jam sibuk antar segmen.")
    st.plotly_chart(segment_profile_comparison_chart(summary_df), width="stretch")
    contrast_note = segment_contrast_sentence(summary_df)
    if contrast_note:
        st.info(contrast_note)

    st.subheader("Peta Dominasi Segmen per Zona")
    st.caption("Warna zona menunjukkan segmen yang paling dominan pada zona penjemputan tersebut.")
    render_segment_cluster_map(
        zone_df,
        load_geojson(precision=int(filters.get("geojson_precision", 5))),
        interaction_mode=filters.get("map_interaction_mode", "Seimbang"),
    )

    st.subheader("Dinamika Waktu dan Cuaca")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(segment_hourly_chart(hourly_df), width="stretch")
    with col2:
        if weather_df.empty:
            st.info("Data cuaca tidak tersedia pada subset segmen ini.")
        else:
            st.plotly_chart(segment_weather_chart(weather_df), width="stretch")

    st.subheader("Interpretasi Segmen")
    st.caption("Narasi berikut dibangun dari statistik agregat, bukan klaim kausal yang berlebihan.")
    narrative_cols = st.columns(min(len(summary_df), 3))
    for index, (_, row) in enumerate(summary_df.sort_values("trips", ascending=False).iterrows()):
        if index >= len(narrative_cols):
            break
        with narrative_cols[index]:
            segment_label = SEGMENT_DISPLAY_NAMES.get(row.get('customer_segment', 'Segmen'), row.get('customer_segment', 'Segmen'))
            st.markdown(f"#### {segment_label}")

            borough_subset = borough_mix_df[borough_mix_df["cluster_id"] == row["cluster_id"]]
            weather_subset = weather_df[weather_df["cluster_id"] == row["cluster_id"]] if not weather_df.empty else pd.DataFrame()
            hourly_subset = hourly_df[hourly_df["cluster_id"] == row["cluster_id"]] if not hourly_df.empty else pd.DataFrame()

            temporal_note = ""
            if not hourly_subset.empty:
                peak_row = hourly_subset.sort_values("trips", ascending=False).iloc[0]
                peak_hour = int(peak_row.get("pickup_hour", 0))
                temporal_note = f"Puncak aktivitas sekitar pukul {peak_hour:02d}."

            tip_note = ""
            if pd.notna(row.get("avg_tip_rate_pct")):
                tip_note = f"Rata-rata tip sekitar {_format_pct(float(row.get('avg_tip_rate_pct')))}."

            primary_summary = segment_profile_sentence(row)
            st.info(primary_summary)

            secondary_items = []
            if not borough_subset.empty:
                secondary_items.append(("Pola spasial", segment_mix_sentence(borough_subset)))
            if temporal_note:
                secondary_items.append(("Pola temporal", temporal_note))
            if tip_note:
                secondary_items.append(("Perilaku tipping", tip_note))
            if not weather_subset.empty:
                secondary_items.append(("Sensitivitas cuaca", segment_weather_sentence(weather_subset)))

            if secondary_items:
                secondary_html = "".join(
                    f"<div style='margin-bottom:6px; color:#3d9cf2;'><strong>{label}:</strong> {text}</div>"
                    for label, text in secondary_items
                )
                st.markdown(
                    """
                    <div style="background:#1f3554; border:1px solid #2b4b74; border-radius:8px; padding:10px 12px; color:#8ec5ff;">
                        <div style="font-weight:600; margin-bottom:6px; color:#3d9cf2;">Catatan Pendukung</div>
                        {content}
                    </div>
                    """.format(content=secondary_html),
                    unsafe_allow_html=True,
                )

    st.divider()
    st.caption(
        "Segmentasi ini menjadi lapisan akhir narasi dashboard: dari pola spasial, temporal, dan cuaca, kini perilaku pelanggan dipadatkan menjadi segmen yang dapat dipakai untuk interpretasi akademik dan eksplorasi lanjutan."
    )

    if st.session_state.get("debug_perf_mode"):
        payload_ms = st.session_state.get("last_segment_map_payload_ms")
        render_ms = st.session_state.get("last_segment_map_render_ms")
        if payload_ms is not None or render_ms is not None:
            st.caption(
                "Timing segmentasi: "
                + ", ".join(
                    part
                    for part in [
                        f"payload {payload_ms} ms" if payload_ms is not None else None,
                        f"render {render_ms} ms" if render_ms is not None else None,
                    ]
                    if part is not None
                )
            )
