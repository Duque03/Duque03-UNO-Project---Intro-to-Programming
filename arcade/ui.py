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
from functools import lru_cache

import streamlit as st

from arcade.art import effects
from arcade.config import ANIMATIONS, FRAME_DELAY, GAME_TITLE, GLOW, SCREEN_H, SCREEN_W

SCREEN_KEY = "game_screen"

TITLE_KEY = "title_screen"

# Look of everything around the game picture (idea 1 of the visual update).
# The pixel font is Jersey 10 (SIL Open Font License), loaded from Google Fonts. The pictures use it too (V4).
TOAST_SECONDS = 3.6  # how long a little message (toast) stays up

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
/* The game fills the window: the 16:9 picture is as big as the window allows, in the middle, with nothing around it
   (the picture is the whole game: no frame, no bar of buttons, no header). */
.block-container {{ max-width: min(100vw, calc(100vh * 16 / 9)) !important; padding: 0 !important; margin: 0 auto; }}
.stMain {{ min-height: 100vh; display: flex; flex-direction: column; justify-content: center; }}
/* the picture always fits the window, so nothing ever scrolls: a scrollbar that comes and goes (one pixel too much)
   made the picture shrink and grow again, and in full screen everything shook from side to side */
html, body, .stMain, [data-testid="stAppViewContainer"] {{ overflow: hidden !important; }}
.stApp {{ background: #05030d !important; }}
[data-testid="stMainBlockContainer"] > div {{ gap: 0 !important; }}
.st-key-game_frame {{ position: relative; gap: 0 !important; isolation: isolate; }}
/* the previous screen's picture, behind everything, for the first run of a new screen (see backdrop()): until the
   new screen's own picture arrives, this shows instead of the black page. Where the picture always is: the middle. */
.st-key-game_backdrop {{ position: fixed !important; left: 50%; top: 50%; transform: translate(-50%, -50%);
    width: min(100vw, calc(100vh * 16 / 9)) !important; aspect-ratio: 16 / 9; z-index: -1; pointer-events: none;
    background: center / 100% 100% no-repeat; image-rendering: pixelated; }}
.st-key-sound_player, .st-key-music_player {{ display: none; }}  /* the sound and music players (arcade/sound.py) */
/* the countdown of a turn (or of a face-off answer) sits on the picture, at the top in the middle */
.st-key-game_clock {{ position: absolute !important; top: 1.2%; left: 50%; transform: translateX(-50%); width: 34.375%;
    z-index: 4; pointer-events: none; }}
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
.st-key-{SCREEN_KEY} img, .st-key-{TITLE_KEY} img {{ border-radius: 0; display: block; }}
.st-key-{SCREEN_KEY} img {{ cursor: pointer; }}
/* animations are drawn on a see-through canvas laid exactly over the picture (arcade/table_anim.py) */
.st-key-{SCREEN_KEY}_stage {{ position: relative; gap: 0 !important; }}
.st-key-{SCREEN_KEY}_anim {{ position: absolute !important; inset: 0; z-index: 3; pointer-events: none; }}
.st-key-{SCREEN_KEY}_anim canvas {{ border-radius: 0; }}
.st-key-{SCREEN_KEY}_alive {{ position: absolute !important; inset: 0; z-index: 2; pointer-events: none; }}
.st-key-{SCREEN_KEY} [data-testid="stElementToolbar"], .st-key-{TITLE_KEY} [data-testid="stElementToolbar"] {{ display: none; }}
.st-key-click_catcher {{ display: none; }}
/* keys with no button on screen (arrows, Space, see keys()): the buttons are on the page, so they hear their key,
   but nobody sees them and they take no room */
[class*="st-key-keys_"] {{ position: absolute !important; top: 0; left: 0; width: 1px !important; height: 1px !important;
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
/* little messages ("Welcome back, ...", "Bought ...!"): a pixel box like the rest of the game, no round corners */
[data-testid="stToast"] {{ background: #16122b !important; border: 4px solid var(--yellow) !important;
    border-radius: 0 !important; box-shadow: 6px 6px 0 #05030d !important; padding: .4rem .9rem !important; }}
[data-testid="stToast"] p {{ color: var(--yellow) !important; font-size: 1.6rem !important; letter-spacing: .06em;
    text-transform: uppercase; }}
[data-testid="stToast"] button, [data-testid="stToastDismissButton"] {{ display: none !important; }}
/* our own little messages (ui.toast): pixel pictures in the top-right corner of the game picture */
.st-key-game_toasts {{ position: absolute !important; top: 13.5%; right: 1.2%; width: 40%; z-index: 6;
    pointer-events: none; gap: .4rem !important; align-items: flex-end; }}
.st-key-game_toasts [data-testid="stMarkdownContainer"] {{ text-align: right; }}
img.arcade-toast {{ image-rendering: pixelated; animation: arcade-toast {TOAST_SECONDS}s steps(24, end) both; }}
@keyframes arcade-toast {{ 0% {{ opacity: 0; transform: translateY(-14px); }} 8% {{ opacity: 1; transform: none; }}
    85% {{ opacity: 1; }} 100% {{ opacity: 0; }} }}
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

# The full-screen button (a small icon in the top-left corner) and the F key: the browser shows only the game.
FULLSCREEN_CSS = """
button.fullscreen {
    position: fixed; top: 8px; left: 50px; z-index: 1000; cursor: pointer; width: 34px; height: 34px; padding: 0;
    font: 1.3rem "Jersey 10", monospace; line-height: 1; color: #f3ead2;
    background: #16122b; border: 3px solid #3ad6ff; border-radius: 0; box-shadow: 3px 3px 0 #05030d;
}
button.fullscreen:hover { background: #2a2150; }
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
    const label = () => {  // a small icon: four corners out (full screen) or in (back to the window); F does the same
        button.textContent = document.fullscreenElement ? "\u2199" : "\u2197";
        button.title = document.fullscreenElement ? "Exit full screen (F)" : "Full screen (F)";
    };
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

    def alive_layer(self):
        """A place laid over the picture, under the animations, for the moving parts of the wall behind a table
        (table_anim.alive). Use it with `with`."""
        self._ensure()
        if getattr(self, "_alive", None) is None:
            self._alive = self._stage.container(key=f"{self.key}_alive").empty()
        return self._alive


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
    src = inline(img)
    slot.image(src, width="stretch")
    st.session_state["_last_frame"], st.session_state["_last_src"] = img, src
    if (hasattr(img, "info") and img.info.get("alive")) or getattr(slot, "_alive", None) is not None:
        from arcade import table_anim  # (table_anim uses this module)

        table_anim.alive(slot, img)  # the machines on the wall behind a table keep playing


FADE_WINDOW = 0.7  # seconds after fade_next() during which a new picture fades in from black


def _fade_style() -> None:
    """Every run writes one small style. Only after fade_next() (entering a table, coming back into the room) does
    the game picture fade in from black: it switches to the other of two identical fade-in animations, and a new
    animation name makes the browser play it again. Any other change of screen (a menu over the room, the pause
    menu, the screens of the title menu) is a plain cut: no black flash (Miguel's call)."""
    now = time.time()
    if st.session_state.get("_fade_next") and ANIMATIONS:
        st.session_state["_fade_count"] = st.session_state.get("_fade_count", 0) + 1
        st.session_state["_fade_until"] = now + FADE_WINDOW
    name = f"arcade-fade-{st.session_state.get('_fade_count', 0) % 2}"
    rule = f"{name} .4s ease-out" if now < st.session_state.get("_fade_until", 0) else "none"
    st.markdown(
        f"<style>.st-key-{SCREEN_KEY} img, .st-key-{SCREEN_KEY}_alive canvas {{ animation: {rule}; }}"
        "@keyframes arcade-fade-0 { from { opacity: 0; } to { opacity: 1; } }"
        "@keyframes arcade-fade-1 { from { opacity: 0; } to { opacity: 1; } }</style>",
        unsafe_allow_html=True,
    )


def remember(img) -> None:
    """Keep this as the last picture on screen (a screen drawn by the browser, like the room, calls it just before
    handing over): the next screen can draw on it, and backdrop() shows it while the next screen gets ready."""
    st.session_state["_last_frame"], st.session_state["_last_src"] = img, inline(img)


@lru_cache(maxsize=1)
def title_backdrop() -> str:
    """The title screen's background, ready to send: the backdrop when leaving the title (drawn by the browser)."""
    from arcade.art import title_layers

    return inline(title_layers.still())


def backdrop(src: str | None) -> None:
    """On the first run of a new screen: the previous picture, behind everything. The old screen's picture (or the
    room) goes away as soon as the new screen draws its first element, and its own picture can take a moment to
    make: without this the page showed black for a moment (opening the pause menu, the opponent picker...)."""
    if src:
        with st.container(key="game_backdrop"):  # (the picture is the box's own background: exactly its size)
            st.markdown(f'<style>.st-key-game_backdrop {{ background-image: url("{src}"); }}</style>',
                        unsafe_allow_html=True)


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


def bar(name: str, widths: list[float]):
    """The row of buttons under the picture, made invisible: the game has no bar of buttons, everything is on the
    picture. The buttons stay on the page so their keys still work (the CSS hides containers whose key starts with
    keys_, see keys()). Whatever a button does must also be a click region on the picture."""
    with st.container(key=f"keys_bar_{name}"):
        return st.columns(widths)


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


# ---------------------------------------------------------------- little messages, in the game's pixel font

TOAST_AREA = 384  # how wide the place for messages is, on the 960-wide picture (the right 40%)


def toast(text: str, delay: float = 0.0) -> None:
    """A little message in the top-right corner of the game ("Welcome back, MIGUEL!", "Bought ...!"), painted in the
    game's own pixel font (st.toast would use the browser's font). It stays for TOAST_SECONDS, even across reruns.
    delay: seconds before it pops up (the welcome waits for the arcade to fade in from black first)."""
    now = time.time()
    count = st.session_state.get("_toast_count", 0) + 1
    st.session_state["_toast_count"] = count
    kept = [t for t in st.session_state.get("_toasts", []) if t["until"] > now]
    item = {"text": text, "until": now + delay + TOAST_SECONDS, "id": count, "delay": delay}
    st.session_state["_toasts"] = (kept + [item])[-3:]


def toast_picture(text: str):
    """The message as a pixel box: dark, a yellow edge with cut corners, a hard shadow, yellow capitals."""
    from PIL import Image

    from arcade.art.pixel import draw_text, panel, text_size, wrap

    lines = wrap(text.upper(), 24)
    width = max(text_size(line, 2)[0] for line in lines) + 36
    height = 22 * len(lines) + 22
    img = Image.new("RGBA", (width + 8, height + 8), (0, 0, 0, 0))
    panel(img, (0, 0, width - 1, height - 1), "#16122b", "#ffe94a", bw=4, shadow=True)
    for i, line in enumerate(lines):
        draw_text(img, (18, 13 + i * 22), line, 2, "#ffe94a", "lt")
    return img


def render_toasts() -> None:
    """Show the messages that are still up. Call it on every full run, inside game_frame, after the screen (so a
    message never shows on the black before the new screen's picture)."""
    now = time.time()
    active = [t for t in st.session_state.get("_toasts", []) if t["until"] > now]
    st.session_state["_toasts"] = active
    with st.container(key="game_toasts"):
        for item in active:
            img = toast_picture(item["text"])
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            src = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
            share = min(100.0, img.width / TOAST_AREA * 100)
            with st.container(key=f"toast_{item['id']}"):  # (its own key: it is not redrawn when another arrives)
                wait = item.get("delay", 0.0)
                st.markdown(f'<img class="arcade-toast" src="{src}" style="width:{share:.2f}%; '
                            f'animation-delay:{wait:.2f}s" alt="">', unsafe_allow_html=True)
