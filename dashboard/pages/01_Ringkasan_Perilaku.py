from __future__ import annotations

import streamlit as st

from components.filters import render_sidebar_filters
from page_content.overview import render


def main() -> None:
    st.set_page_config(page_title="Ringkasan Perilaku", layout="wide")
    filters = render_sidebar_filters()
    render(filters)


main()