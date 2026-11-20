"""What the bots do in the arcade while nobody plays with them: they walk around the room, stop to look at the
machines, the store, the dance pad or a table, and now and then two of them sit down at a table and play together.

Python decides where each bot goes and the way there (a path round the tables and the counter); the browser walks it
smoothly (arcade/room.py). A bot is {"pos", "dir"} plus, while it does something:
    "doing"   "stay" (standing somewhere), "walk", "play" (at a table with another bot) or "talk" (with the player)
    "until"   when that ends (time.time())
    "path"    the points of its walk, from where it was to "pos"; "t0" when it set off; "pid" a number for the walk
    "table"   the table it plays at, while it plays
No Streamlit here, so it is tested like the game rules (tests/test_wander.py).
"""

from __future__ import annotations

import math
import random
from collections import deque
from functools import lru_cache

from arcade import hubmap

SPEED = 26  # walking speed of a bot, small-canvas pixels per second (the player walks at 72)
CELL = 4  # the grid the paths are found on
STAY = (4.0, 10.0)  # how long a bot stands somewhere before it moves on (seconds)
PLAY = (25.0, 45.0)  # how long two bots play at a table
TALK = 7.0  # how long a bot stands still facing the player after being talked to
GAME_CHANCE = 0.03  # each moment, the chance that two free bots go and play at a table
SEAT_FACING = ["down", "right", "left"]  # across the table, left seat, right seat (as in match.py)

# Places worth a look: (where to stand, which way to look). The homes of the bots count too.
SPOTS = [
    ((88, 76), "up"), ((120, 76), "up"), ((152, 76), "up"),  # the three machines
    ((44, 80), "up"), ((68, 78), "up"),  # the championship cabinet, the gumball machine
    ((200, 80), "up"), ((248, 80), "up"),  # the store window
    ((292, 78), "up"),  # the prize machine
    ((22, 100), "left"), ((22, 140), "left"), ((298, 104), "right"), ((298, 146), "right"),  # side machines
    ((118, 162), "down"), ((200, 150), "down"), ((160, 88), "down"), ((108, 112), "left"), ((212, 112), "right"),
]


def _free_point(x: float, y: float) -> bool:
    """Feet can stand here, with a little room around them (walls, tables and the counter only)."""
    return _free_at(int(round(x)), int(round(y)))


@lru_cache(maxsize=None)
def _floor(x: int, y: int) -> bool:
    return hubmap.clamp(x, y) == (x, y) and not hubmap.blocked_by_furniture((x, y))


@lru_cache(maxsize=None)
def _free_at(x: int, y: int) -> bool:
    return all(_floor(x + dx, y + dy) for dx, dy in ((0, 0), (-3, -2), (3, -2), (-3, 2), (3, 2)))


@lru_cache(maxsize=1)
def _grid() -> dict:
    """Every free cell of the floor grid: (column, row) -> its middle point."""
    left, top, right, bottom = hubmap.WALK_AREA
    cells = {}
    for row in range((bottom - top) // CELL + 1):
        for col in range((right - left) // CELL + 1):
            point = (left + col * CELL, top + row * CELL)
            if _free_point(*point):
                cells[(col, row)] = point
    return cells


def _cell_of(point) -> tuple[int, int] | None:
    """The free cell nearest to a point."""
    left, top, _, _ = hubmap.WALK_AREA
    col, row = round((point[0] - left) / CELL), round((point[1] - top) / CELL)
    grid = _grid()
    best, best_gap = None, None
    for dc in range(-3, 4):
        for dr in range(-3, 4):
            cell = (col + dc, row + dr)
            if cell in grid:
                gap = math.dist(grid[cell], point)
                if best is None or gap < best_gap:
                    best, best_gap = cell, gap
    return best


def clear_line(a, b, room: bool = False) -> bool:
    """A straight walk from a to b does not cross a table, the counter or a wall (the feet; with room=True, also
    keeping the little room round them that the paths keep, see _free_point)."""
    steps = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) or 1
    check = _free_point if room else (lambda x, y: _floor(int(round(x)), int(round(y))))
    return all(check(a[0] + (b[0] - a[0]) * i / steps, a[1] + (b[1] - a[1]) * i / steps) for i in range(steps + 1))


def find_path(start, goal) -> list | None:
    """The points of a walk from start to goal round the furniture (start first, goal last), or None."""
    first, last = _cell_of(start), _cell_of(goal)
    if first is None or last is None:
        return None
    grid, came = _grid(), {first: None}
    queue = deque([first])
    while queue:
        cell = queue.popleft()
        if cell == last:
            break
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            step = (cell[0] + dc, cell[1] + dr)
            if step in grid and step not in came and (dc == 0 or dr == 0 or clear_line(grid[cell], grid[step], True)):
                came[step] = cell
                queue.append(step)
    if last not in came:
        return None
    cells = [last]
    while came[cells[-1]] is not None:
        cells.append(came[cells[-1]])
    points = [tuple(start)] + [grid[cell] for cell in reversed(cells)] + [tuple(goal)]
    # keep only the corners: from each point, go straight to the farthest one that can be seen
    out, i = [points[0]], 0
    while i < len(points) - 1:
        j = len(points) - 1
        while j > i + 1 and not clear_line(points[i], points[j], room=0 < i and j < len(points) - 1):
            j -= 1
        out.append(points[j])
        i = j
    return [[int(round(x)), int(round(y))] for x, y in out]


def _new_pid(bot: dict, now: float) -> int:
    """A new number for a walk (the browser starts a walk when the number changes). It only ever grows, even after
    the bots were sent home (their numbers are then gone)."""
    return max(bot.get("pid", 0) + 1, int(now * 1000))


def path_length(path) -> float:
    return sum(math.dist(a, b) for a, b in zip(path, path[1:]))


def where(bot: dict, now: float) -> tuple[tuple[int, int], str]:
    """Where a bot is right now (along its walk, if it walks) and which way it looks."""
    path = bot.get("path")
    if bot.get("doing") != "walk" or not path or len(path) < 2:
        return tuple(bot["pos"]), bot["dir"]
    left = max(0.0, now - bot["t0"]) * SPEED
    for a, b in zip(path, path[1:]):
        piece = math.dist(a, b)
        if left <= piece and piece > 0:
            share = left / piece
            return (int(round(a[0] + (b[0] - a[0]) * share)), int(round(a[1] + (b[1] - a[1]) * share))), \
                hubmap.facing(a, b)
        left -= piece
    return tuple(bot["pos"]), bot["dir"]


def settle(bot: dict, now: float) -> dict:
    """The bot stops where it is now (a walk is cut short). Returns the bot (changed in place)."""
    pos, direction = where(bot, now)
    walking = bot.get("doing") == "walk" and now < bot.get("until", 0)
    bot["pos"], bot["path"] = pos, None
    if walking:
        bot["dir"] = direction
    bot["pid"] = _new_pid(bot, now)
    bot["doing"], bot["until"] = "stay", now
    return bot


def walk(bot: dict, goal, face: str, now: float, then: str = "stay", hold: float = 6.0) -> bool:
    """Send a bot to goal along a path; on arrival it looks `face` and does `then` for `hold` seconds."""
    start, _ = where(bot, now)
    path = find_path(start, goal)
    if path is None:
        return False
    bot["path"], bot["t0"], bot["pid"] = path, now, _new_pid(bot, now)
    bot["pos"], bot["dir"], bot["doing"] = tuple(goal), face, "walk"
    bot["until"] = now + path_length(path) / SPEED
    bot["then"], bot["hold"] = then, hold
    return True


def _taken(bots: dict, name: str) -> list:
    """Where the other bots are or are going."""
    return [tuple(other["pos"]) for key, other in bots.items() if key != name]


def _table_free(table: str, bots: dict, player_pos) -> bool:
    centre = hubmap.SPOTS[table]["center"]
    return math.dist(centre, player_pos) > 46 and not any(b.get("table") == table for b in bots.values())


def tick(bots: dict, homes: dict, player_pos, rng: random.Random, now: float) -> dict:
    """One moment in the room (every IDLE_EVERY seconds). bots: name -> bot. Returns a new dictionary."""
    new = {name: dict(bot) for name, bot in bots.items()}
    for name in sorted(new):
        bot = new[name]
        doing, until = bot.get("doing", "stay"), bot.get("until", 0)
        if doing == "walk" and now >= until:  # arrived
            bot["path"], bot["doing"] = None, bot.get("then", "stay")
            bot["until"] = now + bot.get("hold", rng.uniform(*STAY))
            continue
        if doing in ("walk", "talk") and now < until:
            continue
        if doing == "play" and now < until:
            continue
        if doing == "play":  # the game is over: both get up
            bot["table"] = None
        if doing == "stay" and now < until:
            if rng.random() < 0.25:  # standing: look around now and then
                bot["dir"] = rng.choice([d for d in ("up", "down", "left", "right") if d != bot["dir"]])
            continue
        # free: go somewhere else
        choices = SPOTS + [(homes[name], "up")]
        taken = _taken(new, name) + [tuple(player_pos)]
        options = [(spot, face) for spot, face in choices if all(math.dist(spot, other) > 14 for other in taken)
                   and math.dist(spot, bot["pos"]) > 10]
        if options:
            spot, face = rng.choice(options)
            walk(bot, spot, face, now, "stay", rng.uniform(*STAY))
    _maybe_start_game(new, player_pos, rng, now)
    return new


def _maybe_start_game(bots: dict, player_pos, rng: random.Random, now: float) -> None:
    """Now and then two bots that are only standing around go and play at a table nobody uses."""
    if any(bot.get("table") for bot in bots.values()) or rng.random() >= GAME_CHANCE:
        return
    free = [name for name in sorted(bots) if bots[name].get("doing", "stay") == "stay"]
    tables = [key for key, spot in hubmap.SPOTS.items() if spot["kind"] == "table" and _table_free(key, bots, player_pos)]
    if len(free) < 2 or not tables:
        return
    table = rng.choice(tables)
    pair = rng.sample(free, 2)
    seats = [0, rng.choice([1, 2])]
    length = rng.uniform(*PLAY)
    for name, seat in zip(pair, seats):
        bot = bots[name]
        place = hubmap.SPOTS[table]["seats"][seat]
        if walk(bot, place, SEAT_FACING[seat], now, "play", length):
            bot["table"] = table


def free_table(bots: dict, table: str, keep: list[str], homes: dict, now: float) -> None:
    """The player is about to play at this table with the bots in keep: everyone else playing or standing there
    walks home, and any game the chosen bots were playing stops."""
    for name, bot in bots.items():
        if name in keep:
            if bot.get("table"):
                bot["table"] = None
            settle(bot, now)
            continue
        near = math.dist(where(bot, now)[0], hubmap.SPOTS[table]["center"]) < 40
        if bot.get("table") == table or near:
            bot["table"] = None
            walk(bot, homes[name], "up", now)


def talk(bot: dict, player_pos, now: float) -> None:
    """The player talks to this bot: it stops and turns to face them for a moment (a bot playing at a table answers
    without getting up)."""
    if bot.get("doing") == "play":
        return
    settle(bot, now)
    pos = bot["pos"]
    bot["dir"] = hubmap.facing(pos, player_pos)
    bot["doing"], bot["until"] = "talk", now + TALK
