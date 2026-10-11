"""Cached loaders shared by every page: the priced listings, the models and the small JSON files."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "models"
FIGS = ROOT / "reports" / "figures"
PLANNER_DATA = APP / "demo_data"   # map shapes, sights, restaurants and sample trips used by the planner

# scores from the notebooks (02 price model, 04 reliability, 03 segments)
PRICE_MAPE, PRICE_R2, RELIABILITY_AUC = 0.14, 0.751, 0.953


@st.cache_data(show_spinner="Loading Airbnb listings...")
def load_listings() -> pd.DataFrame:
    """Every listing with the outputs of the three models: fair_price, price_gap, reliability, segment_name."""
    return pd.read_parquet(PROCESSED / "listings_priced.parquet")


@st.cache_resource(show_spinner="Loading the price model...")
def load_price_model():
    import joblib
    return joblib.load(MODELS / "price_model.joblib")


@st.cache_data
def load_rates() -> dict:
    """Lira per unit of each currency, from the TCMB bulletin saved in data/raw/rates.json."""
    info = json.loads((RAW / "rates.json").read_text(encoding="utf-8"))
    return {"TRY": 1.0, **info["TRY_per"]}, info


@st.cache_data
def load_sights() -> list:
    return json.loads((PLANNER_DATA / "mon.json").read_text(encoding="utf-8"))


def money(try_amount: float, cur: str, rates: dict) -> str:
    sym = {"TRY": "₺", "USD": "$", "EUR": "€", "GBP": "£"}[cur]
    return f"{sym}{try_amount / rates[cur]:,.0f}"


def deal_label(gap: float) -> str:
    """price_gap is (fair - listed) / fair, so positive means cheaper than the model expects."""
    if np.isnan(gap):
        return "No estimate"
    if gap > 0.03:
        return f"{gap:.0%} below fair price"
    if gap < -0.03:
        return f"{-gap:.0%} above fair price"
    return "About fair price"
