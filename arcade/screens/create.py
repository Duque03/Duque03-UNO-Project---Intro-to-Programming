"""Create your player: right after a new account, the player picks hair, hair colour, T-shirt and skin.

Mouse: click a choice, then LET'S PLAY!. Keyboard: Up / Down move between the rows, Left / Right change the choice
of that row, Enter is LET'S PLAY!. The yellow arrow only shows while the keys are being used.
The choice is checked and saved by logic/looks.py; store items are worn on top of it later.
"""

from __future__ import annotations

import streamlit as st

from arcade import sound, state, ui
from arcade.art import create as art
from arcade.logic import looks

S = st.session_state


def render() -> None:
    key = ui.keys("create", ui.ARROWS)  # on every run, before the picture (see AGENTS.md)
    choice = S.get("create_choice") or dict(S.player.get("base") or looks.DEFAULT)
    row, rows = S.get("create_row", 0), len(looks.ROWS) + 1  # the last row is LET'S PLAY!
    if key in ("up", "down"):
        row = (row + (1 if key == "down" else -1)) % rows
    elif key in ("left", "right") and row < len(looks.ROWS):
        choice = looks.step(choice, row, 1 if key == "right" else -1)
    if key:
        S.create_keys = True
        sound.play("blip")
    S.create_choice, S.create_row = choice, row

    img, regions = art.creator_picture(S.player["name"], choice, row if S.get("create_keys") else None)
    ui.show(ui.screen(), img)
    point = ui.click()
    if point is not None:
        S.create_keys = False  # the mouse is in use: no arrow
    action = ui.hit(regions, point)
    bar = ui.bar("create", [3, 1.4])  # invisible: LET'S PLAY! is on the picture
    with bar[1]:
        done = ui.button("Let's play!", "create_done", "Enter", type="primary")

    if action and action[0] == "set":
        S.create_choice = dict(choice, **{action[1]: action[2]})
        sound.play("blip")
        st.rerun()
    if done or action == ("done",):
        looks.apply(S.player, choice)  # checked against the lists, then saved
        state.save()
        for name in ("create_choice", "create_row", "create_keys"):
            S.pop(name, None)
        state.go(S.pop("after_create", None) or "hub")
        ui.fade_next()
        sound.play("start")
        st.rerun()
