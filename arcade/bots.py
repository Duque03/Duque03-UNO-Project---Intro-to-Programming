"""The four regulars of the arcade, one per level. Each has its own name, look and level (how well it plays).

They are listed from the easiest to the hardest, which is also the order of the cards when you choose an
opponent (left to right). All four are our own designs.
"""

from __future__ import annotations

# "home" is where the bot hangs out in the arcade (base-canvas coordinates of its feet).
BOTS = [
    {"name": "DEAN", "level": "easy", "skin": "#e8c4a0", "pants": "#2e3140", "hair": "bot_dean_hair",
     "shirt": "bot_dean_suit", "tag": "name_c03", "home": (88, 72), "dir": "up"},        # a university dean
    {"name": "BARK", "level": "medium", "skin": "#c98b4a", "pants": "#c98b4a", "hair": "bot_dog",
     "shirt": "bot_dog_bandana", "tag": "name_r02", "home": (24, 112), "dir": "left"},   # a dog
    {"name": "MANHOSA", "level": "hard", "skin": "#6b4428", "pants": "#1c2238", "hair": "bot_guard_cap",
     "shirt": "bot_guard_uniform", "tag": "name_r03", "home": (296, 116), "dir": "right"},  # a security officer
    {"name": "JOHN", "level": "expert", "skin": "#f0c8a4", "pants": "#3b5b8f", "hair": "bot_john_hair",
     "shirt": "bot_john_tee", "tag": None, "home": (152, 72), "dir": "up"},  # the most ordinary guy there is
]

SHOPKEEPER = {"name": "SHOP", "skin": "#e0b088", "pants": "#3a3a44", "hair": "hair_r02", "shirt": "shirt_r01"}

BOT_NAMES = [b["name"] for b in BOTS]
_BY_NAME = {b["name"]: b for b in BOTS}


def get(name: str) -> dict:
    return _BY_NAME[name]


def level(name: str) -> str:
    """easy, medium, hard or expert (how well this bot plays, and how many coins beating it pays)."""
    return _BY_NAME[name]["level"]


def look(bot: dict) -> tuple:
    """(skin, pants, hair item id, shirt item id) - the shape the sprite code wants."""
    return (bot["skin"], bot["pants"], bot["hair"], bot["shirt"])
