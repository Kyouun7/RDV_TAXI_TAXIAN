from __future__ import annotations

import streamlit as st

from components.charts import hourly_mobility_chart, rush_comparison_chart
from queries.temporal_queries import get_hourly_mobility_trends, get_rush_hour_behavior_comparison
from utils.insights import hourly_spread_sentence, peak_hour_sentence, rush_behavior_sentence


def render(filters: dict):
    st.header("Analisis Perilaku Temporal")
    st.markdown("Memahami kapan pola mobilitas dan perilaku tipping muncul sepanjang hari.")

    hourly_df = get_hourly_mobility_trends(filters)
    st.subheader("Dinamika Mobilitas per Jam")
    st.plotly_chart(hourly_mobility_chart(hourly_df), width="stretch")

    rush_df = get_rush_hour_behavior_comparison(filters)
    st.subheader("Perbandingan Jam Sibuk vs Non-Jam Sibuk")
    st.plotly_chart(rush_comparison_chart(rush_df), width="stretch")
    st.dataframe(rush_df, width="stretch", hide_index=True)

    st.markdown("**Catatan singkat:**")
    st.info(peak_hour_sentence(hourly_df))
    spread_note = hourly_spread_sentence(hourly_df)
    if spread_note:
        st.info(spread_note)
    st.info(rush_behavior_sentence(rush_df))

    st.divider()
    st.caption("Grafik jam digunakan untuk membaca ritme harian, sedangkan tabel jam sibuk memperlihatkan pergeseran perilaku secara ringkas.")