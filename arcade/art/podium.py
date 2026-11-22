"""The end of a UNO game: everyone on a podium (1st in the middle and highest, 2nd on the left, 3rd on the right,
the last one beside it on the floor), with medals, spotlights and the place numbers, all in pixel art.

podium_picture() paints the whole thing; figures() gives each character on its own (see-through), so the screen can
drop them onto their steps one by one with a browser animation (arcade/table_anim.py) before the final picture.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from arcade import catalog
from arcade.art import sprites
from arcade.art.pixel import (
    coin,
    darken,
    draw_text,
    mix,
    rgb,
    shade,
    text_size,
    wrap,
)
from arcade.art.scenes import confetti, sparkle
from arcade.config import SCREEN_H, SCREEN_W

INK = "#16122b"
GROUND = 448  # where the podium and the last player stand
BLOCK_W = 168
STEPS = {1: (480, 160, "#ffd23a"), 2: (304, 112, "#c9d3e6"), 3: (656, 76, "#e0915a")}  # middle x, height, colour
LAST_X = 860
FIGURE_SCALE = 5
MEDALS = {1: ("#ffd23a", "#e2413c"), 2: ("#dfe6f2", "#3a78e8"), 3: ("#e0915a", "#3fae5a")}  # disc, ribbon


def spots(count: int, tied: bool = False) -> list[dict]:
    """Where each player stands, from 1st to last: cx (middle), height of their step (0: on the floor), colour,
    label (the number on the step) and medal (1, 2, 3 or None). Two players: 2nd on the left of 1st; a tie: two
    equal gold steps."""
    if tied:
        return [{"cx": cx, "height": 136, "colour": "#ffd23a", "label": "1", "medal": 1} for cx in (392, 568)]
    if count == 2:
        return [{"cx": 568, "height": 160, "colour": STEPS[1][2], "label": "1", "medal": 1},
                {"cx": 392, "height": 112, "colour": STEPS[2][2], "label": "2", "medal": 2}]
    out = [{"cx": STEPS[p][0], "height": STEPS[p][1], "colour": STEPS[p][2], "label": str(p), "medal": p}
           for p in range(1, min(count, 3) + 1)]
    if count == 4:
        out.append({"cx": LAST_X, "height": 0, "colour": None, "label": "4", "medal": None})
    return out


def _block(img, spot: dict) -> None:
    """One step of the podium: a lit top, the front with the big number, darker sides (pixel art, no blur)."""
    d = ImageDraw.Draw(img)
    cx, height, colour = spot["cx"], spot["height"], spot["colour"]
    x0, x1, top = cx - BLOCK_W // 2, cx + BLOCK_W // 2, GROUND - height
    d.rectangle([x0 - 3, top - 15, x1 + 3, GROUND + 3], fill=rgb(INK))
    d.rectangle([x0, top - 12, x1, top], fill=shade(colour, 1.35))  # the top, seen from a little above
    d.rectangle([x0, top - 12, x1, top - 10], fill=shade(colour, 1.6))
    d.rectangle([x0, top + 1, x1, GROUND], fill=rgb(colour))
    d.rectangle([x0, top + 1, x0 + 8, GROUND], fill=shade(colour, 1.18))  # light edge
    d.rectangle([x1 - 8, top + 1, x1, GROUND], fill=shade(colour, 0.78))  # shaded edge
    d.rectangle([x0, GROUND - 8, x1, GROUND], fill=shade(colour, 0.7))
    number = spot["label"]
    suffix = {"1": "ST", "2": "ND", "3": "RD"}[number]
    nw = text_size(number, 8)[0]
    middle = top + max(36, height // 2)
    draw_text(img, (cx - 10, middle), number, 8, "#ffffff", "mm", shadow=shade(colour, 0.5))
    draw_text(img, (cx - 10 + nw // 2 + 6, middle - 14), suffix, 2, shade(colour, 0.45), "lm")


def _medal(img, cx, chest_y, place: int) -> None:
    """A medal on its ribbon, hanging on the chest."""
    disc, ribbon = MEDALS[place]
    d = ImageDraw.Draw(img)
    for side in (-1, 1):
        for i in range(5):
            x = cx + side * (12 - i * 2)
            d.rectangle([x - 2, chest_y - 14 + i * 3, x + 1, chest_y - 12 + i * 3], fill=rgb(ribbon))
    d.rectangle([cx - 8, chest_y - 2, cx + 8, chest_y + 14], fill=rgb(INK))
    d.rectangle([cx - 11, chest_y + 1, cx + 11, chest_y + 11], fill=rgb(INK))
    d.rectangle([cx - 6, chest_y + 1, cx + 6, chest_y + 11], fill=rgb(disc))
    d.rectangle([cx - 9, chest_y + 3, cx + 9, chest_y + 9], fill=rgb(disc))
    d.rectangle([cx - 4, chest_y + 3, cx - 2, chest_y + 6], fill=shade(disc, 1.5))


def figures(standings: list[dict], tied: bool = False) -> list[tuple]:
    """Each player as a see-through picture standing in their place: [(picture, (x, y)), ...] in place order.

    standings: [{"name", "look", "tag"}] from 1st to last (the tag: a name tag item id, its drawing spec, or None).
    tied: two players who tied (they stand on two equal steps).
    """
    out = []
    for entry, spot in zip(standings, spots(len(standings), tied)):
        on_floor = spot["height"] == 0
        scale = 4 if on_floor else FIGURE_SCALE
        cx, feet = spot["cx"], GROUND if on_floor else GROUND - spot["height"] - 6
        skin, pants, hair, shirt = entry["look"]
        body = sprites.sprite(skin, pants, hair, shirt, "down", 0, 0)
        hair_top = (body.getbbox() or (0, 0, 0, 0))[1]
        body = body.resize((body.width * scale, body.height * scale), Image.NEAREST)
        canvas = Image.new("RGBA", (220, body.height + 70), (0, 0, 0, 0))
        bx = (canvas.width - body.width) // 2
        canvas.paste(body, (bx, 70), body)
        if spot["medal"]:
            _medal(canvas, canvas.width // 2, 70 + (sprites.OY + 11) * scale, spot["medal"])
        tag = entry.get("tag")
        spec = tag if isinstance(tag, dict) else catalog.spec_for("name", tag)
        sprites.draw_name_tag(canvas, canvas.width // 2, 70 + hair_top * scale - 6, entry["name"], spec, 0)
        box = canvas.getbbox()
        piece = canvas.crop(box)
        x = cx - canvas.width // 2 + box[0]
        y = feet - (70 + body.height - scale) + box[1]
        out.append((piece, (x, y)))
    return out


def podium_picture(table, title: str, standings: list[dict], me: str, coins: int = 0, footer: str = "again",
                   with_figures: bool = True, line: str = "", tied: bool = False):
    """The podium over the dimmed table, for every game (UNO: up to four players; checkers and Connect Four: the
    winner and the loser, or two equal steps for a tie). Returns (picture, regions).

    line: a short sentence under the title (a win, loss or tie line), or "".

    footer "again": ENTER CONTINUE and A PLAY AGAIN (regions ("continue",) for the whole picture, ("again",)).
    footer "lobby": ENTER LOBBY (the whole picture is ("lobby",)). with_figures=False leaves the players out (they
    drop in with an animation first).
    """
    img = darken(table, 0.8)
    d = ImageDraw.Draw(img)
    count = len(standings)
    places = spots(count, tied)
    won = bool(standings) and standings[0]["name"] == me and not tied
    winner_x = places[0]["cx"] if places else 480
    # two flat spotlights from the ceiling onto the top step, with checkered edges
    for spread, strength in ((150, 0.10), (100, 0.16)):
        light = Image.new("L", img.size, 0)
        x = 480 if tied else winner_x
        ImageDraw.Draw(light).polygon([(x - 30, 0), (x + 30, 0), (x + spread, GROUND), (x - spread, GROUND)],
                                      fill=255)
        img.paste(Image.blend(img, Image.new("RGB", img.size, (255, 236, 170)), strength), (0, 0), light)
    d = ImageDraw.Draw(img)
    if won:  # behind the podium, so the steps stay clean
        confetti(img, (300, 0, 660, 120), count=60, seed=9)
    # the stage the podium stands on
    d.rectangle([0, GROUND + 1, SCREEN_W, SCREEN_H], fill=rgb("#1a1440"))
    d.rectangle([0, GROUND + 1, SCREEN_W, GROUND + 4], fill=rgb("#ff4fa3"))
    for x in range(0, SCREEN_W, 48):
        d.rectangle([x, GROUND + 5, x + 1, SCREEN_H], fill=rgb("#130f30"))
    for spot in sorted(places, key=lambda spot: spot["height"]):  # (the floor spot has no step)
        if spot["height"]:
            _block(img, spot)
    # the title on a ribbon, and the coins
    tw = text_size(title, 5)[0]
    x0, x1 = 480 - tw // 2 - 40, 480 + tw // 2 + 40
    d.polygon([(x0 - 30, 26), (x0, 26), (x0, 80), (x0 - 30, 80), (x0 - 16, 53)], fill=shade("#e2413c", 0.7))
    d.polygon([(x1 + 30, 26), (x1, 26), (x1, 80), (x1 + 30, 80), (x1 + 16, 53)], fill=shade("#e2413c", 0.7))
    d.rectangle([x0 - 3, 17, x1 + 3, 77], fill=rgb(INK))
    d.rectangle([x0, 20, x1, 74], fill=rgb("#e2413c"))
    d.rectangle([x0, 20, x1, 24], fill=rgb("#ff7a6e"))
    draw_text(img, (480, 48), title, 5, "#ffffff", "mm", shadow=INK)
    if coins:
        label = f"+{coins} COINS"
        lw = text_size(label, 3)[0] + 34
        coin(img, 480 - lw // 2, 94, 3)
        draw_text(img, (480 - lw // 2 + 34, 106), label, 3, "#ffe94a", "lm", shadow=INK)
    if line:  # on the stage, under the podium
        draw_text(img, (480, GROUND + 13), wrap(line.upper(), 64)[0], 2, "#d9d4ff", "mt", shadow=INK)
    if with_figures:
        for piece, (x, y) in figures(standings, tied):
            img.paste(piece, (int(x), int(y)), piece)
        if standings and not tied:
            cx, height = places[0]["cx"], places[0]["height"]
            for sx, sy, size in ((cx - 80, GROUND - height - 150, 3), (cx + 84, GROUND - height - 110, 2),
                                 (cx + 60, GROUND - height - 190, 2)):
                sparkle(img, sx, sy, size)
    if count == 4 and not tied:  # the last player: a small sign at their feet
        draw_text(img, (LAST_X, GROUND + 20), "4TH", 2, mix("#d9d4ff", INK, 0.2), "mm", shadow=INK)
    # what to do next
    regions = []
    if footer == "again":
        regions.append(((0, 0, SCREEN_W, SCREEN_H), ("continue",)))
        _hint(img, 330, 500, "ENTER", "CONTINUE")
        regions.append((_hint(img, 630, 500, "A", "PLAY AGAIN"), ("again",)))
    else:
        regions.append(((0, 0, SCREEN_W, SCREEN_H), ("lobby",)))
        _hint(img, 480, 500, "ENTER", "LOBBY")
    return img, regions


def _hint(img, cx, y, key, text) -> tuple:
    """What clicking here (or its key) does, on a dark plate, centred on cx: just the word, no key printed.
    Returns the plate (for clicks)."""
    d = ImageDraw.Draw(img)
    tw = text_size(text, 2)[0]
    x = cx - tw // 2
    box = (x - 16, y - 8, x + tw + 16, y + 32)
    d.rectangle(box, fill=rgb(INK))
    d.rectangle([box[0] + 3, box[1] + 3, box[2] - 3, box[3] - 3], fill=rgb("#2a2150"))
    draw_text(img, (x, y + 12), text, 2, "#f3ead2", "lm")
    return box
