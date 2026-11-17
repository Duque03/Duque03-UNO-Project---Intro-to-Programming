"""The five regulars of the arcade. Each bot has its own name and look."""

from __future__ import annotations

# "home" is where the bot hangs out in the arcade (base-canvas coordinates of its feet).
BOTS = [
    {"name": "PIXEL", "skin": "#f2c9a0", "pants": "#2b3a67", "hair": "hair_c04", "shirt": "shirt_c04",
     "tag": "name_c03", "home": (88, 72), "dir": "up"},
    {"name": "TURBO", "skin": "#c98d5f", "pants": "#3a3a44", "hair": "hair_r01", "shirt": "shirt_c01",
     "tag": "name_c01", "home": (120, 72), "dir": "up"},
    {"name": "GLITCH", "skin": "#e9c9f2", "pants": "#1d1a22", "hair": "hair_r03", "shirt": "shirt_r03",
     "tag": "name_r03", "home": (152, 72), "dir": "up"},
    {"name": "JOY", "skin": "#8f5a3a", "pants": "#6b2b4a", "hair": "hair_c08", "shirt": "shirt_c06",
     "tag": "name_r01", "home": (24, 112), "dir": "left"},
    {"name": "BYTE", "skin": "#f2d9b8", "pants": "#2a5a3a", "hair": "hair_c06", "shirt": "shirt_c09",
     "tag": "name_r02", "home": (296, 116), "dir": "right"},
]

SHOPKEEPER = {"name": "SHOP", "skin": "#e0b088", "pants": "#3a3a44", "hair": "hair_r02", "shirt": "shirt_r01"}

BOT_NAMES = [b["name"] for b in BOTS]
_BY_NAME = {b["name"]: b for b in BOTS}


def get(name: str) -> dict:
    return _BY_NAME[name]


def look(bot: dict) -> tuple:
    """(skin, pants, hair item id, shirt item id) - the shape the sprite code wants."""
    return (bot["skin"], bot["pants"], bot["hair"], bot["shirt"])
