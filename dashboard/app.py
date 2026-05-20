from __future__ import annotations

import streamlit as st

from components.filters import render_sidebar_filters
from components.kpi_cards import render_behavior_kpis
from config import APP_SUBTITLE, APP_TITLE
from queries.overview_queries import get_behavior_kpis, get_borough_mobility_distribution
from queries.spatial_queries import get_top_behavior_pickup_zones
from queries.temporal_queries import get_hourly_mobility_trends
from utils.insights import dominant_borough_sentence, peak_hour_sentence, zone_hotspot_sentence


def main():
    st.set_page_config(page_title=f"Beranda | {APP_TITLE}", page_icon="🏠", layout="wide")

    st.title("Beranda")
    st.caption(f"{APP_TITLE} — {APP_SUBTITLE}")

    filters = render_sidebar_filters()

    st.markdown(
        """
        Dashboard ini merangkum perilaku mobilitas pelanggan taksi NYC sebagai objek analisis, bukan sekadar volume perjalanan.
        Fokusnya adalah membaca konsentrasi spasial, ritme waktu, dan konteks eksternal untuk membangun dasar segmentasi perilaku.
        """
    )

    st.info(
        "Gunakan navigasi Streamlit di sisi kiri untuk masuk ke analisis spasial, temporal, cuaca, dan halaman segmentasi yang tetap siap diintegrasikan nanti."
    )

    kpi_df = get_behavior_kpis(filters)
    render_behavior_kpis(kpi_df.iloc[0])

    col_left, col_right = st.columns([1.15, 0.85])
    with col_left:
        st.subheader("Konteks Inti")
        st.markdown(
            """
            Proyek ini berangkat dari kebutuhan membedakan pola pelanggan melalui mobilitas spasial.
            Analisis tidak berhenti pada volume perjalanan, tetapi membaca sebaran zona, jam aktif,
            dan sinyal perilaku yang dapat menjadi dasar segmentasi di tahap berikutnya.
            """
        )
        st.markdown(
            """
            **Tujuan utama**
            - Memetakan konsentrasi aktivitas pelanggan secara spasial.
            - Mengidentifikasi dinamika perilaku pada jam sibuk.
            - Membaca pengaruh cuaca terhadap intensitas perjalanan dan tip.
            - Menyiapkan fondasi segmentasi perilaku yang konsisten dan dapat diperluas.
            """
        )
    with col_right:
        st.subheader("Sorotan Cepat")
        borough_df = get_borough_mobility_distribution(filters)
        hourly_df = get_hourly_mobility_trends(filters)
        st.info(dominant_borough_sentence(borough_df))
        st.info(peak_hour_sentence(hourly_df))
        st.info(zone_hotspot_sentence(get_top_behavior_pickup_zones(filters, limit=10)))

    st.subheader("Panduan Penggunaan")
    guide_col1, guide_col2 = st.columns(2)
    with guide_col1:
        st.markdown(
            """
            - Mulai dari ringkasan untuk memahami konteks perilaku.
            - Gunakan analisis spasial untuk melihat hotspot dan zona dominan.
            - Buka temporal untuk membaca ritme jam sibuk.
            """
        )
    with guide_col2:
        st.markdown(
            """
            - Gunakan halaman cuaca untuk melihat konteks eksternal.
            - Gunakan halaman segmentasi sebagai ruang persiapan model klaster.
            - Semua filter bersifat global dan tetap konsisten lintas halaman.
            """
        )

    st.subheader("Narasi Akademik Singkat")
    narrative_col1, narrative_col2 = st.columns(2)
    with narrative_col1:
        st.markdown(
            """
            Dashboard ini memposisikan mobilitas sebagai perilaku, bukan sekadar transportasi.
            Dengan membaca zona, waktu, dan cuaca secara bersamaan, aplikasi ini membantu menyusun
            hipotesis tentang perbedaan karakter pelanggan secara lebih terukur.
            """
        )
    with narrative_col2:
        st.markdown(
            """
            Hasil akhirnya adalah antarmuka analitik yang siap dipresentasikan: ringkas, konsisten,
            dan tetap terbuka untuk integrasi segmentasi pelanggan berbasis klaster pada fase berikutnya.
            """
        )

    st.divider()
    st.caption("Halaman ringkasan sengaja dibuat ringan agar startup lebih cepat; analisis peta dan visual berat tersedia di halaman multipage.")

    if st.session_state.get("debug_perf_mode"):
        payload_ms = st.session_state.get("last_map_payload_ms")
        render_ms = st.session_state.get("last_map_render_ms")
        if payload_ms is not None or render_ms is not None:
            st.caption(
                "Timing peta terakhir: "
                + ", ".join(
                    part
                    for part in [
                        f"payload {payload_ms} ms" if payload_ms is not None else None,
                        f"render {render_ms} ms" if render_ms is not None else None,
                    ]
                    if part is not None
                )
            )

    if st.session_state.get("debug_perf_mode"):
        last_query_ms = st.session_state.get("last_query_time_ms")
        if last_query_ms is not None:
            st.caption(f"Timing kueri terakhir: {last_query_ms} ms")
        else:
            st.caption("Timing kueri belum tersedia pada sesi ini.")


if __name__ == "__main__":
    main()
