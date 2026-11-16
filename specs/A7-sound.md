# Task: A7, music and sound effects

## Why
The game is silent. A little music and a few sound effects make it feel like an arcade.

## What
- Short sound effects when you enter the arcade, sit down at a table, win, lose or tie, open the pause menu
  and open the store.
- A short original chiptune loop plays in the room and at the tables. **M** turns the music on or off and the
  browser remembers the choice. The "How to play" panel lists the M key.
- All sounds are made in the browser with the Web Audio API (no sound files to download), so the game is not
  slower. Python only sends the name of a sound, a few bytes.
- Browsers only allow sound after the first click or key press, so the music starts then.

## Out of scope
- Sounds inside the game tables (card played, piece moved): those screens belong to stream B.
- A volume slider.

## Done when
- A test shows a known sound is queued with a new number each time.
- A test shows an unknown sound name is rejected and the queue is unchanged.
- A test shows the queue never grows beyond a few entries.
- Checked by hand: hear the sounds in a browser, press M to stop and start the music, reload the page and
  the choice is kept.
