"""The online screens: the online menu (create or join a lobby) and the lobby, where friends wait for the host.

Every player's browser looks at the lobby about once a second (watch()), and the screen is drawn again only when
something changed (the lobby's version). When the host starts a game, everyone in the lobby goes to the table.
"""

from __future__ import annotations

import streamlit as st

from arcade import online, sound, state, ui
from arcade.art import online as art
from arcade.logic.lobby import GAME_NAMES, GAME_SIZES, LobbyError
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

def render_menu() -> None:
    me = online.card(S.player)
    ui.show(ui.screen(), art.menu_picture(me, S.get("online_message", "")))
    bar = st.columns([1.3, 1.9, 1.0, 1.0])
    with bar[0]:
        create = ui.button("Create lobby", "online_create", "N", type="primary")
    with bar[1]:
        with st.form("online_join_form", border=False):  # Enter in the box joins, like the Join button
            box, button = st.columns([1.1, 0.8])
            with box:
                code = st.text_input("Code", key="online_code", max_chars=4, placeholder="CODE",
                                     label_visibility="collapsed")
            with button:
                join = st.form_submit_button("Join", width="stretch")
    with bar[2]:
        arcade = ui.button("Arcade", "online_arcade", "A")
    with bar[3]:
        out = ui.button("Log out", "online_out", "Esc")
    if create:
        S.lobby_code = online.lobbies().create(me)
        S.online_message = ""
        sound.play("coin")
        ui.fade_next()
        S.screen = "lobby"
        st.rerun()
    if join:
        try:
            S.lobby_code = online.lobbies().join(code, me)
        except LobbyError as problem:
            S.online_message = str(problem)
            sound.play("lose")
            st.rerun()
        S.online_message = ""
        sound.play("coin")
        ui.fade_next()
        S.screen = "lobby"
        st.rerun()
    if arcade:  # play offline: back into the arcade, with the bots. The room as it was (signing in again would
        ui.fade_next()  # reset the count of key presses the room has handled, and an old Esc would come back)
        state.go("hub")
        st.rerun()
    if out:
        S.player = None
        ui.fade_next()
        S.screen = "title"
        st.rerun()


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
    ui.show(ui.screen(), art.lobby_picture(lobby, me, message, good))
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
