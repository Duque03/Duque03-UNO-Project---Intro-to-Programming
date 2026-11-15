"""Buying and wearing cosmetics. Works on the plain player dictionary."""

from __future__ import annotations

from arcade import catalog


class StoreError(ValueError):
    """Raised when a purchase or outfit change is not allowed."""


def owns(player: dict, item_id: str) -> bool:
    return item_id in player["owned"]


def can_afford(player: dict, item_id: str) -> bool:
    item = catalog.get(item_id)
    return item is not None and player["coins"] >= item["price"]


def buy(player: dict, item_id: str) -> dict:
    """Pay for an item and add it to the wardrobe. Returns the item."""
    item = catalog.get(item_id)
    if item is None:
        raise StoreError("That item does not exist.")
    if owns(player, item_id):
        raise StoreError("You already own that item.")
    if player["coins"] < item["price"]:
        raise StoreError(f"Not enough coins: you need {item['price'] - player['coins']} more.")
    player["coins"] -= item["price"]
    player["owned"].append(item_id)
    return item


def equip(player: dict, item_id: str) -> dict:
    item = catalog.get(item_id)
    if item is None:
        raise StoreError("That item does not exist.")
    if not owns(player, item_id):
        raise StoreError("You can only wear items you own.")
    player["equipped"][item["slot"]] = item_id
    return item


def unequip(player: dict, slot: str) -> None:
    """Go back to the default look for one slot (hair, shirt or name)."""
    if slot not in player["equipped"]:
        raise StoreError("There is no such slot.")
    player["equipped"][slot] = None


def owned_items(player: dict, slot: str) -> list[dict]:
    return [item for item in catalog.by_slot(slot) if item["id"] in player["owned"]]
