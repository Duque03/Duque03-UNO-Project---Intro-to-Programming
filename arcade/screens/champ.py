"""Championship screens: the host's speech, the rules, and the scoreboards."""

from __future__ import annotations

import time

import streamlit as st

from arcade import bots, match, phrases, state, ui
from arcade import player as player_model
from arcade.art import scenes
from arcade.config import CHAMPIONSHIP_PRIZE, GAME_LABELS
from arcade.logic import championship, cursor
from arcade.screens import hub
from arcade.state import S

RULES = [
    "You and 3 bots play UNO, then checkers, then Connect Four.",
    "A win is worth 2 points. A tie is worth 1 point each.",
    "In checkers and Connect Four you face one bot while the other two play each other.",
    f"Finish with the most points to win {CHAMPIONSHIP_PRIZE} coins.",
]


def _backdrop():
    return hub.picture(hint=False)[0]


def render_intro() -> None:
    """The first-time speech, one sentence per press of Enter."""
    lines = phrases.CHAMPIONSHIP_INTRO
    page = S.get("intro_page", 0)
    last = page == len(lines) - 1
    img = scenes.dialog_bubble(_backdrop(), lines[page], page + 1, len(lines), with_coins=(page == 3), footer=not last)
    regions = []
    choices = [{"label": "YES", "action": "yes", "key": "Y", "fill": "#c8f7c5"}, {"label": "NO", "action": "no", "key": "N"}]
    focus = cursor.clamp(S.get("intro_focus"), len(choices))  # the yellow highlight starts on YES
    if last:
        regions = scenes.choice_buttons(img, choices, y=320, focus=focus)
        if not S.player["champ_intro_seen"]:
            S.player["champ_intro_seen"] = True  # from now on the table offers "Start" and "Rules"
            state.save()
    ui.show(ui.screen(), img)
    point = ui.click()
    action = ui.hit(regions, point)

    bar = st.columns([1.4, 1.4, 2.2])
    if not last:
        with bar[0]:
            pressed = ui.button("Next", "intro_next", "Enter", type="primary")
        if pressed or point is not None:
            S.intro_page = page + 1
            st.rerun()
        return
    key = ui.keys("intro", {"Left": "left", "Right": "right", "Enter": "choose"})  # Left / Right, then Enter
    if key in ("left", "right"):
        S.intro_focus = cursor.step(focus, key, len(choices))
        st.rerun()
    if key == "choose":
        action = ("choice", choices[focus]["action"])
    with bar[0]:
        yes = ui.button("Yes", "intro_yes", "Y", type="primary")
    with bar[1]:
        no = ui.button("No", "intro_no", "N")
    if yes or no or action:
        S.intro_focus = None
    if yes or action == ("choice", "yes"):
        match.begin_championship()
        st.rerun()
    if no or action == ("choice", "no"):
        state.go("hub")
        st.rerun()


def render_rules() -> None:
    img = scenes.rules_panel(_backdrop(), RULES)
    ui.show(ui.screen(), img)
    point = ui.click()
    bar = st.columns([1.4, 3.6])
    with bar[0]:
        back = ui.button("Back", "rules_back", "Enter", type="primary")
    if back or point is not None:
        state.go("hub")
        st.rerun()


def _rows(champ) -> list[dict]:
    rows = []
    for name in champ["players"]:
        me = name == champ["me"]
        look = player_model.look(S.player) if me else bots.look(bots.get(name))
        rows.append({"name": name, "look": look, "old": champ["before"][name], "new": champ["points"][name], "me": me})
    return rows


def _round_title(champ) -> tuple[str, str]:
    winners, tied = champ["last_winners"], champ["last_tied"]
    parts = []
    if winners:
        parts.append(("WINNER: " if len(winners) == 1 else "WINNERS: ") + " & ".join(winners))
    if tied:
        parts.append("TIE: " + " & ".join(tied))
    title = parts[0] if parts else "NO WINNER"
    game = championship.ROUNDS[champ["round"] - 1]
    subtitle = f"ROUND {champ['round']} OF 3 - {GAME_LABELS[game]}"
    if len(parts) > 1:
        subtitle += "   " + parts[1] + " (+1 EACH)"
    elif tied:
        subtitle += "   (+1 EACH)"
    return title, subtitle


def render_score() -> None:
    """Standings after a round, with the bars growing to the new totals."""
    champ = S.champ
    title, subtitle = _round_title(champ)
    rows = _rows(champ)
    slot = ui.screen()
    if not S.get("score_animated"):
        ui.play_frames(slot, (scenes.scoreboard(title, rows, championship.MAX_POINTS, k / 8, subtitle)
                              for k in range(0, 9)), 0.06)
        S.score_animated = True
    ui.show(slot, scenes.scoreboard(title, rows, championship.MAX_POINTS, 1.0, subtitle))
    point = ui.click()
    bar = st.columns([1.4, 3.6])
    with bar[0]:
        pressed = ui.button("Continue", "score_next", "Enter", type="primary")
    if pressed or point is not None:
        if championship.is_over(champ):
            S.final_line = None
            state.go("champ_final")
        else:
            match.next_championship_round()
        st.rerun()


def render_final() -> None:
    """The last screen: champion or not, and the prize."""
    champ = S.champ
    won = championship.player_is_champion(champ)
    if not S.get("final_line"):  # pay the prize exactly once
        if won:
            S.player["coins"] += CHAMPIONSHIP_PRIZE
            S.player["championships"] += 1
            state.save()
        S.final_line = state.rng().choice(phrases.CHAMPION_LINES if won else phrases.CHAMPION_LOSE_LINES)
    rows = [dict(row, old=row["new"]) for row in _rows(champ)]
    rows.sort(key=lambda row: -row["new"])
    img = scenes.scoreboard("", rows, championship.MAX_POINTS, 1.0, headline=S.final_line,
                            prize=CHAMPIONSHIP_PRIZE if won else None)
    ui.show(ui.screen(), img)
    point = ui.click()
    bar = st.columns([1.4, 3.6])
    with bar[0]:
        pressed = ui.button("Continue", "final_next", "Enter", type="primary")
    if pressed or point is not None:
        S.champ = None
        S.final_line = None
        match.back_to_hub(centre=True)
        st.rerun()
