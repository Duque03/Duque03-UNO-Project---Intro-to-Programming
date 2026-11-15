"""Checkers (English draughts) rules, with no screen code at all.

  * 8x8 board, pieces only ever stand on the dark squares.
  * The "bottom" side moves up the board, the "top" side moves down.
  * Men move one square diagonally forward. Kings move one square in any
    diagonal direction.
  * Jumping over an enemy piece captures it. If you can capture you must,
    and a piece that can keep jumping has to keep going.
  * A man that reaches the far row becomes a king (and its turn ends).
  * You lose when you have no pieces or no legal move.
  * To stop endless games: after 60 moves in a row without a capture, the side
    with more pieces wins. Equal pieces is a draw.

Pieces on the board: "b"/"B" = bottom man/king, "t"/"T" = top man/king.
"""

from __future__ import annotations

import random

SIZE = 8
BOTTOM, TOP = "bottom", "top"
DRAW = "draw"
QUIET_LIMIT = 60

Move = tuple  # ((from_row, from_col), (to_row, to_col), captured square or None)


class IllegalMove(ValueError):
    """Raised when a player tries something the rules do not allow."""


def other(side: str) -> str:
    return TOP if side == BOTTOM else BOTTOM


def owner(piece: str | None) -> str | None:
    if piece is None:
        return None
    return BOTTOM if piece.lower() == "b" else TOP


class CheckersGame:
    def __init__(self, first: str = BOTTOM, empty: bool = False):
        self.board: list[list[str | None]] = [[None] * SIZE for _ in range(SIZE)]
        if not empty:
            for row in range(SIZE):
                for col in range(SIZE):
                    if (row + col) % 2 == 1:
                        if row < 3:
                            self.board[row][col] = "t"
                        elif row > 4:
                            self.board[row][col] = "b"
        self.turn = first
        self.winner: str | None = None  # "bottom", "top" or "draw"
        self.chain: tuple[int, int] | None = None  # piece that must keep jumping
        self.quiet_moves = 0
        self.last_move: Move | None = None

    def clone(self) -> "CheckersGame":
        copy = CheckersGame(self.turn, empty=True)
        copy.board = [row[:] for row in self.board]
        copy.winner, copy.chain, copy.quiet_moves = self.winner, self.chain, self.quiet_moves
        return copy

    # ----- reading the state
    def count(self, side: str) -> int:
        return sum(1 for row in self.board for piece in row if owner(piece) == side)

    def _directions(self, piece: str):
        if piece == "b":
            return ((-1, -1), (-1, 1))
        if piece == "t":
            return ((1, -1), (1, 1))
        return ((-1, -1), (-1, 1), (1, -1), (1, 1))

    def _captures_from(self, row: int, col: int) -> list[Move]:
        piece = self.board[row][col]
        moves = []
        for dr, dc in self._directions(piece):
            mid_r, mid_c, end_r, end_c = row + dr, col + dc, row + 2 * dr, col + 2 * dc
            if not (0 <= end_r < SIZE and 0 <= end_c < SIZE):
                continue
            middle = self.board[mid_r][mid_c]
            if middle and owner(middle) != owner(piece) and self.board[end_r][end_c] is None:
                moves.append(((row, col), (end_r, end_c), (mid_r, mid_c)))
        return moves

    def _steps_from(self, row: int, col: int) -> list[Move]:
        piece = self.board[row][col]
        moves = []
        for dr, dc in self._directions(piece):
            end_r, end_c = row + dr, col + dc
            if 0 <= end_r < SIZE and 0 <= end_c < SIZE and self.board[end_r][end_c] is None:
                moves.append(((row, col), (end_r, end_c), None))
        return moves

    def legal_moves(self) -> list[Move]:
        """Every move the side to play may make right now."""
        if self.winner:
            return []
        if self.chain:
            return self._captures_from(*self.chain)
        mine = [(r, c) for r in range(SIZE) for c in range(SIZE) if owner(self.board[r][c]) == self.turn]
        captures = [m for r, c in mine for m in self._captures_from(r, c)]
        if captures:
            return captures
        return [m for r, c in mine for m in self._steps_from(r, c)]

    def moves_from(self, square) -> list[Move]:
        square = tuple(square)
        return [m for m in self.legal_moves() if m[0] == square]

    # ----- actions
    def move(self, start, end) -> Move:
        if self.winner:
            raise IllegalMove("The game is over.")
        start, end = tuple(start), tuple(end)
        legal = self.legal_moves()
        match = next((m for m in legal if m[0] == start and m[1] == end), None)
        if match is None:
            if any(m[2] for m in legal):
                raise IllegalMove("You must capture when you can.")
            raise IllegalMove("That piece cannot move there.")
        (r0, c0), (r1, c1), captured = match
        piece = self.board[r0][c0]
        self.board[r0][c0] = None
        self.board[r1][c1] = piece
        self.last_move = match
        crowned = False
        if piece == "b" and r1 == 0:
            self.board[r1][c1], crowned = "B", True
        elif piece == "t" and r1 == SIZE - 1:
            self.board[r1][c1], crowned = "T", True
        if captured:
            self.board[captured[0]][captured[1]] = None
            self.quiet_moves = 0
            if not crowned and self._captures_from(r1, c1):
                self.chain = (r1, c1)  # same player jumps again
                return match
        else:
            self.quiet_moves += 1
        self.chain = None
        self.turn = other(self.turn)
        self._check_end()
        return match

    def _check_end(self) -> None:
        if not self.legal_moves():
            self.winner = other(self.turn)
        elif self.quiet_moves >= QUIET_LIMIT:
            bottom, top = self.count(BOTTOM), self.count(TOP)
            self.winner = DRAW if bottom == top else (BOTTOM if bottom > top else TOP)

    # ----- computer player
    def _score(self, side: str) -> float:
        total = 0.0
        for row in range(SIZE):
            for col in range(SIZE):
                piece = self.board[row][col]
                if piece is None:
                    continue
                value = 1.7 if piece.isupper() else 1.0 + (row if piece == "t" else SIZE - 1 - row) * 0.03
                total += value if owner(piece) == side else -value
        return total

    def _search(self, depth: int, side: str, alpha: float, beta: float) -> float:
        if self.winner == side:
            return 100 + depth
        if self.winner == DRAW:
            return 0
        if self.winner:
            return -100 - depth
        if depth <= 0:
            return self._score(side)
        maximising = self.turn == side
        best = -1e9 if maximising else 1e9
        for start, end, _ in self.legal_moves():
            trial = self.clone()
            trial.move(start, end)
            score = trial._search(depth - 1, side, alpha, beta)
            if maximising:
                best, alpha = max(best, score), max(alpha, score)
            else:
                best, beta = min(best, score), min(beta, score)
            if beta <= alpha:
                break
        return best

    def bot_move(self, rng: random.Random | None = None, depth: int = 2, blunder: float = 0.0) -> Move:
        """Choose and play one move (one jump of a chain) for the side to move."""
        rng = rng or random.Random()
        moves = self.legal_moves()
        if not moves:
            raise IllegalMove("The game is over.")
        if rng.random() < blunder:
            start, end, _ = rng.choice(moves)
            return self.move(start, end)
        side = self.turn
        scored = []
        for start, end, _ in moves:
            trial = self.clone()
            trial.move(start, end)
            scored.append((trial._search(depth, side, -1e9, 1e9), (start, end)))
        best = max(score for score, _ in scored)
        start, end = rng.choice([move for score, move in scored if score >= best - 0.01])
        return self.move(start, end)
