"""Every cosmetic the store sells: 3 tabs x (10 common + 3 rare + 1 legendary).

An item is a plain dictionary:
    id      unique key, e.g. "shirt_c01"
    slot    "hair", "shirt" or "name"
    name    what the store shows
    rarity  "common", "rare" or "legendary"
    price   coins (comes from config.PRICES)
    spec    how the art code should draw it (see arcade/art/sprites.py)

To add or redesign an item, edit the lists below. Nothing else needs to change.
"""

from __future__ import annotations

from arcade.art.pixel import readable_on
from arcade.config import PRICES
from arcade.logic import looks

# Hair colours used by several styles
BLACK, BROWN, BLONDE = "#1d1a22", "#5a3a22", "#f0d264"

# What you wear before buying anything. These are not store items.
DEFAULTS = {
    "hair": {"style": "short", "c1": "#5a3a22"},
    "shirt": {"style": "solid", "c1": "#e9e9ee"},
    "name": {"bg": "#ffffff", "fg": "#16122b", "border": "#16122b", "fx": None},
}

# The themes (all designs are our own, no real clubs, brands or people):
#   football: haircuts you see on the pitch, kits in classic club colours, scarf name tags
#   battle royale: camo, helmets with visors, tactical vests, storm effects
#   Portugal: azulejo tiles, the flag colours, the Nazare fishermen's check, the Ribatejo stocking cap,
#             Santos Populares (sardines and party flags)
# Each tab has one rare item per theme.


def _build() -> list[dict]:
    items: list[dict] = []

    def add(slot, rarity, name, spec):
        number = sum(1 for i in items if i["slot"] == slot and i["rarity"] == rarity) + 1
        items.append(
            {
                "id": f"{slot}_{rarity[0]}{number:02d}",
                "slot": slot,
                "name": name,
                "rarity": rarity,
                "price": PRICES[rarity],
                "spec": spec,
            }
        )

    # ---- hair: 10 common, 3 rare (one per theme), 1 legendary
    for name, style, colour in [
        ("Brown Quiff", "quiff", BROWN), ("Black Buzz Cut", "buzz", BLACK), ("Brown Man Bun", "manbun", BROWN),
        ("Blonde Curtains", "curtains", BLONDE), ("Black Slick Back", "slick", BLACK),
        ("Black Dreads", "dreads", BLACK), ("Blonde Ponytail", "ponytail", BLONDE),
    ]:
        add("hair", "common", name, {"style": style, "c1": colour, "c2": "#d9a520"})
    add("hair", "common", "Headband Hair", {"style": "headband", "c1": BROWN, "c2": "#ffffff"})
    add("hair", "common", "Red Cap", {"style": "cap", "c1": "#d83a3a", "c2": "#7a1f1f", "c3": BROWN})
    add("hair", "common", "Grey Beanie", {"style": "beanie", "c1": "#8d8fa3", "c2": "#5d5f70", "c3": BLACK})
    add("hair", "rare", "Bleached Mohawk", {"style": "mohawk", "c1": "#f3ead2", "c2": "#f0d264"})
    add("hair", "rare", "Campino Cap", {"style": "campino", "c1": "#2a8a3a", "c2": "#d83a3a", "c3": BLACK})
    add("hair", "rare", "Visor Helmet", {"style": "helmet", "c1": "#4a5a3a", "c2": "#3ad6ff"})
    add("hair", "legendary", "Galaxy Hair", {"style": "long", "c1": "#2a0d5e", "galaxy": True})

    # ---- shirts: football kits, battle-royale outfits, Portuguese themes
    for name, colour, trim, number in [
        ("Red Kit", "#d83a3a", "#ffffff", "9"), ("White Kit", "#f3f3f7", "#16122b", "4"),
        ("Green Kit", "#2a8a3a", "#ffffff", "8"), ("Blue Kit", "#2f6fe0", "#ffffff", "10"),
    ]:
        add("shirt", "common", name, {"style": "kit", "c1": colour, "c2": trim, "num": number})
    for name, style, c1, c2 in [
        ("Blue & White Stripes", "stripes", "#ffffff", "#2f6fe0"),
        ("Green Hoops", "hoops", "#2a8a3a", "#ffffff"),
        ("Red & Blue Halves", "halves", "#d83a3a", "#2f6fe0"),
        ("White Red Sash", "sash", "#f3f3f7", "#d83a3a"),
    ]:
        add("shirt", "common", name, {"style": style, "c1": c1, "c2": c2})
    add("shirt", "common", "Forest Camo", {"style": "camo", "c1": "#5a7a3a", "c2": "#3a4a2a", "c3": "#8a7a4a"})
    add("shirt", "common", "Nazare Check", {"style": "plaid", "c1": "#2f4fa8", "c2": "#d83a3a", "c3": "#16122b"})
    add("shirt", "rare", "Azulejo Shirt", {"style": "azulejo", "c1": "#f3f6ff", "c2": "#1d4fa8", "c3": "#6fa8ff"})
    add("shirt", "rare", "Bandeira Kit", {"style": "flag", "c1": "#1f7a32", "c2": "#d22a2a", "c3": "#ffd84a",
                                          "num": "7", "nc": "#ffd84a"})
    add("shirt", "rare", "Tactical Vest", {"style": "vest", "c1": "#4a5a3a", "c2": "#2e3a24", "c3": "#8d8fa3"})
    add("shirt", "legendary", "Golden Champion", {"style": "gold", "c1": "#ffd84a", "c2": "#fff6c4",
                                                  "num": "1", "nc": "#ffffff"})

    # ---- name tags: football scarves and plain colours, then the special effects
    for name, c1, c2 in [
        ("Red & White Scarf", "#d83a3a", "#ffffff"), ("Green & White Scarf", "#2a8a3a", "#ffffff"),
        ("Blue & White Scarf", "#2f6fe0", "#ffffff"), ("Black & White Scarf", "#26262e", "#ffffff"),
        ("Green & Red Scarf", "#2a8a3a", "#d83a3a"), ("Navy & Gold Scarf", "#23346b", "#ffd84a"),
    ]:
        add("name", "common", name, {"bg": c1, "border": c1, "border2": c2, "fg": readable_on(c1), "fx": "scarf"})
    for name, colour in [("Yellow Tag", "#f2d03b"), ("Mint Tag", "#9df0c4"), ("Purple Tag", "#7a3ad8"),
                         ("Pink Tag", "#ff8ac4")]:
        add("name", "common", name, {"bg": colour, "fx": None})
    add("name", "rare", "Santos Populares", {"bg": "#bfe6ff", "fg": "#16122b", "border": "#2f6fe0",
                                             "fx": "arraial"})
    add("name", "rare", "Football Pitch", {"bg": "#2f8f3a", "fg": "#ffffff", "border": "#ffffff", "fx": "pitch"})
    add("name", "rare", "Storm Circle", {"bg": "#2a0d4a", "fg": "#ffffff", "border": "#b07aff", "fx": "storm"})
    add("name", "legendary", "Inferno", {"bg": "#3a0d0d", "fg": "#ffe94a", "border": "#ff7a1a", "fx": "fire"})
    return items


ITEMS: list[dict] = _build()
_BY_ID = {item["id"]: item for item in ITEMS}

# Looks only the bots wear. They are not sold in the store, so they are not in ITEMS.
BOT_ONLY = {
    "bot_dean_hair": {"slot": "hair", "spec": {"style": "dean", "c1": "#b9b9c4", "c2": "#1d1a22"}},
    "bot_dean_suit": {"slot": "shirt", "spec": {"style": "suit", "c1": "#2e3140", "c2": "#f3f3f6", "c3": "#8a1f2e"}},
    "bot_guard_cap": {"slot": "hair", "spec": {"style": "officer", "c1": "#1d1c22", "c2": "#d8343a", "c3": "#121116"}},
    "bot_guard_uniform": {"slot": "shirt",
                          "spec": {"style": "uniform", "c1": "#24232b", "c2": "#d8343a", "c3": "#131217"}},
    "bot_dog": {"slot": "hair", "spec": {"style": "dog", "c1": "#7a4a24", "c2": "#f0d6a8", "c3": "#1d1a22"}},
    "bot_dog_bandana": {"slot": "shirt", "spec": {"style": "solid", "c1": "#2f6fe0"}},
    "bot_john_hair": {"slot": "hair", "spec": {"style": "short", "c1": "#4a3020"}},
    "bot_john_tee": {"slot": "shirt", "spec": {"style": "solid", "c1": "#dcdde3"}},
}


def get(item_id: str) -> dict | None:
    return _BY_ID.get(item_id)


def by_slot(slot: str, rarity: str | None = None) -> list[dict]:
    return [i for i in ITEMS if i["slot"] == slot and (rarity is None or i["rarity"] == rarity)]


def spec_for(slot: str, item_id: str | None) -> dict:
    """The drawing recipe for an item, or the default look when nothing is equipped."""
    if item_id and item_id.startswith("base:"):  # the player's own base look (logic/looks.py)
        found = looks.spec(item_id)
        return found[1] if found and found[0] == slot else DEFAULTS[slot]
    item = (_BY_ID.get(item_id) or BOT_ONLY.get(item_id)) if item_id else None
    if item is None or item["slot"] != slot:
        return DEFAULTS[slot]
    return item["spec"]
