"""The floor map sent to the browser must give exactly the same answers as the rules in hubmap."""

import random

from arcade import hubmap
from arcade.config import BASE_H, BASE_W


def _cell(table, x, y):
    return table[y * BASE_W + x]


def test_runs_round_trip():
    values = [0, 0, 0, 1, 1, 0, 2, 2, 2, 2]
    assert hubmap.unruns(hubmap._runs(values)) == values
    assert hubmap._runs([]) == []


def test_map_covers_the_whole_room():
    fm = hubmap.floor_map()
    assert len(hubmap.unruns(fm["blocked"])) == BASE_W * BASE_H
    assert len(hubmap.unruns(fm["near"])) == BASE_W * BASE_H


def test_blocked_cells_match_the_rules():
    fm = hubmap.floor_map()
    blocked = hubmap.unruns(fm["blocked"])
    rng = random.Random(1)
    points = [(rng.randrange(BASE_W), rng.randrange(BASE_H)) for _ in range(3000)]
    points += [spot["stand"] for spot in hubmap.SPOTS.values()] + [hubmap.SPAWN, hubmap.CENTER]
    for x, y in points:
        can_stand = hubmap.clamp(x, y) == (x, y) and not hubmap.blocked((x, y))
        assert _cell(blocked, x, y) == (0 if can_stand else 1), (x, y)


def test_near_cells_match_the_rules():
    fm = hubmap.floor_map()
    near = hubmap.unruns(fm["near"])
    codes = {value: key for key, value in hubmap.NEAR_CODES.items()}
    left, top, right, bottom = hubmap.WALK_AREA
    rng = random.Random(2)
    for _ in range(3000):
        x, y = rng.randint(left, right), rng.randint(top, bottom)
        assert codes[_cell(near, x, y)] == hubmap.near_spot((x, y)), (x, y)


def test_every_spot_can_be_reached_and_used():
    fm = hubmap.floor_map()
    blocked, near = hubmap.unruns(fm["blocked"]), hubmap.unruns(fm["near"])
    for key, spot in hubmap.SPOTS.items():
        x, y = spot["stand"]
        assert _cell(blocked, x, y) == 0
        assert _cell(near, x, y) == hubmap.NEAR_CODES[key]


def test_outside_the_floor_is_always_blocked():
    fm = hubmap.floor_map()
    blocked = hubmap.unruns(fm["blocked"])
    assert _cell(blocked, 0, 0) == 1
    assert _cell(blocked, BASE_W - 1, BASE_H - 1) == 1
    assert _cell(blocked, 160, hubmap.FLOOR_TOP - 5) == 1
