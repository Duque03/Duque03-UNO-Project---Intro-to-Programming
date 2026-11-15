"""The championship: three rounds (UNO, checkers, Connect Four) scored with points."""

from __future__ import annotations

import random

from arcade.config import GAMES, POINTS_TIE, POINTS_WIN

ROUNDS = list(GAMES)
MAX_POINTS = POINTS_WIN * len(ROUNDS)


def is_unlocked(player: dict) -> bool:
    """The championship opens once you have won each game at least once."""
    return all(player["wins"].get(game, 0) >= 1 for game in GAMES)


def missing_games(player: dict) -> list[str]:
    return [game for game in GAMES if player["wins"].get(game, 0) < 1]


def new_championship(me: str, bot_names: list[str]) -> dict:
    if len(bot_names) != 3:
        raise ValueError("A championship needs exactly 3 bots.")
    players = [me] + list(bot_names)
    return {
        "me": me,
        "players": players,
        "points": {name: 0 for name in players},
        "before": {name: 0 for name in players},  # points before the latest round (for the bar animation)
        "round": 0,  # index into ROUNDS of the round being played
        "pairs": [],
        "last_winners": [],
        "last_tied": [],
    }


def current_game(champ: dict) -> str | None:
    return ROUNDS[champ["round"]] if champ["round"] < len(ROUNDS) else None


def is_over(champ: dict) -> bool:
    return champ["round"] >= len(ROUNDS)


def draw_pairs(champ: dict, rng: random.Random) -> list[tuple[str, str]]:
    """Split the four players into two duels. The player's duel comes first."""
    bots = [name for name in champ["players"] if name != champ["me"]]
    rng.shuffle(bots)
    champ["pairs"] = [(champ["me"], bots[0]), (bots[1], bots[2])]
    return champ["pairs"]


def simulate_duel(a: str, b: str, rng: random.Random, tie_chance: float = 0.0) -> str | None:
    """Decide a bot-versus-bot game without playing it. None means a tie."""
    if rng.random() < tie_chance:
        return None
    return rng.choice([a, b])


def record_round(champ: dict, results: list[tuple[list[str], bool]]) -> None:
    """Add the points for one round and move on to the next.

    results: one entry per game played this round: (names, tied).
    A win gives each listed name 2 points. A tie gives each listed name 1 point.
    """
    if is_over(champ):
        raise ValueError("The championship is already over.")
    champ["before"] = dict(champ["points"])
    champ["last_winners"], champ["last_tied"] = [], []
    for names, tied in results:
        for name in names:
            if name not in champ["points"]:
                raise ValueError(f"{name} is not in this championship.")
            champ["points"][name] += POINTS_TIE if tied else POINTS_WIN
            (champ["last_tied"] if tied else champ["last_winners"]).append(name)
    champ["round"] += 1


def standings(champ: dict) -> list[tuple[str, int]]:
    order = {name: i for i, name in enumerate(champ["players"])}
    return sorted(champ["points"].items(), key=lambda item: (-item[1], order[item[0]]))


def champions(champ: dict) -> list[str]:
    best = max(champ["points"].values())
    return [name for name in champ["players"] if champ["points"][name] == best]


def player_is_champion(champ: dict) -> bool:
    """Sharing first place still counts as winning the championship."""
    return is_over(champ) and champ["me"] in champions(champ)
