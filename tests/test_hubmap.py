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


# ----- A5: bots and the store counter block the way too

BOT = (100, 120)


def test_you_cannot_step_into_a_bot():
    beside = (BOT[0] - 8, BOT[1])
    assert hubmap.step_from(beside, 1, 0, 8, others=[BOT]) == beside  # rejected: the step would end on the bot
    assert hubmap.step_from(beside, -1, 0, 8, others=[BOT]) == (BOT[0] - 16, BOT[1])  # allowed: walking away


def test_a_bot_somewhere_else_does_not_block():
    start = (BOT[0] - 8, BOT[1])
    assert hubmap.step_from(start, 1, 0, 8, others=[(250, 160)]) == BOT


def test_you_cannot_step_onto_the_counter():
    left, _, right, bottom = hubmap.COUNTER_BODY
    x = (left + right) // 2
    below = (x, bottom + 6)
    assert hubmap.blocked((x, bottom - 1))
    assert hubmap.step_from(below, 0, -1, 8) == below  # rejected
    assert hubmap.step_from(below, 1, 0, 8) == (x + 8, bottom + 6)  # allowed: along the counter


def test_the_store_can_still_be_used():
    stand = hubmap.SPOTS["store"]["stand"]
    assert not hubmap.blocked(stand)
    assert hubmap.near_spot(stand) == "store"


def test_a_clicked_walk_stops_before_a_bot():
    start, end = (BOT[0] - 40, BOT[1]), (BOT[0] + 40, BOT[1])
    stop = hubmap.walk_line(start, end, others=[BOT])
    assert start[0] < stop[0] < BOT[0]
    assert not hubmap.blocked(stop, others=[BOT])


def test_a_clicked_walk_goes_all_the_way_when_the_line_is_free():
    start, end = (100, 160), (200, 160)
    assert hubmap.walk_line(start, end, others=[BOT]) == end


def test_a_clicked_walk_stops_before_a_table():
    cx, cy = hubmap.SPOTS["checkers"]["center"]
    stop = hubmap.walk_line((cx, cy + 40), (cx, cy - 30))
    assert cy + 4 < stop[1] < cy + 40
    assert not hubmap.blocked(stop)


@pytest.mark.parametrize("pos", [hubmap.SPAWN, hubmap.CENTER] + [spot["stand"] for spot in hubmap.SPOTS.values()])
def test_nobody_starts_inside_a_bot(pos):
    from arcade import bots
    homes = [bot["home"] for bot in bots.BOTS]
    assert not hubmap.blocked(pos, others=homes)
