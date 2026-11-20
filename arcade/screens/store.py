"""The store: click an item to see it on your character, then buy it with coins.

One picture (arcade/art/shop.py): the tabs (hair, shirt, name) and BACK at the top, every item of the tab on the
shelves as a tile showing only the item, with its price, or OWNED / WEARING, and on the right a fitting room with you
wearing the item on show, with BUY or WEAR on the counter.
Keys: Left / Right the items, Up / Down the tabs, Enter buys (or wears what you own), Esc goes back.
"""

from __future__ import annotations

import streamlit as st

from arcade import catalog, state, ui
from arcade import player as player_model
from arcade.art import shop, sprites
from arcade.config import RARITIES, SLOTS
from arcade.logic import cursor, store
from arcade.state import S

# How a tile's badge looks for each store.status()
BADGES = {"worn": ("WEARING", "worn"), "owned": ("OWNED", "owned")}
GLOWS = {"common": "#43c47e", "rare": "#8a5cff", "legendary": "#ffae1a"}  # the stage light, by rarity


def current_tab(key: str) -> str:
    """The tab on show (hair, shirt or name)."""
    return S.get(key) if S.get(key) in SLOTS else "hair"


def tab_key(key: str | None, tab: str) -> None:
    """Up / Down: the tab above or below."""
    if key in ("up", "down"):
        S[tab] = SLOTS[cursor.step(SLOTS.index(current_tab(tab)), key, len(SLOTS))]


def item_key(key: str | None, ids: list[str], focus_key: str) -> None:
    """Left / Right: show the item next to the one on show, like a click on it. ids: the tab's items in screen order.

    Call it before the picture is drawn, so this run already shows the new item.
    """
    if key in ("left", "right") and ids:
        here = ids.index(S[focus_key]) if S.get(focus_key) in ids else None
        S[focus_key] = ids[cursor.step(here, key, len(ids))]


def picked_item(key: str, slot: str) -> dict | None:
    """The item clicked last, if it belongs to the tab on screen."""
    item = catalog.get(S.get(key) or "")
    return item if item is not None and item["slot"] == slot else None


def preview(player: dict, slot: str, item: dict | None):
    """The big picture of the player wearing the item (or what they wear now), from three sides."""
    trying = {slot: item["id"]} if item else None
    worn = dict(player["equipped"], **(trying or {}))
    return sprites.showcase(player_model.look(player, trying), player["name"], worn["name"], scale=4)


def glow(item: dict | None) -> str:
    """The colour of the light on the stage: the rarity of the item on show."""
    return GLOWS[item["rarity"]] if item else "#3ad6ff"


def shop_click(action, tab: str, focus_key: str) -> None:
    """A click on a tab or an item of the store or the wardrobe picture."""
    if action and action[0] == "tab" and action[1] in SLOTS:
        S[tab], S[focus_key] = action[1], None
        st.rerun()
    if action and action[0] == "item" and catalog.get(action[1]) is not None and action[1] != S.get(focus_key):
        S[focus_key] = action[1]
        st.rerun()


def _tile(player: dict, item: dict, look: tuple) -> dict:
    status = store.status(player, item["id"])
    badge, kind = BADGES.get(status, (str(item["price"]), "price" if status == "affordable" else "poor"))
    return {"item": item, "picture": shop.tile_picture(item["id"], look, player["name"]), "badge": badge, "kind": kind}


def render() -> None:
    player = S.player
    key = ui.keys("store", ui.ARROWS)  # read first: this run already shows the move (Left / Right items, Up / Down tabs)
    tab_key(key, "store_tab")
    slot = current_tab("store_tab")
    item_key(key, [item["id"] for rarity in RARITIES for item in catalog.by_slot(slot, rarity)], "store_focus")
    focus = picked_item("store_focus", slot)
    look = player_model.look(player)
    status = store.status(player, focus["id"]) if focus else None
    actions, note, progress = [], "", None
    if status in ("affordable", "too_expensive"):
        actions = [(f"BUY FOR {focus['price']}", "buy", status == "affordable")]
        if status == "too_expensive":
            note = f"{store.coins_missing(player, focus['id'])} more coins needed"
            progress = (player["coins"], focus["price"])
    elif status == "owned":
        actions = [("WEAR IT", "wear", True)]
    elif status == "worn":
        actions = [("WEARING IT", "worn", False)]
    view = {"title": "STORE", "coins": player["coins"], "slot": slot,
            "sections": [(r, [_tile(player, item, look) for item in catalog.by_slot(slot, r)]) for r in RARITIES],
            "chosen": focus["id"] if focus else None, "preview": preview(player, slot, focus), "glow": glow(focus),
            "info": (focus["name"], focus["rarity"], focus["price"]) if focus else None, "actions": actions,
            "note": note, "progress": progress}
    img, regions = shop.shop_picture(view)
    ui.show(ui.screen(), img)
    action = ui.hit(regions, ui.click())
    bar = ui.bar("store", [1, 1])  # invisible: only the keys (everything is on the picture)
    with bar[0]:
        enter = ui.button("Buy", "store_buy", "Enter", disabled=status not in ("affordable", "owned"))
    with bar[1]:
        back = ui.button("Back to the arcade", "store_back", "Esc")

    shop_click(action, "store_tab", "store_focus")
    if (enter and status == "affordable") or action == ("buy",):
        try:
            store.buy(player, focus["id"])
            state.save()
            ui.toast(f"Bought {focus['name']}!")
        except store.StoreError as problem:
            ui.toast(str(problem))
        st.rerun()
    if (enter and status == "owned") or action == ("wear",):
        store.equip(player, focus["id"])
        state.save()
        st.rerun()
    if back or action == ("back",):
        state.go("hub")
        st.rerun()

