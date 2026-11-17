"""Customize character: try on what you own, then press E to equip or U to take it off.

The items you are wearing have a green pixel tick.
"""

from __future__ import annotations

import streamlit as st

from arcade import state, tiles, ui
from arcade import player as player_model
from arcade.art import scenes
from arcade.config import RARITIES, SLOT_LABELS
from arcade.logic import store
from arcade.screens.store import picked_item, preview, tab_picker
from arcade.state import S


def render() -> None:
    player = S.player
    ui.picture(scenes.banner("WARDROBE", None, "CLICK AN ITEM TO TRY IT ON"))
    left, right = st.columns([3, 2], gap="medium")

    with left:
        slot = tab_picker("wardrobe_tab")
        focus = picked_item("wardrobe_focus", slot)
        if focus is not None and not store.owns(player, focus["id"]):
            focus = None
        look = player_model.look(player)
        owned = store.owned_items(player, slot)
        sections = []
        for rarity in RARITIES:
            row = []
            for item in owned:
                if item["rarity"] != rarity:
                    continue
                worn = player["equipped"][slot] == item["id"]
                row.append(tiles.tile(item, look, player["name"], worn=worn,
                                      picked=focus is not None and focus["id"] == item["id"],
                                      badge="WEARING" if worn else "OWNED", badge_kind="worn" if worn else "owned"))
            sections.append(tiles.section(rarity, row))
        empty = f"You do not own any {SLOT_LABELS[slot].lower()} items yet. Buy some in the store."
        clicked = tiles.grid(sections, key="wardrobe_grid", empty=empty)
        if clicked is not None and clicked != S.get("wardrobe_focus"):
            S.wardrobe_focus = clicked
            st.rerun()

    with right:
        ui.picture(preview(player, slot, focus))
        if focus:
            state_text = "wearing" if player["equipped"][slot] == focus["id"] else "trying on"
            st.caption(f"{focus['name']} ({focus['rarity']}) - {state_text}")
        else:
            st.caption("Showing what you are wearing now.")
        can_equip = focus is not None and player["equipped"][slot] != focus["id"]
        equip = ui.button("Equip", "wardrobe_equip", "E", type="primary", disabled=not can_equip)
        unequip = ui.button(f"Unequip {SLOT_LABELS[slot].lower()}", "wardrobe_unequip", "U",
                            disabled=player["equipped"][slot] is None)
        back = ui.button("Back", "wardrobe_back", "Esc")

    if equip and can_equip:
        store.equip(player, focus["id"])
        state.save()
        st.rerun()
    if unequip and player["equipped"][slot] is not None:
        store.unequip(player, slot)
        S.wardrobe_focus = None
        state.save()
        st.rerun()
    if back:
        state.go("pause")
        st.rerun()
