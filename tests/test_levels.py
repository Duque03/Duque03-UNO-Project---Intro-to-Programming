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
        depths = [table[level][0] for level in LEVELS]
        blunders = [table[level][1] for level in LEVELS]
        assert depths == sorted(depths) and blunders == sorted(blunders, reverse=True)
    for key in ("twins", "stack", "smart"):
        values = [UNO_LEVELS[level][key] for level in LEVELS]
        assert values == sorted(values)
    assert [levels.stars(level) for level in LEVELS] == [1, 2, 3, 4]


def test_a_good_pick_is_accepted():
    levels.check_pick("checkers", ["JOY"], bots.BOT_NAMES)
    levels.check_pick("uno", ["JOY", "TURBO", "GLITCH"], bots.BOT_NAMES)


@pytest.mark.parametrize("game,names", [
    ("checkers", []),                          # nobody picked
    ("connect4", ["JOY", "BYTE"]),             # one too many
    ("uno", ["JOY", "TURBO"]),                 # one too few
    ("uno", ["JOY", "JOY", "TURBO"]),          # the same bot twice
    ("checkers", ["NOBODY"]),                  # not a bot
])
def test_a_bad_pick_is_refused(game, names):
    with pytest.raises(BadPick):
        levels.check_pick(game, names, bots.BOT_NAMES)
    assert BOTS_PER_GAME == {"uno": 3, "checkers": 1, "connect4": 1}


def test_picking_one_opponent_replaces_the_last_one():
    assert levels.toggle([], "JOY", 1) == ["JOY"]
    assert levels.toggle(["JOY"], "BYTE", 1) == ["BYTE"]


def test_picking_three_uno_opponents_and_a_fourth_replaces_the_first():
    picked = []
    for name in ("JOY", "TURBO", "BYTE"):
        picked = levels.toggle(picked, name, 3)
    assert picked == ["JOY", "TURBO", "BYTE"]
    assert levels.toggle(picked, "GLITCH", 3) == ["TURBO", "BYTE", "GLITCH"]


def test_clicking_a_picked_bot_takes_it_back():
    assert levels.toggle(["JOY", "TURBO"], "JOY", 3) == ["TURBO"]
