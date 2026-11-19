"""Play again: after a free-play game, the same table against the same bots (docs/game-design.md, section 3)."""

import pytest
from PIL import Image

from arcade import bots
from arcade.art import scenes
from arcade.config import SCREEN_H, SCREEN_W
from arcade.logic import levels
from arcade.logic.levels import BadPick


def _free(game, names):
    return {"game": game, "mode": "free", "bots": list(names), "others": []}


@pytest.mark.parametrize("game,names", [
    ("uno", ["JOY", "TURBO", "BYTE"]),
    ("checkers", ["GLITCH"]),
    ("connect4", ["PIXEL"]),
])
def test_play_again_keeps_the_table_and_the_bots(game, names):
    match = _free(game, names)
    again = levels.rematch(match, bots.BOT_NAMES)
    assert again == _free(game, names)
    assert again is not match and again["bots"] is not match["bots"]  # a new match: the old one is not changed


def test_play_again_pays_the_same_prize():
    match = _free("uno", ["JOY", "TURBO", "BYTE"])
    again = levels.rematch(match, bots.BOT_NAMES)
    prize = [levels.win_coins([bots.level(name) for name in m["bots"]]) for m in (match, again)]
    assert prize[0] == prize[1]


@pytest.mark.parametrize("match", [
    None,                                                                  # no game was played
    {"game": "uno", "mode": "champ", "bots": ["JOY", "TURBO", "BYTE"], "others": []},  # championship
    _free("poker", ["JOY"]),                                               # not a table
    _free("checkers", ["NOBODY"]),                                         # not a bot
    _free("connect4", ["JOY", "BYTE"]),                                    # one bot too many
    _free("uno", ["JOY", "JOY", "TURBO"]),                                 # the same bot twice
])
def test_play_again_is_refused_when_it_does_not_fit(match):
    with pytest.raises(BadPick):
        levels.rematch(match, bots.BOT_NAMES)


# ----- the result box

def _table():
    return Image.new("RGB", (SCREEN_W, SCREEN_H), (40, 30, 80))


def _hit(regions, x, y):
    """Like ui.hit: later regions lie on top."""
    for (left, top, right, bottom), action in reversed(regions):
        if left <= x <= right and top <= y <= bottom:
            return action
    return None


@pytest.mark.parametrize("coins", [5, 0])  # a win and a loss
def test_the_result_box_offers_play_again(coins):
    img, regions = scenes.result_panel_again(_table(), "VICTORY!", "WELL PLAYED", coins)
    assert img.size == (SCREEN_W, SCREEN_H)
    (left, top, right, bottom), action = regions[-1]
    assert action == ("again",)
    assert _hit(regions, (left + right) / 2, (top + bottom) / 2) == ("again",)


def test_a_click_anywhere_else_still_continues():
    _, regions = scenes.result_panel_again(_table(), "GAME OVER", "WELL PLAYED", 0)
    assert _hit(regions, 5, 5) == ("continue",)  # the corner of the screen, far from PLAY AGAIN
    assert _hit(regions, SCREEN_W // 2, SCREEN_H // 2) == ("continue",)  # the middle of the box


def test_play_again_is_drawn_inside_the_box():
    table = _table()
    img, regions = scenes.result_panel_again(table, "VICTORY!", "WELL PLAYED", 5)
    left, top, right, bottom = regions[-1][0]
    assert 150 <= left < right <= SCREEN_W - 150  # the box spans x 150 to 810
    assert img.getpixel(((left + right) // 2, (top + bottom) // 2)) != table.getpixel((0, 0))  # something is drawn there
    assert table.getpixel((0, 0)) == (40, 30, 80)  # the table picture itself is not changed
