"""Connect Four rules, with no screen code at all.

Two sides, "red" and "yellow", take turns dropping a disc into one of seven
columns. Four in a row (across, down or diagonal) wins. A full board is a tie.
"""

from __future__ import annotations

import random

ROWS, COLS = 6, 7
RED, YELLOW = "red", "yellow"
DRAW = "draw"
_LINES = ((0, 1), (1, 0), (1, 1), (1, -1))


class IllegalMove(ValueError):
    """Raised when a player tries something the rules do not allow."""


def other(side: str) -> str:
    return YELLOW if side == RED else RED


class Connect4Game:
    def __init__(self, first: str = RED):
        self.board: list[list[str | None]] = [[None] * COLS for _ in range(ROWS)]  # row 0 is the top
        self.turn = first
        self.winner: str | None = None  # "red", "yellow" or "draw"
        self.win_cells: list[tuple[int, int]] = []
        self.last: tuple[int, int] | None = None

    def clone(self) -> "Connect4Game":
        copy = Connect4Game(self.turn)
        copy.board = [row[:] for row in self.board]
        copy.winner, copy.win_cells, copy.last = self.winner, list(self.win_cells), self.last
        return copy

    def legal_columns(self) -> list[int]:
        if self.winner:
            return []
        return [c for c in range(COLS) if self.board[0][c] is None]

    def drop(self, col: int) -> int:
        """Drop a disc for the side whose turn it is. Returns the row where it lands."""
        if self.winner:
            raise IllegalMove("The game is over.")
        if not isinstance(col, int) or not 0 <= col < COLS:
            raise IllegalMove("There is no such column.")
        if self.board[0][col] is not None:
            raise IllegalMove("That column is full.")
        row = max(r for r in range(ROWS) if self.board[r][col] is None)
        self.board[row][col] = self.turn
        self.last = (row, col)
        cells = self._line_through(row, col)
        if cells:
            self.winner, self.win_cells = self.turn, cells
        elif all(self.board[0][c] is not None for c in range(COLS)):
            self.winner = DRAW
        else:
            self.turn = other(self.turn)
        return row

    def _line_through(self, row: int, col: int) -> list[tuple[int, int]]:
        side = self.board[row][col]
        for dr, dc in _LINES:
            cells = [(row, col)]
            for sign in (1, -1):
                r, c = row + dr * sign, col + dc * sign
                while 0 <= r < ROWS and 0 <= c < COLS and self.board[r][c] == side:
                    cells.append((r, c))
                    r, c = r + dr * sign, c + dc * sign
            if len(cells) >= 4:
                return sorted(cells)
        return []

    def random_move(self, rng: random.Random | None = None) -> int:
        """Drop a disc in any column that is not full. Used when the player's time runs out."""
        columns = self.legal_columns()
        if not columns:
            raise IllegalMove("The game is over.")
        col = (rng or random.Random()).choice(columns)
        self.drop(col)
        return col

    # ----- computer player
    def bot_move(self, rng: random.Random | None = None, depth: int = 2, blunder: float = 0.0) -> int:
        """Choose and play a column for the side to move. Returns the column."""
        rng = rng or random.Random()
        columns = self.legal_columns()
        if not columns:
            raise IllegalMove("The game is over.")
        me = self.turn
        choice = None
        for col in columns:  # win now if possible
            trial = self.clone()
            trial.drop(col)
            if trial.winner == me:
                choice = col
                break
        if choice is None:
            for col in columns:  # otherwise block an immediate loss
                trial = self.clone()
                trial.turn = other(me)
                trial.drop(col)
                if trial.winner == other(me):
                    choice = col
                    break
        if choice is None and rng.random() < blunder:
            choice = rng.choice(columns)
        if choice is None:
            scored = [(self._search(col, depth, me) + (3 - abs(3 - col)) * 0.1, col) for col in columns]
            best = max(score for score, _ in scored)
            choice = rng.choice([col for score, col in scored if score >= best - 0.05])
        self.drop(choice)
        return choice

    def _search(self, col: int, depth: int, me: str) -> float:
        trial = self.clone()
        trial.drop(col)
        if trial.winner == me:
            return 100 + depth
        if trial.winner == other(me):
            return -100 - depth
        if trial.winner == DRAW or depth <= 0:
            return 0
        scores = [trial._search(c, depth - 1, me) for c in trial.legal_columns()]
        return min(scores) if trial.turn != me else max(scores)
