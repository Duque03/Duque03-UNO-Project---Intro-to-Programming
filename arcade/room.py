"""The arcade room, drawn in the browser so walking is smooth.

How it works
------------
Python still decides everything. It paints the pictures (the room, every pose of
every character, name tags, prompt bubbles) and a map of the floor that says,
for every pixel, "can feet stand here?" and "which spot is this close to?"
(hubmap.floor_map). Each picture is sent to the browser once per session.

ROOM_JS (below) only does what Python cannot do 60 times a second:
  * move the player while W A S D or the arrow keys are held (or towards a
    clicked spot), checking the floor map so nobody walks through furniture;
  * stack the pictures in the right order (who is in front of whom);
  * tell Python, with an event, when something happens that needs a decision.

The events (read them from the value mount() returns):
  pos       the player stopped, or walked into or out of a spot's zone: {x, y, dir}
  interact  E was pressed (or a PLAY/SHOP bubble clicked): {x, y, dir}
  rules     I was pressed (or the RULES bubble clicked) at the championship: {x, y, dir}
  pause     Esc was pressed: {x, y, dir}
  cut_done  a scripted walk to a table (and its zoom) has finished: its id
  need      the browser is missing some pictures (it reloaded): their keys

Python moves the player itself (after a game, with the arrow buttons) by
changing hub["pos"]; scene() notices and the browser jumps there.
"""

from __future__ import annotations

import base64
import io
import json
from functools import lru_cache

import streamlit as st

from arcade import hubmap, wander
from arcade.art import room_layers as layers
from arcade.config import SCALE

SPEED = 72  # walking speed, in small-canvas pixels per second (the old keys did about 80)
WALK_SPEED = 140  # speed of the scripted walks to a table (they never take more than 1.4 s)
DIRECTIONS = layers.DIRECTIONS

_URLS: dict[str, str] = {}  # picture key -> data URL, shared by all sessions (the pictures never change)


def _url(key: str, img) -> str:
    if key not in _URLS:
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", compress_level=6)
        _URLS[key] = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
    return _URLS[key]


class Scene:
    """Collects the pictures a frame uses; each one is sent only if this session's browser lacks it."""

    def __init__(self, sent: set):
        self.sent = sent
        self.assets: dict = {}

    def use(self, key: str, make):
        """make() returns a picture (or plain data). Only called the first time a key is sent."""
        if key not in self.sent:
            value = make()
            self.assets[key] = _url(key, value) if hasattr(value, "save") else value
            self.sent.add(key)
        return key


def _look_key(look) -> str:
    return "sheet:" + "|".join(str(part) for part in look)


def _tag_key(spec) -> str | None:
    return json.dumps(spec, sort_keys=True) if spec else None


TALK_REACH = 18  # how close (small canvas) the player must be to a bot to talk to it (E)
POS_EVERY = 0.35  # online, while walking the browser says where the player is this often (the others see the walk)


def scene(sent: set, *, actors, coins, champ_locked, bubbles, player, cutscene=None, fade=0, ack=0, talk=None,
          online=None) -> dict:
    """Everything the browser needs for the room (data for ROOM_JS).

    actors   the six characters (state.hub_actors()); the player has player=True
    bubbles  spot -> list of prompts (see screens/hub._prompts)
    player   {"seq", "x", "y", "dir"}: where Python wants the player; the browser only jumps there when seq changes
    talk     what the player and a bot are saying: {"id", "me", "bot", "line", "reply"} (screens/hub.py), or None
    online   the online room's extras (screens/online_room.py), or None offline: what each player said
             ("says": {"id", "who", "key", "picture", "left"}), the signs over the tables ("signs": {"key", "picture",
             "x", "y"}, centred there), the mats on the floor where the chairs are ("mats": {"x", "y", "taken"},
             small canvas) and the lobby's plate ("plate": {"key", "picture", "x", "y"}). With it the
             browser also draws the chat bar and the emoji panel, and nobody offers TALK (people chat instead).
    """
    s = Scene(sent)
    data = {
        "bg": s.use(f"bg:{champ_locked}", lambda: layers.background(champ_locked)),
        "top": s.use(f"top:{champ_locked}", lambda: layers.top_layer(champ_locked)),
        "map": s.use("map", hubmap.floor_map),
        "speed": SPEED,
        "walkSpeed": WALK_SPEED,
        "scale": SCALE,
        "feet": [layers.FEET[0] * SCALE, layers.FEET[1] * SCALE],
        "cell": [layers.CELL_W * SCALE, layers.CELL_H * SCALE],
        "poses": layers.POSES,
        "player": player,
        "fade": fade,
        "botSpeed": wander.SPEED,
        "talkReach": TALK_REACH,
    }
    talk_img, (tw, th), tpad = layers.bubble("TALK", "E")
    data["talkBubble"] = {"img": s.use("bubble:talk", lambda: talk_img), "w": tw, "h": th, "pad": tpad}
    data["talk"] = None
    if talk:
        lines = []
        for who, text, mine, at, dur in ((talk["me"], talk["line"], True, 0.0, 2.2),  # one after the other
                                         (talk["bot"], talk["reply"], False, 2.3, 4.0)):
            picture = layers.speech(text, mine)
            key = s.use(f"speech:{int(mine)}:{text}", lambda p=picture: p)
            lines.append({"who": who, "img": key, "w": picture.width, "h": picture.height, "at": at, "dur": dur})
        data["talk"] = {"id": talk["id"], "lines": lines}
    hud, hud_at = layers.hud_layer(coins)
    data["hud"] = {"img": s.use(f"hud:{coins}", lambda: hud), "x": hud_at[0], "y": hud_at[1]}

    data["tables"] = []
    for key, table in layers.table_layers().items():
        data["tables"].append({
            "code": hubmap.NEAR_CODES[key], "sort": table["sort"],
            "img": s.use(f"table:{key}", lambda t=table: t["normal"]),
            "lit": s.use(f"table-lit:{key}", lambda t=table: t["lit"]),
            "x": table["at"][0], "y": table["at"][1],
            "label": s.use(f"label:{key}", lambda t=table: t["label"]),
            "lx": table["label_at"][0], "ly": table["label_at"][1],
        })

    data["actors"] = []
    for actor in actors:
        sheet, rows = layers.sheet(actor["look"])
        tag_frames, anchor = layers.tag_frames(actor["name"], _tag_key(actor.get("tag")))
        tag_base = f"tag:{actor['name']}:{_tag_key(actor.get('tag'))}"
        data["actors"].append({
            "name": actor["name"], "player": bool(actor.get("player")),
            "x": actor["pos"][0], "y": actor["pos"][1], "dir": actor.get("dir", "down"),
            "path": actor.get("path"), "pid": actor.get("pid"),
            "sheet": s.use(_look_key(actor["look"]), lambda img=sheet: img), "rows": rows,
            "tags": [s.use(f"{tag_base}:{i}", lambda img=frame: img) for i, frame in enumerate(tag_frames)],
            "tagAnchor": list(anchor),
        })

    data["bubbles"] = {}
    for spot, prompts in bubbles.items():
        items = []
        for prompt in prompts:
            args = (prompt["text"], prompt.get("key"), bool(prompt.get("lock")), prompt.get("small"))
            img, (w, h), pad = layers.bubble(*args)
            items.append({"img": s.use("bubble:" + repr(args), lambda i=img: i), "w": w, "h": h, "pad": pad,
                          "action": prompt.get("action")})
        data["bubbles"][str(hubmap.NEAR_CODES[spot])] = items

    data["alive"] = []  # the machines' screens and lights, the claw, the bunting: looped by the browser
    for i, patch in enumerate(layers.alive_patches()):
        w, h = patch["frames"][0].size
        keys = [s.use(f"alive:{i}:{k}", lambda img=frame: img) for k, frame in enumerate(patch["frames"])]
        data["alive"].append({"x": patch["x"], "y": patch["y"], "w": w, "h": h, "fps": patch["fps"], "frames": keys})

    data["boxes"] = [{"box": list(box), "stand": list(hubmap.SPOTS[spot]["stand"])}
                     for spot, box in hubmap.CLICK_BOXES.items()]
    data["cutscene"] = cutscene
    data["ack"] = ack  # the number of the last key press (E, I, Esc) Python has handled
    if online is not None:
        data["talkReach"] = 0
        data["online"] = _online(s, online)
    data["assets"] = s.assets
    return data


@lru_cache(maxsize=1)
def _font():
    from arcade.art import title_layers

    return title_layers.font_atlas()


def _online(s: Scene, online: dict) -> dict:
    from arcade.art import chat as chat_art
    from arcade.logic.chat import EMOJIS

    atlas, glyphs, height = _font()
    plate = online.get("plate")
    return {
        "mats": [{"x": mat["x"], "y": mat["y"], "taken": bool(mat["taken"])} for mat in online.get("mats", [])],
        "matImg": {"free": s.use("mat:free", lambda: chat_art.chair_mat(False)),
                   "taken": s.use("mat:taken", lambda: chat_art.chair_mat(True))},
        "posEvery": POS_EVERY,
        "font": {"img": s.use("title:font", lambda: atlas), "glyphs": glyphs, "h": height},
        "emojis": [{"name": name, "img": s.use(f"emoji:{name}", lambda n=name: chat_art.emoji(n, 3))} for name in EMOJIS],
        "send": s.use("chat:send", chat_art.send_icon),
        "says": [{"id": say["id"], "who": say["who"], "left": say["left"],
                  "img": s.use(say["key"], lambda p=say["picture"]: p)} for say in online.get("says", [])],
        "signs": [{"x": sign["x"], "y": sign["y"], "img": s.use(sign["key"], lambda p=sign["picture"]: p)}
                  for sign in online.get("signs", [])],
        "plate": None if plate is None else {"x": plate["x"], "y": plate["y"],
                                             "img": s.use(plate["key"], lambda p=plate["picture"]: p)},
    }


def new_press(value, last: int) -> int | None:
    """The number of a key press sent by the browser, if Python has not handled it yet (None otherwise).

    The browser numbers every press of E, I and Esc and sends it again until Python says it was handled,
    so a press is never lost. Python handles each number once.
    """
    try:
        number = int(value["n"])
    except (TypeError, KeyError, ValueError):
        return None
    return number if number > last else None


def read_pos(value) -> tuple[tuple[int, int], str] | None:
    """Check a position sent by the browser: whole numbers on the floor, a real direction. None if not valid."""
    try:
        x, y = int(round(float(value["x"]))), int(round(float(value["y"])))
        direction = str(value.get("dir", "down"))
    except (TypeError, KeyError, ValueError, AttributeError):
        return None
    if direction not in DIRECTIONS or hubmap.clamp(x, y) != (x, y) or hubmap.blocked_by_furniture((x, y)):
        return None
    return (x, y), direction


ROOM_CSS = """
.arcade-room-wrap { position: relative; width: 100%; }
canvas.arcade-room {
    display: block; width: 100%; height: auto; aspect-ratio: 16 / 9;
    image-rendering: pixelated; cursor: pointer; border-radius: 10px;  /* the frame around it glows (ui.py) */
    outline: none;
}
"""

ROOM_JS = r"""
export default function (component) {
    const { data, setTriggerValue, parentElement } = component;
    // Everything that must survive between Streamlit runs lives on window.
    const G = window.__arcadeRoom || (window.__arcadeRoom = {
        images: {}, objects: {}, maps: {}, keys: [], bots: {}, seq: null, fadeSeen: null,
        cutDone: {}, lastNeed: 0, running: false,
    });
    G.data = data;
    G.send = setTriggerValue;

    // ---- the canvas (created once, kept between runs)
    let canvas = parentElement.querySelector("canvas.arcade-room");
    if (!canvas) {  // inside a box of its own, so the online chat's text box can be laid over it
        const wrap = document.createElement("div");
        wrap.className = "arcade-room-wrap";
        canvas = document.createElement("canvas");
        canvas.className = "arcade-room";
        canvas.width = 960;
        canvas.height = 540;
        wrap.appendChild(canvas);
        parentElement.appendChild(wrap);
    }
    G.canvas = canvas;

    // ---- pictures and the floor map sent this run
    for (const [key, value] of Object.entries(data.assets || {})) {
        if (typeof value === "string") {
            const img = new Image();
            img.src = value;
            G.images[key] = img;
        } else {
            G.objects[key] = value;
        }
    }
    if (!G.maps[data.map] && G.objects[data.map]) {
        const raw = G.objects[data.map];
        const unrun = (runs) => {
            const out = new Uint8Array(raw.w * raw.h);
            let i = 0;
            for (let r = 0; r < runs.length; r += 2) { out.fill(runs[r], i, i + runs[r + 1]); i += runs[r + 1]; }
            return out;
        };
        G.maps[data.map] = { w: raw.w, h: raw.h, blocked: unrun(raw.blocked), near: unrun(raw.near), body: raw.bot_body };
    }

    // ---- where Python wants the player (only when it really moved them)
    if (data.player.seq !== G.seq) {
        G.seq = data.player.seq;
        G.x = data.player.x; G.y = data.player.y; G.dir = data.player.dir;
        G.target = null; G.moving = false; G.zone = null;
    }

    // ---- bots: walk the paths Python planned (arcade/wander.py); otherwise glide to their new spot
    const now = performance.now() / 1000;
    for (const actor of data.actors) {
        if (actor.player) continue;
        const b = G.bots[actor.name];
        if (!b) {
            G.bots[actor.name] = { x: actor.x, y: actor.y, fx: actor.x, fy: actor.y, tx: actor.x, ty: actor.y, t0: 0, dur: 0, dir: actor.dir, pid: actor.pid };
        } else if (actor.pid != null && actor.pid !== b.pid) {  // a new walk (or a stop)
            b.pid = actor.pid;
            b.tx = actor.x; b.ty = actor.y; b.goalDir = actor.dir;
            if (actor.path && actor.path.length > 1) {
                b.path = [[b.x, b.y]].concat(actor.path.slice(1)); b.pathT0 = now;
            } else {
                b.path = null; b.fx = b.x; b.fy = b.y; b.t0 = now;
                b.dur = Math.max(0.15, Math.hypot(b.tx - b.fx, b.ty - b.fy) / (actor.speed || 40));
                b.dir = actor.dir;
            }
        } else if (b.path) {
            b.goalDir = actor.dir;
        } else if (b.tx !== actor.x || b.ty !== actor.y) {
            b.fx = b.x; b.fy = b.y; b.tx = actor.x; b.ty = actor.y; b.t0 = now;
            b.dur = Math.max(0.15, Math.hypot(b.tx - b.fx, b.ty - b.fy) / (actor.speed || 40));
            b.dir = actor.dir;
        } else {
            b.dir = actor.dir;
        }
    }
    for (const name of Object.keys(G.bots)) {  // someone who is not in this room any more (the offline bots, online)
        if (!data.actors.some((a) => !a.player && a.name === name)) delete G.bots[name];
    }
    if (data.talk && data.talk.id !== G.talkId) { G.talkId = data.talk.id; G.talkT0 = now; }
    G.says = G.says || {};  // online: chat message id -> until when its bubble shows
    for (const say of (data.online && data.online.says) || []) if (!(say.id in G.says)) G.says[say.id] = now + say.left;

    // ---- a scripted walk to a table, then a zoom
    if (data.cutscene && (!G.cut || G.cut.id !== data.cutscene.id) && !G.cutDone[data.cutscene.id]) {
        const movers = data.cutscene.movers;
        let longest = 1;
        for (const m of Object.values(movers)) longest = Math.max(longest, Math.hypot(m[2] - m[0], m[3] - m[1]));
        G.cut = { id: data.cutscene.id, movers, zoom: data.cutscene.zoom, t0: now, walk: Math.min(1.4, longest / data.walkSpeed), sent: false };
        G.keys.length = 0; G.target = null;
    } else if (!data.cutscene) {
        G.cut = null;
    }
    if (data.fade && data.fade !== G.fadeSeen) { G.fadeSeen = data.fade; G.fadeStart = now; }

    // ---- input
    const KEYS = { w: "up", arrowup: "up", s: "down", arrowdown: "down", a: "left", arrowleft: "left", d: "right", arrowright: "right" };
    const typing = (event) => {
        const t = event.target;
        return t && (t.isContentEditable || ["input", "textarea", "select"].includes((t.tagName || "").toLowerCase()));
    };
    const here = () => ({ x: Math.round(G.x), y: Math.round(G.y), dir: G.dir });
    const PAUSE_BOX = [10, 470, 44, 44];  // bottom-left corner, above the hints
    // Key presses are numbered and sent again until Python says it handled them (data.ack), so none is lost.
    G.pressN = Math.max(G.pressN || 0, data.ack || 0);
    if (G.press && (data.ack || 0) >= G.press.n) G.press = null;
    const act = (kind, extra) => {
        G.pressN += 1;
        G.press = { kind, value: { ...here(), ...(extra || {}), n: G.pressN }, t: performance.now(), tries: 1 };
        G.send(kind, G.press.value);
    };
    // ---- online: the chat bar. Its text box is a real one (see-through, over the bar), so a phone shows its
    // keyboard and no other key of the game reacts while typing; the canvas draws what is typed in the pixel font.
    const ON = data.online;
    let chatBox = canvas.parentNode.querySelector("input.arcade-chat");
    if (ON && !chatBox) {
        chatBox = document.createElement("input");
        chatBox.className = "arcade-chat";
        chatBox.maxLength = 40; chatBox.autocomplete = "off"; chatBox.spellcheck = false;
        chatBox.setAttribute("aria-label", "Chat");
        const [fx, fy, fw, fh] = CHAT.field;
        chatBox.style.cssText = `position:absolute;left:${fx / 9.6}%;top:${fy / 5.4}%;width:${fw / 9.6}%;`
            + `height:${fh / 5.4}%;opacity:0;border:0;padding:0;margin:0;font-size:16px;cursor:text;z-index:2;`;
        canvas.parentNode.appendChild(chatBox);
        chatBox.addEventListener("focus", () => { G.keys.length = 0; G.target = null; G.emojiOpen = false; });
        chatBox.addEventListener("keydown", (event) => {
            event.stopPropagation();
            if (event.key === "Enter") {
                event.preventDefault();
                const text = chatBox.value.trim();
                chatBox.value = ""; chatBox.blur();
                if (text) act("chat", { text });
            } else if (event.key === "Escape") {
                event.preventDefault(); chatBox.value = ""; chatBox.blur();
            } else if (event.key === "Tab") {
                event.preventDefault(); chatBox.blur(); G.emojiOpen = true; G.emojiFocus = G.emojiFocus || 0;
            }
        });
    }
    if (chatBox) {
        chatBox.style.display = ON ? "block" : "none";
        if (!ON && document.activeElement === chatBox) chatBox.blur();
    }
    G.chatBox = ON ? chatBox : null;
    const sendEmoji = (i) => {
        const pick = ON && ON.emojis[i];
        G.emojiOpen = false;
        if (pick) act("chat", { emoji: pick.name });
    };
    const onKeyDown = (event) => {
        if (!canvas.isConnected || typing(event) || event.ctrlKey || event.metaKey || event.altKey) return;
        const key = (event.key || "").toLowerCase();
        if (G.cut) return;
        if (ON && G.emojiOpen) {  // the emoji panel: arrows move the yellow frame, Enter sends, Esc or Tab closes
            const n = ON.emojis.length, cols = EMOJI_COLS, f = G.emojiFocus || 0;
            const moves = { arrowleft: -1, a: -1, arrowright: 1, d: 1, arrowup: -cols, w: -cols, arrowdown: cols, s: cols };
            if (key in moves) { event.preventDefault(); G.emojiFocus = (f + moves[key] + n) % n; return; }
            if (key === "enter" || key === " " || key === "e") { event.preventDefault(); if (!event.repeat) sendEmoji(f); return; }
            if (key === "escape" || key === "tab") { event.preventDefault(); G.emojiOpen = false; return; }
            G.emojiOpen = false;
        }
        if (ON && key === "enter" && !event.repeat) { event.preventDefault(); G.keys.length = 0; chatBox.focus(); return; }
        if (ON && key === "tab") { event.preventDefault(); G.emojiOpen = true; G.emojiFocus = G.emojiFocus || 0; return; }
        if (key in KEYS) {
            event.preventDefault();
            if (!G.keys.includes(key)) G.keys.push(key);
            G.target = null;
        } else if (key === "e" && !event.repeat) {
            if (G.nearBot) act("talk", { name: G.nearBot });  // next to a bot: talk to it
            else if (G.zone) act("interact");
        } else if (key === "i" && !event.repeat) {
            if (G.zone === 5) act("rules");
        } else if (key === "escape" && !event.repeat) {
            act("pause");
        }
    };
    const onKeyUp = (event) => {
        const i = G.keys.indexOf((event.key || "").toLowerCase());
        if (i >= 0) G.keys.splice(i, 1);
    };
    const onBlur = () => { G.keys.length = 0; };
    const onClick = (event) => {
        if (G.cut) return;
        const box = canvas.getBoundingClientRect();
        const sx = (event.clientX - box.left) * 960 / box.width, sy = (event.clientY - box.top) * 540 / box.height;
        const [px, py, pw, ph] = PAUSE_BOX;
        if (sx >= px && sx <= px + pw && sy >= py && sy <= py + ph) { act("pause"); return; }
        if (ON) {
            const cell = G.emojiOpen ? emojiAt(sx, sy) : -1;
            if (cell >= 0) { sendEmoji(cell); return; }
            if (inside(CHAT.emoji, sx, sy)) { G.emojiOpen = !G.emojiOpen; return; }
            if (inside(CHAT.send, sx, sy)) {
                const text = G.chatBox ? G.chatBox.value.trim() : "";
                if (text) { G.chatBox.value = ""; act("chat", { text }); } else if (G.chatBox) G.chatBox.focus();
                return;
            }
            if (inside(CHAT.bar, sx, sy) || (G.emojiOpen && inside(EMOJI_PANEL, sx, sy))) return;
            G.emojiOpen = false;
        }
        for (const hit of G.hits || []) {
            if (sx >= hit[0] && sx <= hit[2] && sy >= hit[1] && sy <= hit[3]) {
                if (hit[4] === "talk") act("talk", { name: G.nearBot });
                else act(hit[4] === "rules" ? "rules" : "interact");
                return;
            }
        }
        const bx = sx / data.scale, by = sy / data.scale;
        for (const spot of data.boxes) {
            const [l, t, r, b] = spot.box;
            if (bx >= l && bx <= r && by >= t && by <= b) { G.target = { x: spot.stand[0], y: spot.stand[1], face: "up" }; return; }
        }
        const map = G.maps[data.map];
        const [wl, wt, wr, wb] = G.objects[data.map].walk_area;
        G.target = { x: Math.max(wl, Math.min(wr, bx)), y: Math.max(wt, Math.min(wb, by)), face: null };
    };
    const onMove = (event) => {
        const box = canvas.getBoundingClientRect();
        const sx = (event.clientX - box.left) * 960 / box.width, sy = (event.clientY - box.top) * 540 / box.height;
        const [px, py, pw, ph] = PAUSE_BOX;
        G.hoverPause = sx >= px && sx <= px + pw && sy >= py && sy <= py + ph;
        G.hoverChat = !ON ? null : inside(CHAT.emoji, sx, sy) ? "emoji" : inside(CHAT.send, sx, sy) ? "send"
            : G.emojiOpen && emojiAt(sx, sy) >= 0 ? emojiAt(sx, sy) : null;
    };
    // Streamlit calls this function again on every run (new data), so the page listens only once and always
    // hands the event to the newest handlers (several listeners would each react: a key that toggles would undo).
    G.handlers = { keydown: onKeyDown, keyup: onKeyUp, blur: onBlur, click: onClick, move: onMove };
    if (!G.listening) {
        G.listening = true;
        document.addEventListener("keydown", (event) => G.handlers.keydown(event));
        document.addEventListener("keyup", (event) => G.handlers.keyup(event));
        window.addEventListener("blur", (event) => G.handlers.blur(event));
    }
    if (!canvas.dataset.listening) {
        canvas.dataset.listening = "1";
        canvas.addEventListener("click", (event) => G.handlers.click(event));
        canvas.addEventListener("mousemove", (event) => G.handlers.move(event));
    }

    if (!G.running) { G.running = true; G.last = now; requestAnimationFrame(frame); }

    // ================================================================ the loop
    function frame() {
        const c = G.canvas;
        if (!c || !c.isConnected) {  // the room left the page (pause menu, a table, online...)
            G.running = false; G.keys.length = 0;
            G.press = null;  // the press that took it away was handled: never send it again when the room is back
            return;
        }
        const t = performance.now() / 1000;
        const dt = Math.min(0.05, t - G.last);
        G.last = t;
        try { update(t, dt); draw(t); } catch (err) { console.error("arcade room:", err); }
        requestAnimationFrame(frame);
    }

    function free(x, y, ignoreBots = false) {
        // Can the player stand here? The floor map says where walls and furniture are; bots block too
        // unless ignoreBots (used to walk out from under a bot that shuffled onto the player).
        const d = G.data, map = G.maps[d.map];
        if (!map) return false;
        const ix = Math.round(x), iy = Math.round(y);
        if (ix < 0 || iy < 0 || ix >= map.w || iy >= map.h || map.blocked[iy * map.w + ix]) return false;
        if (ignoreBots) return true;
        const [bw, bh] = map.body;
        for (const b of Object.values(G.bots)) {
            const ox = (ix - b.x) / bw, oy = (iy - b.y) / bh;
            if (ox * ox + oy * oy <= 1) return false;
        }
        return true;
    }

    function lightSprite(S) {
        if (G.light) return G.light;
        const r = Math.round(30 * S * 1.35), c = document.createElement("canvas");
        c.width = 2 * r; c.height = Math.round(2 * r * 0.6);
        const x = c.getContext("2d");
        x.translate(r, c.height / 2); x.scale(1, 0.6);
        const g = x.createRadialGradient(0, 0, 0, 0, 0, r);
        g.addColorStop(0, "rgba(46, 38, 29, 1)"); g.addColorStop(0.5, "rgba(40, 33, 25, 1)"); g.addColorStop(1, "rgba(0, 0, 0, 1)");
        x.fillStyle = g; x.fillRect(-r, -r, 2 * r, 2 * r);
        return (G.light = c);
    }

    function vignetteSprite() {
        if (G.vignette) return G.vignette;
        const c = document.createElement("canvas");
        c.width = 960; c.height = 540;
        const x = c.getContext("2d");
        x.translate(480, 270); x.scale(480, 270);
        const v = x.createRadialGradient(0, 0, 0, 0, 0, 1.45);
        for (let i = 0; i <= 12; i++) {
            const rr = i / 12 * 1.45, edge = Math.min(1, Math.max(0, rr - 0.55) / 0.85);
            v.addColorStop(i / 12, `rgba(0, 0, 0, ${0.45 * edge * edge})`);
        }
        x.fillStyle = v; x.fillRect(-1, -1, 2, 2);
        return (G.vignette = c);
    }

    function inside(box, x, y) { return x >= box[0] && x <= box[0] + box[2] && y >= box[1] && y <= box[1] + box[3]; }

    function emojiAt(x, y) {  // which emoji of the open panel is under this point (-1: none)
        const O = G.data.online;
        if (!O) return -1;
        for (let i = 0; i < O.emojis.length; i++) if (inside(emojiCell(i), x, y)) return i;
        return -1;
    }

    function emojiCell(i) {
        const [x, y] = EMOJI_PANEL;
        return [x + 8 + (i % EMOJI_COLS) * 48, y + 8 + Math.floor(i / EMOJI_COLS) * 48, 46, 46];
    }

    function pixelBox(ctx, box, lit) {  // a dark box with a cyan edge, like the music and pause buttons
        const [x, y, w, h] = box;
        ctx.fillStyle = "rgba(13, 10, 31, 0.9)"; ctx.fillRect(x, y, w, h);
        ctx.strokeStyle = lit ? "#ffe94a" : "#3ad6ff"; ctx.lineWidth = 3;
        ctx.strokeRect(x + 1.5, y + 1.5, w - 3, h - 3);
    }

    function letters(colour) {  // the pixel font's letters in one colour, made once
        G.tinted = G.tinted || {};
        const font = G.data.online.font, atlas = img(font.img);
        if (!atlas) return null;
        if (G.tinted[colour] && G.tinted[colour].src === atlas) return G.tinted[colour].c;
        const c = document.createElement("canvas");
        c.width = atlas.width; c.height = atlas.height;
        const x = c.getContext("2d");
        x.drawImage(atlas, 0, 0);
        x.globalCompositeOperation = "source-in"; x.fillStyle = colour; x.fillRect(0, 0, c.width, c.height);
        G.tinted[colour] = { src: atlas, c };
        return c;
    }

    function typed(raw) {  // what was typed, as the game writes it: capitals, no accents, only letters the font has
        const glyphs = G.data.online.font.glyphs;
        return Array.from(raw.toUpperCase().normalize("NFD").replace(/[\u0300-\u036f]/g, ""))
            .filter((ch) => ch in glyphs).join("");
    }

    function chatBar(ctx, t) {
        const O = G.data.online, font = O.font, focused = document.activeElement === G.chatBox;
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        pixelBox(ctx, CHAT.emoji, G.emojiOpen || G.hoverChat === "emoji");
        const face = O.emojis.length && img(O.emojis[0].img);
        if (face) ctx.drawImage(face, CHAT.emoji[0] + (CHAT.emoji[2] - 30) / 2, CHAT.emoji[1] + (CHAT.emoji[3] - 30) / 2, 30, 30);
        pixelBox(ctx, CHAT.field, focused);
        pixelBox(ctx, CHAT.send, G.hoverChat === "send");
        const arrow = img(O.send);
        if (arrow) ctx.drawImage(arrow, CHAT.send[0] + (CHAT.send[2] - arrow.width) / 2 + 2, CHAT.send[1] + (CHAT.send[3] - arrow.height) / 2);
        let text = G.chatBox ? typed(G.chatBox.value) : "";
        const sheet = letters("#f3ead2"), room = CHAT.field[2] - 26;
        const width = (str) => Array.from(str).reduce((w, ch) => w + font.glyphs[ch][1] + 2, 0);
        while (text && width(text) > room) text = text.slice(1);  // a long message shows its end
        let cx = CHAT.field[0] + 12;
        const cy = CHAT.field[1] + Math.round((CHAT.field[3] - font.h) / 2) + 2;
        if (sheet) {
            for (const ch of text) {
                const m = font.glyphs[ch];
                ctx.drawImage(sheet, m[0], 0, m[1], font.h, cx, cy, m[1], font.h);
                cx += m[1] + 2;
            }
        }
        if (focused && Math.floor(t * 2.5) % 2 === 0) { ctx.fillStyle = "#ffe94a"; ctx.fillRect(cx + 1, cy, 3, font.h - 6); }
        if (G.emojiOpen) {
            pixelBox(ctx, EMOJI_PANEL, false);
            O.emojis.forEach((e, i) => {
                const [x, y, w, h] = emojiCell(i), im = img(e.img);
                if (i === G.emojiFocus || i === G.hoverChat) {
                    ctx.strokeStyle = "#ffe94a"; ctx.lineWidth = 3; ctx.strokeRect(x + 1.5, y + 1.5, w - 3, h - 3);
                }
                if (im) ctx.drawImage(im, x + (w - im.width) / 2, y + (h - im.height) / 2);
            });
        }
    }

    function pauseButton(ctx) {  // a small pause button in the corner, for the mouse (Esc does the same)
        const [x, y, w, h] = PAUSE_BOX;
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.fillStyle = "rgba(13, 10, 31, 0.82)"; ctx.fillRect(x, y, w, h);
        ctx.strokeStyle = G.hoverPause ? "#3ad6ff" : "rgba(58, 214, 255, 0.6)"; ctx.lineWidth = 3;
        ctx.strokeRect(x + 1.5, y + 1.5, w - 3, h - 3);
        ctx.fillStyle = "#f3ead2"; ctx.fillRect(x + 13, y + 10, 6, h - 20); ctx.fillRect(x + w - 19, y + 10, 6, h - 20);
    }

    function nearestFloor(x, y) {  // the closest spot where the player may stand (walls and furniture only)
        for (let r = 1; r <= 90; r++) {
            for (let dy = -r; dy <= r; dy++) {
                for (let dx = -r; dx <= r; dx++) {
                    if (Math.max(Math.abs(dx), Math.abs(dy)) === r && free(x + dx, y + dy, true)) return [x + dx, y + dy];
                }
            }
        }
        return null;
    }

    function zoneAt(x, y) {
        const map = G.maps[G.data.map];
        if (!map) return 0;
        return map.near[Math.round(y) * map.w + Math.round(x)] || 0;
    }

    function update(t, dt) {
        const d = G.data;
        for (const b of Object.values(G.bots)) {
            if (b.path) {  // along the planned walk, at a stroll
                let left = (t - b.pathT0) * d.botSpeed, done = true;
                for (let i = 0; i < b.path.length - 1; i++) {
                    const a = b.path[i], c = b.path[i + 1], piece = Math.hypot(c[0] - a[0], c[1] - a[1]);
                    if (piece > 0 && left <= piece) {
                        const s = left / piece;
                        b.x = a[0] + (c[0] - a[0]) * s; b.y = a[1] + (c[1] - a[1]) * s;
                        b.dir = Math.abs(c[0] - a[0]) > Math.abs(c[1] - a[1]) ? (c[0] > a[0] ? "right" : "left") : (c[1] > a[1] ? "down" : "up");
                        done = false;
                        break;
                    }
                    left -= piece;
                }
                b.walking = !done;
                if (done) {
                    const e = b.path[b.path.length - 1];
                    b.x = b.fx = b.tx = e[0]; b.y = b.fy = b.ty = e[1]; b.dur = 0; b.path = null; b.dir = b.goalDir || b.dir;
                }
                continue;
            }
            const p = b.dur ? Math.min(1, (t - b.t0) / b.dur) : 1;
            b.x = b.fx + (b.tx - b.fx) * p; b.y = b.fy + (b.ty - b.fy) * p;
            b.walking = p < 1;
        }
        G.nearBot = null;  // a bot close enough to talk to (E)
        if (!G.cut) {
            let best = Infinity;
            for (const [name, b] of Object.entries(G.bots)) {
                const gap = Math.hypot(b.x - G.x, (b.y - G.y) * 1.2);
                if (gap <= d.talkReach && gap < best) { best = gap; G.nearBot = name; }
            }
        }
        if (G.cut) { updateCut(t); return; }

        let vx = 0, vy = 0, faceKey = null;
        if (G.keys.length) {
            for (const key of G.keys) {
                const dir = KEYS[key];
                if (dir === "left") vx -= 1; if (dir === "right") vx += 1;
                if (dir === "up") vy -= 1; if (dir === "down") vy += 1;
            }
            faceKey = KEYS[G.keys[G.keys.length - 1]];
        } else if (G.target) {
            const dx = G.target.x - G.x, dy = G.target.y - G.y, dist = Math.hypot(dx, dy);
            if (dist < 0.8) {
                G.x = G.target.x; G.y = G.target.y;
                if (G.target.face) G.dir = G.target.face;
                G.target = null;
            } else { vx = dx / dist; vy = dy / dist; }
        }
        const length = Math.hypot(vx, vy);
        let moved = false;
        const map = G.maps[d.map];
        if (map && !free(G.x, G.y, true)) {  // never inside a wall or a table, never off the floor
            const inside = [Math.max(0, Math.min(map.w - 1, Math.round(G.x))), Math.max(0, Math.min(map.h - 1, Math.round(G.y)))];
            const spot = free(inside[0], inside[1], true) ? inside : nearestFloor(inside[0], inside[1]);
            if (spot) { [G.x, G.y] = spot; G.target = null; }
        }
        if (length > 0) {
            vx /= length; vy /= length;
            const step = d.speed * dt;
            const underBot = !free(G.x, G.y);  // a bot shuffled onto us: walk out, ignoring bots but not furniture
            const before = [G.x, G.y];
            if (vx && free(G.x + vx * step, G.y, underBot)) G.x += vx * step;
            if (vy && free(G.x, G.y + vy * step, underBot)) G.y += vy * step;
            moved = G.x !== before[0] || G.y !== before[1];
            if (faceKey) G.dir = faceKey;
            else if (moved) G.dir = Math.abs(vx) > Math.abs(vy) ? (vx > 0 ? "right" : "left") : (vy > 0 ? "down" : "up");
            if (!moved && G.target) G.target = null;  // something is in the way: stop there
        }
        G.walkClock = moved ? (G.walkClock || 0) + dt : 0;
        if (G.press && performance.now() - G.press.t > 700 && G.press.tries < 4) {  // not handled yet: again
            G.press.t = performance.now();
            G.press.tries += 1;
            G.send(G.press.kind, G.press.value);
        }
        if (d.online && moved && t - (G.posSent || 0) > (d.online.posEvery || 0.35)) { G.posSent = t; G.send("pos", here()); }
        const zone = zoneAt(G.x, G.y);
        if (zone !== G.zone && G.zone !== null) G.send("pos", here());
        if (G.moving && !moved && zone === G.zone) G.send("pos", here());
        G.zone = zone;
        G.moving = moved;
    }

    function updateCut(t) {
        const cut = G.cut, p = Math.min(1, (t - cut.t0) / Math.max(0.3, cut.walk));
        cut.pos = {};
        for (const [name, m] of Object.entries(cut.movers)) {
            const moving = Math.hypot(m[2] - m[0], m[3] - m[1]) > 1;
            const face = moving && p < 1 ? (Math.abs(m[2] - m[0]) > Math.abs(m[3] - m[1]) ? (m[2] > m[0] ? "right" : "left") : (m[3] > m[1] ? "down" : "up")) : m[4];
            cut.pos[name] = { x: m[0] + (m[2] - m[0]) * p, y: m[1] + (m[3] - m[1]) * p, dir: face, walking: moving && p < 1 };
        }
        const zoomTime = cut.zoom ? 0.5 : 0;
        cut.zoomP = Math.max(0, Math.min(1, (t - cut.t0 - Math.max(0.3, cut.walk)) / (zoomTime || 1)));
        cut.darkP = cut.zoom ? Math.max(0, Math.min(1, (t - cut.t0 - Math.max(0.3, cut.walk) - zoomTime) / 0.25)) : 0;
        if (!cut.sent && t - cut.t0 >= Math.max(0.3, cut.walk) + zoomTime + (cut.zoom ? 0.3 : 0.12)) {
            cut.sent = true;
            G.cutDone[cut.id] = true;
            G.send("cut_done", cut.id);
        }
    }

    // ================================================================ drawing
    function img(key) {
        const im = G.images[key];
        if (!im) { G.missing.add(key); return null; }
        return im.complete && im.naturalWidth ? im : null;
    }

    function draw(t) {
        const d = G.data, ctx = G.canvas.getContext("2d");
        G.missing = new Set();
        if (!G.maps[d.map]) G.missing.add(d.map);  // no floor map (the browser lost it): ask Python for it again
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.imageSmoothingEnabled = false;
        ctx.globalAlpha = 1;
        ctx.globalCompositeOperation = "source-over";
        const S = d.scale, tick = Math.floor(t * 2);

        if (G.cut && G.cut.zoom && G.cut.zoomP > 0) {  // zoom in on the table, like scenes.zoom
            const ease = G.cut.zoomP * G.cut.zoomP * (3 - 2 * G.cut.zoomP), f = 1 + 2 * ease;
            const w = 960 / f, h = 540 / f;
            const left = Math.max(0, Math.min(960 - w, G.cut.zoom[0] * S - w / 2));
            const top = Math.max(0, Math.min(540 - h, G.cut.zoom[1] * S - h / 2));
            ctx.setTransform(f, 0, 0, f, -left * f, -top * f);
        }

        const bg = img(d.bg);
        if (bg) ctx.drawImage(bg, 0, 0); else { ctx.fillStyle = "#0d0a1f"; ctx.fillRect(0, 0, 960, 540); }
        for (const p of d.alive || []) {  // the games on the screens, the blinking lights, the claw, the bunting
            const frame = img(p.frames[Math.floor(t * p.fps) % p.frames.length]);
            if (frame) ctx.drawImage(frame, p.x * S, p.y * S, p.w * S, p.h * S);
        }

        for (const mat of (d.online && d.online.mats) || []) {  // online: where the chairs of the tables are
            const im = img(mat.taken ? d.online.matImg.taken : d.online.matImg.free);
            if (im) ctx.drawImage(im, Math.round(mat.x * S - im.width / 2), Math.round(mat.y * S - im.height / 2));
        }

        // who stands where, then paint from back to front (tables first on a tie, as in hub_scene)
        const people = [];
        for (const actor of d.actors) {
            let x, y, dir, walking;
            if (G.cut && G.cut.pos && G.cut.pos[actor.name]) ({ x, y, dir, walking } = G.cut.pos[actor.name]);
            else if (actor.player) { x = G.x; y = G.y; dir = G.dir; walking = G.moving; }
            else { const b = G.bots[actor.name]; x = b.x; y = b.y; dir = b.dir; walking = b.walking; }
            people.push({ actor, x, y, dir, walking, sort: y, kind: 1 });
        }
        const things = people.concat(d.tables.map((tb) => ({ table: tb, sort: tb.sort, kind: 0 })));
        things.sort((a, b) => a.sort - b.sort || a.kind - b.kind);
        const zone = G.cut ? 0 : G.zone;
        for (const th of things) {
            if (th.table) {
                const tb = th.table, im = img(zone === tb.code ? tb.lit : tb.img);
                if (im) ctx.drawImage(im, tb.x, tb.y);
                continue;
            }
            const a = th.actor, sheet = img(a.sheet);
            if (!sheet) continue;
            const blinkNow = !th.walking && (tick + nameHash(a.name)) % 9 === 0;
            const pose = th.walking ? 1 + Math.floor((t * 7) % 2) : (blinkNow ? 3 : 0);
            const col = DIRS.indexOf(th.dir) * d.poses + pose, row = tick % a.rows;
            const [cw, ch] = d.cell;
            ctx.drawImage(sheet, col * cw, row * ch, cw, ch, Math.round(th.x * S) - d.feet[0], Math.round(th.y * S) - d.feet[1], cw, ch);
        }

        // a warm light follows the player (painted once, then just stamped: cheap on every computer)
        const me = people.find((p) => p.actor.player);
        if (me) {
            const light = lightSprite(S);
            ctx.save();
            ctx.globalCompositeOperation = "lighter";
            ctx.drawImage(light, Math.round(me.x * S - light.width / 2), Math.round((me.y - 6) * S - light.height / 2));
            ctx.restore();
        }

        // darker edges (the vignette of lighting.vignette), painted once
        ctx.drawImage(vignetteSprite(), 0, 0);

        const top = img(d.top);
        if (top) ctx.drawImage(top, 0, 0);
        for (const tb of d.tables) {
            if (zone === tb.code) { const lab = img(tb.label); if (lab) ctx.drawImage(lab, tb.lx, tb.ly); }
        }
        const hud = img(d.hud.img);
        if (hud && !G.cut) ctx.drawImage(hud, d.hud.x, d.hud.y);
        if (d.online) {  // the sign over each table (1/4, 2/4...) and the lobby's name plate
            for (const sign of d.online.signs) {
                const im = img(sign.img);
                if (im) ctx.drawImage(im, Math.round(sign.x - im.width / 2), Math.round(sign.y - im.height / 2));
            }
            const plate = d.online.plate && img(d.online.plate.img);
            if (plate && !G.cut) ctx.drawImage(plate, d.online.plate.x, d.online.plate.y);
        }

        // name tags, front-most last
        for (const p of people.slice().sort((a, b) => a.y - b.y)) {
            const tags = p.actor.tags, tag = img(tags[tick % tags.length]);
            if (tag) ctx.drawImage(tag, Math.round(p.x * S) - p.actor.tagAnchor[0], Math.round((p.y - 23) * S) - 4 - p.actor.tagAnchor[1]);
        }

        // what the player and a bot are saying (E next to a bot), above their name tags
        if (d.talk && G.talkT0 !== undefined) {
            const e = t - G.talkT0;
            for (const line of d.talk.lines) {
                if (e < line.at || e > line.at + line.dur) continue;
                const p = people.find((pp) => pp.actor.name === line.who), im = img(line.img);
                if (!p || !im) continue;
                const x = Math.max(4, Math.min(956 - line.w, Math.round(p.x * S - line.w / 2)));
                const y = Math.max(4, Math.round((p.y - 23) * S) - 8 - p.actor.tagAnchor[1] - line.h);
                ctx.drawImage(im, x, y);
            }
        }

        // online: what each player said last, above their name tag, for a few seconds
        if (d.online) {
            const latest = {};
            for (const say of d.online.says) if ((G.says[say.id] || 0) > t) latest[say.who] = say;
            for (const say of Object.values(latest)) {
                const p = people.find((pp) => pp.actor.name === say.who), im = img(say.img);
                if (!p || !im) continue;
                const x = Math.max(4, Math.min(956 - im.width, Math.round(p.x * S - im.width / 2)));
                const y = Math.max(4, Math.round((p.y - 23) * S) - 8 - p.actor.tagAnchor[1] - im.height);
                ctx.drawImage(im, x, y);
            }
        }

        // prompt bubbles next to the player
        G.hits = [];
        let items = (!G.cut && me && d.bubbles[String(zone)]) || [];
        if (!G.cut && me && G.nearBot && d.talkBubble) items = [{ ...d.talkBubble, action: "talk" }];
        if (items.length) {
            const onLeft = me.x > 200;
            let y = Math.round((me.y - 20) * S);
            for (const item of items) {
                let x0 = onLeft ? Math.round((me.x - 12) * S) - item.w : Math.round((me.x + 12) * S);
                x0 = Math.max(6, Math.min(960 - item.w - 12, x0));
                const im = img(item.img);
                if (im) ctx.drawImage(im, x0 - item.pad, y - item.pad);
                if (item.action) G.hits.push([x0, y, x0 + item.w, y + item.h, item.action]);
                y += item.h + 10;
            }
        }

        if (!G.cut) pauseButton(ctx);
        if (d.online) chatBar(ctx, t);
        if (G.cut && G.cut.darkP > 0) {  // the end of the zoom: fade to black, the table then fades in from black
            ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = `rgba(0, 0, 0, ${G.cut.darkP})`; ctx.fillRect(0, 0, 960, 540);
        }
        if (G.fadeStart !== undefined) {  // fade in from black when the room appears
            const a = 1 - (t - G.fadeStart) / 0.35;
            if (a > 0) { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = `rgba(0, 0, 0, ${a})`; ctx.fillRect(0, 0, 960, 540); }
        }

        if (G.missing.size && t - G.lastNeed > 1.5) {  // pictures the browser lost (a reload): ask again
            G.lastNeed = t;
            G.send("need", Array.from(G.missing));
        }
    }
}

const DIRS = ["down", "up", "left", "right"];
// The online chat bar at the bottom of the picture: emoji button, text box, send button; the emoji panel above it.
const CHAT = { bar: [270, 490, 420, 40], emoji: [270, 490, 42, 40], field: [318, 490, 324, 40], send: [648, 490, 42, 40] };
const EMOJI_COLS = 6;
const EMOJI_PANEL = [270, 374, 6 * 48 + 14, 2 * 48 + 14];
function nameHash(name) { let s = 0; for (const ch of name) s += ch.charCodeAt(0); return s; }
"""

_room = st.components.v2.component("arcade_room", css=ROOM_CSS, js=ROOM_JS)

EVENTS = ("pos", "interact", "rules", "pause", "cut_done", "need", "talk", "chat")


def mount(data: dict, key: str = "arcade_room"):
    """Show the room. Returns the component result: result.pos, result.interact, ... (None when not sent)."""
    callbacks = {f"on_{name}_change": (lambda: None) for name in EVENTS}
    return _room(key=key, data=data, width="stretch", **callbacks)
