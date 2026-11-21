"""The checkers table. draw() paints the picture, render() shows it and reacts to clicks."""

from __future__ import annotations

import time

import streamlit as st
from PIL import ImageDraw

from arcade import bots, match, state, ui
from arcade.art import scenes
from arcade.art.pixel import draw_text, panel
from arcade.config import CHECKERS_LEVELS, SCREEN_W
from arcade.logic import cursor
from arcade.logic.checkers import BOTTOM, DRAW, SIZE, TOP, IllegalMove, owner
from arcade.screens import common
from arcade.state import S

CELL = 38
BOARD_X = (SCREEN_W - SIZE * CELL) // 2
BOARD_Y = 222
CURSOR = (58, 214, 255)  # the keyboard cursor is blue: on this board yellow already marks the pieces you can move


def _piece(d, img, x, y, piece):
    red = owner(piece) == BOTTOM
    body, rim, dark = ((226, 65, 60), (255, 150, 140), (130, 30, 30)) if red else ((48, 46, 62), (130, 128, 150), (16, 14, 26))
    d.ellipse([x + 5, y + 7, x + CELL - 4, y + CELL - 2], fill=dark)
    d.ellipse([x + 4, y + 3, x + CELL - 5, y + CELL - 6], fill=body, outline=rim, width=2)
    d.ellipse([x + 10, y + 9, x + CELL - 11, y + CELL - 12], outline=rim)
    if piece.isupper():
        draw_text(img, (x + CELL // 2, y + CELL // 2 - 1), "K", 2, "#ffe94a", "mm", shadow="#16122b")


def draw(game, opponent, selected=None, flash="", cursor_cell=None, me=BOTTOM):
    """Returns (picture, clickable regions).

    cursor_cell: the square the arrow keys are on (a blue frame: yellow already marks the pieces), or None.
    me: the side of the player looking at the screen. Online, the second player plays the black (top) pieces and
    sees the board turned round, so their pieces are at the bottom too. Squares and regions stay board squares.
    """
    my_turn = game.winner is None and game.turn == me
    turned = me == TOP

    def at(row, col):  # where a board square is drawn
        return (SIZE - 1 - row, SIZE - 1 - col) if turned else (row, col)
    img = scenes.table_scene("checkers", [opponent], opponent["name"] if game.winner is None and not my_turn else None)
    d = ImageDraw.Draw(img)
    regions = []

    size = SIZE * CELL
    d.rectangle([BOARD_X - 10, BOARD_Y - 10, BOARD_X + size + 9, BOARD_Y + size + 9], fill=(52, 32, 18))
    d.rectangle([BOARD_X - 6, BOARD_Y - 6, BOARD_X + size + 5, BOARD_Y + size + 5], fill=(110, 72, 40))
    legal = game.legal_moves() if my_turn else []
    movable = {move[0] for move in legal}
    targets = {move[1] for move in legal if move[0] == selected}
    recent = set(game.last_move[:2]) if game.last_move else set()
    for row in range(SIZE):
        for col in range(SIZE):
            shown_row, shown_col = at(row, col)
            x, y = BOARD_X + shown_col * CELL, BOARD_Y + shown_row * CELL
            dark_square = (row + col) % 2 == 1
            colour = (86, 120, 70) if dark_square else (236, 224, 190)
            if dark_square and (row, col) in recent:
                colour = (120, 150, 80)
            d.rectangle([x, y, x + CELL - 1, y + CELL - 1], fill=colour)
            if not dark_square:
                continue
            piece = game.board[row][col]
            if piece:
                _piece(d, img, x, y, piece)
            if (row, col) == selected:
                d.rectangle([x, y, x + CELL - 1, y + CELL - 1], outline=(255, 233, 74), width=3)
            elif (row, col) in movable and selected is None:
                for cx, cy in ((x + 1, y + 1), (x + CELL - 7, y + 1), (x + 1, y + CELL - 7), (x + CELL - 7, y + CELL - 7)):
                    d.rectangle([cx, cy, cx + 5, cy + 5], fill=(255, 233, 74))
            if (row, col) in targets:
                d.rectangle([x + 13, y + 13, x + CELL - 14, y + CELL - 14], fill=(124, 255, 58))
                d.rectangle([x, y, x + CELL - 1, y + CELL - 1], outline=(124, 255, 58), width=3)
            regions.append(((x, y, x + CELL - 1, y + CELL - 1), ("cell", row, col)))
    if cursor_cell is not None:  # the keyboard cursor, on top of everything on the board
        shown_row, shown_col = at(*cursor_cell)
        x, y = BOARD_X + shown_col * CELL, BOARD_Y + shown_row * CELL
        d.rectangle([x - 3, y - 3, x + CELL + 2, y + CELL + 2], outline=CURSOR, width=4)

    # score cards left and right of the board
    them = BOTTOM if turned else TOP
    for x0, side, label in ((30, me, "YOU"), (SCREEN_W - 290, them, opponent["name"])):
        red = side == BOTTOM
        panel(img, (x0, 250, x0 + 260, 344), "#16122b", "#e2413c" if red else "#8d8fa3", shadow=False)
        draw_text(img, (x0 + 18, 268), f"{label} - {'RED' if red else 'BLACK'}", 2, "#ff9a94" if red else "#c9ccd6", "lt")
        draw_text(img, (x0 + 18, 298), f"{game.count(side)} PIECES", 3, "#ffffff", "lt")

    hint = ""
    if flash:
        hint, colour = flash, "#ff8a8a"
    elif my_turn:
        capture = any(move[2] for move in legal)
        if game.chain:  # what is happening, not how to play (that is in the rules, I)
            hint = "Keep jumping!"
        else:
            hint = "You must capture" if capture else "Your turn"
        colour = "#ffe94a"
    if hint:
        common.side_message(img, hint, colour)
    return img, regions


def render() -> None:
    game = S.game
    me = S.player["name"]
    opponent = match.opponents()[0]
    slot = ui.screen()
    bot_was_playing = game.winner is None and game.turn == TOP
    # The keys come first, on every run, and are read before drawing (see uno.py). The arrow keys move the cursor one
    # square; Space or Enter is a click on that square. They only count on the player's turn, like a click.
    key = ui.keys("checkers", {**ui.ARROWS, "Space": "space", "Enter": "enter"})
    if S.pop("starter_intro", False):  # a new game: the roulette shows who starts
        common.play_starter(slot, draw(game, opponent)[0], game.turn == BOTTOM, opponent["name"], "checkers")
    if bot_was_playing:
        key = None
    if common.run_clock(game.winner is None and game.turn == BOTTOM):
        while game.winner is None and game.turn == BOTTOM:  # 15 seconds went by: random moves (every jump)
            game.random_move(state.rng())
        common.restart_clock()
        S.selected, S.flash = None, "Time's up! A random move was played"
        st.rerun()

    settings = CHECKERS_LEVELS[bots.level(opponent["name"])]
    first_jump = True
    while game.winner is None and game.turn == TOP:  # bot moves (each jump is shown)
        picture = draw(game, opponent)[0]
        common.show(slot, common.thinking(picture, 0, 1) if first_jump else picture, "checkers")
        started = time.time()
        game.bot_move(state.rng(), **settings)
        if first_jump:
            common.bot_pause(since=started)  # it thinks before its move, then jumps on quickly
        else:
            time.sleep(0.6)
        first_jump = False

    if game.winner and S.result is None:
        if S.match["mode"] == "champ":
            common.show(slot, draw(game, opponent)[0], "checkers")
            time.sleep(1.2)
        if game.winner == DRAW:
            match.finish([me, opponent["name"]], tied=True)
        else:
            match.finish([me if game.winner == BOTTOM else opponent["name"]])
        if S.screen != "checkers":
            st.rerun()
        common.podium_now(slot, draw(game, opponent)[0])  # the winner (and the loser) on the podium

    my_turn = game.winner is None and game.turn == BOTTOM
    common.run_clock(my_turn)  # the bot is done: the player's 15 seconds start
    if not my_turn:
        key = None
    if game.chain:
        S.selected = game.chain
    here = None  # the keyboard cursor: it starts on a piece that can move
    if my_turn:
        here = S.get("checkers_cursor")
        if here is None:
            movable = sorted({move[0] for move in game.legal_moves()})
            here = S.selected or (movable[0] if movable else (SIZE - 1, 0))
        if key in cursor.BOARD_KEYS:
            here = cursor.on_board(here, key, SIZE, SIZE)
        here = S.checkers_cursor = tuple(here)
    img, regions = draw(game, opponent, S.selected, S.flash, cursor_cell=here)
    if not S.result:
        regions += common.corner_buttons(img)  # RULES and PAUSE on the picture (no bar of buttons)
    img, regions = common.with_result(img, regions)
    common.show(slot, img, "checkers")
    point = None if bot_was_playing else ui.click()  # a click made during the bot's turn does not count
    action = ui.hit(regions, point)

    bar = ui.bar("checkers", [1.4, 1.4, 1.4, 1])  # invisible: only the keys (everything is on the picture)
    if S.result:
        common.result_buttons(bar, "checkers", action)  # Continue, or Play again
        return
    common.rules_button(bar[2], "checkers")
    common.pause_button(bar[3], "checkers")
    common.corner_action(action, "checkers")

    if key in ("space", "enter"):  # a click on the square the cursor is on
        action = ("cell", *here)

    if not action or game.winner or game.turn != BOTTOM:
        return
    square = (action[1], action[2])
    S.checkers_cursor = square  # the cursor follows a click too
    try:
        if S.selected and square in {move[1] for move in game.moves_from(S.selected)}:
            game.move(S.selected, square)
            S.selected, S.flash = game.chain, ""
            if game.chain:
                common.restart_clock()  # 15 new seconds for the next jump
        elif game.moves_from(square):
            S.selected, S.flash = square, ""
        elif owner(game.board[square[0]][square[1]]) == BOTTOM:
            must_capture = any(move[2] for move in game.legal_moves())
            S.flash = "You must capture with another piece" if must_capture else "That piece cannot move"
        elif S.selected and not game.chain:
            game.move(S.selected, square)  # not legal: raises the right message
    except IllegalMove as problem:
        S.flash = str(problem)
    st.rerun()
