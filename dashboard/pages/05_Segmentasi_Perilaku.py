from __future__ import annotations

import streamlit as st

from components.filters import render_sidebar_filters
from page_content.segmentation_placeholder import render


def main() -> None:
    st.set_page_config(page_title="Segmentasi Perilaku", layout="wide")
    filters = render_sidebar_filters()
    render(filters)


main()