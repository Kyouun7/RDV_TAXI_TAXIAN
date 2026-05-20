from __future__ import annotations

import streamlit as st

from utils.data_loader import cluster_file_available


def render(filters: dict):
    st.header("Placeholder Segmentasi")
    st.caption("Lapisan cadangan untuk integrasi intelijen perilaku berbasis klaster di masa depan.")

    ready = cluster_file_available()

    if ready:
        st.success("Output cluster terdeteksi. Halaman ini siap untuk fase implementasi berikutnya.")
    else:
        st.info(
            "Output cluster belum tersedia. Dashboard tetap mendukung narasi berorientasi segmentasi melalui kueri konteks perilaku."
        )

    st.subheader("Slot Analitik Segmentasi (Cadangan)")
    c1, c2 = st.columns(2)
    with c1:
        st.selectbox(
            "Segmen dominan per zona",
            options=["Menunggu output model"],
            disabled=True,
        )
    with c2:
        st.selectbox(
            "Tren segmen seiring waktu",
            options=["Menunggu output model"],
            disabled=True,
        )

    st.markdown("### Hook Integrasi yang Direncanakan")
    st.markdown("- Penyambungan filter `cluster_label` di lapisan kueri")
    st.markdown("- Lapisan choropleth segmen dominan")
    st.markdown("- Perbandingan perilaku segmen vs cuaca")
    st.markdown("- Dinamika tipping dan mobilitas per segmen")

    st.divider()
    st.caption("Halaman ini sengaja tetap informatif tetapi tidak memalsukan hasil segmentasi yang belum tersedia.")