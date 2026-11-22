"""The "choose your opponent" panel shown when the player presses E at a table.

It is drawn by the browser over the live room (arcade/room.py, from the pieces at the end of this file), so the room
keeps moving behind it and no new picture is made for each key press. panel_picture() draws the same panel as one
picture (kept for the tests and as a reference of the layout)."""

from __future__ import annotations

from PIL import Image, ImageDraw

from arcade.art import sprites
from arcade.art.scenes import draw_button
from arcade.art.pixel import coin, darken, draw_text, panel, rgb, shade
from arcade.config import LEVEL_COINS, LEVELS, SCREEN_H, SCREEN_W

LEVEL_COLOURS = {"easy": "#3ad678", "medium": "#ffd84a", "hard": "#ff9a3a", "expert": "#ff4f6d"}
CARD_W, CARD_H, GAP, CARD_TOP = 156, 286, 12, 112
FOCUS = "#ffe94a"  # the yellow highlight that the arrow keys move


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
    draw_text(img, (SCREEN_W // 2, 440), line, 3, colour, "mt", shadow="#16122b")
    back = draw_button(img, (SCREEN_W // 2 - 250, 474, SCREEN_W // 2 - 30, 512), "BACK", 2)
    play = draw_button(img, (SCREEN_W // 2 + 30, 474, SCREEN_W // 2 + 250, 512), "PLAY", 2,
                       fill="#c8f7c5" if prize is not None else "#8d8aa6")
    regions += [(back, ("back",))] + ([(play, ("play",))] if prize is not None else [])
    return img, regions


# ---- The picker drawn over the live room (arcade/room.py): the pieces, painted once and sent once.
BUTTON_W, BUTTON_H, BUTTONS_Y = 220, 38, 474
BACK_BOX = (SCREEN_W // 2 - 250, BUTTONS_Y, SCREEN_W // 2 - 30, BUTTONS_Y + BUTTON_H)
PLAY_BOX = (SCREEN_W // 2 + 30, BUTTONS_Y, SCREEN_W // 2 + 250, BUTTONS_Y + BUTTON_H)
LINE_Y = 440


def card_left(count: int) -> int:
    return (SCREEN_W - (count * CARD_W + (count - 1) * GAP)) // 2


def frame_piece(title: str) -> Image.Image:
    """The panel and its title, see-through around it (the room shows, dimmed, behind)."""
    img = Image.new("RGBA", (SCREEN_W, SCREEN_H), (0, 0, 0, 0))
    panel(img, (40, 24, SCREEN_W - 40, SCREEN_H - 24), "#0f0b2a", "#3ad6ff", bw=4)
    draw_text(img, (SCREEN_W // 2, 46), title, 4, "#ffe94a", "mt", shadow="#16122b")
    return img


def card_piece(cardinfo: dict, picked: bool, t: int = 0) -> Image.Image:
    """One bot's card with its coins underneath (30 pixels more), see-through around the coins."""
    img = Image.new("RGBA", (CARD_W, CARD_H + 30), (0, 0, 0, 0))
    img.paste(card(cardinfo, picked, 0, t), (0, 0))
    coin(img, CARD_W // 2 - 40, CARD_H + 10, 2)
    draw_text(img, (CARD_W // 2 - 20, CARD_H + 10), f"+{LEVEL_COINS[cardinfo['level']]}", 2, "#ffe94a", "lt")
    return img


def line_piece(text: str, colour: str) -> Image.Image:
    """A line of text (PICK 2 MORE, WIN AND GET 15 COINS), centred, see-through around it."""
    img = Image.new("RGBA", (SCREEN_W - 120, 30), (0, 0, 0, 0))
    draw_text(img, (img.width // 2, 0), text, 3, colour, "mt", shadow="#16122b")
    return img


def button_piece(label: str, enabled: bool = True) -> Image.Image:
    img = Image.new("RGBA", (BUTTON_W + 8, BUTTON_H + 8), (0, 0, 0, 0))
    fill = "#ffffff" if label == "BACK" else ("#c8f7c5" if enabled else "#8d8aa6")
    draw_button(img, (0, 0, BUTTON_W, BUTTON_H), label, 2, fill=fill)
    return img
