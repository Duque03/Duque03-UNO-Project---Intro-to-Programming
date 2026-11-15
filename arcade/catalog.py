"""Every cosmetic the store sells: 3 tabs x (20 common + 5 rare + 1 legendary).

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

from arcade.config import PRICES

# name, colour
PALETTE = [
    ("Red", "#d83a3a"), ("Orange", "#f08a24"), ("Yellow", "#f2d03b"), ("Lime", "#a4d93a"),
    ("Green", "#3aa655"), ("Teal", "#2a9d8f"), ("Cyan", "#3ad6d9"), ("Sky", "#6fb7ff"),
    ("Blue", "#2f6fe0"), ("Navy", "#23346b"), ("Purple", "#7a3ad8"), ("Violet", "#b07aff"),
    ("Pink", "#ff8ac4"), ("Magenta", "#d93a9c"), ("Brown", "#8a5a33"), ("Tan", "#d9b382"),
    ("Cream", "#f3ead2"), ("Grey", "#8d8fa3"), ("Black", "#26262e"), ("Mint", "#9df0c4"),
]

HAIR_STYLES = [("Short", "short"), ("Spikes", "spiky"), ("Long", "long"), ("Bob", "bob"), ("Ponytail", "ponytail")]
HAIR_COLOURS = [("Black", "#1d1a22"), ("Blonde", "#f0d264"), ("Ginger", "#d9662b"), ("Silver", "#c9ccd6")]

# What you wear before buying anything. These are not store items.
DEFAULTS = {
    "hair": {"style": "short", "c1": "#5a3a22"},
    "shirt": {"style": "solid", "c1": "#e9e9ee"},
    "name": {"bg": "#ffffff", "fg": "#16122b", "border": "#16122b", "fx": None},
}


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

    # ---- hair: 20 common, 5 rare, 1 legendary
    for style_name, style in HAIR_STYLES:
        for colour_name, colour in HAIR_COLOURS:
            add("hair", "common", f"{colour_name} {style_name}", {"style": style, "c1": colour})
    add("hair", "rare", "Neon Mohawk", {"style": "mohawk", "c1": "#7cff3a", "c2": "#2fb81f"})
    add("hair", "rare", "Cosmic Afro", {"style": "afro", "c1": "#8a3ad8", "c2": "#ffd84a"})
    add("hair", "rare", "Bubblegum Twintails", {"style": "twintails", "c1": "#ff7ac8", "c2": "#ffffff"})
    add("hair", "rare", "Ice Spikes", {"style": "spiky", "c1": "#4ad2ff", "c2": "#ffffff"})
    add("hair", "rare", "Royal Bun", {"style": "bun", "c1": "#2b2b6b", "c2": "#ffd84a"})
    add("hair", "legendary", "Rainbow Wave", {"style": "long", "c1": "#ff4f6d", "rainbow": True})

    # ---- shirts
    for colour_name, colour in PALETTE:
        add("shirt", "common", f"{colour_name} Tee", {"style": "solid", "c1": colour})
    add("shirt", "rare", "Racer Stripes", {"style": "hstripe", "c1": "#d83a3a", "c2": "#ffffff"})
    add("shirt", "rare", "Pinstripe Pro", {"style": "vstripe", "c1": "#23346b", "c2": "#dfe6ff"})
    add("shirt", "rare", "Checker Champ", {"style": "check", "c1": "#26262e", "c2": "#f2d03b"})
    add("shirt", "rare", "Star Player", {"style": "emblem", "c1": "#2f6fe0", "c2": "#ffd84a"})
    add("shirt", "rare", "Midnight Hoodie", {"style": "hoodie", "c1": "#3b2a6b", "c2": "#3ad6d9"})
    add("shirt", "legendary", "Golden Champion", {"style": "gold", "c1": "#ffd84a", "c2": "#fff6c4"})

    # ---- name tags
    for colour_name, colour in PALETTE:
        add("name", "common", f"{colour_name} Tag", {"bg": colour, "fx": None})
    add("name", "rare", "Neon Glow", {"bg": "#16122b", "fg": "#7dfcff", "border": "#3ad6d9", "fx": "glow"})
    add("name", "rare", "Gold Plate", {"bg": "#ffd84a", "fg": "#5a3a00", "border": "#a8780f", "fx": "gold"})
    add("name", "rare", "Starry Night", {"bg": "#1b2a6b", "fg": "#ffffff", "border": "#0d1433", "fx": "stars"})
    add("name", "rare", "Heartbeat", {"bg": "#ffd9ea", "fg": "#c2185b", "border": "#c2185b", "fx": "hearts"})
    add("name", "rare", "Thunder", {"bg": "#26262e", "fg": "#ffe94a", "border": "#ffe94a", "fx": "bolt"})
    add("name", "legendary", "Inferno", {"bg": "#3a0d0d", "fg": "#ffe94a", "border": "#ff7a1a", "fx": "fire"})
    return items


ITEMS: list[dict] = _build()
_BY_ID = {item["id"]: item for item in ITEMS}


def get(item_id: str) -> dict | None:
    return _BY_ID.get(item_id)


def by_slot(slot: str, rarity: str | None = None) -> list[dict]:
    return [i for i in ITEMS if i["slot"] == slot and (rarity is None or i["rarity"] == rarity)]


def spec_for(slot: str, item_id: str | None) -> dict:
    """The drawing recipe for an item, or the default look when nothing is equipped."""
    item = _BY_ID.get(item_id) if item_id else None
    if item is None or item["slot"] != slot:
        return DEFAULTS[slot]
    return item["spec"]
