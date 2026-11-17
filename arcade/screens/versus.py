"""Choose your opponents (Miguel's idea): opens when the player presses E at a table.

Each bot has a level (easy, medium, hard, expert) and pays that level's coins. Checkers and Connect Four:
pick one bot. UNO: pick three; the prize is the average of their three levels.
"""

from __future__ import annotations

import streamlit as st

from arcade import bots, catalog, match, sound, state, ui
from arcade.art import versus
from arcade.config import BOTS_PER_GAME, GAME_LABELS
from arcade.logic import levels
from arcade.state import S


def open_for(game: str) -> None:
    """Show the picker for this table (the room picture stays behind it: hub._remember_still)."""
    S.versus = {"game": game, "picked": []}
    state.go("versus")


def _cards() -> list[dict]:
    return [{"name": b["name"], "level": b["level"], "look": bots.look(b), "tag": catalog.spec_for("name", b["tag"])}
            for b in bots.BOTS]


def render() -> None:
    choice = S.versus
    game, picked = choice["game"], choice["picked"]
    needed = BOTS_PER_GAME[game]
    ready = len(picked) == needed
    prize = levels.win_coins([bots.level(name) for name in picked]) if ready else None
    title = f"{GAME_LABELS[game]}: CHOOSE {'YOUR OPPONENT' if needed == 1 else f'{needed} OPPONENTS'}"
    img, regions = versus.panel_picture(S.get("_last_frame"), title, _cards(), picked, needed, prize)
    ui.show(ui.screen(), img)
    action = ui.hit(regions, ui.click())

    bar = st.columns([1] * len(bots.BOTS) + [1.6, 1.2])
    clicked = action[1] if action and action[0] == "pick" else None
    for i, (column, bot) in enumerate(zip(bar, bots.BOTS)):
        with column:
            if ui.button(bot["name"].title(), f"versus_{bot['name']}", str(i + 1),
                         type="primary" if bot["name"] in picked else "secondary"):
                clicked = bot["name"]
    with bar[-2]:
        play = ui.button("Play", "versus_play", "Enter", type="primary", disabled=not ready)
    with bar[-1]:
        back = ui.button("Back", "versus_back", "Esc")

    if clicked:
        choice["picked"] = levels.toggle(picked, clicked, needed)
        sound.play("blip")
        st.rerun()
    if play and ready:
        sound.play("table")
        match.begin_free_play(game, picked)  # back in the room: everyone walks to the table
        st.rerun()
    if back:
        state.go("hub")
        st.rerun()
