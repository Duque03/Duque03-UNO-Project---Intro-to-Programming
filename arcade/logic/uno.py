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
  * House rule, drawing: on their turn a player may draw (whenever they like),
    one card at a time, at most MAX_DRAWS (2) cards. After a draw they may play
    any card that fits, or pass. With nothing to play after the second card, the
    turn passes by itself.
  * House rule, UNO: when a play leaves a player with one card, they must say
    UNO (call_uno) - the screen gives 2 seconds - or draw 2 cards (miss_uno).
  * House rule, places: the first player with no cards finishes 1st and the others play on, without them,
    until only one player is left: that player comes last. (With two players the game ends at once.)
Left out on purpose: challenging a Wild Draw Four and keeping score across rounds.
"""

from __future__ import annotations

import random
from collections import Counter

COLOURS = ("red", "yellow", "green", "blue")
NUMBERS = tuple(str(n) for n in range(10))
ACTIONS = ("skip", "reverse", "draw2")
WILD = "wild"
DRAWS = {"draw2": 2, "wild4": 4}  # cards that make the next player draw, and how many each
UNO_PENALTY = 2
MAX_DRAWS = 2  # cards a player may draw in one turn, one at a time

Card = tuple  # (colour, value) e.g. ("red", "7"), ("blue", "skip"), ("wild", "wild4")


class IllegalMove(ValueError):
    """Raised when a player tries something the rules do not allow."""


def ordinal(place: int) -> str:
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(place, f"{place}th")


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
    def __init__(self, players: list[str], rng: random.Random | None = None, hand_size: int = 7, start: int = 0):
        """start: the seat of the player who goes first (the screens pick it at random with a roulette)."""
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
        if not 0 <= start < len(self.players):
            raise ValueError("The first player must be one of the players.")
        self.turn = start
        self.direction = 1
        self.winner: str | None = None  # 1st place, set when the game is over (only one player has cards left)
        self.out: list[str] = []  # the players who have finished, in order: 1st, 2nd, ...
        self.drawn_card: Card | None = None  # the last card drawn this turn (None before any draw)
        self.draws = 0  # cards drawn this turn (at most MAX_DRAWS)
        self.pending = 0  # cards waiting for the current player (stacked Draw Two / Wild Draw Four)
        self.pending_value: str | None = None  # "draw2" or "wild4": what can be stacked on them
        self.uno_due: str | None = None  # a player who is down to one card and has not said UNO yet
        self.held: tuple[str, Card] | None = None  # (player, last card) waiting for that player to say UNO
        self.last_event = "Game on!"

    # ----- reading the state
    @property
    def current(self) -> str:
        return self.players[self.turn]

    @property
    def top(self) -> Card:
        return self.discard[-1]

    @property
    def active(self) -> list[str]:
        """The players still playing (who have not finished), in seat order."""
        return [p for p in self.players if p not in self.out]

    @property
    def places(self) -> list[str]:
        """Everyone from 1st to last, once the game is over (before that, only those who have finished)."""
        return list(self.out)

    def next_player(self, steps: int = 1) -> str:
        return self.players[self._seat_after(steps)]

    def _seat_after(self, steps: int) -> int:
        """The seat `steps` players further on in the direction of play, skipping players who have finished."""
        seat = self.turn
        for _ in range(steps):
            seat = (seat + self.direction) % len(self.players)
            while self.players[seat] in self.out:
                seat = (seat + self.direction) % len(self.players)
        return seat

    def can_play(self, card: Card) -> bool:
        """Can this card be the first card of a play right now?"""
        colour, value = card
        if self.pending:
            return value == self.pending_value
        return colour == WILD or colour == self.colour or value == self.top[1]

    def playable_cards(self, player: str) -> list[Card]:
        """The cards a play can start with."""
        if self.winner or player != self.current:
            return []
        return [card for card in self.hands[player] if self.can_play(card)]

    def must_draw(self, player: str) -> bool:
        """It is this player's turn, cards are waiting for them (+2 / +4) and they have nothing to answer with:
        the screens then draw for them straight away."""
        return bool(self.pending) and not self.winner and player == self.current and not self.playable_cards(player)

    def can_draw(self, player: str) -> bool:
        """May this player draw now? Facing +2 / +4 cards always; otherwise up to MAX_DRAWS cards a turn."""
        if self.winner or player != self.current:
            return False
        return bool(self.pending) or self.draws < MAX_DRAWS

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
        if not self.can_play(cards[0]):
            if self.pending:
                raise IllegalMove(f"Answer with {card_name((WILD, self.pending_value)) if self.pending_value == 'wild4' else '+2'}"
                                  f" or draw {self.pending} cards.")
            raise IllegalMove("The first card must match the colour or the symbol.")
        if cards[-1][0] == WILD and colour not in COLOURS:
            raise IllegalMove("Choose a colour for the wild card.")
        held = None
        if len(cards) > 1 and not hand:  # house rule: you cannot go out with several cards at once.
            held = cards.pop()  # The last one waits: say UNO first, then it goes down by itself.
            hand.append(held)

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
            self._finish(player)
            if self.winner:
                return
        elif len(self.hands[player]) == 1:
            self.uno_due = player
        if held is not None:
            self.held = (player, held)
            self.last_event += ": say UNO to play the last one!"

        count, value = len(cards), cards[0][1]
        steps = 1
        if value == "skip":
            steps += count
        elif value == "reverse":
            if len(self.active) == 2:  # with two players left a reverse works like a skip
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
        if self.draws >= MAX_DRAWS:
            raise IllegalMove(f"You already drew {MAX_DRAWS} cards: play one or pass.")
        card = self._take()
        if card is None:  # no cards left anywhere: the turn just passes
            self.last_event = f"{player} could not draw (no cards left)"
            self._advance(1)
            return []
        self.hands[player].append(card)
        self.draws += 1
        self.drawn_card = card
        if self.uno_due == player:
            self.uno_due = None
        self.last_event = f"{player} drew a card"
        if self.draws >= MAX_DRAWS and not self.playable_cards(player):  # still nothing to play: next player
            self.last_event = f"{player} drew {MAX_DRAWS} cards and could not play"
            self._advance(1)
        return [card]

    def pass_turn(self, player: str) -> None:
        self._check_turn(player)
        if not self.draws:
            raise IllegalMove("Draw a card before you pass.")
        self.last_event = f"{player} drew and passed"
        self._advance(1)

    def call_uno(self, player: str) -> bool:
        """The player says UNO. True if they needed to (they are down to one card)."""
        if self.uno_due != player:
            return False
        self.uno_due = None
        self.last_event = f"{player}: UNO!"
        if self.held and self.held[0] == player:  # the card that was waiting goes down: they are out
            card = self.held[1]
            self.held = None
            self.hands[player].remove(card)
            self.discard.append(card)
            if card[0] != WILD:
                self.colour = card[0]
            self._finish(player)
            self.last_event = f"{player}: UNO! ...and the last {card_name(card)}. " + self.last_event
            if not self.winner and self.current == player:  # their skips came back round to them: move on
                self._advance(1)
        return True

    def lose_cut(self, player: str, penalty: int = 7) -> None:
        """Corta UNO (logic/trivia.py): the player with UNO lost the face-off. They draw `penalty` cards and keep
        the card that was waiting (if any) in their hand."""
        if self.uno_due != player:
            raise IllegalMove("Only a player waiting to say UNO can lose a cut.")
        self.uno_due = None
        if self.held and self.held[0] == player:
            self.held = None
        self._give(player, penalty)
        self.last_event = f"{player}'s UNO was cut! +{penalty}"

    def miss_uno(self, player: str) -> None:
        """The player did not say UNO in time: they draw 2 cards."""
        if self.uno_due != player:
            return
        self.uno_due = None
        if self.held and self.held[0] == player:
            self.held = None  # the waiting card stays in their hand
        self._give(player, UNO_PENALTY)
        self.last_event = f"{player} forgot to say UNO! +{UNO_PENALTY}"

    def bot_turn(self, player: str, forget_uno: float = 0.15, twins: float = 1.0, stack: float = 1.0,
                 smart: float = 1.0, say_uno: bool = True) -> None:
        """A simple computer player: play something sensible, otherwise draw.

        The numbers are chances between 0 and 1 (config.py sets them for the real game):
        forget_uno  the bot forgets to say UNO (and draws 2)
        twins       the bot plays all its matching cards at once instead of just one
        stack       the bot answers a +2 / +4 with its own instead of taking the cards
        smart       the bot picks its best card instead of any card it can play
        say_uno=False leaves a bot that is down to one card waiting to say UNO (the screen gives the others a moment
        to cut it, then calls call_uno or miss_uno itself).
        """
        self._check_turn(player)
        if self.pending:
            answers = [c for c in self.hands[player] if c[1] == self.pending_value]
            if not answers or self.rng.random() >= stack:
                self.draw(player)
                return
            self._bot_play(player, answers[0], forget_uno, twins, say_uno)
            return
        options = self.playable_cards(player)
        while not options:  # nothing fits: draw, one card at a time (after the second, the turn passes by itself)
            self.draw(player)
            if self.winner or self.current != player:
                return
            options = self.playable_cards(player)
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
        self._bot_play(player, self.rng.choice(options), forget_uno, twins, say_uno)

    def auto_turn(self, player: str) -> None:
        """The player's time ran out: they draw one card (or take the +2 / +4 cards) and their turn passes."""
        self._check_turn(player)
        if self.pending or not self.draws:
            self.draw(player)
        if self.winner is None and self.current == player:  # still their turn: it passes
            self.pass_turn(player)

    # ----- helpers
    def _bot_play(self, player: str, first: Card, forget_uno: float, twins_chance: float = 1.0,
                  say_uno: bool = True) -> None:
        """Play `first` (with its twins, sometimes), ending on the colour the bot holds most of."""
        twins = self.partners(player, first) if self.rng.random() < twins_chance else []
        rest = list(self.hands[player])
        rest.remove(first)  # one copy only: the hand can hold two identical cards
        for twin in twins:
            rest.remove(twin)
        favourite = self._favourite_colour(rest)
        twins.sort(key=lambda c: c[0] == favourite)  # the favourite colour (if any) goes last
        cards = [first] + twins
        self.play(player, cards, favourite if cards[-1][0] == WILD else None)
        if self.uno_due == player and say_uno:
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
        self.turn = self._seat_after(steps)
        self.drawn_card = None
        self.draws = 0

    def _finish(self, player: str) -> None:
        """The player has no cards left: they take the next place. With one player left, the game is over."""
        self.out.append(player)
        if self.uno_due == player:
            self.uno_due = None
        self.last_event = f"{player} is out of cards! {ordinal(len(self.out))} place"
        if len(self.active) == 1:
            self.out.append(self.active[0])
            self.winner = self.out[0]
            self.last_event = f"{player} is out of cards! Game over"

    def play_out(self, settings: dict[str, dict]) -> None:
        """Play the rest of the game at once, every player who is still in playing like a bot.

        Used when the player's own place is settled (they finished, or in a championship someone did).
        settings: for each player still in, the bot_turn chances to play with (see bot_turn).
        """
        for _ in range(5000):  # far more turns than any game needs; stops a game that could not end
            if self.winner:
                return
            if self.uno_due and self.uno_due != self.current:
                self.call_uno(self.uno_due)  # someone who is waiting to say UNO says it
                continue
            self.bot_turn(self.current, **settings[self.current])


def changes(before: UnoGame, after: UnoGame) -> list[tuple[str, str, list[Card]]]:
    """What happened between two moments of the same game, for the animations on the table.

    Returns events (player, "drew" or "played", cards) in the order of play, starting with whoever's turn it was.
    A player's drawn cards come before the cards they played (a card drawn and played straight away is in both).
    """
    played = after.discard[len(before.discard):]
    if after.discard[:len(before.discard)] != before.discard:  # the pile was shuffled back into the deck
        played = after.discard[1:] if after.discard and after.discard[0] == before.top else []
    lost = {p: Counter(before.hands[p]) - Counter(after.hands[p]) for p in before.players}
    drew = {p: list((Counter(after.hands[p]) - Counter(before.hands[p])).elements()) for p in before.players}
    gave = {p: [] for p in before.players}
    for card in played:
        who = next((p for p in before.players if lost[p][card] > 0), None)
        if who is None:  # not in anybody's hand before: drawn and played in the same turn
            who = before.current
            drew[who].append(card)
        else:
            lost[who][card] -= 1
        gave[who].append(card)
    seats = len(before.players)
    order = [before.players[(before.turn + before.direction * k) % seats] for k in range(seats)]
    events = []
    for player in order:
        if drew[player]:
            events.append((player, "drew", drew[player]))
        if gave[player]:
            events.append((player, "played", gave[player]))
    return events
