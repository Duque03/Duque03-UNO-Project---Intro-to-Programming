"""Corta UNO in the arcade (offline): the moments when a UNO can be cut, and the trivia face-off.

The rules are in arcade/logic/trivia.py. Here: which bot tries to cut the player's UNO and when (CUT_LEVELS in
config.py), the short moment a bot waits before saying its own UNO (the player can cut it with K or the button), and
the face-off screen (Y / N, or Left / Right and Enter, or a click; a countdown under the table).
"""

from __future__ import annotations

import copy
import time

import streamlit as st

from arcade import bots, player, sound, state, ui
from arcade.art import duel as duel_art
from arcade.config import CUT_LEVELS, UNO_LEVELS
from arcade.logic import cursor
from arcade.logic.trivia import CUT_PENALTY, ROUND_SECONDS, Duel, bot_answer
from arcade.screens import common

S = st.session_state


def choose_cutter(game, me: str, now: float) -> dict | None:
    """The player is down to one card: the bot (if any) that will try to cut their UNO, and when it presses."""
    rng, best = state.rng(), None
    for name in game.active:
        if name == me:
            continue
        level = CUT_LEVELS[bots.level(name)]
        if rng.random() < level["cut"]:
            at = now + rng.uniform(*level["react"])
            if best is None or at < best["at"]:
                best = {"bot": name, "at": at}
    return best


def bot_window(bot: str, now: float) -> dict:
    """A bot is down to one card: how long it takes to say UNO (the player can cut it meanwhile), or if it forgets."""
    rng, level = state.rng(), bots.level(bot)
    return {"bot": bot, "until": now + rng.uniform(*CUT_LEVELS[level]["say"]),
            "forget": rng.random() < UNO_LEVELS[level]["forget_uno"]}


def start(holder: str, cutter: str) -> None:
    """Someone cut a UNO in time: the face-off begins."""
    S.duel, S.duel_bot, S.duel_focus = Duel(holder, cutter, state.rng(), time.time()), None, 0
    S.uno_cutter = S.bot_uno = None
    sound.play("start")


def _bot_of(duel, me: str) -> str:
    return duel.cutter if duel.holder == me else duel.holder


def _plan_bot(duel, me: str) -> dict:
    """When the bot answers this question, and what it says (decided once per question)."""
    plan = S.get("duel_bot")
    if plan is None or plan["round"] != duel.round:
        rng, level = state.rng(), CUT_LEVELS[bots.level(_bot_of(duel, me))]
        start_time = duel.deadline - ROUND_SECONDS
        at = min(start_time + rng.uniform(*level["think"]), duel.deadline - 0.4)
        plan = S.duel_bot = {"round": duel.round, "at": at, "yes": bot_answer(rng, duel.truth, level["knows"])}
    return plan


def _clock(duel) -> None:
    """The countdown under the table counts the seconds left to answer."""
    S.turn_deadline = duel.deadline if duel.phase == "ask" and duel.deadline > time.time() else None
    S.clock_total, S.clock_label = ROUND_SECONDS, "ANSWER"


def _move_on(duel, me: str) -> None:
    """Let time pass in the face-off: the bot answers when its moment came, a question whose time is up closes,
    the next question comes after the answers were shown."""
    now = time.time()
    if duel.phase == "ask":
        bot, plan = _bot_of(duel, me), _plan_bot(duel, me)
        if bot not in duel.answers and now >= plan["at"]:
            duel.answer(bot, plan["yes"], now)
    duel.tick(now)


@st.fragment(run_every=0.25)
def duel_clock() -> None:
    """Four times a second: the bot answers when its time comes, a question closes when time is up, and the next
    one comes after the answers were shown. The whole screen runs again only when something changed."""
    duel = S.get("duel")
    if S.screen != "uno" or duel is None:
        return
    before = (duel.phase, duel.round, len(duel.answers))
    _move_on(duel, S.player["name"])
    if (duel.phase, duel.round, len(duel.answers)) != before:
        st.rerun()


def _finish(game, me: str) -> None:
    """The face-off is over: the player with UNO draws 7, or their UNO stands."""
    duel = S.pop("duel")
    S.pop("duel_bot", None)
    S.pop("clock_total", None)
    S.pop("clock_label", None)
    common.restart_clock()
    S.uno_before, S.uno_before_picks = copy.deepcopy(game), []  # the next run animates the cards
    if game.uno_due != duel.holder:  # (the UNO was settled some other way meanwhile: nothing more to do)
        S.uno_deadline = None
        return
    if duel.result == "holder":
        game.lose_cut(duel.holder, CUT_PENALTY)
        S.flash = ("Your UNO was cut! +7 cards" if duel.holder == me else f"You cut {duel.holder}'s UNO! +7 for them")
        sound.play("lose" if duel.holder == me else "win")
    else:
        game.call_uno(duel.holder)
        S.flash = "Your UNO stands!" if duel.holder == me else f"{duel.holder}'s UNO stands"
        sound.play("win" if duel.holder == me else "lose")
    S.uno_deadline = None


def render_duel(slot, game, me: str, opponents, table_img, key) -> None:
    """The face-off screen. Ends the run (st.rerun) when the face-off is over."""
    duel = S.duel
    _move_on(duel, me)  # the time may be up already (the countdown asked for this run)
    if duel.phase == "done":
        _finish(game, me)
        st.rerun()
    looks = {o["name"]: o["look"] for o in opponents}
    looks[me] = player.look(S.player)
    asking = duel.phase == "ask" and me not in duel.answers
    focus = S.get("duel_focus", 0)
    if asking and key in ("left", "right"):
        focus = cursor.step(focus, key, 2)
        sound.play("blip")
    if key in ("left", "right", "space"):
        S.uno_keyboard = True  # the yellow frame only shows while the player uses the keys
    S.duel_focus = focus
    view = {"holder": duel.holder, "cutter": duel.cutter, "looks": looks, "me": me, "round": duel.round,
            "question": duel.question, "phase": duel.phase, "answered": {p: p in duel.answers for p in duel.players},
            "answers": dict(duel.answers), "right": dict(duel.right), "truth": duel.truth, "result": duel.result,
            "focus": focus if asking and S.get("uno_keyboard") else None}
    img, regions = duel_art.duel_picture(table_img, view)
    _clock(duel)
    common.show(slot, img, "uno")
    point = ui.click()
    if point is not None:
        S.uno_keyboard = False
    action = ui.hit(regions, point)
    bar = ui.bar("duel", [1.4, 1.4, 1.4, 1])  # invisible: YES and NO are on the picture
    with bar[0]:
        yes = ui.button("Yes", "duel_yes", "Y", type="primary", disabled=not asking)
    with bar[1]:
        no = ui.button("No", "duel_no", "N", type="primary", disabled=not asking)
    if asking and key == "space":
        action = ("yes",) if focus == 0 else ("no",)
    answer = True if yes or action == ("yes",) else False if no or action == ("no",) else None
    if asking and answer is not None:
        duel.answer(me, answer, time.time())
        sound.play("blip")
        st.rerun()
    duel_clock()


def due_cut() -> dict | None:
    """The bot that cuts the player's UNO right now (its moment came before the player said UNO), if any."""
    cutter = S.get("uno_cutter")
    return cutter if cutter and time.time() >= cutter["at"] else None


@st.fragment(run_every=0.25)
def bot_uno_clock() -> None:
    """While a bot waits to say UNO: when its moment comes, it says it (or forgets and draws 2)."""
    window, game = S.get("bot_uno"), S.get("game")
    if S.screen != "uno" or window is None or game is None or time.time() < window["until"]:
        return
    S.bot_uno = None
    S.uno_before, S.uno_before_picks = copy.deepcopy(game), []
    if game.uno_due == window["bot"]:
        if window["forget"]:
            game.miss_uno(window["bot"])
        else:
            game.call_uno(window["bot"])
    st.rerun()


def render_bot_window(slot, game, me: str, picture) -> None:
    """A bot has one card and has not said UNO yet: the CORTA UNO button is up (K or a click)."""
    bot = S.bot_uno["bot"]
    common.run_clock(False)
    common.show(slot, picture, "uno")
    action = ui.hit(picture_regions(), ui.click())
    bar = ui.bar("cut", [1.4, 1.4, 1.4, 1])  # invisible: CORTA UNO! is on the picture
    with bar[0]:
        cut = ui.button("Corta UNO!", "uno_cut", "K", type="primary")
    if (cut or action == ("cut",)) and game.uno_due == bot:
        start(holder=bot, cutter=me)
        st.rerun()
    bot_uno_clock()


def picture_regions():
    """Where the CORTA UNO button is on the picture (the same place as the UNO button)."""
    from arcade.screens.uno import UNO_BOX  # (uno.py imports this file)
    return [(UNO_BOX, ("cut",))]

