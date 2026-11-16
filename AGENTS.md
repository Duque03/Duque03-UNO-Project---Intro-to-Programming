# AGENTS.md

Rules for everyone (people and coding agents) who changes this repository.
Change this file through a pull request, like any other file.

## Stack

- Python 3.11 or newer, managed with `uv`.
- Streamlit for the interface, Pillow to paint the pixel art, SQLite for saved players, pytest for tests.
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
- **Pictures are sent inline as PNG** (`ui.show`, `ui.picture`). Do not call `st.image` with a Pillow image
  directly: it turns pixel art into blurry JPEG and animation frames can go missing.
- **Clicks made during a bot's turn are ignored** (see `bots_were_playing` in the table screens). Keep that
  when you change a table screen.
- **The only JavaScript is `INPUT_JS` in `arcade/ui.py` and `SOUND_JS` in `arcade/sound.py`.** `INPUT_JS` reports
  clicks and walking keys. `SOUND_JS` only plays sounds by name and never sends anything back. Python checks
  every value it receives before using it.

## Data and secrets

- Saved players live in `data/arcade.db` (SQLite). The file is in `.gitignore`. Delete it to reset all players.
- A player is stored as one JSON text per name. New fields get their default from `player.new_player()`.
- Tests use a temporary database (`tmp_path`), never `data/arcade.db`.
- On Streamlit Community Cloud the disk is temporary, so `data/arcade.db` is wiped whenever the app restarts.
  If saved progress must survive there, move storage to a hosted database: change only `arcade/db.py`, read
  the connection string from a secret named `DATABASE_URL`, and keep tests on a local database.
- No keys, passwords or connection strings in the repository. Secrets go in the host's settings and in
  `.streamlit/secrets.toml`, which is in `.gitignore`.

## Known limits (be ready to explain them)

- Anyone who types a name continues that player's save. There is no password yet.
- Walking is one request to the server per step, so it is less smooth than a game written in JavaScript.
- Bots in the room stand still unless they walk to a table.
- In the championship, the two bots that are not playing you do not really play: their result is drawn at random.
