# Group Project Intro-to-Programming

## Arcade Masters

A pixel-art arcade you walk around in. Sit at a table to play **UNO**, **checkers** or **Connect Four**
against five bots, win coins, spend them on hair, shirts and name tags in the store, and unlock the
**championship** by winning each game once.

Team project for Introduction to Programming (Nova SBE, 2026/27).

## Deployed app

The presentation is a live demo of the app running at its deployed URL. The game is not online yet;
the link goes here once it is.

## Run the app on your computer

You need [uv](https://docs.astral.sh/uv/) (the same tool used in class).

```bash
uv sync
uv run streamlit run app.py
```

The game opens at http://localhost:8501. Type a name and a PIN (4 to 8 digits), press **Play**, and use
the same name and PIN later to continue with your coins, clothes and wins.

## Run the tests

```bash
uv run pytest
```

All tests must pass on `main`.

## How to play

| Where | Keys |
|---|---|
| Arcade room | **W A S D** or arrow keys to walk (hold to keep walking), or click where you want to go. **E** to use a table, the store or the championship cabinet. **Esc** for the pause menu. |
| UNO | Click a glowing card. **D** draws a card, **P** passes after drawing. |
| Checkers | Click a piece, then click a green square. Captures are mandatory. |
| Connect Four | Click a column. |
| Wardrobe (Pause > Customize character) | Click an item to try it on. **E** equips it, **U** takes it off. |

Rewards: 5 coins for each win in free play, 50 coins for winning the championship.
Store prices: common 20, rare 100, legendary 500.

## How the project is organised

```
app.py                 decides which screen to show
arcade/config.py       every number you might want to change (prices, rewards, bot strength)
arcade/logic/          the rules of each game, the store and the championship (no screen code)
arcade/art/            draws every picture with code (no image files)
arcade/screens/        one file per screen: shows the picture and reacts to clicks and keys
arcade/catalog.py      all 78 cosmetics
arcade/bots.py         the five bots
arcade/phrases.py      win, lose and championship sentences
arcade/db.py           saves and loads players (SQLite)
tests/                 tests for the rules (accepted and rejected actions)
docs/game-design.md    what the game must do
AGENTS.md              rules for people and coding agents working on this repository
```

## Where the data is stored

- **On your computer:** players are saved in a SQLite file, `data/arcade.db`, created on first run and not
  committed to git. Delete it to reset all players.
- **Online:** the free Streamlit host wipes its disk whenever the app restarts, so the deployed game saves players
  in a free hosted PostgreSQL database instead. `arcade/db.py` switches automatically when a `DATABASE_URL` secret
  is set. The connection string is never in the repository.
- **PINs** are never stored: only a salted PBKDF2 hash (see `arcade/accounts.py`). After 5 wrong PINs a name is
  locked for a minute.

### Setting up the online database (once)

1. Create a free account at [neon.tech](https://neon.tech) and a project (any name, region in Europe).
2. On the project page, copy the connection string (it starts with `postgresql://`).
3. In Streamlit Community Cloud, open the app's **Settings > Secrets** and paste:
   ```toml
   DATABASE_URL = "postgresql://...the string you copied..."
   ```
4. Save. The app restarts and creates its `players` table by itself.

To run the online-save tests against a database you may wipe (never the real one):
`TEST_DATABASE_URL="postgresql://..." uv run pytest tests/test_db_online.py`. Without it they are skipped.
