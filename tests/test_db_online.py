"""Saving to a hosted PostgreSQL database (task D2).

These tests run only when TEST_DATABASE_URL points at a PostgreSQL database
you may write to (never the real one). Without it they are skipped.
"""

import os

import pytest

from arcade import db
from arcade.player import new_player

URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="no TEST_DATABASE_URL set")


@pytest.fixture
def online(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", URL)
    import psycopg

    with psycopg.connect(URL, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS players")
    yield


def test_a_player_is_saved_and_loaded_online(online):
    assert db.where().startswith("hosted")
    assert db.load_player("ANA") is None
    player = new_player("ANA")
    player["coins"] = 75
    db.save_player(player)
    assert db.load_player("ana")["coins"] == 75


def test_saving_again_updates_the_same_row(online):
    player = new_player("ANA")
    db.save_player(player)
    player["coins"] = 5
    db.save_player(player)
    assert db.load_player("ANA")["coins"] == 5
    assert len(db.all_players()) == 1


def test_odd_names_cannot_break_the_online_database(online):
    player = new_player("X'); DROP TABLE players;--")
    db.save_player(player)
    assert db.load_player("X'); DROP TABLE players;--")["name"] == player["name"]
    assert len(db.all_players()) == 1
