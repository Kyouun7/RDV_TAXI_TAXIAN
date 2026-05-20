# Dashboard Analitik Perilaku Taksi NYC

Dokumentasi ini menjelaskan dashboard Streamlit untuk analisis perilaku pelanggan taksi NYC. Fokus utama dashboard adalah interpretasi pola mobilitas, perilaku tipping, dan segmentasi berbasis clustering, bukan sekadar monitoring operasional.

---

## Tujuan Dashboard
- Menyediakan ringkasan perilaku mobilitas berbasis zona, waktu, dan cuaca.
- Menjelaskan dinamika tipping pelanggan dalam konteks spasial dan temporal.
- Menerjemahkan hasil clustering menjadi segmen perilaku yang bisa diinterpretasikan secara akademik.

---

## Arsitektur Ringkas
- **Streamlit multipage** untuk alur analisis per topik.
- **DuckDB + Parquet** untuk agregasi cepat tanpa load penuh.
- **Folium + GeoJSON** untuk peta zonal interaktif.
- **Plotly** untuk grafik analitis (distribusi, tren, perbandingan).
- **Caching** untuk menjaga responsivitas peta dan chart.

---

## Struktur Folder
- `app.py` berfungsi sebagai landing page presentasi.
- `pages/` berisi halaman multipage native dengan urutan bernomor.
- `page_content/` menyimpan renderer utama per halaman.
- `queries/` berisi query DuckDB untuk agregasi.
- `components/` berisi komponen peta, chart, dan KPI.
- `utils/` berisi helper caching, data loader, dan insight generator.

---

## Deskripsi Halaman
- **Ringkasan Perilaku:** KPI utama, hotspot, dan ringkasan mobilitas.
- **Analisis Perilaku Spasial:** konsentrasi zona, tipping per zona, dan koridor bandara.
- **Analisis Perilaku Temporal:** ritme harian, jam sibuk, dan pergeseran perilaku.
- **Analisis Cuaca dan Perilaku:** dampak cuaca terhadap volume, durasi, dan tip.
- **Segmentasi Perilaku:** interpretasi segmen pelanggan dari clustering.
- **Segmentasi Sensitivitas Cuaca:** placeholder arah soft-clustering berbasis cuaca.

---

## Cara Menjalankan

```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

---

## Prasyarat Data
- `data_engineer/data/intermediate/fact_trips.parquet`
- `data_engineer/data/intermediate/fact_trips_with_weather.parquet` (untuk halaman cuaca)
- `data_engineer/data/raw/zones/taxi_zones.geojson`
- `data_engineer/data/intermediate/dim_zones.parquet`
- `data_engineer/data/intermediate/segmented_trips_final.parquet` (untuk segmentasi)

---

## Sistem Segmentasi
- **Saat ini:** hard clustering menghasilkan segmen perilaku perjalanan yang dapat diinterpretasikan.
- **Arah berikutnya:** soft / probabilistic clustering untuk sensitivitas cuaca dan keanggotaan segmen bertingkat.
- Fokus utama: explainability dan interpretasi perilaku, bukan jargon ML.

---

## Strategi Performa
- Query agregasi dilakukan langsung di DuckDB untuk menghindari load dataframe besar.
- GeoJSON disederhanakan dan dicache untuk mempercepat rendering peta.
- Mode interaksi peta dipisah agar tetap responsif saat presentasi.

---

## Troubleshooting Singkat
- Halaman segmentasi kosong: pastikan `segmented_trips_final.parquet` tersedia.
- Halaman cuaca kosong: pastikan `fact_trips_with_weather.parquet` tersedia.
