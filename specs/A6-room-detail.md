# Task: A6, more room detail

## Why
The room is readable but flat: one colour of light everywhere and large empty patches of floor.

## What
Original pixel art only, drawn in `arcade/art/scenes.py`:
- a pink neon **ARCADE** sign on the wall above the three machines;
- soft cones of light from the ceiling onto the machines, the store and the championship cabinet, with
  lighter patches on the floor under them;
- a dance-game floor pad (3x3 tiles with four arrows) in the empty bottom-left corner;
- a dotted guide line on the floor from the door into the room.
Everything new on the floor is flat, so it does not block walking and needs no change in `hubmap.py`.

## Out of scope
- Moving tables, the store or the bots, or adding furniture that blocks walking.
- Animation of the new details (A4 already makes the room move).

## Done when
- A test shows the room is still drawn at 320x180 and changes nothing in where you can walk.
- A test shows the dance pad lies on the walkable floor and covers no table, rug or place to stand.
- The team prefers the new room (before/after pictures in the pull request).
