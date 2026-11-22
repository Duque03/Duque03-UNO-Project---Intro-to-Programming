"""The title screen's order (docs/game-design.md, section 1): first who you are (CREATE A CHARACTER or I HAVE AN
ACCOUNT), a new player makes their character straight away, and only then PLAY OFFLINE or PLAY ONLINE."""

import pytest
import streamlit as st

from arcade import accounts, db, state, title_view
from arcade.art import title_layers
from arcade.screens import title


class Session(dict):
    """A stand-in for st.session_state (a dict that also has attributes)."""

    __getattr__ = dict.get

    def __setattr__(self, key, value):
        self[key] = value


class Rerun(Exception):
    pass


@pytest.fixture
def session(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCADE_DB", str(tmp_path / "arcade.db"))
    s = Session(screen="title", player=None, hub=None, match=None)
    for module in (title, state):
        monkeypatch.setattr(module, "S", s)
    monkeypatch.setattr(st, "session_state", s, raising=False)

    def rerun(*_, **__):
        raise Rerun

    monkeypatch.setattr(st, "rerun", rerun)
    return s


def _account(name, pin):
    """An account whose character is already made."""
    player = accounts.sign_up(name, pin, pin)
    player["look_done"] = True
    db.save_player(player)


def _send(fn, *args):
    with pytest.raises(Rerun):
        fn(*args)


def test_a_new_account_goes_straight_to_making_the_character_then_back_to_choose(session):
    _send(title._sign_in, {"mode": "new", "name": "Ana", "pin": "1234", "pin2": "1234"}, 1)
    assert session.screen == "create" and session.player["name"] == "ANA"
    assert session.after_create == "title"  # after "Let's play!": the title asks offline or online
    assert title_view.scene(set(), signed_in="ANA")["signedIn"] == "ANA"


def test_an_account_signs_in_and_then_chooses_offline_or_online(session):
    _account("Bruno", "2468")
    _send(title._sign_in, {"mode": "login", "name": "bruno", "pin": "2468"}, 1)
    assert session.screen == "title" and session.player["name"] == "BRUNO"
    # (PLAY ONLINE only opens the online box of this same screen: nothing to send, no new picture)
    assert not session.get("_toasts") and session.title_welcome  # the welcome waits for the first room
    title.welcome()
    assert session["_toasts"][-1]["text"] == "Welcome back, BRUNO!" and session.title_welcome is None


def test_play_offline_flies_into_the_arcade_first(session):
    _account("Carla", "1357")
    _send(title._sign_in, {"mode": "login", "name": "Carla", "pin": "1357"}, 1)
    _send(title._play, {"where": "offline", "n": 5})
    assert session.title_enter == 5 and session.screen == "title"  # the browser flies in, then sends "entered"
    _send(title._walk_in)
    assert session.screen == "hub"


def test_a_wrong_pin_is_refused_and_nobody_is_signed_in(session):
    _account("Duda", "1111")
    _send(title._sign_in, {"mode": "login", "name": "Duda", "pin": "9999"}, 3)
    assert session.player is None and session.title_error["n"] == 3


def test_log_out_from_the_choice(session):
    _account("Eva", "4444")
    _send(title._sign_in, {"mode": "login", "name": "Eva", "pin": "4444"}, 1)
    _send(title._log_out)
    assert session.player is None


def test_the_pixel_font_has_the_new_menu_words():
    _, glyphs, _ = title_layers.font_atlas()
    words = ["CREATE A CHARACTER", "I HAVE AN ACCOUNT", "PLAY OFFLINE", "PLAY ONLINE", "LOG OUT", "HELLO, MIGUEL!"]
    assert not {ch for word in words for ch in word if ch not in glyphs}
    assert {"play", "logout"} <= set(title_view.EVENTS)


def test_the_character_maker_is_drawn_on_the_titles_own_background():
    from arcade.art import create
    from arcade.logic import looks

    still = title_layers.still()
    maker, _ = create.creator_picture("ANA", {k: next(iter(o)) for k, o in looks.ROWS}, None)
    for corner in ((5, 5), (5, 530), (950, 300)):  # around the box: the title screen shows
        assert maker.convert("RGB").getpixel(corner) == still.getpixel(corner)


def test_create_lobby_flies_into_the_lobbys_room(session, monkeypatch):
    from arcade import online
    from arcade.logic.lobby import Lobbies

    from arcade.screens import online_room

    lobbies = Lobbies()
    monkeypatch.setattr(online, "lobbies", lambda: lobbies)
    monkeypatch.setattr(online_room, "S", session)
    _account("Fred", "5555")
    _send(title._sign_in, {"mode": "login", "name": "Fred", "pin": "5555"}, 1)
    _send(title._lobby, {"action": "create"}, 2)
    code = session.lobby_code
    assert lobbies.get(code).names() == ["FRED"] and session.title_enter == 2  # the flight, then the room
    _send(title._walk_in)
    assert session.screen == "lobby"


def test_a_wrong_code_is_shown_in_the_join_box(session, monkeypatch):
    from arcade import online
    from arcade.logic.lobby import Lobbies

    monkeypatch.setattr(online, "lobbies", lambda: Lobbies())
    _account("Gil", "6666")
    _send(title._sign_in, {"mode": "login", "name": "Gil", "pin": "6666"}, 1)
    _send(title._lobby, {"action": "join", "code": "ZZZZ"}, 3)
    assert session.title_error == {"text": "There is no lobby with that code.", "n": 3} and not session.lobby_code


def test_leaving_a_lobby_goes_back_to_offline_or_online(session, monkeypatch):
    from arcade import online
    from arcade.logic.lobby import Lobbies
    from arcade.screens import online as online_screens

    lobbies = Lobbies()
    monkeypatch.setattr(online, "lobbies", lambda: lobbies)
    monkeypatch.setattr(online_screens, "S", session)
    _account("Hugo", "7777")
    _send(title._sign_in, {"mode": "login", "name": "Hugo", "pin": "7777"}, 1)
    session.lobby_code = lobbies.create(online.card(session.player))
    online_screens.leave()
    assert session.screen == "title" and session.title_start["step"] == "mode" and session.player["name"] == "HUGO"
    online_screens.leave("That lobby has closed.")
    assert session.title_start["step"] == "online" and session.title_notice["text"] == "That lobby has closed."
