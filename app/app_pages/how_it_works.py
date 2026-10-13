"""How the planner decides: the three models behind it, with a live price checker."""
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from core.data import (FIGS, RELIABILITY_AUC, deal_label, fair_price_parts, load_listings, load_price_model,
                       load_price_stack, monthly_scores, money, price_scores)
from core.auth import account_count
from core.learning import FACTORS, HAND, feedback_stats, learned_weights
from core.ui import currency_picker
from core.usage import visit_stats

df = load_listings()
PRICE_MAPE, PRICE_R2, PRICE_NAME = price_scores()
stack = load_price_stack()

st.title("How it works")
st.write(
    "Behind the map are machine-learning models trained on Inside Airbnb's Istanbul data (snapshot of 25 Sep 2026, "
    f"{len(df):,} listings). They decide which 5 stays you see and why."
)

with st.container(horizontal=True):
    st.metric("Fair-price model, typical error", f"{PRICE_MAPE:.0%}", border=True,
              help=f"{PRICE_NAME}. Median error on held-out listings; R² {PRICE_R2} on log price. Notebooks 02 and 05.")
    st.metric("Active-listing model, AUC", f"{RELIABILITY_AUC}", border=True,
              help="How well it separates listings that were booked in the last year from dead ones. Notebook 04.")
    st.metric("Kinds of stay", df["segment_name"].nunique(), border=True,
              help="K-means clusters, so a hostel bed is never compared with a villa. Notebook 03.")

cur, rates = currency_picker()

# ---------- live price checker ----------
st.header("Check a price")
st.caption("Describe a place and the price model estimates what a fair nightly price would be.")

model = load_price_model()
FEATURES = list(model.feature_names_in_)
AMENITIES = {"Wi-Fi": "has_wifi", "Air conditioning": "has_ac", "Kitchen": "has_kitchen", "Washer": "has_washer",
             "Workspace": "has_workspace", "Self check-in": "has_self_checkin", "Elevator": "has_elevator",
             "Parking": "has_parking", "Balcony": "has_balcony", "Sea view": "has_sea_view",
             "Dishwasher": "has_dishwasher", "TV": "has_tv"}

with st.form("checker", border=True):
    c1, c2, c3 = st.columns(3)
    hood = c1.selectbox("Neighbourhood", sorted(df["neighbourhood_cleansed"].unique()),
                        index=sorted(df["neighbourhood_cleansed"].unique()).index("Beyoglu"))
    stay = c2.selectbox("Type of stay", sorted(df["stay_type"].dropna().unique()))
    room = c3.selectbox("Room", sorted(df["room_type"].dropna().unique()))
    c1, c2, c3 = st.columns(3)
    guests = c1.number_input("Guests", 1, 16, 2)
    beds = c2.number_input("Bedrooms", 0, 10, 1)
    baths = c3.number_input("Bathrooms", 0.0, 8.0, 1.0, step=0.5)
    amen = st.multiselect("Amenities", list(AMENITIES), default=["Wi-Fi", "Air conditioning", "Kitchen", "Washer", "TV"])
    c1, c2 = st.columns(2)
    superhost = c1.toggle("Superhost")
    shared = c2.toggle("Shared bathroom")
    listed = st.number_input(f"Listed price per night in {cur} (optional)", min_value=0, value=0, step=5)
    go = st.form_submit_button("Estimate the fair price", type="primary")

if go:
    group = df[(df["neighbourhood_cleansed"] == hood) & (df["stay_type"] == stay)]
    if len(group) < 20:
        group = df[df["neighbourhood_cleansed"] == hood]
    # start from a typical listing of that kind in that neighbourhood, then apply what the user described
    row = group[FEATURES].median(numeric_only=True).to_frame().T
    row["neighbourhood_cleansed"], row["stay_type"], row["room_type"] = hood, stay, room
    row["accommodates"], row["bedrooms"], row["beds"], row["bathrooms_n"] = guests, beds, max(1, beds), baths
    row["is_shared_bath"], row["is_superhost"] = int(shared), int(superhost)
    for label, col in AMENITIES.items():
        row[col] = int(label in amen)
    parts = fair_price_parts(row)   # each model predicts log price; the app converts back to lira
    fair = float(parts["final"][0])
    lo, hi = fair * (1 - PRICE_MAPE), fair * (1 + PRICE_MAPE)
    with st.container(horizontal=True):
        st.metric("Fair price per night", money(fair, cur, rates), border=True,
                  help=f"Typical range {money(lo, cur, rates)} to {money(hi, cur, rates)}")
        if listed:
            listed_try = listed * rates[cur]
            gap = (fair - listed_try) / fair
            st.metric("Your listed price", money(listed_try, cur, rates), border=True,
                      delta=deal_label(gap), delta_color="normal" if gap > 0.03 else "inverse" if gap < -0.03 else "off")
        st.metric("Typical listed price here", money(group["price"].median(), cur, rates), border=True,
                  help=f"Median of {len(group):,} real listings of this type in {hood}, any size")
    if "mlp" in parts:
        a, b = stack["meta_coef"]
        esc = lambda v: money(v, cur, rates).replace("$", "\\$")   # a bare $ would start a formula in markdown
        st.caption(f"XGBoost says {esc(parts['xgb'][0])} and our neural network says {esc(parts['mlp'][0])}. "
                   + (f"The stacked model combines them on the log scale ({a:.2f} × XGBoost + {b:.2f} × network), "
                      "with weights learned in notebook 05." if stack["use_stack"]
                      else "Notebook 05 found that combining them did not beat XGBoost alone, so the fair price is XGBoost's."))

# ---------- fair vs listed ----------
st.header("Fair price vs listed price")
st.caption("Each dot is a stay. Dots below the line are listed for less than the model thinks they're worth: "
           "those are the \"below fair price\" deals in step 2 of the planner.")
s = df.dropna(subset=["fair_price"]).sample(2000, random_state=1).copy()
s["Listed"] = s["price"] / rates[cur]
s["Fair"] = s["fair_price"] / rates[cur]
s["Deal"] = s["price_gap"].map(deal_label)
lo_v, hi_v = float(s[["Listed", "Fair"]].min().min()), float(s[["Listed", "Fair"]].max().max())
scale = alt.Scale(type="log", domain=[lo_v, hi_v], nice=False)
dots = alt.Chart(s).mark_circle(size=22, opacity=0.45).encode(
    x=alt.X("Fair:Q", scale=scale, title=f"Fair price per night ({cur}, our model)"),
    y=alt.Y("Listed:Q", scale=scale, title=f"Listed price per night ({cur})"),
    tooltip=[alt.Tooltip("name:N", title="Stay"), alt.Tooltip("Listed:Q", format=",.0f"),
             alt.Tooltip("Fair:Q", format=",.0f"), alt.Tooltip("Deal:N")],
)
line = alt.Chart(pd.DataFrame({"v": [lo_v, hi_v]})).mark_line(strokeDash=[4, 4], color="gray").encode(x="v:Q", y="v:Q")
st.altair_chart(dots + line, alt="Scatter of fair price against listed price for 2,000 sampled stays")

# ---------- segments ----------
st.header("The six kinds of stay")
st.caption("Stays are compared only with their own kind, so a cheap shared room never looks like a better deal than a flat.")
seg = (df.groupby("segment_name")
         .agg(stays=("id", "size"), median_price=("price", "median"), guests=("accommodates", "median"))
         .reset_index().sort_values("stays", ascending=False))
seg["Median price"] = (seg["median_price"] / rates[cur]).round()
bars = alt.Chart(seg).mark_bar(cornerRadiusEnd=4, height=18).encode(
    x=alt.X("stays:Q", title="Stays"), y=alt.Y("segment_name:N", sort="-x", title=None, axis=alt.Axis(labelLimit=260)),
    tooltip=[alt.Tooltip("segment_name:N", title="Kind"), alt.Tooltip("stays:Q", format=","),
             alt.Tooltip("Median price:Q", format=",.0f", title=f"Median price ({cur})"),
             alt.Tooltip("guests:Q", title="Median guests")],
)
st.altair_chart(bars, alt="Bar chart of the number of stays in each of the six kinds")

# ---------- ranking ----------
st.header("How the 5 stays are picked")
st.write(
    "Every stay that fits your guests, nights, budget and stay type gets a score from six things: its price, how it "
    "compares with the fair price, how close it is to your sights, its guest rating, how much we can trust it (reviews, "
    "Superhost, and the active-listing model for new stays) and comfort (bedrooms, bathrooms, amenities). "
    "The weights change with the *What matters most?* choice in the planner. The top score is marked Recommended. "
    "Each stay also has a *Similar stays* button: the stays our price network describes most like it."
)

# ---------- learning from testers ----------
st.header("What testers choose")
lw, fb = learned_weights(), feedback_stats()
st.write(
    "When someone plans their days with one of the 5 stays, the planner stores (anonymously) the six factor scores of "
    "all 5 stays and which one they took. Each stay also has a *Good pick for you?* question. From the picks, a "
    "logistic regression on pairs (chosen stay minus each stay passed over) learns how much each factor really "
    f"matters to people. Once there are {lw['min']} picks, the planner's *Balanced* weights start moving towards "
    "the learned ones, a little more with every pick."
)
with st.container(horizontal=True):
    st.metric("Trips planned", f"{lw['n']:,}", border=True, help="Times someone went on to plan their days with one of the 5 stays")
    st.metric("Chose the top stay", "–" if lw["top1"] is None else f"{lw['top1']:.0%}", border=True,
              help="Share of those picks that were stay #1, the one marked Recommended")
    st.metric("Said the stay was a good pick", "–" if fb["yes"] is None else f"{fb['yes']:.0%}", border=True,
              help=f"Out of {fb['n']:,} answers to \"Good pick for you?\" (each person's last answer per stay)")
    st.metric("Top stay a good pick", "–" if fb["yes_top"] is None else f"{fb['yes_top']:.0%}", border=True,
              help=f"Answers about stay #1 only ({fb['n_top']:,})")
if lw["ready"]:
    w = pd.DataFrame({"Factor": FACTORS * 3,
                      "Weight": HAND["Balanced"] + lw["learned"] + lw["balanced"],
                      "Set": ["Hand-set"] * 6 + ["Learned from picks"] * 6 + ["Used now"] * 6})
    order = ["Hand-set", "Learned from picks", "Used now"]
    wbars = alt.Chart(w).mark_bar(cornerRadiusEnd=3, height=9).encode(
        x=alt.X("Weight:Q", title="Weight (out of 100)"),
        y=alt.Y("Factor:N", sort=FACTORS, title=None),
        yOffset=alt.YOffset("Set:N", sort=order),
        color=alt.Color("Set:N", sort=order, scale=alt.Scale(range=["#5474a1", "#b36633", "#323659"]),
                        legend=alt.Legend(title=None, orient="top")),
        tooltip=["Factor", "Set", alt.Tooltip("Weight:Q", format=".0f")],
    ).properties(height=320)
    st.altair_chart(wbars, alt="Bar chart of the hand-set, learned and current weight of each ranking factor")
    st.caption(f"Used now = {1 - lw['alpha']:.0%} hand-set + {lw['alpha']:.0%} learned. People often take the first stay "
               "they see, so the learned weights lean towards the ranking they were shown; that is why they are blended in slowly.")
else:
    st.caption(f"{lw['n']} of the {lw['min']} picks needed before the weights are learned. Until then the planner uses the hand-set weights.")

# ---------- monthly stays ----------
ms = monthly_scores()
if ms:
    st.header("Monthly stays")
    st.write(
        f"About a third of the listings ({ms['n']:,}) only take stays of 28 nights or more. They price differently, so "
        f"they have their own model (notebook 06): its typical error is {ms['MedianAPE_%']:.0f}% (R² {ms['R2_log']:.2f}), "
        f"against {ms['normal_model_MedianAPE_%']:.0f}% when the normal-stay model was used for them. They are harder to "
        "price: fewer of them, few reviews, and many are rarely booked. Explore shows them under *A month or more*."
    )

# ---------- who uses it ----------
st.header("People using the planner")
stats = visit_stats()
if stats is None:
    st.caption("The visitor count isn't available right now.")
else:
    st.caption("Each device is counted once a day. Nothing personal is stored, only a scrambled id."
               + ("" if stats["lasting"] else " This copy keeps the count in a local file, so it restarts when the server does."))
    with st.container(horizontal=True):
        st.metric("Visitors so far", f"{stats['total']:,}", border=True)
        st.metric("Today", f"{stats['today']:,}", border=True)
        st.metric("Last 7 days", f"{stats['week']:,}", border=True, help="Visits per day added up over the last week")
        accounts = account_count()
        st.metric("Accounts", "–" if accounts is None else f"{accounts:,}", border=True, help="People who created an account")
    visits = alt.Chart(stats["per_day"]).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, width=alt.RelativeBandSize(0.7)).encode(
        x=alt.X("yearmonthdate(day):T", title=None, axis=alt.Axis(format="%d %b", labelAngle=0, tickCount=8, grid=False)),
        y=alt.Y("visitors:Q", title="Visitors", axis=alt.Axis(tickMinStep=1)),
        tooltip=[alt.Tooltip("day:T", format="%a %d %b", title="Day"), alt.Tooltip("visitors:Q", title="Visitors")],
    ).properties(height=220)
    st.altair_chart(visits, alt="Bar chart of visitors per day over the last 30 days")

# ---------- notebook figures ----------
FIG_LIST = [("stacking_comparison.png", "XGBoost, the neural network and the two stacked (notebook 05)"),
            ("monthly_model.png", "Monthly stays: their own price model (notebook 06)"),
            ("mlp_listing_embeddings.png", "What the network learned about each stay (notebook 05)"),
            ("predicted_vs_actual.png", "Price model: predicted vs actual (notebook 02)"),
            ("segments.png", "The six kinds of stay (notebook 03)"),
            ("shap_summary.png", "What drives the price (SHAP, notebook 02)"),
            ("reliability_roc.png", "Active-listing model ROC curve (notebook 04)")]
figs = [(FIGS / f, cap) for f, cap in FIG_LIST if (FIGS / f).exists()]
if figs:
    st.header("From the notebooks")
    for k in range(0, len(figs), 2):
        for col, (path, cap) in zip(st.columns(2, vertical_alignment="top"), figs[k:k + 2]):
            col.image(str(path), caption=cap, alt=cap)
