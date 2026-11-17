"""The arcade room: walk with W A S D (or click where you want to go), then press E at a table, the store or the championship.

The room is drawn in the browser (arcade/room.py) so walking is smooth. This
file decides what happens: it sends the browser what to show, and reacts to
what the browser reports (the player stopped somewhere, pressed E, I or Esc,
or a walk to a table finished).
"""

from __future__ import annotations

import time

import streamlit as st

from arcade import bots, hubmap, idle, match, room, state, ui
from arcade.art import scenes
from arcade.config import ANIMATIONS, GAMES, IDLE_EVERY, SCALE
from arcade.logic import championship
from arcade.state import S
from arcade import sound  # A7 (own line, so it merges cleanly with A4)

_LABELS = {"uno": "Play UNO (E)", "checkers": "Play checkers (E)", "connect4": "Play Connect Four (E)",
           "store": "Enter the store (E)", "champ": "Start championship (E)"}
_STEP = 8  # how far one press of an arrow button moves you


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


def _bot_spots() -> list:
    """Where the bots stand: the player cannot walk through them (A5)."""
    return [bot["pos"] for bot in S.hub["bots"].values()]


def _step(dx: int, dy: int) -> None:
    """One press of an arrow button (for mouse and touch screens): turn that way and take a step."""
    hub = S.hub
    start = hub["pos"]
    hub["dir"] = hubmap.facing(start, (start[0] + dx, start[1] + dy))
    hub["pos"] = hubmap.step_from(start, dx, dy, _STEP, _bot_spots())


def _can_use(near: str | None) -> bool:
    return near is not None and not (near == "champ" and not championship.is_unlocked(S.player))


def _can_read_rules(near: str | None) -> bool:
    return near == "champ" and championship.is_unlocked(S.player) and S.player["champ_intro_seen"]


def _remember_still(glow=None) -> None:
    """The next screen fades from this picture of the room (ui.show keeps the last picture in _last_frame)."""
    S["_last_frame"] = picture(glow=glow, hint=False)[0]


def _interact(near: str | None) -> None:
    if near in GAMES:
        from arcade.screens import versus  # (imported here: versus is a screen like this one)

        sound.play("blip")
        _remember_still(glow=near)
        versus.open_for(near)  # choose the opponents first; Play starts the walk to the table
    elif near == "store":
        sound.play("coin")
        _remember_still()
        state.go("store")
    elif near == "champ" and championship.is_unlocked(S.player):
        _remember_still()
        if S.player["champ_intro_seen"]:
            match.begin_championship()
        else:
            S.intro_page = 0
            state.go("champ_intro")


def _pause() -> None:
    sound.play("pause")
    _remember_still()
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
    )


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
    if walk.get("zoom"):
        cx, cy = hubmap.SPOTS[walk["zoom"]]["center"]
        S["_last_frame"] = scenes.zoom(picture(glow=walk["zoom"], hint=False)[0], (cx * SCALE, cy * SCALE), 3.0)
    if walk.get("then") == "start_game":
        ui.fade_next()  # from the zoomed table to the game, through black
        match.start_game()
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
    for name in ("interact", "rules", "pause"):
        value = getattr(events, name)
        if value is None:
            continue
        number = room.new_press(value, hub.get("pressed", 0))
        if number is None:  # the browser sent this press again, but it was already handled
            continue
        hub["pressed"] = number
        _accept(value)
        near = hubmap.near_spot(hub["pos"])
        if name == "pause":
            _pause()
        elif name == "rules" and _can_read_rules(near):
            _remember_still()
            state.go("champ_rules")
        elif name == "interact" and _can_use(near):
            _interact(near)
        st.rerun()
    if events.pos is not None:
        before = hubmap.near_spot(hub["pos"])
        _accept(events.pos)
        if hubmap.near_spot(hub["pos"]) != before:
            st.rerun()  # the buttons under the room change
        return

    if not whole_page and not hub.get("walk"):  # a timed run: the bots shuffle (shown on the next one)
        homes = {bot["name"]: bot["home"] for bot in bots.BOTS}
        hub["bots"] = idle.idle_tick(hub["bots"], homes, hub["pos"], state.rng())


def render() -> None:
    hub = S.hub
    S._hub_page_run = True
    _room_view()
    near = hubmap.near_spot(hub["pos"])

    bar = st.columns([2.3, 1.1, 0.5, 0.5, 0.5, 0.5, 1.3])
    with bar[0]:  # E, I and Esc are handled by the room itself (arcade/room.py), so these have no shortcut
        use = ui.button(_LABELS.get(near, "Walk up to a table"), "hub_use", type="primary", disabled=not _can_use(near))
    with bar[1]:
        rules = ui.button("Rules (I)", "hub_rules", disabled=not _can_read_rules(near))
    arrows = {}
    for column, (label, name, delta) in zip(bar[2:6], (("↑", "up", (0, -1)), ("←", "left", (-1, 0)),
                                                        ("↓", "down", (0, 1)), ("→", "right", (1, 0)))):
        with column:  # for mouse and touch screens; on a keyboard use W A S D or the arrow keys
            arrows[delta] = ui.button(label, f"hub_step_{name}")
    with bar[6]:
        pause = ui.button("Pause (Esc)", "hub_pause")

    if pause:
        _pause()
        st.rerun()
    if use and _can_use(near):
        _interact(near)
        st.rerun()
    if rules and _can_read_rules(near):
        _remember_still()
        state.go("champ_rules")
        st.rerun()
    for (dx, dy), pressed in arrows.items():
        if pressed:
            _step(dx, dy)
            st.rerun()
