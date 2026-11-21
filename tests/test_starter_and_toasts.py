"""Who starts at checkers and Connect Four: the roulette's yellow frame hugs the score cards and never covers the
message under them. Toasts can wait a moment (the welcome waits for the arcade to fade in)."""

import time

import streamlit as st
from PIL import ImageChops

from arcade import bots, catalog
from arcade.logic.checkers import CheckersGame
from arcade.logic.connect4 import RED, Connect4Game
from arcade.screens import checkers, common, connect4

BOT = {"name": "BARK", "look": bots.look(bots.get("BARK")), "tag": catalog.spec_for("name", bots.get("BARK")["tag"])}
MESSAGE_TOP = 352  # common.side_message writes from here down


def test_the_roulette_frames_fit_each_games_cards_and_stay_above_the_message():
    for bottom in (connect4.CARD_BOTTOM, 344):
        plan = common.starter_plan(None, True, "BARK", bottom)
        for x, y, w, h in plan["spin"]["seats"]:
            assert y < common.CARD_TOP and y + h > bottom  # round the card
            assert y + h <= MESSAGE_TOP  # and not over "Your turn"
    connect4_frame = common.starter_plan(None, True, "BARK", connect4.CARD_BOTTOM)["spin"]["seats"][0]
    assert connect4_frame[1] + connect4_frame[3] < MESSAGE_TOP - 10  # Connect Four's shorter cards: a clear gap


def test_the_quiet_table_has_no_message_under_the_cards():
    message = (20, MESSAGE_TOP - 4, 300, MESSAGE_TOP + 70)
    game = Connect4Game(first=RED)
    loud, _ = connect4.draw(game, BOT)
    quiet, _ = connect4.draw(game, BOT, quiet=True)
    assert ImageChops.difference(loud.crop(message), quiet.crop(message)).getbbox() is not None
    board = CheckersGame()
    loud, _ = checkers.draw(board, BOT)
    quiet, _ = checkers.draw(board, BOT, quiet=True)
    assert ImageChops.difference(loud.crop(message), quiet.crop(message)).getbbox() is not None


def test_a_toast_can_wait_before_it_shows(monkeypatch):
    from arcade import ui

    monkeypatch.setattr(st, "session_state", {}, raising=False)
    before = time.time()
    ui.toast("Welcome back, ANA!", delay=0.9)
    item = st.session_state["_toasts"][-1]
    assert item["delay"] == 0.9
    assert item["until"] >= before + 0.9 + ui.TOAST_SECONDS  # it stays its full time once it shows


def test_a_picture_only_fades_in_from_black_when_asked(monkeypatch):
    from arcade import ui

    styles = []
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    monkeypatch.setattr(st, "markdown", lambda text, **_: styles.append(text))
    monkeypatch.setattr(ui, "ANIMATIONS", True)
    ui._fade_style()  # a menu over the room, the pause menu...: a plain cut
    assert "animation: none" in styles[-1]
    ui.fade_next()  # entering a table: through black
    ui._fade_style()
    assert "animation: arcade-fade-" in styles[-1]
    st.session_state.pop("_fade_next")
    ui._fade_style()  # (the same fade, still playing, on the runs right after)
    assert "animation: arcade-fade-" in styles[-1]
    st.session_state["_fade_until"] = 0
    ui._fade_style()
    assert "animation: none" in styles[-1]


def test_chat_letters_keep_small_letters_and_accents():
    from arcade.art import chat as chat_art

    _, glyphs, _ = chat_art.chat_font()
    assert {"a", "ã", "õ", "ê", "ç", "Ã", "É"} <= set(glyphs)
    small, big = chat_art.said("olá", None, False), chat_art.said("OLÁ", None, False)
    assert small.tobytes() != big.tobytes()  # written as typed, not in capitals
