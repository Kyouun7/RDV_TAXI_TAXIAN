import duckdb
import streamlit as st

from config import CACHE_TTL_SECONDS


@st.cache_resource(ttl=CACHE_TTL_SECONDS)
def get_duckdb_connection() -> duckdb.DuckDBPyConnection:
    # In-memory connection is enough because all analytics read directly from parquet files.
    con = duckdb.connect(database=":memory:")
    con.execute("SET threads=4")
    con.execute("SET memory_limit='1GB'")
    con.execute("SET enable_object_cache=true")
    return con
