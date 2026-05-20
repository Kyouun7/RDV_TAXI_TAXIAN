from __future__ import annotations

import streamlit as st


def render(filters: dict):
    st.header("Segmentasi Sensitivitas Cuaca")
    st.markdown(
        "Halaman ini adalah placeholder untuk interpretasi segmentasi yang berfokus pada sensitivitas terhadap cuaca."
    )

    st.markdown(
        "Segmentation yang akan datang menggunakan metode soft / probabilistic clustering untuk menangkap probabilitas keanggotaan segmen (mis. seorang perjalanan bisa memiliki 30% kecenderungan menjadi `Rainy Day Trip` dan 70% menjadi `Everyday Standard Trip`)."
    )

    st.markdown("**Apa yang diharapkan dari lapisan ini:**")
    st.markdown(
        "- Menjelaskan bagaimana cuaca (hujan, salju, suhu) mengubah pola mobilitas dan preferensi rute.\n"
        "- Menyediakan interpretasi probabilistik: bukan label tunggal, melainkan distribusi keanggotaan segmen per perjalanan atau zona.\n"
        "- Memberi wawasan operasional untuk penjadwalan dan kesiapan armada pada kondisi cuaca ekstrim."
    )

    st.info(
        "Artefak model untuk lapisan ini belum tersedia. Halaman ini akan diperbarui setelah model soft-clustering dieksekusi oleh tim ML dan artefak Parquet disimpan di folder intermediate."
    )

    st.markdown("**Contoh segmen (bukan data nyata):**")
    st.markdown(
        "- Rainy Day Trip\n- Everyday Standard Trip\n- Group Short Trip\n- Winter Trip\n- Snowy Trip"
    )

    st.caption(
        "Halaman ini bertujuan memberi konteks metodologis dan ekspektasi analitis — tidak memuat hasil yang belum diproduksi oleh pipeline ML."
    )
