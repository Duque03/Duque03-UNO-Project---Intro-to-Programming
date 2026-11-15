"""Saves and loads players with SQLite (one small file, no server needed).

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


def db_path() -> Path:
    return Path(os.environ.get("ARCADE_DB", "data/arcade.db"))


def _connect(path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(path) if path else db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS players ("
        " name TEXT PRIMARY KEY,"
        " data TEXT NOT NULL,"
        " updated_at TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    return conn


def load_player(name: str, path: Path | str | None = None) -> dict | None:
    """Return the saved player, or None if this name has never played."""
    with closing(_connect(path)) as conn, conn:
        row = conn.execute("SELECT data FROM players WHERE name = ?", (name.upper(),)).fetchone()
    if row is None:
        return None
    player = new_player(name.upper())
    player.update(json.loads(row[0]))  # fields added later keep their defaults
    return player


def save_player(player: dict, path: Path | str | None = None) -> None:
    with closing(_connect(path)) as conn, conn:
        conn.execute(
            "INSERT INTO players (name, data, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)"
            " ON CONFLICT(name) DO UPDATE SET data = excluded.data, updated_at = CURRENT_TIMESTAMP",
            (player["name"].upper(), json.dumps(player)),
        )


def load_or_create(name: str, path: Path | str | None = None) -> tuple[dict, bool]:
    """Returns (player, is_new)."""
    player = load_player(name, path)
    if player is not None:
        return player, False
    player = new_player(name.upper())
    save_player(player, path)
    return player, True
