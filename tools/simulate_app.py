"""Play the real game screens many times with a random player, headless, and report every crash.

    uv run python tools/simulate_app.py --games 100 --seed 1

Each game runs the real app (app.py through tools/sim_driver.py, with Streamlit's AppTest): the real screens, the
real pictures, the real end of the game (podium, PLAY AGAIN, CONTINUE). The player is random but mostly sensible:
it plays legal moves most of the time, sometimes an illegal one (it must be refused), sometimes pauses, opens the
rules, forgets to say UNO, cuts a bot's UNO, answers the face-off at random, plays again or goes back to the room.
Anything that raises is printed with the step that led to it. Slow (about a second per run): this is a check before
a release, not a unit test.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import random
import sys
import time
import traceback

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("ARCADE_DB", "/tmp/arcade_simulate.db")

from streamlit.testing.v1 import AppTest  # noqa: E402

sys.path.insert(0, str(ROOT / "tools"))
import sim_clock  # noqa: E402

from arcade import bots, catalog, hubmap  # noqa: E402
from arcade.config import BOTS_PER_GAME  # noqa: E402
from arcade import player as player_model  # noqa: E402
from arcade.logic.checkers import BOTTOM  # noqa: E402
from arcade.logic.connect4 import RED  # noqa: E402
from arcade.screens import checkers as checkers_screen  # noqa: E402
from arcade.screens import connect4 as connect4_screen  # noqa: E402
from arcade.screens import uno as uno_screen  # noqa: E402

GAMES = ("uno", "checkers", "connect4")
TABLES = set(GAMES)


def new_app(name: str) -> AppTest:
    at = AppTest.from_file(str(ROOT / "tools" / "sim_driver.py"), default_timeout=180)
    at.run()
    player = player_model.new_player(name)
    player["look_done"] = True
    player["coins"] = 500
    at.session_state["player"] = player
    at.session_state["hub"] = {"pos": hubmap.SPAWN, "dir": "up", "walk": None,
                               "bots": {b["name"]: {"pos": b["home"], "dir": b["dir"]} for b in bots.BOTS}}
    return at


def start(at: AppTest, rng: random.Random) -> str:
    game = rng.choice(GAMES)
    count = BOTS_PER_GAME[game]  # (UNO: always the three others, as the versus screen asks)
    names = rng.sample(bots.BOT_NAMES, count)
    if game != "uno" and rng.random() < 0.75:  # the strong bots think for seconds at every move: mostly the quick ones
        names = [rng.choice(("DEAN", "BARK"))]
    at.session_state["match"] = {"game": game, "mode": "free", "bots": names, "others": []}
    at.session_state["_sim_start"] = True
    return game


def button(at: AppTest, key: str):
    for b in at.button:
        if b.key == key and not b.disabled:
            return b
    return None


def press(at: AppTest, key: str) -> bool:
    b = button(at, key)
    if b is None:
        return False
    b.click()
    return True


def click(at: AppTest, box) -> None:
    left, top, right, bottom = box
    at.session_state["_sim_click"] = ((left + right) / 2, (top + bottom) / 2)


def opponents(at):
    return [{"name": n, "look": bots.look(bots.get(n)), "tag": catalog.spec_for("name", bots.get(n)["tag"])}
            for n in at.session_state["match"]["bots"]]


def region(regions, wanted):
    for box, action in regions:
        if action == wanted:
            return box
    return None


def act_uno(at, rng) -> str:
    S = at.session_state
    game, me = S["game"], S["player"]["name"]
    if S["duel"] if "duel" in S else None:
        if rng.random() < 0.3:
            press(at, rng.choice(("duel_yes", "duel_no")))  # (refused once the player has answered)
        sim_clock.sleep(0.5)  # half a second goes by: the bot answers, a question's time runs out
        return "duel"
    if "bot_uno" in S and S["bot_uno"]:
        if rng.random() < 0.35:
            press(at, "uno_cut")
            return "cut"
        sim_clock.sleep(0.4)  # the bot is about to say UNO
        return "wait uno"
    if game.uno_due == me and game.winner is None:
        if rng.random() < 0.06:
            sim_clock.sleep(2.6)  # wait before saying UNO (a bot may cut it meanwhile: there is no time limit)
            return "wait"
        if rng.random() < 0.3:
            press(at, "keys_uno_space")  # Space presses the big UNO! button
            return "uno space"
        press(at, "uno_call")
        return "uno"
    if "pending_wild" in S and S["pending_wild"] is not None:
        if rng.random() < 0.5:
            press(at, "uno_colour")
        else:
            _, regions = uno_screen.draw(game, me, opponents(at), choosing=True, hands=None)
            colours = [box for box, action in regions if action[0] == "colour"]
            click(at, rng.choice(colours))
        return "colour"
    if game.winner is not None or game.current != me:
        return "wait"
    picks = list(S["uno_pick"]) if "uno_pick" in S else []
    _, regions = uno_screen.draw(game, me, opponents(at), picks=picks, hands=None)
    hand = uno_screen.sorted_hand(game.hands[me])
    roll = rng.random()
    if picks and roll < 0.9:
        box = region(regions, ("play",))
        if box:
            click(at, box)
        else:
            press(at, "uno_play")
        return "play"
    if roll < 0.04:
        press(at, rng.choice(("uno_pause", "uno_rules")))
        return "menu"
    if roll < 0.08 and len(hand) > 1:
        press(at, rng.choice(("keys_uno_left", "keys_uno_right", "keys_uno_space")))
        return "key"
    playable = set(map(tuple, game.playable_cards(me))) if hasattr(game, "playable_cards") else set()
    good = [i for i, card in enumerate(hand) if tuple(card) in playable]
    if good and roll < 0.85:
        click(at, region(regions, ("card", rng.choice(good))))
        return "pick"
    if roll < 0.9 and hand:
        click(at, region(regions, ("card", rng.randrange(len(hand)))))  # maybe a card that does not fit
        return "pick?"
    if game.draws and region(regions, ("pass",)) and rng.random() < 0.6:
        click(at, region(regions, ("pass",)))
        return "pass"
    if region(regions, ("draw",)):
        click(at, region(regions, ("draw",)))
    else:
        press(at, "uno_draw")
    return "draw"


def act_checkers(at, rng) -> str:
    S = at.session_state
    game = S["game"]
    if game.winner is not None or game.turn != BOTTOM:
        return "wait"
    roll = rng.random()
    if roll < 0.04:
        press(at, rng.choice(("checkers_pause", "checkers_rules")))
        return "menu"
    if roll < 0.1:
        press(at, rng.choice(("keys_checkers_left", "keys_checkers_right", "keys_checkers_up", "keys_checkers_down",
                              "keys_checkers_space")))
        return "key"
    selected = S["selected"] if "selected" in S else None
    _, regions = checkers_screen.draw(game, {"name": "X", "look": bots.look(bots.BOTS[0]), "tag": None}, selected)
    cells = {action[1:]: box for box, action in regions if action[0] == "cell"}
    moves = game.legal_moves()
    if roll < 0.15:
        click(at, rng.choice(list(cells.values())))  # anywhere on the board (often refused)
        return "cell?"
    if selected is not None:
        targets = [m[1] for m in moves if tuple(m[0]) == tuple(selected)]
        if targets:
            click(at, cells[tuple(rng.choice(targets))])
            return "move"
    move = rng.choice(moves)
    click(at, cells[tuple(move[0])])
    return "select"


def act_connect4(at, rng) -> str:
    S = at.session_state
    game = S["game"]
    if game.winner is not None or game.turn != RED:
        return "wait"
    roll = rng.random()
    if roll < 0.04:
        press(at, rng.choice(("connect4_pause", "connect4_rules")))
        return "menu"
    if roll < 0.25:
        press(at, f"keys_connect4_col{rng.choice(game.legal_columns()) + 1}")
        return "key"
    col = rng.choice(game.legal_columns()) if roll < 0.95 else rng.randrange(7)
    x = connect4_screen.BOARD_X + col * connect4_screen.CELL + connect4_screen.CELL // 2
    at.session_state["_sim_click"] = (x, connect4_screen.BOARD_Y + 60)
    return "drop"


ACTS = {"uno": act_uno, "checkers": act_checkers, "connect4": act_connect4}


def check(at, game_key) -> None:
    """Things that must always hold while a game is on."""
    S = at.session_state
    game = S["game"] if "game" in S else None
    if game_key == "uno" and game is not None and hasattr(game, "hands"):
        total = len(game.deck) + len(game.discard) + sum(len(h) for h in game.hands.values())  # (held: in the hand)
        assert total == 108, f"UNO cards: {total} instead of 108"


def run(games: int, seed: int, verbose: bool = False) -> int:
    rng = random.Random(seed)
    at = new_app(f"SIM{seed}")
    done = crashes = 0
    steps_in_game = 0
    game_key = start(at, rng)
    history = []
    started = time.time()
    while done < games:
        screen = at.session_state["screen"]
        try:
            if screen in TABLES:
                if at.session_state["result"] if "result" in at.session_state else None:
                    done += 1
                    steps_in_game = 0
                    if verbose:
                        print(f"game {done}: {game_key} -> {at.session_state['result']['title']}", flush=True)
                    if rng.random() < 0.4:
                        press(at, f"{screen}_again") or press(at, f"{screen}_continue")
                        history.append("again")
                    else:
                        press(at, f"{screen}_continue")
                        history.append("continue")
                else:
                    history.append(ACTS[screen](at, rng))
                    steps_in_game += 1
            elif screen == "pause":
                if rng.random() < 0.05 and press(at, "pause_leave_table"):
                    done += 1
                    history.append("leave table")
                else:
                    press(at, "pause_resume")
                    history.append("resume")
            elif screen == "howto":
                press(at, "howto_back")
                history.append("rules back")
            elif screen == "hub":
                game_key = start(at, rng)
                history.append(f"start {game_key}")
            else:
                history.append(f"? {screen}")
                at.session_state["screen"] = "hub"
            at.run()
            if at.exception:
                raise RuntimeError("\n".join(str(e.value) for e in at.exception))
            check(at, game_key)
            if verbose and steps_in_game and steps_in_game % 50 == 0:
                print(f"  ... {game_key} step {steps_in_game}: {history[-5:]}", flush=True)
            if steps_in_game > (3000 if game_key == "uno" else 900):
                raise RuntimeError(f"stuck in {screen}: {history[-20:]}")
        except Exception as problem:  # report, then start again with a fresh app
            crashes += 1
            print(f"\n*** CRASH (seed {seed}, game {done + 1}, {game_key}, screen {screen}) after {history[-12:]}")
            print("".join(traceback.format_exception(problem))[-3000:], flush=True)
            at = new_app(f"SIM{seed}")
            game_key = start(at, rng)
            steps_in_game = 0
            done += 1
        history = history[-50:]
    print(f"seed {seed}: {done} games, {crashes} crashes, {time.time() - started:.0f} s", flush=True)
    return crashes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    sys.exit(1 if run(args.games, args.seed, args.verbose) else 0)
