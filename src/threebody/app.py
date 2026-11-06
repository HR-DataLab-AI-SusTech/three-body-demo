"""Three bodies: the Streamlit page. Simulate a setup, save it to the gallery, rate others."""

from __future__ import annotations

import hmac
import os
import secrets
import time

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from threebody import store
from threebody.config import SetupConfig
from threebody.physics import TooCloseError, Trajectory
from threebody.presets import PRESETS

COLOURS = ("#d4104b", "#1f6feb", "#f2a900")  # HR red first
SAVES_PER_MINUTE = 3

st.set_page_config(page_title="Three bodies", page_icon="🪐", layout="wide")


@st.cache_resource
def engine():
    return store.engine_from_env()


@st.cache_data(max_entries=200, show_spinner="Integrating…")
def run(config_json: str) -> Trajectory:
    return SetupConfig.model_validate_json(config_json).run()


def figure(traj: Trajectory) -> go.Figure:
    x, y = traj.positions[..., 0], traj.positions[..., 1]
    pad = 0.15 * max(np.ptp(x), np.ptp(y), 1.0)
    trail = 25
    fig = go.Figure()
    for b in range(3):  # the whole path, faint
        fig.add_trace(
            go.Scatter(
                x=x[:, b],
                y=y[:, b],
                mode="lines",
                hoverinfo="skip",
                line={"color": COLOURS[b], "width": 1},
                opacity=0.25,
                showlegend=False,
            )
        )
    for b in range(3):  # the moving bodies and their recent trail
        fig.add_trace(
            go.Scatter(
                x=x[:1, b],
                y=y[:1, b],
                mode="lines+markers",
                name=f"Body {b + 1}",
                line={"color": COLOURS[b], "width": 2},
                marker={"size": [14], "color": COLOURS[b]},
            )
        )
    frames = []
    for f in range(0, len(traj.times), 2):
        lo = max(0, f - trail)
        frames.append(
            go.Frame(
                name=str(f),
                traces=[3, 4, 5],
                data=[
                    go.Scatter(
                        x=x[lo : f + 1, b],
                        y=y[lo : f + 1, b],
                        marker={"size": [0] * (f - lo) + [14]},
                    )
                    for b in range(3)
                ],
            )
        )
    fig.frames = frames
    fig.update_layout(
        height=460,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        legend={"orientation": "h"},
        xaxis={"range": [x.min() - pad, x.max() + pad], "showgrid": False, "zeroline": False},
        yaxis={
            "range": [y.min() - pad, y.max() + pad],
            "showgrid": False,
            "zeroline": False,
            "scaleanchor": "x",
        },
        updatemenus=[
            {
                "type": "buttons",
                "x": 0,
                "y": 1.02,
                "xanchor": "left",
                "direction": "left",
                "buttons": [
                    {
                        "label": "▶ Play",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": 30, "redraw": False},
                                "transition": {"duration": 0},
                                "fromcurrent": True,
                            },
                        ],
                    },
                    {
                        "label": "⏸ Pause",
                        "method": "animate",
                        "args": [[None], {"frame": {"duration": 0}, "mode": "immediate"}],
                    },
                ],
            }
        ],
    )
    return fig


# ── state ───────────────────────────────────────────────────────────────────────────────────────
ss = st.session_state
ss.setdefault("visitor", secrets.token_urlsafe(24))  # one anonymous id per browser session
ss.setdefault("config", PRESETS["Figure-eight"].config)
ss.setdefault("form_version", 0)  # bumped when a setup is loaded, so the inputs take its values
ss.setdefault("saves", [])
if notice := ss.pop("notice", None):
    st.toast(notice)


def load(config: SetupConfig) -> None:
    ss.config = config
    ss.form_version += 1


# ── the setup ───────────────────────────────────────────────────────────────────────────────────
st.title("🪐 Three bodies")
st.caption(
    "Three masses under Newtonian gravity. Pick one of the famous orbits, change it, watch it, "
    "and save it to the gallery for others to rate."
)

with st.sidebar:
    st.header("Setup")
    preset = st.selectbox("Start from a famous orbit", ["—", *PRESETS])
    if preset != "—":
        st.caption(PRESETS[preset].description)
        if st.button("Load it", use_container_width=True):
            load(PRESETS[preset].config)
            st.rerun()

    cfg, v = ss.config, ss.form_version
    masses, positions, velocities = [], [], []
    for b in range(3):
        with st.expander(f"Body {b + 1}", expanded=b == 0):
            masses.append(
                st.number_input("Mass", 0.01, 100.0, float(cfg.masses[b]), 0.1, key=f"m{b}{v}")
            )
            c1, c2 = st.columns(2)
            positions.append(
                (
                    c1.number_input(
                        "x", -10.0, 10.0, float(cfg.positions[b][0]), 0.05, key=f"x{b}{v}"
                    ),
                    c2.number_input(
                        "y", -10.0, 10.0, float(cfg.positions[b][1]), 0.05, key=f"y{b}{v}"
                    ),
                )
            )
            velocities.append(
                (
                    c1.number_input(
                        "vx", -10.0, 10.0, float(cfg.velocities[b][0]), 0.01, key=f"vx{b}{v}"
                    ),
                    c2.number_input(
                        "vy", -10.0, 10.0, float(cfg.velocities[b][1]), 0.01, key=f"vy{b}{v}"
                    ),
                )
            )
    duration = st.number_input(
        "How long to watch (time units)", 1.0, 100.0, float(cfg.duration), 1.0, key=f"d{v}"
    )

    admin_code = os.environ.get("ADMIN_CODE", "")
    with st.expander("Admin"):
        entered = st.text_input("Code", type="password")
    is_admin = bool(admin_code) and hmac.compare_digest(entered.encode(), admin_code.encode())

current = SetupConfig(
    masses=tuple(masses),
    positions=tuple(positions),  # type: ignore[arg-type]
    velocities=tuple(velocities),
    duration=duration,
)

play, gallery_tab = st.tabs(["Simulate", "Gallery"])

with play:
    try:
        traj = run(current.model_dump_json())
    except TooCloseError:
        st.warning(
            "Two bodies come so close that following them would take too long. "
            "Move them apart a little, or watch for a shorter time."
        )
    else:
        st.plotly_chart(figure(traj), use_container_width=True)
        st.caption(
            f"{len(traj.times)} frames over {current.duration:g} time units · energy kept to "
            f"{traj.energy_drift:.1e} of its start (adaptive 8th-order Runge-Kutta, G = 1)"
        )

    with st.form("save", clear_on_submit=True):
        st.subheader("Save it to the gallery")
        name = st.text_input("Name", max_chars=store.NAME_MAX)
        description = st.text_area("What happens? (optional)", max_chars=store.DESCRIPTION_MAX)
        if st.form_submit_button("Save"):
            now = time.time()
            ss.saves = [t for t in ss.saves if now - t < 60]
            if len(ss.saves) >= SAVES_PER_MINUTE:
                st.warning("That is a lot of saving; try again in a minute.")
            elif not name.strip():
                st.warning("Give it a name first.")
            else:
                try:
                    store.save_setup(engine(), name, description, current)
                    ss.saves.append(now)
                    st.success(f"Saved “{name.strip()}”. Find it in the gallery.")
                except store.GalleryFullError:
                    st.error("The gallery is full for now.")

# ── the gallery ─────────────────────────────────────────────────────────────────────────────────
with gallery_tab:
    c1, c2 = st.columns(2)
    which = c1.radio(
        "Show",
        ["featured", "visitors", "all"],
        horizontal=True,
        format_func={"featured": "Famous orbits", "visitors": "From visitors", "all": "All"}.get,
    )
    order = c2.radio(
        "Sort",
        ["best", "newest"],
        horizontal=True,
        format_func=lambda o: "Best rated" if o == "best" else "Newest",
    )
    items = store.gallery(engine(), order, which=which)  # type: ignore[arg-type]
    if not items:
        st.info("Nothing saved yet. Be the first: simulate something and save it.")
    for item in items:
        with st.container(border=True):
            left, right = st.columns([3, 2])
            score = f"★ {item.rating:.1f} ({item.votes})" if item.rating else "not rated yet"
            badge = " · ⭐ famous orbit" if item.featured else ""
            left.markdown(f"**{item.name}** · {score}{badge}")
            if item.description:
                left.caption(item.description)
            left.caption(
                f"masses {', '.join(f'{m:g}' for m in item.config.masses)} · "
                f"{item.config.duration:g} time units"
                + ("" if item.featured else f" · saved {item.created_at:%d %b %Y}")
            )
            if right.button("Load and play", key=f"load{item.id}"):
                load(item.config)
                st.rerun()
            stars = right.feedback("stars", key=f"rate{item.id}")
            if stars is not None and not ss.get(f"rated{item.id}"):
                ss[f"rated{item.id}"] = True
                if store.rate(engine(), item.id, ss.visitor, stars + 1):
                    ss.notice = f"Thanks — you gave “{item.name}” {stars + 1} ★"
                else:
                    ss.notice = "You already rated this one."
                st.rerun()  # read the gallery again, so the new average shows
            if (
                is_admin
                and not item.featured
                and right.button("Delete", key=f"del{item.id}", type="secondary")
            ):
                store.delete_setup(engine(), item.id)
                st.rerun()

st.divider()
st.caption(
    "Running on the HR DataLab's app hosting: Streamlit and PostgreSQL in Docker, deployed "
    "by CI to Coolify. Source: "
    "[github.com/krinya/three-body-demo]"
    "(https://github.com/krinya/three-body-demo)"
)
