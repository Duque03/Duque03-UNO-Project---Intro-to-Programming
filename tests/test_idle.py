"""A4: the bots shuffle and turn while the player does nothing."""

import random

from arcade import bots, hubmap, idle

HOMES = {bot["name"]: bot["home"] for bot in bots.BOTS}


def _start():
    return {bot["name"]: {"pos": bot["home"], "dir": bot["dir"]} for bot in bots.BOTS}


def test_bots_stay_close_to_home():
    rng, state = random.Random(1), _start()
    for _ in range(300):
        state = idle.idle_tick(state, HOMES, hubmap.CENTER, rng)
        for name, bot in state.items():
            home = HOMES[name]
            assert abs(bot["pos"][0] - home[0]) <= idle.WANDER
            assert abs(bot["pos"][1] - home[1]) <= idle.WANDER


def test_bots_never_step_onto_the_player_or_each_other():
    rng, state = random.Random(2), _start()
    player = (HOMES["BARK"][0] + 6, HOMES["BARK"][1])  # standing right next to BARK
    for _ in range(300):
        before = state
        state = idle.idle_tick(state, HOMES, player, rng)
        for name, bot in state.items():
            if bot["pos"] == before[name]["pos"]:
                continue  # staying put is always allowed
            others = [player] + [other["pos"] for key, other in state.items() if key != name]
            assert not hubmap.blocked(bot["pos"], others), name


def test_bots_never_leave_the_floor_or_enter_furniture():
    rng, state = random.Random(3), _start()
    for _ in range(300):
        state = idle.idle_tick(state, HOMES, hubmap.SPAWN, rng)
        for name, bot in state.items():
            assert bot["pos"] == HOMES[name] or hubmap.clamp(*bot["pos"]) == tuple(bot["pos"])
            assert not hubmap.blocked(bot["pos"])


def test_the_room_is_never_still():
    rng, state = random.Random(4), _start()
    for _ in range(5):
        new = idle.idle_tick(state, HOMES, hubmap.CENTER, rng)
        assert new != state  # at least one bot turned or moved
        state = new


def test_the_given_positions_are_not_changed():
    state = _start()
    copy = {name: dict(bot) for name, bot in state.items()}
    idle.idle_tick(state, HOMES, hubmap.CENTER, random.Random(5))
    assert state == copy
