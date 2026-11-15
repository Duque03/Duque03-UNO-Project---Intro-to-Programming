"""Starting and finishing games, both in free play and in the championship.

The game screens only know their own rules. When a game ends they call
finish(), and this file decides what happens next: coins and a pop-up in free
play, or points and the scoreboard in the championship.
"""

from __future__ import annotations

from arcade import bots, catalog, hubmap, phrases, state
from arcade.config import (
    BOTS_PER_GAME, CHAMPIONSHIP_BOTS, COINS_PER_WIN, SIMULATED_TIE_CHANCE,
)
from arcade.logic import championship
from arcade.logic.checkers import CheckersGame
from arcade.logic.connect4 import Connect4Game
from arcade.logic.uno import UnoGame
from arcade.state import S

SEAT_FACING = ["down", "right", "left"]  # across the table, left seat, right seat


def _walk_to_table(game_key: str, seated: list[str]) -> None:
    """Send the player and the given bots to a table, then zoom in and start."""
    spot = hubmap.SPOTS[game_key]
    movers = {S.player["name"]: (S.hub["pos"], spot["stand"], "up")}
    for name, seat, face in zip(seated, spot["seats"], SEAT_FACING):
        movers[name] = (S.hub["bots"][name]["pos"], seat, face)
    S.hub["walk"] = {"movers": movers, "zoom": game_key, "then": "start_game"}
    S.screen = "hub"


def begin_free_play(game_key: str) -> None:
    names = state.rng().sample(bots.BOT_NAMES, BOTS_PER_GAME[game_key])
    S.match = {"game": game_key, "mode": "free", "bots": names, "others": []}
    _walk_to_table(game_key, names)


def begin_championship() -> None:
    names = state.rng().sample(bots.BOT_NAMES, CHAMPIONSHIP_BOTS)
    S.champ = championship.new_championship(S.player["name"], names)
    next_championship_round()


def next_championship_round() -> None:
    champ = S.champ
    game_key = championship.current_game(champ)
    rivals = [name for name in champ["players"] if name != champ["me"]]
    if game_key == "uno":
        opponents, others = rivals, []
    else:
        pairs = championship.draw_pairs(champ, state.rng())
        opponents, others = [pairs[0][1]], list(pairs[1])
    S.match = {"game": game_key, "mode": "champ", "bots": opponents, "others": others}
    _walk_to_table(game_key, opponents + others)


def start_game() -> None:
    """Create the rules object for the current match and open its screen."""
    match = S.match
    me = S.player["name"]
    if match["game"] == "uno":
        S.game = UnoGame([me] + match["bots"], state.rng())
    elif match["game"] == "checkers":
        S.game = CheckersGame()
    else:
        S.game = Connect4Game()
    S.result = None
    S.flash = ""
    S.selected = None
    S.pending_wild = None
    S.screen = match["game"]


def opponents() -> list[dict]:
    """The bots sitting across the table, ready for the scene painter."""
    return [
        {"name": name, "look": bots.look(bots.get(name)), "tag": catalog.spec_for("name", bots.get(name)["tag"])}
        for name in S.match["bots"]
    ]


def mode_label() -> str:
    if S.match["mode"] == "champ":
        return f"CHAMPIONSHIP - ROUND {S.champ['round'] + 1} OF 3"
    return "FREE PLAY"


def finish(winners: list[str], tied: bool = False) -> None:
    """A game screen calls this once when its game is over."""
    match = S.match
    me = S.player["name"]
    rng = state.rng()
    if match["mode"] == "free":
        won = not tied and me in winners
        if won:
            S.player["coins"] += COINS_PER_WIN
            S.player["wins"][match["game"]] += 1
            state.save()
            S.result = {"title": "VICTORY!", "line": rng.choice(phrases.WIN_LINES), "coins": COINS_PER_WIN}
        elif tied:
            S.result = {"title": "TIE!", "line": rng.choice(phrases.TIE_LINES), "coins": 0}
        else:
            S.result = {"title": "GAME OVER", "line": rng.choice(phrases.LOSE_LINES), "coins": 0}
        return

    results = [(list(winners), tied)]
    if match["others"]:  # the other two bots "play" at the same time
        a, b = match["others"]
        tie_chance = SIMULATED_TIE_CHANCE if match["game"] == "connect4" else 0.0
        winner = championship.simulate_duel(a, b, rng, tie_chance)
        results.append(([a, b], True) if winner is None else ([winner], False))
    championship.record_round(S.champ, results)
    S.score_animated = False
    S.screen = "champ_score"


def back_to_hub(centre: bool = False) -> None:
    """Leave the table and stand in the arcade again."""
    game_key = S.match["game"] if S.match else None
    state.reset_bots()
    if centre or game_key is None:
        S.hub["pos"], S.hub["dir"] = hubmap.CENTER, "down"
    else:
        S.hub["pos"], S.hub["dir"] = hubmap.SPOTS[game_key]["stand"], "up"
    S.hub["walk"] = None
    S.match = S.game = S.result = None
    S.flash = ""
    S.screen = "hub"
