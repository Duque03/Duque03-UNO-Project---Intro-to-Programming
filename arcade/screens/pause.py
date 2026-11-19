"""Pause menu (Esc): resume, customize character, how to play, leave the table (at a table), leave arcade."""

from __future__ import annotations

import streamlit as st

from arcade import match, sound, state, ui
from arcade.art import scenes
from arcade.config import GAMES
from arcade.logic import cursor
from arcade.screens import howto, hub
from arcade.state import S

OPTIONS = [
    {"label": "RESUME", "action": "resume", "key": "ESC"},
    {"label": "WARDROBE", "action": "wardrobe"},
    {"label": "HOW TO PLAY", "action": "howto"},
    {"label": "LEAVE ARCADE", "action": "leave"},
]
LEAVE_TABLE = {"label": "LEAVE TABLE", "action": "leave_table"}


def options(paused_from: str | None) -> list[dict]:
    """The menu. At a game table there is one more choice: leave the table (task B4)."""
    if paused_from in GAMES:
        return OPTIONS[:3] + [LEAVE_TABLE] + OPTIONS[3:]
    return list(OPTIONS)


def leave_table() -> None:
    """Give up the game at this table. Free play: a loss (no coins). Championship: the whole run ends."""
    sound.play("lose")
    champ = S.match and S.match["mode"] == "champ"
    S.champ = None if champ else S.champ
    match.back_to_hub(centre=bool(champ))
    st.toast("You left the championship." if champ else "You left the table. No coins this time.")


def render() -> None:
    at_table = S.paused_from in GAMES
    behind = S.get("pause_behind") if at_table and S.get("pause_behind") is not None else hub.picture(hint=False)[0]
    menu = options(S.paused_from)
    focus = cursor.clamp(S.get("pause_focus"), len(menu))  # the yellow highlight starts on RESUME
    img, regions = scenes.menu_panel(behind, "PAUSED", menu, focus=focus)
    ui.show(ui.screen(), img)
    point = ui.click()
    action = ui.hit(regions, point)
    key = ui.keys("pause", {"Up": "up", "Down": "down", "Enter": "choose"})  # Up / Down move, Enter chooses
    if key in ("up", "down"):
        S.pause_focus = cursor.step(focus, key, len(menu))
        sound.play("blip")
        st.rerun()
    if key == "choose":
        action = ("menu", menu[focus]["action"])
    bar = st.columns(5 if at_table else 4)
    with bar[0]:
        resume = ui.button("Resume", "pause_resume", "Esc", type="primary")
    with bar[1]:
        wardrobe = ui.button("Wardrobe", "pause_wardrobe")
    with bar[2]:
        how = ui.button("How to play", "pause_howto", "H")
    quit_table = False
    if at_table:
        with bar[3]:
            quit_table = ui.button("Leave table", "pause_leave_table")
    with bar[-1]:
        leave = ui.button("Leave arcade", "pause_leave")
    if action or resume or wardrobe or how or quit_table or leave:
        S.pause_focus = None  # the menu opens on RESUME again next time

    if resume or action == ("menu", "resume"):
        state.go(S.paused_from or "hub")
        st.rerun()
    if wardrobe or action == ("menu", "wardrobe"):
        S.wardrobe_focus = None
        state.go("wardrobe")
        st.rerun()
    if how or action == ("menu", "howto"):
        howto.open_from("pause")
        st.rerun()
    if at_table and (quit_table or action == ("menu", "leave_table")):
        leave_table()
        st.rerun()
    if leave or action == ("menu", "leave"):
        state.save()  # progress is kept for next time
        S.match = S.game = S.result = S.champ = None
        S.naming = False
        ui.fade_next()  # back to the title screen through black (A1)
        state.go("title")
        st.rerun()
