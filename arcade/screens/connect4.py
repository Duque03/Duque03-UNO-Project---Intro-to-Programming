"""The Connect Four table. draw() paints the picture, render() shows it and reacts to clicks."""

from __future__ import annotations

import time

import streamlit as st
from PIL import ImageDraw

from arcade import bots, match, state, ui
from arcade.art import scenes
from arcade.art.pixel import draw_text, panel
from arcade.config import CONNECT4_LEVELS, SCREEN_W
from arcade.logic.connect4 import COLS, DRAW, RED, ROWS, YELLOW, IllegalMove
from arcade.screens import common
from arcade.state import S

CELL = 46
BOARD_X = (SCREEN_W - COLS * CELL) // 2
BOARD_Y = 234
_DISC = {RED: ((226, 65, 60), (255, 150, 140)), YELLOW: ((242, 194, 48), (255, 236, 150))}


def draw(game, opponent, flash="", falling=None):
    """Returns (picture, regions). falling=(row, col) draws the last disc higher up while it drops."""
    my_turn = game.winner is None and game.turn == RED
    img = scenes.table_scene("connect4", [opponent], opponent["name"] if game.winner is None and not my_turn else None)
    d = ImageDraw.Draw(img)
    regions = []
    common.header(img, "CONNECT FOUR")

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
            draw_text(img, (x + CELL // 2, BOARD_Y - 14), "V", 2, "#ffe94a", "mb", shadow="#16122b")
            regions.append(((x, BOARD_Y - 34, x + CELL - 1, BOARD_Y + height), ("col", col)))

    panel(img, (30, 250, 290, 322), "#16122b", "#e2413c", shadow=False)
    draw_text(img, (48, 268), "YOU", 2, "#ff9a94", "lt")
    draw_text(img, (48, 292), "RED", 3, "#ffffff", "lt")
    panel(img, (SCREEN_W - 290, 250, SCREEN_W - 30, 322), "#16122b", "#f2c230", shadow=False)
    draw_text(img, (SCREEN_W - 272, 268), opponent["name"], 2, "#ffe9a0", "lt")
    draw_text(img, (SCREEN_W - 272, 292), "YELLOW", 3, "#ffffff", "lt")
    if flash:
        draw_text(img, (160, 350), flash.upper(), 2, "#ff8a8a", "mt", shadow="#16122b")
    elif my_turn:
        draw_text(img, (160, 350), "YOUR TURN:", 2, "#ffe94a", "mt", shadow="#16122b")
        draw_text(img, (160, 372), "CLICK A COLUMN", 2, "#ffe94a", "mt", shadow="#16122b")
    for i, line in enumerate(("FOUR IN A ROW", "WINS. A FULL", "BOARD IS A TIE.")):
        draw_text(img, (SCREEN_W - 160, 350 + i * 22), line, 2, "#d9d4ff", "mt", shadow="#16122b")
    return img, regions


def render() -> None:
    game = S.game
    me = S.player["name"]
    opponent = match.opponents()[0]
    slot = ui.screen()
    bot_was_playing = game.winner is None and game.turn == YELLOW
    if common.run_clock(game.winner is None and game.turn == RED):
        game.random_move(state.rng())  # 15 seconds went by: a random column for the player
        common.restart_clock()
        S.flash = "Time's up! A random move was played"
        st.rerun()

    if game.winner is None and game.turn == YELLOW:
        common.show(slot, common.thinking(draw(game, opponent)[0], 0, 1), "connect4")
        started = time.time()
        game.bot_move(state.rng(), *CONNECT4_LEVELS[bots.level(opponent["name"])])
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

    common.run_clock(game.winner is None and game.turn == RED)  # the bot is done: the player's 15 seconds start
    img, regions = draw(game, opponent, S.flash)
    img, regions = common.with_result(img, regions)
    common.show(slot, img, "connect4")
    point = None if bot_was_playing else ui.click()  # a click made during the bot's turn does not count
    action = ui.hit(regions, point)

    bar = st.columns([1.4, 1.4, 1.4, 1])
    if S.result:
        common.result_buttons(bar, "connect4", action)  # Continue, or Play again
        return
    common.rules_button(bar[2], "connect4")
    common.pause_button(bar[3], "connect4")

    if action and action[0] == "col" and game.winner is None and game.turn == RED:
        try:
            game.drop(action[1])
            S.flash = ""
        except IllegalMove as problem:
            S.flash = str(problem)
        st.rerun()
