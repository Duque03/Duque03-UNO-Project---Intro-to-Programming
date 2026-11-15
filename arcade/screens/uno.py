"""The UNO table. draw() paints the picture, render() shows it and reacts to clicks."""

from __future__ import annotations

import time

import streamlit as st
from PIL import ImageDraw

from arcade import match, ui
from arcade.art import cards, scenes
from arcade.art.pixel import darken, draw_text, panel, rgb
from arcade.config import BOT_DELAY, SCALE, SCREEN_W
from arcade.logic.uno import COLOURS, NUMBERS, WILD, IllegalMove, card_name
from arcade.screens import common
from arcade.state import S

HAND_Y, PILE_Y, DRAW_X, DISCARD_X = 434, 250, 384, 494
_COLOUR_ORDER = {colour: i for i, colour in enumerate(COLOURS + (WILD,))}
_VALUE_ORDER = {value: i for i, value in enumerate(NUMBERS + ("skip", "reverse", "draw2", "wild", "wild4"))}


def sorted_hand(hand):
    return sorted(hand, key=lambda card: (_COLOUR_ORDER[card[0]], _VALUE_ORDER[card[1]]))


def draw(game, me, opponents, flash="", choosing=False):
    """Returns (picture, clickable regions)."""
    my_turn = game.winner is None and game.current == me
    img = scenes.table_scene("uno", opponents, None if game.winner else game.current)
    d = ImageDraw.Draw(img)
    regions = []
    common.header(img, "UNO")

    # how many cards each opponent holds
    for x, opponent in zip(scenes.seat_positions(len(opponents)), opponents):
        count = len(game.hands[opponent["name"]])
        shown = min(count, 9)
        left = x * SCALE - (shown * 9 + 8) // 2 - 14
        for i in range(shown):
            cards.draw_back(img, left + i * 9, 204, 16, 24)
        draw_text(img, (left + shown * 9 + 16, 216), str(count), 3, "#ffffff", "lm", shadow="#16122b")

    # draw pile, discard pile, colour in play
    cards.draw_back(img, DRAW_X - 5, PILE_Y - 5)
    cards.draw_back(img, DRAW_X, PILE_Y)
    draw_text(img, (DRAW_X + cards.CARD_W // 2, PILE_Y + cards.CARD_H + 10), f"DECK {len(game.deck)}", 1, "#d9d4ff", "mt")
    if my_turn and game.drawn_card is None:
        regions.append(((DRAW_X - 5, PILE_Y - 5, DRAW_X + cards.CARD_W, PILE_Y + cards.CARD_H), ("draw",)))
    cards.draw_card(img, DISCARD_X, PILE_Y, game.top)
    box_x = DISCARD_X + cards.CARD_W + 24
    draw_text(img, (box_x, PILE_Y + 2), "COLOUR", 1, "#d9d4ff", "lt")
    d.rectangle([box_x, PILE_Y + 14, box_x + 39, PILE_Y + 53], fill=(255, 255, 255))
    d.rectangle([box_x + 4, PILE_Y + 18, box_x + 35, PILE_Y + 49], fill=rgb(cards.COLOUR_HEX[game.colour]))
    if not game.winner:
        draw_text(img, (box_x, PILE_Y + 64), "NEXT", 1, "#d9d4ff", "lt")
        draw_text(img, (box_x, PILE_Y + 76), game.next_player(), 2, "#ffffff", "lt", shadow="#16122b")

    common.message(img, game.last_event, 368)
    if flash:
        common.message(img, flash, 392, "#ff8a8a")
    elif my_turn:
        common.message(img, "Your turn: click a glowing card or the deck", 392, "#ffe94a")

    # my hand
    hand = sorted_hand(game.hands[me])
    playable = set(game.playable_cards(me)) if my_turn else set()
    count = len(hand)
    step = min(cards.CARD_W + 6, (860 - cards.CARD_W) / max(1, count - 1))
    left = (SCREEN_W - (step * (count - 1) + cards.CARD_W)) / 2
    for i, card in enumerate(hand):
        x = left + i * step
        ok = card in playable
        y = HAND_Y - (16 if ok else 0)
        cards.draw_card(img, x, y, card, dim=my_turn and not ok, glow=ok)
        right = x + (step if i < count - 1 else cards.CARD_W)
        regions.append(((x, y, right, HAND_Y + cards.CARD_H), ("card", card)))

    if choosing:
        img = darken(img, 0.5)
        d = ImageDraw.Draw(img)
        panel(img, (290, 170, 670, 360), "#fff6da", "#16122b", bw=6)
        draw_text(img, (SCREEN_W // 2, 196), "CHOOSE A COLOUR", 3, "#16122b", "mt")
        regions = [((0, 0, SCREEN_W, 540), ("cancel",))]
        for i, colour in enumerate(COLOURS):
            x = 318 + i * 84
            d.rectangle([x, 246, x + 71, 317], fill=(22, 18, 43))
            d.rectangle([x + 6, 252, x + 65, 311], fill=rgb(cards.COLOUR_HEX[colour]))
            regions.append(((x, 246, x + 71, 317), ("colour", colour)))
    return img, regions


def render() -> None:
    game = S.game
    me = S.player["name"]
    opponents = match.opponents()
    slot = ui.screen()
    bots_were_playing = game.winner is None and game.current != me

    while game.winner is None and game.current != me:  # the bots play, one visible move at a time
        ui.show(slot, draw(game, me, opponents)[0])
        time.sleep(BOT_DELAY)
        game.bot_turn(game.current)

    if game.winner and S.result is None:
        if S.match["mode"] == "champ":
            ui.show(slot, draw(game, me, opponents)[0])
            time.sleep(1.2)
        match.finish([game.winner])
        if S.screen != "uno":
            st.rerun()

    my_turn = game.winner is None
    img, regions = draw(game, me, opponents, S.flash, choosing=S.pending_wild is not None)
    img, regions = common.with_result(img, regions)
    ui.show(slot, img)
    point = None if bots_were_playing else ui.click()  # a click made during the bots' turn does not count
    action = ui.hit(regions, point)

    bar = st.columns([1.4, 1.4, 1.4, 1])
    if S.result:
        common.continue_button(bar[0], "uno", point is not None)
        return
    with bar[0]:
        draw_pressed = ui.button("Draw a card", "uno_draw", "D", disabled=not my_turn or game.drawn_card is not None)
    with bar[1]:
        pass_pressed = ui.button("Pass", "uno_pass", "P", disabled=not my_turn or game.drawn_card is None)
    common.pause_button(bar[3], "uno")

    acted = True
    try:
        if S.pending_wild is not None:
            if action and action[0] == "colour":
                game.play(me, S.pending_wild, action[1])
                S.pending_wild, S.flash = None, ""
            elif action == ("cancel",):
                S.pending_wild = None
            else:
                acted = False
        elif draw_pressed or action == ("draw",):
            card = game.draw(me)
            S.flash = f"You drew {card_name(card)}: play it or pass" if game.drawn_card else ""
        elif pass_pressed:
            game.pass_turn(me)
            S.flash = ""
        elif action and action[0] == "card":
            card = action[1]
            if card[0] == WILD and card in game.playable_cards(me):
                S.pending_wild = card
            else:
                game.play(me, card)
                S.flash = ""
        else:
            acted = False
    except IllegalMove as problem:
        S.flash = str(problem)
    if acted:
        st.rerun()
