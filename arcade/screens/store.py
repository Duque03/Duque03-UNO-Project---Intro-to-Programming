"""The store: three tabs (hair, shirt, name), items grouped by rarity, paid with coins."""

from __future__ import annotations

import streamlit as st

from arcade import catalog, state, ui
from arcade import player as player_model
from arcade.art import scenes, sprites
from arcade.config import PRICES, RARITIES, SLOT_LABELS, SLOTS
from arcade.logic import store
from arcade.state import S

COLUMNS = 5


def tab_picker(key: str) -> str:
    """Hair / Shirt / Name switch. Remembers the last tab if the player un-selects it."""
    choice = st.segmented_control("Tab", SLOTS, format_func=SLOT_LABELS.get, default=S.get(key + "_last", "hair"),
                                  key=key, label_visibility="collapsed", width="stretch")
    choice = choice or S.get(key + "_last", "hair")
    S[key + "_last"] = choice
    return choice


def render() -> None:
    player = S.player
    ui.picture(scenes.banner("STORE", player["coins"], "SPEND THE COINS YOU WIN AT THE TABLES"))
    slot = tab_picker("store_tab")
    look = player_model.look(player)

    for rarity in RARITIES:
        st.markdown(
            f"<b class='rarity-{rarity}'>&#9632; {rarity.upper()}</b> &nbsp; {PRICES[rarity]} coins each",
            unsafe_allow_html=True,
        )
        items = catalog.by_slot(slot, rarity)
        columns = st.columns(COLUMNS)
        for index, item in enumerate(items):
            with columns[index % COLUMNS]:
                ui.picture(sprites.item_tile(item, look, player["name"]))
                st.caption(item["name"])
                if store.owns(player, item["id"]):
                    ui.button("Owned", f"buy_{item['id']}", disabled=True)
                elif ui.button(f"Buy · {item['price']}", f"buy_{item['id']}",
                               disabled=not store.can_afford(player, item["id"]),
                               help=None if store.can_afford(player, item["id"]) else "Not enough coins"):
                    try:
                        store.buy(player, item["id"])
                        state.save()
                        st.toast(f"Bought {item['name']}! Wear it from Pause > Customize character.")
                    except store.StoreError as problem:
                        st.toast(str(problem))
                    st.rerun()

    bar = st.columns([1.6, 3.4])
    with bar[0]:
        if ui.button("Back to the arcade", "store_back", "Esc", type="primary"):
            state.go("hub")
            st.rerun()
