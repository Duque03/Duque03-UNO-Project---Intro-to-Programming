"""Title screen: big logo, INSERT NAME, then PLAY."""

from __future__ import annotations

import streamlit as st

from arcade import state, ui
from arcade.art import scenes
from arcade.config import NAME_MAX
from arcade.player import InvalidName, clean_name
from arcade.screens import howto
from arcade.state import S


def _howto_button() -> None:
    """Opens the "How to play" panel (task A3)."""
    if ui.button("How to play", "title_howto", "H"):
        howto.open_from("title")
        st.rerun()


def render() -> None:
    ui.show(st.container(key=ui.TITLE_KEY).empty(), scenes.title_scene(0))  # show(), so the fades start from it
    _, middle, _ = st.columns([1, 1.4, 1])
    with middle:
        if not S.get("naming"):
            if ui.button("Insert name", "title_insert", "Enter", type="primary"):
                S.naming = True
                st.rerun()
            _howto_button()
            return
        with st.form("name_form", border=False):
            raw = st.text_input("Insert name", value=S.last_name, max_chars=NAME_MAX, placeholder="YOUR NAME",
                                label_visibility="collapsed")
            play = st.form_submit_button("Play", type="primary", width="stretch")
        st.caption("Type your name and press Enter. Use the same name later to continue with your coins and clothes.")
        _howto_button()
        if play:
            try:
                name = clean_name(raw)
            except InvalidName as problem:
                st.error(str(problem))
                return
            is_new = state.start_session(name)
            S.naming = False
            ui.fade_next()  # into the arcade through black
            st.toast(f"Welcome, {name}!" if is_new else f"Welcome back, {name}!")
            st.rerun()
