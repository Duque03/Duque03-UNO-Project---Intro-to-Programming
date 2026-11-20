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
from arcade.art.pixel import draw_text, mix, new_layer, outlined, readable_on, rgb, shade, text_size

SPR_W, SPR_H = 20, 28  # sprite canvas (room for tall hair)
OX, OY = 2, 6  # where the 16x22 figure starts inside that canvas
RAINBOW = ["#ff4f6d", "#ff9f1a", "#ffe94a", "#4ade80", "#3ad6ff", "#a06bff"]

# Hair shapes as rectangles (x, y, w, h, colour index) on the 16x22 figure.
# Colour index: 0 = main colour (c1), 1 = accent (c2), 2 = hair under a hat (c3),
# 3 = main colour darker, 4 = main colour lighter, 5 = accent lighter.
_BASE = {
    "front": [(4, 1, 8, 3, 0), (3, 2, 1, 4, 0), (12, 2, 1, 4, 0)],
    "back": [(4, 1, 8, 7, 0), (3, 2, 1, 5, 0), (12, 2, 1, 5, 0)],
    "side": [(4, 1, 8, 3, 0), (8, 2, 4, 6, 0), (12, 3, 1, 4, 0)],
}
_LONG = {
    "front": [(3, 6, 1, 7, 0), (12, 6, 1, 7, 0), (2, 5, 1, 7, 0), (13, 5, 1, 7, 0)],
    "back": [(3, 1, 10, 12, 0), (2, 5, 12, 7, 0)],
    "side": [(8, 8, 5, 5, 0), (12, 3, 1, 9, 0)],
}
# Styles drawn on top of the basic cap of hair (_BASE).
_HAIR = {
    "short": {"front": [], "back": [], "side": []},
    "long": _LONG,
    "ponytail": {
        "front": [(13, 2, 2, 2, 0), (14, 4, 1, 5, 0)],
        "back": [(7, 7, 2, 6, 0)],
        "side": [(12, 2, 2, 2, 0), (13, 4, 1, 6, 0)],
    },
    "quiff": {  # a raised front, combed up
        "front": [(5, 0, 6, 1, 0), (6, -1, 5, 1, 0), (7, -2, 3, 1, 4), (6, 0, 4, 1, 4)],
        "back": [(5, 0, 6, 1, 0), (6, -1, 4, 1, 0)],
        "side": [(2, -1, 7, 2, 0), (3, 1, 1, 1, 0), (2, -1, 4, 1, 4)],
    },
    "curtains": {  # parted in the middle, falling at both sides of the forehead
        "front": [(4, 4, 2, 1, 0), (10, 4, 2, 1, 0), (3, 2, 1, 6, 0), (12, 2, 1, 6, 0), (7, 1, 2, 1, 3)],
        "back": [(3, 2, 10, 7, 0)],
        "side": [(4, 4, 2, 1, 0), (12, 2, 1, 6, 0), (8, 2, 4, 7, 0)],
    },
    "headband": {  # long hair held back by a sports band (colour c2)
        "front": _LONG["front"] + [(3, 3, 10, 1, 1)],
        "back": _LONG["back"] + [(3, 3, 10, 1, 1)],
        "side": _LONG["side"] + [(4, 3, 9, 1, 1)],
    },
}
# Styles that replace the basic cap of hair completely (also hats and helmets).
_FULL = {
    "mohawk": {
        "front": [(7, -4, 2, 8, 0), (6, -3, 1, 6, 1), (9, -3, 1, 6, 1)],
        "back": [(7, -4, 2, 13, 0), (6, -3, 1, 10, 1), (9, -3, 1, 10, 1)],
        "side": [(4, -4, 8, 3, 0), (3, -3, 10, 1, 1), (5, -1, 7, 4, 0)],
    },
    "buzz": {
        "front": [(4, 1, 8, 2, 0), (3, 2, 1, 2, 0), (12, 2, 1, 2, 0)],
        "back": [(4, 1, 8, 6, 0), (3, 2, 1, 4, 0), (12, 2, 1, 4, 0)],
        "side": [(4, 1, 8, 2, 0), (9, 2, 3, 4, 0), (12, 2, 1, 3, 0)],
    },
    "manbun": {  # short darker sides, long top tied in a bun (tie colour c2)
        "front": [(4, 0, 8, 3, 0), (3, 2, 1, 2, 3), (12, 2, 1, 2, 3), (6, -3, 4, 2, 0), (7, -1, 2, 1, 1)],
        "back": [(4, 0, 8, 6, 0), (3, 2, 1, 4, 3), (12, 2, 1, 4, 3), (6, -3, 4, 2, 0), (7, -1, 2, 1, 1)],
        "side": [(4, 0, 8, 3, 0), (9, 2, 3, 4, 3), (12, 3, 1, 3, 3), (9, -3, 4, 2, 0), (10, -1, 2, 1, 1)],
    },
    "slick": {  # combed straight back, with a shine
        "front": [(4, 0, 8, 3, 0), (3, 1, 1, 4, 0), (12, 1, 1, 4, 0), (5, 0, 6, 1, 4)],
        "back": [(4, 0, 8, 8, 0), (3, 1, 1, 6, 0), (12, 1, 1, 6, 0), (5, 1, 6, 1, 4)],
        "side": [(3, 0, 9, 3, 0), (8, 2, 4, 6, 0), (12, 2, 1, 5, 0), (4, 0, 7, 1, 4)],
    },
    "dreads": {  # rope strands with beads (colour c2)
        "front": [(4, 0, 8, 4, 0), (3, 1, 1, 9, 0), (12, 1, 1, 9, 0), (2, 3, 1, 8, 0), (13, 3, 1, 8, 0),
                  (5, 0, 1, 1, 3), (8, 0, 1, 1, 3), (10, 0, 1, 1, 3),
                  (2, 10, 1, 1, 1), (13, 10, 1, 1, 1), (3, 9, 1, 1, 1), (12, 9, 1, 1, 1)],
        "back": [(3, 0, 10, 9, 0), (2, 3, 12, 6, 0), (3, 9, 1, 4, 0), (5, 9, 1, 5, 0), (7, 9, 1, 4, 0),
                 (8, 9, 1, 5, 0), (10, 9, 1, 4, 0), (12, 9, 1, 5, 0),
                 (5, 13, 1, 1, 1), (8, 13, 1, 1, 1), (12, 13, 1, 1, 1), (6, 2, 1, 6, 3), (9, 2, 1, 6, 3)],
        "side": [(4, 0, 8, 4, 0), (8, 2, 5, 7, 0), (13, 3, 1, 7, 0), (9, 9, 1, 4, 0), (11, 9, 1, 5, 0),
                 (13, 10, 1, 1, 1), (9, 13, 1, 1, 1), (10, 2, 1, 6, 3)],
    },
    "cap": {  # c1 cap, c2 peak, c3 hair underneath
        "front": [(3, 2, 1, 4, 2), (12, 2, 1, 4, 2), (4, 0, 8, 1, 0), (3, 1, 10, 2, 0), (3, 3, 10, 1, 1),
                  (7, 0, 2, 1, 4)],
        "back": [(3, 3, 10, 4, 2), (4, 0, 8, 1, 0), (3, 1, 10, 3, 0), (6, 4, 4, 1, 1)],
        "side": [(9, 3, 4, 4, 2), (4, 0, 8, 1, 0), (3, 1, 10, 2, 0), (0, 3, 6, 1, 1), (6, 3, 6, 1, 0)],
    },
    "beanie": {  # c1 wool hat, c2 folded edge and pompom, c3 hair underneath
        "front": [(3, 4, 1, 2, 2), (12, 4, 1, 2, 2), (4, -2, 8, 1, 0), (3, -1, 10, 4, 0), (3, 3, 10, 1, 1),
                  (7, -3, 2, 1, 1), (5, -1, 1, 4, 3), (8, -1, 1, 4, 3), (11, -1, 1, 4, 3)],
        "back": [(3, 4, 10, 3, 2), (4, -2, 8, 1, 0), (3, -1, 10, 4, 0), (3, 3, 10, 1, 1), (7, -3, 2, 1, 1),
                 (5, -1, 1, 4, 3), (8, -1, 1, 4, 3), (11, -1, 1, 4, 3)],
        "side": [(9, 4, 4, 3, 2), (4, -2, 8, 1, 0), (3, -1, 10, 4, 0), (3, 3, 10, 1, 1), (9, -3, 2, 1, 1),
                 (6, -1, 1, 4, 3), (9, -1, 1, 4, 3)],
    },
    "campino": {  # Ribatejo stocking cap: c1 green, c2 red edge and tip, c3 hair
        "front": [(3, 4, 1, 2, 2), (12, 4, 1, 2, 2), (4, -1, 8, 1, 0), (3, 0, 10, 3, 0), (3, 3, 10, 1, 1),
                  (11, -2, 3, 1, 0), (13, -1, 2, 2, 0), (14, 1, 1, 3, 0), (14, 4, 2, 2, 1)],
        "back": [(3, 4, 10, 3, 2), (4, -1, 8, 1, 0), (3, 0, 10, 3, 0), (3, 3, 10, 1, 1),
                 (2, -2, 3, 1, 0), (1, -1, 2, 2, 0), (1, 1, 1, 3, 0), (0, 4, 2, 2, 1)],
        "side": [(9, 4, 4, 3, 2), (4, -1, 8, 1, 0), (3, 0, 10, 3, 0), (3, 3, 10, 1, 1),
                 (10, -2, 4, 1, 0), (13, -1, 2, 3, 0), (14, 2, 1, 3, 0), (14, 5, 2, 2, 1)],
    },
    "dean": {  # grey hair with a side parting, and glasses (c2 frames). Worn by the bot DEAN.
        "front": [(4, 1, 8, 3, 0), (3, 2, 1, 4, 0), (12, 2, 1, 4, 0), (6, 1, 1, 2, 3),
                  (5, 4, 2, 1, 1), (9, 4, 2, 1, 1), (5, 5, 1, 2, 1), (7, 5, 2, 1, 1), (10, 5, 1, 2, 1)],
        "back": [(4, 1, 8, 7, 0), (3, 2, 1, 5, 0), (12, 2, 1, 5, 0)],
        "side": [(4, 1, 8, 3, 0), (8, 2, 4, 6, 0), (12, 3, 1, 4, 0),
                 (4, 4, 3, 1, 1), (6, 5, 4, 1, 1)],
    },
    "officer": {  # security officer's peaked cap: c1 crown, c2 badge, c3 visor and the hair underneath
        "front": [(3, -1, 10, 3, 0), (4, -1, 8, 1, 4), (3, 2, 10, 1, 3), (4, 3, 8, 1, 2), (7, 0, 2, 1, 1),
                  (3, 3, 1, 3, 2), (12, 3, 1, 3, 2)],
        "back": [(3, -1, 10, 3, 0), (4, -1, 8, 1, 4), (3, 2, 10, 1, 3), (3, 3, 10, 4, 2)],
        "side": [(3, -1, 10, 3, 0), (4, -1, 8, 1, 4), (3, 2, 10, 1, 3), (1, 3, 5, 1, 2), (3, 0, 1, 1, 1),
                 (9, 3, 4, 4, 2)],
    },
    "helmet": {  # battle helmet: c1 shell, c2 glowing visor over the eyes
        "front": [(3, -1, 10, 4, 0), (2, 0, 1, 6, 0), (13, 0, 1, 6, 0), (3, 3, 10, 2, 3), (3, 5, 10, 2, 1),
                  (4, 5, 2, 1, 5), (5, -1, 3, 1, 4)],
        "back": [(3, -1, 10, 6, 0), (2, 0, 12, 6, 0), (3, 5, 10, 1, 3), (2, 5, 1, 1, 1), (13, 5, 1, 1, 1),
                 (5, -1, 3, 1, 4)],
        "side": [(3, -1, 10, 4, 0), (12, 0, 2, 6, 0), (3, 3, 9, 2, 3), (2, 5, 6, 2, 1), (2, 5, 2, 1, 5),
                 (10, 2, 2, 4, 0), (5, -1, 3, 1, 4)],
    },
}
HAIR_STYLES = sorted(set(_HAIR) | set(_FULL))


def _hair_rects(style: str, view: str):
    if style in _FULL:
        return _FULL[style][view]
    return _BASE[view] + _HAIR.get(style, _HAIR["short"])[view]


def _hair_colours(spec: dict) -> list:
    c1 = spec["c1"]
    c2 = spec.get("c2", c1)
    r, g, b = rgb(c1)
    darker = mix(c1, "#ffffff", 0.2) if r + g + b < 150 else shade(c1, 0.72)  # black hair shows lines lighter
    return [rgb(c1), rgb(c2), rgb(spec.get("c3", "#3a2618")), darker, shade(c1, 1.3), shade(c2, 1.45)]


def _galaxy(x: int, y: int, t: int):
    """Night-sky hair: deep purple fading to blue, with stars that twinkle."""
    colour = mix("#2a0d5e", "#1f6fd1", max(0.0, min(1.0, (y + 4) / 18)))
    sparkle = (x * 7 + y * 11 + t * 3) % 17
    if sparkle == 0:
        return (255, 255, 255)
    if sparkle == 9:
        return rgb("#ff8ac4")
    return colour


# ---------------------------------------------------------------- shirts

# 3x5 digits for the numbers on the back of football kits
_DIGITS = {
    "0": ["###", "#.#", "#.#", "#.#", "###"], "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["###", "..#", "###", "#..", "###"], "3": ["###", "..#", ".##", "..#", "###"],
    "4": ["#.#", "#.#", "###", "..#", "..#"], "5": ["###", "#..", "###", "..#", "###"],
    "6": ["###", "#..", "###", "#.#", "###"], "7": ["###", "..#", ".#.", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"], "9": ["###", "#.#", "###", "..#", "###"],
}
_CAMO = ["..AA.BB.", ".AAA..B.", "B..A.AA.", "BB...AA.", ".B.AA..B", "..AAA.BB", "A..A..B."]
_AZULEJO = ["B..B", ".LL.", ".LL.", "B..B"]
SHIRT_STYLES = ["solid", "kit", "stripes", "hoops", "halves", "sash", "camo", "plaid", "azulejo", "flag", "vest", "gold",
                "suit", "uniform"]  # the last two are worn by bots only


def _number_pixel(number: str, x: int, y: int) -> bool:
    """Is (x, y) part of the number printed on the back (rows 11 to 15, centred)?"""
    width = len(number) * 4 - 1
    left = 4 + (8 - width) // 2
    row, column = y - 11, x - left
    if not (0 <= row < 5 and 0 <= column < width) or column % 4 == 3:
        return False
    return _DIGITS[number[column // 4]][row][column % 4] == "#"


def _shirt_colour(spec: dict, x: int, y: int, t: int, view: str = "front", arm: bool = False, cuff: bool = False):
    """Colour of one shirt pixel. (x, y) are on the 16x22 figure.

    view is "front", "back" or "side"; arm is True on the sleeves, cuff on the last row of a sleeve.
    """
    style = spec.get("style", "solid")
    c1 = spec["c1"]
    c2 = spec.get("c2", "#ffffff")
    c3 = spec.get("c3", shade(c1, 0.7))
    front, back = view == "front", view == "back"
    colour = c1
    if style == "kit":
        collar = y == 10 and ((5 <= x <= 10) if back else (6 <= x <= 9) if front else (5 <= x <= 6))
        if collar or (front and y == 11 and x in (7, 8)) or cuff:
            colour = c2
    elif style == "stripes":
        colour = c2 if not arm and x in (5, 6, 9, 10) else c2 if cuff else c1
    elif style == "hoops":
        colour = c1 if ((y - 10) // 2) % 2 == 0 else c2
    elif style == "halves":
        left = x <= 7 if not arm else x > 7
        colour = c1 if left != back else c2
    elif style == "sash":
        on_band = (x + y) in (20, 21) if back else (x - y) in (-6, -5)
        colour = c2 if on_band and not arm else c1
    elif style == "camo":
        cell = _CAMO[(y - 10) % len(_CAMO)][x % 8]
        colour = {"A": c2, "B": c3}.get(cell, c1)
    elif style == "plaid":
        line_x, line_y = x % 4 == 1, (y - 10) % 4 == 2
        colour = c3 if line_x and line_y else c2 if line_x or line_y else c1
    elif style == "azulejo":
        cell = _AZULEJO[(y - 10) % 4][x % 4]
        colour = {"B": c2, "L": c3}.get(cell, c1)
        if cuff or (y == 10 and not arm):
            colour = c2
    elif style == "flag":  # green and red like the Portuguese flag, with a yellow sphere on the chest
        green_side = (x <= 6) if not arm else (x < 4)
        if back:
            green_side = (x >= 9) if not arm else (x > 11)
        colour = c1 if green_side else c2
        if front and not arm and 6 <= x <= 8 and 11 <= y <= 13:
            colour = "#ffffff" if (x, y) == (7, 12) else c3
        if y == 10 and not arm:
            colour = c3
    elif style == "vest":
        if arm:
            colour = c3
        elif front and ((x in (5, 6) or x in (9, 10)) and y in (13, 14)):
            colour = c2  # pouches
        elif x in (5, 10) and y in (10, 11):
            colour = shade(c1, 0.7)  # straps
        elif front and x in (7, 8) and y == 12:
            colour = c2
    elif style == "suit":  # c1 jacket, c2 shirt, c3 tie
        if cuff:
            colour = c2
        elif front and not arm and (6 <= x <= 9 and y <= 11 or 7 <= x <= 8 and y <= 13):
            colour = c3 if 7 <= x <= 8 and y >= 11 else c2
        elif view == "side" and not arm and x == 5 and y <= 11:
            colour = c2
    elif style == "uniform":  # security: c1 shirt, c2 badge and stripes, c3 epaulettes and pockets
        if not arm and y == 10 and (x <= 5 or x >= 10):
            colour = c3  # epaulettes
        elif arm and y == 11:
            colour = c2  # a stripe on each sleeve
        elif front and not arm and x in (9, 10) and y in (11, 12):
            colour = c2  # the badge
        elif front and not arm and x in (5, 6) and y == 12:
            colour = c3  # a chest pocket
        elif back and not arm and y in (12, 13) and 4 <= x <= 11 and (x * 3 + y) % 4 != 0:
            colour = c2  # a print across the back
    elif style == "gold":
        colour = mix(c1, "#c98a12", (y - 10) / 8)
        if (x * 7 + y * 13 + t * 5) % 11 == 0:
            colour = c2  # sparkle
        if front and x in (7, 8):
            colour = "#ffffff" if y < 16 else colour  # zip
    number = spec.get("num")
    if number and back and not arm and _number_pixel(number, x, y):
        colour = spec.get("nc", c2)
    if y == 16:
        colour = shade(colour, 0.8)
    return rgb(colour)


EYE_COLOUR = (34, 26, 30)


def _dog(r, fur: str, spec: dict, bandana: str, direction: str, step: int) -> None:
    """A dog on four legs, drawn in the space of the 16x22 figure (the bot BARK, our own design).

    fur is the coat, spec c1 the ears, c2 the muzzle, chest and socks, c3 the nose. The eyes sit where a person's
    eyes are, so the room's blink still finds them from the front.
    """
    coat, dark, light, nose = rgb(fur), shade(fur, 0.78), rgb(spec["c2"]), rgb(spec["c3"])
    ears, band = rgb(spec["c1"]), rgb(bandana)
    wag = {0: 0, 1: -1, 2: 1}[step]
    if direction in ("down", "up"):
        lift_l, lift_r = (1 if step == 1 else 0), (1 if step == 2 else 0)
        legs = (5, 9) if direction == "down" else (4, 10)
        for x, lift in zip(legs, (lift_l, lift_r)):
            r(x, 17, 2, 4 - lift, coat)
            r(x, 21 - lift, 2, 1, light)
        if direction == "down":
            r(4, 13, 8, 4, dark)                # the back half, behind the chest
            r(12 + wag, 10, 1, 3, coat)         # the tail, wagging
            r(5, 11, 6, 6, coat)                # chest
            r(7, 12, 2, 3, light)
        else:
            r(4, 10, 8, 7, coat)                # back
            r(7, 11, 2, 5, dark)
            r(7 + wag, 12, 2, 5, shade(fur, 1.12))  # the tail, closest to us
        r(5, 2, 6, 1, coat)                     # head
        r(4, 3, 8, 7, coat)
        r(2, 3, 2, 6, ears)                     # floppy ears
        r(12, 3, 2, 6, ears)
        r(3, 2, 1, 1, ears)
        r(12, 2, 1, 1, ears)
        if direction == "down":
            r(6, 5, 1, 2, EYE_COLOUR)
            r(9, 5, 1, 2, EYE_COLOUR)
            r(6, 7, 4, 2, light)                # muzzle
            r(7, 7, 2, 1, nose)
            r(8, 9, 1, 1, (255, 122, 138))      # tongue
            r(4, 10, 8, 1, band)                # bandana
            r(6, 11, 4, 1, band)
            r(7, 12, 2, 1, band)
        else:
            r(4, 10, 8, 1, band)
            r(7, 11, 2, 1, band)
    else:  # left (right is the mirror image)
        near, far = {0: (5, 11), 1: (4, 12), 2: (6, 10)}[step], {0: (7, 13), 1: (8, 10), 2: (4, 13)}[step]
        for x in far:
            r(x, 16, 2, 5, dark)
        r(5, 11, 9, 5, coat)                    # body
        r(6, 15, 7, 1, light)
        r(14, 8 + wag, 1, 4, coat)              # the tail, up and wagging
        r(15, 7 + wag, 1, 2, coat)
        for x in near:
            r(x, 16, 2, 4, coat)
            r(x, 20, 2, 1, light)
        r(3, 3, 5, 1, coat)                     # head
        r(2, 4, 7, 6, coat)
        r(0, 7, 3, 2, light)                    # muzzle
        r(0, 7, 1, 1, nose)
        r(1, 9, 3, 1, dark)
        r(4, 5, 1, 2, EYE_COLOUR)
        r(6, 4, 3, 6, ears)
        r(5, 10, 4, 1, band)
        r(4, 11, 3, 1, band)


@lru_cache(maxsize=4096)
def sprite(skin: str, pants: str, hair_id, shirt_id, direction: str = "down", step: int = 0, t: int = 0):
    """Build one character picture (20x28, transparent background)."""
    if direction == "right":
        return sprite(skin, pants, hair_id, shirt_id, "left", step, t).transpose(Image.FLIP_LEFT_RIGHT)

    img = Image.new("RGBA", (SPR_W, SPR_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    hair = catalog.spec_for("hair", hair_id)
    shirt = catalog.spec_for("shirt", shirt_id)
    if hair.get("style") == "dog":  # not a person: the bot BARK
        def dog_rect(x, y, w, h, colour):
            if w > 0 and h > 0:
                d.rectangle([OX + x, OY + y, OX + x + w - 1, OY + y + h - 1], fill=colour)
        _dog(dog_rect, skin, hair, shirt["c1"], direction, step)
        framed = new_layer((SPR_W, SPR_H + 1))
        framed.paste(img, (0, 0))
        return outlined(framed)
    skin_c, skin_dark = rgb(skin), shade(skin, 0.78)
    pants_c, pants_dark, shoe = rgb(pants), shade(pants, 0.75), (30, 26, 40)

    def r(x, y, w, h, colour):
        d.rectangle([OX + x, OY + y, OX + x + w - 1, OY + y + h - 1], fill=colour)

    def shirt_area(x0, x1, y0, y1, darker=False, view="front", arm=False):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                colour = _shirt_colour(shirt, x, y, t, view, arm, cuff=arm and y == y1)
                d.point((OX + x, OY + y), fill=shade(colour, 0.82) if darker else colour)

    if direction in ("down", "up"):
        view = "front" if direction == "down" else "back"
        lift_l, lift_r = (1 if step == 1 else 0), (1 if step == 2 else 0)
        r(5, 17, 3, 3 - lift_l, pants_c)
        r(5, 20 - lift_l, 3, 2, shoe)
        r(8, 17, 3, 3 - lift_r, pants_dark)
        r(8, 20 - lift_r, 3, 2, shoe)
        shirt_area(4, 11, 10, 16, view=view)
        swing = {0: (0, 0), 1: (1, -1), 2: (-1, 1)}[step]
        shirt_area(2, 3, 10, 13 + min(0, swing[0]), darker=True, view=view, arm=True)
        shirt_area(12, 13, 10, 13 + min(0, swing[1]), darker=True, view=view, arm=True)
        r(2, 14 + min(0, swing[0]), 2, 2, skin_c)
        r(12, 14 + min(0, swing[1]), 2, 2, skin_c)
        r(4, 2, 8, 8, skin_c)
        r(4, 9, 8, 1, skin_dark)
        if direction == "down":
            r(6, 5, 1, 2, (34, 26, 30))
            r(9, 5, 1, 2, (34, 26, 30))
            r(7, 8, 2, 1, skin_dark)
    else:  # left (right is the mirror image)
        view = "side"
        if step == 1:
            r(4, 17, 3, 3, pants_c)
            r(9, 17, 3, 3, pants_dark)
            r(3, 20, 4, 2, shoe)
            r(9, 20, 4, 2, shoe)
        else:
            r(6, 17, 4, 3, pants_c)
            r(5, 20, 5, 2, shoe)
        shirt_area(5, 10, 10, 16, view=view)
        arm_x = 7 + {0: 0, 1: -1, 2: 1}[step]
        shirt_area(arm_x, arm_x + 1, 11, 14, darker=True, view=view, arm=True)
        r(arm_x, 15, 2, 2, skin_c)
        r(4, 2, 8, 8, skin_c)
        r(4, 9, 8, 1, skin_dark)
        r(5, 5, 1, 2, (34, 26, 30))

    _draw_hair(d, hair, view, t)
    # one spare row at the bottom so the dark edge also fits under the shoes
    framed = new_layer((SPR_W, SPR_H + 1))
    framed.paste(img, (0, 0))
    return outlined(framed)


def _draw_hair(d, hair: dict, view: str, t: int) -> None:
    """The hair (or hat) on a figure, seen from the front, the back or the side."""
    colours = _hair_colours(hair)
    for x, y, w, h, index in _hair_rects(hair.get("style", "short"), view):
        if hair.get("rainbow") or hair.get("galaxy"):
            for row in range(h):
                for column in range(w):
                    px, py = x + column, y + row
                    colour = (_galaxy(px, py, t) if hair.get("galaxy")
                              else rgb(RAINBOW[(py + t) % len(RAINBOW)]))
                    d.point((OX + px, OY + py), fill=colour)
        elif w > 0 and h > 0:
            d.rectangle([OX + x, OY + y, OX + x + w - 1, OY + y + h - 1], fill=colours[index])


MANNEQUIN, HANGER = "#2e2660", "#b8b4d0"  # what the store shows the items on


def hair_item(hair_id, t: int = 0, head=MANNEQUIN):
    """A hair item on its own, as the store shows it: in front of a plain head shape in a quiet colour (no outline,
    no face, no character), so the hair keeps its form. A see-through picture cropped to the drawing."""
    hair = Image.new("RGBA", (SPR_W, SPR_H), (0, 0, 0, 0))
    _draw_hair(ImageDraw.Draw(hair), catalog.spec_for("hair", hair_id), "front", t)
    img = Image.new("RGBA", (SPR_W, SPR_H), (0, 0, 0, 0))
    ImageDraw.Draw(img).rectangle([OX + 4, OY + 2, OX + 11, OY + 9], fill=rgb(head))
    hair = outlined(hair)
    img.paste(hair, (0, 0), hair)
    return img.crop(img.getbbox())


def shirt_item(shirt_id, t: int = 0):
    """A shirt on its own, as the store shows it: flat on a hanger (no character). A see-through picture cropped to
    the drawing."""
    img = Image.new("RGBA", (SPR_W, SPR_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    shirt = catalog.spec_for("shirt", shirt_id)
    for x, y, w, h in ((7, 6, 2, 1), (8, 7, 1, 1), (4, 8, 8, 1), (3, 9, 10, 1)):  # the hook and the bar
        d.rectangle([OX + x, OY + y, OX + x + w - 1, OY + y + h - 1], fill=rgb(HANGER))
    for y in range(10, 17):
        for x in range(4, 12):
            d.point((OX + x, OY + y), fill=_shirt_colour(shirt, x, y, t, "front"))
    for x in (2, 3, 12, 13):  # the sleeves, a little darker
        for y in range(10, 14):
            d.point((OX + x, OY + y), fill=shade(_shirt_colour(shirt, x, y, t, "front", True, y == 13), 0.82))
    framed = outlined(img)
    return framed.crop(framed.getbbox())


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


def showcase(look, name, tag_item=None, t=0, scale=6):
    """The big preview in the store and the wardrobe: the character from the front, the side and the back, with the
    name tag above, on a see-through picture (the store draws the stage behind it)."""
    gap = 12
    w = 3 * SPR_W * scale + 2 * gap + 20
    h = SPR_H * scale + 64
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for k, direction in enumerate(("down", "left", "up")):
        cx = 10 + SPR_W * scale // 2 + k * (SPR_W * scale + gap)
        draw_character(img, cx, h - 4, look, direction, 0, t, scale)
    if name:
        draw_name_tag(img, w // 2, 44, name, catalog.spec_for("name", tag_item), t)
    return img


# ---------------------------------------------------------------- name tags

def _noise(i: int, t: int) -> int:
    return (i * 37 + t * 17 + (i * i) % 7) % 5


# Little pictures stamped at both ends of a tag: one letter per colour.
_STAMPS = {
    "storm": ([".##", "##.", ".##", "##."], {"#": "#ff8af0"}),
    "arraial": (["..DDDDD.D", ".DEDDDDDD", "SSSSSSSSS", ".SSSSSS.S"],  # sardines
                {"D": "#2f5f9a", "S": "#d3dbe8", "E": "#16122b"}),
    "pitch": ([".WW.", "WKWW", "WWKW", ".WW."], {"W": "#ffffff", "K": "#16122b"}),
}
FLAG_COLOURS = ["#d83a3a", "#f2d03b", "#3aa655", "#2f6fe0", "#ff8ac4"]


def draw_name_tag(img, cx, bottom, name, spec=None, t=0, scale=2):
    """Draw the bubble with the name. (cx, bottom) is the bottom-middle of the bubble.

    spec comes from arcade/catalog.py: bg, fg and border colours and an effect "fx".
    """
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

    def block(x, y, colour, w=u, h=u):
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=rgb(colour))

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
    elif fx == "storm":  # a purple glow that pulses
        pulse = 0.75 + 0.25 * ((t % 4) in (1, 2))
        for grow, strength in ((3 * u, 0.25), (2 * u, 0.5), (u, 0.8)):
            d.rectangle([x0 - grow, y0 - grow, x1 + grow, y1 + grow],
                        fill=mix("#16122b", border, strength * pulse))
    elif fx == "scarf":  # fringe at both ends, like a football scarf
        colours = [border, spec.get("border2", "#ffffff")]
        for k, y in enumerate(range(y0 + u, y1 - u + 1, u)):
            block(x0 - 2 * u, y, colours[k % 2], 2 * u, u - 1)
            block(x1 + 1, y, colours[k % 2], 2 * u, u - 1)
    elif fx == "arraial":  # a string of party flags above the tag
        d.line([x0 - u, y0 - 3 * u, x1 + u, y0 - 3 * u], fill=rgb("#16122b"), width=1)
        for k, x in enumerate(range(x0, x1 - u, 3 * u)):
            colour = rgb(FLAG_COLOURS[k % len(FLAG_COLOURS)])
            d.polygon([(x, y0 - 3 * u), (x + 2 * u, y0 - 3 * u), (x + u, y0 - u)], fill=colour)

    d.rectangle([x0, y0, x1, y1], fill=rgb(border))
    if fx == "scarf":  # the border is made of blocks of the two scarf colours
        colours = [border, spec.get("border2", "#ffffff")]
        for k, x in enumerate(range(x0, x1 + 1, 2 * u)):
            block(x, y0, colours[k % 2], min(2 * u, x1 + 1 - x), u)
            block(x, y1 - u + 1, colours[(k + 1) % 2], min(2 * u, x1 + 1 - x), u)
    d.rectangle([x0 + u, y0 + u, x1 - u, y1 - u], fill=rgb(bg))
    if fx == "pitch":  # mowed stripes, like the grass of a football pitch
        for k, x in enumerate(range(x0 + u, x1 - u + 1, 2 * u)):
            if k % 2:
                block(x, y0 + u, shade(bg, 1.15), min(2 * u, x1 - u + 1 - x), y1 - y0 - 2 * u + 1)
    draw_text(img, (cx, (y0 + y1) // 2 + 1), name, scale, fg, "mm")

    stamp = _STAMPS.get(fx)
    if stamp:
        shape, colours = stamp
        width = len(shape[0]) * u
        sy = (y0 + y1) // 2 - len(shape) * u // 2
        for left in (True, False):
            sx = x0 - width - u if left else x1 + u + 1
            for ry, row in enumerate(shape):
                cells = row if left or fx != "arraial" else row[::-1]  # the fish face each other
                for rx, cell in enumerate(cells):
                    if cell in colours:
                        block(sx + rx * u, sy + ry * u, colours[cell])
    return (x0, y0, x1, y1)
