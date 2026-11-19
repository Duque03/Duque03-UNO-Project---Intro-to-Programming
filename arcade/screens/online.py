"""The online screens: the online menu (create or join a lobby) and the lobby, where friends wait for the host.

Every player's browser looks at the lobby about once a second (watch()), and the screen is drawn again only when
something changed (the lobby's version). When the host starts a game, everyone in the lobby goes to the table.
"""

from __future__ import annotations

import streamlit as st

from arcade import online, sound, state, ui
from arcade.art import online as art
from arcade.logic import cursor
from arcade.logic.lobby import CODE_LETTERS, GAME_NAMES, GAME_SIZES, LobbyError
from arcade.state import S


def leave() -> None:
    """Leave the lobby (and any game in it) and go back to the online menu."""
    if S.get("lobby_code"):
        online.lobbies().leave(S.lobby_code, S.player["name"])
    S.lobby_code = None
    S.online_message = ""
    ui.fade_next()
    S.screen = "online"


@st.fragment(run_every=1.0)
def watch(code: str, seen: int) -> None:
    """Once a second: has the lobby changed since this picture was drawn? Then draw everything again."""
    if online.lobbies().version(code) != seen:
        st.rerun(scope="app")


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


# ---------------------------------------------------------------- the lobby

def render_lobby() -> None:
    code, me = S.get("lobby_code"), S.player["name"]
    try:
        lobby = online.lobbies().get(code)
    except LobbyError:
        S.online_message = "That lobby has closed."
        leave()
        st.rerun()
    if me not in lobby.names():  # someone's leaving closed it, or this player was not in it any more
        S.online_message = "You are not in that lobby any more."
        leave()
        st.rerun()
    if lobby.table is not None and lobby.round != S.get("online_round_done"):
        ui.fade_next()  # the host started a game: to the table
        S.screen = "online_table"
        st.rerun()

    host = lobby.host == me
    message, good = "", False
    if lobby.game:
        low, high = GAME_SIZES[lobby.game]
        if low <= len(lobby.players) <= high:
            message, good = ("Ready! Press START" if host else "Ready! Waiting for the host to start"), True
        else:
            message = f"{GAME_NAMES[lobby.game]} needs {low if low == high else f'{low} to {high}'} players"
    if S.get("online_message"):
        message, good = S.online_message, False
    key = ui.keys("olobby", {"Left": "left", "Right": "right"})  # the host moves along the games
    if key and host:
        index = art.GAMES.index(lobby.game) if lobby.game else None
        index = cursor.step(index, key, len(art.GAMES))
        online.lobbies().choose(code, me, art.GAMES[index])
        sound.play("blip")
        st.rerun()
    img, regions = art.lobby_picture(lobby, me, message, good)
    ui.show(ui.screen(), img)
    clicked = ui.hit(regions, ui.click())
    watch(code, lobby.version)

    bar = st.columns([0.8, 1, 1.3, 1, 1, 0.9])
    with bar[0]:  # the code as text, with a copy button, to paste into a message to friends
        st.code(lobby.code, language=None)
    picks = {}
    for column, (game, label, key) in zip(bar[1:], (("uno", "UNO", "1"), ("checkers", "Checkers", "2"),
                                                   ("connect4", "Connect Four", "3"))):
        with column:
            picks[game] = ui.button(label, f"lobby_{game}", key, disabled=not host,
                                    type="primary" if lobby.game == game else "secondary")
    with bar[4]:
        start = ui.button("Start", "lobby_start", "Enter", type="primary", disabled=not host)
    with bar[5]:
        out = ui.button("Leave", "lobby_leave", "Esc")
    chosen = next((game for game, pressed in picks.items() if pressed), None)
    if clicked and clicked[0] == "game":
        chosen = clicked[1]
    try:
        if chosen:
            online.lobbies().choose(code, me, chosen)
            S.online_message = ""
            sound.play("blip")
            st.rerun()
        if start:
            online.lobbies().start(code, me)
            S.online_message = ""
            sound.play("table")
            st.rerun()
    except LobbyError as problem:
        S.online_message = str(problem)
        sound.play("lose")
        st.rerun()
    if out:
        leave()
        st.rerun()
