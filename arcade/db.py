"""Saves and loads players.

Two places to keep them, behind the same three functions:
  * SQLite, one small file (data/arcade.db). Used on your laptop and in the tests.
  * A hosted PostgreSQL database (for example Neon or Supabase, both free), used
    when a DATABASE_URL is set: as a secret on the host (Streamlit Community
    Cloud: app settings -> Secrets) or as an environment variable. The free
    host wipes its disk whenever the app restarts, so online the progress must
    live in a database of its own (task D2).

The whole player is stored as one JSON text. That keeps this file tiny and
means new fields can be added to the player without changing the table.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from arcade.player import new_player

_TABLE = (
    "CREATE TABLE IF NOT EXISTS players ("
    " name TEXT PRIMARY KEY,"
    " data TEXT NOT NULL,"
    " updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
)
_UPSERT = (
    "INSERT INTO players (name, data, updated_at) VALUES ({p}, {p}, CURRENT_TIMESTAMP)"
    " ON CONFLICT(name) DO UPDATE SET data = excluded.data, updated_at = CURRENT_TIMESTAMP"
)
_SELECT = "SELECT data FROM players WHERE name = {p}"
_TOP = "SELECT data FROM players"


def db_path() -> Path:
    return Path(os.environ.get("ARCADE_DB", "data/arcade.db"))


def database_url() -> str | None:
    """The hosted database to use, if one is set up (never written in the code or the repository)."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        try:
            import streamlit as st

            url = st.secrets.get("DATABASE_URL")
        except Exception:  # no secrets file, or not running inside Streamlit
            url = None
    return url or None


def where() -> str:
    """Where players are saved, in words (for the README and the walkthrough)."""
    return "hosted PostgreSQL database (DATABASE_URL)" if database_url() else f"SQLite file {db_path()}"


def _connect(path: Path | str | None = None):
    """(connection, placeholder). A path always means SQLite (the tests pass one)."""
    url = None if path else database_url()
    if url:
        import psycopg  # only needed online

        conn = psycopg.connect(url, connect_timeout=10, autocommit=True)
        conn.execute(_TABLE)
        return conn, "%s"
    path = Path(path) if path else db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(_TABLE)
    conn.commit()
    return conn, "?"


def _player_from(name: str, data: str) -> dict:
    player = new_player(name.upper())
    player.update(json.loads(data))  # fields added later keep their defaults
    return player


def load_player(name: str, path: Path | str | None = None) -> dict | None:
    """Return the saved player, or None if this name has never played."""
    conn, p = _connect(path)
    with closing(conn):
        row = conn.execute(_SELECT.format(p=p), (name.upper(),)).fetchone()
    return None if row is None else _player_from(name, row[0])


def save_player(player: dict, path: Path | str | None = None) -> None:
    conn, p = _connect(path)
    with closing(conn):
        conn.execute(_UPSERT.format(p=p), (player["name"].upper(), json.dumps(player)))
        conn.commit()


def all_players(path: Path | str | None = None) -> list[dict]:
    """Every saved player (for the hall of fame)."""
    conn, _ = _connect(path)
    with closing(conn):
        rows = conn.execute(_TOP).fetchall()
    players = []
    for (data,) in rows:
        stored = json.loads(data)
        players.append(_player_from(stored.get("name", "?"), data))
    return players


def load_or_create(name: str, path: Path | str | None = None) -> tuple[dict, bool]:
    """Returns (player, is_new). Sign-in with a PIN goes through accounts.sign_in instead."""
    player = load_player(name, path)
    if player is not None:
        return player, False
    player = new_player(name.upper())
    save_player(player, path)
    return player, True
