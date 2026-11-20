"""Title screen: drawn and animated by the browser, with an in-game menu (arcade/title_view.py).

PRESS ENTER -> PLAY -> NEW PLAYER or I HAVE AN ACCOUNT -> name and PIN, all on the picture, by keyboard or mouse.
Python only checks what the browser sends: HOW TO PLAY, or a name and PIN to sign in with. When the sign-in is
accepted, the browser flies into the arcade and then sends "entered"; only then does the player walk in.
"""

from __future__ import annotations

import time

import streamlit as st

from arcade import accounts, catalog, db, room, sound, state, title_view, ui
from arcade import player as player_model
from arcade.logic import championship
from arcade.player import InvalidName
from arcade.screens import howto
from arcade.state import S

ERRORS = (InvalidName, accounts.InvalidPin, accounts.WrongPin, accounts.Locked, accounts.NameTaken,
          accounts.UnknownName)


def _text(value, limit: int) -> str:
    """A short piece of text from the browser (anything else becomes empty)."""
    return value[:limit] if isinstance(value, str) else ""


def _sign_in(value: dict, number: int) -> None:
    """NEW PLAYER or I HAVE AN ACCOUNT. A refusal goes back to the browser, which shows it on the screen."""
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
    if value.get("where") == "online":  # PLAY ONLINE: straight to the online menu (create or join a lobby)
        state.start_session(player)
        if S.screen == "create":  # a new player makes their look first, then goes online
            S.after_create = "online"
        else:
            S.screen = "online"
        ui.fade_next()
        sound.play("start")
        st.toast(f"Welcome, {player['name']}!" if is_new else f"Welcome back, {player['name']}!")
        st.rerun()
    S.title_pending = {"player": player, "new": is_new}
    S.title_enter = number  # the browser flies into the arcade (and plays the start sound), then sends "entered"
    st.rerun()


def _walk_in() -> None:
    """The flight into the arcade is over: start playing with the player who signed in."""
    pending = S.get("title_pending")
    if not pending:
        return
    S.title_pending = None
    player = pending["player"]
    state.start_session(player)
    ui.fade_next()  # the flight ends on black, and the arcade fades in from black
    st.toast(f"Welcome, {player['name']}!" if pending["new"] else f"Welcome back, {player['name']}!")
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
                                               enter=S.get("title_enter", 0)))
    if events.need:  # the browser lost some pictures (it was reloaded): send them again
        sent.difference_update(key for key in events.need if isinstance(key, str))
        st.rerun()
    for name in ("howto", "submit", "entered"):
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
        else:
            _sign_in(value, number)
