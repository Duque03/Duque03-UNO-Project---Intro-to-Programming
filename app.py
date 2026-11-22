"""Arcade Masters - start the game with:  uv run streamlit run app.py

This file only decides which screen to show. Each screen lives in
arcade/screens/ and has a render() function.
"""

import streamlit as st

from arcade import sound, state, ui
from arcade.screens import (champ, checkers, connect4, create, howto, hub, online, online_room, online_table, pause, store,
                            title, uno, versus, wardrobe)

SCREENS = {
    "title": title.render,
    "create": create.render,
    "hub": hub.render,
    "uno": uno.render,
    "checkers": checkers.render,
    "connect4": connect4.render,
    "store": store.render,
    "versus": versus.render,
    "pause": pause.render,
    "wardrobe": wardrobe.render,
    "howto": howto.render,
    "champ_intro": champ.render_intro,
    "champ_rules": champ.render_rules,
    "champ_score": champ.render_score,
    "champ_final": champ.render_final,
    "online": online.render_menu,
    "lobby": online_room.render,  # the online room: friends walk about, chat and sit down at the tables
    "online_table": online_table.render,
}

ui.fresh_page()  # first of all: a full run always starts at the top of the page (see ui.fresh_page)
ui.setup_page()
state.init()
if st.session_state.player is None and st.session_state.screen != "howto":  # for example after a page reload
    st.session_state.screen = "title"  # ("How to play" can be opened from the title screen, before a name is given)
sound.render_music()  # first, so a new screen changes the tune at once (a table's first run takes a few seconds)
with st.container(key="game_frame"):  # one glowing frame around the whole game, buttons included (ui.py)
    shown = st.session_state.get("_screen_shown")  # a new screen: the last picture stays behind until its own arrives
    st.session_state["_screen_shown"] = st.session_state.screen
    if shown == st.session_state.screen:
        ui.backdrop(None, shown)  # (the box is always there, empty, so nothing after it ever moves: a moved element
                                  # is rebuilt by the browser, and that blinked black)
    elif st.session_state.get("_fade_next") and ui.ANIMATIONS:  # through black (ui._fade_style)
        ui.backdrop(st.session_state.get("_last_src"), st.session_state.screen,
                    "black" if shown in ui.BROWSER_SCREENS else "dim")
    else:  # a plain cut: the last picture stays until the new screen's own arrives
        ui.backdrop(ui.title_backdrop() if shown == "title" or st.session_state.screen == "title"
                    else st.session_state.get("_last_src"), st.session_state.screen)
    toasts = st.container(key="game_toasts")  # (made here, filled at the end: always second, whatever the screen)
    try:
        SCREENS[st.session_state.screen]()
    except Exception as problem:  # never a black screen: log it, say so, back to the arcade (state.recover)
        if not state.recover(problem):
            raise
        st.rerun()
    ui.render_toasts(toasts)  # little messages in the game's pixel font, laid on the picture (top right)
sound.render()  # play the sounds asked for during this run (A7)
