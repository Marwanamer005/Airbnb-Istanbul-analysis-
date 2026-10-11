"""The planner: the full-screen map from the design, filled with the real listings and model outputs."""
import streamlit as st

from core.planner_html import build_planner

version = build_planner()

# the map is the whole page: drop the page padding and let the planner fill the window under the menu
st.html("""<style>
  .stMainBlockContainer{padding:3.75rem 0 0 !important;max-width:100% !important}
  .stMain{overflow:hidden}
  .stElementContainer:has(iframe[title="Trip planner map"]){height:auto !important}
  iframe[title="Trip planner map"]{height:calc(100vh - 3.75rem) !important;border:0;display:block}
</style>""")
st.iframe(f"/app/static/planner.html?v={version}", height=860, alt="Trip planner map")
