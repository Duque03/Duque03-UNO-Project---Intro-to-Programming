"""Finishing touches applied to a whole frame just before it is shown (visual update, ideas 2 and 3).

neon_glow() makes the bright, saturated colours (neon signs, arcade screens,
table tops, cards) bleed a soft light around them, like real neon.
"""

from __future__ import annotations

from PIL import Image, ImageChops, ImageFilter

GLOW_MIN_SATURATION = 110  # 0-255: only strong colours glow (whites and greys stay sharp)
GLOW_MIN_BRIGHTNESS = 150  # 0-255: only bright colours glow
GLOW_SHRINK = 4  # the blur is made on a picture this many times smaller (much faster, and softer)


def _neon_mask(img: Image.Image) -> Image.Image:
    """White where a pixel is bright and saturated enough to glow, black elsewhere."""
    _, saturation, value = img.convert("HSV").split()
    strong = saturation.point(lambda v: 255 if v >= GLOW_MIN_SATURATION else 0)
    bright = value.point(lambda v: 255 if v >= GLOW_MIN_BRIGHTNESS else 0)
    return ImageChops.multiply(strong, bright)


def neon_glow(img: Image.Image, strength: float = 0.9, radius: float = 3.0) -> Image.Image:
    """A copy of the picture with a soft glow around its neon colours. strength 0 changes nothing."""
    if not 0 <= strength <= 1:
        raise ValueError("glow strength goes from 0 to 1")
    img = img.convert("RGB")
    if strength == 0:
        return img.copy()
    # Everything is worked out on a picture GLOW_SHRINK times smaller (16 times fewer pixels), then blown up:
    # the halo is blurred anyway, so it looks the same, and it is about twice as fast.
    small = img.resize((max(1, img.width // GLOW_SHRINK), max(1, img.height // GLOW_SHRINK)), Image.BOX)
    neon = Image.composite(small, Image.new("RGB", small.size), _neon_mask(small))
    halo = neon.filter(ImageFilter.GaussianBlur(radius)).resize(img.size, Image.BILINEAR)
    halo = halo.point(lambda v: int(v * strength))
    return ImageChops.screen(img, halo)  # "screen" only ever brightens, like light
