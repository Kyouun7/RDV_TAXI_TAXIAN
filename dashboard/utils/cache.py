import streamlit as st

from config import CACHE_MAX_ENTRIES, CACHE_TTL_SECONDS


def cache_data(func):
    return st.cache_data(ttl=CACHE_TTL_SECONDS, max_entries=CACHE_MAX_ENTRIES)(func)


def cache_resource(func):
    return st.cache_resource(ttl=CACHE_TTL_SECONDS)(func)
