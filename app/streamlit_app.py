"""Kervan, the Istanbul trip planner: pick the sights, get the 5 best Airbnb stays and a day-by-day route.

Run from the repo root:  streamlit run app/streamlit_app.py
(the notebooks must have been run first: they write data/processed/listings_priced.parquet and models/*.joblib)
"""
from pathlib import Path

import streamlit as st

from core.auth import is_admin, sign_out
from core.usage import record_visit

HERE = Path(__file__).resolve().parent

st.set_page_config(page_title="Kervan · Istanbul trip planner", page_icon=str(HERE / "assets" / "kervan_icon512.png"), layout="wide")
st.logo(str(HERE / "assets" / "kervan_logo.svg"), icon_image=str(HERE / "assets" / "kervan_logo.svg"), size="large")
record_visit()

# Travellers only see the planner. Signing in as admin (on the planner's welcome card) adds the two pages
# for checking the data and the models.
pages = [st.Page(HERE / "app_pages" / "plan.py", title="Plan my trip", icon=":material/map:", default=True)]
if is_admin():
    pages += [st.Page(HERE / "app_pages" / "explore.py", title="Explore stays", icon=":material/travel_explore:"),
              st.Page(HERE / "app_pages" / "how_it_works.py", title="How it works", icon=":material/insights:")]
page = st.navigation(pages, position="top")
if is_admin() and page.title != "Plan my trip":
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Sign out", icon=":material/logout:", key="admin_sign_out"):
            sign_out()
            st.session_state._signed_out = True   # the planner forgets the session when it next loads
            st.switch_page(pages[0])
page.run()
