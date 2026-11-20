"""An online game: UNO, checkers or Connect Four against the other people in the lobby (no bots).

The game itself lives in the lobby, on the server (arcade/logic/lobby.py); every move goes through
online.lobbies().act(), which checks it. This screen draws the table from this player's seat with the same pictures
as the arcade (the other players sit across the table, in turn order) and looks for changes once a second.
"""

from __future__ import annotations

import time

import streamlit as st

from arcade import online, sound, state, table_anim, ui
from arcade.art import duel as duel_art
from arcade.art import scenes
from arcade.logic import cursor
from arcade.logic.checkers import SIZE
from arcade.logic.checkers import IllegalMove as CheckersIllegal
from arcade.logic.connect4 import COLS
from arcade.logic.connect4 import IllegalMove as Connect4Illegal
from arcade.logic.lobby import LobbyError, online_coins
from arcade.logic.uno import COLOURS, WILD, card_name, ordinal
from arcade.logic.uno import IllegalMove as UnoIllegal
from arcade.screens import checkers as checkers_screen
from arcade.screens import connect4 as connect4_screen
from arcade.screens import online as online_screens
from arcade.screens import uno as uno_screen
from arcade.state import S

PROBLEMS = (LobbyError, UnoIllegal, CheckersIllegal, Connect4Illegal)


def _act(move: str, **args) -> None:
    """Send a move to the lobby. A refused move is shown in red; the game does not change."""
    try:
        online.lobbies().act(S.lobby_code, S.player["name"], move, **args)
        S.online_flash = ""
    except PROBLEMS as problem:
        S.online_flash = str(problem)
        sound.play("lose")
    st.rerun()


@st.fragment(run_every=1.0)
def _watch(code: str, seen: int, turn: str | None, deadline: float | None, me: str, label: str | None = None) -> None:
    """Once a second: the time left for whoever is playing (or to answer, in a Corta UNO face-off), and a new
    picture as soon as the game changes."""
    if online.lobbies().version(code) != seen:
        st.rerun(scope="app")
    if (turn or label) and deadline:
        left = max(0, int(deadline - time.time() + 0.99))
        who = label or ("YOUR TURN" if turn == me else f"{turn}'S TURN")
        colour = "#ff4f6d" if left <= 5 else "#3ad6ff"
        st.markdown(f"<div style='text-align:right;font:1.15rem \"Jersey 10\",monospace;color:{colour};"
                    f"letter-spacing:.05em'>{who}: {left}s</div>", unsafe_allow_html=True)


def _finish(lobby, me: str) -> None:
    """The game is over: coins once per game, and the result box on top of the table."""
    paid = S.setdefault("online_paid", set())
    key = (lobby.code, lobby.round)
    coins = online_coins(lobby.result, me)
    if key not in paid:
        paid.add(key)
        if coins:
            S.player["coins"] += coins
            state.save()
        places = lobby.result.get("places")
        won = (places and places[0] == me) or lobby.result.get("winner") == me
        sound.play("win" if won else "tie" if lobby.result.get("left") else "lose")


def _result_text(lobby, me: str) -> tuple[str, str]:
    result = lobby.result
    if result.get("left"):
        return "GAME OVER", f"{result['left']} left the game. Nobody wins this one."
    if result.get("places"):
        places = result["places"]
        place = places.index(me) + 1
        line = "  ".join(f"{ordinal(i + 1).upper()} {'YOU' if n == me else n}" for i, n in enumerate(places))
        title = "VICTORY!" if place == 1 else "LAST PLACE" if place == len(places) else f"{ordinal(place).upper()} PLACE!"
        return title, line
    if result.get("winner") is None:
        return "TIE!", "Nobody made four in a row."
    return ("VICTORY!", "You beat your friend!") if result["winner"] == me else ("GAME OVER", f"{result['winner']} wins!")


def render() -> None:
    code, me = S.get("lobby_code"), S.player["name"]
    try:
        lobby = online.lobbies().get(code)
    except LobbyError:
        S.online_message = "That lobby has closed."
        online_screens.leave()
        st.rerun()
    if me not in lobby.names():
        online_screens.leave()
        st.rerun()
    if lobby.table is None:
        S.screen = "lobby"
        st.rerun()
    S["_track"] = lobby.game  # the game's own music (arcade/music.py)
    S.setdefault("online_flash", "")
    if lobby.round != S.get("online_round_seen"):  # a new game: start with nothing picked or highlighted
        S.online_round_seen = lobby.round
        for key in ("ouno_pick", "ouno_wild", "ouno_focus", "ouno_colour", "ock_sel", "ock_cur", "oc4_col",
                    "ouno_seen", "ouno_sent_picks"):
            S.pop(key, None)
        S.online_flash = ""
        S.ouno_intro = lobby.game == "uno"  # UNO starts with the deal and the roulette (see _uno_plan)

    over = lobby.result is not None
    turn = lobby.current()
    mine = turn == me and not over
    if over:
        _finish(lobby, me)
    draw = {"uno": _uno, "checkers": _checkers, "connect4": _connect4}[lobby.game]
    draw(lobby, me, mine, over)
    duel = lobby.duel
    if duel is not None:  # the face-off's own clock
        _watch(code, lobby.version, None, duel.deadline if duel.phase == "ask" else None, me, "ANSWER")
    else:
        _watch(code, lobby.version, turn, lobby.deadline, me)


def _bar_end(bar, lobby, me: str, over: bool) -> None:
    """The last buttons of every online table: back to the lobby when the game is over, and Leave."""
    if over:
        with bar[0]:
            back = ui.button("Lobby", "otable_lobby", "Enter", type="primary")
        if back:
            S.online_round_done = lobby.round
            ui.fade_next()
            S.screen = "lobby"
            st.rerun()
    with bar[-1]:
        out = ui.button("Leave", "otable_leave", "Esc")
    if out:
        online_screens.leave()
        st.rerun()


def _show(img, regions, lobby, me, over, plan=None):
    """Show the table (with the result box when the game is over), after an animation if there is one."""
    if over:
        title, line = _result_text(lobby, me)
        img = scenes.result_panel(img, title, line, online_coins(lobby.result, me))
        regions = []
    slot = ui.screen()
    if plan is None:
        ui.show(slot, img)
        return regions
    table_anim.play(slot, plan)  # the canvas covers the old picture first, so the new one arrives unseen
    time.sleep(0.12)
    ui.show(slot, img)
    time.sleep(max(0.0, table_anim.seconds(plan) - 0.12))
    return regions


def _uno_plan(lobby, me: str, opponents):
    """What to animate on this browser: the deal and the roulette at the start of a game, then the cards that changed
    hands since this browser last drew the table. S.ouno_seen keeps that last table: only a picture of the past for
    the animations; the real game is always the one in the lobby."""
    game, plan = lobby.table, None
    if S.pop("ouno_intro", False):
        names = [o["name"] for o in opponents]
        starter = 0 if game.current == me else names.index(game.current) + 1
        plan = uno_screen.deal_plan(game, me, opponents, starter)
    elif S.get("ouno_seen") is not None:
        plan = uno_screen.move_plan(S.ouno_seen, game, me, opponents, S.pop("ouno_sent_picks", []))
    S.ouno_seen = game
    return plan


# ---------------------------------------------------------------- UNO

def _uno(lobby, me: str, mine: bool, over: bool) -> None:
    game = lobby.table
    seat = lobby.seats.index(me)
    opponents = [lobby.player(lobby.seats[(seat + k) % len(lobby.seats)]) for k in range(1, len(lobby.seats))]
    hand = uno_screen.sorted_hand(game.hands[me])
    picks = [i for i in S.get("ouno_pick") or [] if i < len(hand)]
    wild = S.get("ouno_wild")
    uno_open = game.uno_due == me and not over
    key = ui.keys("ouno", {"Left": "left", "Right": "right", "Space": "space"})  # on every run (see AGENTS.md)
    if lobby.duel is not None and not over:  # Corta UNO: the face-off takes over every screen at the table
        _uno_duel(lobby, me, opponents, key)
        return
    cut_open = game.uno_due not in (None, me) and me in game.active and not over  # Corta UNO can be pressed
    if not mine:
        key = None if not uno_open else key
    if uno_open and lobby.uno_deadline:
        S.uno_deadline = min(lobby.uno_deadline, time.time() + uno_screen.UNO_SECONDS)  # for the UNO! box's bar

    focus = colour_focus = None
    if mine and wild is None:
        focus = cursor.clamp(S.get("ouno_focus"), len(hand))  # starts on the first card (no hint)
        if key in ("left", "right"):
            focus = cursor.step(focus, key, len(hand))
            sound.play("blip")
        S.ouno_focus = focus
    elif mine:
        colour_focus = cursor.clamp(S.get("ouno_colour"), len(COLOURS))
        if key in ("left", "right"):
            colour_focus = cursor.step(colour_focus, key, len(COLOURS))
            sound.play("blip")
        S.ouno_colour = colour_focus
    flash = S.online_flash  # only what just happened; how to play is in the rules
    if cut_open:
        flash = f"{game.uno_due} has one card!"
    if key in ("left", "right", "space"):
        S.ouno_keyboard = True  # the yellow frame only shows while the player uses the keys
    keys = S.get("ouno_keyboard")
    img, regions = uno_screen.draw(game, me, opponents, flash, choosing=wild is not None, picks=picks,
                                   uno_open=uno_open, focus=focus if keys else None,
                                   colour_focus=colour_focus if keys else None, cut_open=cut_open)
    regions = _show(img, regions, lobby, me, over, _uno_plan(lobby, me, opponents))
    point = ui.click() if (mine or uno_open or cut_open) and not over else None
    if point is not None:
        S.ouno_keyboard = False  # playing with the mouse: no frame
    action = ui.hit(regions, point)

    bar = st.columns([1.3, 1, 1, 1.4, 1, 1])
    if over:
        _bar_end(bar, lobby, me, over)
        return
    with bar[0]:
        play = ui.button("Play" if wild is None else "Choose colour", "ouno_play", "Enter", type="primary",
                         disabled=not mine or (not picks and wild is None))
    with bar[1]:
        draw = ui.button("Draw", "ouno_draw", "D", disabled=not mine or not game.can_draw(me))
    with bar[2]:
        passed = ui.button("Pass", "ouno_pass", "P", disabled=not mine or not game.draws)
    with bar[3]:
        if cut_open:
            cut, uno = ui.button("Corta UNO!", "ouno_cut", "K", type="primary"), False
        else:
            cut, uno = False, ui.button("UNO!", "ouno_uno", "U", type="primary" if uno_open else "secondary")
    with bar[4]:
        cancel = ui.button("Cancel", "ouno_cancel", "X", disabled=not mine or (not picks and wild is None))
    _bar_end(bar, lobby, me, over)

    if uno or action == ("uno",):
        sound.play("coin")
        _act("uno")
    if cut or action == ("cut",):
        _act("cut")
    if not mine:
        return
    if cancel or (wild is not None and action == ("cancel",)):
        S.ouno_pick, S.ouno_wild = [], None
        st.rerun()
    if wild is not None:  # choosing the colour of a wild
        if play or key == "space":
            action = ("colour", COLOURS[colour_focus])
        if action and action[0] == "colour":
            S.ouno_sent_picks = picks  # the next picture animates them from where they stood
            S.ouno_wild, S.ouno_pick, S.ouno_focus = None, [], None
            _act("play", cards=wild, colour=action[1])
        return
    if draw or action == ("draw",):
        S.ouno_pick = []
        _act("draw")
    if passed:
        _act("pass")
    if key == "space" and focus is not None:
        action = ("card", focus)
    if play or action == ("play",):  # the pile (or Enter): the picked cards go down; nothing picked, nothing happens
        chosen = uno_screen.picked_cards(game.hands[me], picks)
        if chosen and not game.can_play(chosen[0]):
            S.online_flash = f"The {card_name(chosen[0])} does not match the pile"
            sound.play("lose")
            st.rerun()
        _play_cards(chosen)
    if action and action[0] == "card":  # a click picks a card (it stands up); equal cards can join it
        index = action[1]
        if index in picks:
            S.ouno_pick = [i for i in picks if i != index]
        elif picks and uno_screen.can_add(game.hands[me], picks, index):
            S.ouno_pick = picks + [index]
        else:
            S.ouno_pick = [index]
        S.ouno_focus, S.online_flash = index, ""
        sound.play("blip")
        st.rerun()


def _uno_duel(lobby, me: str, opponents, key) -> None:
    """The Corta UNO face-off (logic/trivia.py): its two players answer YES or NO; everyone else watches."""
    duel, game = lobby.duel, lobby.table
    playing = me in duel.players
    asking = playing and duel.phase == "ask" and me not in duel.answers
    focus = S.get("oduel_focus", 0)
    if asking and key in ("left", "right"):
        focus = cursor.step(focus, key, 2)
        sound.play("blip")
    if key in ("left", "right", "space"):
        S.ouno_keyboard = True
    S.oduel_focus = focus
    looks = {p["name"]: p["look"] for p in opponents}
    looks[me] = lobby.player(me)["look"]
    view = {"holder": duel.holder, "cutter": duel.cutter, "looks": looks, "me": me, "round": duel.round,
            "question": duel.question, "phase": duel.phase, "answered": {p: p in duel.answers for p in duel.players},
            "answers": dict(duel.answers) if duel.phase != "ask" else {me: duel.answers[me]} if me in duel.answers
            else {}, "right": dict(duel.right), "truth": duel.truth, "result": duel.result,
            "focus": focus if asking and S.get("ouno_keyboard") else None}
    table = uno_screen.draw(game, me, opponents)[0]
    img, regions = duel_art.duel_picture(table, view)
    ui.show(ui.screen(), img)
    point = ui.click() if asking else None
    if point is not None:
        S.ouno_keyboard = False
    action = ui.hit(regions, point)
    bar = st.columns([1.3, 1, 1, 1, 1, 1])
    with bar[0]:
        yes = ui.button("Yes", "oduel_yes", "Y", type="primary", disabled=not asking)
    with bar[1]:
        no = ui.button("No", "oduel_no", "N", type="primary", disabled=not asking)
    _bar_end(bar, lobby, me, False)
    if asking and key == "space":
        action = ("yes",) if focus == 0 else ("no",)
    if asking and (yes or no or action in (("yes",), ("no",))):
        sound.play("blip")
        _act("answer", yes=bool(yes or action == ("yes",)))


def _play_cards(cards: list) -> None:
    if not cards:
        return
    if cards[-1][0] == WILD:
        S.ouno_wild = [list(c) for c in cards]
        st.rerun()
    S.ouno_sent_picks = list(S.get("ouno_pick") or [])  # the next picture animates them from where they stood
    S.ouno_pick, S.ouno_focus = [], None
    _act("play", cards=[list(c) for c in cards])


# ---------------------------------------------------------------- Connect Four

def _connect4(lobby, me: str, mine: bool, over: bool) -> None:
    game = lobby.table
    side = lobby.side_of(me)
    friend = lobby.player(next(n for n in lobby.seats if n != me))
    key = ui.keys("oc4", {"Left": "left", "Right": "right", "Space": "drop", "Down": "down"})
    column = cursor.clamp(S.get("oc4_col", COLS // 2), COLS) if mine else None
    if mine and key in ("left", "right"):
        column = cursor.step(column, key, COLS)
        sound.play("blip")
    if mine:
        S.oc4_col = column
    flash = S.online_flash or ("" if mine or over else f"Waiting for {friend['name']}...")
    img, regions = connect4_screen.draw(game, friend, flash, column=column, me=side)
    regions = _show(img, regions, lobby, me, over)
    action = ui.hit(regions, ui.click() if mine else None)
    bar = st.columns([1.3, 1, 1, 1, 1])
    _bar_end(bar, lobby, me, over)
    if mine and key in ("drop", "down"):
        action = ("col", column)
    if mine and action and action[0] == "col":
        sound.play("blip")
        _act("drop", col=action[1])


# ---------------------------------------------------------------- checkers

def _checkers(lobby, me: str, mine: bool, over: bool) -> None:
    game = lobby.table
    side = lobby.side_of(me)
    turned = side != lobby.side_of(lobby.seats[0])
    friend = lobby.player(next(n for n in lobby.seats if n != me))
    key = ui.keys("ock", {"Up": "up", "Down": "down", "Left": "left", "Right": "right", "Space": "space"})
    selected = tuple(S.ock_sel) if S.get("ock_sel") and mine else None
    if game.chain:
        selected = tuple(game.chain)
    cell = tuple(S.get("ock_cur") or (SIZE - 1, 0))
    if mine and key in ("up", "down", "left", "right"):  # the arrows move the cursor as the board is seen
        dr, dc = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}[key]
        if turned:
            dr, dc = -dr, -dc
        cell = (min(SIZE - 1, max(0, cell[0] + dr)), min(SIZE - 1, max(0, cell[1] + dc)))
        S.ock_cur = cell
        sound.play("blip")
    flash = S.online_flash or ("" if mine or over else f"Waiting for {friend['name']}...")
    img, regions = checkers_screen.draw(game, friend, selected, flash, cursor_cell=cell if mine else None, me=side)
    regions = _show(img, regions, lobby, me, over)
    action = ui.hit(regions, ui.click() if mine else None)
    bar = st.columns([1.3, 1, 1, 1, 1])
    _bar_end(bar, lobby, me, over)
    if not mine:
        return
    if key == "space":
        action = ("cell", *cell)
    if not action or action[0] != "cell":
        return
    square = (action[1], action[2])
    S.ock_cur = square
    legal = game.legal_moves()
    if selected and any(m[0] == selected and m[1] == square for m in legal):
        S.ock_sel = None
        sound.play("blip")
        _act("move", start=selected, end=square)
    if any(m[0] == square for m in legal) and not game.chain:
        S.ock_sel = square
    st.rerun()
