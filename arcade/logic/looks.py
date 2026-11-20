"""The look a player picks when they create their account (docs/game-design.md, "Create your player").

It is the base look: what they wear when no store item is equipped. Store hair and shirts still go on top of it
(and taking one off brings the base look back). The choices are a short, fixed list, so a saved value can always be
checked against it.
"""

from __future__ import annotations

HAIR_STYLES = {"boy": "short", "girl": "long"}  # the choice -> the hair style drawn (arcade/art/sprites.py)
HAIR_COLOURS = {"black": "#1d1a22", "ginger": "#c8551e", "brown": "#5a3a22", "blond": "#f0d264"}
SHIRT_COLOURS = {
    "white": "#e9e9ee", "black": "#26262e", "red": "#d83a3a", "orange": "#f08a24", "yellow": "#f2c230",
    "green": "#2a8a3a", "blue": "#2f6fe0", "purple": "#7a3ad8", "pink": "#ff8ac4",
}
SKINS = {"light": "#f6d5b8", "fair": "#f2c9a0", "tan": "#d9a066", "olive": "#b07a4a", "brown": "#8a5a34",
         "dark": "#5e3a22"}
ROWS = [("hair", HAIR_STYLES), ("hair_colour", HAIR_COLOURS), ("shirt", SHIRT_COLOURS), ("skin", SKINS)]

DEFAULT = {"hair": "boy", "hair_colour": "brown", "shirt": "white", "skin": "fair"}


class InvalidLook(ValueError):
    """A choice that is not in the lists above."""


def check(choice: dict) -> dict:
    """The choice with every part checked against the lists (raises InvalidLook)."""
    clean = {}
    for row, options in ROWS:
        value = choice.get(row)
        if value not in options:
            raise InvalidLook(f"Pick a {row.replace('_', ' ')} from the list.")
        clean[row] = value
    return clean


def apply(player: dict, choice: dict) -> None:
    """Save the chosen base look on the player (and mark that they have created their player)."""
    choice = check(choice)
    player["base"] = choice
    player["skin"] = SKINS[choice["skin"]]
    player["look_done"] = True


def step(choice: dict, row: int, delta: int) -> dict:
    """The choice with one row moved to the previous (-1) or next (+1) option, going round at the ends."""
    name, options = ROWS[row]
    keys = list(options)
    current = keys.index(choice[name]) if choice.get(name) in options else 0
    return dict(choice, **{name: keys[(current + delta) % len(keys)]})


def hair_id(base: dict) -> str:
    """The base hair as an item id that catalog.spec_for understands: "base:hair:<style>:<colour>"."""
    base = {**DEFAULT, **(base or {})}
    style = HAIR_STYLES.get(base["hair"], "short")
    return f"base:hair:{style}:{HAIR_COLOURS.get(base['hair_colour'], HAIR_COLOURS['brown'])}"


def shirt_id(base: dict) -> str:
    """The base T-shirt as an item id that catalog.spec_for understands: "base:shirt:<colour>"."""
    base = {**DEFAULT, **(base or {})}
    return f"base:shirt:{SHIRT_COLOURS.get(base['shirt'], SHIRT_COLOURS['white'])}"


def spec(item_id: str) -> tuple[str, dict] | None:
    """(slot, drawing recipe) for a base id, or None if it is not a valid one (only listed values are accepted)."""
    parts = item_id.split(":")
    if parts[:2] == ["base", "hair"] and len(parts) == 4:
        style, colour = parts[2], parts[3]
        if style in HAIR_STYLES.values() and colour in HAIR_COLOURS.values():
            return "hair", {"style": style, "c1": colour}
    if parts[:2] == ["base", "shirt"] and len(parts) == 3 and parts[2] in SHIRT_COLOURS.values():
        return "shirt", {"style": "solid", "c1": parts[2]}
    return None
