"""Customize character: try on what you own, then press E to equip or U to take it off."""

from __future__ import annotations

import streamlit as st

from arcade import catalog, state, ui
from arcade import player as player_model
from arcade.art import scenes, sprites
from arcade.config import SLOT_LABELS
from arcade.logic import store
from arcade.screens.store import tab_picker
from arcade.state import S

COLUMNS = 3


def render() -> None:
    player = S.player
    ui.picture(scenes.banner("WARDROBE", None, "CLICK AN ITEM TO TRY IT ON"))
    left, right = st.columns([3, 2], gap="large")

    with left:
        slot = tab_picker("wardrobe_tab")
        focus = catalog.get(S.get("wardrobe_focus") or "")
        if focus and focus["slot"] != slot:
            focus = None  # the tried-on item belongs to another tab
        owned = store.owned_items(player, slot)
        if not owned:
            st.info(f"You do not own any {SLOT_LABELS[slot].lower()} items yet. Buy some in the store.")
        columns = st.columns(COLUMNS)
        look = player_model.look(player)
        for index, item in enumerate(owned):
            with columns[index % COLUMNS]:
                ui.picture(sprites.item_tile(item, look, player["name"]))
                equipped = player["equipped"][slot] == item["id"]
                label = ("✅ " if equipped else "") + item["name"]
                chosen = focus is not None and focus["id"] == item["id"]
                if ui.button(label, f"try_{item['id']}", type="primary" if chosen else "secondary"):
                    S.wardrobe_focus = item["id"]
                    st.rerun()

    with right:
        preview = {slot: focus["id"]} if focus else None
        worn = dict(player["equipped"], **(preview or {}))
        ui.picture(sprites.portrait(player_model.look(player, preview), player["name"], worn["name"]))
        if focus:
            state_text = "equipped" if player["equipped"][slot] == focus["id"] else "trying on"
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
