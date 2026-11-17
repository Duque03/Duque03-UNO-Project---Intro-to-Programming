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
    game.pending, game.pending_value, game.uno_due = 0, None, None


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
    game.hands["A"] = [("yellow", "5")]  # A cannot answer with a +2
    game.play("ME", ("red", "draw2"))
    assert (game.current, game.pending) == ("A", 2)
    game.draw("A")
    assert len(game.hands["A"]) == 3
    assert (game.current, game.pending) == ("B", 0)


def test_wild_draw_four_sets_colour_and_gives_four_cards():
    game = make_game()
    set_up(game, [("wild", "wild4"), ("blue", "1")], ("red", "9"))
    game.hands["A"] = [("yellow", "5")]
    game.play("ME", ("wild", "wild4"), colour="green")
    assert game.colour == "green"
    assert (game.current, game.pending) == ("A", 4)
    game.draw("A")
    assert len(game.hands["A"]) == 5
    assert game.current == "B"


def test_playing_the_last_card_wins():
    game = make_game()
    set_up(game, [("red", "5")], ("red", "9"))
    game.play("ME", ("red", "5"))
    assert game.winner == "ME"


def test_drawing_goes_on_until_a_card_can_be_played():
    game = make_game()
    set_up(game, [("blue", "1")], ("red", "9"))
    game.deck += [("red", "3"), ("green", "4"), ("green", "3")]  # drawn from the end: green 3, green 4, red 3
    assert game.draw("ME") == [("green", "3"), ("green", "4"), ("red", "3")]
    assert game.current == "ME"
    assert game.playable_cards("ME") == [("red", "3")]


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
    game.discard = [("green", "2"), ("red", "4"), ("red", "9")]
    game.deck = []
    drawn = game.draw("ME")
    assert set(drawn) <= {("green", "2"), ("red", "4")}
    assert ("red", "4") in drawn  # the refilled deck holds a playable card, so the draw stops there
    assert game.top == ("red", "9")


def test_when_no_card_is_left_anywhere_the_turn_passes():
    game = make_game()
    set_up(game, [("blue", "1")], ("red", "9"))
    game.discard, game.deck = [("red", "9")], []
    assert game.draw("ME") == []
    assert game.current == "A"


# ---- house rules: several equal cards at once

def test_several_cards_with_the_same_number_go_together_and_the_last_one_sets_the_colour():
    game = make_game()
    set_up(game, [("red", "4"), ("green", "4"), ("yellow", "4"), ("blue", "1")], ("red", "9"))
    game.play("ME", [("red", "4"), ("green", "4"), ("yellow", "4")])
    assert game.hands["ME"] == [("blue", "1")]
    assert (game.top, game.colour, game.current) == (("yellow", "4"), "yellow", "A")


def test_the_first_card_must_match_and_a_wrong_play_changes_nothing():
    game = make_game()
    set_up(game, [("red", "4"), ("green", "4")], ("red", "9"))
    with pytest.raises(IllegalMove):
        game.play("ME", [("green", "4"), ("red", "4")])
    assert game.hands["ME"] == [("red", "4"), ("green", "4")]
    assert (game.top, game.current) == (("red", "9"), "ME")


def test_cards_with_different_numbers_cannot_go_together():
    game = make_game()
    set_up(game, [("red", "4"), ("red", "5")], ("red", "9"))
    with pytest.raises(IllegalMove):
        game.play("ME", [("red", "4"), ("red", "5")])


def test_you_cannot_play_the_same_card_twice():
    game = make_game()
    set_up(game, [("red", "4"), ("blue", "1")], ("red", "9"))
    with pytest.raises(IllegalMove):
        game.play("ME", [("red", "4"), ("red", "4")])


def test_three_skips_with_four_players_and_you_play_again():
    game = make_game()
    set_up(game, [("red", "skip"), ("blue", "skip"), ("green", "skip"), ("blue", "1")], ("red", "9"))
    game.play("ME", [("red", "skip"), ("blue", "skip"), ("green", "skip")])
    assert game.current == "ME"


def test_two_skips_skip_two_players():
    game = make_game()
    set_up(game, [("red", "skip"), ("blue", "skip"), ("blue", "1")], ("red", "9"))
    game.play("ME", [("red", "skip"), ("blue", "skip")])
    assert game.current == "C"


def test_two_reverses_cancel_out():
    game = make_game()
    set_up(game, [("red", "reverse"), ("blue", "reverse"), ("blue", "1")], ("red", "9"))
    game.play("ME", [("red", "reverse"), ("blue", "reverse")])
    assert (game.direction, game.current) == (1, "A")


def test_several_draw_twos_add_up():
    game = make_game()
    set_up(game, [("red", "draw2"), ("blue", "draw2"), ("blue", "1")], ("red", "9"))
    game.hands["A"] = [("yellow", "5")]
    game.play("ME", [("red", "draw2"), ("blue", "draw2")])
    assert (game.current, game.pending, game.colour) == ("A", 4, "blue")


def test_several_wilds_share_one_colour_and_need_one():
    game = make_game()
    set_up(game, [("wild", "wild"), ("wild", "wild"), ("blue", "1")], ("red", "9"))
    with pytest.raises(IllegalMove):
        game.play("ME", [("wild", "wild"), ("wild", "wild")])
    game.play("ME", [("wild", "wild"), ("wild", "wild")], colour="blue")
    assert (game.colour, game.current) == ("blue", "A")


def test_after_drawing_the_play_starts_with_the_drawn_card_and_may_add_its_twins():
    game = make_game()
    set_up(game, [("blue", "3"), ("green", "1")], ("red", "9"))
    game.deck.append(("red", "3"))
    game.draw("ME")
    with pytest.raises(IllegalMove):
        game.play("ME", [("blue", "3"), ("red", "3")])
    game.play("ME", [("red", "3"), ("blue", "3")])
    assert game.colour == "blue"


# ---- house rules: stacking

def test_a_draw_two_can_be_answered_with_a_draw_two():
    game = make_game()
    set_up(game, [("red", "draw2"), ("blue", "1")], ("red", "9"))
    game.hands["A"] = [("green", "draw2"), ("yellow", "5")]
    game.hands["B"] = [("yellow", "7")]
    game.play("ME", ("red", "draw2"))
    game.play("A", ("green", "draw2"))
    assert (game.current, game.pending) == ("B", 4)
    game.draw("B")
    assert len(game.hands["B"]) == 5
    assert (game.current, game.pending) == ("C", 0)


def test_facing_draw_cards_only_the_same_kind_can_be_played():
    game = make_game()
    set_up(game, [("red", "draw2"), ("blue", "1")], ("red", "9"))
    game.hands["A"] = [("red", "5"), ("wild", "wild4"), ("wild", "wild")]
    game.play("ME", ("red", "draw2"))
    for card in (("red", "5"), ("wild", "wild4"), ("wild", "wild")):
        with pytest.raises(IllegalMove):
            game.play("A", card, colour="red")
    assert (game.current, game.pending) == ("A", 2)


def test_a_wild_draw_four_can_be_answered_with_several_wild_draw_fours():
    game = make_game()
    set_up(game, [("wild", "wild4"), ("blue", "1")], ("red", "9"))
    game.hands["A"] = [("wild", "wild4"), ("wild", "wild4"), ("yellow", "5")]
    game.play("ME", ("wild", "wild4"), colour="green")
    game.play("A", [("wild", "wild4"), ("wild", "wild4")], colour="yellow")
    assert (game.current, game.pending, game.colour) == ("B", 12, "yellow")


def test_passing_is_not_allowed_while_facing_draw_cards():
    game = make_game()
    set_up(game, [("red", "draw2"), ("blue", "1")], ("red", "9"))
    game.hands["A"] = [("yellow", "5")]
    game.play("ME", ("red", "draw2"))
    with pytest.raises(IllegalMove):
        game.pass_turn("A")


# ---- house rules: UNO

def test_going_down_to_one_card_means_uno_is_due_and_saying_it_clears_it():
    game = make_game()
    set_up(game, [("red", "5"), ("blue", "1")], ("red", "9"))
    game.play("ME", ("red", "5"))
    assert game.uno_due == "ME"
    assert game.call_uno("ME") is True
    assert game.uno_due is None
    assert len(game.hands["ME"]) == 1


def test_forgetting_uno_costs_two_cards():
    game = make_game()
    set_up(game, [("red", "5"), ("blue", "1")], ("red", "9"))
    game.play("ME", ("red", "5"))
    game.miss_uno("ME")
    assert game.uno_due is None
    assert len(game.hands["ME"]) == 3


def test_saying_uno_when_it_is_not_due_does_nothing():
    game = make_game()
    set_up(game, [("red", "5"), ("blue", "1"), ("blue", "2")], ("red", "9"))
    game.play("ME", ("red", "5"))
    assert game.uno_due is None
    assert game.call_uno("ME") is False
    game.miss_uno("ME")
    assert len(game.hands["ME"]) == 2


def test_playing_several_cards_down_to_one_also_needs_uno():
    game = make_game()
    set_up(game, [("red", "4"), ("green", "4"), ("blue", "1")], ("red", "9"))
    game.play("ME", [("red", "4"), ("green", "4")])
    assert game.uno_due == "ME"


def test_winning_with_the_last_card_needs_no_uno():
    game = make_game()
    set_up(game, [("red", "4"), ("green", "4")], ("red", "9"))
    game.play("ME", [("red", "4"), ("green", "4")])
    assert (game.winner, game.uno_due) == ("ME", None)


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

def test_a_bot_answers_a_draw_two_when_it_can():
    game = make_game()
    set_up(game, [("red", "draw2"), ("blue", "1")], ("red", "9"))
    game.hands["A"] = [("green", "draw2"), ("yellow", "5"), ("yellow", "6")]
    game.play("ME", ("red", "draw2"))
    game.bot_turn("A")
    assert (game.current, game.pending) == ("B", 4)


def test_a_bot_plays_all_the_twins_of_its_card():
    game = make_game()
    set_up(game, [("blue", "1")], ("red", "9"))
    game.turn = 1
    game.hands["A"] = [("red", "7"), ("green", "7"), ("blue", "7"), ("yellow", "2")]
    game.bot_turn("A")
    assert game.hands["A"] == [("yellow", "2")]


def test_a_bot_says_uno_unless_it_forgets():
    for forget, cards in ((0.0, 1), (1.0, 3)):
        game = make_game()
        set_up(game, [("blue", "1")], ("red", "9"))
        game.turn = 1
        game.hands["A"] = [("red", "7"), ("yellow", "2")]
        game.bot_turn("A", forget_uno=forget)
        assert len(game.hands["A"]) == cards
        assert game.uno_due is None

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


# ---- how well the bots play (config.py: UNO_BOT_TWINS, UNO_BOT_STACK, UNO_BOT_SMART)

def _bot_to_play(game, hand, top):
    set_up(game, [("blue", "1")], top)
    game.hands["A"] = list(hand)
    game.turn = 1  # A plays


def test_bot_that_never_plays_twins_plays_one_card():
    game = make_game()
    _bot_to_play(game, [("red", "5"), ("green", "5"), ("yellow", "5"), ("blue", "9")], ("red", "2"))
    game.bot_turn("A", twins=0.0)
    assert len(game.hands["A"]) == 3
    assert game.top == ("red", "5")


def test_bot_that_always_plays_twins_plays_them_all():
    game = make_game()
    _bot_to_play(game, [("red", "5"), ("green", "5"), ("yellow", "5"), ("blue", "9")], ("red", "2"))
    game.bot_turn("A", twins=1.0)
    assert game.hands["A"] == [("blue", "9")] or len(game.hands["A"]) == 1


def test_bot_that_never_stacks_takes_the_cards():
    game = make_game()
    _bot_to_play(game, [("red", "draw2"), ("blue", "9")], ("green", "draw2"))
    game.pending, game.pending_value = 2, "draw2"
    game.bot_turn("A", stack=0.0)
    assert len(game.hands["A"]) == 4
    assert game.pending == 0 and game.current != "A"


def test_bot_that_always_stacks_passes_the_cards_on():
    game = make_game()
    _bot_to_play(game, [("red", "draw2"), ("blue", "9")], ("green", "draw2"))
    game.pending, game.pending_value = 2, "draw2"
    game.bot_turn("A", stack=1.0)
    assert game.pending == 4
    assert ("red", "draw2") not in game.hands["A"]


def test_careless_bots_still_only_play_legal_cards():
    for seed in range(40):
        game = make_game(seed)
        game.turn = 1
        before, played_from = game.top, len(game.discard)
        game.bot_turn(game.current, twins=0.3, stack=0.3, smart=0.0)
        played = game.discard[played_from:]
        if played:  # the first card matches the card before it, the rest are its twins
            assert played[0][0] in (before[0], "wild") or played[0][1] == before[1]
            assert all(card[1] == played[0][1] for card in played)


# ---- the player's time runs out (auto_turn)

def test_time_out_draws_and_passes_the_turn():
    game = make_game()
    set_up(game, [("red", "5"), ("blue", "1")], ("red", "9"))
    game.auto_turn("ME")
    assert len(game.hands["ME"]) >= 3
    assert game.current == "A"
    assert game.drawn_card is None


def test_time_out_with_cards_stacked_on_you_takes_them_all():
    game = make_game()
    set_up(game, [("red", "5")], ("green", "draw2"))
    game.pending, game.pending_value = 4, "draw2"
    game.auto_turn("ME")
    assert len(game.hands["ME"]) == 5
    assert game.pending == 0 and game.current == "A"


def test_time_out_after_drawing_just_passes():
    game = make_game()
    set_up(game, [("red", "5")], ("red", "9"))
    game.drawn_card = ("red", "5")
    game.auto_turn("ME")
    assert game.hands["ME"] == [("red", "5")]
    assert game.current == "A"


def test_time_out_is_refused_when_it_is_not_your_turn():
    game = make_game()
    set_up(game, [("red", "5")], ("red", "9"))
    game.turn = 1
    with pytest.raises(IllegalMove):
        game.auto_turn("ME")
