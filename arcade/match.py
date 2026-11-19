"""Starting and finishing games, both in free play and in the championship.

The game screens only know their own rules. When a game ends they call
finish(), and this file decides what happens next: coins and a pop-up in free
play, or points and the scoreboard in the championship.
"""

from __future__ import annotations

from arcade import bots, catalog, hubmap, phrases, sound, state, ui
from arcade.config import (
    CHAMPIONSHIP_BOTS, SIMULATED_TIE_CHANCE,
)
from arcade.logic import championship, levels
from arcade.logic import uno as uno_rules
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


def begin_free_play(game_key: str, names: list[str]) -> None:
    """Free play against the bots the player picked (screens/versus.py)."""
    levels.check_pick(game_key, names, bots.BOT_NAMES)
    S.match = {"game": game_key, "mode": "free", "bots": list(names), "others": []}
    _walk_to_table(game_key, names)


def prize() -> int:
    """What winning this free-play game pays: the level of the bot, or the average of the three in UNO."""
    return levels.win_coins([bots.level(name) for name in S.match["bots"]])


def play_again() -> None:
    """Play again on the result box (free play only): the same table against the same bots, straight away.

    Everyone is still seated, so there is no walk: the new game fades in from black, like any game that starts.
    """
    S.match = levels.rematch(S.match, bots.BOT_NAMES)
    sound.play("table")
    ui.fade_next()
    start_game()


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
    if champ["round"] > 0:  # coming from the scoreboard: back into the room through black (A1)
        ui.fade_next()
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
    S.uno_pick, S.uno_deadline = [], None  # UNO house rules: cards picked so far, time left to say UNO
    S.turn_deadline = None  # the clock for the player's turn starts when their first turn begins
    for key in ("uno_focus", "uno_colour_focus", "checkers_cursor", "c4_column"):
        S.pop(key, None)  # the keyboard highlights start fresh: first playable card, a movable piece, the middle column
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


PLACE_TITLES = {1: "VICTORY!", 2: "2ND PLACE!", 3: "3RD PLACE!"}


def finish(winners: list[str], tied: bool = False, places: list[str] | None = None) -> None:
    """A game screen calls this once when its game is over. UNO also gives everyone's places, 1st to last."""
    match = S.match
    me = S.player["name"]
    rng = state.rng()
    if match["mode"] == "free" and places and len(places) > 2:
        _finish_with_places(places)
        return
    sound.play("tie" if tied else "win" if me in winners else "lose")  # A7
    if match["mode"] == "free":
        won = not tied and me in winners
        if won:
            coins = prize()
            S.player["coins"] += coins
            S.player["wins"][match["game"]] += 1
            state.save()
            S.result = {"title": "VICTORY!", "line": rng.choice(phrases.WIN_LINES), "coins": coins}
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
    ui.fade_next()  # from the table to the scoreboard through black (A1)
    S.screen = "champ_score"


def _finish_with_places(places: list[str]) -> None:
    """Free-play UNO: coins for 1st, 2nd and 3rd (levels.place_coins); only 1st counts as a win."""
    me = S.player["name"]
    place = places.index(me) + 1
    coins = levels.place_coins([bots.level(name) for name in S.match["bots"]], place)
    standings = "  ".join(f"{uno_rules.ordinal(i + 1).upper()} {'YOU' if name == me else name}"
                          for i, name in enumerate(places))
    if place == 1:
        S.player["wins"][S.match["game"]] += 1
        line = f"{state.rng().choice(phrases.WIN_LINES)} {standings}"
    elif place == len(places):
        line = f"{state.rng().choice(phrases.LOSE_LINES)} {standings}"
    else:
        line = standings
    S.player["coins"] += coins
    state.save()
    sound.play("win" if place == 1 else "lose" if place == len(places) else "tie")
    S.result = {"title": PLACE_TITLES.get(place, "LAST PLACE"), "line": line, "coins": coins}


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
    ui.fade_next()  # from the table back into the room through black (A1)
    S.screen = "hub"
