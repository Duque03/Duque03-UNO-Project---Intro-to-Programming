"""The clock for the player's turn at a game table (TURN_SECONDS in config.py).

It is only a time stamp, the "deadline": the moment the player's time runs out.
The screens keep it in session state and ask these functions what to do with it.
"""

from __future__ import annotations

from arcade.config import TURN_SECONDS


def keep_or_start(deadline: float | None, my_turn: bool, now: float, seconds: float = TURN_SECONDS) -> float | None:
    """The deadline to keep: none when it is not the player's turn, a new one when their turn begins."""
    if not my_turn:
        return None
    return deadline if deadline is not None else now + seconds


def seconds_left(deadline: float | None, now: float) -> float:
    return 0.0 if deadline is None else max(0.0, deadline - now)


def is_up(deadline: float | None, now: float) -> bool:
    """Has the player's time run out? (Never when there is no clock running.)"""
    return deadline is not None and now >= deadline
