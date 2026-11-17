"""The UNO table. draw() paints the picture, render() shows it and reacts to clicks.

Playing several cards (house rule): click a glowing card. If you hold other
cards with the same number or symbol they light up: click them to add them (the
last one you add sets the colour), then press Play (Enter) or click the pile.
A card with no twins is played straight away.

Saying UNO (house rule): when a play leaves you with one card, a big UNO button
appears for UNO_SECONDS; press it (or U) in time, or draw 2.
"""

from __future__ import annotations

import time

import streamlit as st
from PIL import ImageDraw

from arcade import match, sound, ui
from arcade.art import cards, scenes
from arcade.art.pixel import darken, draw_text, key_icon, panel, rgb
from arcade.config import SCALE, SCREEN_W, UNO_BOT_FORGET, UNO_BOT_SMART, UNO_BOT_STACK, UNO_BOT_TWINS
from arcade.logic.uno import COLOURS, NUMBERS, WILD, IllegalMove, card_name
from arcade.screens import common
from arcade.state import S

HAND_Y, PILE_Y, DRAW_X, DISCARD_X = 434, 250, 384, 494
UNO_SECONDS = 2.0  # time to press UNO after going down to one card
UNO_GRACE = 0.35  # the click needs a moment to travel to the server
UNO_BOX = (744, 236, 936, 336)  # where the big UNO button is on the picture
_COLOUR_ORDER = {colour: i for i, colour in enumerate(COLOURS + (WILD,))}
_VALUE_ORDER = {value: i for i, value in enumerate(NUMBERS + ("skip", "reverse", "draw2", "wild", "wild4"))}


def sorted_hand(hand):
    return sorted(hand, key=lambda card: (_COLOUR_ORDER[card[0]], _VALUE_ORDER[card[1]]))


def picked_cards(hand, picks) -> list:
    """The cards chosen so far, in the order they were clicked. picks are positions in the sorted hand."""
    ordered = sorted_hand(hand)
    return [ordered[i] for i in picks if 0 <= i < len(ordered)]


def can_add(hand, picks, index) -> bool:
    """May the card at this position join the cards already picked? (same number or symbol, not picked yet)"""
    ordered = sorted_hand(hand)
    return bool(picks) and index not in picks and 0 <= index < len(ordered) and ordered[index][1] == ordered[picks[0]][1]


def _uno_left() -> float:
    deadline = S.get("uno_deadline")
    return max(0.0, deadline - time.time()) if deadline else 0.0


def draw(game, me, opponents, flash="", choosing=False, picks=(), uno_open=False):
    """Returns (picture, clickable regions)."""
    my_turn = game.winner is None and game.current == me and not uno_open
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
        if count == 1:
            draw_text(img, (x * SCALE, 186), "UNO!", 2, "#ff4f6d", "mm", shadow="#16122b")

    # draw pile, discard pile, colour in play
    cards.draw_back(img, DRAW_X - 5, PILE_Y - 5)
    cards.draw_back(img, DRAW_X, PILE_Y)
    label = f"DRAW {game.pending}!" if game.pending else f"DECK {len(game.deck)}"
    draw_text(img, (DRAW_X + cards.CARD_W // 2, PILE_Y + cards.CARD_H + 8), label, 1,
              "#d9d4ff" if not game.pending else "#ff8a8a", "mt")
    if my_turn and game.drawn_card is None and not picks:
        regions.append(((DRAW_X - 5, PILE_Y - 5, DRAW_X + cards.CARD_W, PILE_Y + cards.CARD_H), ("draw",)))
    for i, card in enumerate(game.discard[-3:-1]):  # the cards just below show when several were played
        cards.draw_card(img, DISCARD_X - 8 + i * 4, PILE_Y - 6 + i * 3, card)
    cards.draw_card(img, DISCARD_X, PILE_Y, game.top)
    if my_turn and picks:
        regions.append(((DISCARD_X, PILE_Y, DISCARD_X + cards.CARD_W, PILE_Y + cards.CARD_H), ("play",)))
    box_x = DISCARD_X + cards.CARD_W + 24
    draw_text(img, (box_x, PILE_Y + 2), "COLOUR", 1, "#d9d4ff", "lt")
    d.rectangle([box_x, PILE_Y + 14, box_x + 39, PILE_Y + 53], fill=(255, 255, 255))
    d.rectangle([box_x + 4, PILE_Y + 18, box_x + 35, PILE_Y + 49], fill=rgb(cards.COLOUR_HEX[game.colour]))
    if not game.winner:
        draw_text(img, (box_x, PILE_Y + 64), "NEXT", 1, "#d9d4ff", "lt")
        draw_text(img, (box_x, PILE_Y + 76), game.next_player(), 2, "#ffffff", "lt", shadow="#16122b")

    common.message(img, game.last_event, 368)
    hand = sorted_hand(game.hands[me])
    if flash:
        common.message(img, flash, 392, "#ff8a8a")
    elif my_turn and picks:
        common.message(img, f"{len(picks)} picked: add more {card_name(('x', hand[picks[0]][1])).split(' ', 1)[-1]} "
                            "or press Play (Enter)", 392, "#ffe94a")
    elif my_turn and game.pending:
        common.message(img, f"Answer with the same draw card or draw {game.pending}", 392, "#ffe94a")
    elif my_turn:
        common.message(img, "Your turn: click a glowing card or the deck", 392, "#ffe94a")

    # my hand
    playable = set(game.playable_cards(me)) if my_turn else set()
    count = len(hand)
    step = min(cards.CARD_W + 6, (860 - cards.CARD_W) / max(1, count - 1))
    left = (SCREEN_W - (step * (count - 1) + cards.CARD_W)) / 2
    for i, card in enumerate(hand):
        x = left + i * step
        picked = i in picks
        ok = can_add(game.hands[me], list(picks), i) if picks else card in playable
        y = HAND_Y - (22 if picked else 12 if ok else 0)
        cards.draw_card(img, x, y, card, dim=my_turn and not (ok or picked), glow=ok or picked)
        if picked:
            order = list(picks).index(i) + 1
            bx, by = x + cards.CARD_W - 26, y + cards.CARD_H - 30  # the order it was picked in, inside the card
            d.ellipse([bx, by, bx + 22, by + 22], fill=(22, 18, 43))
            draw_text(img, (bx + 11, by + 11), str(order), 2, "#ffe94a", "mm")
        right = x + (step if i < count - 1 else cards.CARD_W)
        regions.append(((x, y, right, HAND_Y + cards.CARD_H), ("card", i)))

    if uno_open:  # house rule: say UNO in time
        x0, y0, x1, y1 = UNO_BOX
        panel(img, UNO_BOX, "#ff4f6d", "#16122b", bw=5)
        draw_text(img, ((x0 + x1) // 2, y0 + 30), "UNO!", 5, "#ffffff", "mm", shadow="#16122b")
        key_icon(img, (x0 + x1) // 2 - 12, y0 + 56, "U", 2, "#ffe94a")
        share = _uno_left() / UNO_SECONDS
        d.rectangle([x0 + 14, y1 - 16, x1 - 14, y1 - 10], fill=(22, 18, 43))
        d.rectangle([x0 + 14, y1 - 16, x0 + 14 + int((x1 - x0 - 28) * share), y1 - 10], fill=(255, 233, 74))
        regions.append((UNO_BOX, ("uno",)))

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


@st.fragment(run_every=0.25)
def _uno_clock() -> None:
    """While the UNO button is up, check four times a second whether time ran out."""
    game = S.get("game")
    if S.screen != "uno" or game is None or S.get("uno_deadline") is None:
        return
    if time.time() > S.uno_deadline + UNO_GRACE:
        game.miss_uno(S.player["name"])
        S.uno_deadline = None
        S.flash = "You forgot to say UNO! +2 cards"
        sound.play("lose")
        st.rerun()


def _play(game, me, chosen, colour=None) -> None:
    """Play the chosen cards, or ask for a colour first when the last one is a wild."""
    if chosen[-1][0] == WILD and colour is None:
        S.pending_wild = list(chosen)
        return
    game.play(me, chosen, colour)
    S.uno_pick, S.pending_wild, S.flash = [], None, ""
    if game.uno_due == me:
        S.uno_deadline = time.time() + UNO_SECONDS


def render() -> None:
    game = S.game
    me = S.player["name"]
    opponents = match.opponents()
    picks = [i for i in S.get("uno_pick") or [] if i < len(game.hands[me])]
    if game.uno_due != me:
        S.uno_deadline = None
    uno_open = game.uno_due == me and game.winner is None
    slot = ui.screen()
    bots_were_playing = game.winner is None and game.current != me and not uno_open
    if common.run_clock(not bots_were_playing and game.winner is None and not uno_open):
        S.pending_wild, S.uno_pick = None, []  # 15 seconds went by: draw and pass for the player
        game.auto_turn(me)
        common.restart_clock()
        S.flash = "Time's up! You drew and your turn passed"
        st.rerun()

    while not uno_open and game.winner is None and game.current != me:  # the bots play, one visible move at a time
        common.show(slot, draw(game, me, opponents)[0], "uno")
        common.bot_pause()
        game.bot_turn(game.current, forget_uno=UNO_BOT_FORGET, twins=UNO_BOT_TWINS, stack=UNO_BOT_STACK,
                      smart=UNO_BOT_SMART)

    if game.winner and S.result is None:
        if S.match["mode"] == "champ":
            common.show(slot, draw(game, me, opponents)[0], "uno")
            time.sleep(1.2)
        match.finish([game.winner])
        if S.screen != "uno":
            st.rerun()

    my_turn = game.winner is None and game.current == me and not uno_open
    common.run_clock(my_turn)  # the bots are done: the player's 15 seconds start
    img, regions = draw(game, me, opponents, S.flash, choosing=S.pending_wild is not None, picks=picks,
                        uno_open=uno_open)
    img, regions = common.with_result(img, regions)
    common.show(slot, img, "uno")
    point = None if bots_were_playing else ui.click()  # a click made during the bots' turn does not count
    action = ui.hit(regions, point)
    if uno_open:
        _uno_clock()

    bar = st.columns([1.4, 1.4, 1.4, 1])
    if S.result:
        common.continue_button(bar[0], "uno", point is not None)
        return
    if uno_open:
        with bar[0]:
            uno_pressed = ui.button("UNO!", "uno_call", "U", type="primary")
        common.pause_button(bar[3], "uno")
        if uno_pressed or action == ("uno",):
            if time.time() <= S.uno_deadline + UNO_GRACE:
                game.call_uno(me)
                sound.play("coin")
            else:
                game.miss_uno(me)
                S.flash = "Too late! +2 cards"
            S.uno_deadline = None
            st.rerun()
        return
    with bar[0]:
        draw_label = f"Draw {game.pending} cards" if game.pending else "Draw a card"
        draw_pressed = ui.button(draw_label, "uno_draw", "D", disabled=not my_turn or game.drawn_card is not None or bool(picks))
    with bar[1]:
        if picks:
            play_pressed = ui.button(f"Play {len(picks)} card{'s' if len(picks) > 1 else ''}", "uno_play", "Enter",
                                     type="primary", disabled=not my_turn)
            pass_pressed = False
        else:
            play_pressed = False
            pass_pressed = ui.button("Pass", "uno_pass", "P", disabled=not my_turn or game.drawn_card is None)
    cancel_pressed = False
    if picks:
        with bar[2]:
            cancel_pressed = ui.button("Cancel", "uno_cancel", "X")  # (Streamlit keeps C and R for itself)
    else:
        common.rules_button(bar[2], "uno")
    common.pause_button(bar[3], "uno")

    acted = True
    try:
        if S.pending_wild is not None:
            if action and action[0] == "colour":
                _play(game, me, S.pending_wild, action[1])
            elif action == ("cancel",):
                S.pending_wild = None
            else:
                acted = False
        elif cancel_pressed:
            S.uno_pick = []
        elif play_pressed or (action == ("play",) and picks):
            _play(game, me, picked_cards(game.hands[me], picks))
        elif draw_pressed or action == ("draw",):
            drawn = game.draw(me)
            S.uno_pick = []
            common.restart_clock()  # 15 new seconds to play the drawn card or pass
            if game.drawn_card:
                many = f"{len(drawn)} cards" if len(drawn) > 1 else "a card"
                S.flash = f"You drew {many}: play the {card_name(game.drawn_card)} or pass"
            else:
                S.flash = ""
        elif pass_pressed:
            game.pass_turn(me)
            S.flash = ""
        elif action and action[0] == "card" and my_turn:
            index = action[1]
            hand = sorted_hand(game.hands[me])
            card = hand[index]
            if index in picks:  # click a picked card again: take it (and the ones after it) back
                S.uno_pick = picks[:picks.index(index)]
            elif picks and can_add(game.hands[me], picks, index):
                S.uno_pick = picks + [index]
            elif card in game.playable_cards(me):
                twins = game.partners(me, card) if game.drawn_card is None or card == game.drawn_card else []
                if twins:
                    S.uno_pick = [index]  # it has twins: let the player pick them too
                else:
                    _play(game, me, [card])
            else:
                S.flash = "That card cannot start a play now"
        else:
            acted = False
    except IllegalMove as problem:
        S.flash = str(problem)
        S.uno_pick = []
    if acted:
        st.rerun()
