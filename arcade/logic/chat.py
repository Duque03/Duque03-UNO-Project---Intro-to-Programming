"""What players may say in the online room: short messages in the game's own letters, rude words hidden, and our own
pixel emojis (drawn in arcade/art/chat.py). No screen code here.

    clean(raw)        the message as it will be shown: capitals, no accents, only letters the pixel font has, at most
                      MAX_LETTERS long, rude words turned into stars
    allowed(times, now)  may this player send another message now? (not too fast, not too many)
"""

from __future__ import annotations

import re
import unicodedata

MAX_LETTERS = 40  # a message fits in a speech bubble of two short lines
LETTERS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !?.,:-_()/+'*")  # what the pixel font can write
GAP = 1.2  # seconds between two messages from the same player
BURST, BURST_SECONDS = 5, 10.0  # at most this many messages in this many seconds
SHOWN = 6.0  # seconds a message stays above its player's head
KEEP = 20  # messages the lobby remembers

# Our own pixel emojis (arcade/art/chat.py draws them), in the order of the emoji panel.
EMOJIS = ["smile", "laugh", "wink", "cool", "love", "wow", "sad", "angry", "heart", "thumbs", "trophy", "gg"]

# Rude words in English and Portuguese, written without accents. Short ones only count as whole words (so
# "computador" or "shitake" are fine); longer ones count anywhere in a word ("fucking", "merdas").
_WHOLE = {"ass", "cu", "fdp", "crl", "pqp", "vsf", "foda", "fode", "puta", "putas", "cona", "pila", "shit",
          "dick", "cock", "cunt", "twat", "slut", "fag", "porra", "corno", "pussy", "tits", "wank", "piss"}
_ANYWHERE = {"fuck", "bitch", "asshole", "bastard", "whore", "nigg", "faggot", "bullshit", "motherf", "merda",
             "caralh", "fodase", "fodasse", "foder", "fodido", "cabrao", "cabroes", "paneleir", "otario", "badalhoc",
             "punheta", "rabeta", "cagalhao", "estupor", "retard"}


def _plain(text: str) -> str:
    """Capitals without accents (ç becomes C, ã becomes A), as the pixel font writes them."""
    flat = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in flat if not unicodedata.combining(ch)).upper()


def _rude(word: str) -> bool:
    low = word.lower()
    return low in _WHOLE or any(bad in low for bad in _ANYWHERE)


def censor(text: str) -> str:
    """Rude words become stars of the same length; everything else stays as it was."""
    return re.sub(r"[A-Z0-9']+", lambda m: "*" * len(m.group()) if _rude(m.group().replace("'", "")) else m.group(),
                  text)


def clean(raw: str) -> str:
    """The message as everyone will see it, or "" if nothing is left to say."""
    text = "".join(ch for ch in _plain(raw) if ch in LETTERS)
    text = " ".join(text.split())[:MAX_LETTERS].strip()
    return censor(text)


def allowed(times: list[float], now: float) -> bool:
    """The times of this player's last messages: may they send another one now?"""
    recent = [t for t in times if now - t < BURST_SECONDS]
    return (not recent or now - recent[-1] >= GAP) and len(recent) < BURST
