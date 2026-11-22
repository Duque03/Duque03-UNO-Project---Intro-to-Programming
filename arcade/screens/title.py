"""Title screen: drawn and animated by the browser, with an in-game menu (arcade/title_view.py).

PRESS ENTER -> CREATE A CHARACTER or I HAVE AN ACCOUNT -> name and PIN -> (a new player makes their character) ->
PLAY OFFLINE or PLAY ONLINE, all on the picture, by keyboard or mouse. Python only checks what the browser sends:
HOW TO PLAY, a name and PIN to sign in with, where to play, LOG OUT. After PLAY OFFLINE the browser flies into the
arcade and then sends "entered"; only then does the player walk in.
"""

from __future__ import annotations

import time

import streamlit as st

from arcade import (
    accounts,
    catalog,
    db,
    hubmap,
    online,
    room,
    sound,
    state,
    title_view,
    ui,
)
from arcade import player as player_model
from arcade.logic import championship
from arcade.logic.lobby import LobbyError
from arcade.player import InvalidName
from arcade.screens import howto
from arcade.state import S

ERRORS = (InvalidName, accounts.InvalidPin, accounts.WrongPin, accounts.Locked, accounts.NameTaken,
          accounts.UnknownName)


def _text(value, limit: int) -> str:
    """A short piece of text from the browser (anything else becomes empty)."""
    return value[:limit] if isinstance(value, str) else ""


def _sign_in(value: dict, number: int) -> None:
    """CREATE A CHARACTER or I HAVE AN ACCOUNT. A refusal goes back to the browser, which shows it on the screen.
    A new player goes straight to making their character; then (and straight away for an account) the title screen
    asks where to play: offline or online."""
    mode = value.get("mode") if isinstance(value, dict) else None
    name, pin = _text(value.get("name"), 40), _text(value.get("pin"), 20)
    try:
        if mode == "new":
            player, is_new = accounts.sign_up(name, pin, _text(value.get("pin2"), 20)), True
        elif mode == "login":
            player, is_new = accounts.log_in(name, pin), False
        else:
            return
    except ERRORS as problem:
        S.title_error = {"text": str(problem), "n": number}
        sound.play("lose")
        st.rerun()
    S.title_error = None
    state.start_session(player)
    S.title_welcome = f"Welcome, {player['name']}!" if is_new else f"Welcome back, {player['name']}!"
    if S.screen == "create":  # a new player makes their character first, then chooses offline or online
        S.after_create = "title"  # (on the title's own background: only the box comes up)
        sound.play("start")
    else:
        S.screen = "title"  # the title screen's menu is now PLAY OFFLINE / PLAY ONLINE
        sound.play("coin")
    st.rerun()


def _play(value: dict) -> None:
    """PLAY OFFLINE: fly into the arcade first. (PLAY ONLINE only changes what the title screen draws.)"""
    if S.player is None:
        return
    S.title_target = "hub"
    S.title_enter = value["n"]  # the browser flies into the arcade (and plays the start sound), then sends "entered"
    st.rerun()


def _lobby(value: dict, number: int) -> None:
    """CREATE LOBBY, or JOIN with a code: then fly in, into the lobby's room. A refusal (wrong code, full) goes back to
    the browser, which shows it in the box."""
    if S.player is None or not isinstance(value, dict):
        return
    card = online.card(S.player)
    try:
        if value.get("action") == "create":
            code = online.lobbies().create(card)
        elif value.get("action") == "join":
            code = online.lobbies().join(_text(value.get("code"), 8), card)
        else:
            return
    except LobbyError as problem:
        S.title_error = {"text": str(problem), "n": number}
        sound.play("lose")
        st.rerun()
    S.title_error = None
    S.lobby_code = code
    S.title_target = "lobby"
    S.title_enter = number  # fly in (as into the arcade), then "entered": the room of the lobby
    sound.play("coin")
    st.rerun()


WELCOME_DELAY = 0.9  # the welcome pops up once the arcade has faded in from black (the fade takes 0.4 s)


def welcome() -> None:
    """Welcome (back), once per sign-in, when the player first goes into a room (the arcade, or an online lobby)."""
    text = S.pop("title_welcome", None)
    if text:
        ui.toast(text, WELCOME_DELAY)


def _walk_in() -> None:
    """The flight into the arcade is over: the player walks in by the door (of the arcade, or of the lobby's room)."""
    if S.player is None:
        return
    if S.pop("title_target", None) == "lobby" and S.get("lobby_code"):
        from arcade.screens import online_room  # (online_room uses this module)

        online_room.enter()  # (the welcome pops up there)
        st.rerun()
    S.hub["pos"], S.hub["dir"], S.hub["walk"] = hubmap.SPAWN, "up", None
    state.reset_bots()
    S.match = S.game = S.result = S.champ = None
    S.screen = "hub"
    ui.fade_next()  # the flight ends on black, and the arcade fades in from black
    welcome()
    st.rerun()


def _log_out() -> None:
    state.save()
    S.player = None
    S.title_welcome = None
    sound.play("blip")
    st.rerun()


CHAMPION_EVERY = 60  # seconds between two looks at the saved players for the best one


def _champion() -> dict | None:
    """The arcade's best player for the title screen (looked up at most once a minute), or None."""
    looked = S.get("_title_champion")
    if looked and time.monotonic() - looked[0] < CHAMPION_EVERY:
        return looked[1]
    best = championship.best_player(db.all_players())
    champion = None
    if best:
        champion = {"name": best["name"], "look": player_model.look(best), "titles": best["championships"],
                    "tag": catalog.spec_for("name", best["equipped"].get("name"))}
    S._title_champion = (time.monotonic(), champion)
    return champion


def render() -> None:
    sent = S.setdefault("_title_sent", set())
    events = title_view.mount(title_view.scene(sent, error=S.get("title_error"), ack=S.get("title_ack", 0),
                                               last_name=S.get("last_name") or "", champion=_champion(),
                                               enter=S.get("title_enter", 0),
                                               signed_in=S.player["name"] if S.get("player") else "",
                                               me=online.card(S.player) if S.get("player") else None,
                                               start=S.get("title_start"), notice=S.get("title_notice")))
    if events.need:  # the browser lost some pictures (it was reloaded): send them again
        sent.difference_update(key for key in events.need if isinstance(key, str))
        st.rerun()
    for name in ("howto", "submit", "play", "lobby", "logout", "entered"):
        value = getattr(events, name)
        if value is None:
            continue
        number = room.new_press(value, S.get("title_ack", 0))
        if number is None:  # sent again by the browser, already handled
            continue
        S.title_ack = number
        if name == "howto":
            sound.play("blip")
            howto.open_from("title")
            st.rerun()
        if name == "entered":
            _walk_in()
        elif name == "play":
            _play(value)
        elif name == "lobby":
            _lobby(value, number)
        elif name == "logout":
            _log_out()
        else:
            _sign_in(value, number)
