from __future__ import annotations

import streamlit as st

from components.charts import weather_behavior_chart
from queries.weather_queries import get_weather_behavior_comparison, get_weather_tip_behavior
from utils.insights import weather_sensitive_sentence


def render(filters: dict):
    st.header("Analisis Perilaku Berdasarkan Cuaca")
    st.markdown("Menelaah bagaimana kategori cuaca berdampak pada volume perjalanan dan perilaku tipping.")

    weather_df = get_weather_behavior_comparison(filters)
    tip_df = get_weather_tip_behavior(filters)

    if weather_df is None or tip_df is None:
        st.warning("Parquet cuaca tidak tersedia; analisis cuaca tidak dapat ditampilkan.")
        return

    st.plotly_chart(weather_behavior_chart(weather_df), width="stretch")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Cuaca vs Mobilitas")
        st.dataframe(weather_df, width="stretch", hide_index=True)
    with col2:
        st.subheader("Cuaca vs Perilaku Tip")
        st.dataframe(tip_df, width="stretch", hide_index=True)

    st.markdown("**Ringkasan pengaruh cuaca:**")
    st.info(weather_sensitive_sentence(weather_df))

    st.divider()
    st.caption("Cuaca diperlakukan sebagai konteks eksternal untuk memahami perubahan volume dan perilaku tip secara lebih hati-hati.")