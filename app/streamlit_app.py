"""Smart Istanbul Trip Planner: pick monuments, days and budget, get the best Airbnb and a day plan.

Run from the repo root:  streamlit run app/streamlit_app.py
"""
import json
import sys
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.currency import SYMBOLS, fmt, load_rates, to_try  # noqa: E402
from src.planner import build_program  # noqa: E402
from src.recommender import FACTORS, MODES, STAY_TYPES, recommend  # noqa: E402

RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
FIGS = ROOT / "reports" / "figures"

st.set_page_config(page_title="Smart Istanbul Trip Planner", page_icon="🕌", layout="wide")


# ---------- data ----------
@st.cache_data
def load_listings():
    return pd.read_parquet(PROCESSED / "listings_priced.parquet")


@st.cache_data
def load_monuments():
    return pd.read_csv(RAW / "monuments.csv")


@st.cache_data
def load_restaurants():
    rows, seen = [], set()
    for f in ["restaurants_eu.geojson", "restaurants_asia.geojson"]:
        with open(RAW / f, encoding="utf-8") as fh:
            for ft in json.load(fh)["features"]:
                p, g = ft.get("properties", {}), ft.get("geometry") or {}
                if g.get("type") != "Point" or not p.get("name") or p.get("@id") in seen:
                    continue
                seen.add(p.get("@id"))
                lon, lat = g["coordinates"][:2]
                rows.append({"name": p["name"], "cuisine": (p.get("cuisine") or "").replace(";", ", ").replace("_", " "),
                             "kind": p.get("amenity", ""), "lat": lat, "lon": lon})
    return pd.DataFrame(rows)


listings = load_listings()
monuments = load_monuments()
restaurants = load_restaurants()
rates, rates_info = load_rates(RAW / "rates.json")


# ---------- sidebar: the trip ----------
def apply_mode():
    for f, v in MODES[st.session_state.mode].items():
        st.session_state[f"w_{f}"] = v


if "mode" not in st.session_state:
    st.session_state.mode = "Balanced"
    apply_mode()

with st.sidebar:
    st.header("Your trip")
    picks = st.multiselect("Monuments you want to see", monuments["name"].tolist(),
                           default=["Hagia Sophia", "Blue Mosque (Sultan Ahmed)", "Topkapi Palace",
                                    "Grand Bazaar", "Galata Tower", "Istiklal Avenue"])
    c1, c2 = st.columns(2)
    days = c1.number_input("Days", 1, 10, 3)
    guests = c2.number_input("Guests", 1, 12, 2)
    c1, c2 = st.columns([2, 1])
    currency = c2.selectbox("Currency", list(rates), index=list(rates).index("USD") if "USD" in rates else 0)
    budget = c1.number_input(f"Max per night ({SYMBOLS[currency]})", min_value=1,
                             value=150 if currency != "TRY" else 7000, step=10 if currency != "TRY" else 250)
    stay_types = st.multiselect("Stay type", STAY_TYPES, default=["Entire home"])

    st.subheader("What matters most?")
    st.radio("Trip priority", list(MODES), key="mode", horizontal=True, on_change=apply_mode,
             label_visibility="collapsed")
    with st.expander("Fine-tune the weights"):
        for f in FACTORS:
            st.slider(f, 0, 100, key=f"w_{f}")
    raw_w = {f: st.session_state[f"w_{f}"] for f in FACTORS}
    total = sum(raw_w.values()) or 1
    weights = {f: v / total * 100 for f, v in raw_w.items()}
    st.caption("Weights (always add up to 100%)")
    st.bar_chart(pd.DataFrame({"weight %": weights}), horizontal=True, height=200)

budget_try = to_try(budget, currency, rates)
chosen = monuments[monuments["name"].isin(picks)]


# ---------- recommend ----------
top, n_candidates = recommend(listings, chosen, stay_types, guests, days, budget_try, weights)

st.title("Smart Istanbul Trip Planner")
st.caption(f"{len(listings):,} Istanbul Airbnb listings (Inside Airbnb, Sept 2026) · fair prices from our "
           f"XGBoost model · rates as of {rates_info['date']}")

tab_stays, tab_trip, tab_insights = st.tabs(["🏠 Best stays", "🗺️ Trip program", "📊 How it works"])


def listing_card(rank, r):
    gap = r["price_gap"]
    tag = f":green[{gap:.0%} below fair]" if gap > 0.02 else (f":red[{-gap:.0%} above fair]" if gap < -0.02 else "about fair")
    with st.container(border=True):
        a, b = st.columns([4, 1])
        a.markdown(f"**{rank}. [{r['name']}](https://www.airbnb.com/rooms/{int(r['id'])})**")
        b.markdown(f"### {r['score']:.0f}")
        st.caption(f"{r['stay_type']} · {r['neighbourhood_cleansed']} · up to {int(r['accommodates'])} guests"
                   f"{' · Superhost' if r['is_superhost'] else ''}"
                   f"{' · ' + r['segment_name'] if 'segment_name' in r and pd.notna(r.get('segment_name')) else ''}")
        st.markdown(f"{fmt(r['price'], currency, rates)} / night · {tag} (fair ≈ {fmt(r['fair_price'], currency, rates)})")
        st.caption(f"{days} nights: {fmt(r['price'] * days, currency, rates)}")
        cols = st.columns(len(FACTORS))
        for col, f in zip(cols, FACTORS):
            col.caption(f)
            col.progress(float(min(max(r[f"f_{f}"], 0), 1)))
        st.markdown(f"*{r['why']}*")


def stays_map(top, chosen, height=480):
    layers = [
        pdk.Layer("ScatterplotLayer", chosen, get_position="[lon, lat]", get_radius=120,
                  get_fill_color=[30, 90, 160, 220], pickable=True),
        pdk.Layer("ScatterplotLayer", top.assign(rank=range(1, len(top) + 1)),
                  get_position="[longitude, latitude]", get_radius=160,
                  get_fill_color=[220, 70, 50, 240], pickable=True),
        pdk.Layer("TextLayer", top.assign(rank=[str(i) for i in range(1, len(top) + 1)]),
                  get_position="[longitude, latitude]", get_text="rank", get_size=14,
                  get_color=[255, 255, 255], get_alignment_baseline="'center'"),
    ]
    pts = pd.concat([chosen[["lat", "lon"]],
                     top[["latitude", "longitude"]].rename(columns={"latitude": "lat", "longitude": "lon"})])
    view = pdk.ViewState(latitude=pts["lat"].mean(), longitude=pts["lon"].mean(), zoom=12 if len(pts) else 10)
    st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=view, map_style=None,
                             tooltip={"text": "{name}"}), height=height)


with tab_stays:
    if top.empty:
        st.warning("No stay matches all your rules. Try a higher budget, fewer guests, more stay types, "
                   "or more days (some listings need a minimum stay).")
    else:
        st.markdown(f"**{n_candidates:,}** listings fit your trip. Here are the 5 best for "
                    f"**{st.session_state.mode if raw_w == MODES[st.session_state.mode] else 'your custom weights'}**.")
        left, right = st.columns([1.1, 1])
        with left:
            stays_map(top, chosen)
            st.caption("🔵 your monuments · 🔴 recommended stays (numbers = rank)")
        with right:
            for i, (_, r) in enumerate(top.iterrows(), start=1):
                listing_card(i, r)


with tab_trip:
    if top.empty or chosen.empty:
        st.info("Pick at least one monument and make sure a stay matches to see the program.")
    else:
        options = {f"{i}. {r['name']}": r for i, (_, r) in enumerate(top.iterrows(), start=1)}
        pick = st.selectbox("Plan around this stay", list(options))
        stay = options[pick]
        plan = build_program(chosen, int(days), stay["latitude"], stay["longitude"], restaurants)
        st.caption("Monuments are grouped into days with K-Means on their location, then ordered by walking "
                   "distance starting from your stay. Restaurants come from OpenStreetMap (no ratings).")

        colors = [[220, 70, 50], [30, 120, 180], [40, 160, 90], [200, 140, 20], [140, 70, 170],
                  [20, 160, 160], [180, 60, 120], [90, 90, 90], [150, 110, 60], [60, 60, 180]]
        layers, fees = [], 0.0
        cols = st.columns(min(int(days), 4))
        for i, d in enumerate(plan):
            with cols[i % len(cols)]:
                with st.container(border=True):
                    st.markdown(f"#### Day {d['day']}")
                    if d["stops"].empty:
                        st.caption("Free day: add more monuments to fill it, or explore the neighbourhood.")
                        continue
                    for j, s in enumerate(d["stops"].itertuples(), start=1):
                        closed = f" · ⚠️ closed {s.closed_day}" if isinstance(s.closed_day, str) and s.closed_day else ""
                        fee = "free" if not s.entry_fee_try else fmt(s.entry_fee_try, currency, rates)
                        st.markdown(f"{j}. **{s.name}**  \n<small>{s.visit_minutes} min · {fee} · "
                                    f"{s.leg_m / 1000:.1f} km from previous stop{closed}</small>",
                                    unsafe_allow_html=True)
                    st.caption(f"≈ {d['minutes'] / 60:.1f} h of visits · tickets {fmt(d['fees'], currency, rates)}")
                    if not d["restaurants"].empty:
                        st.markdown("**Eat nearby**")
                        for r in d["restaurants"].itertuples():
                            st.markdown(f"<small>🍽️ {r.name}{' · ' + r.cuisine if r.cuisine else ''} · "
                                        f"{r.dist_m:.0f} m</small>", unsafe_allow_html=True)
                fees += d["fees"]
                path = [[stay["longitude"], stay["latitude"]]] + d["stops"][["lon", "lat"]].values.tolist()
                layers.append(pdk.Layer("PathLayer", [{"path": path}], get_path="path", get_width=6,
                                        width_min_pixels=3, get_color=colors[i % len(colors)]))
                layers.append(pdk.Layer("ScatterplotLayer", d["stops"], get_position="[lon, lat]",
                                        get_radius=90, get_fill_color=colors[i % len(colors)], pickable=True))

        layers.append(pdk.Layer("ScatterplotLayer", pd.DataFrame([stay]), get_position="[longitude, latitude]",
                                get_radius=150, get_fill_color=[0, 0, 0], pickable=True))
        st.pydeck_chart(pdk.Deck(layers=layers, map_style=None, tooltip={"text": "{name}"},
                                 initial_view_state=pdk.ViewState(latitude=chosen["lat"].mean(),
                                                                  longitude=chosen["lon"].mean(), zoom=12)),
                        height=420)
        stay_total = stay["price"] * days
        st.subheader(f"Trip total: {fmt(stay_total + fees * guests, currency, rates)}")
        st.caption(f"Stay {fmt(stay_total, currency, rates)} + tickets {fmt(fees, currency, rates)} × {guests} "
                   f"guest(s). Ticket prices are estimates.")


with tab_insights:
    st.markdown("### How the planner works")
    st.markdown(
        "1. **Fair price (regression):** an XGBoost model trained on 16k listings predicts what each listing "
        "*should* cost from its size, amenities and location. The gap to the real price is the **Deal** score.\n"
        "2. **Our neural network:** a Keras MLP with a learned district embedding, compared against the trees.\n"
        "3. **Segments (clustering):** K-Means groups listings into 6 market segments without using price.\n"
        "4. **Reliability (classification):** for the 35% of listings with no reviews, a classifier estimates "
        "whether the listing is active. It feeds the **Trust** score.\n"
        "5. **Day plan (clustering):** K-Means groups your monuments into days.")
    figs = [("model_comparison.png", "Model comparison (test set)"), ("cv_comparison.png", "5-fold cross-validation"),
            ("predicted_vs_actual.png", "Predicted vs actual price"), ("shap_summary.png", "What drives price (SHAP)"),
            ("district_embeddings.png", "District embeddings learned by our MLP"),
            ("segments.png", "Listing segments"), ("reliability_roc.png", "Reliability classifier ROC"),
            ("price_map.png", "Where the expensive listings are")]
    shown = [(f, t) for f, t in figs if (FIGS / f).exists()]
    for i in range(0, len(shown), 2):
        cols = st.columns(2)
        for col, (f, t) in zip(cols, shown[i:i + 2]):
            col.markdown(f"**{t}**")
            col.image(str(FIGS / f), width="stretch")
    if "segment_name" in listings:
        st.markdown("### Segments")
        seg = listings.groupby("segment_name").agg(listings=("id", "size"), median_price=("price", "median"),
                                                   km_to_sultanahmet=("dist_sultanahmet_m", lambda s: s.median() / 1000))
        st.dataframe(seg.sort_values("median_price").round(1), width="stretch")
