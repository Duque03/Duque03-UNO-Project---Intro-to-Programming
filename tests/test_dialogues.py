"""Talking to the bots (arcade/dialogues.py)."""
import random

from arcade import bots, dialogues
from arcade.art import room_layers


def test_thirty_different_exchanges_for_every_bot():
    assert sorted(dialogues.DIALOGUES) == sorted(bots.BOT_NAMES)
    for name, lines in dialogues.DIALOGUES.items():
        assert len(lines) == 30, name
        assert len({said for said, _ in lines}) == 30, name  # the player never says the same thing twice
        for said, reply in lines:
            assert said and reply and len(said) <= 66 and len(reply) <= 66


def test_bark_only_ever_says_bark():
    for _, reply in dialogues.DIALOGUES["BARK"]:
        words = reply.lower().replace("!", " ").replace("?", " ").replace(".", " ").split()
        assert words and all(word == "bark" or set(word) <= set("bark") and word.startswith("ba") for word in words)


def test_all_thirty_come_before_any_repeat():
    rng, remaining, seen = random.Random(1), [], []
    for _ in range(30):
        line, remaining = dialogues.next_line("JOHN", remaining, rng)
        seen.append(line)
    assert sorted(seen) == sorted(dialogues.DIALOGUES["JOHN"])


def test_every_line_fits_in_a_speech_bubble():
    for lines in dialogues.DIALOGUES.values():
        for said, reply in lines:
            assert room_layers.speech(said, True).width <= 320 and room_layers.speech(reply).width <= 320
