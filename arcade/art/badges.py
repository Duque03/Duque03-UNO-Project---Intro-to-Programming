"""The big buttons in the middle of the UNO table: UNO! (say it before someone cuts it) and CORTA UNO! (cut someone
else's). Our own design: a comic-book burst with chunky slanted letters, like a sticker slapped on the table.

Plain data in, a Pillow picture out (see-through around the burst). The burst is drawn small and blown up 3x like
everything else; the letters are drawn at full size, outlined, with a coloured drop shadow, then slanted.
"""

from __future__ import annotations

import math
from functools import lru_cache

from PIL import Image, ImageDraw

from arcade.art.pixel import _text_mask, rgb

INK = "#16122b"
STYLES = {  # burst, its light middle, the letters' drop shadow, the small word on top
    "uno": {"burst": "#ffb020", "light": "#ffe94a", "shadow": "#e2413c", "small": None, "small_fill": None},
    "corta": {"burst": "#ff4f6d", "light": "#ff9fb4", "shadow": "#6b1fbf", "small": "CORTA", "small_fill": "#ffe94a"},
}
BASE_W, BASE_H = 104, 58  # the burst on the small canvas (x3 on the picture)


def _burst(size, spikes, inset, colour, shrink=0.0):
    """A star-shaped burst filling most of the box, as a list of points."""
    w, h = size
    cx, cy = w / 2, h / 2
    rx, ry = w / 2 - 1 - shrink, h / 2 - 1 - shrink * h / w
    points = []
    for k in range(spikes * 2):
        angle = math.pi * k / spikes - math.pi / 2
        r = 1.0 if k % 2 == 0 else inset
        points.append((cx + math.cos(angle) * rx * r, cy + math.sin(angle) * ry * r))
    return points


def _outlined(text: str, scale: int, fill: str, shadow: str, outline: int) -> Image.Image:
    """The text with a thick dark outline and a coloured drop shadow, slanted forward."""
    mask = _text_mask(text, scale)
    w, h = mask.size
    pad = outline + scale * 2
    img = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    ink, shade, front = rgb(INK) + (255,), rgb(shadow) + (255,), rgb(fill) + (255,)
    drop = scale + 3
    ring = [(dx, dy) for dx in range(-outline, outline + 1) for dy in range(-outline, outline + 1)
            if dx * dx + dy * dy <= outline * outline]
    for dx, dy in ring:  # the shadow's own outline, then the shadow, then the letters' outline and the letters
        img.paste(ink, (pad + dx + drop, pad + dy + drop), mask)
    for k in range(drop):
        img.paste(shade, (pad + k + 1, pad + k + 1), mask)
    for dx, dy in ring:
        img.paste(ink, (pad + dx, pad + dy), mask)
    img.paste(front, (pad, pad), mask)
    slant = 0.16  # lean the letters forward (each row moves a whole pixel: no blur)
    extra = int(img.height * slant) + 1
    return img.transform((img.width + extra, img.height), Image.AFFINE, (1, slant, -extra, 0, 1, 0), Image.NEAREST)


@lru_cache(maxsize=4)
def badge(kind: str) -> Image.Image:
    """The button for "uno" or "corta", about 312 x 174 on the picture."""
    style = STYLES[kind]
    small = Image.new("RGBA", (BASE_W, BASE_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(small)
    d.polygon(_burst((BASE_W, BASE_H), 14, 0.74, INK), fill=rgb(INK))
    d.polygon(_burst((BASE_W, BASE_H), 14, 0.74, style["burst"], shrink=3), fill=rgb(style["burst"]))
    d.polygon(_burst((BASE_W, BASE_H), 14, 0.74, style["light"], shrink=12), fill=rgb(style["light"]))
    for k in range(5):  # a few sparkles on the burst's edge
        angle = 2 * math.pi * k / 5 + 0.4
        x = BASE_W / 2 + math.cos(angle) * (BASE_W / 2 - 9)
        y = BASE_H / 2 + math.sin(angle) * (BASE_H / 2 - 6)
        d.rectangle([x - 1, y - 1, x, y], fill=(255, 255, 255))
    img = small.resize((BASE_W * 3, BASE_H * 3), Image.NEAREST)

    word = _outlined("UNO!", 8 if kind == "uno" else 7, "#ffffff", style["shadow"], 6)
    if style["small"]:
        top = _outlined(style["small"], 4, style["small_fill"], INK, 4)
        total = top.height + word.height - 22
        y = (img.height - total) // 2
        img.alpha_composite(top, ((img.width - top.width) // 2, y))
        img.alpha_composite(word, ((img.width - word.width) // 2, y + top.height - 22))
    else:
        img.alpha_composite(word, ((img.width - word.width) // 2, (img.height - word.height) // 2 - 2))
    return img


def place(kind: str, centre=(480, 196)) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """The button and the box it covers on the picture, centred here (over the table, above the piles)."""
    img = badge(kind)
    x0, y0 = centre[0] - img.width // 2, centre[1] - img.height // 2
    return img, (x0, y0, x0 + img.width, y0 + img.height)

