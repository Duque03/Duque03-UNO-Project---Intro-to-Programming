"""Visual update, idea 2: the neon glow."""

import pytest
from PIL import Image

from arcade.art import effects


def _canvas(colour=(0, 0, 0)):
    return Image.new("RGB", (120, 80), colour)


def _neon_dot():
    img = _canvas()
    img.paste((255, 40, 160), (56, 36, 64, 44))  # a small bright pink square
    return img


def test_a_neon_colour_lights_up_the_pixels_around_it():
    out = effects.neon_glow(_neon_dot())
    assert sum(out.getpixel((52, 40))) > 0  # just outside the square: no longer black
    assert out.getpixel((5, 5)) == (0, 0, 0)  # far away: still black


def test_white_and_grey_do_not_glow():
    img = _canvas()
    img.paste((255, 255, 255), (56, 36, 64, 44))
    img.paste((150, 150, 150), (10, 10, 20, 20))
    out = effects.neon_glow(img)
    assert out.getpixel((52, 40)) == (0, 0, 0)
    assert out.getpixel((6, 15)) == (0, 0, 0)


def test_the_glow_only_brightens():
    img = _neon_dot()
    out = effects.neon_glow(img)
    for xy in ((60, 40), (52, 40), (5, 5)):
        assert all(after >= before for before, after in zip(img.getpixel(xy), out.getpixel(xy)))


def test_strength_zero_changes_nothing_and_the_size_is_kept():
    img = _neon_dot()
    assert effects.neon_glow(img, 0).tobytes() == img.tobytes()
    assert effects.neon_glow(img).size == img.size


def test_the_original_picture_is_not_changed():
    img = _neon_dot()
    before = img.tobytes()
    effects.neon_glow(img)
    assert img.tobytes() == before


@pytest.mark.parametrize("strength", [-0.1, 1.5])
def test_a_strength_outside_zero_to_one_is_rejected(strength):
    with pytest.raises(ValueError):
        effects.neon_glow(_neon_dot(), strength)
