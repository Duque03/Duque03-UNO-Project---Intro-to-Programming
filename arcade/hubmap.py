"""Where everything stands inside the arcade room.

All positions are on the small 320x180 base canvas. A character's position is
the spot where its feet touch the floor.
"""

from __future__ import annotations

import math
from functools import lru_cache

from arcade.config import SCALE

FLOOR_TOP = 60
WALK_AREA = (14, 74, 306, 172)  # left, top, right, bottom of the floor you can walk on
SPAWN = (160, 166)  # by the door
CENTER = (160, 146)

# Each interactive spot: where it is, where the player stands to use it, and
# where bots sit ("seats": across the table first, then left, then right).
SPOTS = {
    "uno": {"kind": "table", "label": "UNO", "center": (58, 126), "stand": (58, 148),
            "seats": [(58, 116), (30, 131), (86, 131)]},
    "checkers": {"kind": "table", "label": "CHECKERS", "center": (160, 108), "stand": (160, 130),
                 "seats": [(160, 98), (132, 113), (188, 113)]},
    "connect4": {"kind": "table", "label": "CONNECT 4", "center": (258, 126), "stand": (258, 148),
                 "seats": [(258, 116), (230, 131), (286, 131)]},
    "store": {"kind": "store", "label": "STORE", "center": (224, 40), "stand": (224, 80), "seats": []},
    "champ": {"kind": "champ", "label": "CHAMPIONSHIP", "center": (43, 40), "stand": (43, 80), "seats": []},
}

# Clickable areas of the objects (base coordinates: left, top, right, bottom).
CLICK_BOXES = {
    "uno": (34, 110, 82, 142),
    "checkers": (136, 92, 184, 124),
    "connect4": (234, 110, 282, 142),
    "store": (176, 12, 272, 68),
    "champ": (26, 2, 60, 68),
}

# How close you must be before a spot offers "PLAY", "SHOP" or the championship.
TABLE_REACH = (40, 30)  # half-width and half-height of the zone around a table
COUNTER_REACH = (30, 88)  # half-width, and how far down the floor the zone goes
TABLE_BODY = (25, 9)  # the part of a table you cannot walk through (half-width, half-height)
BOT_BODY = (8, 7)  # the part of a bot you cannot walk through, around its feet (half-width, half-height)
COUNTER_BODY = (172, FLOOR_TOP, 276, 76)  # the strip of floor right in front of the store counter


def clamp(x: float, y: float) -> tuple[int, int]:
    """Keep a point inside the walkable floor."""
    left, top, right, bottom = WALK_AREA
    return (int(max(left, min(right, x))), int(max(top, min(bottom, y))))


def distance(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _inside_oval(pos, centre, half_w: float, half_h: float) -> bool:
    return ((pos[0] - centre[0]) / half_w) ** 2 + ((pos[1] - centre[1]) / half_h) ** 2 <= 1


def near_spot(pos) -> str | None:
    """Which spot (if any) the player is close enough to use. Tables can be approached from any side."""
    best, best_distance = None, None
    for key, spot in SPOTS.items():
        if spot["kind"] == "table":
            cx, cy = spot["center"]
            close = _inside_oval(pos, (cx, cy + 6), *TABLE_REACH)
        else:
            close = abs(pos[0] - spot["stand"][0]) <= COUNTER_REACH[0] and pos[1] <= COUNTER_REACH[1]
        if close:
            gap = distance(pos, spot["stand"])
            if best is None or gap < best_distance:
                best, best_distance = key, gap
    return best


def blocked(pos, others=()) -> bool:
    """True when feet cannot go there: inside a table, at the store counter, or on a bot.

    others: the positions of the bots (their feet).
    """
    if table_at(pos) is not None:
        return True
    left, top, right, bottom = COUNTER_BODY
    if left <= pos[0] <= right and top <= pos[1] <= bottom:
        return True
    return any(_inside_oval(pos, other, *BOT_BODY) for other in others)


def table_at(pos) -> str | None:
    """The table whose body covers this point, if any."""
    for key, spot in SPOTS.items():
        if spot["kind"] == "table":
            cx, cy = spot["center"]
            if _inside_oval(pos, (cx, cy + 4), *TABLE_BODY):
                return key
    return None


def step_from(pos, dx: int, dy: int, size: int, others=()) -> tuple[int, int]:
    """Where one WASD step ends: stays on the floor and never ends inside a table, the counter or a bot."""
    target = clamp(pos[0] + dx * size, pos[1] + dy * size)
    return pos if blocked(target, others) else target


def walk_line(start, end, others=()) -> tuple[int, int]:
    """Where a clicked walk ends: along the straight line, stopping just before the first thing in the way."""
    if blocked(start, others):  # already stuck (should not happen): do not stop the walk
        return end
    count = int(max(abs(end[0] - start[0]), abs(end[1] - start[1])))
    last = tuple(start)
    for i in range(1, count + 1):
        t = i / count
        point = (round(start[0] + (end[0] - start[0]) * t), round(start[1] + (end[1] - start[1]) * t))
        if blocked(point, others):
            break
        last = point
    return last


def spot_at(base_x: float, base_y: float) -> str | None:
    """Which object (if any) is under a click."""
    for key, (left, top, right, bottom) in CLICK_BOXES.items():
        if left <= base_x <= right and top <= base_y <= bottom:
            return key
    return None


def to_base(screen_x: float, screen_y: float) -> tuple[float, float]:
    return screen_x / SCALE, screen_y / SCALE


def facing(start, end) -> str:
    """Direction a character looks while walking from start to end."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    if abs(dx) > abs(dy):
        return "right" if dx > 0 else "left"
    return "down" if dy > 0 else "up"


# ----- the floor map for the browser (walking is drawn in the browser, see arcade/room.py)
#
# The browser moves the player 60 times a second, far too often to ask Python
# each time. So Python answers every question in advance, for every pixel of
# the room, and sends the answers as two small tables:
#   blocked: 1 where feet can never stand (outside the floor, tables, counter)
#   near:    which spot (if any) you are close enough to use, as a number
# Bots move, so they are not in the table: the browser checks BOT_BODY itself.

NEAR_CODES = {None: 0, "uno": 1, "checkers": 2, "connect4": 3, "store": 4, "champ": 5}


def _runs(values) -> list[int]:
    """Run-length encoding: [value, count, value, count, ...]. Long runs of the same value become two numbers."""
    out: list[int] = []
    for value in values:
        if out and out[-2] == value:
            out[-1] += 1
        else:
            out += [value, 1]
    return out


def unruns(runs: list[int]) -> list[int]:
    """Undo _runs (the browser does the same in JavaScript)."""
    out: list[int] = []
    for i in range(0, len(runs), 2):
        out += [runs[i]] * runs[i + 1]
    return out


@lru_cache(maxsize=1)
def floor_map() -> dict:
    """Both tables for the whole 320x180 room, row by row (index = y * 320 + x)."""
    from arcade.config import BASE_H, BASE_W

    blocked, near = [], []
    for y in range(BASE_H):
        for x in range(BASE_W):
            on_floor = clamp(x, y) == (x, y)
            blocked.append(0 if on_floor and not blocked_by_furniture((x, y)) else 1)
            near.append(NEAR_CODES[near_spot((x, y))] if on_floor else 0)
    return {"w": BASE_W, "h": BASE_H, "blocked": _runs(blocked), "near": _runs(near),
            "bot_body": list(BOT_BODY), "walk_area": list(WALK_AREA)}


def blocked_by_furniture(pos) -> bool:
    """blocked() without the bots: tables and the store counter."""
    return blocked(pos, ())
