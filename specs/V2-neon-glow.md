# Task: V2, neon glow on every picture

## Why
Neon signs, arcade screens and table tops are drawn as flat colours, so the room looks dull and old.

## What
- Just before a picture is sent to the browser (`ui._inline`), bright and saturated colours get a soft glow
  around them (`arcade/art/effects.py`, `neon_glow`). Whites, greys and dark colours stay sharp, so text and
  panels stay readable.
- The glow can be switched off with `GLOW = False` in `arcade/config.py`.
- It costs about 20 ms per picture (the blur is made on a picture four times smaller).

## Out of scope
- Shadows and lighting (V3), animations (V5).

## Done when
- A test shows a neon colour lights up the pixels around it and far pixels stay black.
- A test shows white and grey do not glow (rejected).
- A test shows the glow only ever brightens, strength 0 changes nothing, and the original picture is untouched.
- A test shows a strength outside 0 to 1 is rejected.
- Checked by hand: title, room, pause menu, store and a table.
