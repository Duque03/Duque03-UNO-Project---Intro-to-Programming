"""Small looping animations that make the arcade feel alive: the games running on the machines' screens, the blinking
lights of their marquees, the claw of the prize machine, the neon sign flickering, the bunting fluttering.

Each one is a short list of little pictures on the small canvas (one pixel = 3 on the big picture). The browser cycles
through them (arcade/room.py in the room; arcade/table_anim.py ALIVE_JS at the tables), so Python sends them once and
nothing has to be redrawn. A "patch" is {"x", "y" (small canvas), "frames": [pictures], "fps"}.
"""

from __future__ import annotations

from functools import lru_cache

from PIL import Image, ImageDraw

from arcade.art.pixel import mix, rgb, shade

FRAMES = 8
NEON = ["#ff4fa3", "#3ad6ff", "#ffe94a", "#7cff3a", "#a06bff", "#ff9f1a"]


def _rect(d, x, y, w, h, colour) -> None:
    if w > 0 and h > 0:
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=colour if isinstance(colour, tuple) else rgb(colour))


@lru_cache(maxsize=64)
def screen_frames(game: int, screen: str, w: int = 16, h: int = 11) -> tuple:
    """A tiny game playing on a machine's screen, as FRAMES pictures (w x h).

    game 0: a little spaceship shooting at blocks; 1: falling blocks; 2: a racing road; 3: a ball bouncing between
    two paddles; 4: a trophy shining (the championship cabinet); 5: a coin bouncing ("insert coin")."""
    base = rgb(screen)
    frames = []
    for f in range(FRAMES):
        img = Image.new("RGB", (w, h), base)
        d = ImageDraw.Draw(img)
        _rect(d, 1, 1, 3, 2, shade(base, 1.5))  # the reflection on the glass
        if game == 0:
            shift = (f // 2) % 2
            for i in range(3):
                _rect(d, 2 + i * 5 + shift, 2, 3, 2, (255, 233, 74) if (i + f) % 4 else (255, 140, 140))
            ship = 3 + (f * 2) % (w - 6) if f < 4 else 3 + ((7 - f) * 2) % (w - 6)
            _rect(d, ship, h - 3, 3, 2, (255, 255, 255))
            bullet = h - 4 - (f % 4) * 2
            _rect(d, ship + 1, bullet, 1, 2, (255, 120, 120))
        elif game == 1:
            for bx, by, colour in ((1, h - 3, "#ff4fa3"), (4, h - 3, "#3ad6ff"), (10, h - 3, "#7cff3a"),
                                   (4, h - 6, "#ffe94a")):
                _rect(d, bx, by, 3, 3, colour)
            _rect(d, 8, min(h - 6, -1 + f * 2), 3, 3, "#ff9f1a")  # the block falling
        elif game == 2:
            _rect(d, 0, h - 6, w, 5, (40, 40, 52))
            for i in range(-1, 4):
                _rect(d, (i * 5 + f * 2) % (w + 5) - 3, h - 4, 3, 1, (255, 255, 255))
            _rect(d, w // 2 - 2, h - 7 + (f % 2), 4, 3, (230, 60, 60))
            _rect(d, 2 + (f * 3) % (w - 4), 1, 2, 2, (255, 246, 170))  # a light passing by
        elif game == 3:
            _rect(d, 1, 2 + (f % 4), 1, 3, (255, 255, 255))
            _rect(d, w - 2, 5 - (f % 4), 1, 3, (255, 255, 255))
            bx = 2 + abs((f * 2) % ((w - 5) * 2) - (w - 5))
            by = 1 + abs((f * 3) % ((h - 3) * 2) - (h - 3))
            _rect(d, bx, by, 2, 2, (255, 233, 74))
            for y in range(0, h, 3):
                _rect(d, w // 2, y, 1, 2, shade(base, 1.4))
        elif game == 4:
            gold, light = (255, 205, 60), (255, 246, 170)
            _rect(d, w // 2 - 3, 2, 6, 4, gold)
            _rect(d, w // 2 - 1, 6, 2, 2, gold)
            _rect(d, w // 2 - 3, 8, 6, 1, gold)
            sparkle = [(w // 2 - 5, 2), (w // 2 + 4, 4), (w // 2 - 4, 7), (w // 2 + 3, 1)][f % 4]
            _rect(d, sparkle[0], sparkle[1], 1, 1, light)
            if f % 2:
                _rect(d, w // 2 - 2, 3, 1, 2, light)
        else:
            y = 2 + abs((f % 6) - 3)
            _rect(d, w // 2 - 2, y, 4, 4, (176, 120, 20))
            _rect(d, w // 2 - 1, y + 1, 2, 2, (255, 205, 60))
            if f % 4 < 2:
                _rect(d, 2, h - 2, w - 4, 1, (255, 233, 74))
        frames.append(img)
    return tuple(frames)


@lru_cache(maxsize=32)
def marquee_frames(w: int, colour: str) -> tuple:
    """The lights along the top of a machine (w x 3), chasing round."""
    frames = []
    for f in range(4):
        img = Image.new("RGB", (w, 3), shade(colour, 0.55))
        d = ImageDraw.Draw(img)
        for x in range(0, w, 2):
            on = (x // 2 + f) % 4 == 0
            _rect(d, x, 1, 1, 1, (255, 246, 200) if on else shade(colour, 1.2))
        frames.append(img)
    return tuple(frames)


@lru_cache(maxsize=4)
def bunting_frames(width: int) -> tuple:
    """The string of little flags across the top of the wall, fluttering (width x 8, see-through)."""
    frames = []
    for f in range(4):
        img = Image.new("RGBA", (width, 8), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, width - 1, 0], fill=(230, 225, 255))
        for i, x in enumerate(range(1, width, 9)):
            sway = 1 if (i + f) % 4 == 0 else -1 if (i + f) % 4 == 2 else 0
            d.polygon([(x, 1), (x + 6, 1), (x + 3 + sway, 6)], fill=rgb(NEON[(i + f // 2) % len(NEON)]))
        frames.append(img)
    return tuple(frames)


@lru_cache(maxsize=2)
def claw_frames() -> tuple:
    """Inside the glass of the prize machine (22 x 20): the claw goes down, grabs, and comes back up."""
    toys = ((2, 15, "#ff4fa3"), (6, 17, "#ffe94a"), (10, 15, "#7cff3a"), (14, 17, "#3ad6ff"), (18, 15, "#ff9f1a"),
            (4, 12, "#a06bff"), (15, 12, "#ff4f6d"))
    drops = [0, 1, 2, 3, 4, 3, 2, 1]
    frames = []
    for f in range(FRAMES):
        img = Image.new("RGB", (22, 20), (30, 46, 100))
        d = ImageDraw.Draw(img)
        for px, py, colour in toys:
            _rect(d, px, py - 2, 4, 4, colour)
            _rect(d, px + 1, py - 1, 1, 1, (255, 255, 255))
        cx = 11 + (-3 if f < 2 else 3 if f >= 6 else 0)
        drop = drops[f]
        _rect(d, cx - 1, 0, 2, 5 + drop, (210, 214, 226))
        _rect(d, cx - 3, 5 + drop, 6, 1, (210, 214, 226))
        grip = 0 if 3 <= f <= 5 else 1
        _rect(d, cx - 3 - grip, 6 + drop, 1, 2, (210, 214, 226))
        _rect(d, cx + 2 + grip, 6 + drop, 1, 2, (210, 214, 226))
        _rect(d, 1, 1, 1, 8, (110, 150, 215))
        frames.append(img)
    return tuple(frames)


def side_glow_frames(screen: str) -> tuple:
    """The glowing strip on the side of a machine seen from the side (3 x 14), pulsing."""
    frames = []
    for f in range(4):
        level = (0.75, 1.0, 1.2, 1.0)[f]
        img = Image.new("RGB", (3, 14), shade(screen, level))
        _rect(ImageDraw.Draw(img), 0, 2 + f * 3, 3, 2, shade(screen, 1.5))
        frames.append(img)
    return tuple(frames)


def neon_frames(base) -> tuple:
    """A neon sign (a finished picture of it) that flickers now and then: mostly on, a short dim moment."""
    dim = Image.blend(base.convert("RGB"), Image.new("RGB", base.size, mix("#16122b", "#000000", 0.2)), 0.45)
    return (base, base, base, base, base, dim, base, dim)


def patch(x: int, y: int, frames, fps: float = 6) -> dict:
    return {"x": x, "y": y, "frames": list(frames), "fps": fps}


def machine_patches(cx: int, base_y: int, screen: str, game: int, w: int = 22, h: int = 40):
    """The moving parts of a machine drawn with scenes._machine(d, cx, base_y, ..., w, h): its screen and marquee."""
    x, top = cx - w // 2, base_y - h
    return [patch(x + 3, top + 9, screen_frames(game, screen, w - 6, 11), 6),
            patch(x + 2, top + 1, marquee_frames(w - 4, screen if game != 4 else "#ffe94a"), 4)]
