"""The store and the wardrobe as one picture each (no buttons outside the game picture), all in pixel art.

Top: a dark bar with the title, the coins, the three tabs (folder tabs) and BACK. Left: a pegboard wall with wooden
shelves, the items of the tab on them as tiles, by rarity (each tile shows only the item: the hair on a plain head
shape, the shirt on a hanger, the name tag on strings). Right: a little fitting room with curtains, the player wearing
the item on show from three sides, its name and price, and on a wooden counter what can be done (BUY, WEAR, EQUIP,
UNEQUIP).
"""

from __future__ import annotations

from functools import lru_cache

from PIL import Image, ImageChops, ImageDraw

from arcade import catalog
from arcade.art import sprites
from arcade.art.pixel import coin, draw_text, mix, rgb, shade, text_size, wrap
from arcade.config import SCREEN_H, SCREEN_W, SLOT_LABELS, SLOTS

TILE_W, TILE_H, GAP = 104, 112, 9
WIDE_W = 128  # the rare and legendary tiles, on the bottom shelf, are wider
GRID_X = 20
ROW_Y = (92, 224)  # the two rows of common items; rare and legendary share the third row
RARE_SIGN_Y, RARE_Y = 360, 388
RIGHT_X = 588  # where the fitting room starts
INK = "#0d0a1f"
RARITY_COLOURS = {"common": "#2f8a4e", "rare": "#6b46c9", "legendary": "#f0a020"}
RARITY_INK = {"common": "#ffffff", "rare": "#ffffff", "legendary": "#16122b"}
TILE_TINT = {"common": "#1d2a3c", "rare": "#261d50", "legendary": "#3a2416"}
WALL, WALL_HOLE = "#221a4a", "#2e2560"
WOOD_TOP, WOOD, WOOD_DARK = "#9a5a3a", "#6b3d2a", "#3a1f1a"
PINK, CURTAIN, CURTAIN_FOLD = "#ff4fa3", "#b8306f", "#8a2052"
BUTTON = {True: ("#ffe94a", "#fff6c0", "#c9a227", "#16122b"), False: ("#3e3670", "#4c4486", "#2c2652", "#8d86b8")}


def tile_width(item: dict) -> int:
    """How wide the tile of this item is (the rare and legendary ones are wider)."""
    return TILE_W if item["rarity"] == "common" else WIDE_W


@lru_cache(maxsize=512)
def tile_picture(item_id: str, look: tuple, name: str) -> Image.Image:
    """Only the item: the hair on a plain head shape, the shirt on a hanger, or the name tag with the player's name.
    (look is not used for hair and shirts any more: the item is shown on its own. Kept for the next runs: do not
    draw on the picture it returns.)"""
    item = catalog.get(item_id)
    if item["slot"] == "name":  # big if it fits in the tile, else small (made smaller still if it must)
        room = tile_width(item) - 12
        for scale in (2, 1):
            img = Image.new("RGBA", (440, 120), (0, 0, 0, 0))
            sprites.draw_name_tag(img, 220, 90, name, item["spec"], scale=scale)
            img = img.crop(img.getbbox())
            if img.width <= room:
                return img
        return img.resize((room, round(img.height * room / img.width)), Image.NEAREST)
    if item["slot"] == "hair":
        picture = sprites.hair_item(item["id"], head=shade(TILE_TINT[item["rarity"]], 1.16))
    else:
        picture = sprites.shirt_item(item["id"])
    unit = 5 if picture.height * 5 <= 80 else 4
    return picture.resize((picture.width * unit, picture.height * unit), Image.NEAREST)


# ---------------------------------------------------------------- little pixel drawings

def _box(d, box, fill, edge=INK, width=3) -> None:
    """A rectangle with a dark edge and cut corners (pixel art)."""
    x0, y0, x1, y1 = box
    d.rectangle([x0 + width, y0, x1 - width, y1], fill=rgb(edge))
    d.rectangle([x0, y0 + width, x1, y1 - width], fill=rgb(edge))
    d.rectangle([x0 + width, y0 + width, x1 - width, y1 - width], fill=rgb(fill))


def _lock(d, x, y, colour) -> None:
    """A small padlock (12 x 14)."""
    c = rgb(colour)
    d.rectangle([x + 3, y, x + 8, y + 1], fill=c)
    d.rectangle([x + 2, y + 1, x + 3, y + 6], fill=c)
    d.rectangle([x + 8, y + 1, x + 9, y + 6], fill=c)
    d.rectangle([x, y + 6, x + 11, y + 13], fill=c)
    d.rectangle([x + 5, y + 8, x + 6, y + 11], fill=rgb(INK))


def _check(d, x, y, colour) -> None:
    """A tick (12 x 10)."""
    for i, (cx, cy) in enumerate(((0, 4), (2, 6), (4, 8), (6, 6), (8, 4), (10, 2), (12, 0))):
        d.rectangle([x + cx, y + cy, x + cx + 2, y + cy + 2], fill=rgb(colour))


def _gem(d, x, y, colour) -> None:
    """A small diamond-shaped gem in a tile's corner (11 x 11)."""
    light, dark = shade(colour, 1.45), shade(colour, 0.6)
    for row, (start, length) in enumerate(((4, 3), (2, 7), (0, 11), (2, 7), (4, 3))):
        d.rectangle([x + start, y + row * 2, x + start + length - 1, y + row * 2 + 1], fill=rgb(INK))
    for row, (start, length) in enumerate(((5, 1), (3, 5), (1, 9), (3, 5))):
        d.rectangle([x + start, y + row * 2 + 1, x + start + length - 1, y + row * 2 + 2],
                    fill=light if row < 2 else rgb(colour) if row == 2 else dark)


def _spark(d, cx, cy, colour="#fff6c0") -> None:
    """A tiny four-pointed sparkle."""
    c = rgb(colour)
    d.rectangle([cx - 1, cy - 4, cx, cy + 3], fill=c)
    d.rectangle([cx - 4, cy - 1, cx + 3, cy], fill=c)


def _shelf(d, x0, x1, y, brackets=False) -> None:
    """A wooden shelf the tiles stand on (the bottom one with brackets under it)."""
    d.rectangle([x0, y, x1, y + 2], fill=rgb(WOOD_TOP))
    d.rectangle([x0, y + 3, x1, y + 9], fill=rgb(WOOD))
    d.rectangle([x0, y + 10, x1, y + 11], fill=rgb(WOOD_DARK))
    for bx in range(x0 + 30, x1 - 20, 136) if brackets else ():
        for step in range(4):
            d.rectangle([bx + step * 2, y + 12 + step * 3, bx + 12 - step * 2, y + 14 + step * 3], fill=rgb(WOOD_DARK))


def _sign(img, x, y, text, rarity) -> None:
    """A small plate with the rarity on it, hanging from two strings."""
    d = ImageDraw.Draw(img)
    tw, th = text_size(text, 2)
    w = tw + 20
    for sx in (x + 6, x + w - 8):
        d.rectangle([sx, y - 8, sx + 1, y], fill=rgb("#8d86b8"))
    _box(d, (x, y, x + w, y + th + 10), RARITY_COLOURS[rarity], width=2)
    d.rectangle([x + 2, y + 2, x + w - 2, y + 3], fill=shade(RARITY_COLOURS[rarity], 1.3))
    draw_text(img, (x + w // 2, y + (th + 10) // 2 + 1), text, 2, RARITY_INK[rarity], "mm")


def _button(img, box, label, enabled) -> tuple:
    """A chunky pixel button: yellow when it can be clicked, dim purple when not."""
    d = ImageDraw.Draw(img)
    face, light, low, ink = BUTTON[enabled]
    x0, y0, x1, y1 = box
    d.rectangle([x0 + 4, y0 + 4, x1 + 4, y1 + 4], fill=rgb("#05030d"))  # its shadow on the counter
    _box(d, box, face)
    d.rectangle([x0 + 3, y0 + 3, x1 - 3, y0 + 5], fill=rgb(light))
    d.rectangle([x0 + 3, y1 - 7, x1 - 3, y1 - 3], fill=rgb(low))
    draw_text(img, ((x0 + x1) // 2, (y0 + y1) // 2 - 1), label, 2, ink, "mm")
    return tuple(int(v) for v in box)


@lru_cache(maxsize=1)
def _wall() -> Image.Image:
    """The pegboard wall behind the shelves (kept: do not draw on it)."""
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), rgb(WALL))
    d = ImageDraw.Draw(img)
    for y in range(72, SCREEN_H, 18):
        for x in range(12 + (9 if (y // 18) % 2 else 0), RIGHT_X - 8, 18):
            d.rectangle([x, y, x + 2, y + 2], fill=rgb(WALL_HOLE))
    return img


def _dithered_oval(img, box, colour) -> None:
    """A flat oval with a checkered edge (pixel art light, no blur)."""
    x0, y0, x1, y1 = box
    solid, edge = Image.new("L", img.size, 0), Image.new("L", img.size, 0)
    ImageDraw.Draw(solid).ellipse(box, fill=255)
    ImageDraw.Draw(edge).ellipse([x0 - 9, y0 - 6, x1 + 9, y1 + 6], fill=255)
    checks = Image.new("L", (6, 6), 0)
    ImageDraw.Draw(checks).rectangle([0, 0, 2, 2], fill=255)
    ImageDraw.Draw(checks).rectangle([3, 3, 5, 5], fill=255)
    pattern = Image.new("L", img.size, 0)
    for y in range(0, img.height, 6):
        for x in range(0, img.width, 6):
            pattern.paste(checks, (x, y))
    edge = ImageChops.multiply(edge, pattern)
    edge.paste(255, (0, 0), solid)
    img.paste(rgb(colour), (0, 0), edge)


# ---------------------------------------------------------------- the parts of the picture

def _top_bar(img, view, regions) -> None:
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, SCREEN_W, 55], fill=rgb("#16122b"))
    d.rectangle([0, 56, SCREEN_W, 58], fill=rgb(PINK))
    left = 96  # the music and full-screen buttons sit at the top left of the window
    draw_text(img, (left, 14), view["title"], 4, "#ffe94a", "lt", shadow="#3b3560")
    x = left + text_size(view["title"], 4)[0] + 16
    if view.get("coins") is not None:  # the coins, in a little box
        label = str(view["coins"])
        w = 46 + text_size(label, 3)[0]
        _box(d, (x, 11, x + w, 47), INK, "#ffe94a")
        coin(img, x + 9, 17, 3)
        draw_text(img, (x + 40, 30), label, 3, "#ffe94a", "lm")
    for i, slot in enumerate(SLOTS):  # folder tabs, the open one joins the pink line
        x0, x1 = 364 + i * 124, 480 + i * 124
        on = slot == view["slot"]
        face = "#ffe94a" if on else "#3e3670"
        d.rectangle([x0 + 6, 14, x1 - 6, 58], fill=rgb(INK))
        d.rectangle([x0, 20, x1, 58], fill=rgb(INK))
        d.rectangle([x0 + 9, 17, x1 - 9, 58 if on else 53], fill=rgb(face))
        d.rectangle([x0 + 3, 23, x1 - 3, 58 if on else 53], fill=rgb(face))
        if on:
            d.rectangle([x0 + 9, 17, x1 - 9, 19], fill=rgb("#fff6c0"))
        draw_text(img, ((x0 + x1) // 2, 37), SLOT_LABELS[slot].upper(), 2, "#16122b" if on else "#d9d4ff", "mm")
        regions.append(((x0, 14, x1, 58), ("tab", slot)))
    box = (832, 11, 944, 47)  # BACK, pink
    _box(d, box, PINK)
    d.rectangle([box[0] + 3, box[1] + 3, box[2] - 3, box[1] + 5], fill=rgb("#ff9fd0"))
    d.rectangle([box[0] + 3, box[3] - 7, box[2] - 3, box[3] - 3], fill=rgb("#c23880"))
    draw_text(img, ((box[0] + box[2]) // 2, 28), "< BACK", 2, "#16122b", "mm")
    regions.append((box, ("back",)))


def _tile(img, x, y, tile: dict, chosen: bool) -> tuple:
    """One tile on the shelf: the rarity strip and gem, the item, and along the bottom its price (pink with a lock
    when it costs too much), OWNED or WEARING."""
    d = ImageDraw.Draw(img)
    rarity = tile["item"]["rarity"]
    edge = RARITY_COLOURS[rarity]
    tile_w = tile_width(tile["item"])
    if chosen:  # the item on show on the right: a white frame round it
        d.rectangle([x - 5, y - 5, x + tile_w + 4, y + TILE_H + 4], fill=rgb("#ffffff"))
    _box(d, (x, y, x + tile_w - 1, y + TILE_H - 1), TILE_TINT[rarity], width=3)
    d.rectangle([x + 3, y + 3, x + tile_w - 4, y + 9], fill=rgb(edge))
    d.rectangle([x + 3, y + 10, x + tile_w - 4, y + 11], fill=shade(edge, 0.6))
    _gem(d, x + tile_w - 18, y + 14, edge)
    if rarity == "legendary":
        for sx, sy in ((x + 14, y + 22), (x + tile_w - 22, y + 70), (x + 20, y + 76)):
            _spark(d, sx, sy)
    picture = tile["picture"]
    img.paste(picture, (x + (tile_w - picture.width) // 2, y + 14 + (70 - picture.height) // 2), picture)
    kind, by = tile["kind"], y + TILE_H - 27
    d.rectangle([x + 3, by, x + tile_w - 4, y + TILE_H - 4], fill=rgb(INK))
    middle = x + tile_w // 2
    if kind in ("price", "poor"):
        colour = "#ffe94a" if kind == "price" else PINK
        width = text_size(tile["badge"], 2)[0] + 22
        if kind == "price":
            coin(img, middle - width // 2, by + 6, 2)
        else:
            _lock(d, middle - width // 2 + 2, by + 5, PINK)
        draw_text(img, (middle - width // 2 + 22, by + 12), tile["badge"], 2, colour, "lm")
    else:
        colour = "#3ad6ff" if kind == "owned" else "#3ad678"
        width = text_size(tile["badge"], 2)[0] + 20
        _check(d, middle - width // 2, by + 7, colour)
        draw_text(img, (middle - width // 2 + 20, by + 12), tile["badge"], 2, colour, "lm")
    return x, y, x + tile_w, y + TILE_H


def _shelves(img, view, regions) -> None:
    d = ImageDraw.Draw(img)
    rows = [(rarity, tiles) for rarity, tiles in view["sections"] if tiles]
    if not rows:
        draw_text(img, ((GRID_X + RIGHT_X) // 2, 290), view.get("empty", "").upper(), 2, "#d9d4ff", "mm")
    chosen = view.get("chosen")
    for rarity, tiles in rows:
        if rarity != "common":
            continue
        _sign(img, GRID_X, ROW_Y[0] - 22, "COMMON", "common")
        for k, tile in enumerate(tiles[:10]):
            tx, ty = GRID_X + (k % 5) * (TILE_W + GAP), ROW_Y[k // 5]
            regions.append((_tile(img, tx, ty, tile, tile["item"]["id"] == chosen), ("item", tile["item"]["id"])))
    for y in ROW_Y:
        _shelf(d, 12, RIGHT_X - 16, y + TILE_H + 1)
    x = GRID_X
    line = sorted((part for part in rows if part[0] != "common"),
                  key=lambda part: ("rare", "legendary").index(part[0]))  # rare first, then the legendary one
    for rarity, tiles in line:
        _sign(img, x, RARE_SIGN_Y, rarity.upper(), rarity)
        for tile in tiles:
            regions.append((_tile(img, x, RARE_Y, tile, tile["item"]["id"] == chosen), ("item", tile["item"]["id"])))
            x += WIDE_W + GAP
        x += 10
    _shelf(d, 12, RIGHT_X - 16, RARE_Y + TILE_H + 1, brackets=True)


def _fitting_room(img, view, regions) -> None:
    """The right side: curtains, the stage with the player wearing the item, its name and price, and the counter."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = RIGHT_X, 66, SCREEN_W - 12, SCREEN_H - 8
    glow = view.get("glow", "#3ad6ff")
    d.rectangle([x0, y0, x1, y1], fill=rgb(INK))
    d.rectangle([x0 + 3, y0 + 3, x1 - 3, y1 - 3], fill=rgb("#1a1440"))
    stage_bottom = 314
    # the light on the back wall: two flat ovals in the rarity colour, with checkered edges
    _dithered_oval(img, (x0 + 60, 112, x1 - 60, 300), mix("#1a1440", glow, 0.18))
    _dithered_oval(img, (x0 + 110, 150, x1 - 110, 290), mix("#1a1440", glow, 0.32))
    # the stage floor
    d.rectangle([x0 + 3, stage_bottom - 22, x1 - 3, stage_bottom], fill=rgb("#2a2150"))
    d.rectangle([x0 + 3, stage_bottom - 22, x1 - 3, stage_bottom - 20], fill=mix("#2a2150", glow, 0.5))
    for k in range(x0 + 12, x1 - 6, 24):
        d.rectangle([k, stage_bottom - 17, k + 1, stage_bottom], fill=rgb("#211a42"))
    preview = view["preview"]
    px = x0 + (x1 - x0 - preview.width) // 2
    img.paste(preview, (px, stage_bottom - 14 - preview.height), preview if preview.mode == "RGBA" else None)
    # the curtains: drawn on the sides and a valance with scallops along the top
    for cx0 in (x0 + 3, x1 - 25):
        d.rectangle([cx0, y0 + 3, cx0 + 22, stage_bottom], fill=rgb(CURTAIN))
        for fold in (cx0 + 6, cx0 + 15):
            d.rectangle([fold, y0 + 20, fold + 2, stage_bottom], fill=rgb(CURTAIN_FOLD))
    d.rectangle([x0 + 3, y0 + 3, x1 - 3, y0 + 17], fill=rgb(PINK))
    d.rectangle([x0 + 3, y0 + 3, x1 - 3, y0 + 5], fill=rgb("#ff9fd0"))
    for sx in range(x0 + 3, x1 - 3, 24):  # scallops
        d.rectangle([sx + 3, y0 + 18, sx + 20, y0 + 20], fill=rgb(PINK))
        d.rectangle([sx + 7, y0 + 21, sx + 16, y0 + 23], fill=rgb(PINK))
        d.rectangle([sx + 7, y0 + 24, sx + 16, y0 + 24], fill=rgb("#c23880"))
    # what it is
    info = view.get("info")
    y = stage_bottom + 12
    if info:
        name, rarity, price = info
        lines = wrap(name.upper(), 17)[:2]
        for text in lines:
            draw_text(img, (x0 + 16, y), text, 3, "#ffffff", "lt", shadow="#3b3560")
            y += 28
        tw = text_size(rarity.upper(), 2)[0]
        _box(d, (x0 + 16, y + 2, x0 + 36 + tw, y + 26), RARITY_COLOURS[rarity], width=2)
        draw_text(img, (x0 + 26 + tw // 2, y + 15), rarity.upper(), 2, RARITY_INK[rarity], "mm")
        if price is not None:
            coin(img, x0 + 52 + tw, y + 6, 2)
            draw_text(img, (x0 + 74 + tw, y + 15), str(price), 2, "#ffe94a", "lm")
    # the counter, with the buttons on it
    top = y1 - 70
    d.rectangle([x0 + 3, top, x1 - 3, top + 4], fill=rgb(WOOD_TOP))
    d.rectangle([x0 + 3, top + 5, x1 - 3, y1 - 3], fill=rgb(WOOD))
    d.rectangle([x0 + 3, y1 - 12, x1 - 3, y1 - 3], fill=rgb("#4a2a20"))
    for k in range(x0 + 40, x1 - 20, 60):
        d.rectangle([k, top + 12, k + 1, y1 - 14], fill=rgb("#5a3324"))
    progress = view.get("progress")
    if progress:  # not enough coins: how far there is to go
        have, need = progress
        bx0, bx1, by = x0 + 16, x1 - 16, top - 30
        d.rectangle([bx0, by, bx1, by + 14], fill=rgb(INK))
        d.rectangle([bx0 + 3, by + 3, bx1 - 3, by + 11], fill=rgb("#2c2652"))
        filled = bx0 + 3 + int((bx1 - bx0 - 6) * min(1.0, have / max(1, need)))
        d.rectangle([bx0 + 3, by + 3, filled, by + 11], fill=rgb("#ffe94a"))
        for k in range(bx0 + 3, bx1 - 3, 12):
            d.rectangle([k, by + 3, k + 1, by + 11], fill=rgb(INK))
    if view.get("note"):
        draw_text(img, ((x0 + x1) // 2, top - 8), view["note"].upper(), 1, PINK, "mb")
    actions = view.get("actions", [])
    width = (x1 - x0 - 32 - 12 * (len(actions) - 1)) // max(1, len(actions))
    for i, (label, action, enabled) in enumerate(actions):
        bx = x0 + 16 + i * (width + 12)
        box = _button(img, (bx, top + 14, bx + width, top + 52), label, enabled)
        if enabled:
            regions.append((box, (action,)))


def shop_picture(view: dict):
    """Returns (picture, clickable regions).

    view: title, coins (or None), slot (the tab on show), sections [(rarity, [tile...])] where a tile is {"item",
    "picture", "badge", "kind"}, chosen (the id on show or None), preview (the player from three sides, see-through,
    see sprites.showcase), glow (the colour of the light on the stage), info (name, rarity, price or None), actions
    [(label, action, enabled)], note (a short line over the counter), progress ((coins, price) when it costs too
    much), empty (shown when the tab has no items).
    Regions: ("tab", slot), ("item", id), ("back",) and each enabled action as (action,).
    """
    img = _wall().copy()
    regions = []
    _top_bar(img, view, regions)
    _shelves(img, view, regions)
    _fitting_room(img, view, regions)
    return img, regions
