"""Arcade Masters - start the game with:  uv run streamlit run app.py

This file only decides which screen to show. Each screen lives in
arcade/screens/ and has a render() function.
"""

import streamlit as st

from arcade import state, ui
from arcade.screens import champ, checkers, connect4, hub, pause, store, title, uno, wardrobe

SCREENS = {
    "title": title.render,
    "hub": hub.render,
    "uno": uno.render,
    "checkers": checkers.render,
    "connect4": connect4.render,
    "store": store.render,
    "pause": pause.render,
    "wardrobe": wardrobe.render,
    "champ_intro": champ.render_intro,
    "champ_rules": champ.render_rules,
    "champ_score": champ.render_score,
    "champ_final": champ.render_final,
}

ui.setup_page()
state.init()
if st.session_state.player is None:  # for example after the page was reloaded
    st.session_state.screen = "title"
SCREENS[st.session_state.screen]()
