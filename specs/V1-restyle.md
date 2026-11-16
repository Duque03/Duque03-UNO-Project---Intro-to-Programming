# Task: V1, restyle the page around the game

## Why
The game picture looks like pixel art, but everything around it (buttons, name field, Streamlit's own header
and menu) looks like a plain web form. That is what makes the game look dated.

## What
Only CSS in `arcade/ui.py` (`_CSS`):
- a dark gradient background with faint scan lines instead of a flat colour;
- Streamlit's header, menu, toolbar and footer are hidden;
- the game picture (and the title picture) sits in a rounded frame with a soft cyan and pink glow;
- buttons get rounded neon outlines that light up on hover; the main button of each screen is a pink-orange
  gradient;
- the name field and the captions match;
- the text uses Pixelify Sans, a pixel font under the SIL Open Font License, loaded from Google Fonts.

## Out of scope
- The pictures themselves (ideas 2 to 5).
- Moving or renaming any button.

## Done when
- A test shows the style frames the game picture and the title picture.
- A test shows the only outside address in the style is Google Fonts.
- Checked by hand: title, room, pause menu, store and a table, at desktop width.
