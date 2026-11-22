"""Online (Miguel, 22 Nov): pressing E at a table where a friend waits used to start the game before the player had
walked to the chair; now the player sits only once there. And Esc at an online table opens the pause menu (the game
goes on meanwhile) instead of leaving the game."""
import random

import pytest
import streamlit as st

from arcade import bots, hubmap, online
from arcade.logic.lobby import Lobbies
from arcade.screens import online_room, pause


class Session(dict):
    __getattr__ = dict.get

    def __setattr__(self, key, value):
        self[key] = value


class Rerun(Exception):
    pass


@pytest.fixture
def room(monkeypatch):
    lobbies = Lobbies(random.Random(3))
    monkeypatch.setattr(online, "lobbies", lambda: lobbies)
    card = lambda name: {"name": name, "look": bots.look(bots.get("JOHN")), "tag": None}  # noqa: E731
    code = lobbies.create(card("ANA"))
    lobbies.join(code, card("BRUNO"))
    lobbies.sit(code, "BRUNO", "connect4")  # a friend is waiting at Connect Four
    s = Session(screen="lobby", lobby_code=code, player={"name": "ANA"})
    monkeypatch.setattr(online_room, "S", s)
    monkeypatch.setattr(st, "session_state", s, raising=False)

    def rerun(*_, **__):
        raise Rerun

    monkeypatch.setattr(st, "rerun", rerun)
    hub = {"pos": hubmap.SPOTS["connect4"]["stand"], "dir": "up", "walk": None, "pressed": 0}
    return lobbies, code, hub


def test_the_player_walks_to_the_chair_before_sitting(room):
    lobbies, code, hub = room
    online_room._interact(code, "ANA", lobbies.get(code), hub)
    assert hub["walk"]["game"] == "connect4"  # walking there...
    assert lobbies.get(code).table_of("ANA") is None  # ...and the game has not started yet
    online_room._finish_walk(code, "ANA", hub)
    assert lobbies.get(code).table_of("ANA") is not None  # sitting down starts it (2 of 2)
    assert hub["walk"] is None


def test_a_chair_taken_meanwhile_leaves_the_player_standing(room, monkeypatch):
    lobbies, code, hub = room
    toasts = []
    monkeypatch.setattr(online_room.ui, "toast", toasts.append)
    online_room._interact(code, "ANA", lobbies.get(code), hub)
    lobbies.join(code, {"name": "CAIO", "look": bots.look(bots.get("DEAN")), "tag": None})
    lobbies.sit(code, "CAIO", "connect4")  # someone else was quicker: that game starts without ANA
    online_room._finish_walk(code, "ANA", hub)
    assert lobbies.get(code).table_of("ANA") is None and toasts


def test_the_pause_menu_at_an_online_table():
    labels = [option["label"] for option in pause.options("online_table")]
    assert labels == ["RESUME", "HOW TO PLAY", "MUSIC: HIGH", "LEAVE TABLE"]
