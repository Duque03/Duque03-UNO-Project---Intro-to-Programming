"""Online lobbies (docs/game-design.md, section 8): codes, joining, the host, playing and the 15-second clock."""

import random

import pytest

from arcade.logic.connect4 import RED
from arcade.logic.lobby import (
    MAX_PLAYERS, TURN_SECONDS, UNO_INTRO_SECONDS, UNO_SECONDS, LobbyError, Lobbies, online_coins,
)
from arcade.logic.uno import IllegalMove as UnoIllegal


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def _player(name):
    return {"name": name, "look": ("#f0c8a4", "#3b5b8f", None, None), "tag": None}


@pytest.fixture
def setup():
    clock = Clock()
    return Lobbies(random.Random(1), clock), clock


def test_creating_a_lobby_gives_a_four_letter_code(setup):
    lobbies, _ = setup
    code = lobbies.create(_player("ANA"))
    assert len(code) == 4 and code.isalpha() and code.isupper()
    lobby = lobbies.get(code)
    assert lobby.host == "ANA" and lobby.names() == ["ANA"]


def test_friends_join_with_the_code_typed_any_way(setup):
    lobbies, _ = setup
    code = lobbies.create(_player("ANA"))
    lobbies.join(f" {code.lower()} ", _player("BRUNO"))
    assert lobbies.get(code).names() == ["ANA", "BRUNO"]


def test_a_wrong_code_is_refused(setup):
    lobbies, _ = setup
    lobbies.create(_player("ANA"))
    with pytest.raises(LobbyError):
        lobbies.join("ZZZZ", _player("BRUNO"))


def test_a_lobby_holds_at_most_four_players(setup):
    lobbies, _ = setup
    code = lobbies.create(_player("P0"))
    for k in range(1, MAX_PLAYERS):
        lobbies.join(code, _player(f"P{k}"))
    with pytest.raises(LobbyError):
        lobbies.join(code, _player("LATE"))
    assert len(lobbies.get(code).players) == MAX_PLAYERS


def test_joining_twice_does_not_add_the_player_twice(setup):
    lobbies, _ = setup
    code = lobbies.create(_player("ANA"))
    lobbies.join(code, _player("ANA"))
    assert lobbies.get(code).names() == ["ANA"]


def test_only_the_host_picks_and_starts_the_game(setup):
    lobbies, _ = setup
    code = lobbies.create(_player("ANA"))
    lobbies.join(code, _player("BRUNO"))
    with pytest.raises(LobbyError):
        lobbies.choose(code, "BRUNO", "uno")
    lobbies.choose(code, "ANA", "uno")
    with pytest.raises(LobbyError):
        lobbies.start(code, "BRUNO")
    lobbies.start(code, "ANA")
    assert lobbies.get(code).table is not None


def test_a_game_needs_the_right_number_of_players(setup):
    lobbies, _ = setup
    code = lobbies.create(_player("ANA"))
    lobbies.choose(code, "ANA", "uno")
    with pytest.raises(LobbyError):
        lobbies.start(code, "ANA")  # alone: UNO needs 2 to 4
    for name in ("B", "C"):
        lobbies.join(code, _player(name))
    lobbies.choose(code, "ANA", "connect4")
    with pytest.raises(LobbyError):
        lobbies.start(code, "ANA")  # three players: Connect Four needs exactly 2
    lobbies.choose(code, "ANA", "uno")
    lobbies.start(code, "ANA")


def test_nobody_joins_in_the_middle_of_a_game(setup):
    lobbies, _ = setup
    code = lobbies.create(_player("ANA"))
    lobbies.join(code, _player("BRUNO"))
    lobbies.choose(code, "ANA", "connect4")
    lobbies.start(code, "ANA")
    with pytest.raises(LobbyError):
        lobbies.join(code, _player("CARLA"))


def _connect4(setup):
    lobbies, clock = setup
    code = lobbies.create(_player("ANA"))
    lobbies.join(code, _player("BRUNO"))
    lobbies.choose(code, "ANA", "connect4")
    lobbies.start(code, "ANA")
    return lobbies, clock, code


def test_the_host_plays_first_and_moves_alternate(setup):
    lobbies, _, code = _connect4(setup)
    lobby = lobbies.get(code)
    assert lobby.current() == "ANA" and lobby.side_of("ANA") == RED
    lobbies.act(code, "ANA", "drop", col=3)
    assert lobbies.get(code).current() == "BRUNO"


def test_playing_out_of_turn_is_refused_and_changes_nothing(setup):
    lobbies, _, code = _connect4(setup)
    before = lobbies.get(code)
    with pytest.raises(LobbyError):
        lobbies.act(code, "BRUNO", "drop", col=3)
    after = lobbies.get(code)
    assert after.table.board == before.table.board and after.current() == "ANA"


def test_every_move_changes_the_version(setup):
    lobbies, _, code = _connect4(setup)
    version = lobbies.version(code)
    lobbies.act(code, "ANA", "drop", col=0)
    assert lobbies.version(code) == version + 1


def test_four_in_a_row_ends_the_game_with_a_winner(setup):
    lobbies, _, code = _connect4(setup)
    for ana, bruno in ((0, 6), (1, 6), (2, 5)):
        lobbies.act(code, "ANA", "drop", col=ana)
        lobbies.act(code, "BRUNO", "drop", col=bruno)
    lobbies.act(code, "ANA", "drop", col=3)
    lobby = lobbies.get(code)
    assert lobby.result == {"winner": "ANA"} and lobby.current() is None
    assert online_coins(lobby.result, "ANA") == 15 and online_coins(lobby.result, "BRUNO") == 0


def test_when_time_is_up_the_game_plays_for_the_player(setup):
    lobbies, clock, code = _connect4(setup)
    clock.now += TURN_SECONDS + 1
    lobby = lobbies.get(code)
    assert lobby.current() == "BRUNO"  # a disc was dropped for ANA
    assert sum(cell is not None for row in lobby.table.board for cell in row) == 1


def test_leaving_in_the_middle_ends_the_game_and_passes_on_the_host(setup):
    lobbies, _, code = _connect4(setup)
    lobbies.leave(code, "ANA")
    lobby = lobbies.get(code)
    assert lobby.host == "BRUNO" and lobby.result == {"winner": None, "left": "ANA"}


def test_a_player_who_left_is_still_drawn_at_the_table(setup):
    lobbies, _, code = _uno(setup)
    lobbies.leave(code, "BRUNO")
    lobby = lobbies.get(code)
    assert lobby.player("BRUNO")["name"] == "BRUNO" and "BRUNO" not in lobby.names()
    assert lobby.result == {"winner": None, "left": "BRUNO"}


def test_the_last_player_to_leave_closes_the_lobby(setup):
    lobbies, _ = setup
    code = lobbies.create(_player("ANA"))
    lobbies.leave(code, "ANA")
    assert lobbies.version(code) is None


def test_the_host_takes_everyone_back_to_the_lobby_after_a_game(setup):
    lobbies, _, code = _connect4(setup)
    with pytest.raises(LobbyError):
        lobbies.back_to_lobby(code, "ANA")  # not before the game is over
    lobbies.leave(code, "BRUNO")
    lobbies.back_to_lobby(code, "ANA")
    assert lobbies.get(code).table is None


def _uno(setup, names=("ANA", "BRUNO", "CARLA")):
    lobbies, clock = setup
    code = lobbies.create(_player(names[0]))
    for name in names[1:]:
        lobbies.join(code, _player(name))
    lobbies.choose(code, names[0], "uno")
    lobbies.start(code, names[0])
    with lobbies._lock:  # these tests start with the first player (the real start is picked at random)
        lobbies._find(code).table.turn = 0
    return lobbies, clock, code


def test_anyone_can_start_online_uno_and_the_deal_gets_its_time(setup):
    _, clock = setup
    starters = set()
    for seed in range(12):
        lobbies = Lobbies(random.Random(seed), clock=clock)
        code = lobbies.create(_player("ANA"))
        lobbies.join(code, _player("BRUNO"))
        lobbies.choose(code, "ANA", "uno")
        lobbies.start(code, "ANA")
        lobby = lobbies.get(code)
        starters.add(lobby.current())
        assert lobby.deadline == clock() + TURN_SECONDS + UNO_INTRO_SECONDS
    assert starters == {"ANA", "BRUNO"}


def test_uno_online_has_no_bots_and_checks_the_rules(setup):
    lobbies, _, code = _uno(setup)
    lobby = lobbies.get(code)
    assert lobby.table.players == ["ANA", "BRUNO", "CARLA"]
    bad = next((c for c in lobby.table.hands["ANA"] if not lobby.table.can_play(c)), None)
    if bad:
        with pytest.raises(UnoIllegal):
            lobbies.act(code, "ANA", "play", cards=[bad])
    lobbies.act(code, "ANA", "draw")
    assert lobbies.get(code).current() in ("ANA", "BRUNO")


def test_forgetting_uno_online_costs_two_cards(setup):
    lobbies, clock, code = _uno(setup)
    with lobbies._lock:  # put ANA one card from UNO
        lobby = lobbies._find(code)
        lobby.table.hands["ANA"] = [("red", "5"), ("red", "6")]
        lobby.table.discard, lobby.table.colour = [("red", "9")], "red"
    lobbies.act(code, "ANA", "play", cards=[("red", "5")])
    clock.now += UNO_SECONDS + 1
    assert len(lobbies.get(code).table.hands["ANA"]) == 3


def test_saying_uno_in_time_keeps_the_card_count(setup):
    lobbies, clock, code = _uno(setup)
    with lobbies._lock:
        lobby = lobbies._find(code)
        lobby.table.hands["ANA"] = [("red", "5"), ("red", "6")]
        lobby.table.discard, lobby.table.colour = [("red", "9")], "red"
    lobbies.act(code, "ANA", "play", cards=[("red", "5")])
    lobbies.act(code, "ANA", "uno")
    clock.now += UNO_SECONDS + 1
    assert len(lobbies.get(code).table.hands["ANA"]) == 1


def test_online_uno_prizes_follow_the_places():
    result = {"places": ["A", "B", "C", "D"]}
    assert [online_coins(result, name) for name in "ABCD"] == [15, 8, 4, 0]
    assert [online_coins({"places": ["A", "B"]}, name) for name in "AB"] == [15, 0]
    assert online_coins({"winner": None}, "A") == 0


def test_codes_only_use_letters_that_can_be_typed_on_the_join_screen(setup):
    from arcade.logic.lobby import CODE_LETTERS
    assert not set("CRMFIO") & set(CODE_LETTERS)
    lobbies, _ = setup
    for k in range(30):
        assert set(lobbies.create(_player(f"P{k}"))) <= set(CODE_LETTERS)


def _ana_down_to_one(setup):
    lobbies, clock, code = _uno(setup)
    with lobbies._lock:
        lobby = lobbies._find(code)
        lobby.table.hands["ANA"] = [("red", "5"), ("red", "6")]
        lobby.table.discard, lobby.table.colour = [("red", "9")], "red"
    lobbies.act(code, "ANA", "play", cards=[("red", "5")])
    return lobbies, clock, code


def _answer(lobbies, code, name, right):
    truth = lobbies.get(code).duel.truth
    lobbies.act(code, name, "answer", yes=truth if right else not truth)


def test_cutting_a_uno_online_starts_a_face_off_and_freezes_the_game(setup):
    lobbies, clock, code = _ana_down_to_one(setup)
    lobbies.act(code, "CARLA", "cut")
    lobby = lobbies.get(code)
    assert (lobby.duel.holder, lobby.duel.cutter) == ("ANA", "CARLA")
    with pytest.raises(LobbyError):
        lobbies.act(code, "BRUNO", "draw")  # nothing else moves during the face-off
    with pytest.raises(LobbyError):
        lobbies.act(code, "BRUNO", "answer", yes=True)  # only the two players answer
    clock.now += UNO_SECONDS + 1
    assert len(lobbies.get(code).table.hands["ANA"]) == 1  # no "forgot UNO" while the face-off runs


def test_losing_the_face_off_online_with_uno_draws_7(setup):
    lobbies, clock, code = _ana_down_to_one(setup)
    lobbies.act(code, "BRUNO", "cut")
    _answer(lobbies, code, "ANA", right=False)
    _answer(lobbies, code, "BRUNO", right=True)
    clock.now += 3  # the answers are shown, then it is over
    lobby = lobbies.get(code)
    assert lobby.duel is None and len(lobby.table.hands["ANA"]) == 8 and lobby.table.uno_due is None


def test_the_cutter_losing_online_means_the_uno_stands(setup):
    lobbies, clock, code = _ana_down_to_one(setup)
    lobbies.act(code, "BRUNO", "cut")
    _answer(lobbies, code, "ANA", right=True)
    _answer(lobbies, code, "BRUNO", right=False)
    clock.now += 3
    lobby = lobbies.get(code)
    assert lobby.duel is None and len(lobby.table.hands["ANA"]) == 1 and lobby.table.uno_due is None


def test_a_uno_cannot_be_cut_by_its_owner_or_after_it_was_said(setup):
    lobbies, clock, code = _ana_down_to_one(setup)
    with pytest.raises(LobbyError):
        lobbies.act(code, "ANA", "cut")
    lobbies.act(code, "ANA", "uno")
    with pytest.raises(LobbyError):
        lobbies.act(code, "BRUNO", "cut")
