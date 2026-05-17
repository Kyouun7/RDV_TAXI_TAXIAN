# Data Engineer Pipeline
**NYC Taxi Customer Behavior Segmentation — Kelompok 1**

Pipeline ini membaca data NYC Yellow Taxi langsung dari URL, membersihkan, mentransformasi, dan menyimpan data yang siap digunakan untuk analisis dan machine learning.

---

## Cara Menjalankan

### 1. Install Dependencies (sekali saja)
```bash
pip install -r requirements.txt
```

### 2. Jalankan Pipeline (satu perintah)
```bash
python pipeline.py
```

Pipeline berjalan otomatis dari awal sampai akhir. Tidak perlu download data manual.

---

## Apa yang Terjadi Saat Pipeline Berjalan

```
[1]  INGEST    Baca 5 bulan data Yellow Taxi langsung dari URL NYC TLC
[1b] ZONES     Download zona lookup + shapefile/GeoJSON untuk peta
[2]  CLEAN     Hapus anomali data (null, tarif negatif, koordinat invalid)
[3]  TRANSFORM Tambah kolom turunan + decode nama zona
[4]  BLEND     Gabung dengan data cuaca (opsional, skip jika tidak ada)
[5]  MODEL     Buat tabel dim_zones + fact_trips (star schema)
```

Output pipeline terlihat seperti ini:
```
[DONE] yellow_tripdata_2025-09.parquet — 4,251,015 rows, 78.0 MB
[DONE] yellow_tripdata_2025-10.parquet — 4,428,699 rows, 81.3 MB
[DONE] yellow_tripdata_2025-11.parquet — 4,181,444 rows, 77.0 MB
[DONE] yellow_tripdata_2025-12.parquet — 4,305,006 rows, 79.7 MB
[DONE] yellow_tripdata_2026-01.parquet — 3,724,889 rows, 68.8 MB
[INFO] Clean row count: 14,558,244 (removed 30.3% anomalies)
[DONE] fact_trips: 14,558,244 rows saved.
```

---

## Struktur Output

```
data/
├── raw/
│   ├── tlc/                             ← data mentah per bulan
│   │   ├── yellow_tripdata_2025-09.parquet   (78 MB)
│   │   ├── yellow_tripdata_2025-10.parquet   (81 MB)
│   │   ├── yellow_tripdata_2025-11.parquet   (77 MB)
│   │   ├── yellow_tripdata_2025-12.parquet   (80 MB)
│   │   └── yellow_tripdata_2026-01.parquet   (69 MB)
│   └── zones/
│       ├── taxi_zone_lookup.csv              (265 zona NYC)
│       └── taxi_zones.geojson                ← untuk peta dashboard
└── intermediate/
    ├── tlc_cleaned.parquet      (267 MB) ← setelah cleaning
    ├── tlc_transformed.parquet  (380 MB) ← setelah feature engineering
    ├── dim_zones.parquet                 ← tabel dimensi zona
    └── fact_trips.parquet       (410 MB) ← TABEL UTAMA, siap pakai
```

> **File yang dibutuhkan tim lain: `fact_trips.parquet` dan `taxi_zones.geojson`**

---

## Kolom di fact_trips.parquet

| Kolom | Tipe | Keterangan |
|---|---|---|
| `trip_id` | BIGINT | Primary key |
| `pickup_location_id` | INTEGER | ID zona penjemputan (FK ke dim_zones) |
| `dropoff_location_id` | INTEGER | ID zona tujuan |
| `pickup_datetime` | TIMESTAMP | Waktu penjemputan |
| `dropoff_datetime` | TIMESTAMP | Waktu tiba |
| `pickup_hour_key` | TIMESTAMP | Dibulatkan ke jam (untuk join cuaca) |
| `passenger_count` | INTEGER | Jumlah penumpang |
| `trip_distance` | DOUBLE | Jarak perjalanan (mil) |
| `trip_duration_min` | DOUBLE | **Durasi perjalanan (menit)** |
| `avg_speed_mph` | DOUBLE | **Kecepatan rata-rata (mph)** |
| `fare_amount` | DOUBLE | Tarif dasar |
| `tip_amount` | DOUBLE | Tip |
| `total_amount` | DOUBLE | Total bayar |
| `tip_rate_pct` | DOUBLE | **Persentase tip dari tarif** |
| `payment_type` | INTEGER | Metode pembayaran |
| `pickup_hour` | BIGINT | Jam penjemputan (0–23) |
| `pickup_day_of_week` | BIGINT | Hari (0=Minggu, 6=Sabtu) |
| `pickup_month` | BIGINT | Bulan |
| `time_of_day` | VARCHAR | morning/afternoon/evening/night |
| `is_rush_hour` | BOOLEAN | True jika jam sibuk weekday |
| `is_weekend` | BOOLEAN | True jika Sabtu/Minggu |
| `pickup_zone` | VARCHAR | Nama zona penjemputan |
| `pickup_borough` | VARCHAR | Borough penjemputan |
| `pickup_service_zone` | VARCHAR | Yellow Zone / Boro Zone / Airports |
| `dropoff_zone` | VARCHAR | Nama zona tujuan |
| `dropoff_borough` | VARCHAR | Borough tujuan |

---

## Anomali yang Ditangani

| Anomali | Penanganan |
|---|---|
| Nilai null pada kolom kritis | Dihapus |
| `fare_amount <= 0` (tarif negatif/nol) | Dihapus |
| `trip_distance <= 0` | Dihapus |
| `tip_amount < 0` | Dihapus |
| `passenger_count = 0` atau `> 6` | Dihapus |
| Waktu dropoff sebelum pickup | Dihapus |
| Durasi perjalanan > 5 jam | Dihapus |
| Jarak > 100 mil | Dihapus |
| LocationID di luar range 1–263 | Dihapus |
| Data di luar periode Sept 2025 – Jan 2026 | Dihapus |

**Hasil:** 20,891,053 → 14,558,244 baris (30.3% dihapus)

---

## Menjalankan Ulang Pipeline

Jika ingin menjalankan ulang dari awal (misal ada update data):
```bash
# Hapus file raw TLC (akan didownload ulang otomatis)
del data\raw\tlc\*.parquet

# Hapus intermediate (akan dibuat ulang)
del data\intermediate\*.parquet

# Jalankan ulang
python pipeline.py
```

---

## File Eksplorasi

Setelah pipeline selesai, tersedia dua file eksplorasi:

```bash
# Buat chart eksplorasi (bar chart, pie, histogram)
python explore_viz.py
# Output: explore_viz.png

# Buat peta interaktif zona NYC
python explore_map.py
# Output: explore_map.html  ← buka di browser
```

Peta `explore_map.html` menampilkan:
- **Choropleth trip volume** — zona mana yang paling banyak perjalanan
- **Toggle ke tip rate** — zona mana yang memberikan tip tertinggi
- **Klik tiap zona** — detail statistik zona (trip count, avg tip, durasi, kecepatan)

> Catatan: Ini adalah peta eksplorasi dari DE. Peta final dashboard akan menampilkan **cluster label** dari hasil ML engineer.

---

## Untuk ML Engineer

Load `fact_trips.parquet` dan gunakan kolom berikut untuk clustering:

```python
import duckdb

df = duckdb.connect().execute("""
    SELECT
        trip_id,
        trip_distance,
        trip_duration_min,
        tip_rate_pct,
        avg_speed_mph,
        pickup_hour,
        pickup_location_id,
        pickup_zone,
        pickup_borough,
        CASE WHEN is_rush_hour THEN 1 ELSE 0 END AS is_rush_hour,
        CASE WHEN is_weekend THEN 1 ELSE 0 END AS is_weekend
    FROM read_parquet('data/intermediate/fact_trips.parquet')
""").fetchdf()
```

Simpan hasil clustering ke: `data/intermediate/fact_trips_clustered.parquet`
(tambahkan kolom `cluster_label` ke dataframe lalu simpan)

---

## Untuk Data Analyst / Visualisasi

File yang dibutuhkan untuk dashboard Streamlit:

```python
import duckdb
import json

# Data utama (gunakan setelah ML selesai)
df = duckdb.connect().execute("""
    SELECT * FROM read_parquet('data/intermediate/fact_trips_clustered.parquet')
    USING SAMPLE 200000
""").fetchdf()

# GeoJSON untuk peta
with open('data/raw/zones/taxi_zones.geojson') as f:
    geojson = json.load(f)

# Dimensi zona
dim = duckdb.connect().execute("""
    SELECT * FROM read_parquet('data/intermediate/dim_zones.parquet')
""").fetchdf()
```

---

*Data Engineer: A. Agung Ngurah A.W & A. Agung Ngurah Bayu W.P*
*Kelompok 1 | MK Rekayasa Data dan Visualisasi | Universitas Brawijaya FILKOM*
