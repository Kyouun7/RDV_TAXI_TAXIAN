# TODO — NYC Taxi Customer Behavior Segmentation
**Kelompok 1 | MK Rekayasa Data dan Visualisasi | Universitas Brawijaya FILKOM**

---

## Status Pengerjaan

| Role | PIC | Status |
|---|---|---|
| **Data Engineer 1 & 2** | **A. Agung Ngurah A.W & A. Agung Ngurah Bayu W.P** | **✅ Selesai** |
| ML Engineer 1 | Harry Phalosa Telaumbanua | 🔲 Belum |
| Project Lead & ML Engineer 2 | Akwila Febryan Santoso | 🔲 Belum |
| Data Analyst / Visualisasi | Made Deva Wikananda Putra | 🔲 Belum |

---

## ✅ Yang Sudah Dibuat — Data Engineer

### Cara Menjalankan Pipeline

```bash
cd data_engineer
pip install -r requirements.txt
python pipeline.py
```

Pipeline berjalan otomatis dari tahap 1 sampai 5. **Tidak perlu download data manual** — data diambil langsung dari internet saat pipeline berjalan.

---

### Yang Sudah Dibuat

#### [1] Data Ingestion
Membaca data Yellow Taxi **langsung dari URL NYC TLC** menggunakan DuckDB httpfs. Data 5 bulan (Sept 2025 – Jan 2026) disimpan per bulan.

**Output:** `data_engineer/data/raw/tlc/`
```
yellow_tripdata_2025-09.parquet   78 MB   4,251,015 baris
yellow_tripdata_2025-10.parquet   81 MB   4,428,699 baris
yellow_tripdata_2025-11.parquet   77 MB   4,181,444 baris
yellow_tripdata_2025-12.parquet   80 MB   4,305,006 baris
yellow_tripdata_2026-01.parquet   69 MB   3,724,889 baris
─────────────────────────────────────────────────────────
Total                            385 MB  20,891,053 baris
```

#### [2] Zone Ingestion
Download taxi zone lookup CSV (265 zona NYC) dan konversi shapefile ke GeoJSON untuk kebutuhan peta.

**Output:** `data_engineer/data/raw/zones/`
```
taxi_zone_lookup.csv    mapping LocationID → nama zona & borough
taxi_zones.geojson      polygon batas zona NYC (untuk peta dashboard)
```

#### [3] Data Cleaning
Membaca semua 5 file monthly, menghapus baris anomali.

| Yang Dihapus | Alasan |
|---|---|
| Nilai null pada kolom kritis | Data tidak lengkap |
| `fare_amount <= 0` | Tarif tidak mungkin nol/negatif |
| `trip_distance <= 0` | Jarak tidak mungkin nol/negatif |
| `tip_amount < 0` | Tip tidak mungkin negatif |
| `passenger_count = 0` atau `> 6` | Di luar kapasitas taxi NYC |
| Dropoff sebelum pickup | Tidak mungkin secara logika |
| Durasi > 5 jam | Tidak realistis untuk NYC |
| Jarak > 100 mil | Tidak realistis untuk NYC |
| LocationID di luar 1–263 | Di luar zona resmi TLC |

**Hasil:** 20,891,053 → **14,558,244 baris** (30.3% dihapus)
**Output:** `data_engineer/data/intermediate/tlc_cleaned.parquet`

#### [4] Feature Engineering
Menambahkan kolom turunan dan mendekode LocationID menjadi nama zona.

**Kolom baru yang ditambahkan:**

| Kolom | Tipe | Keterangan |
|---|---|---|
| `trip_id` | INTEGER | Primary key unik |
| `trip_duration_min` | DOUBLE | Durasi perjalanan (menit) |
| `tip_rate_pct` | DOUBLE | Tip sebagai % dari fare |
| `avg_speed_mph` | DOUBLE | Kecepatan rata-rata |
| `pickup_hour` | INTEGER | Jam pickup (0–23) |
| `pickup_day_of_week` | INTEGER | Hari (0=Minggu, 6=Sabtu) |
| `pickup_month` | INTEGER | Bulan |
| `time_of_day` | VARCHAR | `morning` / `afternoon` / `evening` / `night` |
| `is_rush_hour` | BOOLEAN | True jika jam 07–09 atau 17–19 hari kerja |
| `is_weekend` | BOOLEAN | True jika Sabtu/Minggu |
| `pickup_hour_key` | TIMESTAMP | Waktu pickup dibulatkan ke jam |
| `pickup_zone` | VARCHAR | Nama zona pickup (ex: "Times Sq/Theatre District") |
| `pickup_borough` | VARCHAR | Borough pickup |
| `pickup_service_zone` | VARCHAR | Yellow Zone / Boro Zone / Airports |
| `dropoff_zone` | VARCHAR | Nama zona tujuan |
| `dropoff_borough` | VARCHAR | Borough tujuan |

**Output:** `data_engineer/data/intermediate/tlc_transformed.parquet`

#### [5] Data Modelling (Star Schema)
Membuat dua tabel final siap pakai.

**`dim_zones.parquet`** — 265 baris

| Kolom | Keterangan |
|---|---|
| `zone_id` | LocationID (1–265) |
| `zone_name` | Nama zona |
| `borough` | Borough |
| `service_zone` | Tipe zona |

**`fact_trips.parquet`** — 14,558,244 baris, 26 kolom
Berisi semua kolom asli TLC + semua kolom feature engineering di atas.

**Output:** `data_engineer/data/intermediate/fact_trips.parquet` ← **FILE UTAMA**

#### [6] Visualisasi Eksplorasi
Dua file eksplorasi dari data nyata sebagai referensi untuk tim lain.

**`explore_viz.png`** — chart statistik (generate ulang: `python explore_viz.py`)
- Trip volume per jam, proporsi per borough, top 10 zona
- Distribusi tip rate, perbandingan rush hour vs non-rush hour

**`explore_map.html`** — peta interaktif (generate ulang: `python explore_map.py`)
- Choropleth trip volume per zona (hover = nama zona, klik = detail statistik)
- Toggle ke avg tip rate per zona
- Buka file ini di browser

---

### Semua File Output yang Tersedia untuk Tim

| File | Lokasi | Ukuran | Untuk Siapa |
|---|---|---|---|
| `fact_trips.parquet` | `data_engineer/data/intermediate/` | 410 MB | ML Engineer & Data Analyst |
| `dim_zones.parquet` | `data_engineer/data/intermediate/` | < 1 MB | Data Analyst |
| `taxi_zones.geojson` | `data_engineer/data/raw/zones/` | 5 MB | Data Analyst (peta) |
| `taxi_zone_lookup.csv` | `data_engineer/data/raw/zones/` | < 1 MB | Referensi zona |
| `explore_map.html` | `data_engineer/` | — | Referensi tampilan peta |
| `explore_viz.png` | `data_engineer/` | — | Referensi chart statistik |

> **Catatan:** File `.parquet` di `data/raw/tlc/` dan `data/intermediate/` tidak di-commit ke repo karena ukurannya besar. Jalankan `python pipeline.py` untuk generate ulang semua file tersebut.

---

## Insight Awal dari Data

Hasil eksplorasi `fact_trips.parquet` yang bisa jadi acuan:

- **Manhattan mendominasi** — lebih dari 87% perjalanan pickup dari Manhattan
- **Jam tersibuk** — 18:00–19:00 (evening rush)
- **Top pickup zones** — Upper East Side, JFK Airport, Midtown Center
- **Tip rate** — mayoritas 20–30%, distribusi right-skewed
- **EWR (Newark Airport)** — tip rate tertinggi ~38% meski volume kecil
- **Rush hour** — meningkatkan durasi tapi tidak signifikan mengubah tip rate

---

*Data Engineer: A. Agung Ngurah A.W (DE1) & A. Agung Ngurah Bayu W.P (DE2)*
