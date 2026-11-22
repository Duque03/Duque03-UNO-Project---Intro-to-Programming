"""Going online and back. The online menu (CREATE LOBBY / JOIN A LOBBY / PLAY OFFLINE / GO BACK) and the join box are
drawn by the title screen itself (arcade/title_view.py), so they keep its animation and never flash black; the lobby
is a room like the arcade (screens/online_room.py). This file only sends the player to the right place.
"""

from __future__ import annotations

import streamlit as st

from arcade import online
from arcade.state import S


def to_title(step: str = "mode", notice: str = "") -> None:
    """To the title screen, open on a step: "mode" (PLAY OFFLINE / PLAY ONLINE...) or "online" (the online box),
    with an optional message in the online box."""
    count = (S.get("title_start") or {}).get("n", 0) + 1
    S.title_start = {"step": step, "n": count}
    if notice:
        S.title_notice = {"text": notice, "n": count}
    S.screen = "title"


def leave(notice: str = "") -> None:
    """Leave the lobby (and any game in it): back to the choice of offline or online (Miguel's call), or to the online
    box with a message when the lobby itself went away."""
    if S.get("lobby_code"):
        online.lobbies().leave(S.lobby_code, S.player["name"])
    S.lobby_code = None
    to_title("online" if notice else "mode", notice)


def render_menu() -> None:
    """(The old online menu screen: now the title screen's online box.)"""
    to_title("online")
    st.rerun()
