"""Learns the stay-ranking weights from the stays testers actually chose.

The planner scores every stay on six factors (price, deal, location, rating, trust, comfort) and adds them up
with hand-set weights. Each time someone goes on to plan their days with one of the 5 stays they were shown,
the page stores the six scores of all 5 stays and which one they took (core/usage.py).

From those picks we fit a conditional logit, written as a logistic regression on pairs: for every stay that
was shown but not chosen, the input is (scores of the chosen stay - scores of the other one), and the model
learns how much each factor makes a stay more likely to be chosen. Its coefficients, scaled to add up to 100,
are the learned weights. With few picks they are noisy, so the planner's "Balanced" weights move towards
them gradually: weight on the learned ones = n / (n + 50), and only once there are 30 picks.
"""
import numpy as np
import streamlit as st

from core.usage import load_events

FACTORS = ["Price", "Deal", "Location", "Rating", "Trust", "Comfort"]
HAND = {"Save money": [35, 20, 15, 10, 15, 5], "Balanced": [20, 15, 25, 15, 15, 10], "Enjoy": [5, 10, 30, 25, 10, 20]}
MIN_PICKS, PRIOR = 30, 50


def learned_weights() -> dict:
    """{"n": picks, "ready": bool, and when ready: "learned", "balanced", "alpha", "top1"}"""
    return _fit(len(load_events("pick")))


@st.cache_data(show_spinner=False, max_entries=20)
def _fit(n_picks: int) -> dict:
    """Refits only when the number of picks has changed."""
    picks = load_events("pick")
    out = {"n": len(picks), "ready": False, "min": MIN_PICKS,
           "top1": float(np.mean([p["k"] == 0 for p in picks])) if picks else None}
    if len(picks) < MIN_PICKS:
        return out
    diffs = []
    for p in picks:
        f = np.asarray(p["f"], dtype=float)
        diffs += [f[p["k"]] - f[j] for j in range(len(f)) if j != p["k"]]
    D = np.asarray(diffs)
    D = D[np.abs(D).sum(axis=1) > 0]   # a pair of identical stays says nothing
    if len(D) < MIN_PICKS:
        return out
    from sklearn.linear_model import LogisticRegression
    # each pair appears both ways round, so the model can't just learn "always yes"
    model = LogisticRegression(fit_intercept=False, C=1.0).fit(np.vstack([D, -D]), np.r_[np.ones(len(D)), np.zeros(len(D))])
    beta = np.clip(model.coef_[0], 0, None)   # a factor that pushes people away gets weight 0, not a negative one
    if beta.sum() <= 0:
        return out
    learned = beta / beta.sum() * 100
    alpha = len(picks) / (len(picks) + PRIOR)
    balanced = (1 - alpha) * np.asarray(HAND["Balanced"]) + alpha * learned
    return {**out, "ready": True, "learned": [round(float(v), 1) for v in learned],
            "balanced": [int(round(v)) for v in balanced], "alpha": round(alpha, 2)}


def feedback_stats() -> dict:
    """Share of "yes" answers to "Good pick for you?", overall and for the top stay (#1), counting each
    visitor's last answer per stay only."""
    last = {}
    for e in load_events("feedback"):
        last[(e["visitor"], e["id"])] = e
    ans = list(last.values())
    yes = lambda rows: float(np.mean([r["good"] for r in rows])) if rows else None
    top = [r for r in ans if r["k"] == 0]
    return {"n": len(ans), "yes": yes(ans), "n_top": len(top), "yes_top": yes(top)}


MIN_TRIPS = 20


def real_cooc(n_sights: int) -> dict | None:
    """"Travellers like you also added", from the trips people really planned here: for every pair of sights,
    the % of trips with the first that also have the second, plus how popular each sight is. Each person's
    identical trip counts once. None until there are 20 trips, when the planner keeps its sample trips."""
    return _cooc(len(load_events("pick")), n_sights)


@st.cache_data(show_spinner=False, max_entries=20)
def _cooc(n_picks: int, n_sights: int) -> dict | None:
    trips = {(p.get("user") or p["visitor"], tuple(p.get("sights") or [])) for p in load_events("pick")}
    trips = [set(s) for _, s in trips if len(s) >= 2 and max(s) < n_sights]
    if len(trips) < MIN_TRIPS:
        return None
    has = np.array([[j in t for j in range(n_sights)] for t in trips], dtype=float)   # trips x sights
    both, count = has.T @ has, has.sum(axis=0)
    p = np.where(count[:, None] > 0, both / np.maximum(count[:, None], 1) * 100, 0)
    np.fill_diagonal(p, 0)
    return {"n": len(trips), "real": True, "p": np.rint(p).astype(int).tolist(),
            "pop": np.rint(count / len(trips) * 100).astype(int).tolist()}
