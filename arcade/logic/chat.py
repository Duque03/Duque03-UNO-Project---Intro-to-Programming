"""What players may say in the online room: short messages written as typed (small and capital letters, Portuguese
accents: "Não, você joga?"), rude words hidden, and our own pixel emojis (drawn in arcade/art/chat.py). No screen code
here.

    clean(raw)        the message as it will be shown: only letters the pixel font has, at most MAX_LETTERS long, rude
                      words turned into stars
    allowed(times, now)  may this player send another message now? (not too fast, not too many)
"""

from __future__ import annotations

import re
import unicodedata

MAX_LETTERS = 40  # a message fits in a speech bubble of two short lines
ACCENTED = "ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑáàâãäéèêëíìîïóòôõöúùûüçñ"
SYMBOLS = " !?.,:;-_()/+'\"*@#&%€$=ºª"
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789" + ACCENTED + SYMBOLS  # what the font writes
_ALLOWED = set(LETTERS)
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
    """Small letters without accents (ç becomes c, Ã becomes a): how words are compared with the rude ones."""
    flat = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in flat if not unicodedata.combining(ch)).lower()


def _rude(word: str) -> bool:
    low = _plain(word)
    return low in _WHOLE or any(bad in low for bad in _ANYWHERE)


def censor(text: str) -> str:
    """Rude words become stars of the same length; everything else stays as it was."""
    return re.sub(r"[^\W_]+(?:'[^\W_]+)*", lambda m: "*" * len(m.group()) if _rude(m.group().replace("'", ""))
                  else m.group(), text)


def clean(raw: str) -> str:
    """The message as everyone will see it, or "" if nothing is left to say."""
    text = "".join(ch for ch in unicodedata.normalize("NFC", raw or "") if ch in _ALLOWED)
    text = " ".join(text.split())[:MAX_LETTERS].strip()
    return censor(text)


def allowed(times: list[float], now: float) -> bool:
    """The times of this player's last messages: may they send another one now?"""
    recent = [t for t in times if now - t < BURST_SECONDS]
    return (not recent or now - recent[-1] >= GAP) and len(recent) < BURST
