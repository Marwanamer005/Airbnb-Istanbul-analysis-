"""Accounts: sign up, sign in, the admin login and "stay signed in" tokens.

Where accounts live: the same database as the visitor count (core/usage.py), so the deployed app needs the
`usage_db_url` secret (a Postgres link, e.g. a free Supabase database), or every account is lost when
Streamlit Cloud restarts the app.

Passwords are never stored: only a salted PBKDF2 hash (200,000 rounds of SHA-256). The admin is not an account
in the database; its password is the `admin_password` secret (.streamlit/secrets.toml locally, the app's
Secrets box on Streamlit Cloud), so it never appears in the code on GitHub.
"""
import base64
import datetime as dt
import hashlib
import hmac
import re
import secrets
import time

import streamlit as st

from core.usage import DB_FILE, _connect, _ensure

ADMIN = "admin"
TOKEN_DAYS = 30
MAX_FAILS = 8          # wrong passwords allowed per browser session
USERNAME_RE = re.compile(r"[a-z0-9_.-]{3,24}")


def _secret(name: str):
    try:
        return st.secrets.get(name)
    except Exception:   # no secrets file at all
        return None


def _auth_key() -> bytes:
    """Key that signs the "stay signed in" tokens: the `auth_secret` secret, or a random one kept next to the
    local database (Streamlit Cloud deletes that file on restart, which only means people sign in again)."""
    key = _secret("auth_secret")
    if key:
        return str(key).encode()
    path = DB_FILE.parent / ".auth_secret"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(secrets.token_hex(32))
    return path.read_text().strip().encode()


def _hash(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
    return f"{salt}${digest}"


def _check(password: str, stored: str) -> bool:
    salt, _ = stored.split("$", 1)
    return hmac.compare_digest(_hash(password, salt), stored)


def make_token(username: str) -> str:
    exp = int(time.time()) + TOKEN_DAYS * 86400
    body = f"{username}|{exp}"
    sig = hmac.new(_auth_key(), body.encode(), hashlib.sha256).hexdigest()[:32]
    return base64.urlsafe_b64encode(f"{body}|{sig}".encode()).decode()


def read_token(token: str) -> str | None:
    """The username in a valid, unexpired token, else None."""
    try:
        username, exp, sig = base64.urlsafe_b64decode(str(token).encode()).decode().split("|")
        good = hmac.new(_auth_key(), f"{username}|{exp}".encode(), hashlib.sha256).hexdigest()[:32]
        return username if hmac.compare_digest(sig, good) and int(exp) > time.time() else None
    except Exception:
        return None


def _user_row(username: str):
    con, ph = _connect()
    _ensure(con)
    cur = con.cursor()
    cur.execute(f"SELECT username, name, pw, tour_done FROM users WHERE username = {ph}", (username,))
    row = cur.fetchone()
    con.close()
    return row


def _signed_in(username: str, name: str, role: str, tour_done: bool, remember: bool = False) -> dict:
    """Signs this browser session in. A "stay signed in" token is only handed out when the person ticked
    "Keep me signed in", and never for the admin (token None tells the page to forget any old one)."""
    st.session_state.auth = {"user": username, "name": name, "role": role}
    token = make_token(username) if remember and role != "admin" else None
    return {"ok": True, "user": username, "name": name, "role": role, "tour": not tour_done, "token": token}


def sign_up(username: str, name: str, password: str, remember: bool = False) -> dict:
    username, name = str(username or "").strip().lower(), str(name or "").strip()[:30]
    if not USERNAME_RE.fullmatch(username):
        return {"ok": False, "msg": "Usernames are 3 to 24 letters, numbers, dots, dashes or underscores."}
    if username == ADMIN:
        return {"ok": False, "msg": "That username is taken."}
    if len(str(password or "")) < 8:
        return {"ok": False, "msg": "Use a password of at least 8 characters."}
    name = name or username
    try:
        con, ph = _connect()
        with con:
            _ensure(con)
            cur = con.cursor()
            cur.execute(f"SELECT 1 FROM users WHERE username = {ph}", (username,))
            if cur.fetchone():
                return {"ok": False, "msg": "That username is taken."}
            cur.execute(f"INSERT INTO users (username, name, pw, created, tour_done) VALUES ({ph}, {ph}, {ph}, {ph}, 0)",
                        (username, name, _hash(password), dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")))
        con.close()
    except Exception:
        return {"ok": False, "msg": "Accounts aren't available right now. You can continue as a guest."}
    return _signed_in(username, name, "user", False, remember)


def sign_in(username: str, password: str, remember: bool = False) -> dict:
    fails = st.session_state.get("_auth_fails", 0)
    if fails >= MAX_FAILS:
        return {"ok": False, "msg": "Too many wrong tries. Reload the page to try again."}
    username, password = str(username or "").strip().lower(), str(password or "")
    if username == ADMIN:
        admin_pw = _secret("admin_password")
        if admin_pw and hmac.compare_digest(password.encode(), str(admin_pw).encode()):
            return _signed_in(ADMIN, "Admin", "admin", True)
    else:
        try:
            row = _user_row(username)
        except Exception:
            return {"ok": False, "msg": "Accounts aren't available right now. You can continue as a guest."}
        if row and _check(password, row[2]):
            return _signed_in(row[0], row[1], "user", bool(row[3]), remember)
    st.session_state._auth_fails = fails + 1
    time.sleep(0.6)   # slows down password guessing
    return {"ok": False, "msg": "That username and password don't match."}


def resume(token: str) -> dict:
    """Signs a returning browser back in from its saved token."""
    username = read_token(token)
    if username == ADMIN:   # the admin always signs in with the password
        return {"ok": False}
    if username:
        try:
            row = _user_row(username)
        except Exception:
            row = None
        if row:
            return _signed_in(row[0], row[1], "user", bool(row[3]), remember=True)   # keeps the token fresh
    return {"ok": False}


def sign_out() -> None:
    st.session_state.pop("auth", None)


def tour_done() -> None:
    user = current_user()
    if not user or user == ADMIN:
        return
    try:
        con, ph = _connect()
        with con:
            con.cursor().execute(f"UPDATE users SET tour_done = 1 WHERE username = {ph}", (user,))
        con.close()
    except Exception:
        pass


def current_user() -> str | None:
    return (st.session_state.get("auth") or {}).get("user")


def is_admin() -> bool:
    return (st.session_state.get("auth") or {}).get("role") == "admin"


@st.cache_data(ttl=120, show_spinner=False)
def account_count() -> int | None:
    try:
        con, _ = _connect()
        _ensure(con)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        n = cur.fetchone()[0]
        con.close()
        return int(n)
    except Exception:
        return None
