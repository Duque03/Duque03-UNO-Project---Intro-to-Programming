"""The tunes in arcade/music.py: each fits its bars, uses sensible notes, and every screen has one."""

import pytest

from arcade import music

TUNES = list(music.TRACKS)


def test_there_is_a_tune_for_the_title_the_room_and_each_game():
    assert set(TUNES) == {"title", "room", "uno", "checkers", "connect4"}


@pytest.mark.parametrize("name", TUNES)
def test_every_part_of_a_tune_fits_inside_its_bars(name):
    tune = music.TRACKS[name]
    steps = tune["bars"] * music.STEPS_PER_BAR
    for part in ("lead", "bass", "arp", "stabs"):
        for step, note, length in tune.get(part, []):
            assert 0 <= step and step + length <= steps, (part, step, length)
            assert 28 <= note <= 100, (part, note)  # from a low bass to a high whistle, nothing silly
    for step, kind in tune["drums"]:
        assert 0 <= step < steps and kind in ("k", "s", "h")
    assert 60 <= tune["bpm"] <= 180 and 0 <= tune["swing"] < 0.5


@pytest.mark.parametrize("name", TUNES)
def test_the_melody_never_plays_two_notes_at_once(name):
    lead = music.TRACKS[name]["lead"]
    for (step, _, length), (next_step, _, _) in zip(lead, lead[1:]):
        assert step + length <= next_step


def test_notes_are_read_the_usual_way():
    assert music.midi("A4") == 69 and music.midi("C4") == 60 and music.midi("Bb3") == 58
    assert music.melody("C4:2 r:2 E4") == [[0, 60, 2], [4, 64, 1]]


def test_a_badly_written_drum_bar_is_refused():
    with pytest.raises(AssertionError):
        music.drums(["k.h.s"])  # a bar needs 16 steps


def test_each_screen_plays_its_own_tune_or_keeps_the_last_one():
    assert music.track_for("title") == "title"
    assert music.track_for("hub") == "room" and music.track_for("store") == "room"
    assert music.track_for("uno") == "uno" and music.track_for("connect4") == "connect4"
    assert music.track_for("pause", playing="checkers") == music.SILENCE  # the pause menu is quiet
    assert music.track_for("howto", playing=music.SILENCE) == music.SILENCE  # (its rules too)
    assert music.track_for("wardrobe", playing=music.SILENCE) == music.SILENCE  # and its wardrobe
    assert music.track_for("howto") == "title"


def test_the_music_level_goes_round_high_medium_low():
    from arcade import sound

    assert [sound.next_level(level) for level in ("high", "medium", "low")] == ["medium", "low", "high"]
    assert sound.next_level("nonsense") == "high"
    assert sound.MUSIC_LEVELS["low"] > 0  # low is quiet, never silent (M switches the music off)
