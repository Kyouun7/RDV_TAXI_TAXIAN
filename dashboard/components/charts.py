from __future__ import annotations

import pandas as pd
import plotly.express as px
from config import SEGMENT_DISPLAY_NAMES, SOFT_PALETTE


def _localize_segments(df: pd.DataFrame) -> pd.DataFrame:
    if "customer_segment" not in df.columns:
        return df
    localized = df.copy()
    localized["customer_segment"] = localized["customer_segment"].map(
        lambda value: SEGMENT_DISPLAY_NAMES.get(value, value)
    )
    return localized


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


def weather_duration_tip_chart(df: pd.DataFrame):
    fig = px.scatter(
        df,
        x="avg_duration_min",
        y="avg_tip_rate",
        size="trips",
        color="weather_category",
        title="Karakter Perjalanan per Kategori Cuaca",
        size_max=80,
        labels={
            "avg_duration_min": "Durasi Rata-rata (menit)",
            "avg_tip_rate": "Tip Rata-rata (%)",
            "trips": "Jumlah Perjalanan",
            "weather_category": "Kategori Cuaca",
        },
        hover_data={
            "weather_category": True,
            "trips": True,
            "avg_distance": True,
            "avg_duration_min": ":.2f",
            "avg_tip_rate": ":.2f",
        },
        color_discrete_sequence=["#2aa893", "#1d8fbd", "#7a5ca8", "#f0b35d", "#8a8fbf"],
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend_title_text="Kategori Cuaca",
    )
    fig.update_traces(marker=dict(line=dict(width=0)))
    return fig


def segment_distribution_chart(df: pd.DataFrame):
    localized = _localize_segments(df)
    fig = px.bar(
        localized,
        x="customer_segment",
        y="trips",
        color="avg_tip_rate_pct" if "avg_tip_rate_pct" in localized.columns else None,
        color_continuous_scale=SOFT_PALETTE.get("choropleth_scale"),
        title="Distribusi Perjalanan per Segmen",
        labels={
            "customer_segment": "Segmen Perilaku",
            "trips": "Jumlah Perjalanan",
        },
    )
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    fig.update_traces(marker_line_width=0)
    return fig


def segment_profile_comparison_chart(df: pd.DataFrame):
    localized = _localize_segments(df)
    metrics = [
        "avg_trip_distance",
        "avg_trip_duration_min",
        "avg_tip_rate_pct",
        "avg_speed_mph",
        "rush_hour_ratio",
        "weekend_ratio",
    ]
    available_metrics = [column for column in metrics if column in localized.columns]
    if not available_metrics:
        return px.bar(title="Perbandingan Profil Segmen")

    melted = localized[["customer_segment", *available_metrics]].melt(
        id_vars="customer_segment",
        var_name="metric",
        value_name="value",
    )
    metric_labels = {
        "avg_trip_distance": "Jarak Rata-rata",
        "avg_trip_duration_min": "Durasi Rata-rata",
        "avg_tip_rate_pct": "Tip Rata-rata (%)",
        "avg_speed_mph": "Kecepatan Rata-rata",
        "rush_hour_ratio": "Rasio Jam Sibuk",
        "weekend_ratio": "Rasio Akhir Pekan",
    }
    melted["metric"] = melted["metric"].map(metric_labels)
    fig = px.bar(
        melted,
        x="customer_segment",
        y="value",
        color="customer_segment",
        facet_col="metric",
        facet_col_wrap=3,
        title="Perbandingan Profil Segmen",
        labels={
            "customer_segment": "Segmen Perilaku",
            "value": "Nilai",
        },
        color_discrete_sequence=["#2aa893", "#1d8fbd", "#7a5ca8"],
        text_auto=True,
    )
    fig.for_each_annotation(lambda annotation: annotation.update(text=annotation.text.split("=")[-1]))
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=650)
    fig.update_traces(marker_line_width=0)
    return fig


def segment_hourly_chart(df: pd.DataFrame):
    localized = _localize_segments(df)
    fig = px.line(
        localized,
        x="pickup_hour",
        y="trips",
        color="customer_segment",
        markers=True,
        title="Dinamika Segmen per Jam",
        labels={
            "pickup_hour": "Jam Penjemputan",
            "trips": "Jumlah Perjalanan",
            "customer_segment": "Segmen Perilaku",
        },
        color_discrete_sequence=["#2aa893", "#1d8fbd", "#7a5ca8"],
    )
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig


def segment_weather_chart(df: pd.DataFrame):
    localized = _localize_segments(df)
    fig = px.bar(
        localized,
        x="weather_category",
        y="trips",
        color="customer_segment",
        barmode="group",
        title="Sensitivitas Cuaca per Segmen",
        labels={
            "weather_category": "Kategori Cuaca",
            "trips": "Jumlah Perjalanan",
            "customer_segment": "Segmen Perilaku",
        },
        color_discrete_sequence=["#2aa893", "#1d8fbd", "#7a5ca8"],
    )
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    fig.update_traces(marker_line_width=0)
    return fig