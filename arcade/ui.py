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
from arcade.config import ANIMATIONS, FRAME_DELAY, GAME_TITLE, GLOW, SCREEN_H, SCREEN_W

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
/* the game is as big as the window allows: the frame (picture 16:9 + the strip of buttons) fits in the height */
.block-container {{ max-width: min(97vw, calc((100vh - 150px) * 16 / 9)); padding: .5rem .6rem .3rem .6rem; }}

/* Everything of the game sits inside one glowing frame, like an arcade screen: the picture on top and the
   buttons as a control strip at the bottom, inside the frame (app.py puts every screen in game_frame). */
.st-key-game_frame {{
    background: linear-gradient(180deg, #140f36, #0b0820); border: 2px solid rgba(58, 214, 255, .6);
    border-radius: 18px; padding: 10px 12px 12px 12px; gap: 8px !important;
    box-shadow: 0 0 24px rgba(58, 214, 255, .35), 0 0 60px rgba(255, 79, 163, .22), inset 0 0 40px rgba(0, 0, 0, .55);
}}
.st-key-game_frame .stButton button {{ min-height: 2.4rem; padding: 0 .6rem; background: rgba(13, 10, 31, .9); }}
.st-key-game_frame .stButton button p {{ font-size: 1.2rem; }}
.st-key-game_frame [data-testid="stHorizontalBlock"] {{ gap: .5rem; }}
/* Streamlit fades everything while the script runs; in a game that just looks like the screen going dark */
[data-stale="true"] {{ opacity: 1 !important; transition: none !important; }}
/* Streamlit's own header, menu and footer are not part of the game */
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
#MainMenu, footer, [data-testid="stStatusWidget"] {{ display: none !important; }}
.stMain:focus, .stMain:focus-visible {{ outline: none !important; }}
/* after a key press Streamlit draws a faint box around the page (a focus mark); a game does not need it */
.stMain::before {{ box-shadow: none !important; }}
img {{ image-rendering: pixelated; }}

/* the game picture: the frame around it glows (see game_frame), the picture itself just has round corners */
.st-key-{SCREEN_KEY} img, .st-key-{TITLE_KEY} img {{ border-radius: 10px; }}
.st-key-{SCREEN_KEY} img {{ cursor: pointer; }}
/* animations are drawn on a see-through canvas laid exactly over the picture (arcade/table_anim.py) */
.st-key-{SCREEN_KEY}_stage {{ position: relative; gap: 0 !important; }}
.st-key-{SCREEN_KEY}_anim {{ position: absolute !important; inset: 0; z-index: 3; pointer-events: none; }}
.st-key-{SCREEN_KEY}_anim canvas {{ border-radius: 10px; }}
.st-key-{SCREEN_KEY} [data-testid="stElementToolbar"], .st-key-{TITLE_KEY} [data-testid="stElementToolbar"] {{ display: none; }}
.st-key-click_catcher {{ display: none; }}
/* keys with no button on screen (arrows, Space, see keys()): the buttons are on the page, so they hear their key,
   but nobody sees them and they take no room */
[class*="st-key-keys_"] {{ position: absolute !important; width: 1px !important; height: 1px !important;
    overflow: hidden !important; clip-path: inset(50%); opacity: 0; pointer-events: none; }}

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

# The full-screen button (top right) and the F key: the browser shows only the game, like a normal game.
FULLSCREEN_CSS = """
button.fullscreen {
    position: fixed; top: 10px; right: 14px; z-index: 1000; cursor: pointer;
    font: 1.05rem "Jersey 10", monospace; letter-spacing: .04em; color: #f3ead2;
    background: rgba(13, 10, 31, .85); border: 2px solid rgba(58, 214, 255, .5); border-radius: 10px; padding: 4px 10px;
}
button.fullscreen:hover { border-color: #3ad6ff; box-shadow: 0 0 12px rgba(58, 214, 255, .5); }
"""
FULLSCREEN_JS = r"""
export default function (component) {
    const { parentElement } = component;
    if (parentElement.querySelector("button.fullscreen")) return;
    const button = document.createElement("button");
    button.className = "fullscreen";
    parentElement.appendChild(button);
    const toggle = () => document.fullscreenElement ? document.exitFullscreen()
                                                    : document.documentElement.requestFullscreen().catch(() => {});
    const label = () => { button.textContent = document.fullscreenElement ? "EXIT FULL SCREEN (F)" : "FULL SCREEN (F)"; };
    button.addEventListener("click", toggle);
    document.addEventListener("fullscreenchange", label);
    if (!window.__arcadeFullscreenKey) {
        window.__arcadeFullscreenKey = true;
        document.addEventListener("keydown", (event) => {
            const tag = (event.target.tagName || "").toLowerCase();
            if ((event.key || "").toLowerCase() === "f" && !event.repeat && !["input", "textarea"].includes(tag)
                && !event.ctrlKey && !event.metaKey && !event.altKey) {
                document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen().catch(() => {});
            }
        });
    }
    label();
}
"""
_fullscreen = st.components.v2.component("arcade_fullscreen", css=FULLSCREEN_CSS, js=FULLSCREEN_JS)


def setup_page() -> None:
    """Call once at the top of every run: page settings, styles and the input listener."""
    st.set_page_config(page_title=GAME_TITLE.title(), page_icon="🕹️", layout="wide")
    st.markdown(_CSS, unsafe_allow_html=True)
    result = _input_catcher(key="click_catcher", on_click_change=lambda: None)
    st.session_state["_click"] = _as_point(result.click)
    _fullscreen(key="fullscreen_button")
    _fade_style()


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
        self._stage = None
        self._box = None
        self._place = None
        self._over = None

    def _ensure(self) -> None:
        """The stage holds the picture's container and, on top of it, the place for animations (overlay)."""
        if self._stage is None:
            self._stage = st.container(key=f"{self.key}_stage")
            self._box = self._stage.container(key=self.key)

    def image(self, data: str, **kwargs) -> None:
        self._ensure()
        where = self._box if self._place is None else self._place
        self._place = where.image(data, **kwargs)

    def overlay(self):
        """A place laid exactly over the picture (see arcade/table_anim.py). Use it with `with`."""
        self._ensure()
        if self._over is None:
            self._over = self._stage.container(key=f"{self.key}_anim").empty()
        return self._over


def screen(key: str = SCREEN_KEY) -> Slot:
    """The place where the game picture goes. Use show() to put a picture in it."""
    return Slot(key)


def inline(img) -> str:
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

    After fade_next() the picture fades in from black (task A1). The browser does the fade (see
    _fade_style), so it is smooth on every computer instead of a few pictures sent one by one.
    """
    st.session_state.pop("_fade_next", False)
    slot.image(inline(img), width="stretch")
    st.session_state["_last_frame"] = img


def _fade_style() -> None:
    """Every run writes one small style. After fade_next() it switches the game picture to the other of two
    identical fade-in animations; a new animation name makes the browser play the fade again from black."""
    if st.session_state.get("_fade_next") and ANIMATIONS:
        st.session_state["_fade_count"] = st.session_state.get("_fade_count", 0) + 1
    name = f"arcade-fade-{st.session_state.get('_fade_count', 0) % 2}"
    st.markdown(
        f"<style>.st-key-{SCREEN_KEY} img {{ animation: {name} .4s ease-out; }}"
        "@keyframes arcade-fade-0 { from { opacity: 0; } to { opacity: 1; } }"
        "@keyframes arcade-fade-1 { from { opacity: 0; } to { opacity: 1; } }</style>",
        unsafe_allow_html=True,
    )


def fade_next() -> None:
    """Call just before changing screen: the next picture arrives through black instead of with a cut."""
    st.session_state["_fade_next"] = True


def picture(img) -> None:
    """Show a picture right here on the page (banners, item tiles, portraits)."""
    st.image(inline(img), width="stretch")


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


ARROWS = {"Left": "left", "Right": "right", "Up": "up", "Down": "down"}


def keys(name: str, mapping: dict[str, str]) -> str | None:
    """Keys that have no button on screen (the arrow keys, Space): invisible buttons that only listen for them.

    mapping: shortcut -> what it means, for example {"Left": "left", "Space": "choose"}. Returns the meaning of
    the key pressed in this run, or None. Streamlit listens for a shortcut on the whole page, so a button hears
    its key while it is hidden (the CSS in _CSS hides every container whose key starts with keys_).

    Call it on every run of the screen, before the picture is drawn. A run that leaves the buttons out removes them
    from the page, and the keyboard stops working until the next click. Reading the key first lets the same run draw
    the picture with the highlight already moved (no st.rerun(), which would draw everything twice). To ignore a key
    (for example during a bot's turn), call it anyway and drop what it returns.
    """
    pressed = None
    with st.container(key=f"keys_{name}"):
        for shortcut, meaning in mapping.items():
            if st.button(meaning, key=f"keys_{name}_{meaning}", shortcut=shortcut):
                pressed = meaning
    return pressed


def hit(regions, point):
    """Which clickable region (if any) contains the point. Later regions lie on top."""
    if point is None:
        return None
    x, y = point
    for (left, top, right, bottom), action in reversed(list(regions)):
        if left <= x <= right and top <= y <= bottom:
            return action
    return None
