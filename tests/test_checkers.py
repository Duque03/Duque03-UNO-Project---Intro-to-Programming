import random

import pytest

from arcade.logic.checkers import BOTTOM, DRAW, QUIET_LIMIT, TOP, CheckersGame, IllegalMove


def empty(turn=BOTTOM):
    return CheckersGame(first=turn, empty=True)


def test_start_position_has_twelve_pieces_each_on_dark_squares():
    game = CheckersGame()
    assert game.count(BOTTOM) == 12 and game.count(TOP) == 12
    for row in range(8):
        for col in range(8):
            if game.board[row][col]:
                assert (row + col) % 2 == 1


def test_start_has_seven_legal_moves():
    assert len(CheckersGame().legal_moves()) == 7


# ---- accepted actions

def test_man_steps_diagonally_forward_and_turn_changes():
    game = CheckersGame()
    game.move((5, 0), (4, 1))
    assert game.board[4][1] == "b" and game.board[5][0] is None
    assert game.turn == TOP


def test_capture_removes_the_jumped_piece():
    game = empty()
    game.board[4][3] = "b"
    game.board[3][4] = "t"
    game.board[0][1] = "t"
    game.move((4, 3), (2, 5))
    assert game.board[3][4] is None
    assert game.board[2][5] == "b"
    assert game.count(TOP) == 1


def test_double_jump_keeps_the_turn_until_it_is_finished():
    game = empty()
    game.board[6][1] = "b"
    game.board[5][2] = "t"
    game.board[3][4] = "t"
    game.board[0][7] = "t"
    game.move((6, 1), (4, 3))
    assert game.turn == BOTTOM and game.chain == (4, 3)
    assert [m[1] for m in game.legal_moves()] == [(2, 5)]
    game.move((4, 3), (2, 5))
    assert game.turn == TOP and game.chain is None
    assert game.count(TOP) == 1


def test_man_becomes_king_on_the_far_row():
    game = empty()
    game.board[1][2] = "b"
    game.board[7][0] = "t"
    game.move((1, 2), (0, 1))
    assert game.board[0][1] == "B"


def test_king_can_move_backwards():
    game = empty()
    game.board[2][3] = "B"
    game.board[7][0] = "t"
    game.move((2, 3), (3, 4))
    assert game.board[3][4] == "B"


def test_capturing_the_last_piece_wins():
    game = empty()
    game.board[4][3] = "b"
    game.board[3][4] = "t"
    game.move((4, 3), (2, 5))
    assert game.winner == BOTTOM


def test_player_with_no_legal_move_loses():
    game = empty()
    game.board[0][1] = "t"  # top's only piece, boxed in
    game.board[1][0] = "b"
    game.board[1][2] = "b"
    game.board[2][3] = "b"
    game.board[7][0] = "b"
    game.move((7, 0), (6, 1))
    assert game.legal_moves() == []
    assert game.winner == BOTTOM


def test_long_game_without_captures_goes_to_the_side_with_more_pieces():
    game = empty()
    game.board[7][0] = "B"
    game.board[7][2] = "B"
    game.board[0][7] = "T"
    game.quiet_moves = QUIET_LIMIT - 1
    game.move((7, 0), (6, 1))
    assert game.winner == BOTTOM


def test_long_game_with_equal_pieces_is_a_draw():
    game = empty()
    game.board[7][0] = "B"
    game.board[0][7] = "T"
    game.quiet_moves = QUIET_LIMIT - 1
    game.move((7, 0), (6, 1))
    assert game.winner == DRAW


# ---- rejected actions

def test_moving_backwards_with_a_man_is_rejected():
    game = empty()
    game.board[4][3] = "b"
    game.board[0][1] = "t"
    with pytest.raises(IllegalMove):
        game.move((4, 3), (5, 4))
    assert game.board[4][3] == "b"
    assert game.turn == BOTTOM


def test_moving_the_opponents_piece_is_rejected():
    game = CheckersGame()
    with pytest.raises(IllegalMove):
        game.move((2, 1), (3, 0))


def test_moving_onto_an_occupied_square_is_rejected():
    game = CheckersGame()
    with pytest.raises(IllegalMove):
        game.move((6, 1), (5, 0))


def test_capture_is_mandatory():
    game = empty()
    game.board[4][3] = "b"
    game.board[3][4] = "t"
    game.board[6][1] = "b"
    game.board[0][1] = "t"
    with pytest.raises(IllegalMove, match="capture"):
        game.move((6, 1), (5, 0))
    assert all(move[2] is not None for move in game.legal_moves())


def test_no_moves_after_the_game_is_over():
    game = empty()
    game.board[4][3] = "b"
    game.board[3][4] = "t"
    game.move((4, 3), (2, 5))
    with pytest.raises(IllegalMove):
        game.move((2, 5), (1, 4))


# ---- bots

def test_bot_takes_a_free_capture():
    game = empty(turn=TOP)
    game.board[3][4] = "t"
    game.board[4][3] = "b"
    game.board[7][0] = "b"
    game.bot_move(random.Random(1), depth=2)
    assert game.count(BOTTOM) == 1


@pytest.mark.parametrize("seed", range(6))
def test_bot_against_bot_always_ends(seed):
    rng = random.Random(seed)
    game = CheckersGame()
    for _ in range(2000):
        if game.winner:
            break
        game.bot_move(rng, depth=1, blunder=0.3)
    assert game.winner in (BOTTOM, TOP, DRAW)
