"""Small Streamlit helpers shared by all the screens.

How clicks reach Python
-----------------------
Streamlit pictures are not clickable by themselves. INPUT_JS below listens for
clicks on the game picture and tells Python where the click landed, already
converted to the 960x540 coordinates the drawing code uses (read it with click()).
Walking in the arcade room is handled by the room itself (arcade/room.py).
"""

from __future__ import annotations

import base64
import io
import time

import streamlit as st

from arcade.art import effects, scenes
from arcade.config import ANIMATIONS, FADE_DELAY, FADE_STEPS, FRAME_DELAY, GAME_TITLE, GLOW, SCREEN_H, SCREEN_W

SCREEN_KEY = "game_screen"

TITLE_KEY = "title_screen"

# Look of everything around the game picture (idea 1 of the visual update).
# The pixel font is Jersey 10 (SIL Open Font License), loaded from Google Fonts. The pictures use it too (V4).
_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Jersey+10&display=swap');
:root {{
    --ink: #0d0a1f; --panel: #17123a; --line: #3a2f6b;
    --pink: #ff4fa3; --cyan: #3ad6ff; --yellow: #ffe94a; --text: #f3ead2;
}}
.stApp {{
    background:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(255, 79, 163, .22), transparent 70%),
        radial-gradient(ellipse 70% 45% at 50% 110%, rgba(58, 214, 255, .16), transparent 70%),
        repeating-linear-gradient(0deg, rgba(255, 255, 255, .025) 0 1px, transparent 1px 4px),
        var(--ink);
    background-attachment: fixed;
}}
.stApp, .stApp p, .stApp label, .stApp input, .stApp button, [data-testid="stToast"] {{
    font-family: "Jersey 10", monospace !important;
}}
/* the game is as big as the window allows: the picture (16:9) plus one row of buttons must fit in the height */
.block-container {{ max-width: min(96vw, calc((100vh - 120px) * 16 / 9)); padding: .8rem 1rem .6rem 1rem; }}
/* Streamlit fades everything while the script runs; in a game that just looks like the screen going dark */
[data-stale="true"] {{ opacity: 1 !important; transition: none !important; }}
/* Streamlit's own header, menu and footer are not part of the game */
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
#MainMenu, footer, [data-testid="stStatusWidget"] {{ display: none !important; }}
.stMain:focus, .stMain:focus-visible {{ outline: none !important; }}
img {{ image-rendering: pixelated; }}

/* the game picture sits in a glowing frame, like an arcade screen */
.st-key-{SCREEN_KEY} img, .st-key-{TITLE_KEY} img {{
    border-radius: 14px;
    box-shadow: 0 0 0 2px rgba(58, 214, 255, .55), 0 0 24px rgba(58, 214, 255, .35), 0 0 60px rgba(255, 79, 163, .25);
}}
.st-key-{SCREEN_KEY} img {{ cursor: pointer; }}
.st-key-{SCREEN_KEY} [data-testid="stElementToolbar"], .st-key-{TITLE_KEY} [data-testid="stElementToolbar"] {{ display: none; }}
.st-key-click_catcher {{ display: none; }}

/* buttons: neon outlines that light up */
.stButton button, .stFormSubmitButton button {{
    border-radius: 10px; border: 2px solid rgba(58, 214, 255, .45); background: rgba(23, 18, 58, .75);
    color: var(--text); font-weight: 600; letter-spacing: .03em; text-transform: none; font-size: 1.05rem;
    transition: border-color .12s, box-shadow .12s, transform .12s, background .12s;
}}
.stButton button:hover:not(:disabled), .stFormSubmitButton button:hover:not(:disabled) {{
    border-color: var(--cyan); color: #ffffff; background: rgba(58, 214, 255, .12);
    box-shadow: 0 0 14px rgba(58, 214, 255, .45); transform: translateY(-1px);
}}
.stButton button:disabled {{ border-color: rgba(58, 47, 107, .8); background: rgba(23, 18, 58, .45); opacity: .55; }}
.stButton button p, .stFormSubmitButton button p {{ font-size: 1.3rem; letter-spacing: .04em; }}
button[data-testid^="stBaseButton-primary"]:not(:disabled) {{
    border: 2px solid #ffd0e6; background: linear-gradient(135deg, var(--pink), #ff9f1a);
    box-shadow: 0 0 16px rgba(255, 79, 163, .45);
}}
button[data-testid^="stBaseButton-primary"]:not(:disabled):hover {{
    background: linear-gradient(135deg, #ff6fb5, #ffb84a); box-shadow: 0 0 24px rgba(255, 79, 163, .7);
}}
button[data-testid^="stBaseButton-primary"]:not(:disabled),
button[data-testid^="stBaseButton-primary"]:not(:disabled) * {{ color: #1a0f2e !important; }}

/* the name field on the title screen */
.stTextInput input {{
    border-radius: 10px; background: rgba(23, 18, 58, .9); color: #ffffff; font-size: 1.5rem;
    border: 2px solid rgba(255, 79, 163, .6); letter-spacing: .08em;
}}
.stTextInput input:focus {{ border-color: var(--pink); box-shadow: 0 0 16px rgba(255, 79, 163, .45); }}
[data-testid="stCaptionContainer"] {{ color: #b9b0e8; text-align: center; }}
[data-testid="stToast"] {{ background: var(--panel); border: 2px solid var(--yellow); border-radius: 12px; }}
.rarity-legendary {{ color: #ffb81a; }} .rarity-rare {{ color: #b07aff; }} .rarity-common {{ color: #9df0c4; }}
</style>
"""

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
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
}}
"""
_input_catcher = st.components.v2.component("arcade_input_catcher", js=INPUT_JS)


def setup_page() -> None:
    """Call once at the top of every run: page settings, styles and the input listener."""
    st.set_page_config(page_title=GAME_TITLE.title(), page_icon="🕹️", layout="wide")
    st.markdown(_CSS, unsafe_allow_html=True)
    result = _input_catcher(key="click_catcher", on_click_change=lambda: None)
    st.session_state["_click"] = _as_point(result.click)


def _as_point(value) -> tuple[float, float] | None:
    """Only accept a click that really is a point on the picture."""
    try:
        x, y = float(value["x"]), float(value["y"])
    except (TypeError, KeyError, ValueError):
        return None
    return (x, y) if 0 <= x <= SCREEN_W and 0 <= y <= SCREEN_H else None


def click() -> tuple[float, float] | None:
    """Where the game picture was clicked just now (960x540 coordinates), or None."""
    return st.session_state.get("_click")


class Slot:
    """The place on the page where a picture goes. Use show() to put a picture in it.

    The first picture goes straight into the container, and every later picture
    in the same run replaces it in place. We do not use st.empty() here: an empty
    placeholder makes the browser remove the old picture and wait for the new
    one, so every timed redraw (idle bots, title animation) made the game blink.
    """

    def __init__(self, key: str):
        self.key = key
        self._place = None

    def image(self, data: str, **kwargs) -> None:
        where = st.container(key=self.key) if self._place is None else self._place
        self._place = where.image(data, **kwargs)


def screen(key: str = SCREEN_KEY) -> Slot:
    """The place where the game picture goes. Use show() to put a picture in it."""
    return Slot(key)


def _inline(img) -> str:
    """The picture as text that the browser can show straight away.

    WebP at high quality is about three times smaller than PNG for these pictures
    (the glow and the lighting are soft gradients) and quicker to make, so every
    frame reaches the browser sooner. Sending the picture inline (instead of as a
    separate file the browser has to fetch) keeps animations smooth: a frame can
    never arrive after it has already been replaced.
    """
    if GLOW:  # every picture gets the soft neon glow just before it is sent
        img = effects.neon_glow(img)
    buffer = io.BytesIO()
    img.save(buffer, format="WEBP", quality=92, method=0)
    return "data:image/webp;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


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
