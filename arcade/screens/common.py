"""Bits that every game table shares: the header, the end pop-up, the pause button,
how long the bots think, and the clock for the player's turn."""

from __future__ import annotations

import random
import time

import streamlit as st
from PIL import ImageDraw

from arcade import match, state, ui
from arcade.art import scenes
from arcade.art.pixel import draw_text, text_size
from arcade.config import BOT_THINK, SCREEN_W, TURN_SECONDS
from arcade.logic import turn_clock
from arcade.state import S


def bot_pause(since: float) -> None:
    """A bot thinks for a random time between the two numbers of BOT_THINK before its move shows.
    since: when it started working out the move (that time counts too, so strong bots are not slower)."""
    time.sleep(max(0.0, random.uniform(*BOT_THINK) - (time.time() - since)))


def show(slot, img, screen: str) -> None:
    """Show the table picture. The first time in a run, the turn clock goes right under it."""
    ui.show(slot, img)
    if not getattr(slot, "clock_drawn", False):
        slot.clock_drawn = True
        clock_bar(screen)


def run_clock(my_turn: bool) -> bool:
    """Start, keep or stop the clock for the player's turn. Returns True when their time has run out."""
    S.turn_deadline = turn_clock.keep_or_start(S.get("turn_deadline"), my_turn and not S.get("result"), time.time())
    return turn_clock.is_up(S.turn_deadline, time.time())


def restart_clock() -> None:
    """The player did something that keeps their turn going (drew a card, jumped again): a fresh clock."""
    S.turn_deadline = None


@st.fragment(run_every=1.0)
def clock_bar(screen: str) -> None:
    """The countdown under the table. It redraws itself every second; at zero the whole screen runs
    again, and the screen sees that the time is up and plays for the player."""
    deadline = S.get("turn_deadline")
    if S.screen != screen:
        return
    if deadline is None:  # not the player's turn: an empty line of the same height (it replaces the old bar at once)
        st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
        return
    left = turn_clock.seconds_left(deadline, time.time())
    colour = "#ff4f6d" if left <= 5 else "#3ad6ff"
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:10px;height:30px;margin:-6px 0 2px 0'>"
        f"<div style='flex:1;height:10px;border-radius:5px;background:#17123a;border:1px solid #3a2f6b'>"
        f"<div style='width:{100 * left / TURN_SECONDS:.0f}%;height:100%;border-radius:5px;background:{colour};"
        f"box-shadow:0 0 8px {colour}'></div></div>"
        f"<b style='color:{colour};font-size:1.25rem;min-width:7.5em'>YOUR TURN: {left:.0f}s</b></div>",
        unsafe_allow_html=True,
    )
    if left <= 0:
        st.rerun()


def header(img, title: str) -> None:
    """Game name and mode along the top edge of the table picture."""
    draw_text(img, (16, 8), title, 3, "#ffe94a", "lt", shadow="#16122b")
    draw_text(img, (16 + text_size(title, 3)[0] + 18, 12), match.mode_label(), 2, "#d9d4ff", "lt", shadow="#16122b")


def message(img, text: str, y: int, colour="#ffffff", scale=2) -> None:
    """A centred line of text with a dark strip behind it so it stays readable."""
    if not text:
        return
    text = text.upper()
    width = text_size(text, scale)[0]
    ImageDraw.Draw(img).rectangle(
        [SCREEN_W // 2 - width // 2 - 10, y - 5, SCREEN_W // 2 + width // 2 + 10, y + 7 * scale + 4], fill=(16, 12, 34)
    )
    draw_text(img, (SCREEN_W // 2, y), text, scale, colour, "mt")


def with_result(img, regions):
    """Cover the table with the end-of-game pop-up when a free-play game is over."""
    if not S.result:
        return img, regions
    return scenes.result_panel(img, S.result["title"], S.result["line"], S.result["coins"]), []


def pause_button(column, screen: str) -> None:
    with column:
        if ui.button("Pause", f"{screen}_pause", "Esc"):
            restart_clock()  # the clock stops while the game is paused and starts again on return
            S.paused_from = screen
            S.pause_behind = S.get("_last_frame")  # the menu sits on top of the table as it was
            state.go("pause")
            st.rerun()


def rules_button(column, screen: str) -> None:
    """Opens the rules of this game (task B3); Back returns to the table."""
    from arcade.screens import howto  # (imported here: howto imports the room, which imports this file's neighbours)

    with column:
        if ui.button("Rules", f"{screen}_rules", "H"):
            restart_clock()
            howto.open_from(screen, screen)
            st.rerun()


def continue_button(column, screen: str, clicked_picture: bool) -> None:
    """After the pop-up: Enter (or a click) walks back into the arcade."""
    with column:
        pressed = ui.button("Continue", f"{screen}_continue", "Enter", type="primary")
    if pressed or clicked_picture:
        match.back_to_hub()
        st.rerun()
