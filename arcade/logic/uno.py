"""UNO rules, with no screen code at all.

The official rules, with the team's house rules (task B1):
  * 108 cards: four colours (one 0, two each of 1-9, Skip, Reverse, Draw Two)
    plus four Wild and four Wild Draw Four.
  * Everyone starts with 7 cards. The first card on the pile is always a number.
  * On your turn play a card that matches the colour or the symbol of the top
    card, or play a wild.
  * House rule, several cards at once: together with that first card you may
    play any other cards with the same number or symbol, in the order you
    like. The last one decides the colour (e.g. on a red pile: red 4, green 4,
    yellow 4 -> the next player must follow yellow). Several wilds share one
    chosen colour.
  * Effects add up: each Skip skips one more player (3 skips with 4 players
    and you play again), each Reverse flips the order (two cancel out), each
    Draw Two adds 2 and each Wild Draw Four adds 4 cards for the next player.
  * House rule, stacking: a player facing a Draw Two may answer with Draw Two
    cards, and a player facing a Wild Draw Four with Wild Draw Four cards. The
    cards add up for the next player. Whoever does not answer draws them all
    and loses the turn.
  * House rule, drawing: a player who cannot (or does not want to) play keeps
    drawing until a card can be played; then they may play or pass.
  * House rule, UNO: when a play leaves a player with one card, they must say
    UNO (call_uno) - the screen gives 2 seconds - or draw 2 cards (miss_uno).
  * The first player with no cards wins.
Left out on purpose: challenging a Wild Draw Four and keeping score across rounds.
"""

from __future__ import annotations

import random

COLOURS = ("red", "yellow", "green", "blue")
NUMBERS = tuple(str(n) for n in range(10))
ACTIONS = ("skip", "reverse", "draw2")
WILD = "wild"
DRAWS = {"draw2": 2, "wild4": 4}  # cards that make the next player draw, and how many each
UNO_PENALTY = 2

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


def cards_name(cards: list[Card]) -> str:
    """'RED 4' for one card, '3 x 4 (RED, GREEN, YELLOW)' for several."""
    if len(cards) == 1:
        return card_name(cards[0])
    label = card_name((WILD, cards[0][1])) if cards[0][0] == WILD else card_name(("x", cards[0][1])).split(" ", 1)[1]
    colours = ", ".join(c[0].upper() for c in cards if c[0] != WILD)
    return f"{len(cards)} x {label}" + (f" ({colours})" if colours else "")


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
        self.drawn_card: Card | None = None  # the playable card that ended a draw this turn
        self.pending = 0  # cards waiting for the current player (stacked Draw Two / Wild Draw Four)
        self.pending_value: str | None = None  # "draw2" or "wild4": what can be stacked on them
        self.uno_due: str | None = None  # a player who is down to one card and has not said UNO yet
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
        """Can this card be the first card of a play right now?"""
        colour, value = card
        if self.pending:
            return value == self.pending_value
        return colour == WILD or colour == self.colour or value == self.top[1]

    def playable_cards(self, player: str) -> list[Card]:
        """The cards a play can start with (after a draw: only the card that ended the draw)."""
        if self.winner or player != self.current:
            return []
        if self.drawn_card is not None:
            return [self.drawn_card]
        return [card for card in self.hands[player] if self.can_play(card)]

    def partners(self, player: str, card: Card) -> list[Card]:
        """The other cards in the hand that may be played together with this one (same number or symbol)."""
        rest = list(self.hands[player])
        if card in rest:
            rest.remove(card)
        return [other for other in rest if other[1] == card[1]]

    # ----- actions
    def play(self, player: str, cards, colour: str | None = None) -> None:
        """Play one card, or several cards with the same number or symbol (the first one must match)."""
        self._check_turn(player)
        cards = [tuple(cards)] if cards and isinstance(cards[0], str) else [tuple(c) for c in cards or []]
        if not cards:
            raise IllegalMove("Choose at least one card.")
        hand = list(self.hands[player])
        for card in cards:
            if card not in hand:
                raise IllegalMove("You do not have that card.")
            hand.remove(card)
        if len({card[1] for card in cards}) > 1:
            raise IllegalMove("Cards played together must have the same number or symbol.")
        if self.drawn_card is not None and cards[0] != self.drawn_card:
            raise IllegalMove("After drawing, play starts with the card you drew.")
        if not self.can_play(cards[0]):
            if self.pending:
                raise IllegalMove(f"Answer with {card_name((WILD, self.pending_value)) if self.pending_value == 'wild4' else '+2'}"
                                  f" or draw {self.pending} cards.")
            raise IllegalMove("The first card must match the colour or the symbol.")
        if cards[-1][0] == WILD and colour not in COLOURS:
            raise IllegalMove("Choose a colour for the wild card.")

        self.hands[player] = hand
        self.discard.extend(cards)
        self.colour = colour if cards[-1][0] == WILD else cards[-1][0]
        self.drawn_card = None
        self.last_event = f"{player} played {cards_name(cards)}"
        if cards[-1][0] == WILD:
            self.last_event += f" ({self.colour.upper()})"
        if self.uno_due == player:  # they had one card and did not say it, but now they are out or have more
            self.uno_due = None
        if not self.hands[player]:
            self.winner = player
            self.last_event = f"{player} is out of cards!"
            return
        if len(self.hands[player]) == 1:
            self.uno_due = player

        count, value = len(cards), cards[0][1]
        steps = 1
        if value == "skip":
            steps += count
        elif value == "reverse":
            if len(self.players) == 2:  # with two players a reverse works like a skip
                steps += count
            elif count % 2:
                self.direction *= -1
        elif value in DRAWS:
            self.pending += DRAWS[value] * count
            self.pending_value = value
        self._advance(steps)

    def draw(self, player: str) -> list[Card]:
        """Facing stacked draw cards: take them all and lose the turn.

        Otherwise keep drawing until a card can be played; the turn stays with the
        player, who may play it (see playable_cards) or pass. Returns the cards drawn.
        """
        self._check_turn(player)
        if self.pending:
            taken = self._give(player, self.pending)
            self.last_event = f"{player} drew {len(taken)} cards"
            self.pending, self.pending_value = 0, None
            self._advance(1)
            return taken
        if self.drawn_card is not None:
            raise IllegalMove("You already drew this turn: play the card or pass.")
        taken = []
        while True:
            card = self._take()
            if card is None:  # no cards left anywhere: the turn just passes
                self.last_event = f"{player} drew {len(taken)} cards and found nothing to play" if taken else \
                    f"{player} could not draw (no cards left)"
                self._advance(1)
                return taken
            self.hands[player].append(card)
            taken.append(card)
            if self.uno_due == player:
                self.uno_due = None
            if self.can_play(card):
                self.drawn_card = card
                self.last_event = f"{player} drew {len(taken)} card{'s' if len(taken) > 1 else ''}"
                return taken

    def pass_turn(self, player: str) -> None:
        self._check_turn(player)
        if self.drawn_card is None:
            raise IllegalMove("Draw a card before you pass.")
        self.last_event = f"{player} drew and passed"
        self._advance(1)

    def call_uno(self, player: str) -> bool:
        """The player says UNO. True if they needed to (they are down to one card)."""
        if self.uno_due != player:
            return False
        self.uno_due = None
        self.last_event = f"{player}: UNO!"
        return True

    def miss_uno(self, player: str) -> None:
        """The player did not say UNO in time: they draw 2 cards."""
        if self.uno_due != player:
            return
        self.uno_due = None
        self._give(player, UNO_PENALTY)
        self.last_event = f"{player} forgot to say UNO! +{UNO_PENALTY}"

    def bot_turn(self, player: str, forget_uno: float = 0.15, twins: float = 1.0, stack: float = 1.0,
                 smart: float = 1.0) -> None:
        """A simple computer player: play something sensible, otherwise draw.

        The numbers are chances between 0 and 1 (config.py sets them for the real game):
        forget_uno  the bot forgets to say UNO (and draws 2)
        twins       the bot plays all its matching cards at once instead of just one
        stack       the bot answers a +2 / +4 with its own instead of taking the cards
        smart       the bot picks its best card instead of any card it can play
        """
        self._check_turn(player)
        if self.pending:
            answers = [c for c in self.hands[player] if c[1] == self.pending_value]
            if not answers or self.rng.random() >= stack:
                self.draw(player)
                return
            self._bot_play(player, answers[0], forget_uno, twins)
            return
        options = self.playable_cards(player)
        if not options:
            self.draw(player)
            if self.winner or self.current != player or self.drawn_card is None:
                return
            options = [self.drawn_card]
        danger = len(self.hands[self.next_player()]) <= 2

        def score(card: Card) -> float:
            colour, value = card
            twins = len(self.partners(player, card))
            if colour == WILD:
                return 5 if danger and value == "wild4" else 0  # keep wilds for later
            if value in ACTIONS:
                return (4 if danger else 2) + twins
            return 1 + int(value) / 10 + twins  # getting rid of several cards at once is good

        if self.rng.random() < smart:
            best = max(score(c) for c in options)
            options = [c for c in options if score(c) == best]
        self._bot_play(player, self.rng.choice(options), forget_uno, twins)

    def auto_turn(self, player: str) -> None:
        """The player's time ran out: they draw (or take the +2 / +4 cards) and their turn passes."""
        self._check_turn(player)
        if self.drawn_card is None:
            self.draw(player)
        if self.winner is None and self.current == player:  # they drew a card they could play: they do not
            self.pass_turn(player)

    # ----- helpers
    def _bot_play(self, player: str, first: Card, forget_uno: float, twins_chance: float = 1.0) -> None:
        """Play `first` (with its twins, sometimes), ending on the colour the bot holds most of."""
        may_add = self.drawn_card is None or first == self.drawn_card
        twins = self.partners(player, first) if may_add and self.rng.random() < twins_chance else []
        rest = list(self.hands[player])
        rest.remove(first)  # one copy only: the hand can hold two identical cards
        for twin in twins:
            rest.remove(twin)
        favourite = self._favourite_colour(rest)
        twins.sort(key=lambda c: c[0] == favourite)  # the favourite colour (if any) goes last
        cards = [first] + twins
        self.play(player, cards, favourite if cards[-1][0] == WILD else None)
        if self.uno_due == player:
            if self.rng.random() < forget_uno:
                self.miss_uno(player)
            else:
                self.call_uno(player)

    def _favourite_colour(self, cards: list[Card]) -> str:
        counts = {c: sum(1 for card in cards if card[0] == c) for c in COLOURS}
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

    def _give(self, player: str, count: int) -> list[Card]:
        given = []
        for _ in range(count):
            card = self._take()
            if card is not None:
                self.hands[player].append(card)
                given.append(card)
        return given

    def _advance(self, steps: int) -> None:
        self.turn = (self.turn + self.direction * steps) % len(self.players)
        self.drawn_card = None
