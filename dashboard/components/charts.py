from __future__ import annotations

import pandas as pd
import plotly.express as px
from config import SOFT_PALETTE


def borough_distribution_chart(df: pd.DataFrame):
    fig = px.bar(
        df,
        x="pickup_borough",
        y="trips",
        color="avg_tip_rate_pct",
        color_continuous_scale=SOFT_PALETTE.get("choropleth_scale"),
        title="Distribusi Mobilitas Perilaku per Borough",
        labels={
            "trips": "Jumlah Perjalanan",
            "pickup_borough": "Borough Penjemputan",
        },
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    fig.update_traces(marker_line_width=0)

    return fig


def top_zones_chart(df: pd.DataFrame):
    fig = px.bar(
        df,
        x="trips",
        y="pickup_zone",
        color="avg_tip_rate",
        color_continuous_scale=SOFT_PALETTE.get("choropleth_scale"),
        orientation="h",
        title="Hotspot Mobilitas Perilaku (Zona)",
        labels={
            "pickup_zone": "Zona Penjemputan",
            "trips": "Jumlah Perjalanan",
        },
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    fig.update_traces(marker_line_width=0)

    return fig


def hourly_mobility_chart(df: pd.DataFrame):
    fig = px.line(
        df,
        x="pickup_hour",
        y="trips",
        markers=True,
        title="Dinamika Mobilitas per Jam",
        labels={
            "pickup_hour": "Jam Penjemputan",
            "trips": "Jumlah Perjalanan",
        },
    )

    # Force green-teal theme
    fig.update_traces(
        line=dict(
            color="#2f857f",
            width=4,
        ),
        marker=dict(
            color="#74bf8f",
            size=8,
        ),
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def rush_comparison_chart(df: pd.DataFrame):
    fig = px.bar(
        df,
        x="period",
        y=["avg_duration_min", "avg_tip_rate"],
        barmode="group",
        title="Perbandingan Mobilitas: Jam Sibuk vs Non-Jam Sibuk",
        labels={
            "value": "Nilai Metrik",
            "period": "Periode",
        },
        color_discrete_sequence=[
            "#74bf8f",
            "#0f5b6e",
        ],
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    fig.update_traces(marker_line_width=0)

    return fig


def weather_behavior_chart(df: pd.DataFrame):
    fig = px.bar(
        df,
        x="weather_category",
        y="trips",
        color="avg_tip_rate",
        color_continuous_scale=SOFT_PALETTE.get("choropleth_scale"),
        title="Pengaruh Cuaca terhadap Mobilitas",
        labels={
            "weather_category": "Kategori Cuaca",
            "trips": "Jumlah Perjalanan",
        },
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    fig.update_traces(marker_line_width=0)

    return fig