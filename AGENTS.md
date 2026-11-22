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
uv run python tools/simulate_rules.py --games 1000   # thousands of games with the rules alone (a few minutes)
uv run python tools/simulate_app.py --games 20       # whole random games through the real screens, headless (slow)
```

Before a release, run both simulators: they play the real rules and the real screens with a random player and print
every crash with the steps that led to it (a duplicate element id at the end of Connect Four was found this way).

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
  `rules`, `pause`, `cut_done`, `need`, `talk`, `versus`, and online `chat`), handled in `screens/hub.py` (online:
  `screens/online_room.py`); Python checks every position with
  `room.read_pos`. To move the player from Python, change `S.hub["pos"]`: the browser jumps there on the next run.
- **The bots' walks are planned in Python** (`arcade/wander.py`, no Streamlit, tested in `tests/test_wander.py`): every
  `IDLE_EVERY` seconds `wander.tick` decides who goes where and finds a path round the furniture; the browser walks it
  at `wander.SPEED` when the walk number (`pid`) changes. `wander.where(bot, now)` says where a walking bot is right
  now (used to check a TALK press and to start the walk to a table from where they really are, `wander.free_table`).
  What they say is in `arcade/dialogues.py`; a chat is `S.hub["talk"]`, drawn by `ROOM_JS` as speech bubbles.
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
  An accepted sign-in runs `state.start_session` at once (a new player goes to `screens/create.py`, which comes back
  to the title); with a player signed in (`signed_in`) the menu is PLAY OFFLINE / PLAY ONLINE / HOW TO PLAY / LOG OUT
  (`play`, `logout`). After PLAY OFFLINE Python sends `enter`: the browser flies into the arcade and then sends
  `entered`, and only then does the player walk in. The online menu (`online` step: CREATE LOBBY / JOIN A LOBBY /
  PLAY OFFLINE / GO BACK) and the join box (`join` step) are steps of the same browser view, so moving between them
  sends nothing; only CREATE LOBBY and JOIN send `lobby` (numbered, once: a second press waits for the answer), and
  `screens/title.py` makes or joins the lobby and flies the player into it (`title_target = "lobby"`). Other screens
  open the title on a step with `screens/online.to_title(step, notice)` (the pause menu's PLAY ONLINE, leaving a
  lobby with `online.leave`, which goes back to the `mode` step). The best player shown dancing comes from
  `championship.best_player(db.all_players())`, looked up at most once a minute.
- **Into a game and out of it goes behind the curtain** (`ui.curtain_to(screen)`, never `S.screen = ...` there): the
  screen becomes `"curtain"` (`ui.render_curtain`), whose run lets `CURTAIN_JS` bring the purple ARCADE MASTERS box
  down over the old screen (it is laid on the page outside Streamlit, so no rerun touches it) and then opens the real
  screen; the box lifts once that screen has drawn (its marker in the backdrop box and a fresh picture, the cards'
  animation or a few frames of the room), after at least `CURTAIN_MIN`. Used by `hub._finish_walk`,
  `match.back_to_hub`, the scoreboard and the online `online_room._to_table` / `enter(curtain=True)`.
- **The opponent picker is drawn by `ROOM_JS` over the live room** (`hub._versus_data`, `room._versus`, pieces from
  `art/versus.py` sent once): E at a table only sets `S.hub["versus"]` with a new number; the browser answers with the
  numbered `versus` event (`{"picked": [...]}` for PLAY, `{"picked": None}` for BACK), checked again by
  `hub._versus_answer` (`levels.check_pick`). `screens/versus.py` is the old picture version, no longer opened.
- **Screens fade in with a browser animation** (`ui._fade_style`), never with pictures sent one by one: those
  stutter. Do not add animations made of several pictures to the table screens. The fade only plays after
  `ui.fade_next()` (for `FADE_WINDOW` seconds): call it only where the game should go through black (into a table,
  back into the room). It is a dip to black: from a picture, `app.py` gives the backdrop the old picture darkening
  (`backdrop(..., "dim")`) and the new screen (picture, card animation, room, messages) waits `DIM_SECONDS`, then
  comes up; from a screen the browser draws (`ui.BROWSER_SCREENS`: it already went black by itself) the backdrop is
  black and the new screen comes up at once. The fade's selectors must not depend on `data-stale` (a rerun during
  the fade would start it again), and the canvases are reached through their boxes (they live inside components). Any other change of screen is a plain cut, and on the first run of a new screen `app.py` puts
  the previous picture behind everything (`ui.backdrop`, `_last_src`: kept by `ui.show`, or by `ui.remember` for a
  screen the browser draws, like the room before it opens the pause menu or the store), so the page never shows black
  while the new screen makes its picture. The screens of the title menu draw on `title_layers.still()`.
- **Nothing may move place on the page from one screen to the next.** The backdrop box is always the first thing in
  `game_frame` (empty when the screen did not change) and the toast box always the second (made in `app.py` before
  the screen, filled after it): an element that moves index is rebuilt by the browser (a black blink), and a box that
  moves index showed the old screen's picture inside it. The CSS also takes the old screen out as soon as the new
  picture, room or title is on the page (Streamlit keeps it until the run ends, which doubled the picture), and makes
  every game picture fill the frame from its first frame. Check changes with the browser glitch scripts (every frame).
- **`app.py` calls `ui.fresh_page()` first, on every full run.** Streamlit 1.67 leaves "where the next element goes"
  pointing inside a fragment's container after the fragment runs; when a full run follows in the same thread (quick
  clicks, a busy server), the whole page was written again inside `game_frame` (a doubled picture, blinks, even a
  white page). `tests/test_page_layout.py` checks it. Keep it the first line.
- **No key hints on the screen** (Miguel's call): no key badges on buttons and no "ARROWS: CHOOSE - ENTER: OK" lines.
  The keys still work (hidden buttons, `ui.keys`), and How to play lists them. The one exception: the yellow keys on
  the room's bubbles, E (PLAY, SHOP, TALK, START CHAMPIONSHIP, LEAVE SEAT) and I (RULES), `room_layers.SHOWN_KEYS`.
- **Cards that move on the UNO table are drawn by the browser** (`arcade/table_anim.py`), on a see-through canvas laid
  over the picture (`ui.Slot.overlay`, CSS `game_screen_anim`). Python sends one plan (a picture of the table before
  the move, the card pictures, where each card starts and lands and when), shows the real picture behind it and waits
  for the animation to end (`time.sleep`) before the next move. `screens/uno.py` makes the plans (`deal_plan`, the deal
  and the roulette; `move_plan`, from `logic.uno.changes(before, after)`), offline and online. The overlay is laid
  first and the picture second, so the new picture is never seen before the cards land.
- **The arcade moves by itself** (`arcade/art/alive.py`): the games on the machines' screens, their marquee lights,
  the claw, the neon signs and the bunting are short loops of small pictures that the browser plays. In the room they
  are drawn by `ROOM_JS` right after the background (`room_layers.alive_patches`). Behind a table (`art/table_room.py`:
  the same wall as the room, the part behind that table) they are drawn by `ALIVE_JS` on a see-through canvas over the
  picture (`ui.Slot.alive_layer`, CSS `game_screen_alive`, under the animations). `scenes.table_scene` marks its picture
  (`img.info["alive"]`); `ui.show` then sends only the parts that can be seen, each with a mask of where nothing stands
  in front (the picture compared with `scenes.empty_table_room`), so cards, players, bubbles and a dimmed picture are
  never painted over. A new prop on the wall needs its patch next to it in `LAYOUT` / `alive_patches`.
- **Corta UNO** (`logic/trivia.py`): the face-off is plain logic that is given the time (`now`), so the same `Duel`
  runs offline (`screens/corta.py`, with fragments that let the bot answer and close questions four times a second)
  and online (`Table.duel`, moved on by `Lobbies._tick`). While a face-off runs, nothing else in the game moves.
- **The only JavaScript is `INPUT_JS`, `FULLSCREEN_JS` and `CURTAIN_JS` in `arcade/ui.py`, `SOUND_JS` in `arcade/sound.py`,
  `ROOM_JS` in `arcade/room.py`, `TITLE_JS` in `arcade/title_view.py` and `ANIM_JS` and `ALIVE_JS` in `arcade/table_anim.py`.** `ANIM_JS` only draws (and plays the card sounds through `SOUND_JS`) and never sends anything back. `ALIVE_JS` only loops the moving parts of the wall behind a table (see below). `INPUT_JS` reports clicks on the game picture.
  `FULLSCREEN_JS` is the small full-screen icon (and the F key) and sends nothing back. `SOUND_JS` only plays sounds
  by name (and draws the small music icon, which does what M does) and never sends anything back. Its tunes come from
  `arcade/music.py`, written into the script once (`__SCORE__`). There are two players of the same script:
  `sound.render_music()` at the **top** of every run (key `music_player`: the tune the screen wants, `music.track_for`,
  and the level from `player["music"]`), so a table's tune starts before its slow first run; and `sound.render()` at
  the end (key `sound_player`: the sound cues). The pause menu's tune is `"silence"`. Each tune keeps its own start
  time in the browser (`goTo`), so coming back to it continues as if it had played all along. To change a tune, edit its text in `music.py`; `tests/test_music.py` checks it fits. `ROOM_JS` moves and draws the room; it numbers every press of E (interact or talk), I and Esc and
  sends it again until Python has handled it (`room.new_press`), so a press is never lost. Python checks every value
  it receives before using it. The store and the wardrobe are pictures too (`arcade/art/shop.py`): a click on an item
  is only accepted if the id exists in `catalog.py`.
- **Online lobbies live on the server, not in a session** (`arcade/logic/lobby.py`, shared through
  `st.cache_resource` in `arcade/online.py`). Every player's session reads and changes the same `Lobbies` object, which
  has a lock, so never keep a lobby or its game in `st.session_state`: keep only the code (`S.lobby_code`) and ask
  `online.lobbies().get(code)` for a fresh copy on every run. A lobby is a room: `Lobby.room` (where each player
  stands), `Lobby.chat` (the last messages, cleaned by `logic/chat.py`) and `Lobby.tables`, one `Table` per game, each
  with its chairs, its own game, clock, face-off, result and version. `sit` / `stand` / `say` / `move` change the room;
  a table starts by itself when its chairs are full (UNO also after `UNO_COUNTDOWN`); moves go through
  `lobbies.act()`, which finds the player's table and checks whose turn it is and the game's rules; `done` /
  `quit_table` take a player back to the room, and the table is cleared once everyone who played is back.
- **The online room is the offline room's browser code with extras** (`screens/online_room.py`, `room.scene(...,
  online=...)`): the other players are actors that glide (at `GLIDE`) to where they were last seen, the browser
  reports the player's position every `room.POS_EVERY` seconds while walking, and `ROOM_JS` also draws the table signs,
  the chair mats, the speech bubbles and the chat bar with its emoji panel (`art/chat.py`). The chat's text box is a
  real, see-through `<input>` laid over the bar, so a phone shows its keyboard and no game key fires while typing;
  messages arrive as the `chat` event, numbered like E and Esc. The room looks at the lobby every `LOOK_EVERY` seconds
  (a fragment); a table screen (`screens/online_table.py`) only watches its own table's version
  (`lobbies.version(code, game)`), so walking and chatting in the room do not redraw a game.
- **A click in the room walks round the furniture**: `ROOM_JS` `route()` finds the shortest way over the floor map
  (a breadth-first search, no cut corners) and keeps only its corners; `G.target` is the next corner and
  `G.target.rest` the others. Any key, or a bot in the way, ends the walk (`G.target = null`).
- **`ROOM_JS` listens to the page only once** (`G.handlers`): Streamlit calls the component's function again on every
  run, and a listener added each time would make every key fire several times (a key that toggles would undo itself).
- **Every screen is drawn inside one container, `game_frame`** (app.py), which `ui.py` makes fill the window: the
  16:9 picture as big as the window allows, nothing around it. The countdown (`common.clock_bar`, and the online
  `_watch`) goes in a container keyed `game_clock`, which the CSS lays on the picture at the top.
- **There is no row of buttons under the picture** (Miguel's call: everything is on the screen). A screen's buttons go
  in `ui.bar(name, widths)`, which hides them but keeps their keys, and every action also gets a click region on the
  picture (for the tables: `common.corner_buttons` for RULES / PAUSE / LEAVE, the deck, the pile, PASS).
- **Little messages go through `ui.toast(text)`, never `st.toast`**: the browser's font is not the game's. `ui.toast`
  paints the message in the game's pixel font and keeps it for a few seconds across reruns; `app.py` shows the ones
  still up on every run, after the screen, in the box `app.py` made before it (`ui.render_toasts(box)`, laid on the
  picture at the top right). `delay` makes one
  wait before it pops up (the welcome waits for the arcade to fade in).
- **A screen that raises never leaves a black page**: `app.py` catches it and `state.recover` writes the traceback to
  the log (Streamlit Cloud: Manage app > Logs), shows "Oops! Something went wrong. Back to the arcade.", clears the
  game and goes back to the room (or the lobby) with progress saved. More than three times in a minute, or with
  `ARCADE_STRICT` set (the tests and the simulators set it), the error is shown instead, so bugs are still seen.
- **Streamlit fades the page while the script runs** (`data-stale`). `ui.py` switches that off, because in a game
  it looks like the screen going dark.

## Data and secrets

- Players are saved by `arcade/db.py`: in `data/arcade.db` (SQLite, in `.gitignore`) on a laptop, and in a hosted
  PostgreSQL database when a `DATABASE_URL` secret is set (the deployed app). Same table, same three functions.
- A player is stored as one JSON text per name. New fields get their default from `player.new_player()`.
- The look a player made when they created their account is `player["base"]` (checked by `logic/looks.py`).
  `player.look()` turns it into item ids `base:hair:<style>:<colour>` / `base:shirt:<colour>` when nothing from the
  store is worn, and `catalog.spec_for` draws them (only listed values; anything else draws the default look).
  `look_done` is False only for a brand-new account, which goes to `screens/create.py` first.
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
  In the online room the others are seen where they were up to about a second ago, gliding there.
- Keys pressed very quickly while the server is still drawing the last one can count once (Streamlit joins two
  presses of the same hidden button that arrive during one run). The room and the title menus are drawn in the
  browser, so there every press counts; the picture menus (pause, store, tables) may skip one on a slow server.
- The chat filter is a list of words (English and Portuguese, `logic/chat.py`): it catches the usual rude words, not
  every way of spelling them. Messages are not saved anywhere: they live in the lobby (server memory) and are gone with
  it.
