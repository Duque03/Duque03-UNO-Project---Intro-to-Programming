"""Pictures of the online screens: the online menu, the join screen (type a code) and the lobby.

Everything to choose is drawn on the picture, like the title screen and the pause menu: the arrow keys move a yellow
highlight and a click does the same as Enter. Each picture function returns (picture, regions).
"""

from __future__ import annotations

from functools import lru_cache

from PIL import Image, ImageDraw

from arcade.art import sprites, title_layers
from arcade.art.pixel import darken, draw_text, panel, rgb, upscale, wrap
from arcade.art.scenes import FOCUS, draw_button
from arcade.config import SCREEN_H, SCREEN_W

GAME_LABELS = {"uno": "UNO", "checkers": "CHECKERS", "connect4": "CONNECT FOUR"}
GAME_SIZES_TEXT = {"uno": "2 TO 4 PLAYERS", "checkers": "2 PLAYERS", "connect4": "2 PLAYERS"}
GAMES = list(GAME_LABELS)
SEAT_W = 190
PAD_COLUMNS, PAD_KEY, PAD_GAP = 5, (70, 44), 10  # the on-screen keyboard of the join screen
PAD_ACTIONS = ["DEL", "JOIN", "BACK"]


@lru_cache(maxsize=1)
def _background() -> Image.Image:
    img = title_layers.backdrop()
    if img.width != SCREEN_W:
        img = upscale(img)
    return darken(img.convert("RGB"), 0.45)


def _frame(title: str) -> Image.Image:
    img = _background().copy()
    panel(img, (40, 24, SCREEN_W - 40, SCREEN_H - 24), "#0f0b2a", "#3ad6ff", bw=4)
    draw_text(img, (SCREEN_W // 2, 46), title, 5, "#ffe94a", "mt", shadow="#16122b")
    return img


def _crown(d, x, y, u=3):
    rows = ["#..#..#", "#######", "#.###.#", "#######"]
    for r, row in enumerate(rows):
        for k, c in enumerate(row):
            if c == "#":
                d.rectangle([x + k * u, y + r * u, x + (k + 1) * u - 1, y + (r + 1) * u - 1],
                            fill=rgb("#fff6c4" if r == 0 else "#ffc23a"))


def _message(img, message: str, y: int, good: bool = False) -> None:
    for i, line in enumerate(wrap(message.upper(), 48)):
        draw_text(img, (SCREEN_W // 2, y + i * 22), line, 2, "#7cff3a" if good else "#ff8a8a", "mt", shadow="#16122b")


# ---------------------------------------------------------------- the online menu

def menu_picture(me: dict, options: list[dict], focus: int, message: str = ""):
    """PLAY ONLINE: you, ready to play, and the menu (options: label, action, key). Returns (picture, regions)."""
    img = _frame("PLAY ONLINE")
    draw_text(img, (SCREEN_W // 2, 104), "PLAY WITH FRIENDS ON THEIR OWN PHONES OR LAPTOPS", 2, "#d9d4ff", "mt")
    draw_text(img, (SCREEN_W // 2, 128), "UP TO 4 PLAYERS - NO BOTS", 2, "#7cff3a", "mt")
    d = ImageDraw.Draw(img)
    d.ellipse([140, 418, 300, 446], fill=rgb("#2a2266"))
    sprites.draw_character(img, 220, 440, me["look"], "down", 0, 0, scale=6)
    sprites.draw_name_tag(img, 220, 262, me["name"], me.get("tag"))
    regions = []
    for i, option in enumerate(options):
        y = 172 + i * 70
        box = draw_button(img, (400, y, 860, y + 54), option["label"], 3, fill=FOCUS if i == focus else "#ffffff",
                          key=option.get("key"))
        regions.append((box, ("menu", option["action"])))
    if message:
        _message(img, message, 456)
    else:
        draw_text(img, (630, 466), "ARROWS: CHOOSE  -  ENTER: OK", 2, "#b9b0e8", "mt")
    return img, regions


# ---------------------------------------------------------------- the join screen

def pad_keys(letters: str) -> list[str]:
    """The keys of the on-screen keyboard, in the order the highlight counts them."""
    return list(letters) + PAD_ACTIONS


def join_picture(code: str, letters: str, focus: int, message: str = ""):
    """JOIN A LOBBY: four boxes for the code, like an arcade's high-score letters, and an on-screen keyboard.

    Returns (picture, regions); a region's action is ("key", "A") for a letter, or ("key", "DEL" / "JOIN" / "BACK").
    """
    img = _frame("JOIN A LOBBY")
    d = ImageDraw.Draw(img)
    draw_text(img, (SCREEN_W // 2, 100), "TYPE YOUR FRIEND'S CODE, OR PICK THE LETTERS WITH THE ARROWS", 2,
              "#d9d4ff", "mt")
    for i in range(4):  # the code so far
        x = SCREEN_W // 2 - 2 * 76 + i * 76
        here = i == len(code)
        d.rectangle([x + 4, 128, x + 68, 196], fill=rgb("#1b1546"), outline=rgb(FOCUS if here else "#3a2f6b"),
                    width=4 if here else 3)
        if i < len(code):
            draw_text(img, (x + 36, 164), code[i], 6, "#ffffff", "mm", shadow="#3a2f6b")
        elif here:
            d.rectangle([x + 20, 182, x + 52, 186], fill=rgb(FOCUS))
    if message:
        _message(img, message, 204)
    regions = []
    width = PAD_COLUMNS * PAD_KEY[0] + (PAD_COLUMNS - 1) * PAD_GAP
    left, top = (SCREEN_W - width) // 2, 222
    for i, label in enumerate(letters):
        row, col = divmod(i, PAD_COLUMNS)
        x, y = left + col * (PAD_KEY[0] + PAD_GAP), top + row * (PAD_KEY[1] + PAD_GAP)
        box = draw_button(img, (x, y, x + PAD_KEY[0], y + PAD_KEY[1]), label, 3,
                          fill=FOCUS if i == focus else "#ffffff")
        regions.append((box, ("key", label)))
    rows = -(-len(letters) // PAD_COLUMNS)
    y = top + rows * (PAD_KEY[1] + PAD_GAP) + 2
    third = (width - 2 * PAD_GAP) // 3
    for k, label in enumerate(PAD_ACTIONS):
        x = left + k * (third + PAD_GAP)
        index = len(letters) + k
        fill = FOCUS if index == focus else ("#7cff3a" if label == "JOIN" and len(code) == 4 else "#ffffff")
        box = draw_button(img, (x, y, x + third, y + PAD_KEY[1]), label, 3, fill=fill)
        regions.append((box, ("key", label)))
    draw_text(img, (SCREEN_W // 2, y + 50), "BACKSPACE: DELETE  -  ENTER: OK  -  ESC: BACK", 2, "#b9b0e8", "mt")
    return img, regions


# ---------------------------------------------------------------- the lobby

def lobby_picture(lobby, me: str, message: str = "", good: bool = False):
    """The lobby: its code, the seats (up to 4), the games to pick from and whether it can start.

    Returns (picture, regions); the host's regions are ("game", key) for each game.
    """
    img = _background().copy()
    d = ImageDraw.Draw(img)
    panel(img, (40, 24, SCREEN_W - 40, SCREEN_H - 24), "#0f0b2a", "#3ad6ff", bw=4)
    draw_text(img, (70, 46), "LOBBY", 4, "#ffe94a", "lt", shadow="#16122b")
    draw_text(img, (SCREEN_W - 70, 40), "CODE", 2, "#b9b0e8", "rt")
    draw_text(img, (SCREEN_W - 70, 60), lobby.code, 6, "#ffffff", "rt", shadow="#3a2f6b")
    draw_text(img, (SCREEN_W // 2, 104), "GIVE YOUR FRIENDS THE CODE TO JOIN", 2, "#d9d4ff", "mt")

    left = (SCREEN_W - 4 * SEAT_W) // 2
    for i in range(4):
        x0 = left + i * SEAT_W
        cx = x0 + SEAT_W // 2
        filled = i < len(lobby.players)
        d.rectangle([x0 + 10, 130, x0 + SEAT_W - 10, 330], fill=rgb("#1b1546" if filled else "#140f33"),
                    outline=rgb("#ffe94a" if filled and lobby.players[i]["name"] == me else "#3a2f6b"), width=3)
        if not filled:
            draw_text(img, (cx, 230), "WAITING...", 2, "#5a4f8f", "mm")
            continue
        player = lobby.players[i]
        d.ellipse([cx - 46, 302, cx + 46, 320], fill=rgb("#2a2266"))
        sprites.draw_character(img, cx, 314, player["look"], "down", 0, 0, scale=5)
        sprites.draw_name_tag(img, cx, 166, player["name"], player.get("tag"))
        if player["name"] == lobby.host:
            _crown(d, cx - 10, 136)
            draw_text(img, (cx, 336), "HOST", 2, "#ffc23a", "mt")
        elif player["name"] == me:
            draw_text(img, (cx, 336), "YOU", 2, "#ffe94a", "mt")

    host = lobby.host == me
    regions = []
    width, gap = 250, 20
    x = (SCREEN_W - (3 * width + 2 * gap)) // 2
    for game in GAMES:
        chosen = lobby.game == game
        fill = FOCUS if chosen else ("#ffffff" if host else "#8d8aa6")
        box = draw_button(img, (x, 388, x + width, 440), GAME_LABELS[game], 3, fill=fill)
        draw_text(img, (x + width // 2, 446), GAME_SIZES_TEXT[game], 1, "#d9d4ff", "mt")
        if host:
            regions.append((box, ("game", game)))
        x += width + gap
    if message:
        _message(img, message, 362, good)
    leave = draw_button(img, (70, 470, 250, 508), "LEAVE", 2)
    regions.append((leave, ("leave",)))
    if host:
        start = draw_button(img, (SCREEN_W - 250, 470, SCREEN_W - 70, 508), "START", 2,
                            fill="#c8f7c5" if good else "#8d8aa6")
        regions.append((start, ("start",)))
    return img, regions
