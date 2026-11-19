"""Everything can be done with the keyboard too (docs/game-design.md, section 0).

The arrow keys move a yellow highlight; Space or Enter chooses what it is on, like a click.
"""

import pytest
from PIL import Image, ImageChops

from arcade import bots, catalog, controls
from arcade.art import scenes, versus
from arcade.art.pixel import text_size
from arcade.config import GAMES, SCREEN_H, SCREEN_W
from arcade.logic import cursor


# ----- moving along a row (menus, bots, cards, columns, store items)

def test_right_and_down_go_forward_left_and_up_go_back():
    assert cursor.step(1, "right", 5) == 2
    assert cursor.step(1, "down", 5) == 2
    assert cursor.step(1, "left", 5) == 0
    assert cursor.step(1, "up", 5) == 0


def test_the_highlight_wraps_round_at_the_ends():
    assert cursor.step(4, "right", 5) == 0
    assert cursor.step(0, "left", 5) == 4


def test_without_wrapping_the_highlight_stops_at_the_ends():
    assert cursor.step(4, "right", 5, wrap=False) == 4
    assert cursor.step(0, "left", 5, wrap=False) == 0


def test_the_first_press_lands_on_the_first_thing():
    assert cursor.step(None, "right", 5) == 0
    assert cursor.step(None, "left", 5) == 0


def test_nothing_to_highlight_gives_none():
    assert cursor.step(0, "right", 0) is None
    assert cursor.clamp(3, 0) is None
    assert cursor.first([]) is None


def test_an_unknown_key_is_refused():
    with pytest.raises(ValueError):
        cursor.step(0, "space", 5)
    with pytest.raises(ValueError):
        cursor.on_board((0, 0), "jump", 8, 8)


def test_the_highlight_stays_on_something_that_still_exists():
    assert cursor.clamp(6, 4) == 3  # the hand got smaller: the last card
    assert cursor.clamp(None, 4) == 0
    assert cursor.clamp(2, 4) == 2


def test_the_highlight_starts_on_the_first_useful_thing():
    assert cursor.first([False, False, True, True]) == 2  # e.g. the first card that can be played
    assert cursor.first([False, False]) == 0  # nothing useful: just the first one


# ----- moving on a board (checkers)

def test_the_board_cursor_moves_one_square():
    assert cursor.on_board((3, 3), "up", 8, 8) == (2, 3)
    assert cursor.on_board((3, 3), "down", 8, 8) == (4, 3)
    assert cursor.on_board((3, 3), "left", 8, 8) == (3, 2)
    assert cursor.on_board((3, 3), "right", 8, 8) == (3, 4)


def test_the_board_cursor_cannot_leave_the_board():
    assert cursor.on_board((0, 0), "up", 8, 8) == (0, 0)
    assert cursor.on_board((0, 0), "left", 8, 8) == (0, 0)
    assert cursor.on_board((7, 7), "down", 8, 8) == (7, 7)
    assert cursor.on_board((7, 7), "right", 8, 8) == (7, 7)


# ----- the highlight on the pictures

def _background():
    return Image.new("RGB", (SCREEN_W, SCREEN_H), (40, 30, 80))


def _changed(a, b, box):
    """Did anything change inside this box?"""
    return ImageChops.difference(a.crop(box), b.crop(box)).getbbox() is not None


OPTIONS = [{"label": "RESUME", "action": "resume"}, {"label": "WARDROBE", "action": "wardrobe"},
           {"label": "LEAVE ARCADE", "action": "leave"}]


def test_the_menu_highlight_only_changes_the_chosen_button():
    plain, regions = scenes.menu_panel(_background(), "PAUSED", OPTIONS)
    lit, lit_regions = scenes.menu_panel(_background(), "PAUSED", OPTIONS, focus=1)
    assert regions == lit_regions  # the buttons do not move
    assert _changed(plain, lit, regions[1][0])
    assert not _changed(plain, lit, regions[0][0]) and not _changed(plain, lit, regions[2][0])


def test_a_menu_highlight_on_no_button_is_refused():
    with pytest.raises(ValueError):
        scenes.menu_panel(_background(), "PAUSED", OPTIONS, focus=3)


def test_the_yes_no_highlight_only_changes_the_chosen_button():
    choices = [{"label": "YES", "action": "yes", "key": "Y"}, {"label": "NO", "action": "no", "key": "N"}]
    plain, lit = _background(), _background()
    regions = scenes.choice_buttons(plain, choices)
    assert scenes.choice_buttons(lit, choices, focus=1) == regions
    assert _changed(plain, lit, regions[1][0]) and not _changed(plain, lit, regions[0][0])
    with pytest.raises(ValueError):
        scenes.choice_buttons(_background(), choices, focus=2)


def _cards():
    return [{"name": b["name"], "level": b["level"], "look": bots.look(b), "tag": catalog.spec_for("name", b["tag"])}
            for b in bots.BOTS]


def test_the_opponent_highlight_only_changes_that_bot():
    plain, regions = versus.panel_picture(None, "PICK", _cards(), [], 1, None)
    lit, _ = versus.panel_picture(None, "PICK", _cards(), [], 1, None, focus=2)
    assert _changed(plain, lit, regions[2][0])
    assert not _changed(plain, lit, regions[0][0]) and not _changed(plain, lit, regions[4][0])
    with pytest.raises(ValueError):
        versus.panel_picture(None, "PICK", _cards(), [], 1, None, focus=5)


def test_the_opponent_hint_fits_in_the_panel():
    assert text_size(versus.HINT, 2)[0] <= SCREEN_W - 120


# ----- the How to play panel tells you the keys

@pytest.mark.parametrize("game", GAMES)
def test_every_game_tab_says_how_to_choose_with_the_keyboard(game):
    tab = next(tab for tab in controls.TABS if tab["key"] == game)
    keys = " ".join(key for key, _ in tab["rows"])
    assert "SPACE" in keys
