# Dashboard Ringkas

Folder ini berisi dashboard analitik perilaku pelanggan taksi NYC dengan navigasi multipage native Streamlit.

## Menjalankan

```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

## Struktur

- `app.py` berfungsi sebagai landing page presentasi.
- Folder `pages/` berisi halaman multipage native dengan urutan bernomor.
- Sidebar dipakai untuk filter global, konteks dataset, catatan analitis, dan toggle debug performa.

## Prinsip Desain

- Narasi perilaku pelanggan diutamakan dibanding monitoring taksi umum.
- DuckDB dipakai langsung di atas parquet untuk komputasi berat.
- Yang diteruskan ke Plotly dan Folium hanya hasil agregasi.
- Lapisan segmentasi tetap siap pakai tanpa memalsukan output klaster.

## Halaman

- Ringkasan Perilaku
- Analisis Perilaku Spasial
- Analisis Perilaku Temporal
- Analisis Cuaca dan Perilaku
- Segmentasi Perilaku
