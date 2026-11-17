"""The room drawn in the browser: what Python sends, and how it checks what the browser reports."""

import pytest

from arcade import bots, catalog, hubmap, room
from arcade import player as player_model


def _actors():
    actors = [{"name": b["name"], "look": bots.look(b), "pos": b["home"], "dir": b["dir"],
               "tag": catalog.spec_for("name", b["tag"])} for b in bots.BOTS]
    me = player_model.new_player("MIGUEL")
    actors.append({"name": "MIGUEL", "look": player_model.look(me), "pos": hubmap.SPAWN, "dir": "up",
                   "tag": catalog.spec_for("name", None), "player": True})
    return actors


def _scene(sent, coins=0):
    return room.scene(sent, actors=_actors(), coins=coins, champ_locked=True,
                      bubbles={"uno": [{"text": "PLAY", "key": "E", "action": "interact"}]},
                      player={"seq": 1, "x": 160, "y": 166, "dir": "up"})


def test_a_position_on_the_floor_is_accepted():
    assert room.read_pos({"x": 160, "y": 166, "dir": "up"}) == ((160, 166), "up")
    assert room.read_pos({"x": "100.4", "y": 150.6, "dir": "left"}) == ((100, 151), "left")


@pytest.mark.parametrize("value", [
    {"x": 0, "y": 0, "dir": "up"},  # outside the floor
    {"x": 160, "y": 112, "dir": "up"},  # inside the checkers table
    {"x": 160, "y": 166, "dir": "sideways"},  # not a direction
    {"x": "a", "y": 166, "dir": "up"},  # not a number
    {"y": 166},  # missing x
    None, "160,166", 42,
])
def test_anything_else_is_rejected(value):
    assert room.read_pos(value) is None


def test_every_picture_is_sent_only_once():
    sent = set()
    first = _scene(sent)
    assert first["assets"], "the first frame sends the pictures"
    assert first["bg"] in first["assets"] and first["map"] in first["assets"]
    again = _scene(sent)
    assert again["assets"] == {}, "nothing is sent twice"
    richer = _scene(sent, coins=5)
    assert list(richer["assets"]) == [richer["hud"]["img"]], "only the new coin counter is sent"


def test_the_scene_lists_six_characters_and_the_bubbles_by_zone():
    data = _scene(set())
    assert len(data["actors"]) == 6
    assert [a["name"] for a in data["actors"] if a["player"]] == ["MIGUEL"]
    assert list(data["bubbles"]) == [str(hubmap.NEAR_CODES["uno"])]
    assert data["bubbles"]["1"][0]["action"] == "interact"
    assert len(data["tables"]) == 3


def test_every_picture_the_scene_uses_is_known():
    sent = set()
    data = _scene(sent)
    used = [data["bg"], data["top"], data["map"], data["hud"]["img"]]
    used += [t[k] for t in data["tables"] for k in ("img", "lit", "label")]
    used += [a["sheet"] for a in data["actors"]] + [k for a in data["actors"] for k in a["tags"]]
    used += [b["img"] for items in data["bubbles"].values() for b in items]
    assert set(used) <= sent
