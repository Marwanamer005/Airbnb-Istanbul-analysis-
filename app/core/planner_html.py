"""Builds the map planner page (app/static/planner.html) from the design template and the real data.

The planner itself runs in the browser (map, routes, day plans). Python feeds it the listings with the
model outputs: fair price, price gap, reliability and segment, plus the current exchange rates.
"""
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd
import streamlit as st

from core.data import APP, PLANNER_DATA, load_listings, load_rates

TEMPLATE = APP / "design_demo_template.html"
OUT = APP / "static" / "planner.html"
SIGHT_PHOTOS = APP / "static" / "sights"
UA = {"User-Agent": "SmartIstanbulTripPlanner/1.0 (NTI student project)"}   # Wikipedia asks for one

# districts drawn on the planner map (the routing knows which side of the water each one is on)
DISTRICTS = ["Atasehir", "Bakirkoy", "Bayrampasa", "Besiktas", "Beyoglu", "Esenler", "Eyup", "Fatih", "Gaziosmanpasa",
             "Gungoren", "Kadikoy", "Kagithane", "Sisli", "Umraniye", "Uskudar", "Zeytinburnu"]
STAY_TYPES = ["Entire home", "Hotel room", "Private room", "Serviced apt", "Hostel / shared"]
STATIC_FILES = {"__WORLD__": "world_small.json", "__TURKEY__": "turkey.json", "__IST__": "ist_small.json",
                "__STATIONS__": "stations.json", "__DLABELS__": "distlabels.json", "__MON__": "mon.json",
                "__REST__": "rest.json", "__COOC__": "cooc.json"}


def listings_payload(df: pd.DataFrame) -> dict:
    """Column arrays in the short field names the planner reads (see `const L = LIST.c` in the template)."""
    keep = df["neighbourhood_cleansed"].isin(DISTRICTS) & df["fair_price"].notna() & df["stay_type"].isin(STAY_TYPES)
    # leave out listings that look inactive: no booking in the last year and a low reliability score
    keep &= (df["active_ltm"] == 1) | (df["reliability"] >= 0.5)
    d = df[keep].reset_index(drop=True)
    segs = sorted(d["segment_name"].dropna().unique())
    num = lambda col, nd=0: d[col].fillna(0).round(nd).tolist() if nd else d[col].fillna(0).round().astype(int).tolist()
    c = {
        "id": d["id"].astype(str).tolist(),
        "nm": d["name"].fillna("Airbnb stay").str.slice(0, 60).tolist(),
        "la": d["latitude"].round(5).tolist(), "lo": d["longitude"].round(5).tolist(),
        "pr": num("price"), "fa": num("fair_price"), "gp": num("price_gap", 3),
        "ty": d["stay_type"].map(STAY_TYPES.index).tolist(),
        "ac": num("accommodates"), "mn": num("minimum_nights"), "mx": num("maximum_nights"),
        "ra": num("review_scores_rating", 2), "rs": num("rating_shrunk", 3), "rv": num("number_of_reviews"),
        "sh": num("is_superhost"), "rl": num("reliability", 2), "bd": num("bedrooms", 1), "ba": num("bathrooms_n", 1),
        "am": num("n_amenities"), "sv": num("has_sea_view"),
        "di": d["neighbourhood_cleansed"].map(DISTRICTS.index).tolist(),
        "sg": d["segment_name"].map({s: k for k, s in enumerate(segs)}).fillna(0).astype(int).tolist(),
        "pu": d["picture_url"].fillna("").tolist(),
    }
    return {"types": STAY_TYPES, "dists": DISTRICTS, "segs": segs, "c": c}


def _get(url: str, timeout: int = 15) -> bytes:
    """GET with the User-Agent Wikimedia asks for; waits and retries once when it says "too many requests"."""
    for attempt in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt:
                raise
            time.sleep(3)


def _is_photo(path) -> bool:
    """A usable photo: at least 400 px on its short side (rules out logos, maps and tiny drawings)."""
    try:
        from PIL import Image
        with Image.open(path) as im:
            return min(im.size) >= 400
    except ImportError:
        return path.stat().st_size > 40_000
    except Exception:
        return False


def _candidate_urls(title: str) -> list:
    """Photo URLs to try for a Wikipedia article, best first."""
    q = urllib.parse.quote(title.replace(" ", "_"))
    urls = []
    try:
        info = json.loads(_get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{q}", timeout=8))
        thumb, orig = (info.get("thumbnail") or {}).get("source"), info.get("originalimage") or {}
        # Wikimedia only serves thumbnails at standard widths (960 is one)
        if thumb:
            urls.append(re.sub(r"/\d+px-", "/960px-", thumb))
        if orig.get("source") and orig.get("width", 1e9) <= 2000:
            urls.append(orig["source"])
    except Exception:
        pass
    try:
        # the article's lead image can be a map or a drawing, so also look through the other photos in the article
        api = ("https://en.wikipedia.org/w/api.php?action=query&format=json&generator=images&gimlimit=40"
               f"&prop=imageinfo&iiprop=url|size|mime&iiurlwidth=960&titles={q}")
        pages = json.loads(_get(api, timeout=10)).get("query", {}).get("pages", {}).values()
        skip = ("map", "logo", "flag", "icon", "locator", "coat", "seal", "plan", "commons-", "symbol")
        for pg in pages:
            ii = (pg.get("imageinfo") or [{}])[0]
            name = pg.get("title", "").lower()
            if ii.get("mime") == "image/jpeg" and ii.get("width", 0) >= 800 and not any(w in name for w in skip):
                urls.append(ii.get("thumburl") or ii.get("url"))
    except Exception:
        pass
    return urls


def fetch_sight_photos(sights: list) -> list:
    """Saves one Wikipedia photo per sight in app/static/sights/ (only the first time) and adds its path as `ph`.

    Serving the photos from the app means they show even when a browser can't reach Wikipedia directly.
    A sight whose photo can't be downloaded keeps no `ph`, and the page then asks Wikipedia itself.
    """
    SIGHT_PHOTOS.mkdir(parents=True, exist_ok=True)
    missing = []
    for m in sights:
        title = m.get("wiki") or m["n"]
        name = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") + ".jpg"
        path = SIGHT_PHOTOS / name
        if path.exists() and not _is_photo(path):
            path.unlink()                      # an earlier run saved a logo or tiny image: try again
        if not path.exists():
            for url in _candidate_urls(title):
                try:
                    path.write_bytes(_get(url))
                    if _is_photo(path):
                        break
                    path.unlink()
                except Exception:
                    continue
            time.sleep(0.3)                    # be gentle with Wikimedia
        if path.exists():
            m["ph"] = "sights/" + name
        else:
            missing.append(m["n"])
    if missing:
        print(f"[planner] no photo downloaded for {len(missing)} sights (the browser will try): {', '.join(missing)}")
    return sights


@st.cache_data(show_spinner="Preparing the map and sight photos...")
def build_planner() -> str:
    """Writes the planner page once per server start and returns a version string for cache busting."""
    html = TEMPLATE.read_text(encoding="utf-8")
    for ph, name in STATIC_FILES.items():
        if ph == "__MON__":
            sights = fetch_sight_photos(json.loads((PLANNER_DATA / name).read_text(encoding="utf-8")))
            html = html.replace(ph, json.dumps(sights, ensure_ascii=False))
            continue
        html = html.replace(ph, (PLANNER_DATA / name).read_text(encoding="utf-8").strip())
    html = html.replace("__LIST__", json.dumps(listings_payload(load_listings()), separators=(",", ":"), ensure_ascii=False))
    html = html.replace("__REAL__", "true")
    rates, _ = load_rates()
    html = re.sub(r"const RATES = \{[^}]*\};", "const RATES = " + json.dumps(rates) + ";", html, count=1)
    html = html.replace("From ${COOC.n.toLocaleString(\"en-US\")} sample trips in this preview. The app learns from real saved trips.",
                        "Based on ${COOC.n.toLocaleString(\"en-US\")} sample trips built from how popular each sight is.")
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Smart Istanbul Trip Planner</title>'
            '</head><body>' + html + "</body></html>")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    return hashlib.md5(page.encode()).hexdigest()[:10]
