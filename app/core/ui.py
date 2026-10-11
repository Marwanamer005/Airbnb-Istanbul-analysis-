"""Small widgets shared by the data pages."""
import streamlit as st

from core.data import load_rates


def currency_picker() -> tuple[str, dict]:
    """One currency choice for every page, kept in session state."""
    rates, info = load_rates()
    cur = st.segmented_control("Show prices in", list(rates), default=st.session_state.get("cur", "USD"), key="cur_pick")
    st.session_state.cur = cur or "USD"
    return st.session_state.cur, rates
