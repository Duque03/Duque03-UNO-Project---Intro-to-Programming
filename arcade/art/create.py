"""The "Create your player" picture: the character on the left, the choices on the right (logic/looks.py)."""

from __future__ import annotations

from PIL import Image, ImageDraw

from arcade.art import sprites
from arcade.art.pixel import draw_text, panel, rgb
from arcade.config import SCREEN_H, SCREEN_W
from arcade.logic import looks

ROW_Y = [132, 226, 312, 398]  # the top of each row of choices
LABELS = {"hair": "HAIR", "hair_colour": "HAIR COLOUR", "shirt": "T-SHIRT", "skin": "SKIN"}
DONE_BOX = (560, 474, 860, 524)
GOLD, INK = "#ffe94a", "#16122b"


def _look(choice: dict) -> tuple:
    return (looks.SKINS[choice["skin"]], "#2b3a67", looks.hair_id(choice), looks.shirt_id(choice))


def creator_picture(name: str, choice: dict, focus_row: int | None, t: int = 0):
    """Returns (picture, clickable regions). focus_row: the row the arrow keys are on (5 = DONE), shown only while the
    player uses the keys (None hides it)."""
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), rgb("#1c1642"))
    d = ImageDraw.Draw(img)
    for y in range(0, SCREEN_H, 6):  # a soft glow from the top
        d.rectangle([0, y, SCREEN_W, y + 5], fill=tuple(round(c * (1 - y / SCREEN_H * 0.45)) for c in (44, 34, 96)))
    draw_text(img, (SCREEN_W // 2, 34), "CREATE YOUR PLAYER", 4, GOLD, "mt", shadow=INK)
    regions = []

    # the character, under a spotlight, with their name
    d.ellipse([70, 110, 390, 500], fill=(52, 42, 112))
    d.ellipse([110, 440, 350, 486], fill=(30, 24, 70))
    body = sprites.sprite(*_look(choice), "down", 0, t)
    body = body.resize((body.width * 9, body.height * 9), Image.NEAREST)
    img.paste(body, (230 - body.width // 2, 468 - body.height), body)
    sprites.draw_name_tag(img, 230, 200, name)

    # the choices
    for row, ((key, options), y) in enumerate(zip(looks.ROWS, ROW_Y)):
        if focus_row == row:
            draw_text(img, (430, y + 10), ">", 3, GOLD, "lm", shadow=INK)
        draw_text(img, (456, y - 24), LABELS[key], 2, "#d9d4ff", "lt", shadow=INK)
        x = 456
        for option, colour in options.items():
            chosen = choice[key] == option
            if key == "hair":  # a head with that hair, in the chosen colour
                box = (x, y, x + 96, y + 60)
                panel(img, box, "#2c2466", "#ffffff" if chosen else "#4a3f8f", bw=4)
                head = sprites.head_icon(_look(dict(choice, hair=option)), scale=3)
                img.paste(head, (x + 8, y + 6), head)
                draw_text(img, (x + 76, y + 30), option.upper(), 1, "#ffffff", "mm")
                x += 112
            else:
                size = 40
                box = (x, y + 6, x + size, y + 6 + size)
                d.rectangle([box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4],
                            fill=(255, 255, 255) if chosen else (40, 32, 90))
                d.rectangle(box, fill=rgb(colour))
                x += size + 10
            regions.append((box, ("set", key, option)))

    # done
    if focus_row == len(looks.ROWS):
        d.rectangle([DONE_BOX[0] - 6, DONE_BOX[1] - 6, DONE_BOX[2] + 6, DONE_BOX[3] + 6], outline=rgb(GOLD), width=4)
    panel(img, DONE_BOX, "#2f9e57", "#ffffff", bw=4)
    draw_text(img, ((DONE_BOX[0] + DONE_BOX[2]) // 2, (DONE_BOX[1] + DONE_BOX[3]) // 2), "LET'S PLAY!", 3, "#ffffff",
              "mm", shadow=INK)
    regions.append((DONE_BOX, ("done",)))
    return img, regions
