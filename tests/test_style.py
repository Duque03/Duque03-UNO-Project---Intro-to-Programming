"""V1: the page style around the game picture."""

import re

from arcade import ui


def test_the_style_frames_the_game_and_title_pictures():
    assert f".st-key-{ui.SCREEN_KEY} img" in ui._CSS
    assert f".st-key-{ui.TITLE_KEY} img" in ui._CSS


def test_the_only_outside_address_is_google_fonts():
    addresses = re.findall(r"https?://[^'\")\s]+", ui._CSS)
    assert addresses
    assert all(address.startswith("https://fonts.googleapis.com/") for address in addresses)


def test_streamlit_menu_and_footer_are_hidden():
    assert "#MainMenu" in ui._CSS and "footer" in ui._CSS
