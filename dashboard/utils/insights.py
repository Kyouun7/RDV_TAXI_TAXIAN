from __future__ import annotations

import pandas as pd
import numpy as np


def dominant_borough_sentence(borough_df: pd.DataFrame) -> str:
    if borough_df.empty:
        return "Tidak ada data borough tersedia untuk saat ini."
    row = borough_df.sort_values('trips', ascending=False).iloc[0]
    total = borough_df['trips'].sum()
    pct = row['trips'] / total * 100 if total else 0
    top2 = borough_df.sort_values('trips', ascending=False).head(2)['trips'].sum() / total * 100 if total else 0
    comment = ""
    if pct > 50:
        comment = "Konsentrasi tinggi — menunjukkan pola dominan (mis. komuter atau pusat komersial)."
    elif top2 > 65:
        comment = "Dua borough teratas menyumbang sebagian besar mobilitas, mengindikasikan fokus aktivitas terkonsentrasi."
    return f"Wilayah dominan: {row['pickup_borough']} menyumbang {pct:.1f}% dari aktivitas mobilitas saat ini. {comment}"


def peak_hour_sentence(hourly_df: pd.DataFrame) -> str:
    if hourly_df.empty:
        return "Data jam tidak tersedia."
    row = hourly_df.sort_values('trips', ascending=False).iloc[0]
    return f"Periode aktivitas tertinggi pada jam {int(row['pickup_hour'])}:00 dengan {int(row['trips']):,} perjalanan."


def top_tip_zone_sentence(tip_df: pd.DataFrame) -> str:
    if tip_df.empty:
        return "Tidak ada data tip yang mencukupi untuk analisis." 
    row = tip_df.sort_values('avg_tip_rate', ascending=False).iloc[0]
    zone_name = row.get('pickup_zone', row.get('zone_name', 'zona tidak diketahui'))
    borough_name = row.get('pickup_borough', row.get('borough', 'borough tidak diketahui'))
    msg = f"Zona dengan rata‑rata tip tertinggi: {zone_name} ({borough_name}) — rata‑rata tip {row['avg_tip_rate']}%."
    # detect low-volume but high-tip anomaly
    if 'trips' in tip_df.columns and len(tip_df) > 0:
        median_trips = tip_df['trips'].median()
        if row.get('trips', 0) < median_trips and row['avg_tip_rate'] > tip_df['avg_tip_rate'].mean() + tip_df['avg_tip_rate'].std():
            msg += " Catatan: area ini relatif bervolume rendah tetapi menunjukkan tingkat tip yang tidak biasa tinggi — kandidat anomali perilaku pelanggan."
    return msg


def weather_sensitive_sentence(weather_df: pd.DataFrame) -> str:
    if weather_df is None or weather_df.empty:
        return "Data cuaca tidak tersedia untuk analisis sensitivitas cuaca."
    # pick category with largest trips
    row = weather_df.sort_values('trips', ascending=False).iloc[0]
    msg = f"Kategori cuaca dominan: {row['weather_category']} ({int(row['trips']):,} perjalanan), rata‑rata tip {row['avg_tip_rate']}%."
    # detect directional effects in weather categories if available
    if 'trips_change_vs_clear' in row.index:
        delta = row['trips_change_vs_clear']
        if delta < -0.1:
            msg += " Perjalanan cenderung menurun secara substansial dibanding cuaca cerah, menunjukkan sensitivitas mobilitas terhadap kondisi tersebut."
        elif delta > 0.1:
            msg += " Perjalanan meningkat relatif terhadap cuaca cerah — indikasi aktivitas khusus atau acara yang mempengaruhi permintaan."
    return msg


def rush_behavior_sentence(rush_df: pd.DataFrame) -> str:
    if rush_df is None or rush_df.empty:
        return "Data jam sibuk tidak tersedia."

    indexed = rush_df.set_index("period")
    rush_label = None
    non_rush_label = None
    for label in indexed.index:
        lower = str(label).lower()
        if "rush" in lower and "non" not in lower:
            rush_label = label
        if "non" in lower and "rush" in lower:
            non_rush_label = label
        if "jam sibuk" in lower and "non" not in lower:
            rush_label = label
        if "non-jam sibuk" in lower:
            non_rush_label = label

    if rush_label is not None and non_rush_label is not None:
        rush = indexed.loc[rush_label]
        non_rush = indexed.loc[non_rush_label]
        duration_delta = rush["avg_duration_min"] - non_rush["avg_duration_min"]
        tip_delta = rush["avg_tip_rate"] - non_rush["avg_tip_rate"]
        return (
            "Pada jam sibuk, durasi rata-rata cenderung "
            f"{duration_delta:+.1f} menit dibanding non-jam sibuk, sementara tip rata-rata berubah {tip_delta:+.2f} poin persentase."
        )

    return "Perbandingan jam sibuk tersedia, namun pola utama belum dapat diringkas secara stabil."


def zone_hotspot_sentence(zone_df: pd.DataFrame) -> str:
    if zone_df is None or zone_df.empty:
        return "Data zona belum tersedia."
    count_column = "trip_count" if "trip_count" in zone_df.columns else "trips"
    row = zone_df.sort_values(count_column, ascending=False).iloc[0]
    zone_name = row.get('zone_name', row.get('pickup_zone', 'zona tidak diketahui'))
    borough_name = row.get('borough', row.get('pickup_borough', 'borough tidak diketahui'))
    msg = f"Hotspot utama berada di {zone_name} ({borough_name}) dengan {int(row[count_column]):,} perjalanan."
    # compare tip behavior in hotspot vs city median
    if 'avg_tip_rate' in zone_df.columns:
        city_median_tip = zone_df['avg_tip_rate'].median()
        if row['avg_tip_rate'] > city_median_tip:
            msg += f" Zona ini juga menunjukkan tip rata‑rata lebih tinggi ({row['avg_tip_rate']}%) dibanding median kota ({city_median_tip:.1f}%), mengindikasikan profil pelanggan dengan kecenderungan tipping lebih kuat."
    return msg


def mobility_inequality_sentence(zone_df: pd.DataFrame, count_column: str = 'trips') -> str:
    """Estimate concentration of mobility across zones (simple Gini approximation).

    Returns a concise sentence about mobility concentration.
    """
    if zone_df is None or zone_df.empty or count_column not in zone_df.columns:
        return "Tidak cukup data untuk menilai ketimpangan konsentrasi mobilitas."
    values = zone_df[count_column].fillna(0).to_numpy(dtype=float)
    if values.sum() == 0:
        return "Tidak ada perjalanan tercatat untuk menghitung konsentrasi." 
    # Gini coefficient
    sorted_vals = np.sort(values)
    n = len(sorted_vals)
    index = np.arange(1, n + 1)
    gini = (2.0 * np.sum(index * sorted_vals) / (n * sorted_vals.sum())) - (n + 1) / n
    gini = max(0.0, min(1.0, gini))
    if gini > 0.5:
        tone = "tinggi"
    elif gini > 0.3:
        tone = "moderate"
    else:
        tone = "rendah"
    pct_top5 = sorted_vals[-5:].sum() / sorted_vals.sum() * 100 if n >= 5 else sorted_vals[-1:].sum() / sorted_vals.sum() * 100
    return f"Konsentrasi mobilitas: Gini ≈ {gini:.2f} (konsentrasi {tone}), {pct_top5:.1f}% perjalanan berada di 5 zona teratas."


def high_tip_anomaly_sentence(tip_df: pd.DataFrame) -> str:
    if tip_df is None or tip_df.empty:
        return "Tidak cukup data tip untuk mendeteksi anomali."
    # rank by z-score of avg_tip_rate
    mean = tip_df['avg_tip_rate'].mean()
    std = tip_df['avg_tip_rate'].std()
    if std == 0 or np.isnan(std):
        return "Variabilitas tip rendah — tidak ditemukan anomali tip yang menonjol."
    tip_df = tip_df.copy()
    tip_df['z'] = (tip_df['avg_tip_rate'] - mean) / std
    anomalies = tip_df[tip_df['z'] > 2]
    if anomalies.empty:
        return "Tidak ditemukan zona dengan tingkat tip yang secara statistik menonjol." 
    top = anomalies.sort_values('z', ascending=False).iloc[0]
    zone = top.get('pickup_zone', top.get('zone_name', 'zona tidak diketahui'))
    return f"Anomali tip terdeteksi: {zone} menunjukkan tip jauh di atas rata‑rata (z={top['z']:.2f}), kandidat untuk studi pelanggan lebih lanjut."
