"""Online lobbies: friends playing each other, each on their own phone or laptop. No screen code here.

Everyone who opens the game talks to the same server, so the lobbies live in one shared object (Lobbies) that
every player's session reads and changes. A lock makes sure two players never change a lobby at the same time.

    create   a signed-in player opens a lobby and gets a 4-letter code to give to friends
    join     up to 4 players in a lobby, with the code
    choose   the host (whoever opened it) picks the game: UNO (2 to 4 players), checkers or Connect Four (2)
    start    the host starts it; there are no bots online, only the people in the lobby
    act      a player makes a move; it is checked against the rules like any move in the arcade
    tick     called on every look at the lobby: when a player's 15 seconds are up the game plays for them,
             and a player who did not say UNO in time draws 2
Every change adds 1 to the lobby's version, so a player's screen knows when to draw itself again.
"""

from __future__ import annotations

import copy
import random
import threading
import time

from arcade.logic.checkers import BOTTOM, CheckersGame
from arcade.logic.connect4 import RED, Connect4Game
from arcade.logic.uno import UnoGame

# No I or O (they look like 1 and 0), no C or R (Streamlit keeps those keys for itself), no M or F (the game's keys
# for music and full screen), so every letter of a code can be typed straight on the join screen.
CODE_LETTERS = "ABDEGHJKLNPQSTUVWXYZ"
CODE_LENGTH = 4
MAX_PLAYERS = 4
GAME_SIZES = {"uno": (2, 4), "checkers": (2, 2), "connect4": (2, 2)}
GAME_NAMES = {"uno": "UNO", "checkers": "Checkers", "connect4": "Connect Four"}
TURN_SECONDS = 15
UNO_INTRO_SECONDS = 9  # an online UNO game starts with the deal and the roulette (screens/online_table.py)
UNO_SECONDS = 3  # online, a little longer than in the arcade: the other players' screens are a second behind
FORGET_AFTER = 2 * 60 * 60  # a lobby nobody has touched for 2 hours is removed
ONLINE_PRIZE = 15  # coins for winning online (like beating a medium bot); UNO pays 1st / 2nd / 3rd shares of it


class LobbyError(ValueError):
    """Raised when a lobby action is not allowed (wrong code, lobby full, not the host, not your turn...)."""


class Lobby:
    def __init__(self, code: str, host: dict, now: float):
        self.code = code
        self.host = host["name"]
        self.players: list[dict] = [host]  # {"name", "look", "tag"}, in the order they joined
        self.gone: dict[str, dict] = {}  # players who left in the middle of a game: still drawn at the table
        self.game: str | None = None  # the game the host picked
        self.table = None  # the game being played: UnoGame, CheckersGame or Connect4Game
        self.seats: list[str] = []  # who sits where at the table (for checkers and Connect Four: first player first)
        self.deadline: float | None = None  # when the current player's 15 seconds are up
        self.uno_deadline: float | None = None  # when the player who must say UNO runs out of time
        self.result: dict | None = None  # {"places": [...]} or {"winner": name or None}, when the game is over
        self.round = 0  # how many games this lobby has started (a screen uses it to give coins once per game)
        self.version = 0
        self.touched = now

    def names(self) -> list[str]:
        return [p["name"] for p in self.players]

    def player(self, name: str) -> dict:
        """A player in the lobby, or one who sat at this table and has left."""
        found = next((p for p in self.players if p["name"] == name), None)
        return found or self.gone[name]

    def current(self) -> str | None:
        """Whose turn it is, or None when no game is being played."""
        if self.table is None or self.result is not None:
            return None
        if isinstance(self.table, UnoGame):
            return self.table.current
        side = self.table.turn
        first = side == (BOTTOM if isinstance(self.table, CheckersGame) else RED)
        return self.seats[0] if first else self.seats[1]

    def side_of(self, name: str) -> str | None:
        """Checkers and Connect Four: the side this player plays (the first seat is red and moves first)."""
        if isinstance(self.table, CheckersGame):
            return BOTTOM if self.seats.index(name) == 0 else "top"
        if isinstance(self.table, Connect4Game):
            return RED if self.seats.index(name) == 0 else "yellow"
        return None


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
            self._tick(self._find(code))
            return copy.deepcopy(self._find(code))

    def version(self, code: str) -> int | None:
        """The lobby's version (cheap to ask every second), or None if it is gone."""
        with self._lock:
            lobby = self._lobbies.get(_clean(code))
            if lobby is None:
                return None
            self._tick(lobby)
            return lobby.version

    # ----- the lobby
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
            if lobby.table is not None and lobby.result is None:
                raise LobbyError("That lobby is in the middle of a game.")
            if len(lobby.players) >= MAX_PLAYERS:
                raise LobbyError(f"That lobby is full ({MAX_PLAYERS} players).")
            lobby.players.append(dict(player))
            self._changed(lobby)
            return lobby.code

    def leave(self, code: str, name: str) -> None:
        """Leave the lobby. A game in progress ends (nobody wins); the next player becomes the host."""
        with self._lock:
            lobby = self._lobbies.get(_clean(code))
            if lobby is None or name not in lobby.names():
                return
            if name in lobby.seats:
                lobby.gone[name] = lobby.player(name)  # the others' tables still draw them until the game is over
            lobby.players = [p for p in lobby.players if p["name"] != name]
            if not lobby.players:
                del self._lobbies[lobby.code]
                return
            if lobby.host == name:
                lobby.host = lobby.players[0]["name"]
            if lobby.table is not None and lobby.result is None:
                lobby.result = {"winner": None, "left": name}
            self._changed(lobby)

    def choose(self, code: str, name: str, game: str) -> None:
        with self._lock:
            lobby = self._find(code)
            self._host_only(lobby, name)
            if game not in GAME_SIZES:
                raise LobbyError("Unknown game.")
            lobby.game = game
            self._changed(lobby)

    def start(self, code: str, name: str) -> None:
        with self._lock:
            lobby = self._find(code)
            self._host_only(lobby, name)
            if lobby.game is None:
                raise LobbyError("Pick a game first.")
            if lobby.table is not None and lobby.result is None:
                raise LobbyError("A game is already being played.")
            low, high = GAME_SIZES[lobby.game]
            if not low <= len(lobby.players) <= high:
                needed = f"{low}" if low == high else f"{low} to {high}"
                raise LobbyError(f"{GAME_NAMES[lobby.game]} needs {needed} players.")
            lobby.seats, lobby.gone = lobby.names(), {}
            if lobby.game == "uno":
                start = self._rng.randrange(len(lobby.seats))  # the roulette on everyone's screen shows who it is
                lobby.table = UnoGame(lobby.seats, random.Random(self._rng.random()), start=start)
            elif lobby.game == "checkers":
                lobby.table = CheckersGame()
            else:
                lobby.table = Connect4Game()
            lobby.result, lobby.uno_deadline = None, None
            lobby.round += 1
            lobby.deadline = self._clock() + TURN_SECONDS + (UNO_INTRO_SECONDS if lobby.game == "uno" else 0)
            self._changed(lobby)

    def back_to_lobby(self, code: str, name: str) -> None:
        """The host, after a game: everyone goes back to the lobby to pick the next game."""
        with self._lock:
            lobby = self._find(code)
            self._host_only(lobby, name)
            if lobby.table is not None and lobby.result is None:
                raise LobbyError("Finish the game first.")
            lobby.table, lobby.result = None, None
            self._changed(lobby)

    # ----- playing
    def act(self, code: str, name: str, move: str, **args) -> None:
        """Make a move. UNO: play (cards, colour), draw, pass, uno. Checkers: move (start, end). Connect Four: drop
        (col). The game's own rules check the move (an IllegalMove is raised and nothing changes)."""
        with self._lock:
            lobby = self._find(code)
            self._tick(lobby)
            table = lobby.table
            if table is None or lobby.result is not None:
                raise LobbyError("No game is being played.")
            if name not in lobby.seats:
                raise LobbyError("You are not playing this game.")
            if move == "uno":  # saying UNO is not a turn: it is allowed at any time
                table.call_uno(name)
                lobby.uno_deadline = None if table.uno_due is None else lobby.uno_deadline
            else:
                if lobby.current() != name:
                    raise LobbyError("It is not your turn.")
                before = lobby.current()
                if move == "play":
                    table.play(name, args["cards"], args.get("colour"))
                elif move == "draw":
                    table.draw(name)
                elif move == "pass":
                    table.pass_turn(name)
                elif move == "move":
                    table.move(tuple(args["start"]), tuple(args["end"]))
                elif move == "drop":
                    table.drop(args["col"])
                else:
                    raise LobbyError("Unknown move.")
                if isinstance(table, UnoGame) and table.uno_due == name:
                    lobby.uno_deadline = self._clock() + UNO_SECONDS
                if lobby.current() != before or move in ("draw", "move"):
                    # a new turn, a drawn card or another jump in a chain gets a fresh 15 seconds
                    lobby.deadline = self._clock() + TURN_SECONDS
            self._check_over(lobby)
            self._changed(lobby)

    # ----- helpers
    def _find(self, code: str) -> Lobby:
        lobby = self._lobbies.get(_clean(code))
        if lobby is None:
            raise LobbyError("There is no lobby with that code.")
        return lobby

    def _host_only(self, lobby: Lobby, name: str) -> None:
        if name != lobby.host:
            raise LobbyError("Only the host can do that.")

    def _changed(self, lobby: Lobby) -> None:
        lobby.version += 1
        lobby.touched = self._clock()

    def _tick(self, lobby: Lobby) -> None:
        """Time is up for someone: play for them (and make a forgotten UNO cost 2 cards)."""
        table, now = lobby.table, self._clock()
        if table is None or lobby.result is not None:
            return
        changed = False
        if isinstance(table, UnoGame) and table.uno_due and lobby.uno_deadline and now > lobby.uno_deadline:
            table.miss_uno(table.uno_due)
            lobby.uno_deadline = None
            changed = True
        if lobby.deadline and now > lobby.deadline:
            if isinstance(table, UnoGame):
                table.auto_turn(table.current)
            else:
                table.random_move(self._rng)
            lobby.deadline = now + TURN_SECONDS
            changed = True
        if changed:
            self._check_over(lobby)
            self._changed(lobby)

    def _check_over(self, lobby: Lobby) -> None:
        table = lobby.table
        if lobby.result is not None or table is None or table.winner is None:
            return
        if isinstance(table, UnoGame):
            lobby.result = {"places": table.places}
        elif table.winner == "draw":
            lobby.result = {"winner": None}
        else:
            first = table.winner == (BOTTOM if isinstance(table, CheckersGame) else RED)
            lobby.result = {"winner": lobby.seats[0] if first else lobby.seats[1]}
        lobby.deadline = lobby.uno_deadline = None

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
