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

The game opens at http://localhost:8501. Type a name, press **Play**, and use the same name later to
continue with your coins, clothes and wins.

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

Players are saved in a SQLite file, `data/arcade.db`, which is created on first run and is not
committed to git. Delete the file to reset all players. See `AGENTS.md` for what this means when the
app is deployed.
