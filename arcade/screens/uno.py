"""The UNO table. draw() paints the picture, render() shows it and reacts to clicks.

Playing several cards (house rule): click a glowing card. If you hold other
cards with the same number or symbol they light up: click them to add them (the
last one you add sets the colour), then press Play (Enter) or click the pile.
A card with no twins is played straight away.

Saying UNO (house rule): when a play leaves you with one card, a big UNO button
appears for UNO_SECONDS; press it (or U) in time, or draw 2.
"""

from __future__ import annotations

import copy
import time

import streamlit as st
from PIL import ImageDraw

from arcade import bots, catalog, match, player, sound, table_anim, ui
from arcade.art import cards, scenes
from arcade.art.pixel import darken, draw_text, key_icon, panel, rgb
from arcade.config import SCREEN_H, SCREEN_W, UNO_LEVELS
from arcade.logic import cursor
from arcade.logic.uno import COLOURS, NUMBERS, WILD, IllegalMove, card_name, changes, ordinal
from arcade.screens import common, corta
from arcade.state import S

FOCUS = scenes.FOCUS  # the yellow frame the arrow keys move
HAND_Y, PILE_Y, DRAW_X, DISCARD_X = 434, 286, 384, 494
UNO_SECONDS = 2.0  # time to press UNO after going down to one card
UNO_GRACE = 0.35  # the click needs a moment to travel to the server
UNO_BOX = (748, 330, 940, 420)  # where the big UNO button is on the picture
PICK_LIFT = 36  # how far a picked card stands up out of the hand
PASS_BOX = (270, 300, 360, 334)  # the PASS button, left of the deck (only after drawing)
# Animations (milliseconds): the deal, then the roulette that shows who starts; cards drawn and played during the game
DEAL_GAP, DEAL_FLIGHT, SPIN_MS, LABEL_MS = 90, 300, 2400, 1300
MOVE_GAP, MOVE_FLIGHT = 280, 420
PILE_H = round(cards.CARD_H * cards.LYING)  # the piles lie flat on the table
DECK, PILE = (DRAW_X, PILE_Y), (DISCARD_X, PILE_Y)
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


def _my_hands():
    """The signed-in player's skin and shirt colour, for their hands at the bottom of the table."""
    try:
        me = S.get("player")
    except Exception:  # (drawn outside the app, from a script)
        return None
    if not me:
        return None
    skin, _, _, shirt = player.look(me)
    return skin, catalog.spec_for("shirt", shirt).get("c1", "#3a78e8")


def _draw_hands(img, count: int, hands) -> None:
    """The player's hands at the two ends of a row of `count` cards (the thumbs just cover the outer edges)."""
    left, step = hand_layout(max(count, 1))
    width, u = step * (max(count, 1) - 1) + cards.CARD_W, cards.HAND_UNIT
    cards.draw_holding_hand(img, round(left) + 7 - 8 * u, HAND_Y + 34, *hands)
    cards.draw_holding_hand(img, round(left + width) - 7 - 2 * u, HAND_Y + 34, *hands, right=True)


def hand_layout(count: int) -> tuple[float, float]:
    """Where the player's hand starts (x of the first card) and the distance between two cards."""
    step = min(cards.CARD_W + 6, (860 - cards.CARD_W) / max(1, count - 1))
    return (SCREEN_W - (step * (count - 1) + cards.CARD_W)) / 2, step


def _uno_left() -> float:
    deadline = S.get("uno_deadline")
    return max(0.0, deadline - time.time()) if deadline else 0.0


def draw(game, me, opponents, flash="", choosing=False, picks=(), uno_open=False, focus=None, colour_focus=None,
         hide=(), dealing=False, cut_open=False, hands="me"):
    """Returns (picture, clickable regions).

    focus: the card of the hand (position in the sorted hand) the arrow keys are on; colour_focus: the colour
    (position in COLOURS) while choosing a wild's colour. Both get a yellow frame; None draws none.
    For the animations (see deal_plan and move_plan): hide leaves out these cards of the hand (they are flying);
    dealing draws the table before the cards are dealt (no hands, no pile, nobody's turn yet).
    cut_open shows the CORTA UNO! button (someone else is down to one card and has not said UNO yet).
    hands: (skin, sleeve colour) for the player's own hands holding the cards (first person); "me" takes them from
    the signed-in player; None draws no hands.
    """
    if hands == "me":
        hands = _my_hands()
    my_turn = game.winner is None and game.current == me and not uno_open and not dealing
    img = scenes.table_scene("uno", opponents, None if game.winner or dealing else game.current)
    d = ImageDraw.Draw(img)
    regions = []

    # each opponent holds their cards in a fan, with how many there are on the table in front of them
    for seat, opponent in zip(scenes.table_seats(len(opponents)), opponents):
        if dealing:
            break
        spots, (lx, ly) = fan_layout(seat, len(game.hands[opponent["name"]]))
        if opponent["name"] in game.out:  # finished: their place instead of their cards
            place = ordinal(game.out.index(opponent["name"]) + 1).upper()
            draw_text(img, (lx, ly - 30), f"{place}!", 4, "#ffe94a", "mm", shadow="#16122b")
            continue
        count = len(game.hands[opponent["name"]])
        w, h = fan_size(seat)
        for x, y in spots:
            cards.draw_back(img, x, y, w, h)
        draw_text(img, (lx, ly), str(count), 3, "#ffffff", "mt", shadow="#16122b")
        if count == 1:
            draw_text(img, (lx, spots[0][1] - 18), "UNO!", 2, "#ff4f6d", "mm", shadow="#16122b")

    # the draw pile and the discard pile, lying on the table
    for layer in (2, 1, 0):
        cards.draw_lying_back(img, DRAW_X - layer * 2, PILE_Y - layer * 3)
    if game.pending:
        draw_text(img, (DRAW_X + cards.CARD_W // 2, PILE_Y - 26), f"DRAW {game.pending}!", 2, "#ff8a8a", "mm",
                  shadow="#16122b")
    if my_turn and game.can_draw(me):
        regions.append(((DRAW_X - 4, PILE_Y - 6, DRAW_X + cards.CARD_W, PILE_Y + PILE_H), ("draw",)))
    if my_turn and game.draws and not game.pending:  # after drawing, the player may pass
        box = PASS_BOX
        panel(img, box, "#1c1642", "#ffe94a", bw=3, shadow=False)
        draw_text(img, ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2), "PASS", 2, "#ffe94a", "mm")
        regions.append((box, ("pass",)))
    if dealing:  # nothing on the table yet but the deck (and the player's empty hands, ready for the cards)
        if hands:
            _draw_hands(img, len(game.hands[me]), hands)
        return img, regions
    if game.top[0] == WILD:  # the colour chosen for a wild: the pile glows in that colour
        glow = rgb(cards.COLOUR_HEX[game.colour])
        for grow, strength in ((18, 0.4), (11, 0.75), (6, 1.0)):
            colour = tuple(round(c * strength + f * (1 - strength)) for c, f in zip(glow, rgb(scenes.FELT["uno"])))
            d.rounded_rectangle([DISCARD_X - grow, PILE_Y - grow, DISCARD_X + cards.CARD_W + grow,
                                 PILE_Y + PILE_H + grow], radius=grow + 4, fill=colour)
    for i, card in enumerate(game.discard[-3:-1]):  # the cards just below show when several were played
        cards.draw_lying_card(img, DISCARD_X - 8 + i * 4, PILE_Y - 4 + i * 2, card)
    cards.draw_lying_card(img, DISCARD_X, PILE_Y, game.top)
    if my_turn:  # the picked cards go down when the pile is clicked (with nothing picked, nothing happens)
        regions.append(((DISCARD_X - 8, PILE_Y - 6, DISCARD_X + cards.CARD_W, PILE_Y + PILE_H), ("play",)))
    if not game.winner:
        box_x = DISCARD_X + cards.CARD_W + 26
        draw_text(img, (box_x, PILE_Y + 8), "NEXT", 1, "#d9d4ff", "lt", shadow="#16122b")
        draw_text(img, (box_x, PILE_Y + 20), game.next_player(), 2, "#ffffff", "lt", shadow="#16122b")

    hand = sorted_hand(game.hands[me])
    if flash:  # only what just happened; how to play is in the rules (I)
        common.message(img, flash, 372, "#ff8a8a")

    # my hand: nothing glows; a picked card stands up a little
    count = len(hand)
    left, step = hand_layout(count)
    for i, card in enumerate(hand):
        x = left + i * step
        picked = i in picks
        y = HAND_Y - (PICK_LIFT if picked else 0)
        if i not in hide:
            cards.draw_card(img, x, y, card)
        right = x + (step if i < count - 1 else cards.CARD_W)
        regions.append(((x, y, right, HAND_Y + cards.CARD_H), ("card", i)))
        if i == focus:
            focus_box = (x - 2, y - 2, right + 1, SCREEN_H - 1)
    if hands:  # the player's own hands hold the two ends of the row of cards
        _draw_hands(img, count, hands)
    if focus is not None and 0 <= focus < count:  # the yellow frame the arrow keys move (on top of the cards)
        d.rectangle(focus_box, outline=FOCUS, width=3)

    if uno_open:  # house rule: say UNO in time
        x0, y0, x1, y1 = UNO_BOX
        panel(img, UNO_BOX, "#ff4f6d", "#16122b", bw=5)
        draw_text(img, ((x0 + x1) // 2, y0 + 30), "UNO!", 5, "#ffffff", "mm", shadow="#16122b")
        key_icon(img, (x0 + x1) // 2 - 12, y0 + 56, "U", 2, "#ffe94a")
        share = _uno_left() / UNO_SECONDS
        d.rectangle([x0 + 14, y1 - 16, x1 - 14, y1 - 10], fill=(22, 18, 43))
        d.rectangle([x0 + 14, y1 - 16, x0 + 14 + int((x1 - x0 - 28) * share), y1 - 10], fill=(255, 233, 74))
        regions.append((UNO_BOX, ("uno",)))
    if cut_open:  # house rule: Corta UNO (screens/corta.py)
        x0, y0, x1, y1 = UNO_BOX
        panel(img, UNO_BOX, "#ffe94a", "#16122b", bw=5)
        draw_text(img, ((x0 + x1) // 2, y0 + 26), "CORTA", 4, "#16122b", "mm")
        draw_text(img, ((x0 + x1) // 2, y0 + 56), "UNO!", 4, "#e2413c", "mm", shadow="#16122b")
        key_icon(img, x1 - 34, y1 - 30, "K", 2, "#16122b")
        regions.append((UNO_BOX, ("cut",)))

    if choosing:
        img = darken(img, 0.5)
        d = ImageDraw.Draw(img)
        panel(img, (290, 170, 670, 344), "#fff6da", "#16122b", bw=6)
        draw_text(img, (SCREEN_W // 2, 196), "CHOOSE A COLOUR", 3, "#16122b", "mt")
        regions = [((0, 0, SCREEN_W, 540), ("cancel",))]
        for i, colour in enumerate(COLOURS):
            x = 318 + i * 84
            d.rectangle([x, 246, x + 71, 317], fill=FOCUS if i == colour_focus else (22, 18, 43))
            d.rectangle([x + 6, 252, x + 65, 311], fill=rgb(cards.COLOUR_HEX[colour]))
            regions.append(((x, 246, x + 71, 317), ("colour", colour)))
    return img, regions


# ---------------------------------------------------------------- animations (drawn by arcade/table_anim.py)

def _my_spot(index: int, count: int, raised: bool = False) -> list:
    """Top-left corner of the card at this position of the player's sorted hand."""
    left, step = hand_layout(count)
    return [round(left + index * step), HAND_Y - (PICK_LIFT if raised else 0)]


def fan_size(seat: dict) -> tuple[int, int]:
    """How big an opponent's cards look in their hands (bigger for the ones sitting close to the player)."""
    return 11 * seat["scale"], 16 * seat["scale"]


def fan_layout(seat: dict, count: int) -> tuple[list, tuple[int, int]]:
    """An opponent's cards held up in a fan in front of them: the top-left corner of each card shown (at most 9)
    and where the number of cards goes (on the table in front of them)."""
    shown = min(max(count, 1), 9)
    w, h = fan_size(seat)
    gap = 5 * seat["scale"]
    if seat["facing"] == "down":  # across the table
        middle, bottom = seat["cx"], seat["rim"] - 2
    else:  # on a side: the cards are held out towards the middle of the table
        middle, bottom = seat["cx"] + (38 if seat["facing"] == "right" else -38) * seat["scale"], seat["rim"] + 6
    half = (shown - 1) / 2
    spots = [(round(middle - w / 2 + (i - half) * gap), bottom - h + round(abs(i - half) * seat["scale"]))
             for i in range(min(count, 9))]
    return spots, (middle, bottom + 8)


def _their_spot(opponents, seat: int, count: int, index: int) -> list:
    """Top-left corner of an opponent's card number `index` in their fan, when they hold `count` cards."""
    spots, _ = fan_layout(scenes.table_seats(len(opponents))[seat], max(count, 1))
    return list(spots[min(index, len(spots) - 1)])


def _their_scale(opponents, seat: int) -> float:
    """How big an opponent's held cards are, next to a whole card (for the flying cards)."""
    return fan_size(scenes.table_seats(len(opponents))[seat])[0] / cards.CARD_W


def _seat_boxes(me_count: int, opponents) -> list:
    """The places the roulette lights up: the player's hand first, then the opponents from left to right."""
    left, step = hand_layout(me_count)
    width = step * (me_count - 1) + cards.CARD_W
    boxes = [[round(left) - 16, HAND_Y - 14, round(width) + 32, SCREEN_H - HAND_Y + 10]]
    return boxes + [[seat["cx"] - 33 * seat["scale"], seat["head"] + 4 * seat["scale"], 66 * seat["scale"],
                     seat["rim"] - seat["head"] - 4 * seat["scale"] + 16] for seat in scenes.table_seats(len(opponents))]


def deal_plan(game, me, opponents, starter: int) -> dict:
    """The start of a game: the cards are dealt one at a time around the table, the first card of the pile turns up,
    then a roulette goes round the players and stops on the one who starts (starter: 0 is the player, 1, 2, 3 the
    opponents from left to right)."""
    hand = sorted_hand(game.hands[me])
    sprites = {"back": cards.back_sprite(), "top": cards.card_sprite(game.discard[0])}
    moves, t = [], 0
    for r in range(len(hand)):
        sprites[f"mine{r}"] = cards.card_sprite(hand[r])  # the player's cards arrive face up, in order
        moves.append({"img": f"mine{r}", "from": DECK, "to": _my_spot(r, len(hand)), "at": t, "dur": DEAL_FLIGHT,
                      "h0": cards.LYING,
                      "arc": 30, "stay": True, "sound": "card"})
        t += DEAL_GAP
        for seat, opponent in enumerate(opponents):
            moves.append({"img": "back", "from": DECK, "to": _their_spot(opponents, seat, len(hand), r), "at": t,
                          "h0": cards.LYING, "dur": DEAL_FLIGHT, "s1": _their_scale(opponents, seat), "arc": 20,
                          "stay": True, "sound": "card"})
            t += DEAL_GAP
    t += DEAL_FLIGHT + 250
    moves.append({"img": "top", "from": DECK, "to": PILE, "at": t, "dur": 400, "arc": 26, "stay": True,
                  "h0": cards.LYING, "h1": cards.LYING,
                  "sound": "card"})
    t += 400 + 350
    name = "YOU" if starter == 0 else opponents[starter - 1]["name"]
    sprites["label"] = scenes.big_word("YOU START!" if starter == 0 else f"{name} STARTS!")
    return {"id": table_anim.new_id("uno-deal"), "total": t + SPIN_MS + LABEL_MS, "moves": moves,
            "under": draw(game, me, opponents, dealing=True)[0], "sprites": sprites,
            "spin": {"seats": _seat_boxes(len(hand), opponents), "winner": starter, "at": t, "dur": SPIN_MS,
                     "label": "label"}}


def move_plan(before, after, me, opponents, picks=()) -> dict | None:
    """The cards that changed hands between two moments of the game, one at a time: drawn cards fly from the deck,
    played cards fly to the pile. picks: the cards the player had picked (they stand up). None if nothing moved."""
    seat_of = {o["name"]: i for i, o in enumerate(opponents)}
    events = [event for event in changes(before, after) if event[0] == me or event[0] in seat_of]
    if not events:
        return None
    old_hand, new_hand = sorted_hand(before.hands[me]), sorted_hand(after.hands[me])
    # The picture underneath: the player's hand as it was, without the cards that leave it; or, when cards arrive,
    # the hand as it is now with gaps where they will land.
    new_layout = any(who == me and kind == "drew" for who, kind, _ in events)
    hide, taken = [], set()

    def place(hand, card, prefer=()):
        """The position of this card in the hand (one not used yet), trying the picked cards first."""
        for i in [*prefer, *range(len(hand) - 1, -1, -1)]:
            if 0 <= i < len(hand) and i not in taken and hand[i] == card:
                taken.add(i)
                return i
        return None

    drawn = {who: len(moved) for who, kind, moved in events if kind == "drew"}
    sprites, moves = {"back": cards.back_sprite()}, []
    for who, kind, moved in events:
        for j, card in enumerate(moved):
            name = f"c{len(moves)}"
            sprites[name] = cards.card_sprite(card)
            if who == me and kind == "drew":
                i = place(new_hand, card)
                hide += [] if i is None else [i]
                move = {"img": name, "from": DECK, "arc": 34, "h0": cards.LYING,
                        "to": _my_spot(len(new_hand) // 2 if i is None else i, len(new_hand))}
            elif who == me:
                i = None if new_layout else place(old_hand, card, prefer=picks)
                hide += [] if i is None else [i]
                move = {"img": name, "to": PILE, "arc": 40, "h1": cards.LYING,
                        "from": _my_spot(0, 1) if i is None else _my_spot(i, len(old_hand), i in picks)}
            else:
                seat, count = seat_of[who], len(before.hands[who]) + drawn.get(who, 0)
                if kind == "drew":
                    spot = _their_spot(opponents, seat, count, len(before.hands[who]) + j)
                    move = {"img": "back", "from": DECK, "to": spot, "s1": _their_scale(opponents, seat), "arc": 22,
                            "h0": cards.LYING}
                else:
                    spot = _their_spot(opponents, seat, count, count - 1)
                    move = {"img": name, "from": spot, "to": PILE, "s0": _their_scale(opponents, seat), "s1": 1,
                            "arc": 30,
                            "h1": cards.LYING}
            moves.append(dict(move, at=len(moves) * MOVE_GAP, dur=MOVE_FLIGHT, stay=True, sound="card"))
    under = copy.deepcopy(before)
    if new_layout:
        under.hands[me] = list(after.hands[me])
    keep = [] if new_layout else list(picks)
    return {"id": table_anim.new_id("uno-move"), "total": (len(moves) - 1) * MOVE_GAP + MOVE_FLIGHT + 120,
            "moves": moves, "under": draw(under, me, opponents, picks=keep, hide=hide)[0],
            "sprites": {k: v for k, v in sprites.items() if any(m["img"] == k for m in moves)}}


def _animate(slot, plan, after_img) -> None:
    """Play an animation over the table, then leave the picture of the table as it is now."""
    if plan is None:
        common.show(slot, after_img, "uno")
        return
    table_anim.play(slot, plan)  # the canvas covers the old picture first, so the new one arrives unseen
    time.sleep(0.12)
    common.show(slot, after_img, "uno")
    time.sleep(max(0.0, table_anim.seconds(plan) - 0.12))


def _remember(game, picks=()) -> None:
    """Keep a copy of the table just before the player's move: the next run animates what changed."""
    S.uno_before, S.uno_before_picks = copy.deepcopy(game), list(picks)


@st.fragment(run_every=0.25)
def _uno_clock() -> None:
    """While the UNO button is up, check four times a second whether time ran out."""
    game = S.get("game")
    if S.screen != "uno" or game is None or S.get("uno_deadline") is None:
        return
    cutter = corta.due_cut()
    if cutter and game.uno_due == S.player["name"]:  # a bot cut the UNO before the player said it: face-off
        corta.start(holder=S.player["name"], cutter=cutter["bot"])
        st.rerun()
    if time.time() > S.uno_deadline + UNO_GRACE:
        _remember(game)
        S.uno_cutter = None
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
    before = copy.deepcopy(game)
    game.play(me, chosen, colour)
    S.uno_before, S.uno_before_picks = before, list(S.get("uno_pick") or [])  # the next run animates the cards
    S.uno_pick, S.pending_wild, S.flash = [], None, ""
    S.uno_focus = None  # next turn the frame starts on the first card that can be played
    if game.held and game.held[0] == me:
        S.flash = "Press UNO! and your last card goes down"
    if game.uno_due == me:
        S.uno_deadline = time.time() + UNO_SECONDS
        S.uno_cutter = corta.choose_cutter(game, me, time.time())  # a bot may try to cut this UNO


def _choose_colour(bar, game, me, action, focus, key) -> None:
    """The colour of a wild: a click on a colour, or Left / Right (already applied to focus) and Enter or Space.
    X or a click elsewhere cancels."""
    with bar[0]:
        enter = ui.button("Choose colour", "uno_colour", "Enter", type="primary")
    with bar[2]:
        cancel = ui.button("Cancel", "uno_cancel", "X")
    common.pause_button(bar[3], "uno")
    common.corner_action(action, "uno")
    if enter or key == "space":
        action = ("colour", COLOURS[focus])
    elif cancel:
        action = ("cancel",)
    if not action:
        return
    S.uno_colour_focus = None
    try:
        if action[0] == "colour":
            _play(game, me, S.pending_wild, action[1])
        else:  # ("cancel",): X, or a click outside the colours
            S.pending_wild = None
    except IllegalMove as problem:
        S.flash, S.uno_pick, S.pending_wild = str(problem), [], None
    st.rerun()


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
    # The keys come first, on every run: a run that leaves them out removes them from the page (the keyboard would
    # stop working), and reading them before drawing lets this one picture show the move. Left / Right move the yellow
    # frame (on the hand, or on the colours of a wild); Space is a click on it. Like a click, a key pressed while the
    # bots play does not count.
    key = ui.keys("uno", {"Left": "left", "Right": "right", "Space": "space"})
    if S.get("duel") is not None:  # Corta UNO: the trivia face-off takes over the screen (screens/corta.py)
        corta.render_duel(slot, game, me, opponents, draw(game, me, opponents)[0], key)
        return
    if bots_were_playing:
        key = None
    if common.run_clock(not bots_were_playing and game.winner is None and not uno_open):
        S.pending_wild, S.uno_pick, S.uno_focus = None, [], None  # 15 seconds went by: draw and pass for the player
        _remember(game)
        game.auto_turn(me)
        common.restart_clock()
        S.flash = "Time's up! You drew and your turn passed"
        st.rerun()

    champ = S.match["mode"] == "champ"
    names = [o["name"] for o in opponents]
    if S.pop("uno_intro", False):  # a new game: the cards are dealt, then the roulette shows who starts
        starter = 0 if game.current == me else names.index(game.current) + 1
        _animate(slot, deal_plan(game, me, opponents, starter), draw(game, me, opponents)[0])
        common.restart_clock()  # the player's 15 seconds start after the show
    before = S.pop("uno_before", None)
    if before is not None:  # the player's own move (made in the run before): their cards fly
        plan = move_plan(before, game, me, opponents, S.pop("uno_before_picks", []))
        _animate(slot, plan, draw(game, me, opponents, S.flash, uno_open=uno_open)[0])
        if plan and S.get("uno_deadline"):
            S.uno_deadline += table_anim.seconds(plan)  # the time to say UNO starts when the card has landed
            if S.get("uno_cutter"):
                S.uno_cutter["at"] += table_anim.seconds(plan)  # and so does a bot's chance to cut it
        if plan and game.current == me:
            common.restart_clock()
    # The bots play, one visible move at a time, while the player is still in.
    if game.uno_due not in (None, me) and S.get("bot_uno") is None and game.winner is None:
        S.bot_uno = corta.bot_window(game.uno_due, time.time())
    while (not uno_open and not S.get("bot_uno") and game.winner is None and game.current != me
           and me not in game.out):
        bot = game.current
        common.show(slot, common.thinking(draw(game, me, opponents)[0], names.index(bot), len(opponents)), "uno")
        before, started = copy.deepcopy(game), time.time()
        game.bot_turn(bot, say_uno=False, **UNO_LEVELS[bots.level(bot)])  # each bot plays at its own level
        common.bot_pause(since=started)
        _animate(slot, move_plan(before, game, me, opponents), draw(game, me, opponents)[0])  # its cards fly
        if game.uno_due == bot:  # down to one card: a moment to cut its UNO before it says it
            S.bot_uno = corta.bot_window(bot, time.time())
    if S.get("bot_uno"):
        bot = S.bot_uno["bot"]
        flash = f"{bot} has one card!"
        corta.render_bot_window(slot, game, me, draw(game, me, opponents, flash, cut_open=True)[0])
        return

    if game.winner is None and me in game.out:
        # The player's place is settled: the others finish the game at once instead of the player watching.
        common.show(slot, draw(game, me, opponents)[0], "uno")
        time.sleep(1.2)
        game.play_out({name: UNO_LEVELS[bots.level(name)] for name in game.active})
    if game.winner and S.result is None:
        if champ:
            common.show(slot, draw(game, me, opponents)[0], "uno")
            time.sleep(1.2)
        match.finish([game.winner], places=game.places)
        if S.screen != "uno":
            st.rerun()

    my_turn = game.winner is None and game.current == me and not uno_open
    common.run_clock(my_turn)  # the bots are done: the player's 15 seconds start
    if not my_turn:
        key = None
    hand = sorted_hand(game.hands[me])
    focus = colour_focus = None
    if my_turn and S.pending_wild is None:  # the yellow frame on the hand: Left / Right move it, Space plays
        # The frame starts on the first card, never on a card that fits: that would give the answer away.
        focus = cursor.clamp(S.get("uno_focus"), len(hand))
        if key in ("left", "right"):
            focus = cursor.step(focus, key, len(hand))
            sound.play("blip")
        S.uno_focus = focus
    elif S.pending_wild is not None:  # the yellow frame on the colours of a wild
        colour_focus = cursor.clamp(S.get("uno_colour_focus"), len(COLOURS))
        if key in ("left", "right"):
            colour_focus = cursor.step(colour_focus, key, len(COLOURS))
            sound.play("blip")
        S.uno_colour_focus = colour_focus
    if key in ("left", "right", "space"):
        S.uno_keyboard = True  # the yellow frame only shows while the player uses the keys
    shown_focus = focus if S.get("uno_keyboard") else None
    img, regions = draw(game, me, opponents, S.flash, choosing=S.pending_wild is not None, picks=picks,
                        uno_open=uno_open, focus=shown_focus,
                        colour_focus=colour_focus if S.get("uno_keyboard") else None)
    if not S.result:
        regions += common.corner_buttons(img)  # RULES and PAUSE on the picture (no bar of buttons)
    img, regions = common.with_result(img, regions)
    common.show(slot, img, "uno")
    point = None if bots_were_playing else ui.click()  # a click made during the bots' turn does not count
    if point is not None:
        S.uno_keyboard = False  # playing with the mouse: no frame
    action = ui.hit(regions, point)
    if uno_open:
        _uno_clock()

    bar = ui.bar("uno", [1.4, 1.4, 1.4, 1, 1])  # invisible: only the keys (everything is on the picture)
    if S.result:
        common.result_buttons(bar, "uno", action)  # Continue, or Play again
        return
    common.rules_button(bar[4], "uno")
    if uno_open:
        with bar[0]:
            uno_pressed = ui.button("UNO!", "uno_call", "U", type="primary")
        common.pause_button(bar[3], "uno")
        common.corner_action(action, "uno")
        if uno_pressed or action == ("uno",):
            _remember(game)
            S.uno_cutter = None  # said in time: nobody can cut it any more
            if time.time() <= S.uno_deadline + UNO_GRACE:
                game.call_uno(me)
                sound.play("coin")
            else:
                game.miss_uno(me)
                S.flash = "Too late! +2 cards"
            S.uno_deadline = None
            st.rerun()
        return
    if S.pending_wild is not None:  # choosing a wild's colour has its own buttons and keys
        _choose_colour(bar, game, me, None if bots_were_playing else action, colour_focus, key)
        return
    with bar[0]:
        draw_label = f"Draw {game.pending} cards" if game.pending else "Draw a card"
        draw_pressed = ui.button(draw_label, "uno_draw", "D", disabled=not my_turn or not game.can_draw(me))
    with bar[1]:
        play_pressed = ui.button("Play", "uno_play", "Enter", type="primary", disabled=not my_turn or not picks)
    with bar[2]:
        cancel_pressed = ui.button("Cancel", "uno_cancel", "X", disabled=not picks)  # (Streamlit keeps C and R)
        pass_pressed = (ui.button("Pass", "uno_pass", "P", disabled=not my_turn or not game.draws)
                        or action == ("pass",))
    common.pause_button(bar[3], "uno")
    common.corner_action(action, "uno")

    if key == "space" and focus is not None:  # Space: a click on the card the yellow frame is on
        action = ("card", focus)

    acted = True
    try:
        if cancel_pressed:
            S.uno_pick = []
        elif play_pressed or action == ("play",):  # the pile (or Enter): the picked cards go down
            if not picks:
                acted = False  # clicking the pile with nothing picked does nothing
            else:
                chosen = picked_cards(game.hands[me], picks)
                if not game.can_play(chosen[0]):
                    S.flash = f"The {card_name(chosen[0])} does not match the pile"
                    sound.play("lose")
                else:
                    _play(game, me, chosen)
        elif draw_pressed or action == ("draw",):
            _remember(game)
            drawn = game.draw(me)
            S.uno_pick = []
            common.restart_clock()  # 15 new seconds to play, draw again or pass
            if game.current == me and drawn:
                S.flash = f"You drew the {card_name(drawn[0])}"
                S.uno_focus = sorted_hand(game.hands[me]).index(drawn[0])  # the frame jumps to that card
            else:
                S.flash, S.uno_focus = ("Nothing to play: your turn passes" if drawn else ""), None
        elif pass_pressed:
            game.pass_turn(me)
            S.flash, S.uno_focus = "", None
        elif action and action[0] == "card" and my_turn:
            index = action[1]
            S.uno_focus = index  # the frame follows a click too
            if index in picks:  # a picked card again: it goes back down
                S.uno_pick = [i for i in picks if i != index]
            elif picks and can_add(game.hands[me], picks, index):
                S.uno_pick = picks + [index]  # another card with the same number or symbol
            else:
                S.uno_pick = [index]  # a new pick
            S.flash = ""
            sound.play("blip")
        else:
            acted = False
    except IllegalMove as problem:
        S.flash = str(problem)
        S.uno_pick = []
    if acted:
        st.rerun()
