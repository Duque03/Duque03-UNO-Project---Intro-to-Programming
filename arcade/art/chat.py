"""Pictures for the online room: our own pixel emojis, the speech bubbles of the chat, the sign on each table that
counts who is sitting (1/4, 2/4...) and the lobby's name plate. Plain data in, Pillow pictures out.

The emojis are drawn on a 13x13 grid, one letter per pixel (the key is PALETTE), and blown up like everything else.
"""

from __future__ import annotations

from functools import lru_cache

from PIL import Image, ImageDraw

from arcade.art.pixel import draw_text, panel, text_size, wrap

INK = "#16122b"
PALETTE = {"k": INK, "y": "#ffd23f", "o": "#e8a020", "w": "#ffffff", "r": "#e2413c", "p": "#ff8fb0",
           "b": "#3ad6ff", "a": "#ff7a4a", "G": "#ffcf3a", "g": "#2fbf71"}
SIZE = 13

_FACE_TOP = ["....kkkkk....", "..kkyyyyykk..", ".kyyyyyyyyyk."]
_FACE_BOTTOM = [".kyyyyyyyyyk.", "..kkyyyyykk..", "....kkkkk...."]
_PLAIN = "kyyyyyyyyyyyk"
_EYES = [".kyykyyykyyk.", "kyyykyyykyyyk"]
_SMILE = ["kyykyyyyykyyk", "kyyykkkkkyyyk"]

EMOJI_ART = {
    "smile": _FACE_TOP + _EYES + [_PLAIN, _PLAIN] + _SMILE + _FACE_BOTTOM[:1] + [".kyyyyyyyyyk."] + _FACE_BOTTOM[1:],
    "laugh": _FACE_TOP + [".kyykyyykyyk.", "kyykykykykyyk", "kbyyyyyyyyybk", "kbyyyyyyyyybk", "kyykkkkkkkyyk",
                          "kyykrrrrrkyyk", ".kyykpppkyyk.", ".kyyykkkyyyk."] + _FACE_BOTTOM[1:],
    "wink": _FACE_TOP + [".kyyyyyykyyk.", "kyykkkyykyyyk", _PLAIN, _PLAIN] + _SMILE
            + [".kyyyyyyyyyk.", ".kyyyyyyyyyk."] + _FACE_BOTTOM[1:],
    "cool": _FACE_TOP[:2] + [".kyyyyyyyyyk.", ".kkkkkkkkkkk.", "kykwkkykwkkyk", "kykkkkykkkkyk", _PLAIN,
                             "k" + "y" * 9 + "kyk", "kyyyyyykkkyyk", ".kyyyyyyyyyk.", ".kyyyyyyyyyk."]
            + _FACE_BOTTOM[1:],
    "love": _FACE_TOP + [".kyryryryryk.", "kyyrrryrrryyk", "kyyyryyyryyyk", _PLAIN] + _SMILE
            + [".kyyyyyyyyyk.", ".kyyyyyyyyyk."] + _FACE_BOTTOM[1:],
    "wow": _FACE_TOP + _EYES + [_PLAIN, _PLAIN, "kyyyyykyyyyyk", "kyyyykrkyyyyk", ".kyyyykyyyyk.", ".kyyyyyyyyyk."]
           + _FACE_BOTTOM[1:],
    "sad": _FACE_TOP + _EYES + ["kyyyyyyybyyyk", "kyyyyyyybyyyk", "kyyykkkkkyyyk", ".kykyyyyykyk.",
                                ".kyyyyyyyyyk.", ".kyyyyyyyyyk."] + _FACE_BOTTOM[1:],
    "angry": [r.replace("y", "a") for r in _FACE_TOP] + [".kakaaaaakak.", "kaaakaaakaaak", "kaaakaaakaaak",
                                                         "kaaaaaaaaaaak", "kaaakkkkkaaak", ".kakaaaaakak.",
                                                         ".kaaaaaaaaak.", ".kaaaaaaaaak."]
             + [r.replace("y", "a") for r in _FACE_BOTTOM[1:]],
    "heart": [".............", "..kkk...kkk..", ".krrrk.krrrk.", "krwrrrkrrrrrk", "krwrrrrrrrrrk", "krrrrrrrrrrrk",
              ".krrrrrrrrrk.", "..krrrrrrrk..", "...krrrrrk...", "....krrrk....", ".....krk.....", "......k......",
              "............."],
    "thumbs": [".....kk......", "....kyyk.....", "....kyyk.....", "...kyyyk.....", "..kyyyykkkkk.", "kkkyyyyyyyyyk",
               "kbkyyyyykkkk.", "kbkyyyyyyyyyk", "kbkyyyyykkkk.", "kbkyyyyyyyyk.", "kbkyyyyykkk..", "kkkkkkkkk....",
               "............."],
    "trophy": [".............", ".kkkkkkkkkkk.", "kGkGGwGGGokGk", "kGkGGwGGGokGk", ".kkGGGGGGokk.", "...kGGGGok...",
               "....kGGok....", ".....kGk.....", ".....kGk.....", "....kGGok....", "...kkkkkkk...", "...kGGGGGk...",
               "...kkkkkkk..."],
    "gg": [".............", ".............", ".kkkkkkkkkkk.", "kgggggggggggk", "kgwwwggwwwggk", "kgwggggwggggk",
           "kgwgwggwgwggk", "kgwgwggwgwggk", "kgwwwggwwwggk", "kgggggggggggk", ".kkkkkkkkkkk.", ".............",
           "............."],
}


def emoji(name: str, scale: int = 3) -> Image.Image:
    """One emoji, see-through around it, each grid pixel scale x scale."""
    rows = EMOJI_ART[name]
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in PALETTE:
                img.putpixel((x, y), Image.new("RGB", (1, 1), PALETTE[ch]).getpixel((0, 0)) + (255,))
    return img.resize((SIZE * scale, SIZE * scale), Image.NEAREST)


def _bubble(width: int, height: int, mine: bool) -> tuple[Image.Image, int]:
    """An empty speech bubble with its tail at the bottom middle. Returns (picture, middle x)."""
    img = Image.new("RGBA", (width + 6, height + 16), (0, 0, 0, 0))
    fill = "#bfe6ff" if mine else "#fff6da"
    panel(img, (0, 0, width - 1, height - 1), fill, INK, bw=3, shadow=False)
    d = ImageDraw.Draw(img)
    mid = width // 2
    for row, half in enumerate((7, 5, 3, 1)):  # the tail, in pixel steps
        y = height - 3 + row * 3
        d.rectangle([mid - half - 3, y, mid + half + 2, y + 2], fill=INK)
        if half > 1:
            d.rectangle([mid - half, y, mid + half - 1, y + 2], fill=fill)
    return img, mid


@lru_cache(maxsize=256)
def said(text: str | None, emoji_name: str | None, mine: bool) -> Image.Image:
    """What a player said, in a speech bubble above their head: their own light blue, the others' cream."""
    if emoji_name:
        face = emoji(emoji_name, 3)
        img, mid = _bubble(face.width + 20, face.height + 14, mine)
        img.alpha_composite(face, (mid - face.width // 2, 7))
        return img
    lines = wrap((text or "").upper(), 20)[:2]
    width = max(text_size(line, 2)[0] for line in lines) + 24
    img, mid = _bubble(width, 20 * len(lines) + 16, mine)
    for i, line in enumerate(lines):
        draw_text(img, (mid, 10 + i * 20), line, 2, INK, "mt")
    return img


@lru_cache(maxsize=128)
def table_sign(seated: int, chairs: int, note: str = "", busy: bool = False) -> Image.Image:
    """The sign on a table: a little square per chair (lit when someone sits there), the count (2/4), and under it
    how long UNO still waits or that a game is on."""
    edge = "#ff8a8a" if busy else ("#ffe94a" if note else "#3ad6ff")
    count = f"{seated}/{chairs}"
    cw = text_size(count, 3)[0]
    nw = text_size(note, 2)[0] if note else 0
    squares = chairs * 14 - 4
    width = max(cw + squares + 34, nw + 24)
    height = 44 + (24 if note else 0)
    img = Image.new("RGBA", (width + 4, height + 4), (0, 0, 0, 0))
    panel(img, (0, 0, width - 1, height - 1), INK, edge, bw=3, shadow=True)
    d = ImageDraw.Draw(img)
    x = 12
    for k in range(chairs):
        box = [x, 16, x + 9, 25]
        if k < seated:
            d.rectangle(box, fill="#ffe94a", outline="#ffe94a")
        else:
            d.rectangle(box, outline="#8d8fa3", width=2)
        x += 14
    draw_text(img, (x + 6, 11), count, 3, "#ffffff", "lt")
    if note:
        draw_text(img, (width // 2, 44), note, 2, edge, "mt")
    return img


@lru_cache(maxsize=32)
def lobby_plate(code: str, players: int, most: int) -> Image.Image:
    """The lobby's name plate (bottom right): its code, to give to friends, and how many are in."""
    top, bottom = f"LOBBY {code}", f"{players}/{most} PLAYERS"
    width = max(text_size(top, 3)[0], text_size(bottom, 2)[0]) + 28
    img = Image.new("RGBA", (width + 4, 62), (0, 0, 0, 0))
    panel(img, (0, 0, width - 1, 57), INK, "#3ad6ff", bw=3, shadow=True)
    draw_text(img, (width // 2, 9), top, 3, "#ffe94a", "mt")
    draw_text(img, (width // 2, 36), bottom, 2, "#f3ead2", "mt")
    return img


@lru_cache(maxsize=2)
def chair_mat(taken: bool) -> Image.Image:
    """A little round mat on the floor where each chair of a table is: yellow when someone sits there, a dim ring
    when it is free (so you can see where to go and who is waiting). Drawn small and blown up 3x."""
    w, h = 26, 10
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if taken:
        d.ellipse([0, 0, w - 1, h - 1], fill=(255, 233, 74, 110), outline=(255, 233, 74, 255))
    else:
        d.ellipse([0, 0, w - 1, h - 1], outline=(58, 214, 255, 170))
    return img.resize((w * 3, h * 3), Image.NEAREST)


@lru_cache(maxsize=1)
def send_icon() -> Image.Image:
    """A small arrow for the chat bar's send button."""
    rows = ["k.......", "kk......", "kwk.....", "kwwk....", "kwwwk...", "kwwwwk..", "kwwwk...", "kwwk....",
            "kwk.....", "kk......", "k......."]
    img = Image.new("RGBA", (8, len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "w":
                img.putpixel((x, y), (255, 233, 74, 255))
            elif ch == "k":
                img.putpixel((x, y), (22, 18, 43, 255))
    return img.resize((24, len(rows) * 3), Image.NEAREST)
