"""Draws the playing cards for the UNO table (our own pixel card design, not the shop game's)."""

from __future__ import annotations

from PIL import Image, ImageDraw

from arcade.art.pixel import draw_text, mix, rgb, shade

CARD_W, CARD_H = 66, 96
COLOUR_HEX = {"red": "#e2413c", "yellow": "#f2c230", "green": "#3fae5a", "blue": "#3a78e8", "wild": "#1d1a2b"}

# Our own chunky pixel glyphs ("X" = a pixel), drawn white with a dark outline in the middle of the card.
DIGITS = {
    "0": [".XXXX.", "XXXXXX", "XX..XX", "XX..XX", "XX..XX", "XX..XX", "XX..XX", "XXXXXX", ".XXXX."],
    "1": ["..XX..", ".XXX..", "XXXX..", "..XX..", "..XX..", "..XX..", "..XX..", "XXXXXX", "XXXXXX"],
    "2": [".XXXX.", "XXXXXX", "XX..XX", "....XX", "...XXX", "..XXX.", ".XXX..", "XXXXXX", "XXXXXX"],
    "3": ["XXXXX.", "XXXXXX", "....XX", "..XXXX", "..XXX.", "....XX", "....XX", "XXXXXX", "XXXXX."],
    "4": ["...XX.", "..XXX.", ".XXXX.", "XX.XX.", "XXXXXX", "XXXXXX", "...XX.", "...XX.", "...XX."],
    "5": ["XXXXXX", "XXXXXX", "XX....", "XXXXX.", "XXXXXX", "....XX", "....XX", "XXXXXX", "XXXXX."],
    "6": [".XXXX.", "XXXXX.", "XX....", "XXXXX.", "XXXXXX", "XX..XX", "XX..XX", "XXXXXX", ".XXXX."],
    "7": ["XXXXXX", "XXXXXX", "....XX", "...XX.", "...XX.", "..XX..", "..XX..", "..XX..", "..XX.."],
    "8": [".XXXX.", "XXXXXX", "XX..XX", "XXXXXX", ".XXXX.", "XX..XX", "XX..XX", "XXXXXX", ".XXXX."],
    "9": [".XXXX.", "XXXXXX", "XX..XX", "XX..XX", "XXXXXX", ".XXXXX", "....XX", ".XXXXX", ".XXXX."],
    "+": ["......", "......", "..XX..", "..XX..", "XXXXXX", "XXXXXX", "..XX..", "..XX..", "......"],
}
# Skip: jump over the next player (two arrowheads and a bar). Reverse: one arrow each way.
SKIP = ["X....X.....XX", "XX...XX....XX", "XXX..XXX...XX", "XXXX.XXXX..XX", "XXXXXXXXXX.XX",
        "XXXX.XXXX..XX", "XXX..XXX...XX", "XX...XX....XX", "X....X.....XX"]
_RIGHT = ["........X....", "........XX...", "XXXXXXXXXXX..", "XXXXXXXXXXXX.", "XXXXXXXXXXX..",
          "........XX...", "........X...."]
REVERSE = _RIGHT + ["............."] + [row[::-1] for row in _RIGHT]


def _join(*glyphs, gap=1):
    """Glyphs side by side, with `gap` empty columns between them."""
    return ["".join((g[r] + "." * gap) for g in glyphs)[:-gap or None] for r in range(len(glyphs[0]))]


def _stamp(d, bitmap, x, y, unit, colour):
    for r, row in enumerate(bitmap):
        for c, ch in enumerate(row):
            if ch == "X":
                d.rectangle([x + c * unit, y + r * unit, x + (c + 1) * unit - 1, y + (r + 1) * unit - 1], fill=colour)


def _glyph(d, bitmap, cx, cy, unit, ink, outline):
    """A glyph centred on (cx, cy), with a one-pixel outline all round and a shadow underneath."""
    x, y = cx - len(bitmap[0]) * unit // 2, cy - len(bitmap) * unit // 2
    _stamp(d, bitmap, x + unit, y + 2 * unit, unit, outline)
    for dx in (-unit, 0, unit):
        for dy in (-unit, 0, unit):
            _stamp(d, bitmap, x + dx, y + dy, unit, outline)
    _stamp(d, bitmap, x, y, unit, ink)


def _diamond(d, cx, cy, radius, unit, colours, outline):
    """The wild sign: a diamond in four colours (top-left, top-right, bottom-left, bottom-right)."""
    for row in range(-radius - 1, radius + 2):
        for col in range(-radius - 1, radius + 2):
            inside = abs(row + 0.5) + abs(col + 0.5) <= radius
            edge = abs(row + 0.5) + abs(col + 0.5) <= radius + 1.2
            if not edge:
                continue
            colour = outline if not inside else colours[(row >= 0) * 2 + (col >= 0)]
            px, py = cx + col * unit, cy + row * unit
            d.rectangle([px, py, px + unit - 1, py + unit - 1], fill=colour)


def _corner(d, img, x, y, value, ink, outline):
    """The small sign in the top-left corner (what shows when the cards overlap in the hand)."""
    if value in ("skip", "reverse"):
        _glyph(d, SKIP if value == "skip" else REVERSE, x + 14, y + 13, 1, ink, outline)
    elif value in ("wild", "wild4"):
        _diamond(d, x + 13, y + 13, 4, 1, [rgb(COLOUR_HEX[c]) for c in ("red", "yellow", "green", "blue")], ink)
        if value == "wild4":
            draw_text(img, (x + 21, y + 9), "+4", 1, ink, "lt", shadow=outline)
    else:
        draw_text(img, (x + 9, y + 9), {"draw2": "+2"}.get(value, value), 1, ink, "lt", shadow=outline)


def _body(d, x, y, w, h, fill, edge):
    d.rectangle([x + 3, y, x + w - 4, y + h - 1], fill=edge)
    d.rectangle([x, y + 3, x + w - 1, y + h - 4], fill=edge)
    d.rectangle([x + 6, y + 6, x + w - 7, y + h - 7], fill=fill)


def draw_card(img, x, y, card, dim=False, glow=False):
    """Draw one face-up card with its top-left corner at (x, y). Our own pixel design (see DIGITS, SKIP, REVERSE)."""
    colour, value = card
    d = ImageDraw.Draw(img)
    w, h = CARD_W, CARD_H
    x, y = int(x), int(y)
    fill = rgb(COLOUR_HEX[colour])
    edge, ink = (255, 255, 255), (255, 255, 255)
    quads = [rgb(COLOUR_HEX[c]) for c in ("red", "yellow", "green", "blue")]
    if dim:
        fill, edge, ink = mix(fill, "#16122b", 0.55), (150, 146, 170), (170, 166, 190)
        quads = [mix(q, "#16122b", 0.55) for q in quads]
    outline = shade(fill, 0.4) if colour != "wild" else (6, 5, 14)
    d.rectangle([x + 4, y + 4, x + w + 3, y + h + 3], fill=(10, 8, 24))  # shadow
    if glow:
        d.rectangle([x - 3, y - 3, x + w + 2, y + h + 2], fill=(255, 233, 74))
    _body(d, x, y, w, h, fill, edge)
    # a light top edge and a darker bottom edge make the card look like a raised pixel tile
    d.rectangle([x + 6, y + 6, x + w - 7, y + 8], fill=shade(fill, 1.25) if colour != "wild" else (52, 47, 74))
    d.rectangle([x + 6, y + h - 9, x + w - 7, y + h - 7], fill=shade(fill, 0.78) if colour != "wild" else (8, 7, 18))
    # the middle panel the sign sits on
    panel = shade(fill, 0.86) if colour != "wild" else (40, 36, 60)
    d.rectangle([x + 12, y + 22, x + w - 13, y + h - 23], fill=panel)
    d.rectangle([x + 15, y + 19, x + w - 16, y + h - 20], fill=panel)
    cx, cy = x + w // 2, y + h // 2
    if value == "wild":
        _diamond(d, cx - 1, cy - 1, 7, 3, quads, ink)
    elif value == "wild4":
        _diamond(d, cx - 1, cy - 14, 4, 3, quads, ink)
        _glyph(d, _join(DIGITS["+"], DIGITS["4"]), cx, cy + 15, 3, ink, outline)
    elif value == "draw2":
        _glyph(d, _join(DIGITS["+"], DIGITS["2"]), cx, cy, 3, ink, outline)
    elif value == "skip":
        _glyph(d, SKIP, cx, cy, 3, ink, outline)
    elif value == "reverse":
        _glyph(d, REVERSE, cx, cy, 3, ink, outline)
    else:
        _glyph(d, DIGITS[value], cx, cy, 4, ink, outline)
    _corner(d, img, x, y, value, ink, outline)


def draw_back(img, x, y, w=CARD_W, h=CARD_H):
    """A face-down card."""
    d = ImageDraw.Draw(img)
    x, y = int(x), int(y)
    d.rectangle([x + 3, y + 3, x + w + 2, y + h + 2], fill=(10, 8, 24))
    unit = 3 if w >= 60 else 2 if w >= 36 else 1  # the white border: thinner on the small cards in the fans
    d.rectangle([x + unit, y, x + w - unit - 1, y + h - 1], fill=(255, 255, 255))
    d.rectangle([x, y + unit, x + w - 1, y + h - unit - 1], fill=(255, 255, 255))
    d.rectangle([x + 2 * unit, y + 2 * unit, x + w - 2 * unit - 1, y + h - 2 * unit - 1], fill=(58, 34, 110))
    if w >= 60:
        for i, colour in enumerate(("#ff4fa3", "#3ad6ff", "#ffe94a")):
            d.rectangle([x + 18 + i * 3, y + 30 + i * 12, x + w - 19 - i * 3, y + 36 + i * 12], fill=rgb(colour))


def card_sprite(card):
    """One face-up card on a see-through picture (with its shadow), for the animations on the table."""
    img = Image.new("RGBA", (CARD_W + 4, CARD_H + 4), (0, 0, 0, 0))
    draw_card(img, 0, 0, card)
    return img


def back_sprite():
    """One face-down card on a see-through picture (with its shadow), for the animations on the table."""
    img = Image.new("RGBA", (CARD_W + 3, CARD_H + 3), (0, 0, 0, 0))
    draw_back(img, 0, 0)
    return img


LYING = 0.6  # a card lying on the table looks this tall (perspective), next to one held up


def lie(sprite, scale=1.0):
    """A card picture as it looks lying flat on the table: shorter, the far edge a little narrower.
    scale makes it bigger (the piles in the middle of the table)."""
    w, h = round(sprite.width * scale), sprite.height * scale
    flat = sprite.resize((w, round(h * LYING)), Image.NEAREST)
    inset = 3  # how much narrower the far edge looks, on each side
    out = Image.new("RGBA", flat.size, (0, 0, 0, 0))
    for y in range(flat.height):
        cut = round(inset * (1 - y / max(1, flat.height - 1)))
        row = flat.crop((0, y, w, y + 1)).resize((w - 2 * cut, 1), Image.NEAREST)
        out.paste(row, (cut, y))
    return out


def draw_lying_card(img, x, y, card, scale=1.0):
    """A face-up card lying on the table, its far-left corner at (x, y)."""
    face = lie(card_sprite(card), scale)
    img.paste(face, (int(x), int(y)), face)


def draw_lying_back(img, x, y, scale=1.0):
    """A face-down card lying on the table, its far-left corner at (x, y)."""
    back = lie(back_sprite(), scale)
    img.paste(back, (int(x), int(y)), back)


# The player's own left hand holding the cards (first person): O outline, T thumb, P palm, D palm in shadow, S sleeve.
HAND = ["......OO..", ".....OTTO.", ".....OTTO.", "OOOOOOTTO.", "OPPPPPTTO.", "OPPPPPPPO.", "OPPPPPPPO.",
        "ODDPPPPO..", ".OSSSSSO..", ".OSSSSSO..", ".OSSSSSO..", ".OSSSSSO.."]
HAND_UNIT = 8  # the size of one of its pixels (it is close to the eye, so it looks big)


def draw_holding_hand(img, x, y, skin, sleeve, right=False):
    """One of the player's hands at the bottom of the picture, its top-left corner at (x, y); right: the right hand
    (the left one turned over). The sleeve goes on down to the bottom of the picture."""
    d = ImageDraw.Draw(img)
    colours = {"O": (16, 12, 34), "T": rgb(skin), "P": rgb(skin), "D": shade(rgb(skin), 0.8), "S": rgb(sleeve)}
    rows = HAND + [HAND[-1]] * 6
    u = HAND_UNIT
    for r, row in enumerate(rows):
        for c, ch in enumerate(row[::-1] if right else row):
            if ch in colours:
                d.rectangle([x + c * u, y + r * u, x + c * u + u - 1, y + r * u + u - 1], fill=colours[ch])
