"""What the bots do while nobody plays with them (task A4).

Every tick (see IDLE_EVERY in config.py) each bot may stay put, turn to look
another way, or shuffle one small step. A bot never strays further than WANDER
from its home spot and never steps into furniture, another bot or the player.
No Streamlit here, so it can be tested like the game rules.
"""

from __future__ import annotations

import random

from arcade import hubmap

WANDER = 12  # how far a bot may stray from its home spot (base pixels, across and up/down)
SHUFFLE = 4  # length of one small step
CHANCE_TURN = 0.3
CHANCE_STEP = 0.3

_STEPS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


def _allowed(pos, home, others) -> bool:
    if abs(pos[0] - home[0]) > WANDER or abs(pos[1] - home[1]) > WANDER:
        return False
    on_floor = hubmap.clamp(*pos) == tuple(pos) or tuple(pos) == tuple(home)
    return on_floor and not hubmap.blocked(pos, others)


def idle_tick(bots: dict, homes: dict, player_pos, rng: random.Random) -> dict:
    """One idle moment. bots: name -> {"pos", "dir"}. Returns a new dictionary (the given one is not changed)."""
    new = {name: dict(bot) for name, bot in bots.items()}
    for name in sorted(new):
        bot = new[name]
        roll = rng.random()
        if roll < CHANCE_TURN:
            bot["dir"] = rng.choice([d for d in _STEPS if d != bot["dir"]])
        elif roll < CHANCE_TURN + CHANCE_STEP:
            direction = rng.choice(list(_STEPS))
            dx, dy = _STEPS[direction]
            target = (bot["pos"][0] + dx * SHUFFLE, bot["pos"][1] + dy * SHUFFLE)
            others = [player_pos] + [other["pos"] for key, other in new.items() if key != name]
            bot["dir"] = direction
            if _allowed(target, homes[name], others):
                bot["pos"] = target
    if new == bots and new:  # never a completely still moment: someone looks around
        name = rng.choice(sorted(new))
        new[name]["dir"] = rng.choice([d for d in _STEPS if d != new[name]["dir"]])
    return new
