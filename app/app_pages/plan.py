"""The planner: the full-screen map from the design, filled with the real listings and model outputs."""
import re
from urllib.parse import urlparse

import streamlit as st

from core import auth
from core.data import load_sights
from core.learning import learned_weights, real_cooc
from core.planner_html import build_planner
from core.usage import record_events

# The page address is fixed once per visit: the reruns caused by the bridge below must never reload the planner
# (that would wipe the traveller's plan).
if "planner_src" not in st.session_state:
    version = build_planner()
    # A shared trip link is the app address with ?trip=<code>; the planner reads the code from its own address.
    trip = st.query_params.get("trip", "")
    hash_part = f"#trip={trip}" if re.fullmatch(r"[A-Za-z0-9_-]{8,2000}", trip) else ""
    # On Streamlit Community Cloud the app itself lives under /~/+/ (the page around it is Streamlit's own),
    # so the static files are served from there too.
    path = urlparse(st.context.url or "").path
    base = path[:path.index("/~/+/") + 5] if "/~/+/" in path else "/"
    st.session_state.planner_src = f"{base}app/static/planner.html?v={version}{hash_part}"

# ---------- the bridge between the planner page and Python ----------
# The planner (an iframe on the same site) posts messages to this page: sign in / sign up, "hello" when it loads,
# which stay people plan with and their "Good pick?" answers. This invisible component passes them to Python in
# small batches, and posts Python's answers back into the planner.
_BRIDGE = st.components.v2.component(
    "kervan_bridge",
    js="""
export default function (component) {
  const b = window.__kervanBridge || (window.__kervanBridge = {queue: [], timer: null, sent: new Set()});
  b.send = component.setTriggerValue;   // the latest mount's sender
  // answers from Python: post each one into the planner once
  const frame = document.querySelector('iframe[title="Trip planner map"]');
  for (const msg of (component.data && component.data.out) || []) {
    if (b.sent.has(msg.rid) || !frame || !frame.contentWindow) continue;
    b.sent.add(msg.rid);
    frame.contentWindow.postMessage({kervanReply: msg}, window.location.origin);
  }
  if (b.listening) return;
  b.listening = true;
  window.addEventListener("message", (e) => {
    if (e.origin !== window.location.origin || !e.data || typeof e.data.kervan !== "object") return;
    b.queue.push(e.data.kervan);
    clearTimeout(b.timer);
    b.timer = setTimeout(() => { if (b.send && b.queue.length) b.send("events", b.queue.splice(0, 30)); }, 250);
  });
}
""",
)


def _hello() -> dict:
    """What the planner needs when it loads: weights learned from picks, real-trip suggestions, who is signed in."""
    lw = learned_weights()
    a = st.session_state.get("auth")
    return {"learned": {"n": lw["n"], "balanced": lw["balanced"]} if lw["ready"] else None,
            "cooc": real_cooc(len(load_sights())),
            "auth": {"ok": True, "user": a["user"], "name": a["name"], "role": a["role"], "tour": False} if a else None,
            "signed_out": st.session_state.pop("_signed_out", False)}


def _handle_events():
    events = (st.session_state.get("kervan_bridge") or {}).get("events")
    if not isinstance(events, list):
        return
    out, rest = st.session_state.setdefault("bridge_out", []), []
    for ev in events[:30]:
        if not isinstance(ev, dict):
            continue
        kind, rid = ev.get("kind"), str(ev.get("rid", ""))[:40]
        if kind == "hello":
            out.append({"rid": rid, "kind": "hello", **_hello()})
        elif kind == "signin":
            out.append({"rid": rid, "kind": "auth", **auth.sign_in(ev.get("user"), ev.get("pass"), bool(ev.get("remember")))})
        elif kind == "signup":
            out.append({"rid": rid, "kind": "auth", **auth.sign_up(ev.get("user"), ev.get("name"), ev.get("pass"), bool(ev.get("remember")))})
        elif kind == "resume":
            out.append({"rid": rid, "kind": "resume", **auth.resume(ev.get("token"))})
        elif kind == "signout":
            auth.sign_out()
        elif kind == "tour_done":
            auth.tour_done()
        else:
            rest.append(ev)
    record_events(rest)
    del out[:-10]   # only recent answers are kept; the planner ignores ones it has already seen


_BRIDGE(key="kervan_bridge", data={"out": st.session_state.get("bridge_out", [])}, on_events_change=_handle_events, height=0)

# the map is the whole page: drop the page padding and let the planner fill the window under the menu
st.html("""<style>
  .stMainBlockContainer{padding:3.75rem 0 0 !important;max-width:100% !important}
  .stMain{overflow:hidden}
  .st-key-kervan_bridge{display:none}
  .stElementContainer:has(iframe[title="Trip planner map"]){height:auto !important}
  iframe[title="Trip planner map"]{height:calc(100vh - 3.75rem) !important;border:0;display:block}
</style>""")
st.iframe(st.session_state.planner_src, height=860, alt="Trip planner map")
