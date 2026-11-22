"""The arcade room: walk with W A S D (or click where you want to go), then press E at a table, the store or the championship.

The room is drawn in the browser (arcade/room.py) so walking is smooth. This
file decides what happens: it sends the browser what to show, and reacts to
what the browser reports (the player stopped somewhere, pressed E, I or Esc,
or a walk to a table finished).
"""

from __future__ import annotations

import itertools
import time

import streamlit as st

from arcade import (
    bots,
    catalog,
    dialogues,
    hubmap,
    match,
    room,
    sound,  # A7 (own line, so it merges cleanly with A4)
    state,
    ui,
    wander,
)
from arcade.art import scenes
from arcade.config import ANIMATIONS, BOTS_PER_GAME, GAME_LABELS, GAMES, IDLE_EVERY
from arcade.logic import championship, levels
from arcade.state import S


def _prompts(near: str | None) -> list[dict]:
    """The bubbles shown next to the player."""
    if near in GAMES:
        return [{"text": "PLAY", "key": "E", "action": "interact"}]
    if near == "store":
        return [{"text": "SHOP", "key": "E", "action": "interact"}]
    if near == "champ":
        if not championship.is_unlocked(S.player):
            return [{"text": "LOCKED", "lock": True, "small": "MUST MASTER ALL GAMES TO UNLOCK"}]
        bubbles = [{"text": "START CHAMPIONSHIP", "key": "E", "action": "interact"}]
        if S.player["champ_intro_seen"]:
            bubbles.append({"text": "RULES", "key": "I", "action": "rules"})
        return bubbles
    return []


def picture(prompts=(), glow=None, overrides=None, hint=True):
    """The whole room as one picture (used behind the pause menu, the rules and the fades)."""
    locked = not championship.is_unlocked(S.player)
    t = int(time.time() * 2) % 36  # V5: a clock for small animations (blinks, rainbow hair), two ticks a second
    return scenes.hub_scene(state.hub_actors(overrides), S.player["coins"], prompts, locked, glow, t=t, hint=hint)


def still():
    """The room as a still picture, behind a menu (pause, How to play, the championship bubbles).

    Drawing the whole room takes a while, and it would happen again on every key press in the menu, so the picture
    is kept until something in it changes: the player's clothes or coins, or where anyone stands.
    """
    hub, player = S.hub, S.player
    sign = (tuple(player["equipped"].items()), player["coins"], tuple(hub["pos"]), hub["dir"],
            tuple(sorted((name, tuple(bot["pos"]), bot["dir"]) for name, bot in hub["bots"].items())),
            championship.is_unlocked(player))
    kept = S.get("_still_room")
    if kept is None or kept[0] != sign:
        S["_still_room"] = kept = (sign, picture(hint=False)[0])
    return kept[1]


def _bot_spots() -> list:
    """Where the bots stand: the player cannot walk through them (A5)."""
    return [bot["pos"] for bot in S.hub["bots"].values()]


def _can_use(near: str | None) -> bool:
    return near is not None and not (near == "champ" and not championship.is_unlocked(S.player))


def _can_read_rules(near: str | None) -> bool:
    return near == "champ" and championship.is_unlocked(S.player) and S.player["champ_intro_seen"]


def _remember_still(glow=None) -> None:
    """The next screen fades from this picture of the room (ui.show keeps the last picture in _last_frame)."""
    ui.remember(picture(glow=glow, hint=False)[0])


def _interact(near: str | None) -> None:
    if near in GAMES:  # choose the opponents first, over the room itself; PLAY starts the walk to the table
        sound.play("blip")
        S.hub["versus_n"] = S.hub.get("versus_n", 0) + 1
        S.hub["versus"] = {"game": near, "n": S.hub["versus_n"]}
    elif near == "store":
        sound.play("coin")
        _remember_still()
        S.store_from = "hub"
        state.go("store")
    elif near == "champ" and championship.is_unlocked(S.player):
        _remember_still()
        if S.player["champ_intro_seen"]:
            match.begin_championship()
        else:
            S.intro_page = 0
            state.go("champ_intro")


def _versus_data() -> dict | None:
    """The opponent picker for the browser to draw over the room, or None when it is closed."""
    choice = S.hub.get("versus")
    if not choice:
        return None
    game = choice["game"]
    needed = BOTS_PER_GAME[game]
    cards = [{"name": b["name"], "level": b["level"], "look": bots.look(b), "tag": catalog.spec_for("name", b["tag"])}
             for b in bots.BOTS]
    prizes = {",".join(sorted(combo)): levels.win_coins([bots.level(name) for name in combo])
              for combo in itertools.combinations(bots.BOT_NAMES, needed)}
    title = f"{GAME_LABELS[game]}: CHOOSE {'YOUR OPPONENT' if needed == 1 else f'{needed} OPPONENTS'}"
    return {"n": choice["n"], "needed": needed, "title": title, "cards": cards, "prizes": prizes}


def _versus_answer(value) -> None:
    """PLAY (the bots picked) or BACK in the opponent picker. The picks are checked again here."""
    choice, S.hub["versus"] = S.hub.get("versus"), None
    picked = value.get("picked") if isinstance(value, dict) else None
    if not choice or not isinstance(picked, list):
        return  # BACK
    try:
        levels.check_pick(choice["game"], picked, bots.BOT_NAMES)
    except levels.BadPick:
        return
    sound.play("table")
    match.begin_free_play(choice["game"], picked)  # everyone walks to the table, then the game opens


def _pause() -> None:
    sound.play("pause")
    ui.remember(still())  # drawn now (and kept): the pause menu's first run is quick, and the room is its backdrop
    S.paused_from = "hub"
    state.go("pause")


# ----- talking to the browser

def _player_target() -> dict:
    """Where Python wants the player. seq only changes when Python moved them itself (then the browser jumps there)."""
    hub = S.hub
    if tuple(hub.get("synced") or ()) != tuple(hub["pos"]):
        hub["seq"] = hub.get("seq", 0) + 1
        hub["synced"] = tuple(hub["pos"])
    return {"seq": hub.get("seq", 0), "x": hub["pos"][0], "y": hub["pos"][1], "dir": hub["dir"]}


def _cutscene() -> dict | None:
    """The walk to a table that match.py asked for, in the form the browser plays it."""
    walk = S.hub.get("walk")
    if not walk:
        return None
    if "id" not in walk:
        S["_cut_count"] = S.get("_cut_count", 0) + 1
        walk["id"] = S["_cut_count"]
    movers = {name: [start[0], start[1], end[0], end[1], face] for name, (start, end, face) in walk["movers"].items()}
    zoom = list(hubmap.SPOTS[walk["zoom"]]["center"]) if walk.get("zoom") and ANIMATIONS else None
    return {"id": walk["id"], "movers": movers, "zoom": zoom}


def _scene_data() -> dict:
    if S.pop("_fade_next", False) and ANIMATIONS:  # we arrived through black: the browser fades the room in
        S["_room_fade"] = S.get("_room_fade", 0) + 1
    return room.scene(
        S.setdefault("_room_sent", set()),
        actors=state.hub_actors(),
        coins=S.player["coins"],
        champ_locked=not championship.is_unlocked(S.player),
        bubbles={spot: _prompts(spot) for spot in hubmap.SPOTS},
        player=_player_target(),
        cutscene=_cutscene(),
        fade=S.get("_room_fade", 0),
        ack=S.hub.get("pressed", 0),
        talk=_current_talk(),
        versus=_versus_data(),
    )


TALK_SHOWN = 6.6  # seconds the two speech bubbles of a chat stay in the data sent to the browser
TALK_CHECK = 30  # how far (small canvas) the player may be from a bot when Python checks a TALK press


def _current_talk() -> dict | None:
    talk = S.hub.get("talk")
    if talk and time.time() - talk["t0"] > TALK_SHOWN:
        S.hub["talk"] = talk = None
    return talk


def _talk(value) -> None:
    """E next to a bot: the player says one of their lines to it and it answers (arcade/dialogues.py)."""
    name = value.get("name") if isinstance(value, dict) else None
    hub, now = S.hub, time.time()
    if name not in hub["bots"]:
        return
    spot, _ = wander.where(hub["bots"][name], now)
    if hubmap.distance(spot, hub["pos"]) > TALK_CHECK:
        return
    wander.talk(hub["bots"][name], hub["pos"], now)
    queue = hub.setdefault("chats", {})
    (line, reply), queue[name] = dialogues.next_line(name, queue.get(name, []), state.rng())
    hub["talk"] = {"id": hub.get("talk_count", 0) + 1, "me": S.player["name"], "bot": name, "line": line,
                   "reply": reply, "t0": now}
    hub["talk_count"] = hub["talk"]["id"]
    sound.play("blip")


def _accept(value) -> None:
    """Take the position the browser reports, if it is a real spot on the floor."""
    checked = room.read_pos(value)
    if checked:
        S.hub["pos"], S.hub["dir"] = checked
        S.hub["synced"] = checked[0]


def _finish_walk() -> None:
    """The browser finished the walk to a table: everyone is seated, now start the game."""
    hub = S.hub
    walk = hub["walk"]
    me = S.player["name"]
    for name, (_, end, face) in walk["movers"].items():
        if name == me:
            hub["pos"], hub["dir"] = end, face
            hub["synced"] = tuple(end)
        else:
            hub["bots"][name] = {"pos": end, "dir": face}
    hub["walk"] = None
    # The browser zoomed in and faded to black itself; the ARCADE MASTERS curtain then opens the table.
    if walk.get("then") == "start_game":
        match.start_game()
        ui.curtain_to(S.screen)
    st.rerun()


@st.fragment(run_every=IDLE_EVERY if ANIMATIONS else None)
def _room_view() -> None:
    """The room. It also runs by itself every IDLE_EVERY seconds so the bots can shuffle (A4)."""
    if S.screen != "hub":
        return
    hub = S.hub
    whole_page = S.pop("_hub_page_run", False)
    events = room.mount(_scene_data())

    if events.need:  # the browser lost some pictures (it was reloaded): send them again
        S["_room_sent"].difference_update(key for key in events.need if isinstance(key, str))
        st.rerun(scope="fragment")
    walk = hub.get("walk")
    if walk and events.cut_done is not None and events.cut_done == walk.get("id"):
        _finish_walk()
    for name in ("interact", "rules", "pause", "talk", "versus"):
        value = getattr(events, name)
        if value is None:
            continue
        number = room.new_press(value, hub.get("pressed", 0))
        if number is None:  # the browser sent this press again, but it was already handled
            continue
        hub["pressed"] = number
        _accept(value)
        near = hubmap.near_spot(hub["pos"])
        if name == "talk":
            _talk(value)
            st.rerun(scope="fragment")
        if name == "versus":
            _versus_answer(value)
        elif name == "pause":
            _pause()
        elif name == "rules" and _can_read_rules(near):
            _remember_still()
            state.go("champ_rules")
        elif name == "interact" and _can_use(near):
            _interact(near)
        st.rerun()
    if events.pos is not None:  # the player stopped or walked into another zone: just remember where
        _accept(events.pos)
        return

    if not whole_page and not hub.get("walk"):  # a timed run: the bots walk about (shown on the next one)
        homes = {bot["name"]: bot["home"] for bot in bots.BOTS}
        hub["bots"] = wander.tick(hub["bots"], homes, hub["pos"], state.rng(), time.time())


def render() -> None:
    S._hub_page_run = True
    _room_view()
    # No buttons under the room: E, I and Esc (or a click on a bubble, a table, or the pause button drawn in
    # the corner) are handled by the room itself (arcade/room.py), like in a normal game.
