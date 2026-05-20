from __future__ import annotations

import streamlit as st


def render_behavior_kpis(kpi_row):
    cols = st.columns(5)
    cols[0].metric("Total Aktivitas Mobilitas", f"{int(kpi_row['total_trips']):,}")
    cols[1].metric("Rata‑rata Jarak (mi)", f"{kpi_row['avg_trip_distance']:.2f}")
    cols[2].metric("Rata‑rata Durasi (menit)", f"{kpi_row['avg_trip_duration_min']:.2f}")
    cols[3].metric("Rata‑rata Persen Tip (%)", f"{kpi_row['avg_tip_rate_pct']:.2f}")
    cols[4].metric("Zona Penjemput Aktif", f"{int(kpi_row['active_pickup_zones']):,}")

    st.caption("Ringkasan indikator perilaku pelanggan. Gunakan filter di samping untuk mengeksplorasi konteks.")
