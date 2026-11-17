"""The "How to play" panel (task A3), opened from the title screen, the pause menu and the game tables (B3)."""

from __future__ import annotations

import streamlit as st

from arcade import controls, sound, state, ui
from arcade.art import scenes
from arcade.config import GAMES
from arcade.screens import hub
from arcade.state import S


BACK_TO = ("title", "pause") + tuple(GAMES)  # screens the panel can be opened from


def open_from(screen: str, tab: str | None = None) -> None:
    """Show the panel; Back returns to the given screen (title, pause, or a game table).

    From a table it opens on that game's tab, on top of the table as it was.
    """
    S.howto_from = screen
    S.howto_tab = tab if tab in controls.TAB_KEYS else controls.TAB_KEYS[0]
    S.howto_behind = S.get("_last_frame") if screen in GAMES else None
    state.go("howto")


def render() -> None:
    back_to = S.get("howto_from") or "title"
    tab = S.get("howto_tab") or controls.TAB_KEYS[0]
    # The panel sits on top of the screen it was opened from.
    if back_to == "title" or not S.player:
        behind = scenes.title_scene(0)
    elif back_to in GAMES and S.get("howto_behind") is not None:
        behind = S.howto_behind
    else:
        behind = hub.picture(hint=False)[0]
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
        sound.play("blip")
        st.rerun()
    if back:
        state.go(back_to if back_to in BACK_TO else "title")
        st.rerun()
