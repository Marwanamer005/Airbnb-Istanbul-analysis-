"""Browse the real listings with the model outputs: where the fair-price deals are."""
import altair as alt
import streamlit as st

from core.data import deal_label, load_listings
from core.ui import currency_picker

df = load_listings().dropna(subset=["fair_price"])

st.title("Explore stays")
st.write("Every Airbnb listing in Istanbul with the price our model thinks is fair. Use it to see where the good deals are.")

cur, rates = currency_picker()

with st.container(horizontal=True, vertical_alignment="bottom"):
    hoods = st.multiselect("Neighbourhoods", sorted(df["neighbourhood_cleansed"].unique()),
                           default=["Beyoglu", "Fatih", "Besiktas", "Kadikoy", "Sisli", "Uskudar"])
    kinds = st.multiselect("Kind of stay", sorted(df["segment_name"].dropna().unique()))
    guests = st.number_input("Guests", 1, 16, 2)
    deals_only = st.toggle("Only below fair price", value=True)

f = df[df["accommodates"] >= guests]
if hoods:
    f = f[f["neighbourhood_cleansed"].isin(hoods)]
if kinds:
    f = f[f["segment_name"].isin(kinds)]
f = f[(f["active_ltm"] == 1) | (f["reliability"] >= 0.5)]   # hide listings that look inactive
if deals_only:
    # over 60% below fair is usually a pricing quirk (a single dorm bed, a monthly rate), not a real deal
    f = f[f["price_gap"].between(0.03, 0.6)]

if f.empty:
    st.info("No stays match these filters. Try more neighbourhoods or fewer guests.")
    st.stop()

with st.container(horizontal=True):
    st.metric("Stays", f"{len(f):,}", border=True)
    st.metric("Median price per night", f"{f['price'].median() / rates[cur]:,.0f} {cur}", border=True)
    st.metric("Median saving vs fair price", f"{f['price_gap'].median():.0%}", border=True)

st.subheader("Typical nightly price by neighbourhood")
by = (f.groupby("neighbourhood_cleansed").agg(stays=("id", "size"), price=("price", "median"), fair=("fair_price", "median"))
        .reset_index().query("stays >= 5"))
by["Median price"] = (by["price"] / rates[cur]).round()
by["Median fair price"] = (by["fair"] / rates[cur]).round()
chart = alt.Chart(by).mark_bar(cornerRadiusEnd=4, height=16).encode(
    x=alt.X("Median price:Q", title=f"Median listed price per night ({cur})", axis=alt.Axis(tickCount=6)),
    y=alt.Y("neighbourhood_cleansed:N", sort="-x", title=None),
    tooltip=[alt.Tooltip("neighbourhood_cleansed:N", title="Neighbourhood"), alt.Tooltip("stays:Q", format=","),
             alt.Tooltip("Median price:Q", format=",.0f"), alt.Tooltip("Median fair price:Q", format=",.0f")],
)
st.altair_chart(chart, alt="Bar chart of median nightly price by neighbourhood")

st.subheader("Best deals")
st.caption("Stays with at least 3 reviews, ranked by how far below their fair price they are listed. "
           "Select a row to see similar stays.")
top = f[f["number_of_reviews"] >= 3].sort_values("price_gap", ascending=False).head(200).copy()
top["Price"] = top["price"] / rates[cur]
top["Fair price"] = top["fair_price"] / rates[cur]
top["Deal"] = top["price_gap"].map(deal_label)
top["Link"] = "https://www.airbnb.com/rooms/" + top["id"].astype(str)
table = st.dataframe(
    top[["picture_url", "name", "neighbourhood_cleansed", "segment_name", "accommodates", "Price", "Fair price", "Deal",
         "review_scores_rating", "number_of_reviews", "reliability", "Link"]],
    hide_index=True, row_height=64, alt="Table of the 200 stays priced furthest below their fair price",
    column_config={
        "picture_url": st.column_config.ImageColumn("Photo", width="small"),
        "name": st.column_config.TextColumn("Stay", width="medium"),
        "neighbourhood_cleansed": "Neighbourhood",
        "segment_name": "Kind",
        "accommodates": st.column_config.NumberColumn("Guests"),
        "Price": st.column_config.NumberColumn(f"Price ({cur})", format="%.0f"),
        "Fair price": st.column_config.NumberColumn(f"Fair ({cur})", format="%.0f"),
        "review_scores_rating": st.column_config.NumberColumn("Rating", format="%.2f"),
        "number_of_reviews": st.column_config.NumberColumn("Reviews"),
        "reliability": st.column_config.ProgressColumn("Likely active", min_value=0, max_value=1, format="percent"),
        "Link": st.column_config.LinkColumn("Airbnb", display_text="Open"),
    },
    on_select="rerun", selection_mode="single-row",
)

picked = table.selection.rows
if picked and "similar_ids" in df:
    stay = top.iloc[picked[0]]
    sim = df.set_index("id").reindex(list(stay["similar_ids"])).dropna(subset=["name"]).reset_index()
    st.subheader(f"Stays like {stay['name']}")
    st.caption("Found by our price neural network (notebook 05): it describes every stay with 64 numbers "
               "(size, comfort, location, district), and these are the 5 closest to the one you picked.")
    sim["Price"] = sim["price"] / rates[cur]
    sim["Fair price"] = sim["fair_price"] / rates[cur]
    sim["Deal"] = sim["price_gap"].map(deal_label)
    sim["Link"] = "https://www.airbnb.com/rooms/" + sim["id"].astype(str)
    st.dataframe(
        sim[["picture_url", "name", "neighbourhood_cleansed", "segment_name", "accommodates", "Price", "Fair price",
             "Deal", "review_scores_rating", "number_of_reviews", "Link"]],
        hide_index=True, row_height=64, alt="Table of the 5 stays most like the selected one",
        column_config={
            "picture_url": st.column_config.ImageColumn("Photo", width="small"),
            "name": st.column_config.TextColumn("Stay", width="medium"),
            "neighbourhood_cleansed": "Neighbourhood",
            "segment_name": "Kind",
            "accommodates": st.column_config.NumberColumn("Guests"),
            "Price": st.column_config.NumberColumn(f"Price ({cur})", format="%.0f"),
            "Fair price": st.column_config.NumberColumn(f"Fair ({cur})", format="%.0f"),
            "review_scores_rating": st.column_config.NumberColumn("Rating", format="%.2f"),
            "number_of_reviews": st.column_config.NumberColumn("Reviews"),
            "Link": st.column_config.LinkColumn("Airbnb", display_text="Open"),
        },
    )

st.subheader("Where they are")
st.map(top.rename(columns={"latitude": "lat", "longitude": "lon"})[["lat", "lon"]], color="#b36633", size=40,
       alt="Map of the best deals")
