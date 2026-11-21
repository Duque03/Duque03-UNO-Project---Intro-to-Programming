"""Online lobbies (docs/game-design.md, section 8): codes, joining, the room with its three tables (sit, 1/4, start),
the chat, playing and the 15-second clock."""

import random

import pytest

from arcade.logic import chat
from arcade.logic.connect4 import RED
from arcade.logic.lobby import (
    MAX_PLAYERS, STARTER_SECONDS, TURN_SECONDS, UNO_COUNTDOWN, UNO_INTRO_SECONDS, UNO_SECONDS, LobbyError, Lobbies,
    online_coins,
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


def _room(setup, names):
    lobbies, clock = setup
    code = lobbies.create(_player(names[0]))
    for name in names[1:]:
        lobbies.join(code, _player(name))
    return lobbies, clock, code


def test_creating_a_lobby_gives_a_four_letter_code(setup):
    lobbies, _ = setup
    code = lobbies.create(_player("ANA"))
    assert len(code) == 4 and code.isalpha() and code.isupper()
    lobby = lobbies.get(code)
    assert lobby.names() == ["ANA"] and lobby.room["ANA"]["pos"] is None  # (None: by the door)
    assert sorted(lobby.tables) == ["checkers", "connect4", "uno"]


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


def test_walking_in_the_room_is_seen_by_everyone(setup):
    lobbies, _, code = _room(setup, ["ANA", "BRUNO"])
    version = lobbies.version(code)
    lobbies.move(code, "BRUNO", (120, 140), "left")
    lobby = lobbies.get(code)
    assert lobby.room["BRUNO"] == {"pos": (120, 140), "dir": "left"} and lobbies.version(code) == version + 1
    lobbies.move(code, "BRUNO", (120, 140), "left")  # standing still changes nothing
    assert lobbies.version(code) == version + 1
    with pytest.raises(LobbyError):
        lobbies.move(code, "NOBODY", (1, 1), "up")


def test_a_table_shows_who_sits_and_starts_when_its_chairs_are_full(setup):
    lobbies, _, code = _room(setup, ["ANA", "BRUNO", "CARLA"])
    assert lobbies.sit(code, "ANA", "connect4") == 0
    table = lobbies.get(code).tables["connect4"]
    assert table.seated() == ["ANA"] and table.table is None  # 1/2: waiting
    assert lobbies.sit(code, "BRUNO", "connect4") == 1
    table = lobbies.get(code).tables["connect4"]
    assert table.table is not None and table.seats == ["ANA", "BRUNO"]  # 2/2: the game starts
    assert lobbies.get(code).table_of("ANA").game == "connect4"
    with pytest.raises(LobbyError):
        lobbies.sit(code, "CARLA", "connect4")  # a game is being played there


def test_a_full_table_and_an_unknown_one_are_refused(setup):
    lobbies, _, code = _room(setup, ["ANA", "BRUNO"])
    with pytest.raises(LobbyError):
        lobbies.sit(code, "ANA", "chess")
    lobbies.sit(code, "ANA", "uno")
    assert lobbies.sit(code, "ANA", "uno") == 0  # sitting again keeps the same chair


def test_getting_up_frees_the_chair_and_another_table_moves_you(setup):
    lobbies, _, code = _room(setup, ["ANA", "BRUNO"])
    lobbies.sit(code, "ANA", "checkers")
    lobbies.stand(code, "ANA")
    assert lobbies.get(code).tables["checkers"].seated() == []
    lobbies.sit(code, "ANA", "checkers")
    lobbies.sit(code, "ANA", "uno")  # sitting somewhere else gets up from the first table
    lobby = lobbies.get(code)
    assert lobby.tables["checkers"].seated() == [] and lobby.tables["uno"].seated() == ["ANA"]


def test_uno_starts_at_four_or_after_its_countdown(setup):
    lobbies, clock, code = _room(setup, ["ANA", "BRUNO", "CARLA", "DUDA"])
    for name in ("ANA", "BRUNO", "CARLA", "DUDA"):
        lobbies.sit(code, name, "uno")
    table = lobbies.get(code).tables["uno"]
    assert table.table is not None and len(table.seats) == 4  # 4/4: straight away

    lobbies, clock, code = _room(setup, ["ANA", "BRUNO", "CARLA"])
    lobbies.sit(code, "ANA", "uno")
    assert lobbies.get(code).tables["uno"].countdown is None  # alone: no countdown
    lobbies.sit(code, "BRUNO", "uno")
    assert lobbies.get(code).tables["uno"].countdown == clock() + UNO_COUNTDOWN
    clock.now += 4
    lobbies.sit(code, "CARLA", "uno")  # a third player does not make the others wait longer
    clock.now += UNO_COUNTDOWN - 4 - 1
    assert lobbies.get(code).tables["uno"].table is None
    clock.now += 2
    table = lobbies.get(code).tables["uno"]
    assert table.table is not None and table.seats == ["ANA", "BRUNO", "CARLA"]


def test_the_countdown_stops_if_too_few_are_left(setup):
    lobbies, clock, code = _room(setup, ["ANA", "BRUNO"])
    lobbies.sit(code, "ANA", "uno")
    lobbies.sit(code, "BRUNO", "uno")
    lobbies.stand(code, "BRUNO")
    clock.now += UNO_COUNTDOWN + 1
    table = lobbies.get(code).tables["uno"]
    assert table.countdown is None and table.table is None


def test_two_tables_play_at_the_same_time(setup):
    lobbies, _, code = _room(setup, ["ANA", "BRUNO", "CARLA", "DUDA"])
    for name, game in (("ANA", "checkers"), ("BRUNO", "checkers"), ("CARLA", "connect4"), ("DUDA", "connect4")):
        lobbies.sit(code, name, game)
    lobby = lobbies.get(code)
    assert lobby.tables["checkers"].playing() and lobby.tables["connect4"].playing()
    first = lobby.tables["connect4"].current()
    lobbies.act(code, first, "drop", col=3)  # a move at one table does not touch the other
    assert lobbies.get(code).tables["checkers"].table.last_move is None


def test_someone_can_join_while_a_table_plays(setup):
    lobbies, _, code = _room(setup, ["ANA", "BRUNO"])
    lobbies.sit(code, "ANA", "connect4")
    lobbies.sit(code, "BRUNO", "connect4")
    lobbies.join(code, _player("CARLA"))
    assert "CARLA" in lobbies.get(code).names()


def test_back_in_the_room_after_the_game_frees_the_table(setup):
    lobbies, _, code = _connect4(setup)
    with pytest.raises(LobbyError):
        lobbies.done(code, "ANA")  # not before the game is over
    for ana, bruno in ((0, 6), (1, 6), (2, 5)):
        lobbies.act(code, "ANA", "drop", col=ana)
        lobbies.act(code, "BRUNO", "drop", col=bruno)
    lobbies.act(code, "ANA", "drop", col=3)
    lobbies.done(code, "ANA")
    lobby = lobbies.get(code)
    assert lobby.table_of("ANA") is None and lobby.table_of("BRUNO").result == {"winner": "ANA"}
    with pytest.raises(LobbyError):
        lobbies.sit(code, "ANA", "connect4")  # BRUNO is still looking at the result
    lobbies.done(code, "BRUNO")
    lobby = lobbies.get(code)
    assert lobby.tables["connect4"].table is None and lobby.tables["connect4"].seated() == []
    lobbies.sit(code, "ANA", "connect4")  # free again


def test_the_chat_cleans_messages_and_hides_rude_words(setup):
    lobbies, clock, code = _room(setup, ["ANA", "BRUNO"])
    said = lobbies.say(code, "ANA", "  Olá, vamos jogar?  ")
    assert said["text"] == "OLA, VAMOS JOGAR?" and said["name"] == "ANA"
    clock.now += 2
    assert lobbies.say(code, "BRUNO", "what the fuck")["text"] == "WHAT THE ****"
    clock.now += 2
    assert lobbies.say(code, "BRUNO", "o meu computador")["text"] == "O MEU COMPUTADOR"  # not a rude word inside
    clock.now += 2
    assert lobbies.say(code, "ANA", emoji="laugh")["emoji"] == "laugh"
    assert [m["name"] for m in lobbies.get(code).chat] == ["ANA", "BRUNO", "BRUNO", "ANA"]


def test_the_chat_refuses_empty_messages_unknown_emojis_and_spam(setup):
    lobbies, clock, code = _room(setup, ["ANA", "BRUNO"])
    with pytest.raises(LobbyError):
        lobbies.say(code, "ANA", "   ")
    with pytest.raises(LobbyError):
        lobbies.say(code, "ANA", emoji="skull")
    lobbies.say(code, "ANA", "hi")
    with pytest.raises(LobbyError):
        lobbies.say(code, "ANA", "hi again")  # too fast
    for _ in range(chat.BURST - 1):
        clock.now += chat.GAP
        lobbies.say(code, "ANA", "ok")
    clock.now += chat.GAP
    with pytest.raises(LobbyError):
        lobbies.say(code, "ANA", "one more")  # too many in a few seconds
    clock.now += chat.BURST_SECONDS
    lobbies.say(code, "ANA", "one more")
    with pytest.raises(LobbyError):
        lobbies.say(code, "NOBODY", "hello")


def test_messages_are_short_and_written_with_the_games_letters():
    assert len(chat.clean("A" * 100)) == chat.MAX_LETTERS
    assert chat.clean("café & pão <3") == "CAFE PAO 3"
    assert chat.clean("@@@") == ""


def test_a_new_look_is_seen_by_the_others(setup):
    lobbies, _, code = _room(setup, ["ANA", "BRUNO"])
    lobbies.update_card(code, {**_player("ANA"), "tag": "gold"})
    assert lobbies.get(code).card("ANA")["tag"] == "gold"


def _connect4(setup, ana_starts=True):
    """A Connect Four game between ANA (first chair, red) and BRUNO. Either may start (a roulette shows who); with
    ana_starts the game is started again until ANA does, so the tests below can say who moves."""
    lobbies, clock = setup
    code = lobbies.create(_player("ANA"))
    lobbies.join(code, _player("BRUNO"))
    lobbies.sit(code, "ANA", "connect4")
    lobbies.sit(code, "BRUNO", "connect4")
    while ana_starts and lobbies.get(code).tables["connect4"].current() != "ANA":
        with lobbies._lock:  # start the table again
            lobby = lobbies._find(code)
            lobby.tables["connect4"].table = None
            lobbies._start(lobby, lobby.tables["connect4"])
    return lobbies, clock, code


def _c4(lobbies, code):
    return lobbies.get(code).tables["connect4"]


def test_either_player_may_start_and_moves_alternate(setup):
    starters = set()
    for _ in range(12):
        lobbies, _, code = _connect4((Lobbies(random.Random(len(starters) * 7 + _), clock=setup[1]), setup[1]),
                                     ana_starts=False)
        table = _c4(lobbies, code)
        first = table.current()
        starters.add(first)
        assert table.side_of(first) == table.table.turn and table.side_of("ANA") == RED
        lobbies.act(code, first, "drop", col=3)
        assert _c4(lobbies, code).current() == ("BRUNO" if first == "ANA" else "ANA")
    assert starters == {"ANA", "BRUNO"}


def test_playing_out_of_turn_is_refused_and_changes_nothing(setup):
    lobbies, _, code = _connect4(setup)
    before = _c4(lobbies, code)
    with pytest.raises(LobbyError):
        lobbies.act(code, "BRUNO", "drop", col=3)
    after = _c4(lobbies, code)
    assert after.table.board == before.table.board and after.current() == "ANA"


def test_someone_who_is_not_playing_cannot_move(setup):
    lobbies, _, code = _connect4(setup)
    lobbies.join(code, _player("CARLA"))
    with pytest.raises(LobbyError):
        lobbies.act(code, "CARLA", "drop", col=3)


def test_every_move_changes_the_version_and_the_tables(setup):
    lobbies, _, code = _connect4(setup)
    version, table = lobbies.version(code), lobbies.version(code, "connect4")
    lobbies.act(code, "ANA", "drop", col=0)
    assert lobbies.version(code) == version + 1 and lobbies.version(code, "connect4") == table + 1
    lobbies.move(code, "ANA", (10, 100), "up")  # walking about is not a change at the table
    assert lobbies.version(code, "connect4") == table + 1


def test_four_in_a_row_ends_the_game_with_a_winner(setup):
    lobbies, _, code = _connect4(setup)
    for ana, bruno in ((0, 6), (1, 6), (2, 5)):
        lobbies.act(code, "ANA", "drop", col=ana)
        lobbies.act(code, "BRUNO", "drop", col=bruno)
    lobbies.act(code, "ANA", "drop", col=3)
    table = _c4(lobbies, code)
    assert table.result == {"winner": "ANA"} and table.current() is None
    assert online_coins(table.result, "ANA") == 15 and online_coins(table.result, "BRUNO") == 0


def test_when_time_is_up_the_game_plays_for_the_player(setup):
    lobbies, clock, code = _connect4(setup)
    clock.now += STARTER_SECONDS + TURN_SECONDS + 1  # (the first turn starts after the roulette)
    table = _c4(lobbies, code)
    assert table.current() == "BRUNO"  # a disc was dropped for ANA
    assert sum(cell is not None for row in table.table.board for cell in row) == 1


def test_leaving_in_the_middle_ends_the_game_for_the_others(setup):
    lobbies, _, code = _connect4(setup)
    lobbies.leave(code, "ANA")
    lobby = lobbies.get(code)
    assert lobby.names() == ["BRUNO"] and lobby.table_of("BRUNO").result == {"winner": None, "left": "ANA"}


def test_quitting_a_table_ends_its_game_but_keeps_you_in_the_room(setup):
    lobbies, _, code = _connect4(setup)
    lobbies.quit_table(code, "BRUNO")
    lobby = lobbies.get(code)
    assert "BRUNO" in lobby.names() and lobby.table_of("BRUNO") is None
    assert lobby.table_of("ANA").result == {"winner": None, "left": "BRUNO"}


def test_a_player_who_left_is_still_drawn_at_the_table(setup):
    lobbies, _, code = _uno(setup)
    lobbies.leave(code, "BRUNO")
    lobby = lobbies.get(code)
    table = lobby.table_of("ANA")
    assert table.player("BRUNO")["name"] == "BRUNO" and "BRUNO" not in lobby.names()
    assert table.result == {"winner": None, "left": "BRUNO"}


def test_the_last_player_to_leave_closes_the_lobby(setup):
    lobbies, _ = setup
    code = lobbies.create(_player("ANA"))
    lobbies.leave(code, "ANA")
    assert lobbies.version(code) is None


def _uno(setup, names=("ANA", "BRUNO", "CARLA")):
    lobbies, clock = setup
    code = lobbies.create(_player(names[0]))
    for name in names[1:]:
        lobbies.join(code, _player(name))
    for name in names:
        lobbies.sit(code, name, "uno")
    clock.now += UNO_COUNTDOWN
    lobbies.get(code)  # (the countdown is over: it starts)
    with lobbies._lock:  # these tests start with the first player (the real start is picked at random)
        lobbies._find(code).tables["uno"].table.turn = 0
        lobbies._find(code).tables["uno"].deadline = clock() + TURN_SECONDS
    return lobbies, clock, code


def _t(lobbies, code):
    return lobbies.get(code).tables["uno"]


def test_anyone_can_start_online_uno_and_the_deal_gets_its_time(setup):
    _, clock = setup
    starters = set()
    for seed in range(12):
        lobbies = Lobbies(random.Random(seed), clock=clock)
        code = lobbies.create(_player("ANA"))
        lobbies.join(code, _player("BRUNO"))
        lobbies.sit(code, "ANA", "uno")
        lobbies.sit(code, "BRUNO", "uno")
        clock.now += UNO_COUNTDOWN
        table = lobbies.get(code).tables["uno"]
        starters.add(table.current())
        assert table.deadline == clock() + TURN_SECONDS + UNO_INTRO_SECONDS
    assert starters == {"ANA", "BRUNO"}


def test_uno_online_has_no_bots_and_checks_the_rules(setup):
    lobbies, _, code = _uno(setup)
    lobby = _t(lobbies, code)
    assert lobby.table.players == ["ANA", "BRUNO", "CARLA"]
    bad = next((c for c in lobby.table.hands["ANA"] if not lobby.table.can_play(c)), None)
    if bad:
        with pytest.raises(UnoIllegal):
            lobbies.act(code, "ANA", "play", cards=[bad])
    lobbies.act(code, "ANA", "draw")
    assert _t(lobbies, code).current() in ("ANA", "BRUNO")


def test_forgetting_uno_online_costs_two_cards(setup):
    lobbies, clock, code = _uno(setup)
    with lobbies._lock:  # put ANA one card from UNO
        lobby = lobbies._find(code).tables["uno"]
        lobby.table.hands["ANA"] = [("red", "5"), ("red", "6")]
        lobby.table.discard, lobby.table.colour = [("red", "9")], "red"
    lobbies.act(code, "ANA", "play", cards=[("red", "5")])
    clock.now += UNO_SECONDS + 1
    assert len(_t(lobbies, code).table.hands["ANA"]) == 3


def test_saying_uno_in_time_keeps_the_card_count(setup):
    lobbies, clock, code = _uno(setup)
    with lobbies._lock:
        lobby = lobbies._find(code).tables["uno"]
        lobby.table.hands["ANA"] = [("red", "5"), ("red", "6")]
        lobby.table.discard, lobby.table.colour = [("red", "9")], "red"
    lobbies.act(code, "ANA", "play", cards=[("red", "5")])
    lobbies.act(code, "ANA", "uno")
    clock.now += UNO_SECONDS + 1
    assert len(_t(lobbies, code).table.hands["ANA"]) == 1


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
        lobby = lobbies._find(code).tables["uno"]
        lobby.table.hands["ANA"] = [("red", "5"), ("red", "6")]
        lobby.table.discard, lobby.table.colour = [("red", "9")], "red"
    lobbies.act(code, "ANA", "play", cards=[("red", "5")])
    return lobbies, clock, code


def _answer(lobbies, code, name, right):
    truth = _t(lobbies, code).duel.truth
    lobbies.act(code, name, "answer", yes=truth if right else not truth)


def test_cutting_a_uno_online_starts_a_face_off_and_freezes_the_game(setup):
    lobbies, clock, code = _ana_down_to_one(setup)
    lobbies.act(code, "CARLA", "cut")
    lobby = _t(lobbies, code)
    assert (lobby.duel.holder, lobby.duel.cutter) == ("ANA", "CARLA")
    with pytest.raises(LobbyError):
        lobbies.act(code, "BRUNO", "draw")  # nothing else moves during the face-off
    with pytest.raises(LobbyError):
        lobbies.act(code, "BRUNO", "answer", yes=True)  # only the two players answer
    clock.now += UNO_SECONDS + 1
    assert len(_t(lobbies, code).table.hands["ANA"]) == 1  # no "forgot UNO" while the face-off runs


def test_losing_the_face_off_online_with_uno_draws_7(setup):
    lobbies, clock, code = _ana_down_to_one(setup)
    lobbies.act(code, "BRUNO", "cut")
    _answer(lobbies, code, "ANA", right=False)
    _answer(lobbies, code, "BRUNO", right=True)
    clock.now += 3  # the answers are shown, then it is over
    lobby = _t(lobbies, code)
    assert lobby.duel is None and len(lobby.table.hands["ANA"]) == 8 and lobby.table.uno_due is None


def test_the_cutter_losing_online_means_the_uno_stands(setup):
    lobbies, clock, code = _ana_down_to_one(setup)
    lobbies.act(code, "BRUNO", "cut")
    _answer(lobbies, code, "ANA", right=True)
    _answer(lobbies, code, "BRUNO", right=False)
    clock.now += 3
    lobby = _t(lobbies, code)
    assert lobby.duel is None and len(lobby.table.hands["ANA"]) == 1 and lobby.table.uno_due is None


def test_a_uno_cannot_be_cut_by_its_owner_or_after_it_was_said(setup):
    lobbies, clock, code = _ana_down_to_one(setup)
    with pytest.raises(LobbyError):
        lobbies.act(code, "ANA", "cut")
    lobbies.act(code, "ANA", "uno")
    with pytest.raises(LobbyError):
        lobbies.act(code, "BRUNO", "cut")
