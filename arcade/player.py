"""The player's save data: a plain dictionary that is easy to store and test."""

from __future__ import annotations

import re

from arcade.config import GAMES, NAME_MAX, NAME_MIN, SLOTS
from arcade.logic import looks

_ALLOWED = re.compile(r"^[A-Z0-9 _\-]+$")


class InvalidName(ValueError):
    """Raised when a player name is not acceptable."""


def clean_name(raw: str) -> str:
    """Tidy a typed name and check it. Returns the name in capitals."""
    if not isinstance(raw, str):
        raise InvalidName("Type a name first.")
    name = " ".join(raw.strip().upper().split())
    if len(name) < NAME_MIN:
        raise InvalidName("Type a name first.")
    if len(name) > NAME_MAX:
        raise InvalidName(f"Use at most {NAME_MAX} characters.")
    if not _ALLOWED.match(name):
        raise InvalidName("Use only letters, numbers, spaces, - and _.")
    return name


def new_player(name: str) -> dict:
    return {
        "name": name,
        "coins": 0,
        "owned": [],
        "equipped": {slot: None for slot in SLOTS},
        "wins": {game: 0 for game in GAMES},
        "championships": 0,
        "champ_intro_seen": False,
        "skin": "#f2c9a0",
        "pants": "#2b3a67",
        "base": dict(looks.DEFAULT),  # the look chosen when the account was made (logic/looks.py)
        "look_done": True,  # False only for a brand-new account, until the player has made their look
    }


def look(player: dict, preview: dict | None = None) -> tuple:
    """(skin, pants, hair item, shirt item) for the sprite code. preview overrides what is worn."""
    worn = dict(player["equipped"])
    if preview:
        worn.update(preview)
    base = player.get("base")  # nothing from the store on: the look they made when they created their player
    return (player["skin"], player["pants"], worn["hair"] or looks.hair_id(base), worn["shirt"] or looks.shirt_id(base))
