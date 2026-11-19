"""The online lobbies, shared by every player connected to this server (see arcade/logic/lobby.py).

st.cache_resource keeps one Lobbies object for the whole server, so all players' sessions see the same lobbies.
They live in memory: if the server restarts, the lobbies are gone (saved players are not: they are in the database).
"""

from __future__ import annotations

import streamlit as st

from arcade import catalog
from arcade import player as player_model
from arcade.logic.lobby import Lobbies


@st.cache_resource
def lobbies() -> Lobbies:
    return Lobbies()


def card(player: dict) -> dict:
    """How a player appears to the others: name, look and name tag."""
    return {"name": player["name"], "look": player_model.look(player),
            "tag": catalog.spec_for("name", player["equipped"].get("name"))}
