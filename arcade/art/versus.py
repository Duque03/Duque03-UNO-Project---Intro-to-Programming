"""The "choose your opponent" panel shown when the player presses E at a table."""

from __future__ import annotations

from PIL import Image, ImageDraw

from arcade.art import sprites
from arcade.art.pixel import coin, darken, draw_text, key_icon, panel, rgb, shade
from arcade.config import LEVEL_COINS, LEVELS, SCREEN_H, SCREEN_W

LEVEL_COLOURS = {"easy": "#3ad678", "medium": "#ffd84a", "hard": "#ff9a3a", "expert": "#ff4f6d"}
CARD_W, CARD_H, GAP, CARD_TOP = 156, 286, 12, 112
FOCUS = "#ffe94a"  # the yellow highlight that the arrow keys move
HINT = "ARROWS + SPACE, A NUMBER OR CLICK TO PICK  -  ENTER: PLAY  -  ESC: BACK"


_STAR = ["..#..", ".###.", "#####", ".###.", ".#.#."]


def _star(d, x, y, colour, u=2):
    for row, line in enumerate(_STAR):
        for column, cell in enumerate(line):
            if cell == "#":
                d.rectangle([x + column * u, y + row * u, x + (column + 1) * u - 1, y + (row + 1) * u - 1],
                            fill=rgb(colour))


def card(cardinfo: dict, picked: bool, number: int, t: int = 0) -> Image.Image:
    """One bot: its character, name tag, level, stars and coins."""
    level = cardinfo["level"]
    colour = LEVEL_COLOURS[level]
    img = Image.new("RGB", (CARD_W, CARD_H), rgb("#17123a"))
    d = ImageDraw.Draw(img)
    for y in range(CARD_H):  # the level colour glows up from the bottom
        d.line([(0, y), (CARD_W, y)], fill=shade(colour, 0.12 + 0.28 * (y / CARD_H) ** 2))
    d.ellipse([20, 196, CARD_W - 20, 222], fill=shade(colour, 0.5))  # spotlight on the floor
    sprites.draw_character(img, CARD_W // 2, 216, cardinfo["look"], "down", 0, t, scale=5)
    sprites.draw_name_tag(img, CARD_W // 2, 58, cardinfo["name"], cardinfo.get("tag"), t)
    draw_text(img, (CARD_W // 2, 236), level.upper(), 3, colour, "mt", shadow="#16122b")
    for i in range(len(LEVELS)):
        _star(d, CARD_W // 2 - 32 + i * 17, 262, colour if i <= LEVELS.index(level) else "#3a2f6b")
    border = "#ffffff" if picked else shade(colour, 0.7)
    d.rectangle([0, 0, CARD_W - 1, CARD_H - 1], outline=rgb(border), width=5 if picked else 3)
    key_icon(img, 8, 8, str(number), 2)
    if picked:  # a big tick in the corner
        for x, y in ((CARD_W - 34, 18), (CARD_W - 28, 24), (CARD_W - 22, 18), (CARD_W - 16, 12), (CARD_W - 10, 6)):
            d.rectangle([x - 1, y - 1, x + 8, y + 8], fill=rgb("#16122b"))
        for x, y in ((CARD_W - 34, 18), (CARD_W - 28, 24), (CARD_W - 22, 18), (CARD_W - 16, 12), (CARD_W - 10, 6)):
            d.rectangle([x, y, x + 6, y + 6], fill=rgb("#3ad678"))
    return img


def panel_picture(background, title: str, cards: list[dict], picked: list[str], needed: int,
                  prize: int | None, t: int = 0, focus: int | None = None):
    """The whole picker on top of the (dimmed) room. Returns (image, regions); a region's action is ("pick", name).

    focus: the bot the arrow keys are on (a yellow frame around its card), or None.
    """
    if focus is not None and not 0 <= focus < len(cards):
        raise ValueError("the highlight must be on one of the bots")
    img = darken(background.copy() if background else Image.new("RGB", (SCREEN_W, SCREEN_H)), 0.35)
    panel(img, (40, 24, SCREEN_W - 40, SCREEN_H - 24), "#0f0b2a", "#3ad6ff", bw=4)
    draw_text(img, (SCREEN_W // 2, 46), title, 4, "#ffe94a", "mt", shadow="#16122b")
    regions = []
    left = (SCREEN_W - (len(cards) * CARD_W + (len(cards) - 1) * GAP)) // 2
    for i, info in enumerate(cards):
        x = left + i * (CARD_W + GAP)
        chosen = info["name"] in picked
        y = CARD_TOP - (8 if chosen else 0)
        img.paste(card(info, chosen, i + 1, t), (x, y))
        if i == focus:
            ImageDraw.Draw(img).rectangle([x - 5, y - 5, x + CARD_W + 4, y + CARD_H + 4], outline=rgb(FOCUS), width=4)
        cx = x + CARD_W // 2
        coin(img, cx - 40, y + CARD_H + 10, 2)
        draw_text(img, (cx - 20, y + CARD_H + 10), f"+{LEVEL_COINS[info['level']]}", 2, "#ffe94a", "lt")
        regions.append(((x, y, x + CARD_W, y + CARD_H + 30), ("pick", info["name"])))
    if prize is not None:
        line, colour = f"WIN AND GET {prize} COINS", "#ffe94a"
    else:
        left_to_pick = needed - len(picked)
        line, colour = f"PICK {left_to_pick} MORE", "#d9d4ff"
    draw_text(img, (SCREEN_W // 2, 452), line, 3, colour, "mt", shadow="#16122b")
    draw_text(img, (SCREEN_W // 2, 488), HINT, 2, "#b9b0e8", "mt")
    return img, regions
