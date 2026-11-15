"""UNO rules, with no screen code at all.

Simplified from the official rules:
  * 108 cards: four colours (one 0, two each of 1-9, Skip, Reverse, Draw Two)
    plus four Wild and four Wild Draw Four.
  * Everyone starts with 7 cards. The first card on the pile is always a number.
  * On your turn play a card that matches the colour or the symbol of the top
    card, or play a wild. If you cannot (or do not want to), draw one card:
    you may play that card straight away or pass.
  * Skip: next player loses the turn. Reverse: play order flips.
    Draw Two / Wild Draw Four: next player draws and loses the turn.
  * The first player with no cards wins.
Left out on purpose: shouting "UNO", stacking draw cards, challenging a
Wild Draw Four and keeping score across rounds.
"""

from __future__ import annotations

import random

COLOURS = ("red", "yellow", "green", "blue")
NUMBERS = tuple(str(n) for n in range(10))
ACTIONS = ("skip", "reverse", "draw2")
WILD = "wild"

Card = tuple  # (colour, value) e.g. ("red", "7"), ("blue", "skip"), ("wild", "wild4")


class IllegalMove(ValueError):
    """Raised when a player tries something the rules do not allow."""


def build_deck() -> list[Card]:
    deck: list[Card] = []
    for colour in COLOURS:
        deck.append((colour, "0"))
        for value in NUMBERS[1:] + ACTIONS:
            deck += [(colour, value), (colour, value)]
    deck += [(WILD, "wild")] * 4 + [(WILD, "wild4")] * 4
    return deck


def card_name(card: Card) -> str:
    colour, value = card
    names = {"skip": "SKIP", "reverse": "REVERSE", "draw2": "+2", "wild": "WILD", "wild4": "WILD +4"}
    label = names.get(value, value)
    return label if colour == WILD else f"{colour.upper()} {label}"


class UnoGame:
    def __init__(self, players: list[str], rng: random.Random | None = None, hand_size: int = 7):
        if not 2 <= len(players) <= 10:
            raise ValueError("UNO needs 2 to 10 players.")
        if len(set(players)) != len(players):
            raise ValueError("Player names must be different.")
        self.players = list(players)
        self.rng = rng or random.Random()
        self.deck = build_deck()
        self.rng.shuffle(self.deck)
        self.hands = {p: [self.deck.pop() for _ in range(hand_size)] for p in self.players}
        while self.deck[-1][1] not in NUMBERS:  # first card must be a number
            self.deck.insert(0, self.deck.pop())
        first = self.deck.pop()
        self.discard: list[Card] = [first]
        self.colour: str = first[0]  # colour in play (matters after a wild)
        self.turn = 0
        self.direction = 1
        self.winner: str | None = None
        self.drawn_card: Card | None = None  # card drawn this turn that may still be played
        self.last_event = "Game on!"

    # ----- reading the state
    @property
    def current(self) -> str:
        return self.players[self.turn]

    @property
    def top(self) -> Card:
        return self.discard[-1]

    def next_player(self, steps: int = 1) -> str:
        return self.players[(self.turn + self.direction * steps) % len(self.players)]

    def can_play(self, card: Card) -> bool:
        colour, value = card
        return colour == WILD or colour == self.colour or value == self.top[1]

    def playable_cards(self, player: str) -> list[Card]:
        if self.winner or player != self.current:
            return []
        if self.drawn_card is not None:
            return [self.drawn_card]
        return [card for card in self.hands[player] if self.can_play(card)]

    # ----- actions
    def play(self, player: str, card: Card, colour: str | None = None) -> None:
        self._check_turn(player)
        card = tuple(card)
        if card not in self.hands[player]:
            raise IllegalMove("You do not have that card.")
        if self.drawn_card is not None and card != self.drawn_card:
            raise IllegalMove("After drawing you can only play the card you drew.")
        if not self.can_play(card):
            raise IllegalMove("That card does not match the colour or the symbol.")
        if card[0] == WILD and colour not in COLOURS:
            raise IllegalMove("Choose a colour for the wild card.")

        self.hands[player].remove(card)
        self.discard.append(card)
        self.colour = colour if card[0] == WILD else card[0]
        self.drawn_card = None
        self.last_event = f"{player} played {card_name(card)}"
        if card[0] == WILD:
            self.last_event += f" ({self.colour.upper()})"
        if not self.hands[player]:
            self.winner = player
            self.last_event = f"{player} is out of cards!"
            return

        skip = 0
        value = card[1]
        if value == "reverse":
            if len(self.players) == 2:
                skip = 1
            else:
                self.direction *= -1
        elif value == "skip":
            skip = 1
        elif value in ("draw2", "wild4"):
            self._give(self.next_player(), 2 if value == "draw2" else 4)
            skip = 1
        self._advance(1 + skip)

    def draw(self, player: str) -> Card | None:
        """Take one card. If it can be played the turn stays with the player."""
        self._check_turn(player)
        if self.drawn_card is not None:
            raise IllegalMove("You already drew a card this turn.")
        card = self._take()
        self.last_event = f"{player} drew a card"
        if card is None:  # no cards left anywhere: the turn just passes
            self._advance(1)
            return None
        self.hands[player].append(card)
        if self.can_play(card):
            self.drawn_card = card
        else:
            self._advance(1)
        return card

    def pass_turn(self, player: str) -> None:
        self._check_turn(player)
        if self.drawn_card is None:
            raise IllegalMove("Draw a card before you pass.")
        self.last_event = f"{player} drew a card and passed"
        self._advance(1)

    def bot_turn(self, player: str) -> None:
        """A simple computer player: play something sensible, otherwise draw."""
        self._check_turn(player)
        options = self.playable_cards(player)
        if not options:
            self.draw(player)
            if self.winner or self.current != player or self.drawn_card is None:
                return
            options = [self.drawn_card]
        danger = len(self.hands[self.next_player()]) <= 2

        def score(card: Card) -> float:
            colour, value = card
            if colour == WILD:
                return 5 if danger and value == "wild4" else 0  # keep wilds for later
            if value in ACTIONS:
                return 4 if danger else 2
            return 1 + int(value) / 10

        best = max(score(c) for c in options)
        card = self.rng.choice([c for c in options if score(c) == best])
        self.play(player, card, self._favourite_colour(player, card))

    # ----- helpers
    def _favourite_colour(self, player: str, played: Card) -> str | None:
        if played[0] != WILD:
            return None
        rest = list(self.hands[player])
        rest.remove(played)
        counts = {c: sum(1 for card in rest if card[0] == c) for c in COLOURS}
        most = max(counts.values())
        return self.rng.choice([c for c in COLOURS if counts[c] == most])

    def _check_turn(self, player: str) -> None:
        if self.winner:
            raise IllegalMove("The game is over.")
        if player not in self.hands:
            raise IllegalMove("That player is not in this game.")
        if player != self.current:
            raise IllegalMove("It is not your turn.")

    def _take(self) -> Card | None:
        if not self.deck and len(self.discard) > 1:
            top = self.discard.pop()
            self.deck = self.discard
            self.rng.shuffle(self.deck)
            self.discard = [top]
        return self.deck.pop() if self.deck else None

    def _give(self, player: str, count: int) -> None:
        for _ in range(count):
            card = self._take()
            if card is not None:
                self.hands[player].append(card)

    def _advance(self, steps: int) -> None:
        self.turn = (self.turn + self.direction * steps) % len(self.players)
        self.drawn_card = None
