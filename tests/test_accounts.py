"""Signing in with a name and a PIN (task D3)."""

import json
import sqlite3

import pytest

from arcade import accounts, db
from arcade.player import InvalidName


@pytest.fixture
def path(tmp_path):
    return tmp_path / "save.db"


def test_a_new_name_is_created_with_its_pin(path):
    player, is_new = accounts.sign_in("ana", "1234", path)
    assert is_new and player["name"] == "ANA"
    again, is_new = accounts.sign_in("ANA", "1234", path)
    assert not is_new and again["name"] == "ANA"


def test_the_right_pin_loads_the_saved_progress(path):
    player, _ = accounts.sign_in("ana", "1234", path)
    player["coins"] = 120
    db.save_player(player, path)
    loaded, _ = accounts.sign_in("ana", "1234", path)
    assert loaded["coins"] == 120


def test_a_wrong_pin_is_refused_and_the_progress_is_unchanged(path):
    player, _ = accounts.sign_in("ana", "1234", path)
    player["coins"] = 120
    db.save_player(player, path)
    with pytest.raises(accounts.WrongPin):
        accounts.sign_in("ana", "9999", path)
    assert db.load_player("ANA", path)["coins"] == 120


@pytest.mark.parametrize("pin", ["", "   ", "123", "123456789", "12a4", "12 34", None, 1234])
def test_a_pin_that_is_not_4_to_8_digits_is_refused(path, pin):
    with pytest.raises(accounts.InvalidPin):
        accounts.sign_in("ana", pin, path)
    assert db.load_player("ANA", path) is None  # nothing was created


def test_a_bad_name_is_refused_before_anything_is_saved(path):
    with pytest.raises(InvalidName):
        accounts.sign_in("<script>", "1234", path)


def test_the_pin_is_never_stored(path):
    accounts.sign_in("ana", "13579", path)
    with sqlite3.connect(path) as conn:
        stored = conn.execute("SELECT data FROM players").fetchone()[0]
    assert "13579" not in stored
    record = json.loads(stored)["pin"]
    assert set(record) == {"salt", "hash", "iterations"}


def test_the_same_pin_gives_a_different_hash_for_each_player(path):
    a, _ = accounts.sign_in("ana", "1234", path)
    b, _ = accounts.sign_in("rui", "1234", path)
    assert a["pin"]["hash"] != b["pin"]["hash"]


def test_five_wrong_pins_lock_the_name_for_a_minute(path):
    accounts.sign_in("ana", "1234", path, now=1000)
    for i in range(accounts.MAX_TRIES):
        with pytest.raises(accounts.WrongPin):
            accounts.sign_in("ana", "0000", path, now=1000 + i)
    with pytest.raises(accounts.Locked):
        accounts.sign_in("ana", "1234", path, now=1010)  # even the right PIN waits
    player, _ = accounts.sign_in("ana", "1234", path, now=1000 + accounts.LOCK_SECONDS + 10)
    assert player["failed_pins"] == 0 and player["locked_until"] == 0


def test_a_save_from_before_pins_gets_the_first_pin_used(path):
    old, _ = db.load_or_create("ANA", path)  # the way players were saved before PINs
    old["coins"] = 40
    db.save_player(old, path)
    player, is_new = accounts.sign_in("ana", "2468", path)
    assert not is_new and player["coins"] == 40
    with pytest.raises(accounts.WrongPin):
        accounts.sign_in("ana", "1111", path)


def test_check_pin_survives_a_broken_record():
    assert accounts.check_pin("1234", {}) is False
    assert accounts.check_pin("1234", {"salt": "not-hex", "hash": "x"}) is False


# ---- NEW PLAYER and I HAVE AN ACCOUNT

def test_new_player_is_created_with_its_pin(path):
    player = accounts.sign_up("Miguel", "1234", "1234", path)
    assert player["name"] == "MIGUEL"
    assert accounts.log_in("miguel", "1234", path)["name"] == "MIGUEL"


def test_new_player_with_a_taken_name_is_refused(path):
    accounts.sign_up("Miguel", "1234", "1234", path)
    with pytest.raises(accounts.NameTaken):
        accounts.sign_up("MIGUEL", "9999", "9999", path)
    assert accounts.log_in("Miguel", "1234", path)  # the first player still has their PIN


def test_new_player_must_type_the_same_pin_twice(path):
    with pytest.raises(accounts.InvalidPin):
        accounts.sign_up("Miguel", "1234", "1243", path)
    with pytest.raises(accounts.UnknownName):
        accounts.log_in("Miguel", "1234", path)  # nothing was saved


def test_log_in_with_an_unknown_name_is_refused(path):
    with pytest.raises(accounts.UnknownName):
        accounts.log_in("Nobody", "1234", path)


def test_log_in_with_a_wrong_pin_is_refused(path):
    accounts.sign_up("Miguel", "1234", "1234", path)
    with pytest.raises(accounts.WrongPin):
        accounts.log_in("Miguel", "4321", path)
