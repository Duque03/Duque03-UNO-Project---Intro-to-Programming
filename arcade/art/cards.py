"""Draws the playing cards for the UNO table (our own simple card design)."""

from __future__ import annotations

from PIL import ImageDraw

from arcade.art.pixel import draw_text, mix, rgb, shade

CARD_W, CARD_H = 66, 96
COLOUR_HEX = {"red": "#e2413c", "yellow": "#f2c230", "green": "#3fae5a", "blue": "#3a78e8", "wild": "#1d1a2b"}
_BIG = {"skip": ("SKIP", 2), "reverse": ("<>", 4), "draw2": ("+2", 4), "wild": ("WILD", 2), "wild4": ("+4", 4)}
_SMALL = {"skip": "SKIP", "reverse": "<>", "draw2": "+2", "wild": "W", "wild4": "+4"}


def _body(d, x, y, w, h, fill, edge):
    d.rectangle([x + 3, y, x + w - 4, y + h - 1], fill=edge)
    d.rectangle([x, y + 3, x + w - 1, y + h - 4], fill=edge)
    d.rectangle([x + 6, y + 6, x + w - 7, y + h - 7], fill=fill)


def draw_card(img, x, y, card, dim=False, glow=False):
    """Draw one face-up card with its top-left corner at (x, y)."""
    colour, value = card
    d = ImageDraw.Draw(img)
    w, h = CARD_W, CARD_H
    x, y = int(x), int(y)
    fill = rgb(COLOUR_HEX[colour])
    edge, ink = (255, 255, 255), (255, 255, 255)
    if dim:
        fill, edge, ink = mix(fill, "#16122b", 0.55), (150, 146, 170), (170, 166, 190)
    d.rectangle([x + 4, y + 4, x + w + 3, y + h + 3], fill=(10, 8, 24))  # shadow
    if glow:
        d.rectangle([x - 3, y - 3, x + w + 2, y + h + 2], fill=(255, 233, 74))
    _body(d, x, y, w, h, fill, edge)
    d.rectangle([x + 12, y + 20, x + w - 13, y + h - 21], outline=shade(fill, 1.35), width=3)
    if colour == "wild":
        size = 12
        cx, cy = x + w // 2, y + h // 2 - (16 if value == "wild4" else 14)
        for i, name in enumerate(("red", "yellow", "green", "blue")):
            quad = rgb(COLOUR_HEX[name])
            if dim:
                quad = mix(quad, "#16122b", 0.55)
            qx, qy = cx - size + (i % 2) * size, cy - size + (i // 2) * size
            d.rectangle([qx, qy, qx + size - 1, qy + size - 1], fill=quad)
        label, scale = _BIG[value]
        draw_text(img, (x + w // 2, y + h - 24), label, 2 if value == "wild" else 3, ink, "mm", shadow=(10, 8, 24))
    else:
        label, scale = _BIG.get(value, (value, 6))
        draw_text(img, (x + w // 2 + 1, y + h // 2), label, scale, ink, "mm", shadow=shade(fill, 0.45))
    draw_text(img, (x + 9, y + 9), _SMALL.get(value, value), 1, ink, "lt")


def draw_back(img, x, y, w=CARD_W, h=CARD_H):
    """A face-down card."""
    d = ImageDraw.Draw(img)
    x, y = int(x), int(y)
    d.rectangle([x + 3, y + 3, x + w + 2, y + h + 2], fill=(10, 8, 24))
    unit = 3 if w >= 40 else 1
    d.rectangle([x + unit, y, x + w - unit - 1, y + h - 1], fill=(255, 255, 255))
    d.rectangle([x, y + unit, x + w - 1, y + h - unit - 1], fill=(255, 255, 255))
    d.rectangle([x + 2 * unit, y + 2 * unit, x + w - 2 * unit - 1, y + h - 2 * unit - 1], fill=(58, 34, 110))
    if w >= 40:
        for i, colour in enumerate(("#ff4fa3", "#3ad6ff", "#ffe94a")):
            d.rectangle([x + 18 + i * 3, y + 30 + i * 12, x + w - 19 - i * 3, y + 36 + i * 12], fill=rgb(colour))
