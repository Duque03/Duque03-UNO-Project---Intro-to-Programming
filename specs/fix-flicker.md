# Fix: the game picture blinks on and off

## Why
Since the idle bots (A4) and the title animation (V5) redraw the picture on a timer, the picture disappeared
for a moment at every redraw: on and off about twice a second, worse on a slower computer.

## What
The picture slot was `st.empty()`. On each run Streamlit first replaces the old picture with an empty
placeholder, so the browser removes the picture and waits for the new one. Now `ui.screen()` returns a
`Slot`: the first picture of a run goes straight into the container (the browser keeps the old picture until
the new one is ready), and later pictures in the same run (walking, fades, bot moves) replace it in place.

## Out of scope
- Making the timed redraws faster or less frequent.

## Done when
- Tests show the first picture goes straight into the container, later ones replace it, and no empty
  placeholder is ever used (rejected).
- In the browser, the title, the room (idle and walking), the pause fade and an UNO table always show exactly
  one picture when sampled every 40 ms.
