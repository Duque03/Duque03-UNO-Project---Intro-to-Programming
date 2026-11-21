"""Everything the game remembers while the browser tab is open.

Streamlit reruns the whole script on every click, so anything that must
survive goes into st.session_state. Progress that must survive closing the
browser (coins, cosmetics, wins) is written to the database by save().
"""

from __future__ import annotations

import os
import random
import sys
import time
import traceback

import streamlit as st

from arcade import bots, catalog, db, hubmap
from arcade import player as player_model

S = st.session_state

_DEFAULTS = {
    "screen": "title",
    "player": None,
    "hub": None,
    "match": None,  # {"game", "mode": "free" or "champ", "bots": [...], "others": [...]}
    "game": None,  # the rules object of the game being played
    "result": None,  # end-of-game pop-up in free play
    "champ": None,
    "flash": "",  # one-line message shown on the game table
    "paused_from": None,
    "last_name": "",
}


def init() -> None:
    for key, value in _DEFAULTS.items():
        if key not in S:
            S[key] = value
    if "rng" not in S:
        S.rng = random.Random()


def rng() -> random.Random:
    return S.rng


def go(screen: str) -> None:
    S.screen = screen


def save() -> None:
    if S.player:
        db.save_player(S.player)


def start_session(player: dict) -> None:
    """Walk into the arcade with a player who has signed in (see accounts.sign_in)."""
    S.player = player
    S.last_name = player["name"]
    S.hub = {"pos": hubmap.SPAWN, "dir": "up", "bots": {}, "walk": None}
    reset_bots()
    S.match = S.game = S.result = S.champ = None
    S.screen = "hub" if player.get("look_done", True) else "create"  # a new player makes their look first


def reset_bots() -> None:
    S.hub["bots"] = {b["name"]: {"pos": b["home"], "dir": b["dir"]} for b in bots.BOTS}


# ----- actors: the little dictionaries the scene painter wants

def player_actor(pos=None, direction=None, step=0) -> dict:
    p = S.player
    return {
        "name": p["name"],
        "look": player_model.look(p),
        "pos": pos or S.hub["pos"],
        "dir": direction or S.hub["dir"],
        "step": step,
        "tag": catalog.spec_for("name", p["equipped"]["name"]),
        "player": True,
    }


def bot_actor(name: str, pos=None, direction=None, step=0) -> dict:
    bot = bots.get(name)
    where = S.hub["bots"][name] if S.hub else {"pos": bot["home"], "dir": bot["dir"]}
    return {
        "name": name,
        "look": bots.look(bot),
        "pos": pos or where["pos"],
        "dir": direction or where["dir"],
        "step": step,
        "tag": catalog.spec_for("name", bot["tag"]),
        "path": where.get("path") if pos is None else None,  # a walk across the room (arcade/wander.py)
        "pid": where.get("pid"),
    }


def hub_actors(overrides: dict | None = None) -> list[dict]:
    """All six characters. overrides: name -> (pos, direction, step) while they walk."""
    overrides = overrides or {}
    me = S.player["name"]
    actors = []
    for name in bots.BOT_NAMES:
        actors.append(bot_actor(name, *overrides.get(name, (None, None, 0))))
    actors.append(player_actor(*overrides.get(me, (None, None, 0))))
    return actors


GAME_KEYS = ("game", "result", "duel", "duel_bot", "bot_uno", "uno_cutter", "uno_before", "uno_before_picks",
             "uno_intro", "starter_intro", "pending_wild", "uno_pick", "uno_deadline", "turn_deadline", "selected")
RECOVER_LIMIT = 3  # more than this many problems within a minute: show the error instead of going round in circles


def recover(problem: BaseException) -> bool:
    """Something went wrong while a screen was drawn. Instead of a black screen, write what happened in the log
    (Streamlit Cloud: Manage app > Logs), show a short message and go back to the arcade with the progress saved.
    Returns False when it keeps happening (or in the tests and the simulators: ARCADE_STRICT), so the caller raises."""
    traceback.print_exception(problem, file=sys.stderr)
    now = time.time()
    recent = [t for t in st.session_state.get("_recoveries", []) if now - t < 60] + [now]
    st.session_state["_recoveries"] = recent
    if os.environ.get("ARCADE_STRICT") or len(recent) > RECOVER_LIMIT:
        return False
    from arcade import ui  # (ui is not needed anywhere else in this file)

    for key in GAME_KEYS:
        st.session_state.pop(key, None)
    st.session_state["match"] = None
    if st.session_state.get("player") is None:
        st.session_state["screen"] = "title"
    else:
        st.session_state["screen"] = "lobby" if st.session_state.get("lobby_code") else "hub"
        try:  # (going back must not fail in its turn)
            if st.session_state.get("hub"):
                reset_bots()
            save()
        except Exception as second:  # noqa: BLE001
            traceback.print_exception(second, file=sys.stderr)
    ui.toast("Oops! Something went wrong. Back to the arcade.")
    return True
