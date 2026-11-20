"""Bits that every game table shares: the header, the end pop-up, the pause button,
how long the bots think, and the clock for the player's turn."""

from __future__ import annotations

import random
import time

import streamlit as st
from PIL import ImageDraw

from arcade import match, state, ui
from arcade.art import scenes
from arcade.art.pixel import draw_text, panel, text_size
from arcade.config import BOT_THINK, SCREEN_W, TURN_SECONDS
from arcade.logic import turn_clock
from arcade.state import S


def bot_pause(since: float) -> None:
    """A bot thinks for a random time between the two numbers of BOT_THINK before its move shows.
    since: when it started working out the move (that time counts too, so strong bots are not slower)."""
    time.sleep(max(0.0, random.uniform(*BOT_THINK) - (time.time() - since)))


def thinking(img, seat: int, seats: int):
    """A "..." speech bubble next to the head of the bot whose turn it is (seat: 0, 1, 2 round the table)."""
    spot = scenes.table_seats(seats)[seat]
    left_side = spot["facing"] == "left"  # the bot on the right: the bubble goes on its left, towards the table
    reach = 23 * spot["scale"]  # from the middle of the character to beside its head
    x, top = (spot["cx"] - reach - 66 if left_side else spot["cx"] + reach), spot["head"] + 15 * spot["scale"]
    tail = x + 66 - 4 if left_side else x + 4  # the tail points at the bot's head
    lean = -1 if left_side else 1
    d = ImageDraw.Draw(img)
    d.polygon([(tail, top + 44), (tail + lean * 12, top + 32), (tail + lean * 18, top + 32)], fill=(22, 18, 43))
    d.rectangle([x, top, x + 66, top + 34], fill=(22, 18, 43))
    d.rectangle([x + 3, top + 3, x + 63, top + 31], fill=(255, 246, 218))
    d.polygon([(tail + lean * 3, top + 39), (tail + lean * 12, top + 30), (tail + lean * 16, top + 30)],
              fill=(255, 246, 218))
    phase = int(time.time() * 3) % 3  # one dot is lifted, so it looks alive between two pictures
    for i in range(3):
        y = top + 12 - (3 if i == phase else 0)
        d.rectangle([x + 12 + i * 16, y, x + 21 + i * 16, y + 9], fill=(22, 18, 43))
    return img


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
    if deadline is None:  # not the player's turn: an empty line of the same height (it replaces the old bar at once)
        st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
        return
    left = turn_clock.seconds_left(deadline, time.time())
    total, label = S.get("clock_total", TURN_SECONDS), S.get("clock_label", "YOUR TURN")  # (Corta UNO: ANSWER)
    colour = "#ff4f6d" if left <= min(5, total / 3) else "#3ad6ff"
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:10px;height:30px;margin:-6px 0 2px 0'>"
        f"<div style='flex:1;height:10px;border-radius:5px;background:#17123a;border:1px solid #3a2f6b'>"
        f"<div style='width:{100 * left / total:.0f}%;height:100%;border-radius:5px;background:{colour};"
        f"box-shadow:0 0 8px {colour}'></div></div>"
        f"<b style='color:{colour};font-size:1.25rem;min-width:7.5em'>{label}: {left:.0f}s</b></div>",
        unsafe_allow_html=True,
    )
    if left <= 0 and S.get("clock_fired") != deadline:
        # Time is up: run the screen once so it can act (play for the player, close a question). Only once per
        # deadline: if the screen does not move the deadline, running it again and again would freeze the page.
        S.clock_fired = deadline
        st.rerun()


def header(img, title: str) -> None:
    """Game name and mode along the top edge of the table picture."""
    draw_text(img, (16, 8), title, 3, "#ffe94a", "lt", shadow="#16122b")
    draw_text(img, (16 + text_size(title, 3)[0] + 18, 12), match.mode_label(), 2, "#d9d4ff", "lt", shadow="#16122b")


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
    """Cover the table with the end-of-game pop-up when a free-play game is over.

    Its regions: PLAY AGAIN, and the rest of the picture (a click there continues)."""
    if not S.result:
        return img, regions
    return scenes.result_panel_again(img, S.result["title"], S.result["line"], S.result["coins"])


def corner_buttons(img, names=("rules", "pause")) -> list:
    """Small buttons in the top-right corner of a table picture (there is no bar of buttons under the picture).
    Returns their click regions: ("rules",), ("pause",), ("leave",)."""
    labels = {"rules": "RULES", "pause": "PAUSE", "leave": "LEAVE"}
    regions, right = [], SCREEN_W - 14
    for name in reversed(names):
        width = text_size(labels[name], 2)[0] + 28
        box = (right - width, 8, right, 38)
        panel(img, box, "#1c1642", "#3ad6ff", bw=3, shadow=False)
        draw_text(img, ((box[0] + box[2]) // 2, 24), labels[name], 2, "#ffffff", "mm")
        regions.append((box, (name,)))
        right = box[0] - 10
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
