"""The arcade room cut into layers, for the browser to stack (see arcade/room.py).

scenes.hub_scene() paints the whole room as one picture. To let the browser
draw walking smoothly, the same drawings are split into pieces that are made
once and sent once:

  background  the room and the three tables (with the neon glow baked in)
  top         signs, table labels and the walking hint, painted over everything
  hud         the coin counter
  tables      each table on its own, so a character walking behind it is hidden
  sheets      one picture per character look with every pose (4 directions,
              standing, two walking steps, blinking), for every animation tick
  tags        the name tag above a character, for every animation tick
  bubbles     the "PLAY E" style prompts shown next to the player

Everything is drawn with the same functions as before, so the room looks the same.
"""

from __future__ import annotations

import json
from functools import lru_cache

from PIL import Image, ImageChops

from arcade import hubmap
from arcade.art import effects, lighting, sprites
from arcade.art.pixel import (
    CHAR_H,
    draw_text,
    lock,
    panel,
    text_size,
    upscale,
)
from arcade.art.scenes import (
    INK,
    TABLE_ORIGIN,
    _hub_background,
    _lay,
    blink,
    draw_coin_counter,
    table_sprite,
)
from arcade.config import GLOW, SCALE, SCREEN_H, SCREEN_W

DIRECTIONS = ["down", "up", "left", "right"]
POSES = 4  # standing, step 1, step 2, blinking
CELL_W, CELL_H = 24, 36  # one pose, on the small canvas
FEET = (12, 30)  # where the feet are inside a cell
SPRITE_TICKS = 6  # animated cosmetics repeat every 6 ticks (the rainbow has 6 colours)
TAG_TICKS = 5  # the flames of a name tag repeat every 5 ticks
TABLES = ("uno", "checkers", "connect4")


def _transparent(size) -> Image.Image:
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _crop(img: Image.Image) -> tuple[Image.Image, tuple[int, int]]:
    """Cut away the empty border. Returns the piece and where its top-left corner was."""
    box = img.getbbox() or (0, 0, 1, 1)
    return img.crop(box), (box[0], box[1])


# ---------------------------------------------------------------- the room itself

def _room_base() -> Image.Image:
    """The room and its tables on the small canvas (no characters)."""
    img = _hub_background().copy()
    for key in TABLES:
        cx, cy = hubmap.SPOTS[key]["center"]
        _lay(img, lighting.soft_oval(50, 12, 0.55), (cx - 28, cy + 2))
        img.paste(table_sprite(key), (cx - TABLE_ORIGIN[0], cy - TABLE_ORIGIN[1]), table_sprite(key))
    return img


def _label_colour(highlight: bool) -> str:
    return "#ffe94a" if highlight else "#d9d4ff"


def _draw_label(img, key: str, highlight: bool) -> None:
    cx, cy = hubmap.SPOTS[key]["center"]
    draw_text(img, (cx * SCALE, (cy - 15) * SCALE), hubmap.SPOTS[key]["label"], 2, _label_colour(highlight), "mb",
              shadow=INK)


@lru_cache(maxsize=2)
def top_layer(champ_locked: bool) -> Image.Image:
    """Signs, table labels and the walking hint (drawn over the characters, as in hub_scene)."""
    top = _transparent((SCREEN_W, SCREEN_H))
    panel(top, (224 * SCALE - 52, 4, 224 * SCALE + 52, 34), "#16122b", "#ffe94a", shadow=False)
    draw_text(top, (224 * SCALE, 19), "STORE", 2, "#ffe94a", "mm")
    draw_text(top, (43 * SCALE, 33 * SCALE), "#1", 2, "#ffe94a", "mm")
    if champ_locked:
        lock(top, 43 * SCALE - 10, 46 * SCALE, 3)
    for key in TABLES:
        _draw_label(top, key, False)
    return top


@lru_cache(maxsize=2)
def background(champ_locked: bool) -> Image.Image:
    """The room, blown up, with the soft neon glow of the room and its signs baked in."""
    big = upscale(_room_base()).convert("RGB")
    if not GLOW:
        return big
    with_signs = big.copy()
    with_signs.paste(top_layer(champ_locked), (0, 0), top_layer(champ_locked))
    halo = ImageChops.subtract(effects.neon_glow(with_signs), with_signs)  # only the light around the neon
    return ImageChops.add(big, halo)


@lru_cache(maxsize=64)
def hud_layer(coins: int) -> tuple[Image.Image, tuple[int, int]]:
    """The coin counter, cut to its size, and where it goes."""
    hud = _transparent((SCREEN_W, 60))
    draw_coin_counter(hud, coins)
    return _crop(hud)


@lru_cache(maxsize=1)
def table_layers() -> dict:
    """Each table alone (normal, and lit up when the player is close), plus its lit-up label.

    at: where the table goes on the screen. sort: the y the table counts as for "who
    is in front" (the same as in hub_scene).
    """
    layers = {}
    for key in TABLES:
        cx, cy = hubmap.SPOTS[key]["center"]
        label = _transparent((SCREEN_W, SCREEN_H))
        _draw_label(label, key, True)
        label, label_at = _crop(label)
        layers[key] = {"normal": upscale(table_sprite(key)), "lit": upscale(table_sprite(key, True)),
                       "at": ((cx - TABLE_ORIGIN[0]) * SCALE, (cy - TABLE_ORIGIN[1]) * SCALE),
                       "label": label, "label_at": label_at, "sort": cy + 4}
    return layers


# ---------------------------------------------------------------- characters

def _pose(look, direction: str, pose: int, t: int) -> Image.Image:
    cell = _transparent((CELL_W, CELL_H))
    x, y = FEET
    _lay(cell, lighting.soft_oval(13, 5, 0.7), (x - 9, y - 5))  # soft shadow at the feet
    step = pose if pose in (1, 2) else 0
    sprites.draw_character(cell, x, y, look, direction, step, t)
    if pose == 3:
        blink(cell, x, y, look[0], direction)
    return cell


@lru_cache(maxsize=64)
def sheet(look: tuple) -> tuple[Image.Image, int]:
    """Every pose of one look on one picture, blown up.

    Columns: direction (down, up, left, right) x pose (standing, step 1, step 2, blink).
    Rows: animation ticks. A look that does not change with time has a single row.
    Returns (picture, number of rows).
    """
    rows = []
    for t in range(SPRITE_TICKS):
        row = _transparent((CELL_W * len(DIRECTIONS) * POSES, CELL_H))
        for d, direction in enumerate(DIRECTIONS):
            for pose in range(POSES):
                row.paste(_pose(look, direction, pose, t), ((d * POSES + pose) * CELL_W, 0))
        if rows and row.tobytes() == rows[0].tobytes():
            break  # the same as tick 0: this look does not move by itself
        rows.append(row)
    picture = _transparent((rows[0].width, CELL_H * len(rows)))
    for i, row in enumerate(rows):
        picture.paste(row, (0, i * CELL_H))
    return upscale(picture), len(rows)


@lru_cache(maxsize=64)
def tag_frames(name: str, spec_json: str | None) -> tuple[list[Image.Image], tuple[int, int]]:
    """The name tag for every animation tick, and the point of the picture that sits on the anchor.

    The anchor is where hub_scene puts the tag: (x * 3, (y - 23) * 3 - 4) for feet at (x, y).
    """
    spec = json.loads(spec_json) if spec_json else None  # the tag's drawing recipe, as JSON so it can be cached
    frames, boxes = [], []
    for t in range(TAG_TICKS):
        canvas = _transparent((480, 160))
        sprites.draw_name_tag(canvas, 240, 130, name, spec, t)
        frames.append(canvas)
        boxes.append(canvas.getbbox() or (0, 0, 1, 1))
        if t and frames[-1].tobytes() == frames[0].tobytes():
            frames.pop()
            boxes.pop()
            break
    left, top = min(b[0] for b in boxes), min(b[1] for b in boxes)
    right, bottom = max(b[2] for b in boxes), max(b[3] for b in boxes)
    return [f.crop((left, top, right, bottom)) for f in frames], (240 - left, 130 - top)


# ---------------------------------------------------------------- prompt bubbles

@lru_cache(maxsize=32)
def bubble(text: str, key: str | None = None, locked: bool = False, small: str | None = None):
    """One prompt bubble, drawn as in hub_scene. Returns (picture, (width, height) of the box)."""
    scale = 2
    tw, _ = text_size(text, scale)
    key_w = 0  # (no key printed on the bubble)
    lock_w = 30 if locked else 0
    w = tw + key_w + lock_w + 24
    h = 34 + (CHAR_H * 1 + 6 if small else 0)
    if small:
        w = max(w, text_size(small, 1)[0] + 24)
    pad = 12
    img = _transparent((w + pad * 2, h + pad * 2))
    x0, y = pad, pad
    panel(img, (x0, y, x0 + w, y + h), "#ffffff" if not locked else "#d9d4e6", INK)
    cursor = x0 + 12
    if locked:
        lock(img, cursor, y + 5, 2, "#6b6880")
        cursor += lock_w - 8
    draw_text(img, (cursor, y + 17), text, scale, INK, "lm")
    if small:
        draw_text(img, (x0 + 12, y + 31), small, 1, "#4a4660", "lt")
    return img, (w, h), pad


@lru_cache(maxsize=512)
def speech(text: str, mine: bool = False):
    """A speech bubble with a little tail at the bottom (what the player or a bot says when they talk in the room).
    The player's bubbles are light blue, the bots' cream. Returns the picture (its tail tip is at the bottom middle)."""
    from arcade.art.pixel import wrap

    lines = wrap(text.upper(), 22)
    width = max(text_size(line, 2)[0] for line in lines) + 24
    height = 20 * len(lines) + 16
    img = _transparent((width + 6, height + 16))
    fill = "#bfe6ff" if mine else "#fff6da"
    panel(img, (0, 0, width - 1, height - 1), fill, INK, bw=3, shadow=False)
    from PIL import ImageDraw

    d = ImageDraw.Draw(img)
    mid = width // 2
    for row, half in enumerate((7, 5, 3, 1)):  # the tail, in pixel steps
        y = height - 3 + row * 3
        d.rectangle([mid - half - 3, y, mid + half + 2, y + 2], fill=INK)
        if half > 1:
            d.rectangle([mid - half, y, mid + half - 1, y + 2], fill=fill)
    for i, line in enumerate(lines):
        draw_text(img, (mid, 10 + i * 20), line, 2, INK, "mt")
    return img


# ---------------------------------------------------------------- what moves on the walls

@lru_cache(maxsize=1)
def alive_patches() -> tuple:
    """The moving parts of the room (arcade/art/alive.py): the games on the machines' screens and their marquee lights,
    the trophy on the championship cabinet, the claw of the prize machine, the glowing sides of the machines along
    the side walls, the ARCADE sign and the bunting. Positions on the small canvas, matching scenes._hub_background."""
    from arcade.art import alive
    from arcade.art.scenes import _hub_background
    from arcade.art.table_room import _sign_box

    top = hubmap.FLOOR_TOP
    out = [alive.patch(0, 2, alive.bunting_frames(320), 3)]
    for game, (cx, screen) in enumerate(((88, "#58c4d8"), (120, "#f0a060"), (152, "#8fd860"))):
        out += alive.machine_patches(cx, top + 2, screen, game)
    out += alive.machine_patches(43, top + 4, "#2a1a4a", 4, w=28, h=46)
    out.append(alive.patch(292 - 11, top + 3 - 46 + 6, alive.claw_frames(), 3))
    for x, y, screen in ((11, 88, "#ff7ac8"), (11, 130, "#8fd860"), (306, 92, "#58c4d8"), (306, 134, "#ffe94a")):
        out.append(alive.patch(x, y, alive.side_glow_frames(screen), 3))
    x, y, w, h = _sign_box(120, 9, "ARCADE")
    out.append(alive.patch(x, y, alive.neon_frames(_hub_background().crop((x, y, x + w, y + h))), 3))
    return tuple(out)
