"""Corta UNO: the yes-or-no face-off (docs/game-design.md, UNO)."""
import random

import pytest

from arcade.logic.trivia import QUESTIONS, REVEAL_SECONDS, ROUND_SECONDS, Duel, TriviaError, bot_answer
from arcade.logic.uno import IllegalMove, UnoGame


def _duel(now=0.0):
    return Duel("ANA", "BRUNO", random.Random(3), now)


def _finish_round(duel, holder_right, cutter_right, now):
    truth = duel.truth
    duel.answer("ANA", truth if holder_right else not truth, now)
    duel.answer("BRUNO", truth if cutter_right else not truth, now)


def test_the_question_bank_is_big_and_has_both_answers():
    assert len(QUESTIONS) >= 50
    assert len({q for q, _ in QUESTIONS}) == len(QUESTIONS)  # no question twice
    yes = sum(1 for _, answer in QUESTIONS if answer)
    assert 0.35 < yes / len(QUESTIONS) < 0.65


def test_holder_wrong_and_cutter_right_means_the_holder_lost():
    duel = _duel()
    _finish_round(duel, holder_right=False, cutter_right=True, now=1)
    assert duel.phase == "reveal" and duel.result == "holder"
    assert duel.right == {"ANA": False, "BRUNO": True}
    assert duel.tick(1 + REVEAL_SECONDS + 0.1) and duel.phase == "done"


def test_cutter_wrong_and_holder_right_means_the_uno_stands():
    duel = _duel()
    _finish_round(duel, holder_right=True, cutter_right=False, now=1)
    assert duel.result == "cutter"


def test_both_right_or_both_wrong_brings_another_question():
    duel = _duel()
    first = duel.question
    _finish_round(duel, holder_right=True, cutter_right=True, now=1)
    assert duel.result is None and duel.phase == "reveal"
    duel.tick(1 + REVEAL_SECONDS + 0.1)
    assert duel.phase == "ask" and duel.round == 1 and duel.question != first and duel.answers == {}
    _finish_round(duel, holder_right=False, cutter_right=False, now=5)
    duel.tick(5 + REVEAL_SECONDS + 0.1)
    assert duel.round == 2 and duel.result is None


def test_no_answer_in_time_counts_as_wrong():
    duel = _duel()
    duel.answer("BRUNO", duel.truth, 2)
    assert not duel.tick(ROUND_SECONDS - 1)  # still time
    assert duel.tick(ROUND_SECONDS + 0.1)  # ANA never answered
    assert duel.result == "holder"


def test_answers_that_are_not_allowed_are_refused():
    duel = _duel()
    with pytest.raises(TriviaError):
        duel.answer("CARLA", True, 1)  # not in the face-off
    duel.answer("ANA", True, 1)
    with pytest.raises(TriviaError):
        duel.answer("ANA", False, 1)  # twice
    duel.answer("BRUNO", True, 1)
    with pytest.raises(TriviaError):
        duel.answer("BRUNO", True, 1)  # the answers are being shown
    with pytest.raises(TriviaError):
        Duel("ANA", "ANA", random.Random(1), 0)  # nobody cuts their own UNO


def test_bots_answer_right_as_often_as_their_level_says():
    rng = random.Random(5)
    right = sum(bot_answer(rng, True, 0.8) for _ in range(2000))
    assert 1500 < right < 1700


def _uno_game():
    game = UnoGame(["ME", "A"], random.Random(1))
    game.hands = {"ME": [("red", "7"), ("blue", "3")], "A": [("yellow", "1"), ("yellow", "3"), ("green", "9")]}
    game.discard, game.colour = [("red", "5")], "red"
    return game


def test_losing_a_cut_draws_7_cards():
    game = _uno_game()
    game.play("ME", [("red", "7")])
    assert game.uno_due == "ME"
    game.lose_cut("ME")
    assert len(game.hands["ME"]) == 8 and game.uno_due is None


def test_only_a_player_waiting_to_say_uno_can_lose_a_cut():
    game = _uno_game()
    with pytest.raises(IllegalMove):
        game.lose_cut("A")


def test_a_bot_can_wait_to_say_uno():
    game = _uno_game()
    game.turn = 1
    game.hands["A"] = [("red", "1"), ("green", "9")]
    game.bot_turn("A", forget_uno=0, say_uno=False)
    assert game.uno_due == "A"  # the screen gives the others a moment to cut it
