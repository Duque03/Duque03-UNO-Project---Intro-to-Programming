"""Title screen: drawn and animated by the browser, with an in-game menu (arcade/title_view.py).

PLAY -> NEW PLAYER or I HAVE AN ACCOUNT -> name and PIN, all on the picture, by keyboard or mouse.
Python only checks what the browser sends: HOW TO PLAY, or a name and PIN to sign in with.
"""

from __future__ import annotations

import streamlit as st

from arcade import accounts, room, sound, state, title_view, ui
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
    state.start_session(player)
    ui.fade_next()  # into the arcade through black
    sound.play("start")
    st.toast(f"Welcome, {player['name']}!" if is_new else f"Welcome back, {player['name']}!")
    st.rerun()


def render() -> None:
    sent = S.setdefault("_title_sent", set())
    events = title_view.mount(title_view.scene(sent, error=S.get("title_error"), ack=S.get("title_ack", 0),
                                               last_name=S.get("last_name") or ""))
    if events.need:  # the browser lost some pictures (it was reloaded): send them again
        sent.difference_update(key for key in events.need if isinstance(key, str))
        st.rerun()
    for name in ("howto", "submit"):
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
        _sign_in(value, number)
