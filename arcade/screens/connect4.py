"""The Connect Four table. draw() paints the picture, render() shows it and reacts to clicks."""

from __future__ import annotations

import time

import streamlit as st
from PIL import ImageDraw

from arcade import bots, match, state, ui
from arcade.art import scenes
from arcade.art.pixel import draw_text, panel
from arcade.config import CONNECT4_LEVELS, SCREEN_W
from arcade.logic import cursor
from arcade.logic.connect4 import COLS, DRAW, RED, ROWS, YELLOW, IllegalMove
from arcade.screens import common
from arcade.state import S

CELL = 46
BOARD_X = (SCREEN_W - COLS * CELL) // 2
BOARD_Y = 234
_DISC = {RED: ((226, 65, 60), (255, 150, 140)), YELLOW: ((242, 194, 48), (255, 236, 150))}


def draw(game, opponent, flash="", falling=None, column=None, me=RED):
    """Returns (picture, regions). falling=(row, col) draws the last disc higher up while it drops.

    column: the column the arrow keys are on (a yellow frame and a bigger arrow), or None.
    me: the side of the player looking at the screen (online, the second player is yellow).
    """
    my_turn = game.winner is None and game.turn == me
    img = scenes.table_scene("connect4", [opponent], opponent["name"] if game.winner is None and not my_turn else None)
    d = ImageDraw.Draw(img)
    regions = []

    width, height = COLS * CELL, ROWS * CELL
    d.rectangle([BOARD_X - 12, BOARD_Y - 10, BOARD_X + width + 11, BOARD_Y + height + 9], fill=(20, 40, 120))
    d.rectangle([BOARD_X - 8, BOARD_Y - 6, BOARD_X + width + 7, BOARD_Y + height + 5], fill=(47, 111, 224))
    d.rectangle([BOARD_X - 8, BOARD_Y - 6, BOARD_X + width + 7, BOARD_Y - 3], fill=(120, 170, 255))
    d.rectangle([BOARD_X - 20, BOARD_Y + height + 9, BOARD_X + 10, BOARD_Y + height + 17], fill=(20, 40, 120))
    d.rectangle([BOARD_X + width - 11, BOARD_Y + height + 9, BOARD_X + width + 19, BOARD_Y + height + 17], fill=(20, 40, 120))
    for row in range(ROWS):
        for col in range(COLS):
            x, y = BOARD_X + col * CELL, BOARD_Y + row * CELL
            side = game.board[row][col]
            if falling and game.last == (row, col):
                side = None  # the disc has not arrived yet
            if falling and falling == (row, col):
                side = game.board[game.last[0]][game.last[1]]
            if side:
                fill, light = _DISC[side]
                d.ellipse([x + 5, y + 5, x + CELL - 6, y + CELL - 6], fill=fill, outline=(16, 12, 34), width=2)
                d.ellipse([x + 12, y + 12, x + CELL - 13, y + CELL - 13], outline=light, width=2)
            else:
                d.ellipse([x + 5, y + 5, x + CELL - 6, y + CELL - 6], fill=(18, 14, 40), outline=(16, 32, 100), width=2)
            if (row, col) in game.win_cells and not falling:
                d.ellipse([x + 2, y + 2, x + CELL - 3, y + CELL - 3], outline=(255, 255, 255), width=4)
    if my_turn:
        for col in game.legal_columns():
            x = BOARD_X + col * CELL
            draw_text(img, (x + CELL // 2, BOARD_Y - 14), "V", 3 if col == column else 2, "#ffe94a", "mb",
                      shadow="#16122b")
            regions.append(((x, BOARD_Y - 34, x + CELL - 1, BOARD_Y + height), ("col", col)))
        if column is not None:  # the yellow frame the arrow keys move (also on a full column: Space is refused there)
            x = BOARD_X + column * CELL
            d.rectangle([x + 1, BOARD_Y - 4, x + CELL - 2, BOARD_Y + height + 3], outline=scenes.FOCUS, width=3)

    them = YELLOW if me == RED else RED
    for x0, side, label in ((30, me, "YOU"), (SCREEN_W - 290, them, opponent["name"])):
        edge, light = ("#e2413c", "#ff9a94") if side == RED else ("#f2c230", "#ffe9a0")
        panel(img, (x0, 250, x0 + 260, 322), "#16122b", edge, shadow=False)
        draw_text(img, (x0 + 18, 268), label, 2, light, "lt")
        draw_text(img, (x0 + 18, 292), side.upper(), 3, "#ffffff", "lt")
    if flash:
        draw_text(img, (160, 350), flash.upper(), 2, "#ff8a8a", "mt", shadow="#16122b")
    elif my_turn:  # how to play is in the rules (I), not on the table
        draw_text(img, (160, 350), "YOUR TURN", 2, "#ffe94a", "mt", shadow="#16122b")
    return img, regions


def render() -> None:
    game = S.game
    me = S.player["name"]
    opponent = match.opponents()[0]
    slot = ui.screen()
    bot_was_playing = game.winner is None and game.turn == YELLOW
    # The keys come first, on every run, and are read before drawing (see uno.py). Left / Right move the frame;
    # Space, Enter or Down drop the disc there; 1-7 drop straight into a column. Only on the player's turn.
    keys = {"Left": "left", "Right": "right", "Space": "space", "Enter": "enter", "Down": "down"}
    keys.update({str(col + 1): f"col{col + 1}" for col in range(COLS)})
    key = ui.keys("connect4", keys)
    if bot_was_playing:
        key = None
    if common.run_clock(game.winner is None and game.turn == RED):
        game.random_move(state.rng())  # 15 seconds went by: a random column for the player
        common.restart_clock()
        S.flash = "Time's up! A random move was played"
        st.rerun()

    if game.winner is None and game.turn == YELLOW:
        common.show(slot, common.thinking(draw(game, opponent)[0], 0, 1), "connect4")
        started = time.time()
        game.bot_move(state.rng(), **CONNECT4_LEVELS[bots.level(opponent["name"])])
        common.bot_pause(since=started)

    if game.winner and S.result is None:
        if S.match["mode"] == "champ":
            common.show(slot, draw(game, opponent)[0], "connect4")
            time.sleep(1.2)
        if game.winner == DRAW:
            match.finish([me, opponent["name"]], tied=True)
        else:
            match.finish([me if game.winner == RED else opponent["name"]])
        if S.screen != "connect4":
            st.rerun()
        common.podium_now(slot, draw(game, opponent)[0])  # the winner (and the loser) on the podium

    my_turn = game.winner is None and game.turn == RED
    common.run_clock(my_turn)  # the bot is done: the player's 15 seconds start
    if not my_turn:
        key = None
    column = cursor.clamp(S.get("c4_column", COLS // 2), COLS) if my_turn else None  # starts in the middle
    if key in ("left", "right"):
        column = S.c4_column = cursor.step(column, key, COLS, wrap=False)
    img, regions = draw(game, opponent, S.flash, column=column)
    if not S.result:
        regions += common.corner_buttons(img)  # RULES and PAUSE on the picture (no bar of buttons)
    img, regions = common.with_result(img, regions)
    common.show(slot, img, "connect4")
    point = None if bot_was_playing else ui.click()  # a click made during the bot's turn does not count
    action = ui.hit(regions, point)

    bar = ui.bar("connect4", [1.4, 1.4, 1.4, 1])  # invisible: only the keys (everything is on the picture)
    if S.result:
        common.result_buttons(bar, "connect4", action)  # Continue, or Play again
        return
    common.rules_button(bar[2], "connect4")
    common.pause_button(bar[3], "connect4")
    common.corner_action(action, "connect4")

    if key in ("space", "enter", "down"):
        action = ("col", column)
    elif key and key.startswith("col"):
        action = ("col", int(key[3:]) - 1)

    if action and action[0] == "col" and game.winner is None and game.turn == RED:
        S.c4_column = action[1]  # the frame follows a click or a number too
        try:
            game.drop(action[1])
            S.flash = ""
        except IllegalMove as problem:
            S.flash = str(problem)
        st.rerun()
