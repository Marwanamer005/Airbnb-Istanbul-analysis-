"""Smart Istanbul Trip Planner: pick the sights, get the 5 best Airbnb stays and a day-by-day route.

Run from the repo root:  streamlit run app/streamlit_app.py
(the notebooks must have been run first: they write data/processed/listings_priced.parquet and models/*.joblib)
"""
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent

st.set_page_config(page_title="Smart Istanbul Trip Planner", page_icon=str(HERE / "assets" / "logo512.png"), layout="wide")
st.logo(str(HERE / "assets" / "logo.svg"), size="large")

page = st.navigation(
    [
        st.Page(HERE / "app_pages" / "plan.py", title="Plan my trip", icon=":material/map:", default=True),
        st.Page(HERE / "app_pages" / "explore.py", title="Explore stays", icon=":material/travel_explore:"),
        st.Page(HERE / "app_pages" / "how_it_works.py", title="How it works", icon=":material/insights:"),
    ],
    position="top",
)
page.run()
