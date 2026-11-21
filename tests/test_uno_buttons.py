"""The big UNO! and CORTA UNO! buttons in the middle of the UNO table, and the player's own place once their cards
are gone (docs/game-design.md, section 3)."""

import random

from PIL import ImageChops

from arcade import bots, catalog
from arcade.art import badges
from arcade.config import SCREEN_H, SCREEN_W
from arcade.logic.uno import UnoGame
from arcade.screens import uno

OPPONENTS = [{"name": n, "look": bots.look(bots.get(n)), "tag": catalog.spec_for("name", bots.get(n)["tag"])}
             for n in ("DEAN", "BARK", "JOHN")]


def _game():
    return UnoGame(["ME", "DEAN", "BARK", "JOHN"], random.Random(2), start=0)


def test_the_two_buttons_are_big_and_in_the_middle_of_the_table_above_the_piles():
    for kind in ("uno", "corta"):
        img, box = badges.place(kind, uno.BADGE_AT)
        assert img.width >= 280 and img.height >= 150
        assert abs((box[0] + box[2]) / 2 - SCREEN_W / 2) <= 1 and box[1] > 0 and box[3] <= uno.PILE_Y + 8
    assert badges.badge("uno").tobytes() != badges.badge("corta").tobytes()


def test_the_uno_button_is_clicked_before_anything_under_it():
    game = _game()
    game.uno_due = "ME"
    _, regions = uno.draw(game, "ME", OPPONENTS, uno_open=True, hands=None)
    assert regions[0] == (uno.UNO_BOX, ("uno",))
    game.uno_due = "DEAN"
    _, regions = uno.draw(game, "ME", OPPONENTS, cut_open=True, hands=None)
    assert regions[0][1] == ("cut",)
    _, regions = uno.draw(game, "ME", OPPONENTS, hands=None)
    assert all(action not in (("uno",), ("cut",)) for _, action in regions)


def test_a_player_who_finished_sees_their_own_place_where_their_cards_were():
    game = _game()
    playing, _ = uno.draw(game, "ME", OPPONENTS, hands=None)
    game.hands["ME"] = []
    game.out.append("ME")  # 1st, while the other three play on
    first, _ = uno.draw(game, "ME", OPPONENTS, hands=None)
    bottom = (0, uno.HAND_Y, SCREEN_W, SCREEN_H)
    assert ImageChops.difference(playing.crop(bottom), first.crop(bottom)).getbbox() is not None
    game.out.insert(0, "DEAN")  # now 2nd: another picture
    second, _ = uno.draw(game, "ME", OPPONENTS, hands=None)
    assert ImageChops.difference(first.crop(bottom), second.crop(bottom)).getbbox() is not None
