"""Pictures of the online screens: the online menu (create or join a lobby) and the lobby itself."""

from __future__ import annotations

from functools import lru_cache

from PIL import Image, ImageDraw

from arcade.art import sprites, title_layers
from arcade.art.pixel import darken, draw_text, panel, rgb, upscale, wrap
from arcade.config import SCREEN_H, SCREEN_W

GAME_LABELS = {"uno": "UNO", "checkers": "CHECKERS", "connect4": "CONNECT FOUR"}
GAME_SIZES_TEXT = {"uno": "2 TO 4 PLAYERS", "checkers": "2 PLAYERS", "connect4": "2 PLAYERS"}
SEAT_W = 190


@lru_cache(maxsize=1)
def _background() -> Image.Image:
    img = title_layers.backdrop()
    if img.width != SCREEN_W:
        img = upscale(img)
    return darken(img.convert("RGB"), 0.45)


def _crown(d, x, y, u=3):
    rows = ["#..#..#", "#######", "#.###.#", "#######"]
    for r, row in enumerate(rows):
        for k, c in enumerate(row):
            if c == "#":
                d.rectangle([x + k * u, y + r * u, x + (k + 1) * u - 1, y + (r + 1) * u - 1],
                            fill=rgb("#fff6c4" if r == 0 else "#ffc23a"))


def menu_picture(me: dict, message: str = "") -> Image.Image:
    """PLAY ONLINE: what you can do, and you, ready to play."""
    img = _background().copy()
    panel(img, (60, 40, SCREEN_W - 60, SCREEN_H - 40), "#0f0b2a", "#3ad6ff", bw=4)
    draw_text(img, (SCREEN_W // 2, 70), "PLAY ONLINE", 5, "#ffe94a", "mt", shadow="#16122b")
    sprites.draw_character(img, 210, 400, me["look"], "down", 0, 0, scale=7)
    sprites.draw_name_tag(img, 210, 190, me["name"], me.get("tag"))
    lines = [("CREATE A LOBBY", "#ffffff"), ("AND SEND THE CODE TO YOUR FRIENDS.", "#d9d4ff"), ("", None),
             ("OR JOIN ONE", "#ffffff"), ("WITH A FRIEND'S 4-LETTER CODE.", "#d9d4ff"), ("", None),
             ("UP TO 4 PLAYERS. NO BOTS:", "#7cff3a"), ("JUST YOU AND YOUR FRIENDS.", "#7cff3a")]
    for i, (line, colour) in enumerate(lines):
        if line:
            draw_text(img, (370, 160 + i * 30), line, 2 if colour != "#ffffff" else 3, colour, "lt", shadow="#16122b")
    if message:
        for i, line in enumerate(wrap(message.upper(), 40)):
            draw_text(img, (SCREEN_W // 2, 430 + i * 24), line, 2, "#ff8a8a", "mt", shadow="#16122b")
    return img


def lobby_picture(lobby, me: str, message: str = "", good: bool = False) -> Image.Image:
    """The lobby: its code, the seats (up to 4), the game the host picked and whether it can start."""
    img = _background().copy()
    d = ImageDraw.Draw(img)
    panel(img, (40, 24, SCREEN_W - 40, SCREEN_H - 24), "#0f0b2a", "#3ad6ff", bw=4)
    draw_text(img, (70, 46), "LOBBY", 4, "#ffe94a", "lt", shadow="#16122b")
    draw_text(img, (SCREEN_W - 70, 40), "CODE", 2, "#b9b0e8", "rt")
    draw_text(img, (SCREEN_W - 70, 60), lobby.code, 6, "#ffffff", "rt", shadow="#3a2f6b")
    draw_text(img, (SCREEN_W // 2, 110), "GIVE YOUR FRIENDS THE CODE TO JOIN", 2, "#d9d4ff", "mt")

    left = (SCREEN_W - 4 * SEAT_W) // 2
    for i in range(4):
        x0 = left + i * SEAT_W
        cx = x0 + SEAT_W // 2
        filled = i < len(lobby.players)
        d.rectangle([x0 + 10, 140, x0 + SEAT_W - 10, 360], fill=rgb("#1b1546" if filled else "#140f33"),
                    outline=rgb("#ffe94a" if filled and lobby.players[i]["name"] == me else "#3a2f6b"), width=3)
        if not filled:
            draw_text(img, (cx, 250), "WAITING...", 2, "#5a4f8f", "mm")
            continue
        player = lobby.players[i]
        d.ellipse([cx - 50, 330, cx + 50, 350], fill=rgb("#2a2266"))
        sprites.draw_character(img, cx, 344, player["look"], "down", 0, 0, scale=6)
        sprites.draw_name_tag(img, cx, 176, player["name"], player.get("tag"))
        if player["name"] == lobby.host:
            _crown(d, cx - 10, 146)
            draw_text(img, (cx, 366), "HOST", 2, "#ffc23a", "mt")
        elif player["name"] == me:
            draw_text(img, (cx, 366), "YOU", 2, "#ffe94a", "mt")

    if lobby.game:
        line = f"GAME: {GAME_LABELS[lobby.game]} ({GAME_SIZES_TEXT[lobby.game]})"
    else:
        line = "THE HOST PICKS A GAME"
    draw_text(img, (SCREEN_W // 2, 404), line, 3, "#ffffff", "mt", shadow="#16122b")
    if message:
        draw_text(img, (SCREEN_W // 2, 446), message.upper(), 2, "#7cff3a" if good else "#ff8a8a", "mt",
                  shadow="#16122b")
    return img
