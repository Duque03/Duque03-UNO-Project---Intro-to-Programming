"""Draws the characters and their name tags.

A character is a 16x22 pixel figure made of layers: legs, shirt, head, hair.
It can face down, up, left or right, and has a two-step walk cycle.
The hair and shirt layers read their recipe ("spec") from arcade/catalog.py,
so new cosmetics usually only need a new catalog entry.
"""

from __future__ import annotations

from functools import lru_cache

from PIL import Image, ImageDraw

from arcade import catalog
from arcade.art.pixel import CHAR_H, draw_text, mix, new_layer, outlined, readable_on, rgb, shade, text_size

SPR_W, SPR_H = 20, 28  # sprite canvas (room for tall hair)
OX, OY = 2, 6  # where the 16x22 figure starts inside that canvas
RAINBOW = ["#ff4f6d", "#ff9f1a", "#ffe94a", "#4ade80", "#3ad6ff", "#a06bff"]

# Hair shapes as rectangles (x, y, w, h, colour index) on the 16x22 figure.
# Colour index 0 = main colour, 1 = accent colour.
_BASE = {
    "front": [(4, 1, 8, 3, 0), (3, 2, 1, 4, 0), (12, 2, 1, 4, 0)],
    "back": [(4, 1, 8, 7, 0), (3, 2, 1, 5, 0), (12, 2, 1, 5, 0)],
    "side": [(4, 1, 8, 3, 0), (8, 2, 4, 6, 0), (12, 3, 1, 4, 0)],
}
_SPIKES = [(4, -1, 2, 2, 1), (7, -2, 2, 3, 1), (10, -1, 2, 2, 1)]
_HAIR = {
    "short": {"front": [], "back": [], "side": []},
    "spiky": {"front": _SPIKES, "back": _SPIKES, "side": _SPIKES},
    "long": {
        "front": [(3, 6, 1, 7, 0), (12, 6, 1, 7, 0), (2, 5, 1, 7, 0), (13, 5, 1, 7, 0)],
        "back": [(3, 1, 10, 12, 0), (2, 5, 12, 7, 0)],
        "side": [(8, 8, 5, 5, 0), (12, 3, 1, 9, 0)],
    },
    "bob": {
        "front": [(3, 6, 1, 3, 0), (12, 6, 1, 3, 0), (2, 4, 1, 4, 0), (13, 4, 1, 4, 0), (4, 4, 2, 1, 0)],
        "back": [(3, 1, 10, 8, 0), (2, 4, 12, 4, 0)],
        "side": [(7, 2, 6, 7, 0), (4, 4, 2, 1, 0)],
    },
    "ponytail": {
        "front": [(13, 2, 2, 2, 0), (14, 4, 1, 5, 0)],
        "back": [(7, 7, 2, 6, 0)],
        "side": [(12, 2, 2, 2, 0), (13, 4, 1, 6, 0)],
    },
    "twintails": {
        "front": [(1, 3, 2, 7, 0), (13, 3, 2, 7, 0), (2, 3, 1, 1, 1), (13, 3, 1, 1, 1)],
        "back": [(1, 3, 2, 7, 0), (13, 3, 2, 7, 0), (2, 3, 1, 1, 1), (13, 3, 1, 1, 1)],
        "side": [(11, 3, 2, 8, 0), (11, 3, 2, 1, 1)],
    },
    "bun": {
        "front": [(6, -2, 4, 3, 0), (9, -1, 1, 1, 1)],
        "back": [(6, -2, 4, 3, 0), (9, -1, 1, 1, 1)],
        "side": [(9, -2, 4, 3, 0), (12, -1, 1, 1, 1)],
    },
}
# Styles that replace the basic cap of hair completely.
_FULL = {
    "mohawk": {
        "front": [(7, -4, 2, 8, 0), (6, -3, 1, 6, 1), (9, -3, 1, 6, 1)],
        "back": [(7, -4, 2, 13, 0), (6, -3, 1, 10, 1), (9, -3, 1, 10, 1)],
        "side": [(4, -4, 8, 3, 0), (3, -3, 10, 1, 1), (5, -1, 7, 4, 0)],
    },
    "afro": {
        "front": [(4, -4, 8, 1, 0), (3, -3, 10, 1, 0), (2, -2, 12, 6, 0), (2, 4, 2, 2, 0), (12, 4, 2, 2, 0),
                  (5, -2, 1, 1, 1), (10, 0, 1, 1, 1), (3, 1, 1, 1, 1)],
        "back": [(4, -4, 8, 1, 0), (3, -3, 10, 1, 0), (2, -2, 12, 11, 0), (5, -2, 1, 1, 1), (10, 3, 1, 1, 1)],
        "side": [(4, -4, 8, 1, 0), (3, -3, 10, 1, 0), (2, -2, 12, 6, 0), (8, 4, 6, 4, 0), (6, -1, 1, 1, 1)],
    },
}


def _hair_rects(style: str, view: str):
    if style in _FULL:
        return _FULL[style][view]
    return _BASE[view] + _HAIR.get(style, _HAIR["short"])[view]


def _shirt_colour(spec: dict, x: int, y: int, t: int):
    """Colour of one shirt pixel. (x, y) are on the 16x22 figure."""
    style = spec.get("style", "solid")
    c1 = spec["c1"]
    c2 = spec.get("c2", "#ffffff")
    if style == "hstripe":
        colour = c1 if ((y - 10) // 2) % 2 == 0 else c2
    elif style == "vstripe":
        colour = c1 if x % 2 == 0 else c2
    elif style == "check":
        colour = c1 if ((x // 2) + (y // 2)) % 2 == 0 else c2
    elif style == "emblem":
        star = (x in (7, 8) and 11 <= y <= 14) or (y in (12, 13) and 6 <= x <= 9)
        colour = c2 if star else c1
    elif style == "hoodie":
        if x in (6, 9) and y in (10, 11, 12):
            colour = c2  # drawstrings
        elif 6 <= x <= 9 and y in (14, 15):
            colour = shade(c1, 0.7)  # pocket
        else:
            colour = c1
    elif style == "gold":
        colour = mix(c1, "#c98a12", (y - 10) / 8)
        if (x * 7 + y * 13 + t * 5) % 11 == 0:
            colour = c2  # sparkle
        if x in (7, 8):
            colour = "#ffffff" if y < 16 else colour  # zip
    else:
        colour = c1
    if y == 16:
        colour = shade(colour, 0.8)
    return rgb(colour)


@lru_cache(maxsize=4096)
def sprite(skin: str, pants: str, hair_id, shirt_id, direction: str = "down", step: int = 0, t: int = 0):
    """Build one character picture (20x28, transparent background)."""
    if direction == "right":
        return sprite(skin, pants, hair_id, shirt_id, "left", step, t).transpose(Image.FLIP_LEFT_RIGHT)

    img = Image.new("RGBA", (SPR_W, SPR_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    hair = catalog.spec_for("hair", hair_id)
    shirt = catalog.spec_for("shirt", shirt_id)
    skin_c, skin_dark = rgb(skin), shade(skin, 0.78)
    pants_c, pants_dark, shoe = rgb(pants), shade(pants, 0.75), (30, 26, 40)

    def r(x, y, w, h, colour):
        d.rectangle([OX + x, OY + y, OX + x + w - 1, OY + y + h - 1], fill=colour)

    def shirt_area(x0, x1, y0, y1, darker=False):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                colour = _shirt_colour(shirt, x, y, t)
                d.point((OX + x, OY + y), fill=shade(colour, 0.82) if darker else colour)

    if direction in ("down", "up"):
        lift_l, lift_r = (1 if step == 1 else 0), (1 if step == 2 else 0)
        r(5, 17, 3, 3 - lift_l, pants_c)
        r(5, 20 - lift_l, 3, 2, shoe)
        r(8, 17, 3, 3 - lift_r, pants_dark)
        r(8, 20 - lift_r, 3, 2, shoe)
        shirt_area(4, 11, 10, 16)
        swing = {0: (0, 0), 1: (1, -1), 2: (-1, 1)}[step]
        shirt_area(2, 3, 10, 13 + min(0, swing[0]), darker=True)
        shirt_area(12, 13, 10, 13 + min(0, swing[1]), darker=True)
        r(2, 14 + min(0, swing[0]), 2, 2, skin_c)
        r(12, 14 + min(0, swing[1]), 2, 2, skin_c)
        r(4, 2, 8, 8, skin_c)
        r(4, 9, 8, 1, skin_dark)
        if direction == "down":
            r(6, 5, 1, 2, (34, 26, 30))
            r(9, 5, 1, 2, (34, 26, 30))
            r(7, 8, 2, 1, skin_dark)
        view = "front" if direction == "down" else "back"
    else:  # left (right is the mirror image)
        if step == 1:
            r(4, 17, 3, 3, pants_c)
            r(9, 17, 3, 3, pants_dark)
            r(3, 20, 4, 2, shoe)
            r(9, 20, 4, 2, shoe)
        else:
            r(6, 17, 4, 3, pants_c)
            r(5, 20, 5, 2, shoe)
        shirt_area(5, 10, 10, 16)
        arm_x = 7 + {0: 0, 1: -1, 2: 1}[step]
        shirt_area(arm_x, arm_x + 1, 11, 14, darker=True)
        r(arm_x, 15, 2, 2, skin_c)
        r(4, 2, 8, 8, skin_c)
        r(4, 9, 8, 1, skin_dark)
        r(5, 5, 1, 2, (34, 26, 30))
        view = "side"

    c1 = hair["c1"]
    c2 = hair.get("c2", c1)
    for x, y, w, h, index in _hair_rects(hair.get("style", "short"), view):
        if hair.get("rainbow"):
            for row in range(h):
                r(x, y + row, w, 1, rgb(RAINBOW[(y + row + t) % len(RAINBOW)]))
        else:
            r(x, y, w, h, rgb(c2 if index == 1 else c1))
    # one spare row at the bottom so the dark edge also fits under the shoes
    framed = new_layer((SPR_W, SPR_H + 1))
    framed.paste(img, (0, 0))
    return outlined(framed)


def draw_character(canvas, cx, feet_y, look, direction="down", step=0, t=0, scale=1):
    """Paste a character so that the middle of its feet sits on (cx, feet_y)."""
    skin, pants, hair_id, shirt_id = look
    img = sprite(skin, pants, hair_id, shirt_id, direction, step, t)
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    canvas.paste(img, (int(cx - img.width // 2), int(feet_y - img.height + scale)), img)


def head_icon(look, scale=3):
    """Just the head, for the championship scoreboard."""
    skin, pants, hair_id, shirt_id = look
    img = sprite(skin, pants, hair_id, shirt_id, "down", 0, 0).crop((1, 0, 19, 17))
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def portrait(look, name=None, tag_item=None, scale=8, direction="down", t=0, background="#231a4d"):
    """A big character picture for the store and the wardrobe."""
    w, h = SPR_W * scale + 80, SPR_H * scale + 70
    img = Image.new("RGB", (w, h), rgb(background))
    draw_character(img, w // 2, h - 14, look, direction, 0, t, scale)
    if name:
        draw_name_tag(img, w // 2, 44, name, catalog.spec_for("name", tag_item), t)
    return img


RARITY_COLOURS = {"common": "#3a6b5a", "rare": "#6b3ad8", "legendary": "#ffb81a"}


def item_tile(item, look, name, size=(168, 132)):
    """Store / wardrobe thumbnail: the item shown on the player's own character."""
    w, h = size
    edge = rgb(RARITY_COLOURS[item["rarity"]])
    img = Image.new("RGB", (w, h), edge)
    ImageDraw.Draw(img).rectangle([4, 4, w - 5, h - 5], fill=(28, 22, 66))
    skin, pants, hair_id, shirt_id = look
    if item["slot"] == "hair":
        draw_character(img, w // 2, h - 8, (skin, pants, item["id"], shirt_id), "down", scale=4)
    elif item["slot"] == "shirt":
        draw_character(img, w // 2, h - 8, (skin, pants, hair_id, item["id"]), "down", scale=4)
    else:
        draw_name_tag(img, w // 2, h // 2 + 14, name, item["spec"])
    return img


# ---------------------------------------------------------------- name tags

def _noise(i: int, t: int) -> int:
    return (i * 37 + t * 17 + (i * i) % 7) % 5


def draw_name_tag(img, cx, bottom, name, spec=None, t=0, scale=2):
    """Draw the bubble with the name. (cx, bottom) is the bottom-middle of the bubble."""
    spec = spec or catalog.DEFAULTS["name"]
    bg = spec.get("bg", "#ffffff")
    fg = spec.get("fg") or readable_on(bg)
    border = spec.get("border") or shade(bg, 0.5)
    fx = spec.get("fx")
    u = 3
    tw, th = text_size(name, scale)
    x0, x1 = int(cx - tw // 2 - 3 * u), int(cx + tw // 2 + 3 * u)
    y0, y1 = int(bottom - th - 2 * u), int(bottom)
    d = ImageDraw.Draw(img)

    if fx == "fire":
        flames = ["#ff3b1a", "#ff7a1a", "#ffb81a", "#ffe94a"]
        columns = (x1 - x0) // u + 4
        for i in range(columns):
            height = 2 + _noise(i, t)
            fx_x = x0 - 2 * u + i * u
            for k in range(height):
                colour = flames[min(3, k * 4 // max(1, height))]
                d.rectangle([fx_x, y0 - (k + 1) * u, fx_x + u - 1, y0 - k * u - 1], fill=rgb(colour))
        for side_x in (x0 - 2 * u, x0 - u, x1 + 1, x1 + u + 1):
            for k in range((y1 - y0) // u + 1):
                if _noise(k + side_x, t) > 1:
                    d.rectangle([side_x, y1 - (k + 1) * u, side_x + u - 1, y1 - k * u - 1],
                                fill=rgb(flames[min(3, k // 2)]))
    elif fx == "glow":
        for grow, strength in ((3 * u, 0.25), (2 * u, 0.5), (u, 0.8)):
            d.rectangle([x0 - grow, y0 - grow, x1 + grow, y1 + grow], fill=mix("#16122b", border, strength))

    d.rectangle([x0, y0, x1, y1], fill=rgb(border))
    d.rectangle([x0 + u, y0 + u, x1 - u, y1 - u], fill=rgb(bg))
    if fx == "gold":
        d.rectangle([x0 + u, y0 + u, x1 - u, y0 + 2 * u], fill=rgb("#fff3a8"))
        d.rectangle([x0 + u, y1 - 2 * u, x1 - u, y1 - u], fill=rgb("#d9a520"))
    draw_text(img, (cx, (y0 + y1) // 2 + 1), name, scale, fg, "mm")

    def stamp(shape, colour, left):
        width = len(shape[0]) * u
        sx = x0 - width - u if left else x1 + u + 1
        sy = (y0 + y1) // 2 - len(shape) * u // 2
        for ry, row in enumerate(shape):
            for rx, cell in enumerate(row):
                if cell == "#":
                    d.rectangle([sx + rx * u, sy + ry * u, sx + (rx + 1) * u - 1, sy + (ry + 1) * u - 1],
                                fill=rgb(colour))

    if fx == "stars":
        star = [".#.", "###", ".#."]
        stamp(star, "#ffe94a", True)
        stamp(star, "#ffe94a", False)
    elif fx == "hearts":
        heart = ["#.#", "###", ".#."]
        stamp(heart, "#ff4f8b", True)
        stamp(heart, "#ff4f8b", False)
    elif fx == "bolt":
        bolt = [".##", "##.", ".##", "##."]
        stamp(bolt, "#ffe94a", True)
        stamp(bolt, "#ffe94a", False)
    return (x0, y0, x1, y1)
