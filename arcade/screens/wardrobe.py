"""Wardrobe: try on what you own, then EQUIP it (E or Enter) or take it off with UNEQUIP (U).

One picture, like the store (arcade/art/shop.py), with only the items you own.
"""

from __future__ import annotations

import streamlit as st

from arcade import state, ui
from arcade import player as player_model
from arcade.art import shop
from arcade.config import RARITIES, SLOT_LABELS
from arcade.logic import store
from arcade.screens.store import current_tab, item_key, picked_item, preview, shop_click, tab_key
from arcade.state import S


def render() -> None:
    player = S.player
    key = ui.keys("wardrobe", ui.ARROWS)  # read first: this run already shows the move (Left / Right items, Up / Down tabs)
    tab_key(key, "wardrobe_tab")
    slot = current_tab("wardrobe_tab")
    owned = store.owned_items(player, slot)
    item_key(key, [item["id"] for rarity in RARITIES for item in owned if item["rarity"] == rarity], "wardrobe_focus")
    focus = picked_item("wardrobe_focus", slot)
    if focus is not None and not store.owns(player, focus["id"]):
        focus = None
    look = player_model.look(player)
    sections = []
    for rarity in RARITIES:
        row = []
        for item in owned:
            if item["rarity"] == rarity:
                worn = player["equipped"][slot] == item["id"]
                row.append({"item": item, "picture": shop.tile_picture(item["id"], look, player["name"]),
                            "badge": "WEARING" if worn else "OWNED", "kind": "worn" if worn else "owned"})
        sections.append((rarity, row))
    can_equip = focus is not None and player["equipped"][slot] != focus["id"]
    can_unequip = player["equipped"][slot] is not None
    view = {"title": "WARDROBE", "coins": None, "slot": slot, "sections": sections,
            "chosen": focus["id"] if focus else None, "preview": preview(player, slot, focus),
            "info": (focus["name"], focus["rarity"], None) if focus else None,
            "actions": [("EQUIP", "equip", can_equip), (f"UNEQUIP {SLOT_LABELS[slot].upper()}", "unequip", can_unequip)],
            "empty": f"You do not own any {SLOT_LABELS[slot].lower()} items yet"}
    img, regions = shop.shop_picture(view)
    ui.show(ui.screen(), img)
    action = ui.hit(regions, ui.click())
    bar = ui.bar("wardrobe", [1, 1, 1, 1])  # invisible: only the keys (everything is on the picture)
    with bar[0]:
        equip = ui.button("Equip", "wardrobe_equip", "E", disabled=not can_equip)
    with bar[1]:
        enter = ui.button("Equip ", "wardrobe_enter", "Enter", disabled=not can_equip)
    with bar[2]:
        unequip = ui.button("Unequip", "wardrobe_unequip", "U", disabled=not can_unequip)
    with bar[3]:
        back = ui.button("Back", "wardrobe_back", "Esc")

    shop_click(action, "wardrobe_tab", "wardrobe_focus")
    if (equip or enter or action == ("equip",)) and can_equip:
        store.equip(player, focus["id"])
        state.save()
        st.rerun()
    if (unequip or action == ("unequip",)) and can_unequip:
        store.unequip(player, slot)
        S.wardrobe_focus = None
        state.save()
        st.rerun()
    if back or action == ("back",):
        state.go("pause")
        st.rerun()
