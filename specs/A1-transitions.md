# Task: A1, fade to black between screens

## Why
Every screen change is an instant cut today: the title screen, the room and the tables replace each other
from one frame to the next, which feels unfinished.

## What
- When the player enters the arcade (Play on the title screen), when a game starts (after the zoom on the
  table) and when a game ends (back to the room, or on to the championship scoreboard), the old picture fades
  to black and the new one fades in from black.
- Leaving the arcade from the pause menu fades back to the title screen the same way.
- The number of frames and the time between them are settings in `arcade/config.py` (`FADE_STEPS`,
  `FADE_DELAY`). With `ANIMATIONS = False` every change stays instant.

## Out of scope
- Opening the pause menu, the store, the wardrobe and the "How to play" panel. They are panels on top of the
  room, not new places.
- Sound, and any other kind of animation (slides, wipes).

## Done when
- A test shows a fade of 0 keeps the picture and a fade of 1 is fully black.
- A test shows a fade outside 0 to 1, or with fewer than 1 step, is rejected.
- A test shows the frames go from the old picture to black and then to the new picture, getting darker then lighter.
- Checked by hand: enter the arcade, start a game, finish it. None of these is an instant cut.
