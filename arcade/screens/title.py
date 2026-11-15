"""Title screen: big logo, INSERT NAME, then PLAY."""

from __future__ import annotations

import streamlit as st

from arcade import state, ui
from arcade.art import scenes
from arcade.config import NAME_MAX
from arcade.player import InvalidName, clean_name
from arcade.state import S


def render() -> None:
    ui.picture(scenes.title_scene(0))
    _, middle, _ = st.columns([1, 1.4, 1])
    with middle:
        if not S.get("naming"):
            if ui.button("Insert name", "title_insert", "Enter", type="primary"):
                S.naming = True
                st.rerun()
            return
        with st.form("name_form", border=False):
            raw = st.text_input("Insert name", value=S.last_name, max_chars=NAME_MAX, placeholder="YOUR NAME",
                                label_visibility="collapsed")
            play = st.form_submit_button("Play", type="primary", width="stretch")
        st.caption("Type your name and press Enter. Use the same name later to continue with your coins and clothes.")
        if play:
            try:
                name = clean_name(raw)
            except InvalidName as problem:
                st.error(str(problem))
                return
            is_new = state.start_session(name)
            S.naming = False
            st.toast(f"Welcome, {name}!" if is_new else f"Welcome back, {name}!")
            st.rerun()
