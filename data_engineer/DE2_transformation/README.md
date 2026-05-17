# DE2 - Transformation, Cleaning & Blending

**PIC:** A. Agung Ngurah Bayu W.P  
**Tanggung jawab:** Membersihkan data mentah, feature engineering, dan menggabungkan data taksi dengan cuaca

## Prasyarat

DE1 harus sudah selesai menjalankan ingestion agar folder `data/raw/` terisi.

## Files

| File | Deskripsi |
|---|---|
| `cleaning.py` | Hapus anomali: missing value, tarif negatif, koordinat tidak valid, durasi tidak masuk akal |
| `feature_engineering.py` | Tambah kolom turunan: durasi perjalanan, tip rate, kecepatan, kategori waktu, rush hour |
| `data_blending.py` | Join data taksi dengan data cuaca berdasarkan jam penjemputan |
| `prefect_flow.py` | Orkestrasi pipeline dengan Prefect (jalankan ketiga tahap berurutan) |

## Cara Jalankan

```bash
# Install dependencies (sekali saja)
pip install -r ../requirements.txt

# Jalankan pipeline transformasi (setelah DE1 selesai)
python prefect_flow.py
```

Atau jalankan satu per satu:

```bash
python cleaning.py
python feature_engineering.py
python data_blending.py
```

## Output

```
data/intermediate/
├── tlc_cleaned.parquet       # Setelah cleaning
├── tlc_transformed.parquet   # Setelah feature engineering
└── tlc_with_weather.parquet  # Final: siap untuk analisis & ML
```

## Anomali yang ditangani (cleaning.py)

| Anomali | Penanganan |
|---|---|
| Kolom kritis null | Hapus baris |
| `fare_amount <= 0` | Hapus baris |
| `trip_distance <= 0` | Hapus baris |
| `tip_amount < 0` | Hapus baris |
| `passenger_count = 0` atau `> 6` | Hapus baris |
| Dropoff sebelum pickup | Hapus baris |
| Durasi > 5 jam | Hapus baris |
| Jarak > 100 mil | Hapus baris |
| LocationID di luar 1-263 | Hapus baris |
| Data di luar periode Sept 2025 - Jan 2026 | Hapus baris |

## Kolom baru yang ditambahkan (feature_engineering.py)

| Kolom | Deskripsi |
|---|---|
| `trip_duration_min` | Durasi perjalanan dalam menit |
| `tip_rate_pct` | Persentase tip dari fare |
| `avg_speed_mph` | Kecepatan rata-rata dalam mph |
| `pickup_hour` | Jam penjemputan (0-23) |
| `pickup_day_of_week` | Hari dalam minggu (0=Minggu, 6=Sabtu) |
| `pickup_month` | Bulan penjemputan |
| `time_of_day` | morning / afternoon / evening / night |
| `is_rush_hour` | True jika jam sibuk weekday |
| `is_weekend` | True jika Sabtu/Minggu |
| `pickup_hour_key` | Timestamp dibulatkan ke jam (untuk join cuaca) |

## Kolom cuaca yang ditambahkan (data_blending.py)

| Kolom | Deskripsi |
|---|---|
| `temperature_2m` | Suhu udara (°C) |
| `precipitation` | Curah hujan (mm) |
| `snowfall` | Salju (cm) |
| `windspeed_10m` | Kecepatan angin (km/h) |
| `weathercode` | Kode cuaca WMO |
| `weather_category` | snow / heavy_rain / light_rain / freezing / clear |
