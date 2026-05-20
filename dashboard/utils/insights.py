from __future__ import annotations

import pandas as pd

from config import SEGMENT_DISPLAY_NAMES
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


def mobility_inequality_sentence(zone_df: pd.DataFrame, count_column: str = 'trips') -> str | None:
    """Estimate concentration of mobility across zones (simple Gini approximation).

    Returns a concise sentence about mobility concentration.
    """
    if zone_df is None or zone_df.empty or count_column not in zone_df.columns:
        return None
    values = zone_df[count_column].fillna(0).to_numpy(dtype=float)
    if values.sum() == 0:
        return None
    # Gini coefficient
    sorted_vals = np.sort(values)
    n = len(sorted_vals)
    index = np.arange(1, n + 1)
    gini = (2.0 * np.sum(index * sorted_vals) / (n * sorted_vals.sum())) - (n + 1) / n
    gini = max(0.0, min(1.0, gini))
    if gini > 0.5:
        tone = "tinggi"
    elif gini > 0.3:
        tone = "sedang"
    else:
        tone = "rendah"
    pct_top5 = sorted_vals[-5:].sum() / sorted_vals.sum() * 100 if n >= 5 else sorted_vals[-1:].sum() / sorted_vals.sum() * 100
    return f"Konsentrasi mobilitas: Gini ≈ {gini:.2f} (konsentrasi {tone}), {pct_top5:.1f}% perjalanan berada di 5 zona teratas."


def high_tip_anomaly_sentence(tip_df: pd.DataFrame) -> str | None:
    if tip_df is None or tip_df.empty:
        return None

    tip_df = tip_df.copy()
    if 'avg_tip_rate' not in tip_df.columns:
        return None

    p90 = tip_df['avg_tip_rate'].quantile(0.9)
    p10 = tip_df['avg_tip_rate'].quantile(0.1)
    median_trips = tip_df['trips'].median() if 'trips' in tip_df.columns else None

    high_tip = tip_df[tip_df['avg_tip_rate'] >= p90]
    low_tip = tip_df[tip_df['avg_tip_rate'] <= p10]

    high_tip_row = None
    if not high_tip.empty:
        if median_trips is not None:
            candidates = high_tip[high_tip['trips'] <= median_trips]
            high_tip_row = (candidates if not candidates.empty else high_tip).sort_values('avg_tip_rate', ascending=False).iloc[0]
        else:
            high_tip_row = high_tip.sort_values('avg_tip_rate', ascending=False).iloc[0]

    low_tip_row = None
    if not low_tip.empty and median_trips is not None:
        candidates = low_tip[low_tip['trips'] >= median_trips]
        if not candidates.empty:
            low_tip_row = candidates.sort_values('avg_tip_rate', ascending=True).iloc[0]

    if high_tip_row is not None and low_tip_row is not None:
        high_zone = high_tip_row.get('pickup_zone', high_tip_row.get('zone_name', 'zona tidak diketahui'))
        low_zone = low_tip_row.get('pickup_zone', low_tip_row.get('zone_name', 'zona tidak diketahui'))
        return (
            f"Kontras tip terlihat jelas: {high_zone} berada di kelompok tip tinggi (~{high_tip_row['avg_tip_rate']:.2f}%) "
            f"sementara {low_zone} berada di kelompok tip rendah (~{low_tip_row['avg_tip_rate']:.2f}%) meski volumenya relatif besar."
        )

    if high_tip_row is not None:
        zone = high_tip_row.get('pickup_zone', high_tip_row.get('zone_name', 'zona tidak diketahui'))
        if median_trips is not None:
            return (
                f"Zona tip tinggi seperti {zone} (~{high_tip_row['avg_tip_rate']:.2f}%) muncul dengan volume lebih kecil dari median, "
                "mengindikasikan tipping yang kuat pada kantong permintaan tertentu."
            )
        return f"Zona tip tinggi seperti {zone} (~{high_tip_row['avg_tip_rate']:.2f}%) menonjol di antara zona lain."

    spread = p90 - p10
    return f"Sebaran tip antar zona relatif terkendali (selisih P90-P10 ≈ {spread:.2f} poin), tidak tampak outlier ekstrem pada filter ini."


def volume_tip_contrast_sentence(zone_df: pd.DataFrame) -> str | None:
    if zone_df is None or zone_df.empty:
        return None
    if 'trip_count' in zone_df.columns:
        count_column = 'trip_count'
    elif 'trips' in zone_df.columns:
        count_column = 'trips'
    else:
        return None
    if 'avg_tip_rate' not in zone_df.columns:
        return None

    top = zone_df.sort_values(count_column, ascending=False).iloc[0]
    median_tip = zone_df['avg_tip_rate'].median()
    zone_name = top.get('zone_name', top.get('pickup_zone', 'zona tidak diketahui'))
    if top['avg_tip_rate'] < median_tip:
        return (
            f"Zona ber-volume tertinggi ({zone_name}) memiliki tip rata-rata {top['avg_tip_rate']:.2f}% di bawah median kota ({median_tip:.2f}%), "
            "mengindikasikan volume tinggi tidak selalu sejalan dengan tipping." 
        )
    if top['avg_tip_rate'] > median_tip:
        return (
            f"Zona ber-volume tertinggi ({zone_name}) juga mencatat tip di atas median kota ({top['avg_tip_rate']:.2f}% vs {median_tip:.2f}%), "
            "mengindikasikan volume tinggi berjalan bersama tipping yang kuat."
        )
    return None


def hourly_spread_sentence(hourly_df: pd.DataFrame) -> str | None:
    if hourly_df is None or hourly_df.empty or 'trips' not in hourly_df.columns:
        return None
    peak = hourly_df.sort_values('trips', ascending=False).iloc[0]
    trough = hourly_df.sort_values('trips', ascending=True).iloc[0]
    if peak['trips'] == 0:
        return None
    ratio = (trough['trips'] / peak['trips']) * 100
    return (
        f"Aktivitas terendah terjadi sekitar pukul {int(trough['pickup_hour']):02d}:00 dengan {int(trough['trips']):,} perjalanan, "
        f"sekitar {ratio:.1f}% dari puncak harian."
    )


def weather_tip_contrast_sentence(tip_df: pd.DataFrame) -> str | None:
    if tip_df is None or tip_df.empty or 'avg_tip_rate' not in tip_df.columns:
        return None
    top = tip_df.sort_values('avg_tip_rate', ascending=False).iloc[0]
    bottom = tip_df.sort_values('avg_tip_rate', ascending=True).iloc[0]
    return (
        f"Tip tertinggi muncul pada {top['weather_category']} (~{top['avg_tip_rate']:.2f}%), "
        f"sedangkan terendah pada {bottom['weather_category']} (~{bottom['avg_tip_rate']:.2f}%), menunjukkan kontras perilaku tipping antar kondisi cuaca."
    )


def segment_contrast_sentence(summary_df: pd.DataFrame) -> str | None:
    if summary_df is None or summary_df.empty:
        return None
    required = ['avg_trip_distance', 'avg_trip_duration_min', 'avg_tip_rate_pct']
    if not all(col in summary_df.columns for col in required):
        return None

    distance_min = summary_df['avg_trip_distance'].min()
    distance_max = summary_df['avg_trip_distance'].max()
    tip_min = summary_df['avg_tip_rate_pct'].min()
    tip_max = summary_df['avg_tip_rate_pct'].max()
    duration_min = summary_df['avg_trip_duration_min'].min()
    duration_max = summary_df['avg_trip_duration_min'].max()

    return (
        f"Rentang antar segmen cukup lebar: jarak rata-rata {distance_min:.2f}-{distance_max:.2f} mil, "
        f"durasi {duration_min:.1f}-{duration_max:.1f} menit, dan tip {tip_min:.1f}%-{tip_max:.1f}%."
    )


def segment_profile_sentence(profile_row: pd.Series) -> str:
    if profile_row is None or profile_row.empty:
        return "Profil segmen belum tersedia."

    segment_name = profile_row.get("customer_segment", "Segmen tidak diketahui")
    display_name = SEGMENT_DISPLAY_NAMES.get(segment_name, segment_name)
    trips = int(profile_row.get("trips", 0))
    distance = float(profile_row.get("avg_trip_distance", 0) or 0)
    duration = float(profile_row.get("avg_trip_duration_min", 0) or 0)
    tip = float(profile_row.get("avg_tip_rate_pct", 0) or 0)
    speed = float(profile_row.get("avg_speed_mph", 0) or 0)
    rush_ratio = float(profile_row.get("rush_hour_ratio", 0) or 0)
    weekend_ratio = float(profile_row.get("weekend_ratio", 0) or 0)

    if distance >= 8 and tip <= 8:
        behavior = "cenderung menunjukkan mobilitas jarak jauh dengan tip yang relatif rendah, konsisten dengan pola perjalanan lintas zona yang lebih fungsional daripada rekreasional."
    elif distance <= 2 and tip >= 18:
        behavior = "didominasi perjalanan urban jarak pendek dengan tip yang tinggi, mengindikasikan mobilitas bernilai tinggi di area inti kota."
    elif weekend_ratio >= 0.30:
        behavior = "lebih kuat pada akhir pekan, sehingga mengarah pada pola rekreasional atau aktivitas yang tidak sepenuhnya komuter."
    elif rush_ratio >= 0.25:
        behavior = "terkonsentrasi pada jam sibuk, sehingga lebih dekat ke perilaku komuter atau mobilitas rutin harian."
    else:
        behavior = "menunjukkan pola campuran yang tidak terlalu terpusat pada satu konteks waktu tertentu."

    return (
        f"{display_name} mencakup {trips:,} perjalanan dengan jarak rata-rata {distance:.2f} mil, durasi {duration:.2f} menit, "
        f"tip {tip:.2f}%, dan kecepatan {speed:.2f} mph; segmen ini {behavior}"
    )


def segment_mix_sentence(borough_df: pd.DataFrame) -> str:
    if borough_df is None or borough_df.empty:
        return "Komposisi borough per segmen belum tersedia."
    row = borough_df.sort_values("trips", ascending=False).iloc[0]
    borough = row.get("pickup_borough", "borough tidak diketahui")
    share = row["trips"] / borough_df["trips"].sum() * 100 if borough_df["trips"].sum() else 0
    return f"Segmen ini paling kuat terkait dengan {borough} yang menyumbang {share:.1f}% dari perjalanan pada subset yang ditampilkan."


def segment_weather_sentence(weather_df: pd.DataFrame) -> str:
    if weather_df is None or weather_df.empty:
        return "Sensitivitas cuaca per segmen belum tersedia."
    row = weather_df.sort_values("trips", ascending=False).iloc[0]
    segment_name = SEGMENT_DISPLAY_NAMES.get(row.get("customer_segment", ""), row.get("customer_segment", "segmen tidak diketahui"))
    return (
        f"{segment_name} paling sering muncul pada kondisi {row.get('weather_category', 'cuaca tidak diketahui')} "
        f"dengan {int(row['trips']):,} perjalanan dan tip rata-rata {row.get('avg_tip_rate_pct', 0):.2f}%."
    )
