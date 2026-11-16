"""The "How to play" panel (task A3), opened from the title screen and from the pause menu."""

from __future__ import annotations

import streamlit as st

from arcade import controls, state, ui
from arcade.art import scenes
from arcade.screens import hub
from arcade.state import S


def open_from(screen: str) -> None:
    """Show the panel; Back returns to the given screen ("title" or "pause")."""
    S.howto_from = screen
    S.howto_tab = controls.TAB_KEYS[0]
    state.go("howto")


def render() -> None:
    back_to = S.get("howto_from") or "title"
    tab = S.get("howto_tab") or controls.TAB_KEYS[0]
    # The panel sits on top of the screen it was opened from.
    behind = scenes.title_scene(0) if back_to == "title" or not S.player else hub.picture(hint=False)[0]
    img, regions = scenes.howto_panel(behind, controls.TABS, tab)
    ui.show(ui.screen(), img)
    action = ui.hit(regions, ui.click())

    bar = st.columns([1, 1, 1, 1, 1])
    chosen = None
    for i, (column, item) in enumerate(zip(bar, controls.TABS)):
        with column:
            if ui.button(item["label"].title(), f"howto_{item['key']}", str(i + 1),
                         type="primary" if item["key"] == tab else "secondary"):
                chosen = item["key"]
    with bar[-1]:
        back = ui.button("Back", "howto_back", "Esc")

    if action and action[0] == "tab":
        chosen = action[1]
    if chosen in controls.TAB_KEYS and chosen != tab:
        S.howto_tab = chosen
        st.rerun()
    if back:
        state.go(back_to if back_to in ("title", "pause") else "title")
        st.rerun()
