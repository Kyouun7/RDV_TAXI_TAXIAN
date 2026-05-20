from __future__ import annotations

import streamlit as st

from components.charts import weather_behavior_chart, weather_duration_tip_chart
from queries.weather_queries import get_weather_behavior_comparison, get_weather_tip_behavior
from utils.insights import weather_sensitive_sentence, weather_tip_contrast_sentence


def render(filters: dict):
    st.header("Analisis Perilaku Berdasarkan Cuaca")
    st.markdown("Menelaah bagaimana kategori cuaca berdampak pada volume perjalanan dan perilaku tipping.")

    weather_df = get_weather_behavior_comparison(filters)
    tip_df = get_weather_tip_behavior(filters)

    if weather_df is None or tip_df is None:
        st.warning("Parquet cuaca tidak tersedia; analisis cuaca tidak dapat ditampilkan.")
        return

    st.plotly_chart(weather_behavior_chart(weather_df), width="stretch")

    st.subheader("Ringkasan Dampak Cuaca terhadap Mobilitas")
    summary_cols = ["weather_category", "trips", "avg_distance", "avg_duration_min", "avg_tip_rate"]
    summary_df = weather_df[summary_cols].copy() if all(col in weather_df.columns for col in summary_cols) else weather_df
    st.dataframe(summary_df, width="stretch", hide_index=True)

    st.subheader("Karakter Perjalanan per Cuaca")
    st.plotly_chart(weather_duration_tip_chart(weather_df), width="stretch")
    st.caption(
        "Ukuran titik merepresentasikan volume perjalanan; posisi menunjukkan durasi dan tip rata-rata untuk tiap kategori cuaca."
    )

    st.markdown("**Ringkasan pengaruh cuaca:**")
    st.info(weather_sensitive_sentence(weather_df))
    tip_contrast_note = weather_tip_contrast_sentence(tip_df)
    if tip_contrast_note:
        st.info(tip_contrast_note)

    st.divider()
    st.caption("Cuaca diperlakukan sebagai konteks eksternal untuk memahami perubahan volume dan perilaku tip secara lebih hati-hati.")