"""Scores Airbnb listings for a trip and explains the top picks.

Flow: hard filters -> six factor scores in [0, 1] -> weighted sum -> top N + a "why" line.
"""
import numpy as np
import pandas as pd

from src.geo import haversine_m

FACTORS = ["Cost", "Deal", "Location", "Quality", "Trust", "Comfort"]

# Weights per trip priority (percent, each row sums to 100)
MODES = {
    "Save money": {"Cost": 35, "Deal": 20, "Location": 15, "Quality": 10, "Trust": 15, "Comfort": 5},
    "Balanced":   {"Cost": 20, "Deal": 15, "Location": 25, "Quality": 15, "Trust": 15, "Comfort": 10},
    "Enjoy":      {"Cost": 5,  "Deal": 10, "Location": 30, "Quality": 25, "Trust": 10, "Comfort": 20},
}

STAY_TYPES = ["Entire home", "Hotel room", "Private room", "Serviced apt", "Hostel / shared"]

LOCATION_FULL_SCORE_M = 500     # average distance to chosen monuments that scores 1.0
LOCATION_ZERO_SCORE_M = 8000    # ... and 0.0


def filter_listings(df, stay_types, guests, nights, max_price_try):
    """Hard rules: a listing that fails any of these is never shown."""
    m = (
        df["stay_type"].isin(stay_types)
        & (df["accommodates"] >= guests)
        & (df["minimum_nights"] <= nights)
        & (df["maximum_nights"].fillna(10_000) >= nights)
        & (df["price"] <= max_price_try)
    )
    if "has_availability" in df:
        m &= df["has_availability"].ne("f")
    return df[m].copy()


def mean_distance_m(df, monuments):
    """Average distance (m) from each listing to the chosen monuments."""
    if monuments.empty:
        return pd.Series(np.nan, index=df.index)
    d = np.column_stack([
        haversine_m(df["latitude"].to_numpy(), df["longitude"].to_numpy(), lat, lon)
        for lat, lon in monuments[["lat", "lon"]].to_numpy()
    ])
    return pd.Series(d.mean(axis=1), index=df.index)


def factor_scores(c, guests, monuments):
    """Six scores in [0, 1], higher is better. `c` is the filtered candidate table."""
    s = pd.DataFrame(index=c.index)
    # Cost: cheapest candidate = 1, most expensive = 0 (rank-based so outliers don't squash it)
    s["Cost"] = 1 - c["price"].rank(pct=True) if len(c) > 1 else 1.0
    # Deal: 0.5 = priced at fair value, 1 = 50%+ below fair, 0 = 50%+ above fair
    s["Deal"] = (0.5 + c["price_gap"].clip(-0.5, 0.5))
    # Location: close to the monuments the guest picked
    dist = c["dist_to_picks_m"]
    if dist.isna().all():
        s["Location"] = 1 - (c["dist_sultanahmet_m"].clip(0, 10_000) / 10_000)
    else:
        s["Location"] = 1 - ((dist - LOCATION_FULL_SCORE_M)
                             / (LOCATION_ZERO_SCORE_M - LOCATION_FULL_SCORE_M)).clip(0, 1)
    # Quality: rating already shrunk toward the city mean for listings with few reviews
    s["Quality"] = ((c["rating_shrunk"] - 4.0) / 1.0).clip(0, 1)
    # Trust: review history + Superhost; for listings with no reviews, the reliability model
    reviewed = c["number_of_reviews"] > 0
    history = (np.log1p(c["number_of_reviews"]) / np.log1p(100)).clip(0, 1)
    trust_reviewed = 0.6 * history + 0.4 * c["is_superhost"]
    if "reliability" in c:
        trust_new = 0.5 * c["reliability"].fillna(0.5)
    else:
        trust_new = pd.Series(0.25, index=c.index)
    s["Trust"] = np.where(reviewed, trust_reviewed, trust_new)
    # Comfort: room to spread out + amenities
    beds_per_guest = (c["bedrooms"].clip(lower=0.5) / max(guests, 1) * 2).clip(0, 1)
    baths = (c["bathrooms_n"] / max(1, np.ceil(guests / 3))).clip(0, 1)
    amen = (c["n_amenities"] / 50).clip(0, 1)
    s["Comfort"] = 0.4 * beds_per_guest + 0.2 * baths + 0.4 * amen
    return s.astype(float)


def recommend(df, monuments, stay_types, guests, nights, max_price_try, weights, top_n=5):
    """Return (top listings with scores and 'why', number of candidates after filters)."""
    c = filter_listings(df, stay_types, guests, nights, max_price_try)
    if c.empty:
        return c, 0
    c["dist_to_picks_m"] = mean_distance_m(c, monuments)
    scores = factor_scores(c, guests, monuments)
    w = pd.Series(weights, dtype=float)
    w = w / w.sum() if w.sum() > 0 else pd.Series(1 / len(FACTORS), index=FACTORS)
    c["score"] = (scores[FACTORS] * w[FACTORS]).sum(axis=1) * 100
    for f in FACTORS:
        c[f"f_{f}"] = scores[f]
    top = c.sort_values("score", ascending=False).head(top_n).copy()
    top["why"] = [explain(row, w) for _, row in top.iterrows()]
    return top, len(c)


def explain(row, w):
    """Plain-language reasons from the two factors that contributed most."""
    contrib = {f: row[f"f_{f}"] * w[f] for f in FACTORS}
    reasons = []
    for f in sorted(contrib, key=contrib.get, reverse=True)[:2]:
        if f == "Location" and pd.notna(row["dist_to_picks_m"]):
            reasons.append(f"{row['dist_to_picks_m'] / 1000:.1f} km on average from your monuments")
        elif f == "Location":
            reasons.append(f"{row['dist_sultanahmet_m'] / 1000:.1f} km from Sultanahmet")
        elif f == "Deal":
            gap = row["price_gap"]
            reasons.append(f"{gap:.0%} below its fair price" if gap > 0.02 else "priced about fair")
        elif f == "Cost":
            reasons.append("one of the cheapest stays that fit your trip")
        elif f == "Quality":
            reasons.append(f"rated {row['review_scores_rating']:.2f} from {int(row['number_of_reviews'])} reviews"
                           if row["number_of_reviews"] > 0 else "new listing")
        elif f == "Trust":
            if row["number_of_reviews"] > 0:
                reasons.append(("Superhost, " if row["is_superhost"] else "") + f"{int(row['number_of_reviews'])} reviews")
            else:
                reasons.append("new listing that looks active")
        else:
            reasons.append(f"{int(row['bedrooms'])} bedroom(s), {int(row['n_amenities'])} amenities")
    return "; ".join(reasons).capitalize() + "."
