"""Bot levels and the coins they pay (Miguel's table: easy 5, medium 15, hard 25, expert 40)."""

import pytest

from arcade import bots
from arcade.config import BOTS_PER_GAME, CHECKERS_LEVELS, CONNECT4_LEVELS, LEVEL_COINS, LEVELS, UNO_LEVELS
from arcade.logic import levels
from arcade.logic.levels import BadPick


def test_one_bot_pays_its_level():
    assert [levels.win_coins([level]) for level in LEVELS] == [5, 15, 25, 40]


def test_three_uno_bots_pay_the_average_rounded():
    assert levels.win_coins(["easy", "medium", "hard"]) == 15
    assert levels.win_coins(["easy", "easy", "medium"]) == 8  # 8.33
    assert levels.win_coins(["medium", "hard", "expert"]) == 27  # 26.67


def test_unknown_level_is_refused():
    with pytest.raises(BadPick):
        levels.win_coins(["impossible"])
    with pytest.raises(BadPick):
        levels.win_coins([])


def test_every_bot_has_a_level_and_every_level_has_a_bot():
    assert {bots.level(name) for name in bots.BOT_NAMES} == set(LEVELS)
    assert set(LEVEL_COINS) == set(UNO_LEVELS) == set(CHECKERS_LEVELS) == set(CONNECT4_LEVELS) == set(LEVELS)


def test_levels_get_stronger_in_order():
    for table in (CHECKERS_LEVELS, CONNECT4_LEVELS):
        depths = [table[level]["depth"] for level in LEVELS]
        blunders = [table[level]["blunder"] for level in LEVELS]
        assert depths == sorted(depths) and blunders == sorted(blunders, reverse=True)
    for key in ("win", "block"):
        values = [CONNECT4_LEVELS[level][key] for level in LEVELS]
        assert values == sorted(values) and values[-1] == 1.0  # hard and expert never miss
    for key in ("twins", "stack", "smart"):
        values = [UNO_LEVELS[level][key] for level in LEVELS]
        assert values == sorted(values)
    forgets = [UNO_LEVELS[level]["forget_uno"] for level in LEVELS]
    assert forgets == sorted(forgets, reverse=True)
    assert [levels.stars(level) for level in LEVELS] == [1, 2, 3, 4]


def test_a_good_pick_is_accepted():
    levels.check_pick("checkers", ["DEAN"], bots.BOT_NAMES)
    levels.check_pick("uno", ["DEAN", "BARK", "JOHN"], bots.BOT_NAMES)


@pytest.mark.parametrize("game,names", [
    ("checkers", []),                          # nobody picked
    ("connect4", ["DEAN", "MANHOSA"]),             # one too many
    ("uno", ["DEAN", "BARK"]),                 # one too few
    ("uno", ["DEAN", "DEAN", "BARK"]),          # the same bot twice
    ("checkers", ["NOBODY"]),                  # not a bot
])
def test_a_bad_pick_is_refused(game, names):
    with pytest.raises(BadPick):
        levels.check_pick(game, names, bots.BOT_NAMES)
    assert BOTS_PER_GAME == {"uno": 3, "checkers": 1, "connect4": 1}


def test_picking_one_opponent_replaces_the_last_one():
    assert levels.toggle([], "DEAN", 1) == ["DEAN"]
    assert levels.toggle(["DEAN"], "MANHOSA", 1) == ["MANHOSA"]


def test_picking_three_uno_opponents_and_a_fourth_replaces_the_first():
    picked = []
    for name in ("DEAN", "BARK", "MANHOSA"):
        picked = levels.toggle(picked, name, 3)
    assert picked == ["DEAN", "BARK", "MANHOSA"]
    assert levels.toggle(picked, "JOHN", 3) == ["BARK", "MANHOSA", "JOHN"]


def test_clicking_a_picked_bot_takes_it_back():
    assert levels.toggle(["DEAN", "BARK"], "DEAN", 3) == ["BARK"]


# ----- UNO prizes by place (docs/game-design.md, section 3): full, half, a quarter, nothing for last

def test_uno_places_win_full_half_and_a_quarter_of_the_prize():
    picked = ["easy", "medium", "hard"]  # prize 15
    assert [levels.place_coins(picked, place) for place in (1, 2, 3, 4)] == [15, 8, 4, 0]
    assert [levels.place_coins(["expert"] * 3, place) for place in (1, 2, 3, 4)] == [40, 20, 10, 0]


def test_a_place_below_one_is_rejected():
    with pytest.raises(ValueError):
        levels.place_coins(["easy", "easy", "easy"], 0)
