"""The pause menu offers "leave table" only at a game table (task B4); sentence banks are never empty."""

from arcade import phrases
from arcade.screens import pause


def test_leave_table_only_at_a_table():
    for table in ("uno", "checkers", "connect4"):
        actions = [option["action"] for option in pause.options(table)]
        assert "leave_table" in actions
        assert actions[0] == "resume" and actions[-1] == "leave"
    for elsewhere in ("hub", None):
        assert "leave_table" not in [option["action"] for option in pause.options(elsewhere)]


def test_play_online_only_from_the_room():
    assert "online" in [option["action"] for option in pause.options("hub")]
    for table in ("uno", "checkers", "connect4"):
        assert "online" not in [option["action"] for option in pause.options(table)]


def test_the_menu_list_itself_is_not_changed():
    before = list(pause.OPTIONS)
    pause.options("uno")
    assert pause.OPTIONS == before


def test_sentence_banks():
    assert phrases.WIN_LINES[0] == "Congratulations!! You won!"
    assert len(phrases.TIE_LINES) >= 5
    assert len(phrases.LOSE_LINES) >= 20
    for bank in (phrases.WIN_LINES, phrases.TIE_LINES, phrases.LOSE_LINES):
        assert all(line.strip() for line in bank)
