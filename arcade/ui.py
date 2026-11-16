"""Small Streamlit helpers shared by all the screens.

How clicks and walking keys reach Python
----------------------------------------
Streamlit pictures are not clickable by themselves, and Streamlit cannot tell
that a key is being held down. INPUT_JS below is the only JavaScript in the
project. It does two small jobs:

  * it listens for clicks on the game picture and tells Python where the
    click landed, already converted to the 960x540 coordinates the drawing
    code uses (read it with click());
  * while W, A, S, D or an arrow key is held down in the arcade room, it
    tells Python "one step that way" about ten times a second (read it
    with move()).
"""

from __future__ import annotations

import base64
import io
import time

import streamlit as st

from arcade.art import scenes
from arcade.config import ANIMATIONS, FADE_DELAY, FADE_STEPS, FRAME_DELAY, GAME_TITLE, SCREEN_H, SCREEN_W

SCREEN_KEY = "game_screen"

_CSS = f"""
<style>
.stApp {{ background: #0d0a1f; }}
.block-container {{ max-width: 992px; padding: 1.2rem 1rem 1rem 1rem; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.stMain:focus, .stMain:focus-visible {{ outline: none !important; }}
img {{ image-rendering: pixelated; }}
.st-key-{SCREEN_KEY} img {{ cursor: pointer; }}
.st-key-{SCREEN_KEY} [data-testid="stElementToolbar"] {{ display: none; }}
.st-key-click_catcher {{ display: none; }}
.stButton button, .stFormSubmitButton button {{
    border-radius: 0; border: 3px solid #3a2f6b; font-weight: 700;
    text-transform: uppercase; letter-spacing: .04em;
}}
.stButton button:hover, .stFormSubmitButton button:hover {{ border-color: #ffe94a; color: #ffe94a; }}
button[data-testid^="stBaseButton-primary"]:not(:disabled) {{ border-color: #fff3a8; }}
button[data-testid^="stBaseButton-primary"]:not(:disabled),
button[data-testid^="stBaseButton-primary"]:not(:disabled) * {{ color: #16122b !important; }}
.rarity-legendary {{ color: #ffb81a; }} .rarity-rare {{ color: #b07aff; }} .rarity-common {{ color: #9df0c4; }}
</style>
"""

ROOM_MARKER = "hub_use"  # key of a button that only exists in the arcade room
STEP_MS = 100  # how often a held key sends another step

INPUT_JS = f"""
export default function (component) {{
    const {{ setTriggerValue }} = component;

    const onClick = (event) => {{
        const picture = event.target;
        if (!(picture instanceof HTMLImageElement) || !picture.closest(".st-key-{SCREEN_KEY}")) return;
        const box = picture.getBoundingClientRect();
        if (!box.width || !box.height) return;
        setTriggerValue("click", {{
            x: ((event.clientX - box.left) / box.width) * {SCREEN_W},
            y: ((event.clientY - box.top) / box.height) * {SCREEN_H},
        }});
    }};

    const STEPS = {{
        w: [0, -1], a: [-1, 0], s: [0, 1], d: [1, 0],
        arrowup: [0, -1], arrowleft: [-1, 0], arrowdown: [0, 1], arrowright: [1, 0],
    }};
    const held = [];
    let timer = null;
    const inRoom = () => document.querySelector(".st-key-{ROOM_MARKER}") !== null;
    const sendStep = () => {{
        if (!held.length || !inRoom()) return;
        const [dx, dy] = STEPS[held[held.length - 1]];
        setTriggerValue("move", {{ dx, dy }});
    }};
    const stopWalking = () => {{
        held.length = 0;
        if (timer) {{ clearInterval(timer); timer = null; }}
    }};
    const onKeyDown = (event) => {{
        const key = (event.key || "").toLowerCase();
        if (!(key in STEPS) || event.repeat || event.ctrlKey || event.metaKey || event.altKey) return;
        const tag = (event.target.tagName || "").toLowerCase();
        if (tag === "input" || tag === "textarea" || !inRoom()) return;
        if (key.startsWith("arrow")) event.preventDefault();  // do not scroll the page
        if (!held.includes(key)) held.push(key);
        sendStep();
        if (!timer) timer = setInterval(sendStep, {STEP_MS});
    }};
    const onKeyUp = (event) => {{
        const index = held.indexOf((event.key || "").toLowerCase());
        if (index >= 0) held.splice(index, 1);
        if (!held.length) stopWalking();
    }};

    document.addEventListener("click", onClick);
    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("keyup", onKeyUp);
    window.addEventListener("blur", stopWalking);
    return () => {{
        document.removeEventListener("click", onClick);
        document.removeEventListener("keydown", onKeyDown);
        document.removeEventListener("keyup", onKeyUp);
        window.removeEventListener("blur", stopWalking);
        stopWalking();
    }};
}}
"""
_input_catcher = st.components.v2.component("arcade_input_catcher", js=INPUT_JS)

_STEPS = {(0, -1), (-1, 0), (0, 1), (1, 0)}


def setup_page() -> None:
    """Call once at the top of every run: page settings, styles and the input listener."""
    st.set_page_config(page_title=GAME_TITLE.title(), page_icon="🕹️", layout="centered")
    st.markdown(_CSS, unsafe_allow_html=True)
    result = _input_catcher(key="click_catcher", on_click_change=lambda: None, on_move_change=lambda: None)
    point, step = result.click, result.move
    st.session_state["_click"] = _as_point(point)
    st.session_state["_move"] = _as_step(step)


def _as_point(value) -> tuple[float, float] | None:
    """Only accept a click that really is a point on the picture."""
    try:
        x, y = float(value["x"]), float(value["y"])
    except (TypeError, KeyError, ValueError):
        return None
    return (x, y) if 0 <= x <= SCREEN_W and 0 <= y <= SCREEN_H else None


def _as_step(value) -> tuple[int, int] | None:
    """Only accept one step up, down, left or right (never a bigger jump)."""
    try:
        step = (int(value["dx"]), int(value["dy"]))
    except (TypeError, KeyError, ValueError):
        return None
    return step if step in _STEPS else None


def click() -> tuple[float, float] | None:
    """Where the game picture was clicked just now (960x540 coordinates), or None."""
    return st.session_state.get("_click")


def move() -> tuple[int, int] | None:
    """The step asked for by a walking key just now, as (dx, dy), or None."""
    return st.session_state.get("_move")


def screen():
    """The place where the game picture goes. Use show() to put a picture in it."""
    return st.container(key=SCREEN_KEY).empty()


def _inline(img) -> str:
    """The picture as text that the browser can show straight away.

    PNG keeps the pixel art sharp. Sending the picture inline (instead of as a
    separate file the browser has to fetch) is what keeps animations smooth:
    a frame can never arrive after it has already been replaced.
    """
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", compress_level=3)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def show(slot, img) -> None:
    """Put a picture in a slot made by screen().

    After fade_next(), the picture shown before fades to black first and this
    one fades in from black (task A1).
    """
    previous = st.session_state.get("_last_frame")
    if st.session_state.pop("_fade_next", False) and ANIMATIONS and previous is not None:
        for frame in scenes.fade_through_black(previous, img, FADE_STEPS):
            slot.image(_inline(frame), width="stretch")
            time.sleep(FADE_DELAY)
    slot.image(_inline(img), width="stretch")
    st.session_state["_last_frame"] = img


def fade_next() -> None:
    """Call just before changing screen: the next picture arrives through black instead of with a cut."""
    st.session_state["_fade_next"] = True


def picture(img) -> None:
    """Show a picture right here on the page (banners, item tiles, portraits)."""
    st.image(_inline(img), width="stretch")


def play_frames(slot, frames, delay: float = FRAME_DELAY) -> None:
    """Show pictures one after another. Skipped when animations are switched off."""
    if not ANIMATIONS:
        return
    for frame in frames:
        show(slot, frame)
        time.sleep(delay)


def button(label: str, key: str, shortcut: str | None = None, **kwargs) -> bool:
    """A button that can also be pressed with a keyboard key."""
    kwargs.setdefault("width", "stretch")
    return st.button(label, key=key, shortcut=shortcut, **kwargs)


def hit(regions, point):
    """Which clickable region (if any) contains the point. Later regions lie on top."""
    if point is None:
        return None
    x, y = point
    for (left, top, right, bottom), action in reversed(list(regions)):
        if left <= x <= right and top <= y <= bottom:
            return action
    return None
