"""A1: screens change through black instead of with an instant cut."""

import pytest
from PIL import Image

from arcade.art import scenes


def _brightness(img) -> float:
    pixels = list(img.convert("L").get_flattened_data())
    return sum(pixels) / len(pixels)


def _picture(colour, size=(96, 54)):
    return Image.new("RGB", size, colour)


def test_a_fade_of_zero_keeps_the_picture():
    img = _picture((200, 100, 50))
    assert scenes.fade(img, 0).getpixel((0, 0)) == (200, 100, 50)


def test_a_fade_of_one_is_black():
    assert scenes.fade(_picture((200, 100, 50)), 1).getpixel((0, 0)) == (0, 0, 0)


def test_a_fade_does_not_change_the_original_picture():
    img = _picture((200, 100, 50))
    scenes.fade(img, 0.5)
    assert img.getpixel((0, 0)) == (200, 100, 50)


@pytest.mark.parametrize("amount", [-0.1, 1.5])
def test_a_fade_outside_zero_to_one_is_rejected(amount):
    with pytest.raises(ValueError):
        scenes.fade(_picture((200, 100, 50)), amount)


def test_the_frames_go_through_black():
    old, new = _picture((255, 255, 255)), _picture((120, 200, 80))
    frames = scenes.fade_through_black(old, new, 4)
    assert len(frames) == 7  # 4 frames down to black, 3 back up (the new picture itself is shown after)
    assert frames[3].getpixel((0, 0)) == (0, 0, 0)
    levels = [_brightness(frame) for frame in frames]
    assert levels[:4] == sorted(levels[:4], reverse=True)  # darker and darker
    assert levels[3:] == sorted(levels[3:])  # then lighter and lighter
    assert levels[-1] < _brightness(new)  # the last frame is still a little dark


def test_the_frames_have_the_size_of_the_new_picture():
    frames = scenes.fade_through_black(_picture((255, 255, 255), (50, 50)), _picture((0, 0, 255)), 3)
    assert {frame.size for frame in frames} == {(96, 54)}


def test_a_fade_with_no_steps_is_rejected():
    with pytest.raises(ValueError):
        scenes.fade_through_black(_picture((255, 255, 255)), _picture((0, 0, 0)), 0)
