"""Bot levels: which bots you may pick at a table and how many coins beating them pays.

Each bot has a level (easy, medium, hard, expert; see bots.py and config.LEVEL_COINS).
"""

from __future__ import annotations

from arcade.config import BOTS_PER_GAME, LEVEL_COINS, LEVELS


class BadPick(ValueError):
    """Raised when the chosen opponents do not fit the table."""


def win_coins(levels: list[str]) -> int:
    """Coins for beating these bots: one bot pays its level; several (UNO) pay the average, rounded."""
    if not levels or any(level not in LEVEL_COINS for level in levels):
        raise BadPick("Unknown level.")
    return round(sum(LEVEL_COINS[level] for level in levels) / len(levels))


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


def toggle(picked: list[str], name: str, needed: int) -> list[str]:
    """Click a bot in the picker: picks it, or takes it back if it was picked.

    With one opponent (checkers, Connect Four) a new click replaces the old one. With three (UNO), a fourth
    click replaces the bot picked first.
    """
    if name in picked:
        return [n for n in picked if n != name]
    chosen = picked + [name]
    return chosen[-needed:]
