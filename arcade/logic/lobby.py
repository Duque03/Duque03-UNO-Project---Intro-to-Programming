"""Online lobbies: up to four friends in their own arcade room, each on their own phone or laptop. No screen code here.

A lobby is a room like the arcade, with three tables. Everyone walks about and chats; to play, a player sits at a
table and waits for the others (the table shows 1/4, 2/4...). Each table is its own game, so two tables can play
at the same time.

    create / join  a signed-in player opens a lobby and gets a 4-letter code to give to friends; at most 4 players
    move           where a player stands in the room (the screen checks the floor first)
    sit / stand    take a chair at a table, or get up. Checkers and Connect Four start when both chairs are taken.
                   UNO starts at 4/4, or UNO_COUNTDOWN seconds after the second player sat down
    say            a short message or one of the pixel emojis (logic/chat.py hides rude words)
    act            a move at the player's table, checked against the rules like any move in the arcade
    done / quit    back to the room after a game (or in the middle of one: the game ends for the others)
    tick           called on every look at the lobby: starts UNO when its countdown is over, plays for a player
                   whose 15 seconds are up, and ends a Corta UNO face-off
Every change adds 1 to the lobby's version (and to the table's, when it is about that table), so a player's screen
knows when to draw itself again.

Everyone who opens the game talks to the same server, so the lobbies live in one shared object (Lobbies) that
every player's session reads and changes. A lock makes sure two players never change a lobby at the same time.
"""

from __future__ import annotations

import copy
import random
import threading
import time

from arcade.logic import chat
from arcade.logic.checkers import BOTTOM, TOP, CheckersGame
from arcade.logic.connect4 import RED, YELLOW, Connect4Game
from arcade.logic.trivia import CUT_PENALTY, Duel, TriviaError
from arcade.logic.uno import UnoGame

# No I or O (they look like 1 and 0), no C or R (Streamlit keeps those keys for itself), no M or F (the game's keys
# for music and full screen), so every letter of a code can be typed straight on the join screen.
CODE_LETTERS = "ABDEGHJKLNPQSTUVWXYZ"
CODE_LENGTH = 4
MAX_PLAYERS = 4
GAMES = ("uno", "checkers", "connect4")  # the three tables of the room
GAME_SIZES = {"uno": (2, 4), "checkers": (2, 2), "connect4": (2, 2)}
GAME_NAMES = {"uno": "UNO", "checkers": "Checkers", "connect4": "Connect Four"}
UNO_COUNTDOWN = 10  # seconds UNO waits for more players once two are seated (it starts at once at 4/4)
TURN_SECONDS = 15
UNO_INTRO_SECONDS = 9  # an online UNO game starts with the deal and the roulette (screens/online_table.py)
STARTER_SECONDS = 4  # checkers and Connect Four start with a roulette that shows who starts
FORGET_AFTER = 2 * 60 * 60  # a lobby nobody has touched for 2 hours is removed
ONLINE_PRIZE = 15  # coins for winning online (like beating a medium bot); UNO pays 1st / 2nd / 3rd shares of it


class LobbyError(ValueError):
    """Raised when a lobby action is not allowed (wrong code, lobby full, table taken, not your turn...)."""


class Table:
    """One table of the room: who sits there and, once it has started, its game."""

    def __init__(self, code: str, game: str):
        self.code = code
        self.game = game
        self.chairs: list[str | None] = [None] * GAME_SIZES[game][1]  # who sits on each chair (screens place them)
        self.countdown: float | None = None  # UNO with 2 or 3 seated: when it starts anyway
        self.table = None  # the game being played: UnoGame, CheckersGame or Connect4Game
        self.seats: list[str] = []  # who plays, in turn order (checkers and Connect Four: the first side first)
        self.cards: dict[str, dict] = {}  # how each of them looks (kept after they leave: still drawn at the table)
        self.back: set[str] = set()  # who has gone back to the room after the game
        self.deadline: float | None = None  # when the current player's 15 seconds are up
        self.duel: Duel | None = None  # a Corta UNO face-off (logic/trivia.py): nothing else moves at this table
        self.result: dict | None = None  # {"places": [...]} or {"winner": name or None}, when the game is over
        self.round = 0  # this game's number in the lobby (a screen uses it to give coins once per game)
        self.version = 0

    def seated(self) -> list[str]:
        return [name for name in self.chairs if name]

    def playing(self) -> bool:
        return self.table is not None and self.result is None

    def player(self, name: str) -> dict:
        return self.cards[name]

    def current(self) -> str | None:
        """Whose turn it is, or None when no game is being played."""
        if not self.playing():
            return None
        if isinstance(self.table, UnoGame):
            return self.table.current
        side = self.table.turn
        first = side == (BOTTOM if isinstance(self.table, CheckersGame) else RED)
        return self.seats[0] if first else self.seats[1]

    def side_of(self, name: str) -> str | None:
        """Checkers and Connect Four: the side this player plays (the first seat is red and moves first)."""
        if isinstance(self.table, CheckersGame):
            return BOTTOM if self.seats.index(name) == 0 else TOP
        if isinstance(self.table, Connect4Game):
            return RED if self.seats.index(name) == 0 else YELLOW
        return None


class Lobby:
    def __init__(self, code: str, host: dict, now: float):
        self.code = code
        self.players: list[dict] = [host]  # {"name", "look", "tag"}, in the order they came in
        self.room: dict[str, dict] = {host["name"]: {"pos": None, "dir": "up"}}  # where each one stands (None: door)
        self.tables = {game: Table(code, game) for game in GAMES}
        self.chat: list[dict] = []  # the last messages: {"id", "name", "text", "emoji", "t"}
        self.said: dict[str, list[float]] = {}  # when each player last spoke (not too fast)
        self.messages = 0
        self.rounds = 0  # games started in this lobby
        self.version = 0
        self.touched = now

    def names(self) -> list[str]:
        return [p["name"] for p in self.players]

    def card(self, name: str) -> dict:
        return next(p for p in self.players if p["name"] == name)

    def chair_of(self, name: str) -> tuple[str, int] | None:
        """(game, chair) where this player sits, or None."""
        for game, table in self.tables.items():
            if name in table.chairs:
                return game, table.chairs.index(name)
        return None

    def table_of(self, name: str) -> Table | None:
        """The table whose game this player is in (playing, or looking at its end), or None."""
        return next((t for t in self.tables.values() if name in t.seats and name not in t.back and t.table is not None),
                    None)


class Lobbies:
    """Every lobby on the server. All methods are safe to call from several players' sessions at once."""

    def __init__(self, rng: random.Random | None = None, clock=time.time):
        self._lobbies: dict[str, Lobby] = {}
        self._lock = threading.RLock()
        self._rng = rng or random.Random()
        self._clock = clock

    # ----- reading
    def get(self, code: str) -> Lobby:
        """A copy of the lobby as it is now (safe to read and draw while others play on)."""
        with self._lock:
            lobby = self._find(code)
            self._tick(lobby)
            return copy.deepcopy(lobby)

    def version(self, code: str, game: str | None = None) -> int | None:
        """The lobby's version, or one table's (cheap to ask every second); None if the lobby is gone."""
        with self._lock:
            lobby = self._lobbies.get(_clean(code))
            if lobby is None:
                return None
            self._tick(lobby)
            return lobby.tables[game].version if game in lobby.tables else lobby.version

    # ----- coming and going
    def create(self, player: dict) -> str:
        with self._lock:
            self._forget_old()
            for _ in range(1000):
                code = "".join(self._rng.choice(CODE_LETTERS) for _ in range(CODE_LENGTH))
                if code not in self._lobbies:
                    break
            self._lobbies[code] = Lobby(code, dict(player), self._clock())
            return code

    def join(self, code: str, player: dict) -> str:
        with self._lock:
            lobby = self._find(code)
            if player["name"] in lobby.names():
                return lobby.code  # already in (for example after reloading the page)
            if len(lobby.players) >= MAX_PLAYERS:
                raise LobbyError(f"That lobby is full ({MAX_PLAYERS} players).")
            lobby.players.append(dict(player))
            lobby.room[player["name"]] = {"pos": None, "dir": "up"}
            self._changed(lobby)
            return lobby.code

    def leave(self, code: str, name: str) -> None:
        """Leave the lobby. A game this player is in ends for the others (nobody wins)."""
        with self._lock:
            lobby = self._lobbies.get(_clean(code))
            if lobby is None or name not in lobby.names():
                return
            self._quit_table(lobby, name)
            self._stand(lobby, name)
            lobby.players = [p for p in lobby.players if p["name"] != name]
            lobby.room.pop(name, None)
            if not lobby.players:
                del self._lobbies[lobby.code]
                return
            for table in lobby.tables.values():
                self._clear_if_done(lobby, table)
            self._changed(lobby)

    def update_card(self, code: str, player: dict) -> None:
        """The player changed clothes (wardrobe): the others see the new look."""
        with self._lock:
            lobby = self._find(code)
            for i, p in enumerate(lobby.players):
                if p["name"] == player["name"] and p != player:
                    lobby.players[i] = dict(player)
                    self._changed(lobby)

    # ----- the room
    def move(self, code: str, name: str, pos, direction: str) -> None:
        """Where the player stands now (the screen has checked it is on the floor)."""
        with self._lock:
            lobby = self._find(code)
            spot = lobby.room.get(name)
            if spot is None:
                raise LobbyError("You are not in this lobby.")
            pos = (int(pos[0]), int(pos[1]))
            if spot["pos"] != pos or spot["dir"] != direction:
                spot["pos"], spot["dir"] = pos, direction
                self._changed(lobby)

    def sit(self, code: str, name: str, game: str) -> int:
        """Take a free chair at a table. Returns the chair's number (the screen knows where it is)."""
        with self._lock:
            lobby = self._find(code)
            self._tick(lobby)
            if name not in lobby.names():
                raise LobbyError("You are not in this lobby.")
            table = lobby.tables.get(game)
            if table is None:
                raise LobbyError("Unknown game.")
            if lobby.table_of(name) is not None:
                raise LobbyError("Finish your game first.")
            if table.table is not None:
                raise LobbyError("A game is being played there.")
            if name in table.chairs:
                return table.chairs.index(name)
            if None not in table.chairs:
                raise LobbyError("That table is full.")
            self._stand(lobby, name)  # (from another table)
            chair = table.chairs.index(None)
            table.chairs[chair] = name
            low, high = GAME_SIZES[game]
            if len(table.seated()) >= high:
                self._start(lobby, table)
            elif len(table.seated()) >= low and table.countdown is None:
                table.countdown = self._clock() + UNO_COUNTDOWN
            self._changed(lobby, table)
            return chair

    def stand(self, code: str, name: str) -> None:
        """Get up from a chair before the game starts (walking away does it too)."""
        with self._lock:
            lobby = self._find(code)
            if self._stand(lobby, name):
                self._changed(lobby)

    def say(self, code: str, name: str, text: str | None = None, emoji: str | None = None) -> dict:
        """A message (text, cleaned by logic/chat.py) or an emoji, above the player's head for a few seconds."""
        with self._lock:
            lobby = self._find(code)
            if name not in lobby.names():
                raise LobbyError("You are not in this lobby.")
            if emoji is not None:
                if emoji not in chat.EMOJIS:
                    raise LobbyError("Unknown emoji.")
                text = None
            else:
                text = chat.clean(text or "")
                if not text:
                    raise LobbyError("Nothing to say.")
            now = self._clock()
            times = lobby.said.setdefault(name, [])
            if not chat.allowed(times, now):
                raise LobbyError("Slow down a little!")
            times[:] = [t for t in times if now - t < chat.BURST_SECONDS] + [now]
            lobby.messages += 1
            message = {"id": lobby.messages, "name": name, "text": text, "emoji": emoji, "t": now}
            lobby.chat = (lobby.chat + [message])[-chat.KEEP:]
            self._changed(lobby)
            return dict(message)

    # ----- after a game
    def done(self, code: str, name: str) -> None:
        """Back to the room after the game is over (the table is free again once everyone has gone back)."""
        with self._lock:
            lobby = self._find(code)
            table = lobby.table_of(name)
            if table is None:
                return
            if table.playing():
                raise LobbyError("Finish the game first.")
            self._leave_table(lobby, table, name)
            self._changed(lobby, table)

    def quit_table(self, code: str, name: str) -> None:
        """Leave the game in the middle (LEAVE at the table): it ends for the others, and this player is back in
        the room."""
        with self._lock:
            lobby = self._find(code)
            if self._quit_table(lobby, name):
                self._changed(lobby)

    # ----- playing
    def act(self, code: str, name: str, move: str, **args) -> None:
        """Make a move at the player's table. UNO: play (cards, colour), draw, pass, uno, cut, answer. Checkers: move
        (start, end). Connect Four: drop (col). The game's own rules check the move (an IllegalMove is raised and
        nothing changes)."""
        with self._lock:
            lobby = self._find(code)
            self._tick(lobby)
            table = lobby.table_of(name)
            if table is None or not table.playing():
                raise LobbyError("No game is being played.")
            game = table.table
            if table.duel is not None:  # a face-off: only its two players move, and only to answer
                if move != "answer":
                    raise LobbyError("Wait for the Corta UNO face-off to end.")
                try:
                    table.duel.answer(name, bool(args.get("yes")), self._clock())
                except TriviaError as problem:
                    raise LobbyError(str(problem)) from None
            elif move == "uno":  # saying UNO is not a turn: it is allowed at any time (there is no time limit)
                game.call_uno(name)
            elif move == "cut":  # Corta UNO: someone else is down to one card and has not said UNO yet
                holder = getattr(game, "uno_due", None)
                if holder is None or holder == name or name not in game.active:
                    raise LobbyError("There is no UNO to cut.")
                table.duel = Duel(holder, name, self._rng, self._clock())
            elif move == "answer":
                raise LobbyError("There is no face-off.")
            else:
                if table.current() != name:
                    raise LobbyError("It is not your turn.")
                before = table.current()
                if move == "play":
                    game.play(name, args["cards"], args.get("colour"))
                elif move == "draw":
                    game.draw(name)
                elif move == "pass":
                    game.pass_turn(name)
                elif move == "move":
                    game.move(tuple(args["start"]), tuple(args["end"]))
                elif move == "drop":
                    game.drop(args["col"])
                else:
                    raise LobbyError("Unknown move.")
                if table.current() != before or move in ("draw", "move"):
                    # a new turn, a drawn card or another jump in a chain gets a fresh 15 seconds
                    table.deadline = self._clock() + TURN_SECONDS
            self._check_over(table)
            self._changed(lobby, table)

    # ----- helpers
    def _find(self, code: str) -> Lobby:
        lobby = self._lobbies.get(_clean(code))
        if lobby is None:
            raise LobbyError("There is no lobby with that code.")
        return lobby

    def _changed(self, lobby: Lobby, table: Table | None = None) -> None:
        lobby.version += 1
        lobby.touched = self._clock()
        if table is not None:
            table.version += 1

    def _stand(self, lobby: Lobby, name: str) -> bool:
        """Free this player's chair at a table that has not started. True if they were sitting."""
        found = lobby.chair_of(name)
        if found is None:
            return False
        table = lobby.tables[found[0]]
        if table.table is not None:
            return False  # (a game is on: leaving it is quit_table)
        table.chairs[found[1]] = None
        if len(table.seated()) < GAME_SIZES[table.game][0]:
            table.countdown = None
        table.version += 1
        return True

    def _start(self, lobby: Lobby, table: Table) -> None:
        seats = table.seated()
        table.seats, table.back, table.countdown = seats, set(), None
        table.cards = {name: dict(lobby.card(name)) for name in seats}
        if table.game == "uno":
            start = self._rng.randrange(len(seats))  # the roulette on everyone's screen shows who it is
            table.table = UnoGame(seats, random.Random(self._rng.random()), start=start)
        elif table.game == "checkers":  # either player may start (the roulette shows who)
            table.table = CheckersGame(first=self._rng.choice((BOTTOM, TOP)))
        else:
            table.table = Connect4Game(first=self._rng.choice((RED, YELLOW)))
        table.result, table.duel = None, None
        lobby.rounds += 1
        table.round = lobby.rounds
        intro = UNO_INTRO_SECONDS if table.game == "uno" else STARTER_SECONDS
        table.deadline = self._clock() + TURN_SECONDS + intro
        table.version += 1

    def _quit_table(self, lobby: Lobby, name: str) -> bool:
        table = lobby.table_of(name)
        if table is None:
            return False
        if table.playing():
            table.result = {"winner": None, "left": name}
            table.deadline = None
            table.duel = None
        self._leave_table(lobby, table, name)
        return True

    def _leave_table(self, lobby: Lobby, table: Table, name: str) -> None:
        table.back.add(name)
        if name in table.chairs:
            table.chairs[table.chairs.index(name)] = None
        table.version += 1
        self._clear_if_done(lobby, table)

    def _clear_if_done(self, lobby: Lobby, table: Table) -> None:
        """Everyone who played has gone back to the room (or left the lobby): the table is free again."""
        if table.table is None or table.playing():
            return
        names = lobby.names()
        if all(name in table.back or name not in names for name in table.seats):
            fresh = Table(lobby.code, table.game)
            fresh.version, fresh.round = table.version + 1, table.round
            lobby.tables[table.game] = fresh

    def _tick(self, lobby: Lobby) -> None:
        """The clock moved on: start UNO after its countdown, play for whoever ran out of time."""
        now = self._clock()
        for table in lobby.tables.values():
            if table.table is None:
                if table.countdown is not None and now >= table.countdown:
                    if len(table.seated()) >= GAME_SIZES[table.game][0]:
                        self._start(lobby, table)
                    table.countdown = None
                    self._changed(lobby, table)
                continue
            if self._tick_game(table, now):
                self._check_over(table)
                self._changed(lobby, table)

    def _tick_game(self, table: Table, now: float) -> bool:
        """Time is up for someone at this table: play for them (or end the face-off when its time came)."""
        game = table.table
        if not table.playing():
            return False
        if table.duel is not None:  # the face-off runs on its own clock; the game waits for it
            if not table.duel.tick(now):
                return False
            if table.duel.phase == "done":
                duel, table.duel = table.duel, None
                if duel.result == "holder":
                    game.lose_cut(duel.holder, CUT_PENALTY)
                else:
                    game.call_uno(duel.holder)
                table.deadline = now + TURN_SECONDS  # the player whose turn it is gets fresh seconds
            return True
        changed = False
        if table.deadline and now > table.deadline:
            if isinstance(game, UnoGame):
                game.auto_turn(game.current)
            else:
                game.random_move(self._rng)
            table.deadline = now + TURN_SECONDS
            changed = True
        return changed

    def _check_over(self, table: Table) -> None:
        game = table.table
        if table.result is not None or game is None or game.winner is None:
            return
        if isinstance(game, UnoGame):
            table.result = {"places": game.places}
        elif game.winner == "draw":
            table.result = {"winner": None}
        else:
            first = game.winner == (BOTTOM if isinstance(game, CheckersGame) else RED)
            table.result = {"winner": table.seats[0] if first else table.seats[1]}
        table.deadline = None
        table.duel = None

    def _forget_old(self) -> None:
        now = self._clock()
        for code in [c for c, lobby in self._lobbies.items() if now - lobby.touched > FORGET_AFTER]:
            del self._lobbies[code]


def _clean(code: str) -> str:
    """What a player typed, as a code: capitals, no spaces."""
    return "".join((code or "").split()).upper()


def online_coins(result: dict, name: str) -> int:
    """Coins a player wins for an online game: the prize for 1st (UNO: half for 2nd, a quarter for 3rd)."""
    if result.get("places"):
        places = result["places"]
        if name not in places or len(places) < 3:
            return ONLINE_PRIZE if places and places[0] == name else 0
        share = {1: 1.0, 2: 0.5, 3: 0.25}.get(places.index(name) + 1, 0)
        return int(ONLINE_PRIZE * share + 0.5)
    return ONLINE_PRIZE if result.get("winner") == name else 0
