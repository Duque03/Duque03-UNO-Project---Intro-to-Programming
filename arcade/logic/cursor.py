"""Moving the yellow highlight with the arrow keys (docs/game-design.md, section 0).

Menus, bots, cards, columns and store items sit in a row: Left / Up go back, Right / Down go forward.
The checkers board is a grid: the arrow keys move one square and stop at the edge.
No Streamlit here, so it is tested like the game rules.
"""

from __future__ import annotations

ROW_KEYS = {"left": -1, "up": -1, "right": 1, "down": 1}
BOARD_KEYS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}


def step(index: int | None, key: str, count: int, wrap: bool = True) -> int | None:
    """Where the highlight goes in a row of `count` things after an arrow key. None when there is nothing.

    The first press (index None) lands on the first thing. With wrap, going past an end comes round to the
    other end; without, the highlight stops there.
    """
    if key not in ROW_KEYS:
        raise ValueError(f"not an arrow key: {key}")
    if count <= 0:
        return None
    if index is None:
        return 0
    moved = clamp(index, count) + ROW_KEYS[key]
    return moved % count if wrap else min(max(moved, 0), count - 1)


def clamp(index: int | None, count: int) -> int | None:
    """Keep the highlight on something that still exists (a hand of cards can get smaller)."""
    if count <= 0:
        return None
    if index is None:
        return 0
    return min(max(index, 0), count - 1)


def first(useful: list[bool]) -> int | None:
    """Where the highlight starts: the first useful thing (for example a card that can be played), else the first."""
    if not useful:
        return None
    return next((i for i, ok in enumerate(useful) if ok), 0)


def on_board(cell: tuple[int, int], key: str, rows: int, cols: int) -> tuple[int, int]:
    """The board cursor after an arrow key: one square that way, or no move at the edge."""
    if key not in BOARD_KEYS:
        raise ValueError(f"not an arrow key: {key}")
    dr, dc = BOARD_KEYS[key]
    row, col = cell
    return (min(max(row + dr, 0), rows - 1), min(max(col + dc, 0), cols - 1))


PAD_COLUMNS = 5


def pad_step(index: int, key: str, letters: int, columns: int = PAD_COLUMNS) -> int:
    """The on-screen keyboard for a lobby code: `letters` keys in rows of `columns`, then a bottom row of three
    (DEL, JOIN, BACK at letters, letters + 1, letters + 2). The arrows move one key and stop at the edges; Down from
    the last row of letters goes to the bottom row, Up from the bottom row comes back above it."""
    if key not in BOARD_KEYS:
        raise ValueError(f"not an arrow key: {key}")
    rows = -(-letters // columns)
    if index >= letters:  # the bottom row
        spot = index - letters
        if key in ("left", "right"):
            return letters + min(max(spot + (1 if key == "right" else -1), 0), 2)
        if key == "up":
            col = (0, columns // 2, columns - 1)[spot]
            return min((rows - 1) * columns + col, letters - 1)
        return index
    row, col = divmod(index, columns)
    if key == "left":
        return index if col == 0 else index - 1
    if key == "right":
        return index if col == columns - 1 or index + 1 >= letters else index + 1
    if key == "up":
        return index if row == 0 else index - columns
    if row == rows - 1 or index + columns >= letters:  # down from the last row: to DEL, JOIN or BACK
        return letters + (0 if col < columns // 2 else 1 if col == columns // 2 else 2)
    return index + columns
