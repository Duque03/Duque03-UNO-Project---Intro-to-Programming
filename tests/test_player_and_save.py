import pytest

from arcade import catalog, db
from arcade.logic import store
from arcade.player import InvalidName, clean_name, look, new_player


# ---- names

@pytest.mark.parametrize("raw, expected", [("miguel", "MIGUEL"), ("  Ana  Sofia ", "ANA SOFIA"), ("p1_x-2", "P1_X-2")])
def test_good_names_are_tidied(raw, expected):
    assert clean_name(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "x" * 11, "<script>", "a;DROP", "joão", None, 42])
def test_bad_names_are_rejected(raw):
    with pytest.raises(InvalidName):
        clean_name(raw)


def test_new_player_starts_with_nothing():
    player = new_player("ANA")
    assert player["coins"] == 0 and player["owned"] == []
    assert player["wins"] == {"uno": 0, "checkers": 0, "connect4": 0}
    # nothing from the store on: the base look, which for an old save is the old default (short brown hair, white tee)
    assert look(player) == (player["skin"], player["pants"], "base:hair:short:#5a3a22", "base:shirt:#e9e9ee")
    assert catalog.spec_for("hair", look(player)[2]) == catalog.DEFAULTS["hair"]
    assert catalog.spec_for("shirt", look(player)[3]) == catalog.DEFAULTS["shirt"]


def test_preview_changes_the_look_without_changing_the_player():
    player = new_player("ANA")
    assert look(player, {"hair": "hair_r01"})[2] == "hair_r01"
    assert player["equipped"]["hair"] is None


# ---- saving (the "restart the app" check)

def test_unknown_player_loads_as_none(tmp_path):
    assert db.load_player("NOBODY", tmp_path / "save.db") is None


def test_progress_survives_a_restart(tmp_path):
    path = tmp_path / "save.db"
    player, is_new = db.load_or_create("ANA", path)
    assert is_new
    player["coins"] = 120
    store.buy(player, "shirt_r01")
    store.equip(player, "shirt_r01")
    player["wins"]["uno"] = 2
    player["champ_intro_seen"] = True
    db.save_player(player, path)

    loaded, is_new = db.load_or_create("ANA", path)  # as if the app was started again
    assert not is_new
    assert loaded == player
    assert loaded["coins"] == 20 and loaded["equipped"]["shirt"] == "shirt_r01"


def test_rejected_purchase_leaves_the_saved_data_unchanged(tmp_path):
    path = tmp_path / "save.db"
    player, _ = db.load_or_create("ANA", path)
    with pytest.raises(store.StoreError):
        store.buy(player, "hair_l01")
    assert db.load_player("ANA", path) == new_player("ANA")


def test_players_do_not_share_progress_and_names_ignore_case(tmp_path):
    path = tmp_path / "save.db"
    ana, _ = db.load_or_create("ANA", path)
    ana["coins"] = 50
    db.save_player(ana, path)
    rui, is_new = db.load_or_create("RUI", path)
    assert is_new and rui["coins"] == 0
    assert db.load_player("ana", path)["coins"] == 50


def test_odd_names_cannot_break_the_database(tmp_path):
    path = tmp_path / "save.db"
    nasty = "X'; DROP TABLE players;--"
    db.save_player(new_player(nasty), path)
    assert db.load_player(nasty, path)["name"] == nasty
    assert db.load_player("ANA", path) is None
