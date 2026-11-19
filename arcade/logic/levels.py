"""Bot levels: which bots you may pick at a table and how many coins beating them pays.

Each bot has a level (easy, medium, hard, expert; see bots.py and config.LEVEL_COINS).
"""

from __future__ import annotations

from arcade.config import BOTS_PER_GAME, LEVEL_COINS, LEVELS, UNO_PLACE_SHARE


class BadPick(ValueError):
    """Raised when the chosen opponents do not fit the table."""


def win_coins(levels: list[str]) -> int:
    """Coins for beating these bots: one bot pays its level; several (UNO) pay the average, rounded."""
    if not levels or any(level not in LEVEL_COINS for level in levels):
        raise BadPick("Unknown level.")
    return round(sum(LEVEL_COINS[level] for level in levels) / len(levels))


def place_coins(levels: list[str], place: int) -> int:
    """UNO prize for finishing in `place` (1 = first): 1st the full prize, 2nd half, 3rd a quarter, last nothing.

    Halves are rounded up (half of 15 is 8)."""
    if place < 1:
        raise ValueError("Places start at 1.")
    return int(win_coins(levels) * UNO_PLACE_SHARE.get(place, 0) + 0.5)


def stars(level: str) -> int:
    """1 star for easy up to 4 for expert."""
    return LEVELS.index(level) + 1


def check_pick(game: str, names: list[str], known: list[str]) -> None:
    """The opponents chosen for a table must be real bots, all different, and exactly as many as the table needs."""
    needed = BOTS_PER_GAME[game]
    if any(name not in known for name in names):
        raise BadPick("That bot is not in the arcade.")
    if len(set(names)) != len(names):
        raise BadPick("Pick each bot only once.")
    if len(names) != needed:
        raise BadPick(f"Pick {needed} opponent{'s' if needed > 1 else ''}.")


def rematch(match: dict | None, known: list[str]) -> dict:
    """Play again after a free-play game: a new match at the same table against the same bots (same prize).

    Only free play has a Play again; a championship goes on to its scoreboard. Raises BadPick when the
    match does not fit. The given match is not changed.
    """
    if not match or match.get("mode") != "free":
        raise BadPick("Play again is only for free play.")
    if match.get("game") not in BOTS_PER_GAME:
        raise BadPick("There is no such table.")
    names = list(match.get("bots") or [])
    check_pick(match["game"], names, known)
    return {"game": match["game"], "mode": "free", "bots": names, "others": []}


def toggle(picked: list[str], name: str, needed: int) -> list[str]:
    """Click a bot in the picker: picks it, or takes it back if it was picked.

    With one opponent (checkers, Connect Four) a new click replaces the old one. With three (UNO), a fourth
    click replaces the bot picked first.
    """
    if name in picked:
        return [n for n in picked if n != name]
    chosen = picked + [name]
    return chosen[-needed:]
