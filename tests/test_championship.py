import random

import pytest

from arcade.logic import championship as ch


def make():
    return ch.new_championship("ME", ["A", "B", "C"])


def test_locked_until_every_game_has_been_won_once(player):
    assert not ch.is_unlocked(player)
    player["wins"] = {"uno": 3, "checkers": 1, "connect4": 0}
    assert not ch.is_unlocked(player)
    assert ch.missing_games(player) == ["connect4"]
    player["wins"]["connect4"] = 1
    assert ch.is_unlocked(player)


def test_everyone_starts_on_zero_points():
    champ = make()
    assert champ["points"] == {"ME": 0, "A": 0, "B": 0, "C": 0}
    assert ch.current_game(champ) == "uno"


def test_a_win_is_worth_two_points():
    champ = make()
    ch.record_round(champ, [(["A"], False)])
    assert champ["points"]["A"] == 2
    assert champ["before"]["A"] == 0
    assert ch.current_game(champ) == "checkers"


def test_two_duels_give_two_winners_two_points_each():
    champ = make()
    ch.record_round(champ, [(["A"], False)])
    ch.record_round(champ, [(["ME"], False), (["B"], False)])
    assert champ["points"] == {"ME": 2, "A": 2, "B": 2, "C": 0}
    assert champ["last_winners"] == ["ME", "B"]


def test_a_tie_gives_one_point_to_both_players():
    champ = make()
    ch.record_round(champ, [(["ME", "A"], True), (["B"], False)])
    assert champ["points"] == {"ME": 1, "A": 1, "B": 2, "C": 0}
    assert champ["last_tied"] == ["ME", "A"]


def test_winning_all_three_rounds_gives_the_maximum_of_six_points():
    champ = make()
    for _ in range(3):
        ch.record_round(champ, [(["ME"], False)])
    assert champ["points"]["ME"] == ch.MAX_POINTS == 6
    assert ch.is_over(champ)
    assert ch.player_is_champion(champ)


def test_player_who_finishes_behind_is_not_champion():
    champ = make()
    ch.record_round(champ, [(["A"], False)])
    ch.record_round(champ, [(["A"], False), (["B"], False)])
    ch.record_round(champ, [(["ME"], False), (["B"], False)])
    assert ch.champions(champ) == ["A", "B"]
    assert not ch.player_is_champion(champ)


def test_sharing_first_place_counts_as_champion():
    champ = make()
    ch.record_round(champ, [(["A"], False)])
    ch.record_round(champ, [(["ME"], False), (["B"], False)])
    ch.record_round(champ, [(["ME"], False), (["A"], False)])
    assert ch.champions(champ) == ["ME", "A"]
    assert ch.player_is_champion(champ)


def test_standings_are_sorted_by_points():
    champ = make()
    ch.record_round(champ, [(["C"], False)])
    assert ch.standings(champ)[0] == ("C", 2)


def test_pairs_always_include_the_player_first_and_every_bot_once():
    champ = make()
    for seed in range(20):
        pairs = ch.draw_pairs(champ, random.Random(seed))
        assert pairs[0][0] == "ME"
        assert sorted([pairs[0][1], *pairs[1]]) == ["A", "B", "C"]


def test_simulated_duel_returns_one_of_the_two_or_a_tie():
    rng = random.Random(5)
    results = {ch.simulate_duel("A", "B", rng, tie_chance=0.3) for _ in range(200)}
    assert results == {"A", "B", None}
    assert {ch.simulate_duel("A", "B", rng) for _ in range(50)} == {"A", "B"}


# ---- rejected actions

def test_fourth_round_is_rejected():
    champ = make()
    for _ in range(3):
        ch.record_round(champ, [(["ME"], False)])
    with pytest.raises(ValueError):
        ch.record_round(champ, [(["ME"], False)])
    assert champ["points"]["ME"] == 6


def test_points_for_someone_outside_the_championship_are_rejected():
    champ = make()
    with pytest.raises(ValueError):
        ch.record_round(champ, [(["STRANGER"], False)])


def test_championship_needs_exactly_three_bots():
    with pytest.raises(ValueError):
        ch.new_championship("ME", ["A", "B"])
