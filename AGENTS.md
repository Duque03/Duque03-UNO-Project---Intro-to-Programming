# AGENTS.md

Rules for everyone (people and coding agents) who changes this repository.
Change this file through a pull request, like any other file.

## Stack

- Python 3.11 or newer, managed with `uv`.
- Streamlit for the interface, Pillow to paint the pixel art, SQLite (laptop) or a hosted PostgreSQL database
  through psycopg (online) for saved players, pytest for tests.
- No other libraries without agreeing as a team first. Keep versions pinned in `pyproject.toml`
  and keep `requirements.txt` (used by the host) identical to it.

## Commands

```bash
uv sync                          # install
uv run streamlit run app.py      # run the game at http://localhost:8501
uv run pytest                    # run all tests
```

## Folder rules

| Folder | What goes there | What must never go there |
|---|---|---|
| `arcade/logic/` | Rules: UNO, checkers, Connect Four, store, championship | Any `streamlit` or `PIL` import |
| `arcade/art/` | Functions that take plain data and return a Pillow image | Any `streamlit` import, any game rule |
| `arcade/screens/` | One file per screen: show the picture, read clicks and keys, call the logic | Game rules (put them in `logic/` and test them) |
| `arcade/config.py` | Numbers and settings | Code |
| `tests/` | pytest tests for `logic/`, `player.py`, `db.py`, `hubmap.py` | Tests that need a browser |

Every picture is painted on a 320x180 canvas and scaled up 3 times to 960x540. Positions in
`arcade/hubmap.py` are on the small canvas.

## Streams have one owner

Each stream owns its files. Nobody changes another stream's files without asking the owner first.
The full task list is in the project plan (section 5).

| Stream | Owns these files | Owner | Reviewed by |
|---|---|---|---|
| A. Room and movement | `arcade/screens/hub.py`, `title.py`; `arcade/hubmap.py`; `arcade/art/scenes.py` | Louis (`LouisBlondeau00`) | Owner of B |
| B. Game tables | `arcade/logic/uno.py`, `checkers.py`, `connect4.py`; `arcade/screens/uno.py`, `checkers.py`, `connect4.py`, `common.py`; `arcade/art/cards.py`; `arcade/phrases.py` | _name_ | Owner of A |
| C. Store and cosmetics | `arcade/logic/store.py`; `arcade/screens/store.py`, `wardrobe.py`, `pause.py`; `arcade/catalog.py`; `arcade/art/sprites.py` | _name_ | Owner of D |
| D. Championship, saves, online | `arcade/logic/championship.py`; `arcade/screens/champ.py`; `arcade/match.py`, `state.py`, `db.py`, `player.py`; `app.py`; `README.md`; deployment | _name_ | Owner of C |

## Shared files have one owner

Git does not notice when two branches change the meaning of the same data. Ask the owner before
changing these files, and change them in a small pull request of their own.

| File | Why it is shared | Owner |
|---|---|---|
| `arcade/player.py`, `arcade/db.py` | The shape of the saved player | _name_ |
| `arcade/state.py`, `arcade/match.py`, `app.py` | How screens hand over to each other | _name_ |
| `arcade/config.py`, `arcade/catalog.py` | Prices, rewards, item ids | _name_ |
| `arcade/ui.py`, `.streamlit/config.toml` | Clicks, keys, how pictures are shown | _name_ |

## Branches and review

- Never commit straight to `main`. One branch per task, named after the task (`uno-stacking`, `store-preview`).
- Keep branches short-lived. Merge small changes often.
- Every pull request is reviewed by one other member before it is merged. The reviewer checks that the
  change does what the task asked, stays inside its scope, and that tests cover accepted and rejected actions.
- If `main` breaks, fixing it comes before any other work.

## Tests

- Write or update the tests first, review them against `docs/game-design.md`, then implement.
- Every rule needs a test for an accepted action and a test for a rejected action.
- Never weaken, skip or delete a test to get a green result. If a test is wrong, fix it against the design document.
- All tests pass before a pull request is opened and after it is merged.
- After a change to a screen, also play that screen by hand: do one allowed action, one rejected action,
  then stop and restart the app and check that saved progress is still there.

## Things that are easy to get wrong

- **Streamlit reruns the whole script on every click.** Anything that must survive goes in
  `st.session_state` (see `arcade/state.py`). Anything that must survive closing the browser goes through
  `state.save()`.
- **`.streamlit/config.toml` sets `fastReruns = false` on purpose.** With the default, a click made while
  the bots are still moving starts a second run next to the first and the bots move twice. Do not change it.
- **It also switches off Streamlit's message cache** (`[global] minCachedMessageSize`). With the cache, after a dropped
  connection or an app restart the browser could be asked for a picture it had already thrown away and show
  "Connection error ... Cached ForwardMsg MISS". Do not lower it.
- **Pictures are sent inline** (`ui.show`, `ui.picture`, as high-quality WebP). Do not call `st.image` with a Pillow
  image directly: it turns pixel art into blurry JPEG and animation frames can go missing.
- **The arcade room is drawn in the browser** (`arcade/room.py`), so walking is smooth. Python still owns every
  rule: `hubmap.floor_map()` turns the rules of `hubmap.py` (floor, tables, counter, zones) into a table for the
  browser, so change the rules in `hubmap.py` and the browser follows. The room's pictures come from
  `arcade/art/room_layers.py` and are sent once per session. The browser reports events (`pos`, `interact`,
  `rules`, `pause`, `cut_done`, `need`), handled in `screens/hub.py`; Python checks every position with `room.read_pos`.
  To move the player from Python, change `S.hub["pos"]`: the browser jumps there on the next run.
- **Clicks made during a bot's turn are ignored** (see `bots_were_playing` in the table screens). Keep that
  when you change a table screen. The same goes for keys: the table screens only listen for them on the player's turn.
- **Everything works with the mouse and with the keyboard** (`docs/game-design.md`, section 0). Keys that have no
  button on screen (the arrows, Space) come from `ui.keys()`: buttons with a Streamlit shortcut that stay on the page
  but are made invisible by the `keys_` rule in `ui._CSS`, so they still hear their key. The arrow keys move a yellow
  highlight (`arcade/logic/cursor.py`); Space or Enter does what a click on it does. A new choice on a screen needs
  both a click and a key. Call `ui.keys()` on **every** run of the screen, before drawing the picture: a run that
  leaves it out (for example the run where the bots move) removes the buttons from the page and the keyboard stops
  working; to ignore a key, call it and drop the answer. Move the highlight in the same run (no `st.rerun()`), so one
  key press draws one picture.
- **The title screen is drawn in the browser too** (`arcade/title_view.py`): Python paints the pieces once
  (`arcade/art/title_layers.py`, including a sheet of the pixel font's letters) and the browser animates them and draws
  the menu and the name and PIN boxes. It sends `howto` or `submit` (name, PIN) with a number; `screens/title.py`
  checks them with `accounts.sign_up` / `accounts.log_in` and sends back the number it handled and any error message.
  An accepted sign-in is kept in `S.title_pending` and Python sends `enter`: the browser flies into the arcade and
  then sends `entered`, and only then does `state.start_session` run. The best player shown dancing comes from
  `championship.best_player(db.all_players())`, looked up at most once a minute.
- **Screens fade in with a browser animation** (`ui._fade_style`), never with pictures sent one by one: those
  stutter. Do not add animations made of several pictures to the table screens.
- **Cards that move on the UNO table are drawn by the browser** (`arcade/table_anim.py`), on a see-through canvas laid
  over the picture (`ui.Slot.overlay`, CSS `game_screen_anim`). Python sends one plan (a picture of the table before
  the move, the card pictures, where each card starts and lands and when), shows the real picture behind it and waits
  for the animation to end (`time.sleep`) before the next move. `screens/uno.py` makes the plans (`deal_plan`, the deal
  and the roulette; `move_plan`, from `logic.uno.changes(before, after)`), offline and online. The overlay is laid
  first and the picture second, so the new picture is never seen before the cards land.
- **Corta UNO** (`logic/trivia.py`): the face-off is plain logic that is given the time (`now`), so the same `Duel`
  runs offline (`screens/corta.py`, with fragments that let the bot answer and close questions four times a second)
  and online (`Lobby.duel`, moved on by `Lobbies._tick`). While a face-off runs, nothing else in the game moves.
- **The only JavaScript is `INPUT_JS` and `FULLSCREEN_JS` in `arcade/ui.py`, `SOUND_JS` in `arcade/sound.py`,
  `ROOM_JS` in `arcade/room.py`, `TITLE_JS` in `arcade/title_view.py`, `ANIM_JS` in `arcade/table_anim.py` and `JS` in
  `arcade/tiles.py`.** `ANIM_JS` only draws (and plays the card sounds through `SOUND_JS`) and never sends anything back. `INPUT_JS` reports clicks on the game picture.
  `FULLSCREEN_JS` is the FULL SCREEN button (and the F key) and sends nothing back. `SOUND_JS` only plays sounds by
  name (and draws the MUSIC button, which does what M does) and never sends anything back. Its tunes come from
  `arcade/music.py`, written into the script once (`__SCORE__`); each run only sends the name of the tune the screen
  wants (`music.track_for`). To change a tune, edit its text in `music.py`; `tests/test_music.py` checks it fits. `ROOM_JS` moves and draws the room; it numbers every press of E, I and Esc and
  sends it again until Python has handled it (`room.new_press`), so a press is never lost. The `tiles.py` script draws
  the item grid of the store and the wardrobe and reports which item was clicked. Python checks every value it
  receives before using it (`tiles.grid` only accepts ids that exist in `catalog.py`).
- **Online lobbies live on the server, not in a session** (`arcade/logic/lobby.py`, shared through
  `st.cache_resource` in `arcade/online.py`). Every player's session reads and changes the same `Lobbies` object, which
  has a lock, so never keep a lobby or its game in `st.session_state`: keep only the code (`S.lobby_code`) and ask
  `online.lobbies().get(code)` for a fresh copy on every run. Moves go through `lobbies.act()`, which checks whose
  turn it is and the game's rules. The screens (`screens/online.py`, `screens/online_table.py`) look at the lobby's
  version once a second (a fragment) and draw again only when it changed.
- **Every screen is drawn inside one container, `game_frame`** (app.py), which `ui.py` styles as the glowing frame
  with the buttons at the bottom. A new screen gets the frame for free.
- **Streamlit fades the page while the script runs** (`data-stale`). `ui.py` switches that off, because in a game
  it looks like the screen going dark.

## Data and secrets

- Players are saved by `arcade/db.py`: in `data/arcade.db` (SQLite, in `.gitignore`) on a laptop, and in a hosted
  PostgreSQL database when a `DATABASE_URL` secret is set (the deployed app). Same table, same three functions.
- A player is stored as one JSON text per name. New fields get their default from `player.new_player()`.
- Tests use a temporary SQLite file (`tmp_path`), never `data/arcade.db` and never the real online database.
  `tests/test_db_online.py` only runs with `TEST_DATABASE_URL` set to a database that may be wiped.
- Sign-in goes through `accounts.sign_up` (new player) and `accounts.log_in` (name + PIN). PINs are stored only as salted PBKDF2 hashes; never log,
  print or show them.
- No keys, passwords or connection strings in the repository. Secrets go in the host's settings and in
  `.streamlit/secrets.toml`, which is in `.gitignore`.

## Known limits (be ready to explain them)

- A forgotten PIN cannot be recovered (there is no email). Delete the player from the database to free the name.
- Walking happens in the browser and Python only hears about it when the player stops, changes zone or presses a
  key, so the position Python knows can be a fraction of a second old (every action re-sends it).
- In the championship, the two bots that are not playing you do not really play: their result is drawn at random.
- Online lobbies are kept in the server's memory: if the server restarts (or the free host puts the app to sleep after
  hours with no visitors), open lobbies are gone. Saved players are not: they are in the database.
- Online moves reach the other players within about a second, because each browser asks the server once a second.
