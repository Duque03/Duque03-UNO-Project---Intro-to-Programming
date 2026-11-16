# Task: A5, no walking through bots or the store counter

## Why
The game tables already stop the player, but the player can walk straight through the five bots and squeeze
up against the store counter. Clicking somewhere on the floor also walks in a straight line through anything.

## What
- A step with W A S D (or the arrow keys or buttons) that would end inside a bot, a table or the strip of floor
  right in front of the store counter is refused: the player turns but stays in place, like at a table today.
- Clicking the floor walks in a straight line and stops just before the first thing in the way.
- The size of a bot's body and the counter's floor strip are numbers in `arcade/hubmap.py`.
- Nobody starts or comes back from a table inside a bot.

## Out of scope
- Bots blocking each other, and bots walking to a table (they can still pass through the player).
- Walking around obstacles automatically (path finding).

## Done when
- Tests show a step into a bot is refused and a step away from it is allowed.
- Tests show a step onto the counter strip is refused and a step beside it is allowed.
- Tests show a clicked walk stops before a bot and goes all the way when the line is free.
- Tests show the door, the centre and every place to stand are free of bots.
- Checked by hand: walk into a bot and into the counter, then away again.
