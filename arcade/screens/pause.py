"""Pause menu (Esc): resume, customize character, leave arcade."""

from __future__ import annotations

import streamlit as st

from arcade import state, ui
from arcade.art import scenes
from arcade.screens import howto, hub
from arcade.state import S

OPTIONS = [
    {"label": "RESUME", "action": "resume", "key": "ESC"},
    {"label": "CUSTOMIZE CHARACTER", "action": "wardrobe"},
    {"label": "HOW TO PLAY", "action": "howto"},
    {"label": "LEAVE ARCADE", "action": "leave"},
]


def render() -> None:
    img, regions = scenes.menu_panel(hub.picture(hint=False)[0], "PAUSED", OPTIONS)
    ui.show(ui.screen(), img)
    point = ui.click()
    action = ui.hit(regions, point)
    bar = st.columns(4)
    with bar[0]:
        resume = ui.button("Resume", "pause_resume", "Esc", type="primary")
    with bar[1]:
        wardrobe = ui.button("Customize character", "pause_wardrobe")
    with bar[2]:
        how = ui.button("How to play", "pause_howto", "H")
    with bar[3]:
        leave = ui.button("Leave arcade", "pause_leave")

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
    if leave or action == ("menu", "leave"):
        state.save()  # progress is kept for next time
        S.match = S.game = S.result = S.champ = None
        S.naming = False
        state.go("title")
        st.rerun()
