"""The Corta UNO face-off, drawn over the table (see arcade/logic/trivia.py for the rules)."""

from __future__ import annotations

from PIL import Image, ImageDraw

from arcade.art import sprites
from arcade.art.pixel import draw_text, panel, rgb, wrap

BOX = (100, 56, 860, 484)
YES_BOX, NO_BOX = (282, 392, 462, 452), (498, 392, 678, 452)
GOOD, BAD, GOLD = "#5fe08a", "#ff4f6d", "#ffe94a"


def _player(img, cx, name, look, role, status, status_colour):
    """One side of the face-off: their head, name, role and how they are doing."""
    head = sprites.head_icon(look, scale=4)
    img.paste(head, (cx - head.width // 2, 158), head)
    draw_text(img, (cx, 238), name, 3, "#ffffff", "mt", shadow="#16122b")
    draw_text(img, (cx, 264), role, 1, "#d9d4ff", "mt")
    draw_text(img, (cx, 280), status, 2, status_colour, "mt", shadow="#16122b")


def duel_picture(table, view: dict):
    """The face-off box over a darkened table. Returns (picture, clickable regions).

    view: holder and cutter (names), looks {name: look}, me (the player looking at it, or None to only watch),
    round (0 for the first question), question, phase ("ask", "reveal" or "done"), answered {name: True once they
    answered}, answers {name: yes?} and right {name: right?} (shown in "reveal"), truth, result (None, "holder" or
    "cutter"), focus (0 YES, 1 NO: the yellow frame while the player chooses).
    """
    img = Image.blend(table.convert("RGB"), Image.new("RGB", table.size, (8, 6, 20)), 0.62)
    panel(img, BOX, "#16122b", GOLD, bw=6)
    d = ImageDraw.Draw(img)
    regions = []
    draw_text(img, (480, 82), "CORTA UNO!", 5, BAD, "mt", shadow="#3b0f1d")
    draw_text(img, (480, 128), f"TRIVIA FACE-OFF  -  QUESTION {view['round'] + 1}", 2, GOLD, "mt")
    reveal = view["phase"] in ("reveal", "done")
    for cx, name, role in ((250, view["holder"], "HAS UNO"), (710, view["cutter"], "CUT IT")):
        if reveal:
            said = view["answers"].get(name)
            status = "NO ANSWER" if said is None else ("YES" if said else "NO")
            right = view["right"].get(name, False)
            status, colour = f"{status}: {'RIGHT' if right else 'WRONG'}", GOOD if right else BAD
        elif view["answered"].get(name):
            status, colour = "ANSWERED", GOOD
        else:
            status, colour = "THINKING...", "#d9d4ff"
        label = "YOU" if name == view.get("me") else name
        _player(img, cx, label, view["looks"][name], role, status, colour)
    draw_text(img, (480, 200), "VS", 4, GOLD, "mt", shadow="#16122b")
    lines = wrap(view["question"].upper(), 34)
    y = 318 - 12 * (len(lines) - 1)
    for line in lines:
        draw_text(img, (480, y), line, 3, "#ffffff", "mt", shadow="#3b3560")
        y += 30
    me = view.get("me")
    if view["phase"] == "ask" and me in (view["holder"], view["cutter"]) and not view["answered"].get(me):
        for i, (box, word, colour) in enumerate(((YES_BOX, "YES", "#2f9e57"), (NO_BOX, "NO", "#c43a4f"))):
            if view.get("focus") == i:
                d.rectangle([box[0] - 6, box[1] - 6, box[2] + 6, box[3] + 6], outline=rgb(GOLD), width=4)
            panel(img, box, colour, "#ffffff", bw=4)
            draw_text(img, ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2), word, 4, "#ffffff", "mm",
                      shadow="#16122b")
            regions.append((box, ("yes",) if word == "YES" else ("no",)))
    elif view["phase"] == "ask":
        mine = view["answers"].get(me)
        line = "WAITING FOR THE ANSWERS..." if mine is None else f"YOU SAID {'YES' if mine else 'NO'}. WAITING..."
        draw_text(img, (480, 412), line, 2, "#d9d4ff", "mt")
    else:
        draw_text(img, (480, 396), f"THE ANSWER IS {'YES' if view['truth'] else 'NO'}", 3, GOLD, "mt",
                  shadow="#16122b")
        draw_text(img, (480, 436), outcome_line(view), 2, "#ffffff", "mt", shadow="#16122b")
    return img, regions


def outcome_line(view: dict) -> str:
    """What the last question decided, in words."""
    holder, me = view["holder"], view.get("me")
    holder_name = "YOU" if holder == me else holder
    if view["result"] == "holder":
        return f"{holder_name} {'DRAW' if holder == me else 'DRAWS'} 7 CARDS!"
    if view["result"] == "cutter":
        return f"{'YOUR' if holder == me else holder + chr(39) + 'S'} UNO STANDS!"
    both = "BOTH RIGHT" if view["right"].get(holder) else "BOTH WRONG"
    return f"{both}! ANOTHER QUESTION..."
