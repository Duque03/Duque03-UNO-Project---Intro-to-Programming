"""Create your player: the base look chosen with a new account (docs/game-design.md)."""
import pytest

from arcade import accounts, catalog, db
from arcade.logic import looks
from arcade.logic.looks import InvalidLook
from arcade.player import look, new_player


def test_a_listed_choice_is_saved_as_the_base_look():
    player = new_player("ANA")
    looks.apply(player, {"hair": "girl", "hair_colour": "ginger", "shirt": "green", "skin": "dark"})
    assert player["look_done"] and player["skin"] == looks.SKINS["dark"]
    hair, shirt = look(player)[2:]
    assert catalog.spec_for("hair", hair) == {"style": "long", "c1": looks.HAIR_COLOURS["ginger"]}
    assert catalog.spec_for("shirt", shirt) == {"style": "solid", "c1": looks.SHIRT_COLOURS["green"]}


@pytest.mark.parametrize("bad", [{"hair": "bald"}, {"hair_colour": "#123456"}, {"shirt": "gold"}, {"skin": None}])
def test_a_choice_that_is_not_in_the_lists_is_refused(bad):
    player = new_player("ANA")
    with pytest.raises(InvalidLook):
        looks.apply(player, {**looks.DEFAULT, **bad})
    assert player["base"] == looks.DEFAULT  # nothing changed


def test_store_items_go_on_top_of_the_base_look_and_taking_them_off_brings_it_back():
    player = new_player("ANA")
    looks.apply(player, {"hair": "girl", "hair_colour": "black", "shirt": "red", "skin": "tan"})
    player["equipped"]["hair"] = "hair_c01"
    assert look(player)[2] == "hair_c01"
    player["equipped"]["hair"] = None
    assert look(player)[2] == looks.hair_id(player["base"])


def test_made_up_base_ids_draw_the_default_look():
    assert catalog.spec_for("hair", "base:hair:short:#ff00ff") == catalog.DEFAULTS["hair"]  # not a listed colour
    assert catalog.spec_for("shirt", "base:hair:short:#1d1a22") == catalog.DEFAULTS["shirt"]  # wrong slot
    assert catalog.spec_for("shirt", "base:shirt") == catalog.DEFAULTS["shirt"]


def test_the_arrows_go_round_each_row():
    choice = dict(looks.DEFAULT)
    assert looks.step(choice, 0, 1)["hair"] == "girl" and looks.step(choice, 0, 2)["hair"] == "boy"
    assert looks.step(choice, 2, -1)["shirt"] == list(looks.SHIRT_COLOURS)[-1]


def test_a_new_account_makes_its_look_first_and_old_saves_do_not(tmp_path):
    path = tmp_path / "save.db"
    player = accounts.sign_up("ana", "1234", "1234", path)
    assert player["look_done"] is False and db.load_player("ANA", path)["look_done"] is False
    old = new_player("OLD")
    del old["look_done"], old["base"]
    db.save_player(old, path)
    assert db.load_player("OLD", path)["look_done"] is True  # saves from before this screen keep their look
