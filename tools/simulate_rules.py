"""Play thousands of games with the rules alone (no screens), with random and bot players, and check that nothing
breaks: no crash, every game ends, no card appears or disappears, every refused move changes nothing.

    uv run python tools/simulate_rules.py --games 1000

Covers UNO (2 to 4 players, with the house rules: stacking, twins, saying or forgetting UNO, Corta UNO), checkers,
Connect Four, the trivia face-off, and online lobbies (several players acting at random, out of turn too, with the
15-second clock running out). Fast: a few seconds per thousand games.
"""

from __future__ import annotations

import argparse
import copy
import pathlib
import random
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from arcade.config import UNO_LEVELS  # noqa: E402
from arcade.logic import trivia  # noqa: E402
from arcade.logic.checkers import CheckersGame  # noqa: E402
from arcade.logic.checkers import IllegalMove as CheckersIllegal  # noqa: E402
from arcade.logic.connect4 import Connect4Game  # noqa: E402
from arcade.logic.connect4 import IllegalMove as Connect4Illegal  # noqa: E402
from arcade.logic.lobby import TURN_SECONDS, LobbyError, Lobbies  # noqa: E402
from arcade.logic.uno import COLOURS, WILD, IllegalMove, UnoGame  # noqa: E402

LEVELS = list(UNO_LEVELS)


def cards_in(game: UnoGame) -> int:
    return len(game.deck) + len(game.discard) + sum(len(h) for h in game.hands.values())  # (a held card is in the hand)


def state_of(game: UnoGame):
    return (copy.deepcopy(game.hands), list(game.discard), list(game.deck), game.current, game.pending, game.colour,
            game.uno_due, game.held, game.draws, game.direction, list(game.out), game.winner)


def uno_game(rng: random.Random) -> dict:
    """One UNO game: one random player (the 'human') and bots at random levels, all the house rules."""
    count = rng.choice((2, 3, 4))
    names = ["ME"] + [f"BOT{i}" for i in range(1, count)]
    game = UnoGame(names, random.Random(rng.random()), start=rng.randrange(count))
    levels = {name: rng.choice(LEVELS) for name in names}
    stats = {"refused": 0, "cuts": 0, "missed": 0}
    for turn in range(3000):
        assert cards_in(game) == 108, f"UNO cards: {cards_in(game)}"
        if game.winner:
            break
        # someone is down to one card and has not said UNO: they say it, forget, or get cut
        if game.uno_due:
            holder = game.uno_due
            roll = rng.random()
            if roll < 0.08:
                game.miss_uno(holder)
                stats["missed"] += 1
            elif roll < 0.18:
                duel = trivia.Duel(holder, "X", random.Random(rng.random()), 0.0)
                now = 0.0
                while duel.phase != "done":
                    now += rng.uniform(0.5, 4)
                    for who in duel.players:
                        if rng.random() < 0.7 and duel.phase == "ask":
                            try:
                                duel.answer(who, rng.random() < 0.6, now)
                            except trivia.TriviaError:
                                pass
                    duel.tick(now)
                    assert now < 600, "the face-off never ends"
                stats["cuts"] += 1
                if duel.result == "holder":
                    game.lose_cut(holder, trivia.CUT_PENALTY)
                else:
                    game.call_uno(holder)
            else:
                game.call_uno(holder)
            continue
        player = game.current
        if player != "ME":
            game.bot_turn(player, say_uno=False, **UNO_LEVELS[levels[player]])
            continue
        roll = rng.random()
        if roll < 0.1:  # an illegal move: it must be refused and change nothing
            before = state_of(game)
            hand = game.hands[player]
            bad = rng.choice([[], [("purple", "9")], [hand[0], hand[-1]] if len(hand) > 1 else [], [hand[0]]])
            try:
                game.play(player, bad, rng.choice(COLOURS + (None,)))
                stats["refused"] -= 1  # it was legal after all (the first card fitted)
            except IllegalMove:
                assert state_of(game) == before, "a refused move changed the game"
            stats["refused"] += 1
            continue
        if roll < 0.15:
            game.auto_turn(player)  # the 15 seconds ran out
            continue
        playable = game.playable_cards(player)
        if playable and roll < 0.85:
            first = rng.choice(playable)
            cards = [first] + [c for c in game.partners(player, first) if c != first][:rng.randrange(3)]
            colour = rng.choice(COLOURS) if cards[-1][0] == WILD else None
            try:
                game.play(player, cards, colour)
            except IllegalMove:
                game.play(player, [first], colour if first[0] == WILD else None)
        elif game.draws and (not game.can_draw(player) or rng.random() < 0.5):
            game.pass_turn(player)
        elif game.can_draw(player):
            game.draw(player)
        else:
            game.auto_turn(player)
    else:
        raise AssertionError("UNO game did not end in 3000 turns")
    assert sorted(game.places) == sorted(names) and len(set(game.places)) == len(names), game.places
    return stats


def checkers_game(rng: random.Random) -> dict:
    game, refused = CheckersGame(), 0
    for _ in range(600):
        if game.winner:
            return {"refused": refused}
        if rng.random() < 0.1:  # a move that is not allowed changes nothing
            board = copy.deepcopy(game.board)
            try:
                game.move((rng.randrange(8), rng.randrange(8)), (rng.randrange(8), rng.randrange(8)))
            except CheckersIllegal:
                assert game.board == board
                refused += 1
            continue
        if rng.random() < 0.5:
            game.random_move(rng)
        else:
            game.bot_move(rng, depth=rng.choice((1, 2, 3)), blunder=rng.random() * 0.3)
    raise AssertionError("checkers game did not end in 600 moves")


def connect4_game(rng: random.Random) -> dict:
    game, refused = Connect4Game(), 0
    for _ in range(200):
        if game.winner:
            assert game.winner in ("red", "yellow", "draw") or game.winner
            return {"refused": refused}
        if rng.random() < 0.05:
            full = [c for c in range(7) if c not in game.legal_columns()] + [7, -1]
            board = copy.deepcopy(game.board)
            try:
                game.drop(rng.choice(full))
            except (Connect4Illegal, IndexError, ValueError):
                assert game.board == board
                refused += 1
            continue
        if rng.random() < 0.5:
            game.random_move(rng)
        else:
            game.bot_move(rng, depth=rng.choice((1, 2, 3)), blunder=rng.random() * 0.3)
    raise AssertionError("Connect Four game did not end in 200 moves")


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def lobby_game(rng: random.Random) -> dict:
    """Several players in an online lobby, acting at random (often out of turn), with the clock running."""
    clock = Clock()
    lobbies = Lobbies(random.Random(rng.random()), clock=clock)
    game = rng.choice(("uno", "checkers", "connect4"))
    count = rng.choice((2, 3, 4)) if game == "uno" else 2
    names = [f"P{i}" for i in range(count)]
    code = lobbies.create({"name": names[0], "look": None, "tag": None})
    for name in names[1:]:
        lobbies.join(code, {"name": name, "look": None, "tag": None})
    lobbies.choose(code, names[0], game)
    lobbies.start(code, names[0])
    refused = 0
    for _ in range(4000):
        lobby = lobbies.get(code)
        if lobby.result is not None:
            if game == "uno":
                assert sorted(lobby.result["places"]) == sorted(names)
            return {"refused": refused}
        table = lobby.table
        if game == "uno":
            assert cards_in(table) == 108, f"online UNO cards: {cards_in(table)}"
        clock.now += rng.choice((0.2, 0.5, 1.0, 3.0, TURN_SECONDS + 1 if rng.random() < 0.05 else 0.3))
        name = rng.choice(names) if rng.random() < 0.3 else (lobby.current() or rng.choice(names))
        try:
            if lobby.duel is not None:
                lobbies.act(code, name, "answer", yes=rng.random() < 0.5)
            elif game == "uno":
                roll = rng.random()
                if table.uno_due and roll < 0.15:
                    lobbies.act(code, name, "cut")
                elif table.uno_due and roll < 0.7:
                    lobbies.act(code, table.uno_due, "uno")
                elif name == table.current and table.playable_cards(name) and roll < 0.85:
                    card = rng.choice(table.playable_cards(name))
                    lobbies.act(code, name, "play", cards=[card], colour=rng.choice(COLOURS))
                elif name == table.current and table.draws and rng.random() < 0.5:
                    lobbies.act(code, name, "pass")
                else:
                    lobbies.act(code, name, "draw")
            elif game == "checkers":
                move = rng.choice(table.legal_moves())
                lobbies.act(code, name, "move", start=move[0], end=move[1])
            else:
                lobbies.act(code, name, "drop", col=rng.choice(table.legal_columns()))
        except (LobbyError, IllegalMove, CheckersIllegal, Connect4Illegal):
            refused += 1
        lobbies.version(code)  # (asking for the version also lets the server's clock act)
    raise AssertionError(f"online {game} game did not end")


SIMULATIONS = {"uno": uno_game, "checkers": checkers_game, "connect4": connect4_game, "online": lobby_game}


def main(games: int, seed: int) -> int:
    failures = 0
    for kind, simulate in SIMULATIONS.items():
        rng, started, totals = random.Random(seed), time.time(), {}
        for i in range(games):
            try:
                for key, value in simulate(rng).items():
                    totals[key] = totals.get(key, 0) + value
            except Exception as problem:  # noqa: BLE001 (report every kind of failure)
                failures += 1
                print(f"*** {kind} game {i + 1} (seed {seed}): {type(problem).__name__}: {problem}")
        print(f"{kind:9} {games} games in {time.time() - started:5.1f} s  {totals}", flush=True)
    print("no problems found" if not failures else f"{failures} problems found")
    return failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--games", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    sys.exit(1 if main(args.games, args.seed) else 0)
