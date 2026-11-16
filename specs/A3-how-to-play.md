# Task: A3, "How to play" panel

## Why
Nothing in the game tells a new player which keys to use. Someone who has never seen the game does not know
that E starts a table, that D draws a card in UNO or that Esc pauses.

## What
- A **How to play** button on the title screen and a **HOW TO PLAY** option in the pause menu open a light-blue
  panel in the style of the other menus.
- The panel has four tabs: the arcade room, UNO, checkers and Connect Four. Each tab says in one line what the
  goal is and lists the keys (or clicks) and what they do, as described in `docs/game-design.md`.
- Tabs are chosen by clicking them on the picture or with the buttons under it (keys 1 to 4).
  **Back** (Esc) returns to where the panel was opened (title screen or pause menu).
- The text lives in `arcade/controls.py`, so it can be corrected without touching the drawing code.

## Out of scope
- Rules of each game in full (the championship already has its own rules panel).
- Changing any key or button of the room or the tables.

## Done when
- A test shows the panel has a tab for the room and for each of the three games.
- A test shows every tab can be drawn, and a click on a tab name selects that tab.
- A test shows an unknown tab, or a line too long to fit in the panel, is rejected instead of being drawn
  outside the panel.
- Checked by hand: open the panel from the title screen and from the pause menu, switch tabs, go back.
  A person who has never played can start a table using only the panel.
