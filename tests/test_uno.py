import random

import pytest

from arcade.logic.uno import COLOURS, IllegalMove, UnoGame, build_deck


def make_game(seed=1):
    return UnoGame(["ME", "A", "B", "C"], random.Random(seed))


def set_up(game, hand, top, colour=None):
    """Put the game in a known position with ME to play."""
    game.hands["ME"] = list(hand)
    game.discard = [top]
    game.colour = colour or top[0]
    game.turn = 0
    game.direction = 1
    game.drawn_card = None


def test_deck_has_108_cards():
    deck = build_deck()
    assert len(deck) == 108
    assert sum(1 for c in deck if c[0] == "wild") == 8
    assert sum(1 for c in deck if c == ("red", "0")) == 1
    assert sum(1 for c in deck if c == ("red", "7")) == 2


def test_deal_gives_seven_cards_and_a_number_on_top():
    game = make_game()
    assert all(len(hand) == 7 for hand in game.hands.values())
    assert game.top[1].isdigit()
    assert len(game.deck) + 4 * 7 + 1 == 108


# ---- accepted actions

def test_matching_colour_is_accepted_and_turn_moves_on():
    game = make_game()
    set_up(game, [("red", "5"), ("blue", "1")], ("red", "9"))
    game.play("ME", ("red", "5"))
    assert game.top == ("red", "5")
    assert game.current == "A"
    assert len(game.hands["ME"]) == 1


def test_matching_number_changes_the_colour_in_play():
    game = make_game()
    set_up(game, [("blue", "9"), ("green", "1")], ("red", "9"))
    game.play("ME", ("blue", "9"))
    assert game.colour == "blue"


def test_skip_jumps_over_the_next_player():
    game = make_game()
    set_up(game, [("red", "skip"), ("blue", "1")], ("red", "9"))
    game.play("ME", ("red", "skip"))
    assert game.current == "B"


def test_reverse_flips_the_order():
    game = make_game()
    set_up(game, [("red", "reverse"), ("blue", "1")], ("red", "9"))
    game.play("ME", ("red", "reverse"))
    assert game.direction == -1
    assert game.current == "C"


def test_reverse_with_two_players_acts_like_skip():
    game = UnoGame(["ME", "A"], random.Random(3))
    set_up(game, [("red", "reverse"), ("blue", "1")], ("red", "9"))
    game.play("ME", ("red", "reverse"))
    assert game.current == "ME"


def test_draw_two_makes_next_player_draw_and_lose_the_turn():
    game = make_game()
    set_up(game, [("red", "draw2"), ("blue", "1")], ("red", "9"))
    before = len(game.hands["A"])
    game.play("ME", ("red", "draw2"))
    assert len(game.hands["A"]) == before + 2
    assert game.current == "B"


def test_wild_draw_four_sets_colour_and_gives_four_cards():
    game = make_game()
    set_up(game, [("wild", "wild4"), ("blue", "1")], ("red", "9"))
    before = len(game.hands["A"])
    game.play("ME", ("wild", "wild4"), colour="green")
    assert game.colour == "green"
    assert len(game.hands["A"]) == before + 4
    assert game.current == "B"


def test_playing_the_last_card_wins():
    game = make_game()
    set_up(game, [("red", "5")], ("red", "9"))
    game.play("ME", ("red", "5"))
    assert game.winner == "ME"


def test_drawing_an_unplayable_card_ends_the_turn():
    game = make_game()
    set_up(game, [("blue", "1")], ("red", "9"))
    game.deck.append(("green", "3"))
    assert game.draw("ME") == ("green", "3")
    assert game.current == "A"


def test_drawing_a_playable_card_lets_you_play_it_or_pass():
    game = make_game()
    set_up(game, [("blue", "1")], ("red", "9"))
    game.deck.append(("red", "3"))
    game.draw("ME")
    assert game.current == "ME"
    assert game.playable_cards("ME") == [("red", "3")]
    game.pass_turn("ME")
    assert game.current == "A"


def test_empty_deck_is_refilled_from_the_discard_pile():
    game = make_game()
    set_up(game, [("blue", "1")], ("red", "9"))
    game.discard = [("green", "2"), ("green", "4"), ("red", "9")]
    game.deck = []
    card = game.draw("ME")
    assert card in (("green", "2"), ("green", "4"))
    assert game.top == ("red", "9")


# ---- rejected actions

def test_wrong_colour_and_number_is_rejected_and_nothing_changes():
    game = make_game()
    set_up(game, [("blue", "1"), ("green", "2")], ("red", "9"))
    with pytest.raises(IllegalMove):
        game.play("ME", ("blue", "1"))
    assert game.top == ("red", "9")
    assert len(game.hands["ME"]) == 2
    assert game.current == "ME"


def test_playing_out_of_turn_is_rejected():
    game = make_game()
    set_up(game, [("red", "5")], ("red", "9"))
    game.hands["A"] = [("red", "1"), ("red", "2")]
    with pytest.raises(IllegalMove):
        game.play("A", ("red", "1"))


def test_playing_a_card_you_do_not_hold_is_rejected():
    game = make_game()
    set_up(game, [("red", "5")], ("red", "9"))
    with pytest.raises(IllegalMove):
        game.play("ME", ("red", "6"))


def test_wild_without_a_colour_is_rejected():
    game = make_game()
    set_up(game, [("wild", "wild"), ("blue", "1")], ("red", "9"))
    with pytest.raises(IllegalMove):
        game.play("ME", ("wild", "wild"))
    with pytest.raises(IllegalMove):
        game.play("ME", ("wild", "wild"), colour="purple")
    assert ("wild", "wild") in game.hands["ME"]


def test_passing_without_drawing_is_rejected():
    game = make_game()
    set_up(game, [("blue", "1")], ("red", "9"))
    with pytest.raises(IllegalMove):
        game.pass_turn("ME")


def test_drawing_twice_in_one_turn_is_rejected():
    game = make_game()
    set_up(game, [("blue", "1")], ("red", "9"))
    game.deck.append(("red", "3"))
    game.draw("ME")
    with pytest.raises(IllegalMove):
        game.draw("ME")


def test_no_moves_after_the_game_is_over():
    game = make_game()
    set_up(game, [("red", "5")], ("red", "9"))
    game.play("ME", ("red", "5"))
    with pytest.raises(IllegalMove):
        game.draw("A")


# ---- bots

@pytest.mark.parametrize("seed", range(25))
def test_four_bots_always_finish_a_game_with_legal_moves(seed):
    game = UnoGame(["A", "B", "C", "D"], random.Random(seed))
    for _ in range(3000):
        if game.winner:
            break
        game.bot_turn(game.current)
    assert game.winner in game.players
    assert game.hands[game.winner] == []
    total = len(game.deck) + len(game.discard) + sum(len(h) for h in game.hands.values())
    assert total == 108
    assert game.colour in COLOURS
