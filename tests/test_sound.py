"""A7: the Python side of sound only queues names of known sounds."""

import pytest

from arcade import sound


def test_a_known_sound_is_queued_with_a_new_number():
    queue = sound.add_cue([], "win")
    queue = sound.add_cue(queue, "coin")
    assert [cue["name"] for cue in queue] == ["win", "coin"]
    assert queue[1]["id"] > queue[0]["id"]


def test_an_unknown_sound_is_rejected_and_the_queue_is_unchanged():
    queue = sound.add_cue([], "win")
    with pytest.raises(ValueError):
        sound.add_cue(queue, "explosion")
    assert [cue["name"] for cue in queue] == ["win"]


def test_the_queue_stays_short():
    queue = []
    for _ in range(20):
        queue = sound.add_cue(queue, "blip")
    assert len(queue) == sound.MAX_QUEUE
    assert queue[-1]["id"] == 20


def test_adding_does_not_change_the_given_queue():
    queue = sound.add_cue([], "win")
    sound.add_cue(queue, "lose")
    assert len(queue) == 1


def test_every_sound_the_game_uses_has_a_name_the_browser_knows():
    for name in sound.SOUNDS:
        assert f'{name}:' in sound.SOUND_JS
