"""The end of every game, played through the real app headless (Streamlit's AppTest, tools/sim_driver.py): the last
move, the podium, PLAY AGAIN and CONTINUE must never crash (a duplicate element id once did, at the end of
Connect Four). tools/simulate_app.py plays whole random games the same way."""
import pathlib
import random
import sys
import time

import pytest
from streamlit.testing.v1 import AppTest

from arcade import bots, hubmap
from arcade import player as player_model
from arcade.logic.connect4 import RED, YELLOW, Connect4Game
from arcade.logic.uno import UnoGame
from arcade.screens import connect4 as connect4_screen

DRIVER = pathlib.Path(__file__).resolve().parent.parent / "tools" / "sim_driver.py"


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCADE_DB", str(tmp_path / "arcade.db"))
    from arcade import ui

    glow, setup = ui.GLOW, ui.setup_page
    yield _new_app()
    # the driver runs in this process: give the game back its real clock, glow and page setup for the other tests
    for name, module in list(sys.modules.items()):
        if name.startswith("arcade") and getattr(getattr(module, "time", None), "__name__", "") == "sim_clock":
            module.time = time
    ui.GLOW, ui.setup_page = glow, getattr(ui, "_sim_setup", setup)


def _new_app():
    at = AppTest.from_file(str(DRIVER), default_timeout=120)
    at.run()
    me = player_model.new_player("TESTER")
    me["look_done"] = True
    at.session_state["player"] = me
    at.session_state["hub"] = {"pos": hubmap.SPAWN, "dir": "up", "walk": None,
                               "bots": {b["name"]: {"pos": b["home"], "dir": b["dir"]} for b in bots.BOTS}}
    return at


def _start(at, game, names):
    at.session_state["match"] = {"game": game, "mode": "free", "bots": names, "others": []}
    at.session_state["_sim_start"] = True
    at.run()
    assert not at.exception, at.exception


def _press(at, key):
    next(b for b in at.button if b.key == key).click()
    at.run()
    assert not at.exception, at.exception


def _connect4_one_move_from_the_end(at, winner_side):
    """Three in a row for the given side at the bottom; the player (red) moves next."""
    game = Connect4Game()
    for col, side in ((0, RED), (6, YELLOW), (1, RED), (6, YELLOW), (2, RED), (5, YELLOW)):
        game.board[game.legal_columns() and max(r for r in range(6) if game.board[r][col] is None)][col] = side
    if winner_side == YELLOW:  # yellow has three in column 6 and red cannot stop it after its move
        game.board[max(r for r in range(6) if game.board[r][6] is None)][6] = YELLOW
    game.turn = RED
    at.session_state["game"] = game


def test_winning_connect_four_ends_on_the_podium_then_play_again_and_continue(app):
    _start(app, "connect4", ["DEAN"])
    _connect4_one_move_from_the_end(app, RED)
    app.session_state["_sim_click"] = (connect4_screen.BOARD_X + 3 * connect4_screen.CELL + 20, 300)  # column 4
    app.run()
    assert not app.exception, app.exception
    assert app.session_state["result"]["title"] == "VICTORY!" and app.session_state["result"]["podium"]
    _press(app, "connect4_again")
    assert app.session_state["result"] is None and app.session_state["screen"] == "connect4"
    _connect4_one_move_from_the_end(app, RED)
    app.session_state["_sim_click"] = (connect4_screen.BOARD_X + 3 * connect4_screen.CELL + 20, 300)
    app.run()
    _press(app, "connect4_continue")
    assert app.session_state["screen"] == "hub"


def test_losing_connect_four_ends_on_the_podium(app):
    _start(app, "connect4", ["JOHN"])  # the expert finishes its four in a row
    _connect4_one_move_from_the_end(app, YELLOW)
    app.session_state["_sim_click"] = (connect4_screen.BOARD_X + 4 * connect4_screen.CELL + 20, 300)  # not the win
    app.run()
    assert not app.exception, app.exception
    assert app.session_state["result"]["title"] == "GAME OVER"
    assert app.session_state["result"]["podium"][0]["name"] == "JOHN"


def test_the_end_of_uno_with_four_players_ends_on_the_podium(app):
    _start(app, "uno", ["DEAN", "BARK", "MANHOSA"])
    me = "TESTER"
    game = UnoGame([me, "DEAN", "BARK", "MANHOSA"], random.Random(4), start=0)
    top = game.discard[-1]
    game.hands[me] = [("red" if top[0] == "wild" else top[0], "5")]  # one card, and it fits
    game.colour = game.hands[me][0][0]
    app.session_state["game"] = game
    app.session_state["uno_intro"] = False
    app.run()
    assert not app.exception, app.exception
    game.play(me, game.hands[me])  # (the same as clicking the card and the pile)
    app.run()
    assert not app.exception, app.exception
    result = app.session_state["result"]
    assert result["podium"][0]["name"] == me and len(result["podium"]) == 4
    _press(app, "uno_continue")
    assert app.session_state["screen"] == "hub"


def test_a_screen_that_breaks_goes_back_to_the_arcade_instead_of_a_black_screen(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCADE_DB", str(tmp_path / "arcade.db"))
    monkeypatch.delenv("ARCADE_STRICT", raising=False)
    at = AppTest.from_file(str(DRIVER.parent.parent / "app.py"), default_timeout=120)
    at.run()
    me = player_model.new_player("TESTER")
    me["look_done"] = True
    at.session_state["player"] = me
    at.session_state["hub"] = {"pos": hubmap.SPAWN, "dir": "up", "walk": None,
                               "bots": {b["name"]: {"pos": b["home"], "dir": b["dir"]} for b in bots.BOTS}}
    at.session_state["match"] = {"game": "uno", "mode": "free", "bots": ["DEAN", "BARK", "JOHN"], "others": []}
    at.session_state["game"] = None  # a broken table: drawing it raises
    at.session_state["screen"] = "uno"
    at.run()
    assert not at.exception
    assert at.session_state["screen"] == "hub" and at.session_state["match"] is None
    assert any("Something went wrong" in t["text"] for t in at.session_state["_toasts"])


def test_the_pause_menu_is_quiet_and_sets_the_music_level(app):
    _start(app, "checkers", ["DEAN"])
    assert app.session_state["_track"] == "checkers"  # the game's tune from its very first run
    app.session_state["paused_from"] = "checkers"
    app.session_state["screen"] = "pause"
    app.run()
    assert not app.exception, app.exception
    assert app.session_state["_track"] == "silence"  # Esc: the music stops while the menu is open
    _press(app, "pause_music")
    assert app.session_state["player"]["music"] == "medium" and app.session_state["screen"] == "pause"
    _press(app, "pause_music")
    _press(app, "pause_music")
    assert app.session_state["player"]["music"] == "high"  # round again: high, medium, low, high
    _press(app, "pause_wardrobe")
    assert app.session_state["screen"] == "wardrobe" and app.session_state["_track"] == "silence"  # still paused
    _press(app, "wardrobe_back")
    _press(app, "pause_howto")
    assert app.session_state["screen"] == "howto" and app.session_state["_track"] == "silence"
    _press(app, "howto_back")
    _press(app, "pause_resume")
    assert app.session_state["screen"] == "checkers" and app.session_state["_track"] == "checkers"


def test_signing_in_again_keeps_the_count_of_room_key_presses(app):
    """The browser numbers E, I and Esc across the whole visit; a new sign-in must not make an old Esc look new."""
    from arcade import state

    app.session_state["hub"]["pressed"] = 7
    app.session_state["screen"] = "title"
    app.run()
    player = app.session_state["player"]
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(state, "S", app.session_state)
        patch.setattr(state, "reset_bots", lambda: None)
        state.start_session(player)
    assert app.session_state["hub"]["pressed"] == 7


def test_the_online_room_takes_players_to_their_table_and_back(app, monkeypatch):
    """The lobby is a room: the player comes in by the door, sits down, the game starts when the table is full, and
    LEAVE (or the end of the game) brings them back to the room. Esc in the room opens a menu that leaves the lobby."""
    from arcade import online
    from arcade.logic.lobby import Lobbies

    lobbies = Lobbies(random.Random(3))
    monkeypatch.setattr(online, "lobbies", lambda: lobbies)
    me = app.session_state["player"]
    code = lobbies.create(online.card(me))
    lobbies.join(code, {"name": "BRUNO", "look": bots.look(bots.get("JOHN")), "tag": None})
    app.session_state["lobby_code"] = code
    app.session_state["screen"] = "lobby"
    app.run()
    assert not app.exception, app.exception
    assert app.session_state["screen"] == "lobby" and lobbies.get(code).room["TESTER"]["pos"] is not None

    lobbies.sit(code, "TESTER", "connect4")
    lobbies.sit(code, "BRUNO", "connect4")  # 2/2: the game starts
    app.run()
    assert not app.exception, app.exception
    assert app.session_state["screen"] == "online_table" and app.session_state["online_game"] == "connect4"
    app.run()  # (the table itself, with the roulette)
    assert not app.exception, app.exception
    _press(app, "otable_leave")
    assert app.session_state["screen"] == "lobby"
    assert lobbies.get(code).tables["connect4"].result == {"winner": None, "left": "TESTER"}

    app.session_state["paused_from"] = "lobby"
    app.session_state["pause_behind"] = None
    app.session_state["screen"] = "pause"
    app.run()
    assert not app.exception, app.exception
    _press(app, "pause_leave_lobby")
    assert app.session_state["screen"] == "online" and "TESTER" not in lobbies.get(code).names()


def test_space_says_uno_offline_with_no_time_limit(app):
    _start(app, "uno", ["DEAN", "BARK", "MANHOSA"])
    game = UnoGame(["TESTER", "DEAN", "BARK", "MANHOSA"], random.Random(4), start=0)
    top = game.discard[-1]
    colour = "red" if top[0] == "wild" else top[0]
    game.hands["TESTER"] = [(colour, "5"), ("blue", "1") if colour != "blue" else ("green", "1")]
    game.colour = colour
    game.play("TESTER", [game.hands["TESTER"][0]])  # down to one card: the big UNO! button
    app.session_state["game"] = game
    app.session_state["uno_intro"] = False
    app.session_state["uno_cutter"] = None  # (no bot will cut it)
    app.run()
    assert not app.exception, app.exception
    assert game.uno_due == "TESTER"
    time.sleep(0.01)
    app.run()  # time goes by: still there, no +2
    assert app.session_state["game"].uno_due == "TESTER" and len(app.session_state["game"].hands["TESTER"]) == 1
    _press(app, "keys_uno_space")
    assert app.session_state["game"].uno_due is None and len(app.session_state["game"].hands["TESTER"]) == 1


def test_space_cuts_a_uno_online(app, monkeypatch):
    from arcade import online
    from arcade.logic.lobby import UNO_COUNTDOWN, Lobbies

    clock = [1000.0]
    lobbies = Lobbies(random.Random(5), clock=lambda: clock[0])
    monkeypatch.setattr(online, "lobbies", lambda: lobbies)
    me = app.session_state["player"]
    code = lobbies.create(online.card(me))
    lobbies.join(code, {"name": "BRUNO", "look": bots.look(bots.get("JOHN")), "tag": None})
    lobbies.join(code, {"name": "CARLA", "look": bots.look(bots.get("DEAN")), "tag": None})
    for name in ("TESTER", "BRUNO", "CARLA"):
        lobbies.sit(code, name, "uno")
    clock[0] += UNO_COUNTDOWN
    lobbies.get(code)  # (the countdown is over: UNO starts)
    with lobbies._lock:  # BRUNO is down to one card and has not said UNO
        table = lobbies._find(code).tables["uno"]
        table.table.hands["BRUNO"] = [("red", "5")]
        table.table.uno_due = "BRUNO"
    app.session_state["lobby_code"] = code
    app.session_state["online_game"] = "uno"
    app.session_state["screen"] = "online_table"
    app.session_state["ouno_intro"] = False
    app.session_state["online_round_seen"] = lobbies.get(code).tables["uno"].round
    app.run()
    assert not app.exception, app.exception
    _press(app, "keys_ouno_space")
    duel = lobbies.get(code).tables["uno"].duel
    assert duel is not None and (duel.holder, duel.cutter) == ("BRUNO", "TESTER")


def test_after_sitting_down_online_the_player_stays_on_the_chair(monkeypatch):
    """The walk to the chair is only a cutscene in the browser: afterwards the browser must be told to put the player
    on the chair (a new seq), or they would pop back to where they started while still seated."""
    from arcade import online
    from arcade.logic.lobby import Lobbies
    from arcade.screens import online_room

    lobbies = Lobbies(random.Random(1))
    monkeypatch.setattr(online, "lobbies", lambda: lobbies)
    code = lobbies.create({"name": "ANA", "look": None, "tag": None})
    lobbies.sit(code, "ANA", "uno")
    hub = {"pos": (100, 150), "dir": "up", "seq": 100000, "synced": (100, 150),
           "walk": {"id": 1, "from": (100, 150), "to": (58, 116), "dir": "down"}}
    online_room._finish_walk(code, "ANA", hub)
    target = online_room._player_target(hub)
    assert target["seq"] == 100001 and (target["x"], target["y"], target["dir"]) == (58, 116, "down")
    assert lobbies.get(code).room["ANA"]["pos"] == (58, 116)


def test_the_shop_works_from_the_online_room_and_goes_back_to_it(app, monkeypatch):
    from arcade import online
    from arcade.logic.lobby import Lobbies

    lobbies = Lobbies(random.Random(2))
    monkeypatch.setattr(online, "lobbies", lambda: lobbies)
    code = lobbies.create(online.card(app.session_state["player"]))
    app.session_state["lobby_code"] = code
    app.session_state["store_from"] = "lobby"
    app.session_state["screen"] = "store"
    app.run()
    assert not app.exception, app.exception
    _press(app, "store_back")
    assert app.session_state["screen"] == "lobby"
