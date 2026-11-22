"""The opponent picker is drawn over the live room (Miguel: the picture behind the old picker jumped). E at a table
opens it, PLAY (with the right number of bots) starts the walk to the table, BACK or a wrong pick does nothing."""
import pytest
import streamlit as st

from arcade import bots, hubmap, match, room, state
from arcade import player as player_model
from arcade.screens import hub


class Session(dict):
    """A stand-in for st.session_state (a dict that also has attributes)."""

    __getattr__ = dict.get

    def __setattr__(self, key, value):
        self[key] = value


@pytest.fixture
def session(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCADE_DB", str(tmp_path / "arcade.db"))
    me = player_model.new_player("TESTER")
    s = Session(screen="hub", player=me, match=None, game=None,
                hub={"pos": hubmap.SPOTS["uno"]["stand"], "dir": "up", "walk": None, "pressed": 0,
                     "bots": {b["name"]: {"pos": b["home"], "dir": b["dir"]} for b in bots.BOTS}})
    for module in (hub, state, match):
        monkeypatch.setattr(module, "S", s)
    monkeypatch.setattr(st, "session_state", s, raising=False)
    return s


def test_E_at_a_table_opens_the_picker_over_the_room(session):
    hub._interact("uno")
    assert session.screen == "hub"  # no new screen: the room stays, the picker is drawn on it
    data = hub._versus_data()
    assert data["needed"] == 3 and data["title"] == "UNO: CHOOSE 3 OPPONENTS"
    assert [card["name"] for card in data["cards"]] == bots.BOT_NAMES
    assert len(data["prizes"]) == 4  # (every way of choosing 3 of the 4 bots has its prize line)
    first = data["n"]
    hub._interact("checkers")
    assert hub._versus_data()["n"] == first + 1 and hub._versus_data()["needed"] == 1  # (a new number: it opens again)


def test_play_with_the_bots_picked_starts_the_walk(session):
    hub._interact("connect4")
    hub._versus_answer({"picked": [bots.BOT_NAMES[0]], "n": 5})
    assert session.hub["versus"] is None
    assert session.match["game"] == "connect4" and session.match["bots"] == [bots.BOT_NAMES[0]]
    assert session.hub["walk"]["then"] == "start_game"


@pytest.mark.parametrize("picked", [None, [], ["NOBODY"], bots.BOT_NAMES[:2]])
def test_back_or_a_wrong_pick_starts_nothing(session, picked):
    hub._interact("checkers")
    hub._versus_answer({"picked": picked, "n": 5})
    assert session.hub["versus"] is None and session.match is None and session.hub["walk"] is None


def test_the_room_gets_the_picker_pieces_once(session):
    hub._interact("uno")
    sent = set()
    data = room.scene(sent, actors=state.hub_actors(), coins=0, champ_locked=True, bubbles={}, player=hub._player_target(),
                      versus=hub._versus_data())
    pieces = data["versus"]
    assert pieces["names"] == bots.BOT_NAMES and len(pieces["cards"]) == len(bots.BOT_NAMES)
    assert pieces["frame"] in data["assets"] and pieces["playOn"] in data["assets"]
    again = room.scene(sent, actors=state.hub_actors(), coins=0, champ_locked=True, bubbles={},
                       player=hub._player_target(), versus=hub._versus_data())
    assert pieces["frame"] not in again["assets"]  # (already in the browser: not sent again)
