"""The bots in the arcade (arcade/wander.py): they walk round the room, stop to look at things, sometimes play at a
table, stop to talk, and never walk through furniture."""
import math
import random

from arcade import bots, hubmap, wander

HOMES = {bot["name"]: bot["home"] for bot in bots.BOTS}


def _start():
    return {bot["name"]: {"pos": bot["home"], "dir": bot["dir"]} for bot in bots.BOTS}


def _run(seed, ticks=500, player=hubmap.SPAWN):
    rng, room, now = random.Random(seed), _start(), 1000.0
    for _ in range(ticks):
        now += 1.2
        room = wander.tick(room, HOMES, player, rng, now)
        yield room, now


def test_every_place_worth_a_look_and_every_seat_is_on_the_floor():
    for spot, face in wander.SPOTS:
        assert wander._free_point(*spot), spot
        assert face in ("up", "down", "left", "right")
    for key, spot in hubmap.SPOTS.items():
        for seat in spot["seats"]:
            assert wander._free_point(*seat), (key, seat)


def test_a_path_goes_round_the_tables_never_through_them():
    path = wander.find_path((30, 150), (290, 150))  # from one side of the room to the other, past the tables
    assert path[0] == [30, 150] and path[-1] == [290, 150]
    for a, b in zip(path, path[1:]):
        assert wander.clear_line(a, b)
    assert wander.find_path((30, 150), (160, 110)) is None or not wander._free_point(160, 110)  # not into a table


def test_bots_walk_far_from_home_but_never_into_furniture():
    farthest = {name: 0.0 for name in HOMES}
    for room, now in _run(1):
        for name, bot in room.items():
            pos, _ = wander.where(bot, now)
            farthest[name] = max(farthest[name], math.dist(pos, HOMES[name]))
            assert tuple(bot["pos"]) == HOMES[name] or wander._free_point(*bot["pos"]) or bot.get("table")
            for a, b in zip(bot.get("path") or [], (bot.get("path") or [])[1:]):
                assert wander.clear_line(a, b), (name, a, b)
    assert all(distance > 60 for distance in farthest.values())  # they go round the room, not just near home


def test_now_and_then_two_bots_play_at_a_table_facing_it():
    seen = False
    for room, now in _run(2, ticks=900):
        playing = [bot for bot in room.values() if bot.get("doing") == "play"]
        if len(playing) == 2:
            seen = True
            table = playing[0]["table"]
            assert playing[1]["table"] == table
            seats = hubmap.SPOTS[table]["seats"]
            for bot in playing:
                assert tuple(bot["pos"]) in [tuple(seat) for seat in seats]
                assert bot["dir"] == wander.SEAT_FACING[[tuple(s) for s in seats].index(tuple(bot["pos"]))]
    assert seen


def test_they_never_play_at_the_table_the_player_stands_at():
    stand = hubmap.SPOTS["uno"]["stand"]
    for room, now in _run(3, ticks=900, player=stand):
        assert all(bot.get("table") != "uno" for bot in room.values())


def test_a_bot_stops_where_it_is_to_talk_and_turns_to_the_player():
    rng, now = random.Random(4), 0.0
    bot = {"pos": (30, 150), "dir": "up"}
    assert wander.walk(bot, (290, 150), "up", now)
    halfway = wander.where(bot, now + 3)[0]
    wander.talk(bot, (halfway[0] + 10, halfway[1]), now + 3)
    assert tuple(bot["pos"]) == halfway and bot["doing"] == "talk" and bot["dir"] == "right"
    room = wander.tick({"DEAN": bot}, {"DEAN": HOMES["DEAN"]}, hubmap.SPAWN, rng, now + 4)
    assert room["DEAN"]["pos"] == halfway  # still listening
    room = wander.tick(room, {"DEAN": HOMES["DEAN"]}, hubmap.SPAWN, rng, now + 3 + wander.TALK + 0.1)
    assert room["DEAN"]["doing"] == "walk"  # and then off again


def test_chosen_bots_stop_and_the_others_leave_the_table():
    now, room = 0.0, _start()
    seats = hubmap.SPOTS["checkers"]["seats"]
    for name, seat in (("DEAN", 0), ("JOHN", 1)):
        room[name].update(pos=seats[seat], dir=wander.SEAT_FACING[seat], doing="play", until=99, table="checkers")
    wander.free_table(room, "checkers", ["DEAN"], HOMES, now)
    assert room["DEAN"]["table"] is None and room["DEAN"]["doing"] == "stay"
    assert room["JOHN"]["table"] is None and room["JOHN"]["doing"] == "walk"
    assert tuple(room["JOHN"]["pos"]) == HOMES["JOHN"]


def test_the_given_positions_are_not_changed():
    room = _start()
    copy = {name: dict(bot) for name, bot in room.items()}
    wander.tick(room, HOMES, hubmap.CENTER, random.Random(5), 10.0)
    assert room == copy
