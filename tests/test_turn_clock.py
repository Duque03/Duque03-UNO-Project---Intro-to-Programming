"""The 15-second clock for the player's turn (arcade/logic/turn_clock.py)."""

from arcade.config import TURN_SECONDS
from arcade.logic import turn_clock


def test_clock_starts_when_the_players_turn_begins():
    assert turn_clock.keep_or_start(None, True, now=100.0) == 100.0 + TURN_SECONDS


def test_clock_keeps_running_during_the_same_turn():
    assert turn_clock.keep_or_start(110.0, True, now=105.0) == 110.0


def test_clock_stops_when_it_is_not_the_players_turn():
    assert turn_clock.keep_or_start(110.0, False, now=105.0) is None


def test_time_is_up_only_at_the_deadline():
    assert not turn_clock.is_up(110.0, now=109.9)
    assert turn_clock.is_up(110.0, now=110.0)
    assert not turn_clock.is_up(None, now=1e9)  # no clock running: never up


def test_seconds_left_never_goes_below_zero():
    assert turn_clock.seconds_left(110.0, now=104.0) == 6.0
    assert turn_clock.seconds_left(110.0, now=200.0) == 0.0
    assert turn_clock.seconds_left(None, now=1.0) == 0.0


def test_the_turn_lasts_fifteen_seconds_and_bots_think_one_to_three():
    from arcade.config import BOT_THINK
    assert TURN_SECONDS == 15
    assert BOT_THINK == (1.0, 3.0)
