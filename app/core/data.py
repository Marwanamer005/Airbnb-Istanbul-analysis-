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

# scores from the notebooks (02 price model, 04 reliability, 03 segments); price_scores() reads notebook 05's when it has run
PRICE_MAPE, PRICE_R2, RELIABILITY_AUC = 0.14, 0.751, 0.954


@st.cache_data(show_spinner="Loading Airbnb listings...")
def load_listings() -> pd.DataFrame:
    """Every listing with the outputs of the three models: fair_price, price_gap, reliability, segment_name."""
    return pd.read_parquet(PROCESSED / "listings_priced.parquet")


@st.cache_data(show_spinner="Loading monthly stays...")
def load_monthly():
    """Monthly listings (min stay 28+ nights) with the fair price from their own model (notebook 06), or None before 06 has run."""
    path = PROCESSED / "listings_monthly.parquet"
    if not path.exists():
        return None
    df = load_listings()
    m = df[df["is_monthly"] == 1].drop(columns=["fair_price", "price_gap"])
    return m.merge(pd.read_parquet(path), on="id").rename(columns={"fair_price_m": "fair_price", "price_gap_m": "price_gap"})


@st.cache_data
def monthly_scores():
    """Typical error and R² of the monthly price model (notebook 06), or None."""
    path = MODELS / "monthly_scores.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


@st.cache_resource(show_spinner="Loading the price model...")
def load_price_model():
    import joblib
    return joblib.load(MODELS / "price_model.joblib")


@st.cache_resource(show_spinner="Loading the neural network...")
def load_price_stack():
    """The neural network's weights and the stacking meta-model saved by notebook 05 (None before 05 has run)."""
    import joblib
    path = MODELS / "price_stack.joblib"
    return joblib.load(path) if path.exists() else None


def mlp_log_price(stack: dict, X: pd.DataFrame) -> np.ndarray:
    """Runs the Keras price network in plain NumPy: district embedding + features, then Dense layers with ReLU."""
    d2i = {d: i for i, d in enumerate(stack["districts"])}
    dist = X["neighbourhood_cleansed"].map(d2i).fillna(0).astype(int).to_numpy()
    num = np.clip(stack["scaler"].transform(X[stack["num"]]), -5, 5)
    h = np.hstack([stack["emb"][dist], num, stack["onehot"].transform(X[stack["small_cats"]])])
    for k, (W, b) in enumerate(stack["dense"]):
        h = h @ W + b
        if k < len(stack["dense"]) - 1:
            h = np.maximum(h, 0)
    return h.ravel() * stack["y_std"] + stack["y_mean"]


def fair_price_parts(X: pd.DataFrame) -> dict:
    """Fair price per night in lira from each model and the final one the app uses (stacked when notebook 05 says so)."""
    model, stack = load_price_model(), load_price_stack()
    xgb = model.predict(X[list(model.feature_names_in_)])
    out = {"xgb": np.exp(xgb)}
    if stack is not None:
        mlp = mlp_log_price(stack, X)
        a, b = stack["meta_coef"]
        out["mlp"] = np.exp(mlp)
        out["final"] = np.exp(np.clip(a * xgb + b * mlp + stack["meta_intercept"], stack["log_min"], stack["log_max"])) \
            if stack["use_stack"] else out["xgb"]
    else:
        out["final"] = out["xgb"]
    return out


def price_scores() -> tuple[float, float, str]:
    """Typical error, R² and a name for the fair-price model the app uses."""
    stack = load_price_stack()
    if stack is not None and stack["use_stack"]:
        t = stack["test_scores"]["Stacked (XGBoost + MLP)"]
        return t["MedianAPE_%"] / 100, round(t["R2_log"], 3), "XGBoost stacked with our neural network"
    return PRICE_MAPE, PRICE_R2, "tuned XGBoost"


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
