"""The page keeps the same shape from one screen to the next (Miguel saw black blinks and a doubled picture): inside
game_frame the backdrop box is always first and the toast box always second, whatever the screen, and the backdrop
box says which screen is on (the CSS uses it: the turn clock only shows at a table)."""
import pathlib

import pytest
from streamlit.testing.v1 import AppTest

from arcade import bots, hubmap
from arcade import player as player_model

APP = pathlib.Path(__file__).resolve().parent.parent / "app.py"


@pytest.fixture
def at(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCADE_DB", str(tmp_path / "arcade.db"))
    app = AppTest.from_file(str(APP), default_timeout=60)
    app.run()
    assert not app.exception, app.exception
    return app


def _frame(app):
    return next(block for block in app.main.children.values() if getattr(block, "key", None) == "game_frame")


def _first_two(app):
    children = list(_frame(app).children.values())
    return [getattr(child, "key", None) for child in children[:2]]


def _marker(app):
    backdrop = list(_frame(app).children.values())[0]
    return " ".join(getattr(child, "value", "") or "" for child in backdrop.children.values())


def _sign_in(app):
    me = player_model.new_player("TESTER")
    me["look_done"] = True
    app.session_state["player"] = me
    app.session_state["hub"] = {"pos": hubmap.SPAWN, "dir": "up", "walk": None, "pressed": 0,
                                "bots": {b["name"]: {"pos": b["home"], "dir": b["dir"]} for b in bots.BOTS}}


def test_title_starts_with_the_backdrop_then_the_toasts(at):
    assert _first_two(at) == ["game_backdrop", "game_toasts"]
    assert "arcade-on-title" in _marker(at)


@pytest.mark.parametrize("screen", ["hub", "pause", "store", "wardrobe"])
def test_every_screen_keeps_the_same_first_two_boxes(at, screen):
    _sign_in(at)
    at.session_state["screen"] = screen
    at.session_state["paused_from"] = "hub"
    at.run()
    assert not at.exception, at.exception
    assert _first_two(at) == ["game_backdrop", "game_toasts"]
    assert f"arcade-on-{screen}" in _marker(at)
    at.run()  # the same screen again: the backdrop box is still there (empty), so nothing after it moves
    assert not at.exception, at.exception
    assert _first_two(at) == ["game_backdrop", "game_toasts"]


def test_a_toast_goes_in_the_toast_box(at):
    from arcade import ui

    _sign_in(at)
    at.session_state["screen"] = "pause"
    at.session_state["paused_from"] = "hub"
    at.session_state["_toasts"] = [{"id": 1, "text": "Bought a hat!", "until": 9e12, "delay": 0.0}]
    at.run()
    assert not at.exception, at.exception
    toasts = list(_frame(at).children.values())[1]
    assert toasts.key == "game_toasts"
    assert len(toasts.children) == 1  # (the message's own box, inside)
    assert ui.TOAST_SECONDS > 0


def _poisoned_page():
    """A run that starts with Streamlit still pointing inside a container (as after a fragment ran in the same
    thread), then ui.fresh_page(), then the page."""
    import streamlit as st
    from streamlit.delta_generator_singletons import context_dg_stack

    from arcade import ui

    box = st.container(key="frame")
    with box:
        st.markdown("inside")
    context_dg_stack.set((*context_dg_stack.get(), box))  # (what the fragment left behind)
    ui.fresh_page()
    st.markdown("top")


def test_fresh_page_puts_the_run_back_at_the_top_of_the_page():
    app = AppTest.from_function(_poisoned_page)
    app.run()
    assert not app.exception, app.exception
    keys = [getattr(child, "key", None) for child in app.main.children.values()]
    top_level = [getattr(child, "value", None) for child in app.main.children.values()]
    assert "frame" in keys
    assert "top" in top_level  # written on the page itself, not inside the box
    frame = next(child for child in app.main.children.values() if getattr(child, "key", None) == "frame")
    assert [getattr(child, "value", None) for child in frame.children.values()] == ["inside"]


def test_into_a_game_and_out_goes_behind_the_curtain(monkeypatch):
    """curtain_to() opens the "curtain" screen (the old screen stays while the curtain comes down), and that screen
    then opens the real one."""
    import streamlit as st

    from arcade import ui

    session = {"screen": "uno", "player": {"name": "TESTER"}, "_fade_next": True}
    monkeypatch.setattr(st, "session_state", session, raising=False)
    ui.curtain_to("hub")
    assert session["screen"] == "curtain" and session["_curtain_target"] == "hub"
    assert "_fade_next" not in session  # (the curtain is the transition: no fade on top of it)
    first = session["_curtain_n"]
    slept = []
    monkeypatch.setattr(ui.time, "sleep", slept.append)

    class Rerun(Exception):
        pass

    def rerun():
        raise Rerun

    monkeypatch.setattr(st, "rerun", rerun)
    with pytest.raises(Rerun):
        ui.render_curtain()
    assert session["screen"] == "hub" and "_curtain_target" not in session
    assert slept and slept[0] >= ui.CURTAIN_CLOSE  # (it waits for the curtain to be down first)
    ui.curtain_to("connect4")
    assert session["_curtain_n"] == first + 1  # (a new number: the browser brings the curtain down again)


def test_the_curtain_is_always_on_the_page(at):
    keys = [getattr(child, "key", None) for child in at.main.children.values()]
    assert "curtain" in keys
    _sign_in(at)
    at.session_state["screen"] = "hub"
    at.run()
    assert not at.exception, at.exception
    assert [getattr(child, "key", None) for child in at.main.children.values()].index("curtain") == keys.index("curtain")
