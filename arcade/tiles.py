"""The grid of item tiles in the store and the wardrobe.

The browser draws the grid (HTML buttons), so a whole tab fits on one screen and a
click answers straight away. Python sends the pictures and the state of each tile
(price, owned, worn, picked) and hears back which tile was clicked.

    picked = tiles.grid(sections, key="store_grid")   # the item id clicked this run, or None
"""

from __future__ import annotations

import base64
import io
import json
from functools import lru_cache

import streamlit as st
from PIL import Image

from arcade import catalog
from arcade.art import sprites
from arcade.art.pixel import coin, new_layer, outlined

# A green pixel tick (on the items you are wearing) and a coin (next to the prices).
_TICK = [
    "......##",
    ".....##.",
    "##..##..",
    ".####...",
    "..##....",
]


def _data_url(img: Image.Image) -> str:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


@lru_cache(maxsize=1)
def tick_url() -> str:
    layer = new_layer((len(_TICK[0]) + 2, len(_TICK) + 2))
    for y, row in enumerate(_TICK):
        for x, cell in enumerate(row):
            if cell == "#":
                layer.putpixel((x + 1, y + 1), (58, 214, 120, 255))
    return _data_url(outlined(layer))


@lru_cache(maxsize=1)
def coin_url() -> str:
    img = new_layer((10, 10))
    coin(img, 1, 1, 1)
    return _data_url(img)


@lru_cache(maxsize=1024)
def tile_picture(item_id: str, look: tuple, name: str) -> str:
    """The item on the player's own character (hair: head and shoulders, shirt: whole body), or the name tag."""
    item = catalog.get(item_id)
    skin, pants, hair_id, shirt_id = look
    if item["slot"] == "name":
        img = new_layer((260, 76))
        sprites.draw_name_tag(img, 130, 60, name, item["spec"])
        return _data_url(img.crop(img.getbbox()))
    if item["slot"] == "hair":
        hair_id = item_id
    else:
        shirt_id = item_id
    img = sprites.sprite(skin, pants, hair_id, shirt_id, "down", 0, 0)
    if item["slot"] == "hair":
        img = img.crop((0, 0, sprites.SPR_W, 21))  # head and shoulders
    else:
        img = img.crop((0, 7, sprites.SPR_W, 26))  # head to knees, so the shirt is bigger
    return _data_url(img)


def tile(item: dict, look: tuple, name: str, *, picked: bool, badge: str, badge_kind: str,
         worn: bool = False) -> dict:
    """What the browser needs to draw one tile. badge_kind: "price", "poor", "owned" or "worn"."""
    return {
        "id": item["id"],
        "name": item["name"],
        "img": tile_picture(item["id"], look, name),
        "wide": item["slot"] == "name",
        "picked": picked,
        "worn": worn,
        "badge": badge,
        "kind": badge_kind,
    }


def section(rarity: str, tiles: list[dict]) -> dict:
    """A group of tiles under a heading (the price is on every tile, so the heading is just the rarity)."""
    return {"rarity": rarity, "title": rarity.upper(), "tiles": tiles}


CSS = """
.tile-root { font-family: "Jersey 10", monospace; color: #f3ead2; --tile: 72px; }
.tile-root .row { display: flex; flex-wrap: wrap; gap: 4px 14px; align-items: flex-start; }
.tile-root .section { margin-bottom: 8px; }
.tile-root .head { font-size: 1.15rem; letter-spacing: .08em; margin: 0 0 4px 2px; white-space: nowrap;
    display: inline-block; border-bottom: 3px solid currentColor; padding-bottom: 1px; }
.tile-root .head.legendary { color: #ffc23a; } .tile-root .head.rare { color: #b98aff; }
.tile-root .head.common { color: #6fe0a0; }
.tile-root .grid { display: flex; flex-wrap: wrap; gap: 7px; }

/* item cards, like the item shop of a big game: the rarity colour glows behind the item */
.tile-root button.tile {
    --base: #1d4a35; --glow: #43c47e; --edge: #7cffb0;
    position: relative; width: var(--tile); padding: 0; margin: 0; cursor: pointer; overflow: hidden;
    display: flex; flex-direction: column; align-items: stretch; color: #ffffff; font: inherit;
    background: radial-gradient(circle at 50% 38%, var(--glow) 0%, var(--base) 72%);
    border: 2px solid var(--edge); border-radius: 7px;
    box-shadow: inset 0 0 0 2px rgba(0, 0, 0, .35), 0 3px 0 rgba(0, 0, 0, .45);
    transition: transform .1s, box-shadow .1s, filter .1s;
}
.tile-root button.tile.rare { --base: #2c1666; --glow: #8a5cff; --edge: #c9a8ff; }
.tile-root button.tile.legendary { --base: #6a2a06; --glow: #ffae1a; --edge: #ffe08a; }
.tile-root button.tile.wide { width: calc(var(--tile) * 1.5 + 4px); }
.tile-root button.tile.featured { width: calc(var(--tile) * 2 + 7px); }
.tile-root button.tile.featured.wide { width: calc(var(--tile) * 1.5 + 4px); }
.tile-root button.tile:hover { transform: translateY(-3px) scale(1.03); filter: brightness(1.12);
    box-shadow: inset 0 0 0 2px rgba(0, 0, 0, .35), 0 0 14px var(--glow); }
.tile-root button.tile:focus-visible { outline: 3px solid #ffe94a; outline-offset: 1px; }
.tile-root button.tile.picked { border-color: #ffffff;
    box-shadow: 0 0 0 3px #ffffff, 0 0 18px var(--glow), inset 0 0 0 2px rgba(0, 0, 0, .35); }
.tile-root button.tile.featured::after {  /* a shine that sweeps across the featured item */
    content: ""; position: absolute; top: 0; left: -60%; width: 40%; height: 100%; pointer-events: none;
    background: linear-gradient(100deg, transparent, rgba(255, 255, 255, .35), transparent);
    animation: tile-shine 2.6s ease-in-out infinite;
}
@keyframes tile-shine { 0% { left: -60%; } 55%, 100% { left: 130%; } }
.tile-root .pic { height: calc(var(--tile) * .8); width: 100%; display: flex; align-items: center;
    justify-content: center; padding: 3px 3px 0; box-sizing: border-box; }
.tile-root button.tile.featured .pic { height: calc(var(--tile) * 1.9); }
.tile-root .pic img { image-rendering: pixelated; max-width: 100%; max-height: 100%; height: 100%;
    object-fit: contain; filter: drop-shadow(0 3px 2px rgba(0, 0, 0, .55)); }
.tile-root button.tile.wide .pic { height: calc(var(--tile) * .5); }
.tile-root button.tile.wide.featured .pic { height: calc(var(--tile) * .5); }
.tile-root button.tile.wide .pic img { height: auto; image-rendering: auto; }
.tile-root .strip { background: rgba(5, 3, 18, .72); padding: 2px 3px 3px; display: flex; flex-direction: column;
    align-items: center; gap: 1px; }
.tile-root .name { font-size: .95rem; line-height: 1; max-width: 100%; overflow: hidden; text-overflow: ellipsis;
    white-space: nowrap; text-transform: uppercase; letter-spacing: .03em; }
.tile-root button.tile.featured .name { font-size: 1.2rem; }
.tile-root.compact button.tile:not(.wide):not(.featured) .name { display: none; }
.tile-root .badge { font-size: 1.05rem; line-height: 1; display: flex; align-items: center; gap: 3px; }
.tile-root .badge img { width: 12px; height: 12px; image-rendering: pixelated; }
.tile-root .badge.price { color: #ffe94a; } .tile-root .badge.poor { color: #ff6b7a; }
.tile-root .badge.owned { color: #7cffb0; } .tile-root .badge.worn { color: #3ad678; }
.tile-root .tick { position: absolute; top: 4px; right: 4px; width: 22px; image-rendering: pixelated; z-index: 2; }
.tile-root .label { position: absolute; top: 4px; left: 5px; font-size: .9rem; letter-spacing: .08em;
    color: #1a0f2e; background: #ffe08a; padding: 0 4px; border-radius: 3px; z-index: 2; }
"""

JS = r"""
export default function (component) {
    const { data, setTriggerValue, parentElement } = component;
    let root = parentElement.querySelector(".tile-root");
    if (!root) {
        root = document.createElement("div");
        root.className = "tile-root";
        parentElement.appendChild(root);
    }
    // Size the cards to the space there is: five across (the 10 commons make two rows), never tiny, never huge.
    const fit = () => {
        const width = root.clientWidth || parentElement.clientWidth || 600;
        const tall = Math.floor((window.innerHeight - 460) / 3.5);  // and the whole store must fit in the height
        const size = Math.max(50, Math.min(88, tall, Math.floor((width - 4 * 7 - 4) / 5)));
        root.style.setProperty("--tile", size + "px");
        root.classList.toggle("compact", size < 72);  // small tiles: the name shows on hover and in the preview
    };
    if (!root.__resize) {
        root.__resize = new ResizeObserver(fit);
        root.__resize.observe(root);
    }
    root.onclick = (event) => {
        const button = event.target.closest("button.tile");
        if (button) setTriggerValue("pick", button.dataset.id);
    };
    const text = JSON.stringify(data);
    if (root.__last === text) return;  // nothing changed: keep the page as it is
    root.__last = text;

    const escape = (s) => String(s).replace(/[&<>"']/g, (c) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
    const tileHtml = (t, rarity) => {
        const coinImg = (t.kind === "price" || t.kind === "poor") ? `<img src="${data.coin}" alt="">` : "";
        const featured = rarity === "legendary";
        return `<button class="tile ${rarity}${t.wide ? " wide" : ""}${featured ? " featured" : ""}${t.picked ? " picked" : ""}"
                    data-id="${escape(t.id)}" title="${escape(t.name)}">
            ${featured ? `<span class="label">FEATURED</span>` : ""}
            <span class="pic"><img src="${t.img}" alt="${escape(t.name)}"></span>
            <span class="strip"><span class="name">${escape(t.name)}</span>
            <span class="badge ${t.kind}">${coinImg}${escape(t.badge)}</span></span>
            ${t.worn ? `<img class="tick" src="${data.tick}" alt="worn">` : ""}
        </button>`;
    };
    const sectionHtml = (s) => `<div class="section">
        <div class="head ${s.rarity}">&#9632; ${escape(s.title)}</div>
        <div class="grid">${s.tiles.map((t) => tileHtml(t, s.rarity)).join("")}</div></div>`;
    const top = data.sections.filter((s) => s.rarity !== "common" && s.tiles.length);
    const rest = data.sections.filter((s) => s.rarity === "common" && s.tiles.length);
    root.innerHTML = (top.length ? `<div class="row">${top.map(sectionHtml).join("")}</div>` : "")
        + rest.map(sectionHtml).join("")
        + (data.empty && !top.length && !rest.length ? `<p>${escape(data.empty)}</p>` : "");
    fit();
}
"""

_grid = st.components.v2.component("arcade_tiles", css=CSS, js=JS)


def grid(sections: list[dict], key: str, empty: str = "") -> str | None:
    """Show the tiles. Returns the id of the tile clicked in this run, or None."""
    data = {"sections": sections, "tick": tick_url(), "coin": coin_url(), "empty": empty}
    result = _grid(key=key, data=data, width="stretch", on_pick_change=lambda: None)
    picked = getattr(result, "pick", None)
    if isinstance(picked, str) and catalog.get(picked) is not None:
        return picked
    return None


def data_size(sections: list[dict]) -> int:
    """How many bytes the grid sends to the browser (kept small on purpose, see tests)."""
    return len(json.dumps(sections))
