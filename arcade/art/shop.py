"""The store and the wardrobe as one picture each (no buttons outside the game picture).

Top: the title, the coins, the three tabs and BACK. Left: the items of the tab as tiles, by rarity. Right: the player
wearing the item on show, its name and price, and what can be done with it (BUY, WEAR, EQUIP, UNEQUIP).
"""

from __future__ import annotations

from functools import lru_cache

from PIL import Image, ImageDraw

from arcade import catalog
from arcade.art import sprites
from arcade.art.pixel import coin, draw_text, panel, rgb, shade, text_size, wrap
from arcade.art.scenes import draw_button
from arcade.config import SCREEN_H, SCREEN_W, SLOT_LABELS, SLOTS

TILE_W, TILE_H, GAP = 104, 120, 10
GRID_X, GRID_Y = 24, 78
RIGHT_X = 616
RARITY_COLOURS = {"common": "#43c47e", "rare": "#8a5cff", "legendary": "#ffae1a"}
BADGE = {"price": ("#ffe94a", "#16122b"), "poor": ("#5a5470", "#c9c3e6"), "owned": ("#3ad6ff", "#16122b"),
         "worn": ("#3ad678", "#16122b")}


@lru_cache(maxsize=512)
def tile_picture(item_id: str, look: tuple, name: str) -> Image.Image:
    """The item on the player's own character (hair: head and shoulders, shirt: down to the knees), or the tag.
    (Kept for the next runs: do not draw on the picture it returns.)"""
    item = catalog.get(item_id)
    skin, pants, hair_id, shirt_id = look
    if item["slot"] == "name":  # drawn with room to spare, then made smaller if it is wider than a tile
        img = Image.new("RGBA", (220, 80), (0, 0, 0, 0))
        sprites.draw_name_tag(img, 110, 60, name, item["spec"], scale=1)
        img = img.crop(img.getbbox())
        if img.width > TILE_W - 12:
            img = img.resize((TILE_W - 12, round(img.height * (TILE_W - 12) / img.width)), Image.NEAREST)
        return img
    if item["slot"] == "hair":
        body = sprites.sprite(skin, pants, item["id"], shirt_id, "down", 0, 0).crop((0, 0, sprites.SPR_W, 21))
    else:
        body = sprites.sprite(skin, pants, hair_id, item["id"], "down", 0, 0).crop((0, 7, sprites.SPR_W, 26))
    return body.resize((body.width * 4, body.height * 4), Image.NEAREST)


def _tile(img, x, y, tile: dict, chosen: bool) -> tuple:
    """One tile: rarity frame, the picture, and a badge (price, OWNED or WEARING) along the bottom."""
    d = ImageDraw.Draw(img)
    edge = RARITY_COLOURS[tile["item"]["rarity"]]
    if chosen:  # the item on show on the right
        d.rectangle([x - 5, y - 5, x + TILE_W + 4, y + TILE_H + 4], fill=(255, 255, 255))
    d.rectangle([x, y, x + TILE_W - 1, y + TILE_H - 1], fill=rgb(edge))
    d.rectangle([x + 4, y + 4, x + TILE_W - 5, y + TILE_H - 5], fill=(28, 22, 66))
    picture = tile["picture"]
    img.paste(picture, (x + (TILE_W - picture.width) // 2, y + 6 + (86 - picture.height) // 2), picture)
    fill, ink = BADGE[tile["kind"]]
    d.rectangle([x + 4, y + TILE_H - 28, x + TILE_W - 5, y + TILE_H - 5], fill=rgb(fill))
    if tile["kind"] in ("price", "poor"):
        width = text_size(tile["badge"], 2)[0] + 22
        coin(img, x + (TILE_W - width) // 2, y + TILE_H - 23, 1)
        draw_text(img, (x + (TILE_W - width) // 2 + 22, y + TILE_H - 16), tile["badge"], 2, ink, "lm")
    else:
        draw_text(img, (x + TILE_W // 2, y + TILE_H - 16), tile["badge"], 2, ink, "mm")
    return x, y, x + TILE_W, y + TILE_H


def shop_picture(view: dict):
    """Returns (picture, clickable regions).

    view: title, coins (or None), slot (the tab on show), sections [(rarity, [tile...])] where a tile is {"item",
    "picture", "badge", "kind"}, chosen (the id on show or None), preview (the big picture), info (name, rarity,
    price or None), actions [(label, action, enabled)], note (a short line under the actions), empty (shown when the
    tab has no items).
    Regions: ("tab", slot), ("item", id), ("back",) and each enabled action as (action,).
    """
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), rgb("#1c1642"))
    d = ImageDraw.Draw(img)
    for y in range(0, SCREEN_H, 6):
        d.rectangle([0, y, SCREEN_W, y + 5], fill=tuple(round(c * (1 - y / SCREEN_H * 0.4)) for c in (40, 30, 88)))
    regions = []

    # top: title, coins, tabs, back
    draw_text(img, (22, 16), view["title"], 4, "#ffe94a", "lt", shadow="#16122b")
    x = 22 + text_size(view["title"], 4)[0] + 18
    if view.get("coins") is not None:
        coin(img, x, 18, 3)
        draw_text(img, (x + 34, 22), str(view["coins"]), 3, "#ffe94a", "lt", shadow="#16122b")
    for i, slot in enumerate(SLOTS):
        box = (330 + i * 160, 12, 480 + i * 160, 50)
        draw_button(img, box, SLOT_LABELS[slot].upper(), 2, fill="#ffe94a" if slot == view["slot"] else "#ffffff")
        regions.append((box, ("tab", slot)))
    back = draw_button(img, (820, 12, 944, 50), "BACK", 2)
    regions.append((back, ("back",)))

    # left: the items, by rarity
    y = GRID_Y
    rows = [(r, t) for r, t in view["sections"] if t]
    if not rows:
        draw_text(img, (300, 280), view.get("empty", "").upper(), 2, "#d9d4ff", "mm")
    line = []  # rare and legendary share a line
    for rarity, tiles in rows:
        if rarity == "common":
            draw_text(img, (GRID_X, y), "COMMON", 2, RARITY_COLOURS[rarity], "lt", shadow="#16122b")
            for k, tile in enumerate(tiles):
                tx, ty = GRID_X + (k % 5) * (TILE_W + GAP), y + 22 + (k // 5) * (TILE_H + GAP)
                regions.append((_tile(img, tx, ty, tile, tile["item"]["id"] == view.get("chosen")),
                                ("item", tile["item"]["id"])))
            y += 22 + ((len(tiles) + 4) // 5) * (TILE_H + GAP) + 6
        else:
            line.append((rarity, tiles))
    x = GRID_X
    line.sort(key=lambda part: ("rare", "legendary").index(part[0]))  # rare first, then the legendary one
    for rarity, tiles in line:
        draw_text(img, (x, y), rarity.upper(), 2, RARITY_COLOURS[rarity], "lt", shadow="#16122b")
        for k, tile in enumerate(tiles):
            regions.append((_tile(img, x, y + 22, tile, tile["item"]["id"] == view.get("chosen")),
                            ("item", tile["item"]["id"])))
            x += TILE_W + GAP
        x += 14

    # right: the player wearing it, and what can be done
    panel(img, (RIGHT_X - 8, 66, SCREEN_W - 12, SCREEN_H - 12), "#16122b", "#3a2f6b", bw=3, shadow=False)
    preview = view["preview"]
    img.paste(preview, (RIGHT_X + (SCREEN_W - 20 - RIGHT_X - preview.width) // 2, 74))
    y = 74 + preview.height + 12
    info = view.get("info")
    if info:
        name, rarity, price = info
        for text in wrap(name.upper(), 18):
            draw_text(img, (RIGHT_X + 8, y), text, 3, "#ffffff", "lt", shadow="#16122b")
            y += 28
        draw_text(img, (RIGHT_X + 8, y + 2), rarity.upper(), 2, RARITY_COLOURS[rarity], "lt")
        if price is not None:
            coin(img, RIGHT_X + 140, y, 1)
            draw_text(img, (RIGHT_X + 162, y + 2), str(price), 2, "#ffe94a", "lt")
    by = SCREEN_H - 24 - 46 * len(view.get("actions", []))
    for label, action, enabled in view.get("actions", []):
        box = (RIGHT_X + 4, by, SCREEN_W - 24, by + 38)
        draw_button(img, box, label, 2, fill="#c8f7c5" if enabled else shade(rgb("#8d8aa6"), 1.0))
        if enabled:
            regions.append((box, (action,)))
        by += 46
    if view.get("note"):
        draw_text(img, ((RIGHT_X + SCREEN_W - 20) // 2, SCREEN_H - 30 - 46 * len(view.get("actions", [])) - 14),
                  view["note"].upper(), 1, "#ff8a8a", "mm")
    return img, regions
