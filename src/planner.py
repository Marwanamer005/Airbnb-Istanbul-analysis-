"""Turns chosen monuments into a day-by-day program around the chosen stay."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from src.geo import haversine_m


def group_into_days(monuments, days, seed=42):
    """K-Means on monument coordinates, k = number of days (or fewer if fewer monuments).

    Then rebalance so no day has more than ceil(n / k) stops: an overfull day hands its
    farthest-from-centre monument to the nearest day that still has room.
    """
    m = monuments.reset_index(drop=True).copy()
    k = max(1, min(days, len(m)))
    if k == 1:
        m["day"] = 0
        return m
    xy = m[["lat", "lon"]].to_numpy()
    km = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(xy)
    centres = km.cluster_centers_
    dist = np.array([[haversine_m(a, b, c[0], c[1]) for c in centres] for a, b in xy])
    cap = int(np.ceil(len(m) / k))
    day = km.labels_.copy()
    for _ in range(len(m)):
        counts = np.bincount(day, minlength=k)
        over = np.where(counts > cap)[0]
        if not len(over):
            break
        d = over[0]
        members = np.where(day == d)[0]
        worst = members[np.argmax(dist[members, d])]
        options = [j for j in np.argsort(dist[worst]) if counts[j] < cap]
        day[worst] = options[0]
    m["day"] = day
    # number days from west to east so the plan reads naturally
    order = m.groupby("day")["lon"].mean().sort_values().index
    m["day"] = m["day"].map({d: i for i, d in enumerate(order)})
    return m


def order_stops(day_monuments, start_lat, start_lon):
    """Nearest-neighbour walk starting from the stay."""
    left = day_monuments.copy()
    route, lat, lon = [], start_lat, start_lon
    while len(left):
        d = haversine_m(lat, lon, left["lat"].to_numpy(), left["lon"].to_numpy())
        i = int(np.argmin(d))
        row = left.iloc[i].copy()
        row["leg_m"] = d[i]
        route.append(row)
        lat, lon = row["lat"], row["lon"]
        left = left.drop(left.index[i])
    return pd.DataFrame(route)


def restaurants_near(restaurants, lat, lon, n=3, radius_m=800):
    """Closest named restaurants to a point (restaurants: DataFrame with name, cuisine, lat, lon)."""
    d = haversine_m(lat, lon, restaurants["lat"].to_numpy(), restaurants["lon"].to_numpy())
    near = restaurants.assign(dist_m=d)
    near = near[near["dist_m"] <= radius_m].sort_values("dist_m")
    # prefer places that list a cuisine (more useful to a visitor), then fill with the rest
    with_cuisine = near[near["cuisine"].fillna("") != ""]
    picked = pd.concat([with_cuisine.head(n), near]).drop_duplicates("name").head(n)
    return picked


def build_program(monuments, days, stay_lat, stay_lon, restaurants):
    """Return a list of days: {'day', 'stops' (DataFrame), 'restaurants' (DataFrame), 'minutes', 'fees'}."""
    if monuments.empty:
        return []
    grouped = group_into_days(monuments, days)
    plan = []
    for d in range(days):
        todays = grouped[grouped["day"] == d]
        if todays.empty:
            plan.append({"day": d + 1, "stops": todays, "restaurants": restaurants.head(0),
                         "minutes": 0, "fees": 0})
            continue
        stops = order_stops(todays, stay_lat, stay_lon)
        centre = stops[["lat", "lon"]].mean()
        plan.append({
            "day": d + 1,
            "stops": stops,
            "restaurants": restaurants_near(restaurants, centre["lat"], centre["lon"]),
            "minutes": int(stops["visit_minutes"].sum()),
            "fees": float(stops["entry_fee_try"].fillna(0).sum()),
        })
    return plan
