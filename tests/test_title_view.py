"""The title screen drawn by the browser (arcade/title_view.py): what Python sends it."""

import pytest

from arcade import accounts, title_view
from arcade.art import title_layers
from arcade.player import InvalidName


def test_every_picture_is_sent_once_per_session():
    sent = set()
    first = title_view.scene(sent)
    for key in ("bg", "cabinets", "logo", "logoSmall"):
        assert first[key] in first["assets"]
    assert first["font"]["img"] in first["assets"]
    assert len(first["bots"]) == 5 and all(bot["sheet"] in first["assets"] for bot in first["bots"])
    again = title_view.scene(sent)
    assert again["assets"] == {}  # the browser already has them
    assert again["bots"][0]["sheet"] == first["bots"][0]["sheet"]


def test_the_answer_to_a_sign_in_goes_back_with_its_number():
    data = title_view.scene(set(), error={"text": "Wrong PIN", "n": 3}, ack=3, last_name="MIGUEL")
    assert data["ack"] == 3 and data["error"] == {"text": "Wrong PIN", "n": 3} and data["lastName"] == "MIGUEL"
    assert data["pinMin"] == accounts.PIN_MIN and data["pinMax"] == accounts.PIN_MAX


def _messages(tmp_path):
    """Every message the sign-in can show on the title screen."""
    path = tmp_path / "players.db"
    accounts.sign_up("Taken", "1234", "1234", path)
    attempts = [
        lambda: accounts.sign_up("", "1234", "1234", path),
        lambda: accounts.sign_up("Bad*Name", "1234", "1234", path),
        lambda: accounts.sign_up("Fine", "12", "12", path),
        lambda: accounts.sign_up("Fine", "1234", "4321", path),
        lambda: accounts.sign_up("Taken", "1234", "1234", path),
        lambda: accounts.log_in("Nobody", "1234", path),
        lambda: accounts.log_in("Taken", "9999", path),
    ] + [lambda: accounts.log_in("Taken", "9999", path)] * 5
    out = []
    for attempt in attempts:
        with pytest.raises((InvalidName, accounts.InvalidPin, accounts.WrongPin, accounts.Locked,
                            accounts.NameTaken, accounts.UnknownName)) as problem:
            attempt()
        out.append(str(problem.value).upper())
    return out


def test_the_pixel_font_has_every_letter_the_title_screen_writes(tmp_path):
    _, glyphs, _ = title_layers.font_atlas()
    texts = _messages(tmp_path) + ["PLAY", "HOW TO PLAY", "NEW PLAYER", "I HAVE AN ACCOUNT", "WELCOME BACK", "BACK",
                                   "CREATE", "LOG IN", "THE PIN MUST BE 4 TO 8 DIGITS", "THE TWO PINS ARE NOT THE SAME",
                                   "REMEMBER YOUR PIN: IT CANNOT BE RECOVERED", "ARROWS: CHOOSE  -  ENTER: OK"]
    missing = {ch for text in texts for ch in text if ch not in glyphs}
    assert not missing, missing
