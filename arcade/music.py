"""The music: one original chiptune loop for the title, one for the arcade room and one for each game.

All five tunes are our own. Each is written here as plain text and turned into a list of notes that the browser
plays with the Web Audio API (SOUND_JS in sound.py). Nothing is recorded, so there are no sound files.

How a tune is written (one bar = 16 steps, a step is a sixteenth note):
    lead / melody   "A4:2 C5:2 E5:3 D5:1 ..."  a note and how many steps it lasts; "r:4" is a rest of 4 steps
    chords          one chord a bar: "Am", "F", "C7", "Gm"... (major, m = minor, 7 = seventh)
    bass            a pattern of (step in the bar, semitones above the chord's root, length) played on every chord
    arp / stabs     the chord's notes played as a pattern (an index into the chord's notes, or None for a rest)
    drums           16 letters a bar: k kick, s snare, h hi-hat, x kick + hi-hat, . nothing
"""

from __future__ import annotations

STEPS_PER_BAR = 16
_NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
         "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
_QUALITY = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10), "maj7": (0, 4, 7, 11)}


def midi(name: str) -> int:
    """'A4' -> 69 (the MIDI number of the note)."""
    pitch, octave = name[:-1], int(name[-1])
    return 12 * (octave + 1) + _NOTE[pitch]


def melody(text: str) -> list[list[int]]:
    """'A4:2 r:2 C5' -> [[step, note, length], ...] (a note without a length lasts one step)."""
    events, step = [], 0
    for token in text.split():
        name, _, length = token.partition(":")
        length = int(length or 1)
        if name != "r":
            events.append([step, midi(name), length])
        step += length
    return events


def length(text: str) -> int:
    return sum(int(token.partition(":")[2] or 1) for token in text.split())


def _chord(symbol: str) -> tuple[int, tuple]:
    """'F#m7' -> (6, (0, 3, 7, 10)): the root's pitch class and the chord's intervals."""
    root = symbol[:2] if len(symbol) > 1 and symbol[1] in "#b" else symbol[:1]
    return _NOTE[root], _QUALITY[symbol[len(root):]]


def bass(chords: list[str], pattern: list[tuple[int, int, int]], octave: int = 2) -> list[list[int]]:
    events = []
    for bar, symbol in enumerate(chords):
        root, _ = _chord(symbol)
        base = 12 * (octave + 1) + root
        for step, interval, steps in pattern:
            events.append([bar * STEPS_PER_BAR + step, base + interval, steps])
    return events


def arpeggio(chords: list[str], pattern: list[int | None], octave: int = 4, steps: int = 1) -> list[list[int]]:
    """The chord's notes (and the root an octave up) played in `pattern`, one entry every `steps` steps."""
    events = []
    for bar, symbol in enumerate(chords):
        root, intervals = _chord(symbol)
        notes = [12 * (octave + 1) + root + i for i in intervals[:3]] + [12 * (octave + 2) + root]
        for k, index in enumerate(pattern):
            if index is not None:
                events.append([bar * STEPS_PER_BAR + k * steps, notes[index], steps])
    return events


def stabs(chords: list[str], at: list[int], octave: int = 4, steps: int = 1) -> list[list[int]]:
    """The whole chord, short, on the given steps of every bar (an offbeat 'chop')."""
    events = []
    for bar, symbol in enumerate(chords):
        root, intervals = _chord(symbol)
        for step in at:
            for i in intervals[:3]:
                events.append([bar * STEPS_PER_BAR + step, 12 * (octave + 1) + root + i, steps])
    return events


def drums(bars: list[str]) -> list[list]:
    hits = {"k": ["k"], "s": ["s"], "h": ["h"], "x": ["k", "h"]}
    events = []
    for bar, pattern in enumerate(bars):
        assert len(pattern) == STEPS_PER_BAR, pattern
        for step, letter in enumerate(pattern):
            for kind in hits.get(letter, []):
                events.append([bar * STEPS_PER_BAR + step, kind])
    return events


# ---------------------------------------------------------------- the five tunes

def _title() -> dict:
    """Title screen: a bright, driving arcade anthem in A minor."""
    chords = ["Am", "F", "C", "G", "Am", "F", "Dm", "E"]
    lead = ("A4:2 C5:2 E5:3 D5:1 C5:2 E5:2 A5:4 "
            "A5:2 G5:2 F5:2 C5:2 F5:4 A5:2 G5:2 "
            "E5:2 G5:2 C6:3 B5:1 G5:2 E5:2 G5:4 "
            "D6:2 B5:2 G5:2 A5:2 B5:4 r:4 "
            "A5:2 E5:2 A5:2 B5:2 C6:4 E6:2 C6:2 "
            "A5:2 F5:2 C5:2 F5:2 A5:3 G5:1 F5:2 E5:2 "
            "F5:2 E5:2 D5:2 F5:2 A5:4 F5:2 E5:2 "
            "E5:2 G#5:2 B5:2 G#5:2 E5:4 r:4")
    return {
        "bpm": 132, "swing": 0.0, "bars": len(chords),
        "lead": melody(lead),
        "bass": bass(chords, [(k * 2, 0 if k % 2 == 0 else 12, 2) for k in range(8)]),
        "arp": arpeggio(chords, [0, 1, 2, 3, 2, 1] * 2 + [0, 1, 2, 1]),
        "drums": drums(["x.h.s.h.x.hks.h."] * 7 + ["x.h.s.h.s.s.ssss"]),
    }


def _room() -> dict:
    """The arcade room: a light, bouncy tune in F major with a little swing, chords on the offbeats."""
    chords = ["F", "Dm", "Gm", "C7", "F", "Am", "Bb", "C7"]
    lead = ("C5 r F5 r A5:2 G5 F5 r:2 A5 r C6:2 r:2 "
            "A5 r F5 r D5:2 E5 F5 r:2 A5 G5 F5:2 r:2 "
            "G5 r Bb5 r D6:2 C6 Bb5 r:2 G5 A5 Bb5:2 r:2 "
            "C6:2 Bb5 G5 E5:2 G5:2 C5:4 r:4 "
            "C5 r F5 r A5:2 G5 F5 r:2 C6 r F6:2 r:2 "
            "E6:2 C6 A5 r:2 E5 G5 A5:2 C6:2 E6:2 r:2 "
            "D6:2 Bb5 F5 r:2 D5 F5 Bb5:2 A5 C6 D6:2 C6:2 "
            "E6 r C6 r G5:2 E5:2 Bb5:2 G5:2 C6:2 r:2")
    return {
        "bpm": 112, "swing": 0.3, "bars": len(chords),
        "lead": melody(lead),
        "bass": bass(chords, [(0, 0, 2), (4, 7, 2), (8, 12, 2), (12, 7, 2)]),
        "stabs": stabs(chords, [2, 6, 10, 14]),
        "drums": drums(["k.h.s.h.k.h.s.h."] * 7 + ["k.h.s.h.k.s.s.ss"]),
    }


def _uno() -> dict:
    """UNO: a fast, funky party tune in G, syncopated melody and a busy bass."""
    chords = ["G", "F", "C", "G", "G", "F", "C", "D7"]
    lead = ("G5 r B5 D6:2 B5 r A5 G5:2 B5 D6 r:2 G5:2 "
            "A5 r C6 F6:2 C6 r Bb5 A5:2 F5 A5 r:2 C6:2 "
            "G5 r E5 G5:2 C6 r B5 C6:2 E6 D6 r:2 C6:2 "
            "B5:2 A5 G5 r:2 D5 E5 G5:4 r:4 "
            "G5 r B5 D6:2 B5 r A5 G5:2 B5 D6 r:2 G6:2 "
            "F6:2 E6 C6 r:2 A5 C6 F6:2 E6 C6 A5:2 C6:2 "
            "E6:2 D6 C6 r:2 G5 A5 C6:2 D6 E6 G6:4 "
            "F#6:2 E6 D6 r:2 A5 B5 C6:2 A5:2 F#5:2 D5:2")
    return {
        "bpm": 138, "swing": 0.0, "bars": len(chords),
        "lead": melody(lead),
        "bass": bass(chords, [(0, 0, 2), (3, 12, 1), (6, 0, 1), (8, 7, 2), (11, 12, 1), (14, 10, 2)]),
        "stabs": stabs(chords, [2, 7, 10], octave=4),
        "drums": drums(["k..hs.hk.khs.h.h"] * 7 + ["k..hs.hk.ksss.ss"]),
    }


def _checkers() -> dict:
    """Checkers: calm and thoughtful, in D minor, a melody over a broken-chord accompaniment."""
    chords = ["Dm", "A", "Dm", "C", "Bb", "F", "Gm", "A"]
    lead = ("D5:4 F5:2 E5:2 D5:2 A4:2 D5:4 "
            "C#5:4 E5:2 D5:2 C#5:2 E5:2 A5:4 "
            "F5:4 A5:2 G5:2 F5:2 E5:2 D5:4 "
            "E5:4 G5:2 F5:2 E5:2 D5:2 C5:4 "
            "D5:2 F5:2 Bb5:4 D6:2 C6:2 Bb5:4 "
            "A5:2 C6:2 F6:4 C6:2 D6:2 C6:4 "
            "Bb5:2 A5:2 G5:4 D5:2 E5:2 G5:2 A5:2 "
            "A5:4 E5:2 C#5:2 A4:4 r:4")
    return {
        "bpm": 96, "swing": 0.0, "bars": len(chords),
        "lead": melody(lead),
        "bass": bass(chords, [(0, 0, 8), (8, 7, 8)]),
        "arp": arpeggio(chords, [0, 2, 1, 2] * 2, octave=4, steps=2),
        "drums": drums(["k...h...k...h..."] * 8),
    }


def _connect4() -> dict:
    """Connect Four: a bouncy, hopping puzzle tune in C major."""
    chords = ["C", "Am", "F", "G", "C", "Em", "F", "G7"]
    lead = ("E5 G5 C6:2 G5 E5 G5:2 C6 D6 E6:2 C6 D6 G5:2 "
            "C6 A5 E5:2 A5 C6 E6:2 C6 B5 A5:2 C6 B5 E6:2 "
            "A5 C6 F6:2 C6 A5 C6:2 F5 G5 A5:2 C6 A5 F5:2 "
            "G5 B5 D6:2 B5 G5 D6:2 G6:4 r:4 "
            "E5 G5 C6:2 G5 E5 G5:2 C6 D6 E6:2 C6 D6 G5:2 "
            "B5 G5 E5:2 G5 B5 E6:2 B5 A5 G5:2 B5 A5 G5:2 "
            "A5 C6 F6:2 C6 D6 C6:2 A5 C6 F6:2 A6 G6 F6:2 "
            "D6:2 B5 G5 F5:2 G5:2 B5:2 D6:2 G6:2 r:2")
    return {
        "bpm": 126, "swing": 0.0, "bars": len(chords),
        "lead": melody(lead),
        "bass": bass(chords, [(0, 0, 2), (4, 12, 2), (8, 7, 2), (12, 12, 2)]),
        "arp": arpeggio(chords, [0, 1, 2, 1] * 4, octave=4),
        "drums": drums(["k.h.s.h.k.k.s.h."] * 7 + ["k.h.s.h.kssss.ss"]),
    }


TRACKS = {"title": _title(), "room": _room(), "uno": _uno(), "checkers": _checkers(), "connect4": _connect4()}

# Which tune each screen plays. A screen that is not listed keeps the tune that was playing (the rules).
SCREEN_TRACKS = {
    "title": "title",
    "hub": "room", "store": "room", "wardrobe": "room", "versus": "room",
    "champ_intro": "room", "champ_rules": "room", "champ_score": "room", "champ_final": "room",
    "uno": "uno", "checkers": "checkers", "connect4": "connect4",
    "online": "title", "lobby": "title",  # an online game plays its own game's tune (screens/online_table.py)
    "pause": "silence",  # the pause menu is quiet; the tune goes on unheard and is back where it would be on resume
}
SILENCE = "silence"


def track_for(screen: str, playing: str | None = None) -> str:
    """The tune for this screen: its own, or the one already playing if it has none (or the title's)."""
    return SCREEN_TRACKS.get(screen) or playing or "title"
