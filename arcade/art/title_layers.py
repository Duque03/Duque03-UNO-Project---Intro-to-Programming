"""The pieces of the title screen, painted once. The browser animates them (arcade/title_view.py).

backdrop()   the sky and the floor (no stars, no grid lines: the browser draws those, moving)
cabinets()   the four glowing arcade cabinets, on a see-through layer
logo()       ARCADE MASTERS with its neon glow, on a see-through layer
stars()      where the stars are and their colours (the browser makes them twinkle)
font_atlas() every letter the menus need, white, in the game's pixel font, side by side
The dancing bots reuse the room's sprite sheets and name tags (room_layers.sheet, room_layers.tag_frames).
"""

from __future__ import annotations

import random
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter

from arcade.art.pixel import draw_text, mix, new_base, rect, rgb, text_size, upscale
from arcade.art.scenes import _machine
from arcade.config import BASE_W, SCREEN_W

HORIZON = 110  # small-canvas row where the floor starts
CABINETS = ((26, "#3a2f6b", "#3ad6ff"), (58, "#4a2f5f", "#ff4fa3"), (262, "#2f3f6b", "#7cff3a"), (294, "#3a2f6b", "#ffe94a"))
FONT_SCALE = 2  # the letters are drawn at this text scale (14 pixels tall), the browser blows them up
FONT_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !?.,:-_()/+'"


@lru_cache(maxsize=1)
def backdrop() -> Image.Image:
    img = new_base("#120d2e")
    d = ImageDraw.Draw(img)
    for y in range(HORIZON):
        rect(d, 0, y, BASE_W, 1, mix("#120d2e", "#3a1a5e", y / HORIZON))
    rect(d, 0, HORIZON, BASE_W, 180 - HORIZON, (14, 10, 36))
    return upscale(img)


@lru_cache(maxsize=1)
def cabinets() -> Image.Image:
    layer = Image.new("RGBA", (BASE_W, 180), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for cx, body, screen in CABINETS:
        _machine(d, cx, 150, rgb(body), rgb(screen), w=26, h=62, glow=True)
    return upscale(layer)


@lru_cache(maxsize=2)
def logo(small: bool = False) -> Image.Image:
    """ARCADE MASTERS in three offset colours, with a soft yellow glow around it.
    small: the version shown above the name and PIN boxes."""
    size, lines, shift = (6, (("ARCADE", 10), ("MASTERS", 66)), 3) if small else (11, (("ARCADE", 22), ("MASTERS", 128)), 6)
    text = Image.new("RGBA", (SCREEN_W, 130 if small else 250), (0, 0, 0, 0))
    for line, y in lines:
        draw_text(text, (SCREEN_W // 2 + shift, y + shift), line, size, "#3ad6ff", "mt")
        draw_text(text, (SCREEN_W // 2, y), line, size, "#ff4fa3", "mt")
        draw_text(text, (SCREEN_W // 2 - shift // 2, y - shift // 2), line, size, "#ffe94a", "mt")
    glow = Image.new("RGBA", text.size, (255, 215, 90, 0))
    glow.putalpha(text.getchannel("A").filter(ImageFilter.GaussianBlur(6 if small else 10)).point(lambda a: int(a * 0.55)))
    out = Image.alpha_composite(glow, text)
    return out


@lru_cache(maxsize=1)
def stars() -> list[list]:
    """[x, y, colour, twinkle phase] for 60 stars, on the big picture."""
    rng = random.Random(11)
    out = []
    for i in range(60):
        x, y = rng.randrange(BASE_W) * 3, rng.randrange(90) * 3
        out.append([x, y, rng.choice(["#ffffff", "#ffe94a", "#3ad6ff"]), round(rng.random() * 6.28, 2)])
    return out


@lru_cache(maxsize=1)
def font_atlas() -> tuple[Image.Image, dict, int]:
    """All the letters in a row, white on see-through. Returns (picture, {letter: [x, width]}, height)."""
    height = text_size("A", FONT_SCALE)[1] + 6  # room under the capitals for , and _
    widths = {ch: (text_size(ch, FONT_SCALE)[0] if ch != " " else 8) for ch in FONT_CHARS}
    img = Image.new("RGBA", (sum(widths.values()) + 2 * len(FONT_CHARS), height), (0, 0, 0, 0))
    glyphs, x = {}, 0
    for ch in FONT_CHARS:
        if ch != " ":
            draw_text(img, (x, 1), ch, FONT_SCALE, "#ffffff", "lt")
        glyphs[ch] = [x, widths[ch]]
        x += widths[ch] + 2
    return img, glyphs, height

