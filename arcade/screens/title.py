"""Title screen: the animated logo, then PLAY or HOW TO PLAY.

PLAY asks NEW PLAYER or I HAVE AN ACCOUNT, then the name and the PIN (typed twice for a new player).
The animation is made once and played by the browser as one looping picture (ui.movie), so the server
does no work while the title screen is open.
"""

from __future__ import annotations

from functools import lru_cache

import streamlit as st

from arcade import accounts, sound, state, ui
from arcade.art import scenes
from arcade.config import ANIMATIONS, NAME_MAX, TITLE_EVERY
from arcade.player import InvalidName
from arcade.screens import howto
from arcade.state import S

ERRORS = (InvalidName, accounts.InvalidPin, accounts.WrongPin, accounts.Locked, accounts.NameTaken,
          accounts.UnknownName)


@lru_cache(maxsize=1)
def _movie() -> str:
    return ui.movie([scenes.title_scene(t) for t in range(scenes.TITLE_FRAMES)], TITLE_EVERY)


def _picture() -> None:
    with st.container(key=ui.TITLE_KEY):
        if ANIMATIONS:
            st.image(_movie(), width="stretch")
        else:
            ui.picture(scenes.title_scene(0))
    S["_last_frame"] = scenes.title_scene(0)  # the arcade fades in from this picture


def _go(step: str | None) -> None:
    S.title_step = step
    sound.play("blip")
    st.rerun()


def _enter_arcade(player: dict, is_new: bool) -> None:
    state.start_session(player)
    S.title_step = None
    ui.fade_next()  # into the arcade through black
    sound.play("start")
    st.toast(f"Welcome, {player['name']}!" if is_new else f"Welcome back, {player['name']}!")
    st.rerun()


def _menu() -> None:
    play_col, how_col = st.columns(2)
    with play_col:
        play = ui.button("Play", "title_play", "Enter", type="primary")
    with how_col:
        how = ui.button("How to play", "title_howto", "H")
    if play:
        _go("account")
    if how:
        howto.open_from("title")
        st.rerun()


def _account() -> None:
    new_col, old_col, back_col = st.columns([1.2, 1.2, 0.7])
    with new_col:
        new = ui.button("New player", "title_new", "N", type="primary")
    with old_col:
        old = ui.button("I have an account", "title_old", "L")
    with back_col:
        back = ui.button("Back", "title_back", "Esc")
    if new:
        _go("new")
    if old:
        _go("login")
    if back:
        _go(None)


def _form(new: bool) -> None:
    with st.form("account_form", border=False):
        columns = st.columns([1.3, 1, 1, 1.2] if new else [1.3, 1, 1.2])
        with columns[0]:
            raw = st.text_input("Name", value=S.last_name, max_chars=NAME_MAX, placeholder="YOUR NAME",
                                label_visibility="collapsed")
        with columns[1]:
            raw_pin = st.text_input("PIN", type="password", max_chars=accounts.PIN_MAX,
                                    placeholder="PIN (4-8 DIGITS)", label_visibility="collapsed")
        again = None
        if new:
            with columns[2]:
                again = st.text_input("PIN again", type="password", max_chars=accounts.PIN_MAX,
                                      placeholder="PIN AGAIN", label_visibility="collapsed")
        with columns[-1]:
            submit = st.form_submit_button("Create player" if new else "Log in", type="primary", width="stretch")
    note, back_col = st.columns([3.4, 0.8])
    with note:
        st.caption("Pick a name and a PIN, and remember the PIN: it cannot be recovered." if new else
                   "Your name and your PIN, to keep your coins and clothes.")
    with back_col:
        back = ui.button("Back", "title_form_back", "Esc")
    if back:
        _go("account")
    if submit:
        try:
            if new:
                _enter_arcade(accounts.sign_up(raw, raw_pin, again), True)
            else:
                _enter_arcade(accounts.log_in(raw, raw_pin), False)
        except ERRORS as problem:
            st.error(str(problem))


def render() -> None:
    _picture()
    step = S.get("title_step")
    if step == "account":
        _account()
    elif step in ("new", "login"):
        _form(new=step == "new")
    else:
        _menu()
