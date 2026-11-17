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

import streamlit as st

from arcade import hubmap
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


def scene(sent: set, *, actors, coins, champ_locked, bubbles, player, cutscene=None, fade=0) -> dict:
    """Everything the browser needs for the room (data for ROOM_JS).

    actors   the six characters (state.hub_actors()); the player has player=True
    bubbles  spot -> list of prompts (see screens/hub._prompts)
    player   {"seq", "x", "y", "dir"}: where Python wants the player; the browser only jumps there when seq changes
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
    }
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

    data["boxes"] = [{"box": list(box), "stand": list(hubmap.SPOTS[spot]["stand"])}
                     for spot, box in hubmap.CLICK_BOXES.items()]
    data["cutscene"] = cutscene
    data["assets"] = s.assets
    return data


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
canvas.arcade-room {
    display: block; width: 100%; height: auto; aspect-ratio: 16 / 9;
    image-rendering: pixelated; cursor: pointer; border-radius: 14px;
    box-shadow: 0 0 0 2px rgba(58, 214, 255, .55), 0 0 24px rgba(58, 214, 255, .35), 0 0 60px rgba(255, 79, 163, .25);
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
    if (!canvas) {
        canvas = document.createElement("canvas");
        canvas.className = "arcade-room";
        canvas.width = 960;
        canvas.height = 540;
        parentElement.appendChild(canvas);
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

    // ---- bots: glide to their new spot instead of jumping
    const now = performance.now() / 1000;
    for (const actor of data.actors) {
        if (actor.player) continue;
        const b = G.bots[actor.name];
        if (!b) {
            G.bots[actor.name] = { x: actor.x, y: actor.y, fx: actor.x, fy: actor.y, tx: actor.x, ty: actor.y, t0: 0, dur: 0, dir: actor.dir };
        } else if (b.tx !== actor.x || b.ty !== actor.y) {
            b.fx = b.x; b.fy = b.y; b.tx = actor.x; b.ty = actor.y; b.t0 = now;
            b.dur = Math.max(0.15, Math.hypot(b.tx - b.fx, b.ty - b.fy) / 40);
            b.dir = actor.dir;
        } else {
            b.dir = actor.dir;
        }
    }

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
    const onKeyDown = (event) => {
        if (!canvas.isConnected || typing(event) || event.ctrlKey || event.metaKey || event.altKey) return;
        const key = (event.key || "").toLowerCase();
        if (G.cut) return;
        if (key in KEYS) {
            event.preventDefault();
            if (!G.keys.includes(key)) G.keys.push(key);
            G.target = null;
        } else if (key === "e" && !event.repeat) {
            if (G.zone) setTriggerValue("interact", here());
        } else if (key === "i" && !event.repeat) {
            if (G.zone === 5) setTriggerValue("rules", here());
        } else if (key === "escape" && !event.repeat) {
            setTriggerValue("pause", here());
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
        for (const hit of G.hits || []) {
            if (sx >= hit[0] && sx <= hit[2] && sy >= hit[1] && sy <= hit[3]) {
                setTriggerValue(hit[4] === "rules" ? "rules" : "interact", here());
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
    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("keyup", onKeyUp);
    window.addEventListener("blur", onBlur);
    canvas.addEventListener("click", onClick);

    if (!G.running) { G.running = true; G.last = now; requestAnimationFrame(frame); }

    return () => {
        document.removeEventListener("keydown", onKeyDown);
        document.removeEventListener("keyup", onKeyUp);
        window.removeEventListener("blur", onBlur);
        canvas.removeEventListener("click", onClick);
    };

    // ================================================================ the loop
    function frame() {
        const c = G.canvas;
        if (!c || !c.isConnected) { G.running = false; G.keys.length = 0; return; }
        const t = performance.now() / 1000;
        const dt = Math.min(0.05, t - G.last);
        G.last = t;
        try { update(t, dt); draw(t); } catch (err) { console.error("arcade room:", err); }
        requestAnimationFrame(frame);
    }

    function free(x, y) {
        const d = G.data, map = G.maps[d.map];
        if (!map) return false;
        const ix = Math.round(x), iy = Math.round(y);
        if (ix < 0 || iy < 0 || ix >= map.w || iy >= map.h || map.blocked[iy * map.w + ix]) return false;
        const [bw, bh] = map.body;
        for (const b of Object.values(G.bots)) {
            const ox = (ix - b.tx) / bw, oy = (iy - b.ty) / bh;
            if (ox * ox + oy * oy <= 1) return false;
        }
        return true;
    }

    function zoneAt(x, y) {
        const map = G.maps[G.data.map];
        if (!map) return 0;
        return map.near[Math.round(y) * map.w + Math.round(x)] || 0;
    }

    function update(t, dt) {
        const d = G.data;
        for (const b of Object.values(G.bots)) {
            const p = b.dur ? Math.min(1, (t - b.t0) / b.dur) : 1;
            b.x = b.fx + (b.tx - b.fx) * p; b.y = b.fy + (b.ty - b.fy) * p;
            b.walking = p < 1;
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
        if (length > 0) {
            vx /= length; vy /= length;
            const step = d.speed * dt;
            const stuck = !free(G.x, G.y);  // a bot shuffled onto us: let the player walk out
            const before = [G.x, G.y];
            if (vx && (stuck || free(G.x + vx * step, G.y))) G.x += vx * step;
            if (vy && (stuck || free(G.x, G.y + vy * step))) G.y += vy * step;
            moved = G.x !== before[0] || G.y !== before[1];
            if (faceKey) G.dir = faceKey;
            else if (moved) G.dir = Math.abs(vx) > Math.abs(vy) ? (vx > 0 ? "right" : "left") : (vy > 0 ? "down" : "up");
            if (!moved && G.target) G.target = null;  // something is in the way: stop there
        }
        G.walkClock = moved ? (G.walkClock || 0) + dt : 0;
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
        if (!cut.sent && t - cut.t0 >= Math.max(0.3, cut.walk) + zoomTime + 0.12) {
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

        // a warm light follows the player
        const me = people.find((p) => p.actor.player);
        if (me) {
            ctx.save();
            ctx.globalCompositeOperation = "lighter";
            ctx.translate(me.x * S, (me.y - 6) * S);
            ctx.scale(1, 0.6);
            const r = 30 * S * 1.35, g = ctx.createRadialGradient(0, 0, 0, 0, 0, r);
            g.addColorStop(0, "rgba(46, 38, 29, 1)");
            g.addColorStop(0.5, "rgba(40, 33, 25, 1)");
            g.addColorStop(1, "rgba(0, 0, 0, 1)");
            ctx.fillStyle = g;
            ctx.fillRect(-r, -r, 2 * r, 2 * r);
            ctx.restore();
        }

        // darker edges (the vignette of lighting.vignette)
        ctx.save();
        ctx.translate(480, 270);
        ctx.scale(480, 270);
        const v = ctx.createRadialGradient(0, 0, 0, 0, 0, 1.45);
        for (let i = 0; i <= 12; i++) {
            const rr = i / 12 * 1.45, edge = Math.min(1, Math.max(0, rr - 0.55) / 0.85);
            v.addColorStop(i / 12, `rgba(0, 0, 0, ${0.45 * edge * edge})`);
        }
        ctx.fillStyle = v;
        ctx.fillRect(-1, -1, 2, 2);
        ctx.restore();

        const top = img(d.top);
        if (top) ctx.drawImage(top, 0, 0);
        for (const tb of d.tables) {
            if (zone === tb.code) { const lab = img(tb.label); if (lab) ctx.drawImage(lab, tb.lx, tb.ly); }
        }
        const hud = img(d.hud.img);
        if (hud && !G.cut) ctx.drawImage(hud, d.hud.x, d.hud.y);

        // name tags, front-most last
        for (const p of people.slice().sort((a, b) => a.y - b.y)) {
            const tags = p.actor.tags, tag = img(tags[tick % tags.length]);
            if (tag) ctx.drawImage(tag, Math.round(p.x * S) - p.actor.tagAnchor[0], Math.round((p.y - 23) * S) - 4 - p.actor.tagAnchor[1]);
        }

        // prompt bubbles next to the player
        G.hits = [];
        const items = (!G.cut && me && d.bubbles[String(zone)]) || [];
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
function nameHash(name) { let s = 0; for (const ch of name) s += ch.charCodeAt(0); return s; }
"""

_room = st.components.v2.component("arcade_room", css=ROOM_CSS, js=ROOM_JS)

EVENTS = ("pos", "interact", "rules", "pause", "cut_done", "need")


def mount(data: dict, key: str = "arcade_room"):
    """Show the room. Returns the component result: result.pos, result.interact, ... (None when not sent)."""
    callbacks = {f"on_{name}_change": (lambda: None) for name in EVENTS}
    return _room(key=key, data=data, width="stretch", **callbacks)
