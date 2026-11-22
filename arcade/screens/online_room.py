"""The online room: the arcade with the friends in the lobby instead of the bots (docs/game-design.md, section 8).

Everyone walks about and chats (Enter to type, Tab or the face for the emojis). To play, walk to a table and press E:
your character sits down and the table's sign counts who is waiting (1/4, 2/4...). Checkers and Connect Four start
when both chairs are taken; UNO at 4/4, or a few seconds after the second player sat down. Then everyone who sat
goes to the table (screens/online_table.py); the others keep walking about.

The room is drawn by the browser like the offline one (arcade/room.py, with its online extras). The lobby lives on
the server (arcade/logic/lobby.py): this screen tells it where the player is, what they say and where they sit, and
looks at it a few times a second to draw the others.
"""

from __future__ import annotations

import time

import streamlit as st

from arcade import hubmap, online, room, sound, state, ui
from arcade.art import chat as chat_art
from arcade.art import scenes
from arcade.config import ANIMATIONS, GAMES, SCALE, SCREEN_H, SCREEN_W
from arcade.logic import chat
from arcade.logic.lobby import GAME_SIZES, MAX_PLAYERS, LobbyError
from arcade.screens import online as online_screens
from arcade.screens import title as title_screen
from arcade.state import S
from arcade.wander import SEAT_FACING

LOOK_EVERY = 0.6  # seconds between two looks at the lobby (the others' walks and words)
GLIDE = 80  # how fast (small canvas pixels a second) the others glide to where they were last seen
DOORS = [(124, 166), (148, 166), (172, 166), (196, 166)]  # where each player comes in (the order they joined)
SIT_REACH = 8  # a seated player who walks further than this from the chair has got up
SIGN_ABOVE = 30  # how far above the feet of whoever sits across a table its sign ends (small canvas)


def chairs(game: str) -> list[tuple[tuple[int, int], str]]:
    """Where each chair of a table is and which way its player faces: in front, across, left, right."""
    spot = hubmap.SPOTS[game]
    places = [(tuple(spot["stand"]), "up")] + [(tuple(seat), face) for seat, face in zip(spot["seats"], SEAT_FACING)]
    return places[:GAME_SIZES[game][1]]


def _hub() -> dict:
    """This player's place in the online room (the offline room keeps its own, S.hub)."""
    if S.get("ohub") is None or S.ohub.get("code") != S.lobby_code:
        # (seq counts from far away from the offline room's, so the browser always notices it is a new place)
        S.ohub = {"code": S.lobby_code, "pos": None, "dir": "up", "seq": 100000, "synced": None, "pressed": 0,
                  "walk": None}
    return S.ohub


def enter(curtain: bool = False) -> None:
    """Go into the room of the lobby in S.lobby_code: from the online menu (the flight fades in), or back from a
    table (curtain=True: behind the ARCADE MASTERS curtain)."""
    if curtain:
        ui.curtain_to("lobby")
    else:
        ui.fade_next()
        S.screen = "lobby"


def render() -> None:
    code, me = S.get("lobby_code"), S.player["name"]
    lobby = _lobby(code)
    if lobby is None or me not in lobby.names():
        online_screens.leave("That lobby has closed." if lobby is None else "You are not in that lobby any more.")
        st.rerun()
    card = online.card(S.player)
    if lobby.card(me) != card:  # new clothes from the wardrobe: the others see them
        online.lobbies().update_card(code, card)
    if lobby.table_of(me) is not None:  # a game this player sat down for has started
        _to_table(lobby.table_of(me).game)
    title_screen.welcome()  # (the first time in a room since signing in: "Welcome back, ...!")
    hub = _hub()
    if hub["pos"] is None:
        spot = lobby.room[me]["pos"]
        hub["pos"] = tuple(spot) if spot else DOORS[lobby.names().index(me) % len(DOORS)]
        online.lobbies().move(code, me, hub["pos"], hub["dir"])
    S["_ohub_page_run"] = True
    _room_view(code)


def _lobby(code):
    try:
        return online.lobbies().get(code)
    except LobbyError:
        return None


def _to_table(game: str) -> None:
    S.online_game = game
    S["_track"] = game  # with that game's tune from the first picture (sound.render_music)
    ui.curtain_to("online_table")  # into the game behind the ARCADE MASTERS curtain
    st.rerun()


@st.fragment(run_every=LOOK_EVERY if ANIMATIONS else None)
def _room_view(code: str) -> None:
    """The room. It also runs by itself every LOOK_EVERY seconds, to show where the others went and what they said."""
    if S.screen != "lobby" or S.get("lobby_code") != code:
        return
    me, hub = S.player["name"], _hub()
    lobby = _lobby(code)
    if lobby is None or me not in lobby.names() or lobby.table_of(me) is not None:
        st.rerun(scope="app")  # closed, left, or a game started: the whole page decides where to go
    S.pop("_ohub_page_run", False)
    events = room.mount(_scene(lobby, me, hub))

    if events.need:  # the browser lost some pictures (it was reloaded): send them again
        S["_room_sent"].difference_update(key for key in events.need if isinstance(key, str))
        st.rerun(scope="fragment")
    walk = hub.get("walk")
    if walk and events.cut_done is not None and events.cut_done == walk.get("id"):
        _finish_walk(code, me, hub)
        st.rerun(scope="fragment")
    for name in ("interact", "pause", "chat"):
        value = getattr(events, name)
        if value is None:
            continue
        number = room.new_press(value, hub.get("pressed", 0))
        if number is None:  # sent again by the browser, but already handled
            continue
        hub["pressed"] = number
        _accept(code, me, hub, value, lobby)
        if name == "chat":
            _say(code, me, value)
        elif name == "pause":
            _pause(code, me, lobby, hub)
        else:
            _interact(code, me, lobby, hub)
        st.rerun(scope="fragment")
    if events.pos is not None:
        _accept(code, me, hub, events.pos, lobby)


# ---------------------------------------------------------------- what the browser asked for

def _accept(code: str, me: str, hub: dict, value, lobby) -> None:
    """Take the position the browser reports (if it is on the floor), tell the lobby, and get up from a chair when
    the player walked away from it."""
    checked = room.read_pos(value)
    if not checked:
        return
    hub["pos"], hub["dir"] = checked
    hub["synced"] = checked[0]
    online.lobbies().move(code, me, *checked)
    seat = lobby.chair_of(me)
    if seat and not hub.get("walk"):
        place, _ = chairs(seat[0])[seat[1]]
        if hubmap.distance(place, checked[0]) > SIT_REACH:
            online.lobbies().stand(code, me)


def _interact(code: str, me: str, lobby, hub: dict) -> None:
    """E at a table: sit down (or get up, if this is where the player sits). E at the counter: the store, as in the
    arcade (the others see the player standing at the counter meanwhile)."""
    near = hubmap.near_spot(hub["pos"])
    if near == "store":
        online.lobbies().stand(code, me)
        sound.play("coin")
        ui.remember(still(lobby, me, hub))  # (the backdrop while the store gets ready)
        S.store_from = "lobby"
        state.go("store")
        st.rerun()
    if near not in GAMES:
        return
    seat = lobby.chair_of(me)
    if seat and seat[0] == near:
        online.lobbies().stand(code, me)
        sound.play("blip")
        return
    # The player first walks to the chair, and only sits (which can start the game) once there: before, a game with
    # someone already waiting started at once and the player never reached the table.
    table = lobby.tables.get(near)
    problem = ("Finish your game first." if lobby.table_of(me) is not None
               else "A game is being played there." if table is None or table.table is not None
               else "That table is full." if None not in table.chairs else None)
    if problem:
        sound.play("lose")
        ui.toast(problem)
        st.rerun()
    sound.play("table")
    place, face = chairs(near)[table.chairs.index(None)]
    S["_cut_count"] = S.get("_cut_count", 0) + 1
    hub["walk"] = {"id": S["_cut_count"], "to": place, "dir": face, "from": tuple(hub["pos"]), "game": near}


def _finish_walk(code: str, me: str, hub: dict) -> None:
    """The walk to the chair is over: now the player sits (the others see them on it, and a full table starts)."""
    walk, hub["walk"] = hub["walk"], None
    place, face = walk["to"], walk["dir"]
    if walk.get("game"):
        try:
            chair = online.lobbies().sit(code, me, walk["game"])
            place, face = chairs(walk["game"])[chair]  # (another chair if someone took that one meanwhile)
        except LobbyError as problem:  # taken, or a game started there meanwhile: stay standing there
            sound.play("lose")
            ui.toast(str(problem))
    hub["pos"], hub["dir"] = place, face  # (not marked as synced: the browser must jump onto the chair,
    online.lobbies().move(code, me, place, face)  # its walk was only a cutscene's)


def _say(code: str, me: str, value) -> None:
    text = value.get("text") if isinstance(value, dict) else None
    emoji = value.get("emoji") if isinstance(value, dict) else None
    try:
        online.lobbies().say(code, me, text=str(text)[:200] if text is not None else None,
                             emoji=str(emoji) if emoji is not None else None)
        sound.play("blip")
    except LobbyError as problem:
        sound.play("lose")
        ui.toast(str(problem))
        st.rerun()


def _pause(code: str, me: str, lobby, hub: dict) -> None:
    """Esc: the pause menu (the others keep playing: it only pauses this screen). A chair is given up first, so a
    table never starts with someone who is reading a menu."""
    online.lobbies().stand(code, me)
    sound.play("pause")
    S.pause_behind = still(lobby, me, hub)
    ui.remember(S.pause_behind)  # (the backdrop while the menu gets ready)
    S.paused_from = "lobby"
    state.go("pause")
    st.rerun()


# ---------------------------------------------------------------- what the browser draws

def _actors(lobby, me: str, hub: dict) -> list[dict]:
    actors = []
    for i, card in enumerate(lobby.players):
        name = card["name"]
        if name == me:
            actors.append({"name": me, "look": card["look"], "tag": card["tag"], "pos": hub["pos"], "dir": hub["dir"],
                           "player": True})
            continue
        spot = lobby.room.get(name) or {}
        actors.append({"name": name, "look": card["look"], "tag": card["tag"], "speed": GLIDE,
                       "pos": tuple(spot.get("pos") or DOORS[i % len(DOORS)]), "dir": spot.get("dir") or "up"})
    return actors


def _prompts(lobby, me: str) -> dict:
    """The bubbles next to the player, by spot: PLAY at a table with a free chair (LEAVE SEAT where they sit)."""
    seat = lobby.chair_of(me)
    bubbles = {spot: [] for spot in hubmap.SPOTS}
    for game in GAMES:
        table = lobby.tables[game]
        if seat and seat[0] == game:
            bubbles[game] = [{"text": "LEAVE SEAT", "key": "E", "action": "interact"}]
        elif table.table is not None:
            bubbles[game] = [{"text": "PLAYING", "lock": True}]
        elif None not in table.chairs:
            bubbles[game] = [{"text": "FULL", "lock": True}]
        else:
            bubbles[game] = [{"text": "PLAY", "key": "E", "action": "interact"}]
    bubbles["store"] = [{"text": "SHOP", "key": "E", "action": "interact"}]  # the same store as in the arcade
    bubbles["champ"] = [{"text": "COMING SOON...", "lock": True}]  # the online championship is not there yet
    return bubbles


def _signs(lobby) -> list[dict]:
    """The sign on each table: who is waiting (1/4), how long UNO still waits, or that a game is on."""
    now, signs = time.time(), []
    for game in GAMES:
        table = lobby.tables[game]
        chairs_n = len(table.chairs)
        if table.table is not None:
            seated, note, busy = len(table.seats), "PLAYING", True
        else:
            seated, busy = len(table.seated()), False
            note = f"STARTS IN {max(0, int(table.countdown - now + 0.99))}" if table.countdown else ""
        picture = chat_art.table_sign(seated, chairs_n, note, busy)
        spot = hubmap.SPOTS[game]  # over the table, above the head of whoever sits across it
        bottom = (spot["seats"][0][1] - SIGN_ABOVE) * SCALE
        signs.append({"key": f"sign:{seated}:{chairs_n}:{note}:{busy}", "picture": picture,
                      "x": spot["center"][0] * SCALE, "y": bottom - picture.height // 2})
    return signs


def _mats(lobby) -> list[dict]:
    """A mat on the floor at every chair, lit where someone sits (or plays)."""
    mats = []
    for game in GAMES:
        table = lobby.tables[game]
        for k, (place, _) in enumerate(chairs(game)):
            taken = table.chairs[k] is not None or (table.table is not None and k < len(table.seats))
            mats.append({"x": place[0], "y": place[1], "taken": taken})
    return mats


def _says(lobby, me: str) -> list[dict]:
    """What was said in the last few seconds, each above its player's head."""
    now, says = time.time(), []
    for message in lobby.chat:
        left = chat.SHOWN - (now - message["t"])
        if left <= 0 or message["name"] not in lobby.names():
            continue
        mine = message["name"] == me
        key = f"said:{int(mine)}:{message['emoji'] or ''}:{message['text'] or ''}"
        says.append({"id": message["id"], "who": message["name"], "left": round(left, 2), "key": key,
                     "picture": chat_art.said(message["text"], message["emoji"], mine)})
    return says


def _plate(lobby) -> dict:
    picture = chat_art.lobby_plate(lobby.code, len(lobby.players), MAX_PLAYERS)
    return {"key": f"plate:{lobby.code}:{len(lobby.players)}", "picture": picture,
            "x": SCREEN_W - picture.width - 8, "y": SCREEN_H - picture.height - 6}


def _player_target(hub: dict) -> dict:
    """Where Python wants the player; seq changes only when Python moved them itself (the browser jumps there)."""
    if tuple(hub.get("synced") or ()) != tuple(hub["pos"]):
        hub["seq"] = hub.get("seq", 0) + 1
        hub["synced"] = tuple(hub["pos"])
    return {"seq": hub.get("seq", 0), "x": hub["pos"][0], "y": hub["pos"][1], "dir": hub["dir"]}


def _cutscene(hub: dict, me: str) -> dict | None:
    walk = hub.get("walk")
    if not walk:
        return None
    start, end = walk["from"], walk["to"]
    return {"id": walk["id"], "movers": {me: [start[0], start[1], end[0], end[1], walk["dir"]]}, "zoom": None}


def _scene(lobby, me: str, hub: dict) -> dict:
    if S.pop("_fade_next", False) and ANIMATIONS:  # arrived through black: the browser fades the room in
        S["_room_fade"] = S.get("_room_fade", 0) + 1
    return room.scene(
        S.setdefault("_room_sent", set()),
        actors=_actors(lobby, me, hub),
        coins=S.player["coins"],
        champ_locked=True,
        bubbles=_prompts(lobby, me),
        player=_player_target(hub),
        cutscene=_cutscene(hub, me),
        fade=S.get("_room_fade", 0),
        ack=hub.get("pressed", 0),
        online={"says": _says(lobby, me), "signs": _signs(lobby), "mats": _mats(lobby), "plate": _plate(lobby)},
    )


def still(lobby, me: str, hub: dict):
    """The room as one still picture (behind the pause menu)."""
    actors = _actors(lobby, me, hub)
    for actor in actors:
        actor["pos"] = tuple(actor["pos"])
    return scenes.hub_scene(actors, S.player["coins"], (), True, None, t=0, hint=False)[0]
