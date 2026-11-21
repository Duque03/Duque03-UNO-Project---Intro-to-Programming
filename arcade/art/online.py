"""Pictures of the online screens: the online menu and the join screen (type a code). The lobby itself is a room
like the arcade (screens/online_room.py, art/chat.py).

Everything to choose is drawn on the picture, like the title screen and the pause menu: the arrow keys move a yellow
highlight and a click does the same as Enter. Each picture function returns (picture, regions).
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from arcade.art import sprites, title_layers
from arcade.art.pixel import draw_text, panel, rgb, wrap
from arcade.art.scenes import FOCUS, draw_button
from arcade.config import SCREEN_H, SCREEN_W

PAD_COLUMNS, PAD_KEY, PAD_GAP = 5, (70, 44), 10  # the on-screen keyboard of the join screen
PAD_ACTIONS = ["DEL", "JOIN", "BACK"]


PANEL = (196, 30, SCREEN_W - 196, SCREEN_H - 30)  # the box in the middle; the title screen shows around it


def _frame(title: str) -> Image.Image:
    """The title screen's own background (so coming here from its menu only brings up this box) and the box."""
    img = title_layers.still().copy()
    panel(img, PANEL, "#0f0b2a", "#3ad6ff", bw=4)
    draw_text(img, (SCREEN_W // 2, PANEL[1] + 20), title, 5, "#ffe94a", "mt", shadow="#16122b")
    return img


def _message(img, message: str, y: int, good: bool = False) -> None:
    for i, line in enumerate(wrap(message.upper(), 38)):
        draw_text(img, (SCREEN_W // 2, y + i * 22), line, 2, "#7cff3a" if good else "#ff8a8a", "mt", shadow="#16122b")


# ---------------------------------------------------------------- the online menu

def menu_picture(me: dict, options: list[dict], focus: int, message: str = ""):
    """PLAY ONLINE: you, ready to play, and the menu (options: label, action, key). Returns (picture, regions)."""
    img = _frame("PLAY ONLINE")
    draw_text(img, (SCREEN_W // 2, 92), "PLAY WITH FRIENDS ON THEIR OWN", 2, "#d9d4ff", "mt")
    draw_text(img, (SCREEN_W // 2, 114), "PHONES OR LAPTOPS - UP TO 4, NO BOTS", 2, "#7cff3a", "mt")
    body = sprites.sprite(*me["look"], "down", 0, 0)  # big, next to the buttons (no spotlight: just the character)
    scale = 8
    x, feet = 296, 414
    sprites.draw_character(img, x, feet, me["look"], "down", 0, 0, scale=scale)
    head = body.getbbox()[1]  # (the sprite has room above the head: the tag sits just over the hair)
    sprites.draw_name_tag(img, x, feet - (body.height - head) * scale - 8, me["name"], me.get("tag"))
    regions = []
    for i, option in enumerate(options):
        y = 160 + i * 66
        box = draw_button(img, (390, y, 740, y + 52), option["label"], 3, fill=FOCUS if i == focus else "#ffffff",
                          key=option.get("key"))
        regions.append((box, ("menu", option["action"])))
    if message:
        _message(img, message, 438)
    else:
        draw_text(img, (565, 446), "ARROWS: CHOOSE  -  ENTER: OK", 2, "#b9b0e8", "mt")
    return img, regions


# ---------------------------------------------------------------- the join screen

def pad_keys(letters: str) -> list[str]:
    """The keys of the on-screen keyboard, in the order the highlight counts them."""
    return list(letters) + PAD_ACTIONS


def join_picture(code: str, letters: str, focus: int, message: str = ""):
    """JOIN A LOBBY: four boxes for the code, like an arcade's high-score letters, and an on-screen keyboard.

    Returns (picture, regions); a region's action is ("key", "A") for a letter, or ("key", "DEL" / "JOIN" / "BACK").
    """
    img = _frame("JOIN A LOBBY")
    d = ImageDraw.Draw(img)
    draw_text(img, (SCREEN_W // 2, 96), "TYPE YOUR FRIEND'S CODE", 2, "#d9d4ff", "mt")
    for i in range(4):  # the code so far
        x = SCREEN_W // 2 - 2 * 76 + i * 76
        here = i == len(code)
        d.rectangle([x + 4, 128, x + 68, 196], fill=rgb("#1b1546"), outline=rgb(FOCUS if here else "#3a2f6b"),
                    width=4 if here else 3)
        if i < len(code):
            draw_text(img, (x + 36, 164), code[i], 6, "#ffffff", "mm", shadow="#3a2f6b")
        elif here:
            d.rectangle([x + 20, 182, x + 52, 186], fill=rgb(FOCUS))
    if message:
        _message(img, message, 204)
    regions = []
    width = PAD_COLUMNS * PAD_KEY[0] + (PAD_COLUMNS - 1) * PAD_GAP
    left, top = (SCREEN_W - width) // 2, 222
    for i, label in enumerate(letters):
        row, col = divmod(i, PAD_COLUMNS)
        x, y = left + col * (PAD_KEY[0] + PAD_GAP), top + row * (PAD_KEY[1] + PAD_GAP)
        box = draw_button(img, (x, y, x + PAD_KEY[0], y + PAD_KEY[1]), label, 3,
                          fill=FOCUS if i == focus else "#ffffff")
        regions.append((box, ("key", label)))
    rows = -(-len(letters) // PAD_COLUMNS)
    y = top + rows * (PAD_KEY[1] + PAD_GAP) + 2
    third = (width - 2 * PAD_GAP) // 3
    for k, label in enumerate(PAD_ACTIONS):
        x = left + k * (third + PAD_GAP)
        index = len(letters) + k
        fill = FOCUS if index == focus else ("#7cff3a" if label == "JOIN" and len(code) == 4 else "#ffffff")
        box = draw_button(img, (x, y, x + third, y + PAD_KEY[1]), label, 3, fill=fill)
        regions.append((box, ("key", label)))
    draw_text(img, (SCREEN_W // 2, y + 50), "ENTER: OK  -  ESC: BACK", 2, "#b9b0e8", "mt")
    return img, regions
