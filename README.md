# NYC Taxi Customer Behavior Segmentation
**Kelompok 1 | MK Rekayasa Data dan Visualisasi | Universitas Brawijaya FILKOM**

Analisis pola perilaku penumpang NYC Yellow Taxi (Sept 2025 – Jan 2026) menggunakan clustering dan visualisasi geospatial.

---

## Struktur Project

```
RDV/
├── TODO.md                          ← status pengerjaan & penjelasan output DE
├── data_engineer/                   ← pipeline data (DE1 & DE2)
├── ml_engineer/                     ← clustering (ML Engineer)
└── dashboard/                       ← visualisasi Streamlit (Data Analyst)
```

---

## 1. Data Engineer — Jalankan Pipeline

> Kerjakan ini pertama. Output-nya dipakai oleh ML Engineer dan Data Analyst.

```bash
cd data_engineer
pip install -r requirements.txt
python pipeline.py
```

Pipeline otomatis mengambil data dari internet dan menghasilkan file siap pakai. Tidak perlu download manual.

**Output utama yang dihasilkan:**
- `data_engineer/data/intermediate/fact_trips.parquet` — 14.5 juta baris data perjalanan
- `data_engineer/data/raw/zones/taxi_zones.geojson` — polygon zona NYC untuk peta

Lihat `TODO.md` untuk penjelasan lengkap semua yang sudah dibuat DE.

**Opsional — lihat visualisasi eksplorasi:**
```bash
cd data_engineer
python explore_viz.py    # → explore_viz.png  (chart statistik)
python explore_map.py    # → explore_map.html (peta interaktif, buka di browser)
```

---

## 2. ML Engineer — Clustering

Gunakan `data_engineer/data/intermediate/fact_trips.parquet` sebagai input.

Simpan hasil ke:
- `data_engineer/data/intermediate/fact_trips_clustered.parquet` (tambahkan kolom `cluster_label`)
- `data_engineer/data/intermediate/cluster_names.json` (nama deskriptif tiap cluster)

Fitur yang direkomendasikan untuk clustering:
```
trip_distance, trip_duration_min, tip_rate_pct, avg_speed_mph,
pickup_hour, is_rush_hour, is_weekend
```

---

## 3. Data Analyst — Dashboard

```bash
pip install streamlit folium streamlit-folium plotly duckdb
streamlit run dashboard/dashboard.py
```

File yang dibutuhkan:
- `data_engineer/data/intermediate/fact_trips_clustered.parquet`
- `data_engineer/data/raw/zones/taxi_zones.geojson`
- `data_engineer/data/intermediate/dim_zones.parquet`

---

## Tim

| Role | Nama |
|---|---|
| Data Engineer 1 | A. Agung Ngurah A.W |
| Data Engineer 2 | A. Agung Ngurah Bayu W.P |
| ML Engineer 1 | Harry Phalosa Telaumbanua |
| Project Lead & ML Engineer 2 | Akwila Febryan Santoso |
| Data Analyst / Visualisasi | Made Deva Wikananda Putra |
