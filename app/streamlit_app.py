"""Streamlit entry point. Run: uv run streamlit run app/streamlit_app.py"""

import streamlit as st

import aoi_budget

st.set_page_config(page_title="AOI Budget Tool", layout="centered")
st.title("AOI Budget Tool")
st.caption(f"Public-data prototype, v{aoi_budget.__version__}")
st.info("Estimator coming in v0. Public-data estimate; AOI pricing will replace these assumptions.")
