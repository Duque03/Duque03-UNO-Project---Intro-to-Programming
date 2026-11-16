"""Arcade Masters - start the game with:  uv run streamlit run app.py

This file only decides which screen to show. Each screen lives in
arcade/screens/ and has a render() function.
"""

import streamlit as st

from arcade import state, ui
from arcade.screens import champ, checkers, connect4, howto, hub, pause, store, title, uno, wardrobe

SCREENS = {
    "title": title.render,
    "hub": hub.render,
    "uno": uno.render,
    "checkers": checkers.render,
    "connect4": connect4.render,
    "store": store.render,
    "pause": pause.render,
    "wardrobe": wardrobe.render,
    "howto": howto.render,
    "champ_intro": champ.render_intro,
    "champ_rules": champ.render_rules,
    "champ_score": champ.render_score,
    "champ_final": champ.render_final,
}

ui.setup_page()
state.init()
if st.session_state.player is None and st.session_state.screen != "howto":  # for example after a page reload
    st.session_state.screen = "title"  # ("How to play" can be opened from the title screen, before a name is given)
SCREENS[st.session_state.screen]()
