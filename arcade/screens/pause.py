"""Pause menu (Esc): resume, customize character, how to play, music level, leave the table (at a table), leave
arcade. The music is quiet while it is open (arcade/music.py)."""

from __future__ import annotations

import streamlit as st

from arcade import match, sound, state, ui
from arcade.art import scenes
from arcade.config import GAMES
from arcade.logic import cursor
from arcade.screens import howto, hub
from arcade.state import S

OPTIONS = [
    {"label": "RESUME", "action": "resume", "key": "ESC"},
    {"label": "WARDROBE", "action": "wardrobe"},
    {"label": "HOW TO PLAY", "action": "howto"},
    {"label": "LEAVE ARCADE", "action": "leave"},
]
LEAVE_TABLE = {"label": "LEAVE TABLE", "action": "leave_table"}
PLAY_ONLINE = {"label": "PLAY ONLINE", "action": "online"}
LEAVE_LOBBY = {"label": "LEAVE LOBBY", "action": "leave_lobby"}


def music_option(level: str) -> dict:
    """The music row: shows the level and goes round high, medium, low (never off: M switches the music off)."""
    return {"label": f"MUSIC: {level.upper()}", "action": "music"}


def options(paused_from: str | None, level: str = "high") -> list[dict]:
    """The menu. At a game table there is one more choice: leave the table (task B4). In the room: play online. In
    the online room: leave the lobby, which takes the place of leaving the arcade."""
    if paused_from == "lobby":
        return OPTIONS[:3] + [music_option(level), LEAVE_LOBBY]
    if paused_from == "online_table":  # (no wardrobe in the middle of a game with friends)
        return [OPTIONS[0], OPTIONS[2], music_option(level), LEAVE_TABLE]
    extra = LEAVE_TABLE if paused_from in GAMES else PLAY_ONLINE
    return OPTIONS[:3] + [music_option(level), extra] + OPTIONS[3:]


def change_music() -> None:
    """Next music level, kept with the player's progress."""
    S.player["music"] = sound.next_level(S.player.get("music", "high"))
    state.save()


def leave_table() -> None:
    """Give up the game at this table. Free play: a loss (no coins). Championship: the whole run ends."""
    sound.play("lose")
    champ = S.match and S.match["mode"] == "champ"
    S.champ = None if champ else S.champ
    match.back_to_hub(centre=bool(champ))
    ui.toast("You left the championship." if champ else "You left the table. No coins this time.")


def render() -> None:
    online_table = S.paused_from == "online_table"  # an online game goes on while this menu is open
    at_table = S.paused_from in GAMES or online_table
    online_room = S.paused_from == "lobby"
    behind = S.get("pause_behind") if (at_table or online_room) and S.get("pause_behind") is not None else hub.still()
    menu = options(S.paused_from, S.player.get("music", "high"))
    # The keys are read before drawing, so this one picture already shows where the highlight went (no second run)
    key = ui.keys("pause", {"Up": "up", "Down": "down", "Enter": "choose"})  # Up / Down move, Enter chooses
    focus = cursor.clamp(S.get("pause_focus"), len(menu))  # the yellow highlight starts on RESUME
    if key in ("up", "down"):
        focus = S.pause_focus = cursor.step(focus, key, len(menu))
        sound.play("blip")
    img, regions = scenes.menu_panel(behind, "PAUSED", menu, focus=focus)
    ui.show(ui.screen(), img)
    point = ui.click()
    action = ui.hit(regions, point)
    if key == "choose":
        action = ("menu", menu[focus]["action"])
    bar = ui.bar("pause", [1] * 6)  # invisible: the menu is on the picture
    with bar[0]:
        resume = ui.button("Resume", "pause_resume", "Esc", type="primary")
    with bar[1]:
        wardrobe = ui.button("Wardrobe", "pause_wardrobe", disabled=online_table)
    with bar[2]:
        how = ui.button("How to play", "pause_howto", "H")
    with bar[3]:
        louder = ui.button("Music level", "pause_music")
    quit_table = go_online = False
    with bar[4]:
        if at_table:
            quit_table = ui.button("Leave table", "pause_leave_table")
        elif online_room:
            quit_table = ui.button("Leave lobby", "pause_leave_lobby")
        else:
            go_online = ui.button("Play online", "pause_online", "O")
    with bar[-1]:
        leave = ui.button("Leave arcade", "pause_leave", disabled=online_room)
    if louder or action == ("menu", "music"):  # stays in the menu, with the highlight on this row
        change_music()
        sound.play("blip")
        S.pause_focus = [option["action"] for option in menu].index("music")
        st.rerun()
    if action or resume or wardrobe or how or quit_table or go_online or leave:
        S.pause_focus = None  # the menu opens on RESUME again next time

    if resume or action == ("menu", "resume"):
        state.go(S.paused_from or "hub")
        st.rerun()
    if wardrobe or action == ("menu", "wardrobe"):
        S.wardrobe_focus = None
        state.go("wardrobe")
        st.rerun()
    if how or action == ("menu", "howto"):
        howto.open_from("pause")
        st.rerun()
    if online_room and (quit_table or action == ("menu", "leave_lobby")):  # back to the online menu
        from arcade.screens import online as online_screens

        sound.play("blip")
        online_screens.leave()
        st.rerun()
    if online_table and (quit_table or action == ("menu", "leave_table")):
        from arcade.screens import online_table as table_screen

        sound.play("lose")
        table_screen.leave_table()
        st.rerun()
    if at_table and (quit_table or action == ("menu", "leave_table")):
        leave_table()
        st.rerun()
    if not at_table and not online_room and (go_online or action == ("menu", "online")):  # create or join a lobby with friends
        from arcade.screens import online as online_screens

        state.save()
        online_screens.to_title("online")  # the title screen's online box
        st.rerun()
    if not online_room and (leave or action == ("menu", "leave")):
        state.save()  # progress is kept for next time
        S.match = S.game = S.result = S.champ = None
        S.naming = False
        state.go("title")  # back to the title's menu (offline, online, log out)
        st.rerun()
