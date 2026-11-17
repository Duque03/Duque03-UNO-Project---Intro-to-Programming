"""Signing in with a name and a PIN (task D3). No Streamlit here, so it can be tested like the game rules.

The PIN itself is never stored. We keep a random "salt" and the result of
running PIN + salt through PBKDF2 (a slow, standard hash from Python's own
hashlib). Checking a PIN means hashing it again with the same salt and
comparing. Someone who reads the database cannot get the PINs back, and
guessing is slowed down twice: by the hash, and by locking a name for a
minute after MAX_TRIES wrong PINs in a row (saved with the player, so a new
browser tab does not reset it).
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import time

from arcade import db
from arcade.player import clean_name, new_player

PIN_MIN, PIN_MAX = 4, 8
ITERATIONS = 200_000
MAX_TRIES = 5
LOCK_SECONDS = 60
_DIGITS = re.compile(r"^[0-9]+$")


class InvalidPin(ValueError):
    """The PIN is not 4 to 8 digits."""


class WrongPin(ValueError):
    """The PIN does not match this name."""


class Locked(ValueError):
    """Too many wrong PINs: the name is locked for a moment."""


def clean_pin(raw) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise InvalidPin("Type a PIN too (4 to 8 digits).")
    pin = raw.strip()
    if not _DIGITS.match(pin) or not PIN_MIN <= len(pin) <= PIN_MAX:
        raise InvalidPin(f"The PIN must be {PIN_MIN} to {PIN_MAX} digits.")
    return pin


def pin_record(pin: str, salt: str | None = None) -> dict:
    """What we store instead of the PIN."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt), ITERATIONS).hex()
    return {"salt": salt, "hash": digest, "iterations": ITERATIONS}


def check_pin(pin: str, record: dict) -> bool:
    try:
        digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(record["salt"]),
                                     int(record.get("iterations", ITERATIONS))).hex()
    except (KeyError, TypeError, ValueError):
        return False
    return hmac.compare_digest(digest, record.get("hash", ""))


def sign_in(raw_name, raw_pin, path=None, now: float | None = None) -> tuple[dict, bool]:
    """Check the name and PIN and return (player, is_new).

    A name that has never played is created with this PIN. A name saved before
    PINs existed gets this PIN now. Raises InvalidName, InvalidPin, WrongPin or Locked;
    a refused sign-in never changes the player's progress.
    """
    now = time.time() if now is None else now
    name = clean_name(raw_name)
    pin = clean_pin(raw_pin)
    player = db.load_player(name, path)
    if player is None:
        player = new_player(name)
        player["pin"] = pin_record(pin)
        db.save_player(player, path)
        return player, True
    if not player.get("pin"):  # an older save, from before PINs: this PIN becomes theirs
        player["pin"] = pin_record(pin)
        db.save_player(player, path)
        return player, False
    if player.get("locked_until", 0) > now:
        wait = int(player["locked_until"] - now) + 1
        raise Locked(f"Too many wrong PINs. Try again in {wait} seconds.")
    if not check_pin(pin, player["pin"]):
        player["failed_pins"] = player.get("failed_pins", 0) + 1
        if player["failed_pins"] >= MAX_TRIES:
            player["failed_pins"] = 0
            player["locked_until"] = now + LOCK_SECONDS
        db.save_player(player, path)  # only the counter changes, never the progress
        left = MAX_TRIES - player["failed_pins"]
        raise WrongPin("Wrong PIN for this name." + (f" {left} tries left." if player["failed_pins"] else
                                                      f" Locked for {LOCK_SECONDS} seconds."))
    if player.get("failed_pins") or player.get("locked_until"):
        player["failed_pins"], player["locked_until"] = 0, 0
        db.save_player(player, path)
    return player, False
