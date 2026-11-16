# Task: A4, bots feel alive while idle

## Why
The five bots stand perfectly still unless they walk to a table, so the room looks like a photo.

## What
- About every 1.2 seconds (`IDLE_EVERY` in `arcade/config.py`) each bot may stay put, turn to look another way,
  or shuffle one small step, even when the player does nothing.
- A bot never strays more than a few steps from its home spot (`WANDER` in `arcade/idle.py`), so it stays by
  "its" machine.
- A bot never steps into a table, the store counter, another bot or the player, and never leaves the floor.
- While bots walk to a table, or when animations are switched off, they do not shuffle.
- The rule lives in `arcade/idle.py` (no Streamlit), so it is tested like the rest of the logic.

## Out of scope
- Bots walking all the way between machines (they shuffle near home).
- Bots talking, or reacting to the player.

## Done when
- A test shows that over many ticks every bot stays within `WANDER` of its home.
- A test shows a bot never moves onto the player or onto another bot (rejected move).
- A test shows that over a few ticks at least one bot moves or turns (the room is never still).
- A test shows the bots' positions passed in are not changed (a new dictionary comes back).
- Checked by hand: stand still in the room for ten seconds and watch the bots; walk next to one.
