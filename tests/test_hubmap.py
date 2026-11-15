"""The arcade room: where you can walk and when a table offers PLAY."""

import pytest

from arcade import hubmap


@pytest.mark.parametrize("key", ["uno", "checkers", "connect4", "store", "champ"])
def test_standing_at_a_spot_counts_as_near(key):
    assert hubmap.near_spot(hubmap.SPOTS[key]["stand"]) == key


@pytest.mark.parametrize("key", ["uno", "checkers", "connect4"])
def test_a_table_can_be_approached_from_any_side(key):
    cx, cy = hubmap.SPOTS[key]["center"]
    for dx, dy in ((-30, 6), (30, 6), (0, -16), (0, 30)):
        assert hubmap.near_spot((cx + dx, cy + dy)) == key


def test_the_door_is_not_near_anything():
    assert hubmap.near_spot(hubmap.SPAWN) is None
    assert hubmap.near_spot(hubmap.CENTER) is None


def test_far_from_the_counter_is_not_near_the_store():
    x, _ = hubmap.SPOTS["store"]["stand"]
    assert hubmap.near_spot((x, 120)) != "store"


def test_clamp_keeps_you_on_the_floor():
    left, top, right, bottom = hubmap.WALK_AREA
    assert hubmap.clamp(-50, -50) == (left, top)
    assert hubmap.clamp(9999, 9999) == (right, bottom)


def test_you_cannot_step_into_a_table():
    cx, cy = hubmap.SPOTS["checkers"]["center"]
    below = (cx, cy + 16)
    assert not hubmap.blocked(below)
    assert hubmap.blocked((cx, cy + 4))
    assert hubmap.step_from(below, 0, -1, 8) == below  # rejected: the step would end inside the table
    assert hubmap.step_from(below, 0, 1, 8) == (cx, cy + 24)  # allowed: walking away


def test_nobody_starts_or_sits_inside_a_table():
    assert not hubmap.blocked(hubmap.SPAWN)
    assert not hubmap.blocked(hubmap.CENTER)
    for spot in hubmap.SPOTS.values():
        assert not hubmap.blocked(spot["stand"])


def test_facing_follows_the_bigger_movement():
    assert hubmap.facing((0, 0), (5, 1)) == "right"
    assert hubmap.facing((0, 0), (-5, 1)) == "left"
    assert hubmap.facing((0, 0), (1, 5)) == "down"
    assert hubmap.facing((0, 0), (1, -5)) == "up"
