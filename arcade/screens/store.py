"""The store: click an item to see it on your character, then buy it with coins.

Left: the three tabs (hair, shirt, name) and every item of the tab as a tile showing its price,
or OWNED / WEARING. Right: a big preview of you wearing the picked item, and the Buy button.
"""

from __future__ import annotations

import streamlit as st

from arcade import catalog, state, tiles, ui
from arcade import player as player_model
from arcade.art import scenes, sprites
from arcade.config import RARITIES, SLOT_LABELS, SLOTS
from arcade.logic import cursor, store
from arcade.state import S

# How a tile's badge looks for each store.status()
BADGES = {"worn": ("WEARING", "worn"), "owned": ("OWNED", "owned")}


def tab_picker(key: str) -> str:
    """Hair / Shirt / Name switch. Remembers the last tab if the player un-selects it. Up / Down change it too."""
    wanted = S.pop(key + "_next", None)  # asked for by Up / Down earlier in this run (see tab_key)
    if wanted in SLOTS:
        S[key] = wanted  # set before the switch is drawn, the only moment Streamlit allows it
    default = None if key in S else S.get(key + "_last", "hair")  # (a default as well would make Streamlit warn)
    choice = st.segmented_control("Tab", SLOTS, format_func=SLOT_LABELS.get, default=default,
                                  key=key, label_visibility="collapsed", width="stretch")
    choice = choice or S.get(key + "_last", "hair")
    S[key + "_last"] = choice
    return choice


def tab_key(key: str | None, tab: str) -> None:
    """Up / Down: the tab above or below. Call it before tab_picker, which applies it in this same run."""
    if key in ("up", "down"):
        here = S.get(tab) or S.get(tab + "_last", "hair")
        S[tab + "_next"] = SLOTS[cursor.step(SLOTS.index(here), key, len(SLOTS))]


def item_key(key: str | None, ids: list[str], focus_key: str) -> None:
    """Left / Right: show the item next to the one on show, like a click on it. ids: the tab's items in screen order.

    Call it before the tiles and the preview are drawn, so this run already shows the new item.
    """
    if key in ("left", "right") and ids:
        here = ids.index(S[focus_key]) if S.get(focus_key) in ids else None
        S[focus_key] = ids[cursor.step(here, key, len(ids))]


def picked_item(key: str, slot: str) -> dict | None:
    """The item clicked last, if it belongs to the tab on screen."""
    item = catalog.get(S.get(key) or "")
    return item if item is not None and item["slot"] == slot else None


GLOWS = {"common": "#43c47e", "rare": "#8a5cff", "legendary": "#ffae1a"}  # the same colours as the tiles


def preview(player: dict, slot: str, item: dict | None):
    """The big picture of the player wearing the item (or what they wear now)."""
    trying = {slot: item["id"]} if item else None
    worn = dict(player["equipped"], **(trying or {}))
    glow = GLOWS[item["rarity"]] if item else "#3ad6ff"
    return sprites.showcase(player_model.look(player, trying), player["name"], worn["name"], glow=glow)


def _tile(player: dict, item: dict, look: tuple, focus: dict | None) -> dict:
    status = store.status(player, item["id"])
    badge, kind = BADGES.get(status, (str(item["price"]), "price" if status == "affordable" else "poor"))
    return tiles.tile(item, look, player["name"], picked=focus is not None and focus["id"] == item["id"],
                      badge=badge, badge_kind=kind, worn=status == "worn")


def render() -> None:
    player = S.player
    key = ui.keys("store", ui.ARROWS)  # read first: this run already shows the move (Left / Right items, Up / Down tabs)
    tab_key(key, "store_tab")
    ui.picture(scenes.banner("STORE", player["coins"], "CLICK AN ITEM (OR LEFT / RIGHT) TO TRY IT ON"))
    left, right = st.columns([3, 2], gap="medium")

    with left:
        slot = tab_picker("store_tab")
        item_key(key, [item["id"] for rarity in RARITIES for item in catalog.by_slot(slot, rarity)], "store_focus")
        focus = picked_item("store_focus", slot)
        look = player_model.look(player)
        sections = [tiles.section(rarity, [_tile(player, item, look, focus) for item in catalog.by_slot(slot, rarity)])
                    for rarity in RARITIES]
        clicked = tiles.grid(sections, key="store_grid")
        if clicked is not None and clicked != S.get("store_focus"):
            S.store_focus = clicked
            st.rerun()

    with right:
        ui.picture(preview(player, slot, focus))
        if focus is None:
            st.caption("Click an item to see it on you.")
            status = None
        else:
            status = store.status(player, focus["id"])
            st.markdown(f"<p class='store-item'><b class='rarity-{focus['rarity']}'>{focus['name']}</b>"
                        f" &middot; {focus['rarity']} &middot; {focus['price']} coins</p>", unsafe_allow_html=True)
        buy = wear = False
        if status in ("affordable", "too_expensive"):  # Enter buys (a greyed-out button ignores it)
            buy = ui.button(f"Buy for {focus['price']} coins", "store_buy", "Enter", type="primary",
                            disabled=status == "too_expensive")
            if status == "too_expensive":
                st.caption(f"You need {store.coins_missing(player, focus['id'])} more coins. Win games to earn them.")
        elif status == "owned":
            wear = ui.button("Wear it now", "store_wear", "Enter", type="primary")
        elif status == "worn":
            ui.button("You are wearing it", "store_worn", disabled=True)
        back = ui.button("Back to the arcade", "store_back", "Esc")

    if buy:
        try:
            store.buy(player, focus["id"])
            state.save()
            st.toast(f"Bought {focus['name']}!")
        except store.StoreError as problem:
            st.toast(str(problem))
        st.rerun()
    if wear:
        store.equip(player, focus["id"])
        state.save()
        st.rerun()
    if back:
        state.go("hub")
        st.rerun()
