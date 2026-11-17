"""Bits that every game table shares: the header, the end pop-up and the pause button."""

from __future__ import annotations

import streamlit as st
from PIL import ImageDraw

from arcade import match, state, ui
from arcade.art import scenes
from arcade.art.pixel import draw_text, text_size
from arcade.config import SCREEN_W
from arcade.state import S


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
            S.paused_from = screen
            S.pause_behind = S.get("_last_frame")  # the menu sits on top of the table as it was
            state.go("pause")
            st.rerun()


def rules_button(column, screen: str) -> None:
    """Opens the rules of this game (task B3); Back returns to the table."""
    from arcade.screens import howto  # (imported here: howto imports the room, which imports this file's neighbours)

    with column:
        if ui.button("Rules", f"{screen}_rules", "H"):
            howto.open_from(screen, screen)
            st.rerun()


def continue_button(column, screen: str, clicked_picture: bool) -> None:
    """After the pop-up: Enter (or a click) walks back into the arcade."""
    with column:
        pressed = ui.button("Continue", f"{screen}_continue", "Enter", type="primary")
    if pressed or clicked_picture:
        match.back_to_hub()
        st.rerun()
