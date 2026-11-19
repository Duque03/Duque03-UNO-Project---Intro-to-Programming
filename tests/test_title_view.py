"""The title screen drawn by the browser (arcade/title_view.py): what Python sends it."""

import pytest

from arcade import accounts, catalog, title_view
from arcade.art import title_layers
from arcade.player import InvalidName, look, new_player


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


def test_no_champion_until_someone_has_won_a_championship():
    assert title_view.scene(set())["champion"] is None


def test_the_champion_dances_with_their_skins_and_number_of_titles():
    champ = new_player("ANA")
    champ["equipped"] = {"hair": "hair_r01", "shirt": "shirt_c01", "name": "name_r02"}
    sent = set()
    data = title_view.scene(sent, champion={"name": "ANA", "look": look(champ), "titles": 3,
                                            "tag": catalog.spec_for("name", "name_r02")})
    assert data["champion"]["titles"] == 3
    assert data["champion"]["sheet"] in data["assets"] and data["champion"]["tags"][0] in data["assets"]
    assert all(bot["x"] != data["champion"]["x"] for bot in data["bots"])


def test_an_accepted_sign_in_tells_the_browser_to_fly_into_the_arcade():
    assert title_view.scene(set())["enter"] == 0
    assert title_view.scene(set(), enter=4)["enter"] == 4
    assert "entered" in title_view.EVENTS


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
                                   "REMEMBER YOUR PIN: IT CANNOT BE RECOVERED", "ARROWS: CHOOSE  -  ENTER: OK",
                                   "PRESS ENTER", "ENTER YOUR NAME", "CHAMPION X12", "1-5: POKE A BOT  -  M: MUSIC",
                                   "CLICK A BOT (OR 1-5) TO MAKE IT DANCE"] + title_view.LINES
    missing = {ch for text in texts for ch in text if ch not in glyphs}
    assert not missing, missing
