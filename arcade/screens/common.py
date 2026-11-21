"""Bits that every game table shares: the header, the end pop-up, the pause button,
how long the bots think, and the clock for the player's turn."""

from __future__ import annotations

import random
import time

import streamlit as st
from PIL import ImageDraw

from arcade import match, state, table_anim, ui
from arcade.art import podium, scenes
from arcade.art.pixel import draw_text, panel, text_size, wrap
from arcade.config import BOT_THINK, SCREEN_W, TURN_SECONDS
from arcade.logic import turn_clock
from arcade.state import S


def bot_pause(since: float) -> None:
    """A bot thinks for a random time between the two numbers of BOT_THINK before its move shows.
    since: when it started working out the move (that time counts too, so strong bots are not slower)."""
    time.sleep(max(0.0, random.uniform(*BOT_THINK) - (time.time() - since)))


THINK_CHANCE = 0.35  # how often a bot shows a little "?" bubble while it thinks (not every time)
THINK_MARKS = ("?", "?", "?", "?!", "!?")


def thinking(img, seat: int, seats: int, rng=random):
    """Now and then, a little "?" (or "?!") bubble next to the head of the bot whose turn it is (seat: 0, 1, 2 round
    the table). Most turns there is none."""
    if rng.random() >= THINK_CHANCE:
        return img
    mark = rng.choice(THINK_MARKS)
    spot = scenes.table_seats(seats)[seat]
    left_side = spot["facing"] == "left"  # the bot on the right: the bubble goes on its left, towards the table
    reach = 23 * spot["scale"]  # from the middle of the character to beside its head
    width = 24 + text_size(mark, 3)[0]
    x, top = (spot["cx"] - reach - width if left_side else spot["cx"] + reach), spot["head"] + 15 * spot["scale"]
    tail = x + width - 4 if left_side else x + 4  # the tail points at the bot's head
    lean = -1 if left_side else 1
    d = ImageDraw.Draw(img)
    d.polygon([(tail, top + 44), (tail + lean * 12, top + 32), (tail + lean * 18, top + 32)], fill=(22, 18, 43))
    d.rectangle([x, top, x + width, top + 34], fill=(22, 18, 43))
    d.rectangle([x + 3, top + 3, x + width - 3, top + 31], fill=(255, 246, 218))
    d.polygon([(tail + lean * 3, top + 39), (tail + lean * 12, top + 30), (tail + lean * 16, top + 30)],
              fill=(255, 246, 218))
    draw_text(img, (x + width // 2, top + 17), mark, 3, (22, 18, 43), "mm")
    return img


SPIN_MS, LABEL_MS = 2400, 1300  # the roulette that shows who starts, then the name of who it landed on


def side_message(img, text: str, colour) -> None:
    """A short message under the player's score card (checkers, Connect Four), on as many lines as it needs."""
    for i, line in enumerate(wrap(text.upper(), 20)[:3]):
        draw_text(img, (160, 352 + i * 22), line, 2, colour, "mt", shadow="#16122b")


def starter_plan(table, me_starts: bool, name: str) -> dict:
    """Checkers and Connect Four: a roulette goes between the two score cards and stops on whoever starts."""
    sprites = {"label": scenes.big_word("YOU START!" if me_starts else f"{name} STARTS!")}
    boxes = [[22, 242, 276, 110], [SCREEN_W - 298, 242, 276, 110]]  # the two score cards (left: the player)
    return {"id": table_anim.new_id("starter"), "total": 300 + SPIN_MS + LABEL_MS, "moves": [], "under": table,
            "sprites": sprites, "spin": {"seats": boxes, "winner": 0 if me_starts else 1, "at": 300, "dur": SPIN_MS,
                                         "label": "label"}}


def play_starter(slot, table, me_starts: bool, name: str, screen: str | None) -> None:
    """Show who starts (the roulette), then the table, and start the player's clock after the show.
    screen: the table's screen (its countdown goes under the picture), or None online (it has its own)."""
    plan = starter_plan(table, me_starts, name)
    table_anim.play(slot, plan)
    time.sleep(0.12)
    if screen is None:
        ui.show(slot, table)
    else:
        show(slot, table, screen)
    time.sleep(max(0.0, table_anim.seconds(plan) - 0.12))
    restart_clock()


def show(slot, img, screen: str) -> None:
    """Show the table picture. The first time in a run, the turn clock goes right under it."""
    ui.show(slot, img)
    if not getattr(slot, "clock_drawn", False):
        slot.clock_drawn = True
        clock_bar(screen)


def run_clock(my_turn: bool) -> bool:
    """Start, keep or stop the clock for the player's turn. Returns True when their time has run out."""
    S.turn_deadline = turn_clock.keep_or_start(S.get("turn_deadline"), my_turn and not S.get("result"), time.time())
    return turn_clock.is_up(S.turn_deadline, time.time())


def restart_clock() -> None:
    """The player did something that keeps their turn going (drew a card, jumped again): a fresh clock."""
    S.turn_deadline = None


@st.fragment(run_every=1.0)
def clock_bar(screen: str) -> None:
    """The countdown under the table. It redraws itself every second; at zero the whole screen runs
    again, and the screen sees that the time is up and plays for the player."""
    deadline = S.get("turn_deadline")
    if S.screen != screen:
        return
    with st.container(key="game_clock"):  # laid on the picture, at the top in the middle (ui._CSS)
        if deadline is None:  # not the player's turn: nothing (it replaces the old bar at once)
            st.markdown("", unsafe_allow_html=True)
            return
        left = turn_clock.seconds_left(deadline, time.time())
        total, label = S.get("clock_total", TURN_SECONDS), S.get("clock_label", "YOUR TURN")  # (Corta UNO: ANSWER)
        ui.picture(scenes.timer_strip(left, total, label))
    if left <= 0 and S.get("clock_fired") != deadline:
        # Time is up: run the screen once so it can act (play for the player, close a question). Only once per
        # deadline: if the screen does not move the deadline, running it again and again would freeze the page.
        S.clock_fired = deadline
        st.rerun()


def message(img, text: str, y: int, colour="#ffffff", scale=2) -> None:
    """A centred line of text with a dark strip behind it so it stays readable."""
    if not text:
        return
    text = text.upper()
    width = text_size(text, scale)[0]
    ImageDraw.Draw(img).rectangle(
        [SCREEN_W // 2 - width // 2 - 10, y - 5, SCREEN_W // 2 + width // 2 + 10, y + 7 * scale + 4], fill=(16, 12, 34)
    )
    draw_text(img, (SCREEN_W // 2, y), text, scale, colour, "mt")


def with_result(img, regions):
    """Cover the table with the end-of-game pop-up when a free-play game is over (UNO: the podium).

    Its regions: PLAY AGAIN, and the rest of the picture (a click there continues)."""
    if not S.result:
        return img, regions
    if S.result.get("podium"):
        result = S.result
        return podium.podium_picture(img, result["title"], result["podium"], S.player["name"], result["coins"],
                                     line=result.get("line", ""), tied=result.get("tied", False))
    return scenes.result_panel_again(img, S.result["title"], S.result["line"], S.result["coins"])


PODIUM_DROP, PODIUM_GAP = 420, 480  # each player drops onto their step (ms), the last one first


def podium_plan(table, title: str, standings: list[dict], me: str, coins: int = 0, footer: str = "again",
                line: str = "", tied: bool = False) -> dict:
    """The players drop onto the podium one by one, from the last to the winner (arcade/table_anim.py)."""
    under, _ = podium.podium_picture(table, title, standings, me, coins, footer, with_figures=False, line=line,
                                     tied=tied)
    sprites, moves, t = {}, [], 200
    pieces = podium.figures(standings, tied)
    for i in reversed(range(len(pieces))):
        piece, (x, y) = pieces[i]
        sprites[f"p{i}"] = piece
        moves.append({"img": f"p{i}", "from": [x, y - 320], "to": [x, y], "at": t, "dur": PODIUM_DROP,
                      "stay": True, "sound": "card"})
        t += PODIUM_GAP
    return {"id": table_anim.new_id("podium"), "total": t + 250, "under": under, "sprites": sprites, "moves": moves}


def podium_now(slot, table) -> None:
    """A free-play game just ended: the last move shows a moment, then everyone drops onto the podium."""
    result = S.get("result")
    if not result or not result.get("podium"):
        return
    ui.show(slot, table)
    time.sleep(0.9)
    plan = podium_plan(table, result["title"], result["podium"], S.player["name"], result["coins"],
                       line=result.get("line", ""), tied=result.get("tied", False))
    play_podium(slot, plan, with_result(table, [])[0])


def play_podium(slot, plan: dict, final) -> None:
    """Play the podium animation, then leave the final picture (with everyone on it) behind it."""
    table_anim.play(slot, plan)
    time.sleep(0.12)
    ui.show(slot, final)
    time.sleep(max(0.0, table_anim.seconds(plan) - 0.12))


def corner_buttons(img, names=("rules", "pause")) -> list:
    """Small square buttons in the top-right corner of a table picture (there is no bar of buttons): "?" for the
    rules, two bars for pause, X to leave an online table. Returns their click regions: ("rules",), ("pause",),
    ("leave",)."""
    regions, right = [], SCREEN_W - 12
    d = ImageDraw.Draw(img)
    for name in reversed(names):
        box = (right - 40, 10, right, 46)
        panel(img, box, "#16122b", "#3ad6ff", bw=3, shadow=False)
        cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
        if name == "pause":
            d.rectangle([cx - 8, cy - 9, cx - 3, cy + 8], fill=(243, 234, 210))
            d.rectangle([cx + 3, cy - 9, cx + 8, cy + 8], fill=(243, 234, 210))
        else:
            draw_text(img, (cx, cy + 1), "?" if name == "rules" else "X", 3, "#f3ead2", "mm")
        regions.append((box, (name,)))
        right = box[0] - 8
    return regions


def corner_action(action, screen: str) -> None:
    """A click on PAUSE or RULES in the corner (see corner_buttons)."""
    if action == ("pause",):
        _open_pause(screen)
    elif action == ("rules",):
        _open_rules(screen)


def _open_pause(screen: str) -> None:
    restart_clock()  # the clock stops while the game is paused and starts again on return
    S.paused_from = screen
    S.pause_behind = S.get("_last_frame")  # the menu sits on top of the table as it was
    state.go("pause")
    st.rerun()


def _open_rules(screen: str) -> None:
    """Opens the rules of this game (task B3); Back returns to the table."""
    from arcade.screens import howto  # (imported here: howto imports the room, which imports this file's neighbours)

    restart_clock()
    howto.open_from(screen, screen)
    st.rerun()


def pause_button(column, screen: str) -> None:
    """Esc pauses (the PAUSE button on the picture does the same)."""
    with column:
        if ui.button("Pause", f"{screen}_pause", "Esc"):
            _open_pause(screen)


def rules_button(column, screen: str) -> None:
    """H opens the rules (the RULES button on the picture does the same)."""
    with column:
        if ui.button("Rules", f"{screen}_rules", "H"):
            _open_rules(screen)


def result_buttons(bar, screen: str, action) -> None:
    """After the pop-up. Continue (Enter, or a click on the picture) walks back into the arcade.
    Play again (A, or a click on PLAY AGAIN) starts the same game against the same bots straight away."""
    with bar[0]:
        leave = ui.button("Continue", f"{screen}_continue", "Enter", type="primary")
    with bar[1]:
        again = ui.button("Play again", f"{screen}_again", "A")
    if again or action == ("again",):
        match.play_again()
        st.rerun()
    if leave or action == ("continue",):
        match.back_to_hub()
        st.rerun()
