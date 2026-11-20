"""Corta UNO: the trivia face-off between a player who is down to one card and someone who cut their UNO.

House rule (docs/game-design.md, UNO): while a player who is down to one card has not said UNO yet, anyone else can
press CORTA UNO. If they are first, the two of them answer yes-or-no questions, against the clock. When both are right
or both are wrong, another question comes. As soon as one is right and the other is wrong it is over:
- the player with UNO was wrong: they draw 7 cards (nothing happens to the other one);
- the one who cut was wrong: the UNO stands, as if it had been said (nothing happens to them either).
A question not answered in time counts as wrong.

This file has no Streamlit in it: the UNO screen (offline) and the lobby (online) give it the time (`now`).
"""

from __future__ import annotations

import random

ROUND_SECONDS = 8  # time to answer one question
REVEAL_SECONDS = 2.5  # how long the answers stay on screen before the next question (or the end)
CUT_PENALTY = 7  # cards the player with UNO draws if they lose

# Our own yes-or-no questions: (question, the right answer). Short enough to read in a few seconds.
QUESTIONS: list[tuple[str, bool]] = [
    ("Is the Sun a star?", True),
    ("Do spiders have six legs?", False),
    ("Is Lisbon the capital of Portugal?", True),
    ("Is water made of hydrogen and oxygen?", True),
    ("Does a week have eight days?", False),
    ("Is the Pacific the biggest ocean on Earth?", True),
    ("Is a tomato a fruit, for a botanist?", True),
    ("Do wild penguins live at the North Pole?", False),
    ("Is Mount Everest the highest mountain above the sea?", True),
    ("Is 7 x 8 equal to 54?", False),
    ("Does sound travel faster than light?", False),
    ("Is a dolphin a mammal?", True),
    ("Is Au the chemical symbol for gold?", True),
    ("Has a person ever walked on Mars?", False),
    ("Is the Great Wall of China in Japan?", False),
    ("Does water boil at 100 degrees Celsius at sea level?", True),
    ("Does the Moon make its own light?", False),
    ("Is Python a programming language?", True),
    ("Is a square a kind of rectangle?", True),
    ("Is 2 a prime number?", True),
    ("Is 9 a prime number?", False),
    ("Do plants take in carbon dioxide?", True),
    ("Is the Amazon river in Africa?", False),
    ("Is Jupiter the biggest planet of our solar system?", True),
    ("Does an octopus have three hearts?", True),
    ("Is Portuguese the main language of Brazil?", True),
    ("Is a byte made of 8 bits?", True),
    ("Is the heart a muscle?", True),
    ("Is Venus the closest planet to the Sun?", False),
    ("Is most of Antarctica covered in ice?", True),
    ("Does a triangle have four sides?", False),
    ("Does ice float on water?", True),
    ("Does an adult human have about 206 bones?", True),
    ("Is pi exactly 3?", False),
    ("Is Paris the capital of Spain?", False),
    ("Can an ostrich fly?", False),
    ("Does the Earth go round the Sun once a year?", True),
    ("Is a kilometre 1000 metres?", True),
    ("Does the Nile flow through Egypt?", True),
    ("Is a whale a fish?", False),
    ("Is half of 50 equal to 30?", False),
    ("Does a leap year have 366 days?", True),
    ("Is copper a metal?", True),
    ("Is the Sahara in South America?", False),
    ("Is a spider an insect?", False),
    ("Is the Colosseum in Rome?", True),
    ("Is 15 an even number?", False),
    ("Is binary written with only 0 and 1?", True),
    ("Does Saturn have rings?", True),
    ("Is a banana a berry, for a botanist?", True),
    ("Is the metal mercury liquid at room temperature?", True),
    ("Is 12 x 12 equal to 144?", True),
    ("Does the Earth have two moons?", False),
    ("Is oxygen the most common gas in the air?", False),
    ("Do bees make honey?", True),
    ("Does a hexagon have six sides?", True),
    ("Is Tokyo the capital of China?", False),
    ("Is the Douro a river in Portugal?", True),
    ("Is a kilogram heavier than a pound?", True),
    ("Did the Titanic sink in the Pacific Ocean?", False),
    ("Is 0 degrees Celsius the point where water freezes?", True),
    ("Is the Atlantic Ocean between Europe and America?", True),
]


class TriviaError(ValueError):
    """An answer that is not allowed (not one of the two players, answered twice, not the time to answer)."""


class Duel:
    """One face-off. phase: "ask" (waiting for answers), "reveal" (showing who was right), "done" (result is set).

    result: "holder" when the player with UNO lost (they draw 7), "cutter" when the one who cut lost (UNO stands).
    """

    def __init__(self, holder: str, cutter: str, rng: random.Random, now: float):
        if holder == cutter:
            raise TriviaError("Nobody can cut their own UNO.")
        self.holder, self.cutter = holder, cutter
        self.order = rng.sample(range(len(QUESTIONS)), len(QUESTIONS))  # no question comes twice in one duel
        self.round = 0
        self.answers: dict[str, bool] = {}
        self.right: dict[str, bool] = {}  # who was right in the last question (shown during "reveal")
        self.result: str | None = None
        self.phase = "ask"
        self.deadline = now + ROUND_SECONDS
        self.reveal_until = 0.0

    @property
    def players(self) -> tuple[str, str]:
        return self.holder, self.cutter

    @property
    def question(self) -> str:
        return QUESTIONS[self.order[self.round]][0]

    @property
    def truth(self) -> bool:
        return QUESTIONS[self.order[self.round]][1]

    def answer(self, player: str, yes: bool, now: float) -> None:
        """A player answers yes (True) or no (False). When both have answered, the answers are shown."""
        if player not in self.players:
            raise TriviaError("Only the two players in the face-off answer.")
        if self.phase != "ask":
            raise TriviaError("This is not the time to answer.")
        if player in self.answers:
            raise TriviaError("You already answered.")
        self.answers[player] = bool(yes)
        if len(self.answers) == 2:
            self._close(now)

    def tick(self, now: float) -> bool:
        """Let time pass: close a question whose time is up, move on after the answers were shown. True if it changed."""
        if self.phase == "ask" and now > self.deadline:
            self._close(now)
            return True
        if self.phase == "reveal" and now > self.reveal_until:
            if self.result is not None:
                self.phase = "done"
            else:
                self.round += 1
                self.answers = {}
                self.phase, self.deadline = "ask", now + ROUND_SECONDS
            return True
        return False

    def _close(self, now: float) -> None:
        self.right = {p: self.answers.get(p) == self.truth for p in self.players}  # no answer = wrong
        if self.right[self.holder] != self.right[self.cutter]:
            self.result = "holder" if not self.right[self.holder] else "cutter"
        elif self.round + 1 >= len(QUESTIONS):  # every question was used: the UNO stands
            self.result = "cutter"
        self.phase, self.reveal_until = "reveal", now + REVEAL_SECONDS


def bot_answer(rng: random.Random, truth: bool, knows: float) -> bool:
    """A bot's answer: right with the chance `knows` (0 to 1)."""
    return truth if rng.random() < knows else not truth
