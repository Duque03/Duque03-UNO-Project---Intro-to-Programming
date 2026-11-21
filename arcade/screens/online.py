"""The online screens: the online menu (create or join a lobby with its 4-letter code). The lobby itself is a room
like the arcade, where friends walk about, chat and sit down at the tables (screens/online_room.py).
"""

from __future__ import annotations

import streamlit as st

from arcade import online, sound, state, ui
from arcade.art import online as art
from arcade.logic import cursor
from arcade.logic.lobby import CODE_LETTERS, LobbyError
from arcade.state import S


def leave() -> None:
    """Leave the lobby (and any game in it) and go back to the online menu."""
    if S.get("lobby_code"):
        online.lobbies().leave(S.lobby_code, S.player["name"])
    S.lobby_code = None
    S.online_message = ""
    ui.fade_next()
    S.screen = "online"


# ---------------------------------------------------------------- the online menu

MENU = [
    {"label": "CREATE LOBBY", "action": "create", "key": "N"},
    {"label": "JOIN A LOBBY", "action": "join", "key": "J"},
    {"label": "PLAY OFFLINE", "action": "arcade", "key": "A"},
    {"label": "LOG OUT", "action": "logout", "key": "ESC"},
]


def render_menu() -> None:
    if S.get("online_step") == "join":
        _render_join()
        return
    me = online.card(S.player)
    # Keys first, on every run (see AGENTS.md): Up / Down move the yellow highlight, Enter or Space chooses.
    key = ui.keys("omenu", {"Up": "up", "Down": "down", "Enter": "choose", "Space": "space", "n": "create",
                            "j": "join", "a": "arcade", "Escape": "logout"})
    focus = cursor.clamp(S.get("online_focus"), len(MENU))
    if key in ("up", "down"):
        focus = S.online_focus = cursor.step(focus, key, len(MENU))
        sound.play("blip")
    img, regions = art.menu_picture(me, MENU, focus, S.get("online_message", ""))
    ui.show(ui.screen(), img)
    action = ui.hit(regions, ui.click())
    choice = action[1] if action else None
    if key in ("choose", "space"):
        choice = MENU[focus]["action"]
    elif key in ("create", "join", "arcade", "logout"):
        choice = key
    if not choice:
        return
    S.online_message = ""
    if choice == "create":
        S.lobby_code = online.lobbies().create(me)
        sound.play("coin")
        ui.fade_next()
        S.screen = "lobby"
    elif choice == "join":
        S.online_step, S.join_code, S.join_focus = "join", "", 0
        sound.play("blip")
    elif choice == "arcade":  # play offline: back into the arcade, with the bots. The room as it was (signing in
        ui.fade_next()        # again would reset the count of key presses the room has handled: an old Esc returns)
        state.go("hub")
    else:
        S.player = None
        ui.fade_next()
        S.screen = "title"
    st.rerun()


def _render_join() -> None:
    """JOIN A LOBBY: type the code (or pick its letters on the on-screen keyboard with the arrows), Enter joins."""
    letters = CODE_LETTERS
    keys = art.pad_keys(letters)
    mapping = {"Up": "up", "Down": "down", "Left": "left", "Right": "right", "Enter": "press", "Space": "space",
               "Backspace": "DEL", "Escape": "BACK"}
    mapping.update({letter.lower(): letter for letter in letters})  # the letters typed on the keyboard
    key = ui.keys("ojoin", mapping)
    code, focus = S.get("join_code", ""), cursor.clamp(S.get("join_focus"), len(keys))
    if key in ("up", "down", "left", "right"):
        focus = S.join_focus = cursor.pad_step(focus, key, len(letters))
        sound.play("blip")
        key = None
    elif key in ("press", "space"):
        key = keys[focus]
    img, regions = art.join_picture(code, letters, focus, S.get("online_message", ""))
    ui.show(ui.screen(), img)
    action = ui.hit(regions, ui.click())
    if action:
        key = action[1]
        if key in keys:
            S.join_focus = keys.index(key)
    if not key:
        return
    if key == "BACK":
        S.online_step, S.online_message = "menu", ""
        sound.play("blip")
    elif key == "DEL":
        S.join_code, S.online_message = code[:-1], ""
        sound.play("blip")
    elif key == "JOIN":
        _join(code)
    elif len(code) < 4:  # a letter
        S.join_code, S.online_message = code + key, ""
        sound.play("blip")
        if len(S.join_code) == 4:
            S.join_focus = len(letters) + 1  # the highlight jumps to JOIN: Enter joins
    st.rerun()


def _join(code: str) -> None:
    if len(code) < 4:
        S.online_message = "A code has 4 letters"
        sound.play("lose")
        return
    try:
        S.lobby_code = online.lobbies().join(code, online.card(S.player))
    except LobbyError as problem:
        S.online_message = str(problem)
        sound.play("lose")
        return
    S.online_message, S.online_step = "", "menu"
    sound.play("coin")
    ui.fade_next()
    S.screen = "lobby"
