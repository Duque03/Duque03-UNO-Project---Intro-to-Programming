"""The game picture is replaced in place, never through an empty placeholder (fix for the blinking screen)."""

from arcade import ui


class FakeElement:
    def __init__(self, log, where):
        self.log, self.where = log, where

    def image(self, data, **kwargs):
        self.log.append(("image", self.where, data))
        return FakeElement(self.log, f"element {len(self.log)}")

    def empty(self):
        self.log.append(("empty", self.where, None))
        return FakeElement(self.log, "empty")


class FakeStreamlit:
    def __init__(self):
        self.log = []

    def container(self, key):
        self.log.append(("container", key, None))
        return FakeElement(self.log, key)


def _fake(monkeypatch):
    fake = FakeStreamlit()
    monkeypatch.setattr(ui, "st", fake)
    return fake


def test_screen_puts_nothing_on_the_page_before_a_picture(monkeypatch):
    fake = _fake(monkeypatch)
    ui.screen()
    assert fake.log == []


def test_first_picture_goes_straight_into_the_container(monkeypatch):
    fake = _fake(monkeypatch)
    ui.screen().image("one")
    assert fake.log == [("container", ui.SCREEN_KEY, None), ("image", ui.SCREEN_KEY, "one")]


def test_later_pictures_replace_the_one_before(monkeypatch):
    fake = _fake(monkeypatch)
    slot = ui.screen()
    slot.image("one")
    slot.image("two")
    slot.image("three")
    assert [entry[0] for entry in fake.log].count("container") == 1
    assert fake.log[2] == ("image", "element 2", "two")  # drawn over the first picture, not under it
    assert fake.log[3] == ("image", "element 3", "three")


def test_no_empty_placeholder_is_ever_used(monkeypatch):
    """Rejected: an empty placeholder removes the old picture first, which made the screen blink."""
    fake = _fake(monkeypatch)
    slot = ui.screen(ui.TITLE_KEY)
    for frame in ("a", "b"):
        slot.image(frame)
    assert all(kind != "empty" for kind, _, _ in fake.log)
    assert fake.log[0] == ("container", ui.TITLE_KEY, None)
