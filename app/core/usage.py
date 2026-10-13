"""Counts the people who use the app (one row per visitor per day) and stores what testers choose in the planner:
which of the 5 stays they plan with, and their "Good pick?" answers. Nothing personal is stored.

Where the count lives:
- If the app's secrets have a `usage_db_url` (a Postgres link, e.g. a free Supabase database), it goes there and
  survives restarts and redeploys. That is what the deployed app should use.
- Otherwise it goes to data/usage.sqlite next to the app. Fine on your own computer, but Streamlit Community Cloud
  wipes that file whenever the app restarts, so the online count would start again from zero.
"""
import datetime as dt
import hashlib
import json
import re
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_FILE = Path(__file__).resolve().parents[2] / "data" / "usage.sqlite"
SALT = "istanbul-trip-planner"   # so the stored ids can't be matched back to an address


def _db_url():
    try:
        return st.secrets.get("usage_db_url")
    except Exception:   # no secrets file at all
        return None


def _connect():
    """Returns (connection, placeholder) for Postgres or the local SQLite file."""
    url = _db_url()
    if url:
        import psycopg2   # only needed online
        return psycopg2.connect(url, connect_timeout=5), "%s"
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_FILE), "?"


def _ensure(con):
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS visits (day TEXT NOT NULL, visitor TEXT NOT NULL, PRIMARY KEY (day, visitor))")
    cur.execute("CREATE TABLE IF NOT EXISTS events (ts TEXT NOT NULL, visitor TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL, "
                "username TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, name TEXT NOT NULL, pw TEXT NOT NULL, "
                "created TEXT NOT NULL, tour_done INTEGER NOT NULL DEFAULT 0)")
    con.commit()
    # events tables made before accounts existed have no username column yet
    try:
        cur.execute("SELECT username FROM events WHERE 1 = 0")
    except Exception:
        con.rollback()
        cur.execute("ALTER TABLE events ADD COLUMN username TEXT")
        con.commit()


def _visitor_id() -> str:
    """The same device on the same day gives the same id; it is a salted hash, never the address itself."""
    ctx = st.context
    ip = (ctx.headers.get("X-Forwarded-For") or "").split(",")[0].strip() or getattr(ctx, "ip_address", None) or ""
    agent = ctx.headers.get("User-Agent") or ""
    if not ip:   # no address visible: fall back to this browser session
        ip = st.session_state.setdefault("_visitor_session", hashlib.sha256(str(id(st.session_state)).encode()).hexdigest())
    return hashlib.sha256(f"{SALT}|{ip}|{agent}".encode()).hexdigest()[:16]


def record_visit() -> None:
    """Call once per page run; it writes at most once per browser session."""
    if st.session_state.get("_visit_logged"):
        return
    st.session_state._visit_logged = True
    try:
        con, ph = _connect()
        with con:
            _ensure(con)
            con.cursor().execute(
                f"INSERT INTO visits (day, visitor) VALUES ({ph}, {ph}) ON CONFLICT (day, visitor) DO NOTHING",
                (dt.date.today().isoformat(), _visitor_id()))
        con.close()
        visit_stats.clear()
    except Exception as e:   # counting must never break the app
        st.session_state._visit_error = str(e)


@st.cache_data(ttl=60, show_spinner=False)
def visit_stats() -> dict | None:
    """Total visitors, today's, and visitors per day for the last 30 days. None if the count can't be read."""
    try:
        con, ph = _connect()
        _ensure(con)
        cur = con.cursor()
        today = dt.date.today()
        cur.execute("SELECT COUNT(DISTINCT visitor) FROM visits")
        total = cur.fetchone()[0]
        cur.execute(f"SELECT day, COUNT(*) FROM visits WHERE day >= {ph} GROUP BY day", ((today - dt.timedelta(days=29)).isoformat(),))
        rows = dict(cur.fetchall())
        con.close()
    except Exception:
        return None
    days = pd.date_range(today - dt.timedelta(days=29), today)
    per_day = pd.DataFrame({"day": days, "visitors": [rows.get(d.date().isoformat(), 0) for d in days]})
    return {"total": int(total), "today": int(rows.get(today.isoformat(), 0)),
            "week": int(per_day["visitors"].tail(7).sum()), "per_day": per_day, "lasting": bool(_db_url())}


# ---------- planner events: picks and "Good pick?" answers ----------
MODES = ("Save money", "Balanced", "Enjoy")
MAX_EVENTS_PER_SESSION = 300


def _num(v, lo, hi, kind=float):
    """A number inside [lo, hi], or None. The events come from the browser, so nothing is trusted as it is."""
    try:
        v = kind(v)
    except (TypeError, ValueError):
        return None
    return v if lo <= v <= hi else None


def _clean(ev) -> dict | None:
    """Keeps only the expected fields with sane values; anything else is dropped."""
    if not isinstance(ev, dict) or ev.get("kind") not in ("pick", "feedback"):
        return None
    k, mode = _num(ev.get("k"), 0, 4, int), ev.get("mode")
    if k is None or mode not in MODES:
        return None
    if ev["kind"] == "feedback":
        good, sid = _num(ev.get("good"), 0, 1, int), str(ev.get("id", ""))
        if good is None or not re.fullmatch(r"\d{1,25}", sid):
            return None
        return {"kind": "feedback", "k": k, "good": good, "id": sid, "mode": mode}
    f = ev.get("f")
    if not isinstance(f, list) or not 2 <= len(f) <= 5 or k >= len(f):
        return None
    rows = [[_num(v, -1, 2) for v in row] for row in f if isinstance(row, list) and len(row) == 6]
    if len(rows) != len(f) or any(v is None for row in rows for v in row):
        return None
    ids = [str(i) for i in ev.get("ids", [])][:5]
    sights = ev.get("sights") if isinstance(ev.get("sights"), list) else []
    return {"kind": "pick", "k": k, "mode": mode, "f": rows, "ids": [i for i in ids if re.fullmatch(r"\d{1,25}", i)],
            "days": _num(ev.get("days"), 1, 7, int), "guests": _num(ev.get("guests"), 1, 16, int),
            "swapped": bool(ev.get("swapped")), "long": bool(ev.get("long")),
            "sights": sorted({v for v in (_num(x, 0, 200, int) for x in sights[:40]) if v is not None})}


def record_events(events) -> int:
    """Stores the planner's events (a list sent by the page). Returns how many were kept."""
    if not isinstance(events, list):
        return 0
    seen = st.session_state.setdefault("_events_logged", 0)
    clean = [e for e in map(_clean, events[:30]) if e][: max(0, MAX_EVENTS_PER_SESSION - seen)]
    if not clean:
        return 0
    try:
        con, ph = _connect()
        with con:
            _ensure(con)
            now, visitor = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), _visitor_id()
            user = (st.session_state.get("auth") or {}).get("user")   # None for guests
            con.cursor().executemany(f"INSERT INTO events (ts, visitor, kind, payload, username) VALUES ({ph}, {ph}, {ph}, {ph}, {ph})",
                                     [(now, visitor, e["kind"], json.dumps(e), user) for e in clean])
        con.close()
    except Exception as e:   # storing must never break the app
        st.session_state._events_error = str(e)
        return 0
    st.session_state._events_logged = seen + len(clean)
    load_events.clear()
    return len(clean)


@st.cache_data(ttl=120, show_spinner=False)
def load_events(kind: str) -> list[dict]:
    """Every stored event of one kind ("pick" or "feedback"), oldest first, each with its visitor id."""
    try:
        con, ph = _connect()
        _ensure(con)
        cur = con.cursor()
        cur.execute(f"SELECT visitor, payload, username FROM events WHERE kind = {ph} ORDER BY ts", (kind,))
        rows = cur.fetchall()
        con.close()
    except Exception:
        return []
    return [{**json.loads(p), "visitor": v, "user": u} for v, p, u in rows]
