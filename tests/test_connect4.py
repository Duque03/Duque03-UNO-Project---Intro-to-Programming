import random

import pytest

from arcade.logic.connect4 import COLS, DRAW, RED, ROWS, YELLOW, Connect4Game, IllegalMove


def play(game, columns):
    for col in columns:
        game.drop(col)


def test_disc_lands_on_the_bottom_and_turn_changes():
    game = Connect4Game()
    assert game.drop(3) == ROWS - 1
    assert game.board[ROWS - 1][3] == RED
    assert game.turn == YELLOW


def test_discs_stack_up():
    game = Connect4Game()
    play(game, [3, 3])
    assert game.board[ROWS - 2][3] == YELLOW


def test_four_in_a_column_wins():
    game = Connect4Game()
    play(game, [0, 1, 0, 1, 0, 1, 0])
    assert game.winner == RED
    assert len(game.win_cells) == 4


def test_four_in_a_row_wins():
    game = Connect4Game()
    play(game, [0, 0, 1, 1, 2, 2, 3])
    assert game.winner == RED


def test_diagonal_wins():
    game = Connect4Game()
    play(game, [0, 1, 1, 2, 2, 3, 2, 3, 3, 6, 3])
    assert game.winner == RED


def test_full_board_without_a_line_is_a_draw():
    game = Connect4Game()
    order = [0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0,
             2, 3, 2, 3, 2, 3, 3, 2, 3, 2, 3, 2,
             4, 5, 4, 5, 4, 5, 5, 4, 5, 4, 5, 4,
             6, 6, 6, 6, 6, 6]
    play(game, order)
    assert game.winner == DRAW
    assert game.legal_columns() == []


def test_full_column_is_rejected_and_board_is_unchanged():
    game = Connect4Game()
    play(game, [2, 2, 2, 2, 2, 2])
    snapshot = [row[:] for row in game.board]
    turn = game.turn
    with pytest.raises(IllegalMove):
        game.drop(2)
    assert game.board == snapshot
    assert game.turn == turn


@pytest.mark.parametrize("col", [-1, COLS, 99, "3", None])
def test_column_that_does_not_exist_is_rejected(col):
    game = Connect4Game()
    with pytest.raises(IllegalMove):
        game.drop(col)


def test_no_moves_after_the_game_is_over():
    game = Connect4Game()
    play(game, [0, 1, 0, 1, 0, 1, 0])
    with pytest.raises(IllegalMove):
        game.drop(4)


def test_bot_takes_a_winning_move():
    game = Connect4Game()
    play(game, [0, 6, 1, 6, 2, 5])  # red has three in a row on the bottom
    assert game.bot_move(random.Random(1)) == 3
    assert game.winner == RED


def test_bot_blocks_an_immediate_loss():
    game = Connect4Game()
    play(game, [0, 6, 1, 6, 2])  # yellow to move, red threatens column 3
    assert game.bot_move(random.Random(1)) == 3
    assert game.winner is None


@pytest.mark.parametrize("seed", range(10))
def test_bot_against_bot_always_ends(seed):
    rng = random.Random(seed)
    game = Connect4Game()
    for _ in range(ROWS * COLS):
        if game.winner:
            break
        game.bot_move(rng, depth=2, blunder=0.2)
    assert game.winner in (RED, YELLOW, DRAW)


def test_random_move_drops_in_a_column_that_is_not_full():
    game = Connect4Game()
    play(game, [0] * ROWS)  # column 0 is full
    for seed in range(20):
        trial = game.clone()
        col = trial.random_move(random.Random(seed))
        assert col != 0 and col in game.legal_columns()


def test_random_move_is_refused_when_the_game_is_over():
    game = Connect4Game()
    play(game, [0, 1, 0, 1, 0, 1, 0])  # red wins in column 0
    with pytest.raises(IllegalMove):
        game.random_move(random.Random(1))
