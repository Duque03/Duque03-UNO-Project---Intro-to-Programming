"""The room behind a game table: the same arcade as the hub, seen from a chair at that table.

Each table looks at its own part of the hub's back wall (UNO: the championship cabinet and the gumball machine;
checkers: the row of machines under the ARCADE sign; Connect Four: the store and the prize machine), with the same
bricks, bunting, neon strip, posters and confetti floor as the room. The moving parts (the games on the screens, the
marquee lights, the claw, the neon sign, the bunting) are patches the browser loops (arcade/art/alive.py), drawn on a
see-through canvas over the table picture only where nothing stands in front of them (see visible_patches).
"""

from __future__ import annotations

import base64
import io
import random
from functools import lru_cache

from PIL import Image, ImageChops, ImageDraw

from arcade import bots
from arcade.art import alive, sprites
from arcade.art.pixel import mix, new_base, new_layer, outlined, rect, rgb, stamp, text_size
from arcade.art.scenes import (FLOOR_A, FLOOR_B, GROUT, MORTAR, NEON, TABLE_COLOURS, WALL, _bunting, _claw_machine,
                               _gumball, _light_beams, _machine, _neon_sign, _plant, _poster, _side_machine,
                               _trophy)
from arcade.config import BASE_H, BASE_W

WALL_BOTTOM = 86  # where the wall meets the floor (small canvas)
BASE = 84  # where the machines stand

# What hangs on / stands against the wall behind each table. ("machine", cx, body, screen, game) ...
LAYOUT = {
    "uno": [
        ("poster", 4, 18, 13, 17, "#3aa655", "heart"), ("machine", 40, "#5a3fa8", "#ff7ac8", 3),
        ("champ", 111), ("machine", 160, "#8a3f86", "#f0a060", 1), ("gumball", 196),
        ("sign", 214, 24, "UNO", "#ff4fa3"), ("poster", 222, 46, 13, 17, "#d93a9c", "star"),
        ("machine", 280, "#3f5fae", "#58c4d8", 0), ("plant", 312),
    ],
    "checkers": [
        ("poster", 6, 16, 13, 17, "#2f6fe0", "ship"), ("sign", 52, 20, "ARCADE", "#ff4fa3"),
        ("machine", 40, "#3f5fae", "#8fd860", 3), ("machine", 111, "#5a3fa8", "#58c4d8", 0),
        ("machine", 160, "#8a3f86", "#f0a060", 1), ("machine", 209, "#3f5fae", "#8fd860", 2),
        ("store", 240, 330),
    ],
    "connect4": [
        ("poster", 8, 16, 13, 17, "#3aa655", "heart"), ("machine", 44, "#8a3f86", "#f0a060", 2),
        ("claw", 108), ("machine", 160, "#5a3fa8", "#58c4d8", 0), ("store", 190, 306),
        ("plant", 312),
    ],
}


def _store(img, d, props, x0, x1) -> None:
    """The store window as in the hub: striped awning, shelves of goods, the shopkeeper behind the counter."""
    top = 22
    rect(d, x0, top + 4, x1 - x0, WALL_BOTTOM - top - 8, (16, 12, 38))
    shelf_rng = random.Random(3)
    keeper = (x0 + x1) // 2
    for shelf_y in (top + 12, top + 24):
        rect(d, x0 + 3, shelf_y + 6, x1 - x0 - 6, 1, (110, 84, 56))
        for sx in range(x0 + 5, x1 - 6, 7):
            if abs(sx - keeper) < 12:
                continue
            rect(d, sx, shelf_y + 1, 4, 5, rgb(shelf_rng.choice(NEON)))
    sprites.draw_character(props, keeper, top + 44, bots.look(bots.SHOPKEEPER), "down")
    counter = top + 34
    rect(d, x0 - 4, counter, x1 - x0 + 8, 3, (214, 150, 86))
    rect(d, x0 - 2, counter + 3, x1 - x0 + 4, BASE - counter - 3, (138, 90, 51))
    for px in range(x0 + 6, x1, 14):
        rect(d, px, counter + 5, 1, BASE - counter - 7, (110, 70, 40))
    for i, ax in enumerate(range(x0 - 4, x1 + 4, 8)):
        rect(d, ax, top, 8, 7, (232, 68, 58) if i % 2 == 0 else (243, 234, 210))
        rect(d, ax + 1, top + 7, 6, 1, (170, 44, 40) if i % 2 == 0 else (200, 190, 168))
    rect(d, x0 - 4, top, 2, BASE - top, (122, 90, 58))
    rect(d, x1 + 2, top, 2, BASE - top, (122, 90, 58))


@lru_cache(maxsize=4)
def backdrop(kind: str) -> Image.Image:
    """The wall and the floor behind a table (small canvas, no table, no people). Kept: do not draw on it."""
    img = new_base("#1c1642")
    d = ImageDraw.Draw(img)
    # bricks, the neon strip and the skirting board, as in the room
    rect(d, 0, 0, BASE_W, WALL_BOTTOM, WALL)
    for i, y in enumerate(range(0, WALL_BOTTOM, 6)):
        rect(d, 0, y, BASE_W, 1, MORTAR)
        for x in range(-6 if i % 2 else 0, BASE_W, 12):
            rect(d, x, y, 1, 6, MORTAR)
    rect(d, 0, WALL_BOTTOM - 9, BASE_W, 2, rgb("#ff4fa3"))
    rect(d, 0, WALL_BOTTOM - 6, BASE_W, 1, rgb("#3ad6ff"))
    rect(d, 0, WALL_BOTTOM - 3, BASE_W, 3, (14, 10, 32))
    # the floor: the same tiles and confetti, and a rug in the table's colour
    for ty in range(WALL_BOTTOM, BASE_H, 15):
        for tx in range(-5, BASE_W, 15):
            rect(d, tx, ty, 15, 15, FLOOR_A if ((tx + 5) // 15 + (ty - WALL_BOTTOM) // 15) % 2 == 0 else FLOOR_B)
            rect(d, tx, ty, 15, 1, GROUT)
            rect(d, tx, ty, 1, 15, GROUT)
    rng = random.Random(11)
    for _ in range(90):
        x, y = rng.randrange(4, BASE_W - 4), rng.randrange(WALL_BOTTOM + 3, BASE_H - 2)
        rect(d, x, y, 2 if rng.random() < 0.5 else 1, 1, mix(rng.choice(NEON), FLOOR_B, 0.4))
    colour = TABLE_COLOURS[kind]
    d.ellipse([-20, 96, BASE_W + 20, 196], fill=mix(colour, FLOOR_B, 0.55))
    d.ellipse([-10, 100, BASE_W + 10, 192], fill=mix(colour, FLOOR_B, 0.74))

    wall = new_layer()
    wd = ImageDraw.Draw(wall)
    _bunting(wd)
    props = new_layer()
    pd = ImageDraw.Draw(props)
    signs = []
    for item in LAYOUT[kind]:
        what = item[0]
        if what == "poster":
            _poster(wd, *item[1:])
        elif what == "machine":
            _, cx, body, screen, game = item
            _machine(pd, cx, BASE, rgb(body), rgb(screen), game=game)
        elif what == "champ":
            _machine(pd, item[1], BASE + 2, rgb("#d9a520"), rgb("#2a1a4a"), w=28, h=46, glow=True)
            _trophy(pd, item[1], BASE + 2 - 46)
        elif what == "gumball":
            _gumball(pd, item[1], BASE + 1)
        elif what == "claw":
            _claw_machine(pd, item[1], BASE + 1)
        elif what == "plant":
            _plant(pd, item[1], BASE + 1)
        elif what == "side":
            _side_machine(pd, *item[1:])
        elif what == "store":
            _store(img, pd, props, item[1], item[2])
        elif what == "sign":
            signs.append(item[1:])
    stamp(img, outlined(wall))
    stamp(img, outlined(props))
    for cx, y, text, colour in signs:
        _neon_sign(img, cx, y, text, colour)
    _light_beams(img, ((111, 84, 138, WALL_BOTTOM + 24), (209, 182, 236, WALL_BOTTOM + 24)))  # lamps, as in the room
    return img


def _sign_box(cx, y, text) -> tuple:
    """Where scenes._neon_sign draws its board: (x, y, w, h)."""
    tw, th = text_size(text, 1)
    return (cx - tw // 2 - 4, y - 3, tw + 8, th + 6)


@lru_cache(maxsize=4)
def patches(kind: str) -> tuple:
    """The moving parts of the wall behind a table, as alive.patch dictionaries (small canvas)."""
    out = [alive.patch(0, 2, alive.bunting_frames(BASE_W), 3)]
    for item in LAYOUT[kind]:
        what = item[0]
        if what == "machine":
            _, cx, body, screen, game = item
            out += alive.machine_patches(cx, BASE, screen, game)
        elif what == "champ":
            out += alive.machine_patches(item[1], BASE + 2, "#2a1a4a", 4, w=28, h=46)
        elif what == "claw":
            out.append(alive.patch(item[1] - 11, BASE + 1 - 46 + 6, alive.claw_frames(), 3))
        elif what == "sign":
            cx, y, text, _ = item[1:]
            x, top, w, h = _sign_box(cx, y, text)
            out.append(alive.patch(x, top, alive.neon_frames(backdrop(kind).crop((x, top, x + w, top + h))), 3))
    return tuple(out)


# ---------------------------------------------------------------- on the browser's side

def _url(img) -> str:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


@lru_cache(maxsize=4)
def _frame_urls(kind: str) -> tuple:
    """The frames of every patch as pictures for the browser, darkened like the picture's edges where they are."""
    from arcade.art.scenes import EDGE_DARK, frame_mask

    edges, out = frame_mask(), []
    for p in patches(kind):
        urls = []
        for frame in p["frames"]:
            w, h = frame.size
            where = edges.crop((p["x"], p["y"], p["x"] + w, p["y"] + h))
            if where.getbbox():
                plain = frame.convert("RGB")
                dark = Image.blend(plain, Image.new("RGB", frame.size, EDGE_DARK[0]), EDGE_DARK[1])
                plain.paste(dark, (0, 0), where)
                if frame.mode == "RGBA":
                    plain = plain.convert("RGBA")
                    plain.putalpha(frame.getchannel("A"))
                frame = plain
            urls.append(_url(frame))
        out.append(tuple(urls))
    return tuple(out)


def visible_patches(picture, empty, kind: str) -> list[dict]:
    """The patches of this table that can be seen on this picture, ready for the browser: their frames and a mask of
    the pixels where nothing stands in front of the wall. A patch hidden everywhere is left out; a fully visible one
    has no mask (None).

    picture: the finished table picture (960 x 540); empty: the room behind it with nobody in it
    (scenes.empty_table_room). Wherever the two differ, something is in front: a player, the table, a card."""
    out = []
    for p, frames in zip(patches(kind), _frame_urls(kind)):
        w, h = p["frames"][0].size
        box = (p["x"] * 3, p["y"] * 3, (p["x"] + w) * 3, (p["y"] + h) * 3)
        diff = ImageChops.difference(picture.crop(box).convert("RGB"), empty.crop(box).convert("RGB"))
        mask = diff.convert("L").point(lambda v: 255 if v == 0 else 0)
        if mask.getbbox() is None:
            continue
        layer = None
        if mask.getextrema() != (255, 255):
            layer = Image.new("RGBA", mask.size, (255, 255, 255, 0))
            layer.putalpha(mask)
            layer = _url(layer)
        out.append({"x": p["x"], "y": p["y"], "w": w, "h": h, "fps": p["fps"], "frames": list(frames), "mask": layer})
    return out
