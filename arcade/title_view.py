"""The title screen, drawn in the browser: a smooth animation and a menu that is part of the game.

How it works (like the room, arcade/room.py)
---------------------------------------------
Python paints the pieces once (arcade/art/title_layers.py and the bots' sprite sheets) and sends each
picture to the browser once per session. TITLE_JS animates them 60 times a second (twinkling stars, the
floor grid sliding towards you, the five regulars dancing) and draws the menu on top, in the game's pixel
font, like in a real game:

    CREATE A CHARACTER / I HAVE AN ACCOUNT / HOW TO PLAY  ->  name and PIN boxes  ->  (a new player makes their
    character first: screens/create.py)  ->  PLAY OFFLINE / PLAY ONLINE / HOW TO PLAY / LOG OUT
    PLAY ONLINE  ->  the online box: CREATE LOBBY / JOIN A LOBBY / PLAY OFFLINE / GO BACK  ->  JOIN: the code box
Everything before a room is this one animated screen: changing step only changes what is drawn (no new picture, no
black, the stars and the dancers keep going).

Arrow keys (or W S) choose, Enter confirms, Esc goes back; the mouse works too. The browser only tells
Python two things (read them from the value mount() returns):

    howto    HOW TO PLAY was chosen: {n}
    submit   the name and PIN were sent: {mode: "new" or "login", name, pin, pin2, n}
    play     a signed-in player chose PLAY OFFLINE: {where: "offline", n}
    lobby    CREATE LOBBY or JOIN with a code: {action: "create"} or {action: "join", code}, with n
    logout   a signed-in player chose LOG OUT: {n}
    entered  the camera finished flying into the arcade after PLAY OFFLINE (or into the lobby's room): {n}
    need     the browser is missing some pictures (it reloaded): their keys

It starts like an arcade machine waiting for a player: the logo drops in and PRESS ENTER blinks. Clicking a
bot (or pressing 1 to 4) makes it jump and say something. The player with the most championships, if any,
dances on a gold podium with a crown, so the screen changes as people play.

Every event carries a number n. Python handles each number once and sends back the last one it handled
(ack), with an error message if the sign-in was refused; the browser then shows the message.
"""

from __future__ import annotations

from functools import lru_cache

import streamlit as st

from arcade import bots, catalog
from arcade.accounts import PIN_MAX, PIN_MIN
from arcade.art import room_layers, title_layers
from arcade.config import NAME_MAX, SCALE
from arcade.logic.lobby import CODE_LENGTH, CODE_LETTERS
from arcade.room import Scene, _look_key, _tag_key

FEET_Y = 176 * SCALE  # where the bots stand on the big picture
BOT_X = (100 * SCALE, 140 * SCALE, 180 * SCALE, 220 * SCALE)  # one per bot, easiest on the left
SPOT_COLOURS = ("#3ad6ff", "#ff4fa3", "#ffe94a", "#b07aff")


@lru_cache(maxsize=16)
def _sheet(look: tuple):
    return room_layers.sheet(look)


LINES = ["LET'S PLAY!", "I NEVER LOSE", "UNO!", "BEAT ME!", "NICE SKIN!", "ONE MORE?",
         "STOP POKING!", "I'M ON FIRE!", "GG!", "PICK ME!"]  # short: the bubble covers the bot's name tag
CHAMPION_X = 284 * SCALE  # the arcade's best player dances here, on a little gold podium


def _dancer(s: Scene, look: tuple, name: str, spec) -> dict:
    sheet, rows = _sheet(look)
    frames, anchor = room_layers.tag_frames(name, _tag_key(spec))
    tag_base = f"tag:{name}:{_tag_key(spec)}"
    return {"rows": rows, "anchor": list(anchor), "sheet": s.use(_look_key(look), lambda img=sheet: img),
            "tags": [s.use(f"{tag_base}:{k}", lambda img=frame: img) for k, frame in enumerate(frames)]}


def scene(sent: set, *, error: dict | None = None, ack: int = 0, last_name: str = "", champion: dict | None = None,
          enter: int = 0, signed_in: str = "", me: dict | None = None, start: dict | None = None,
          notice: dict | None = None) -> dict:
    """Everything the browser needs for the title screen (data for TITLE_JS).

    champion: {"name", "look", "tag", "titles"} of the arcade's best player (it changes as people play), or None.
    enter: the number of a PLAY OFFLINE Python accepted: the browser flies into the arcade, then sends "entered".
    signed_in: the name of the player who has signed in (the menu is then PLAY OFFLINE / PLAY ONLINE...), or "".
    me: the signed-in player's card ({"name", "look", "tag"}), who dances in the online box.
    start: {"step", "n"}: open on this step (a new n each time), e.g. the online box from the pause menu.
    notice: {"text", "n"}: a message for the online box (for example "That lobby has closed.").
    """
    s = Scene(sent)
    atlas, glyphs, height = title_layers.font_atlas()
    data = {
        "bg": s.use("title:bg", title_layers.backdrop),
        "cabinets": s.use("title:cabinets", title_layers.cabinets),
        "logo": s.use("title:logo", title_layers.logo),
        "logoSmall": s.use("title:logo-small", lambda: title_layers.logo(small=True)),
        "font": {"img": s.use("title:font", lambda: atlas), "glyphs": glyphs, "h": height},
        "stars": title_layers.stars(),
        "horizon": title_layers.HORIZON * SCALE,
        "cell": [room_layers.CELL_W * SCALE, room_layers.CELL_H * SCALE],
        "feet": [room_layers.FEET[0] * SCALE, room_layers.FEET[1] * SCALE],
        "poses": room_layers.POSES, "dirs": list(room_layers.DIRECTIONS),
        "feetY": FEET_Y, "bots": [],
        "error": error, "ack": ack, "lastName": last_name, "enter": enter, "lines": LINES, "signedIn": signed_in,
        "nameMax": NAME_MAX, "pinMin": PIN_MIN, "pinMax": PIN_MAX,
        "codeLetters": CODE_LETTERS, "codeLength": CODE_LENGTH, "start": start, "notice": notice, "me": None,
    }
    for i, bot in enumerate(bots.BOTS):
        dancer = _dancer(s, bots.look(bot), bot["name"], catalog.spec_for("name", bot["tag"]))
        data["bots"].append({"x": BOT_X[i], "spot": SPOT_COLOURS[i], **dancer})
    if me:
        data["me"] = _dancer(s, me["look"], me["name"], me.get("tag"))
    data["champion"] = None
    if champion:
        data["champion"] = {"x": CHAMPION_X, "titles": champion["titles"], "spot": "#ffd84a",
                            **_dancer(s, champion["look"], champion["name"], champion["tag"])}
    data["assets"] = s.assets
    return data


TITLE_CSS = """
canvas.arcade-title {
    display: block; width: 100%; height: auto; aspect-ratio: 16 / 9;
    image-rendering: pixelated; border-radius: 10px; outline: none;
}
"""

TITLE_JS = r"""
export default function (component) {
    const { data, setTriggerValue, parentElement } = component;
    const G = window.__arcadeTitle || (window.__arcadeTitle = {
        images: {}, tinted: {}, step: "menu", sel: 0, focus: 0,
        fields: { name: "", pin: "", pin2: "" }, error: "", pending: null, pressN: 0, lastNeed: 0,
        running: false, hover: null, pokes: {}, attractDone: false, flyT0: null, enterSeen: 0, introT0: null,
        code: "", pad: 0, startSeen: 0, noticeSeen: 0,
    });
    const sfx = (name) => { const A = window.__arcadeAudio; if (A && A.effect) A.effect(name); };
    G.data = data;
    G.send = setTriggerValue;
    if (!G.fields.name && data.lastName) G.fields.name = data.lastName;
    for (const [key, value] of Object.entries(data.assets || {})) {
        if (typeof value === "string") { const im = new Image(); im.src = value; G.images[key] = im; }
    }
    // Python's answer to the last name + PIN sent
    G.pressN = Math.max(G.pressN, data.ack || 0);
    if (G.pending && (data.ack || 0) >= G.pending.n) {
        const refused = data.error && data.error.n === G.pending.n;
        G.error = refused ? String(data.error.text).toUpperCase() : "";
        if (refused && G.pending.kind === "submit") { G.fields.pin = ""; G.fields.pin2 = ""; G.focus = 1; }
        G.pending = null;
    }

    let canvas = parentElement.querySelector("canvas.arcade-title");
    if (!canvas) {  // the title screen has just appeared: start on the first menu
        canvas = document.createElement("canvas");
        canvas.className = "arcade-title";
        canvas.width = 960; canvas.height = 540;
        parentElement.appendChild(canvas);
        G.step = "menu"; G.sel = 0; G.focus = 0; G.error = ""; G.pending = null;
        G.fields.pin = ""; G.fields.pin2 = ""; G.flyT0 = null;
        if (!G.attractDone) G.introT0 = performance.now() / 1000;
    }
    G.canvas = canvas;
    const SIGNED = ["mode", "online", "join"];  // the steps of a signed-in player
    if (data.start && data.start.n !== G.startSeen) {  // opened on a given step (the online box, from the pause menu)
        G.startSeen = data.start.n; G.step = data.start.step; G.sel = 0; G.pad = 0; G.code = ""; G.error = "";
        G.attractDone = true;
    }
    if (data.signedIn && !SIGNED.includes(G.step)) {  // signed in (or a new character made): now offline or online
        G.step = "mode"; G.sel = 0; G.error = ""; G.attractDone = true; G.pending = null;
    } else if (!data.signedIn && SIGNED.includes(G.step)) {  // logged out
        G.step = "menu"; G.sel = 0;
    }
    if (data.notice && data.notice.n !== G.noticeSeen) { G.noticeSeen = data.notice.n; G.error = String(data.notice.text).toUpperCase(); }
    if (data.enter && data.enter !== G.enterSeen) {  // Python accepted the sign-in: fly into the arcade
        G.enterSeen = data.enter; G.flyT0 = performance.now() / 1000; sfx("start");
    }

    // ---------------------------------------------------------------- what the menus do
    const MENUS = {  // first who you are, then where you play
        menu: [["CREATE A CHARACTER", () => go("new")], ["I HAVE AN ACCOUNT", () => go("login")],
               ["HOW TO PLAY", () => act("howto", {})]],
        mode: [["PLAY OFFLINE", () => act("play", { where: "offline" })], ["PLAY ONLINE", () => go("online")],
               ["HOW TO PLAY", () => act("howto", {})], ["LOG OUT", () => act("logout", {})]],
        online: [["CREATE LOBBY", () => lobby({ action: "create" })], ["JOIN A LOBBY", () => go("join")],
                 ["PLAY OFFLINE", () => act("play", { where: "offline" })], ["GO BACK", () => go("mode", 1)]],
    };
    const PAD_ACTIONS = ["DEL", "JOIN", "BACK"];
    const padKeys = () => [...data.codeLetters, ...PAD_ACTIONS];
    function lobby(value) {  // CREATE LOBBY or JOIN: once (a second press waits for Python's answer)
        if (G.pending) return;
        if (value.action === "join" && G.code.length !== data.codeLength) { G.error = `A CODE HAS ${data.codeLength} LETTERS`; return; }
        G.error = "";
        act("lobby", value);
        G.pending = G.lastPress;
    }
    function padPress(label) {
        if (label === "DEL") { G.code = G.code.slice(0, -1); G.error = ""; sfx("blip"); }
        else if (label === "JOIN") lobby({ action: "join", code: G.code });
        else if (label === "BACK") go("online", 1);
        else if (G.code.length < data.codeLength) {
            G.code += label; G.error = ""; sfx("blip");
            if (G.code.length === data.codeLength) G.pad = data.codeLetters.length + 1;  // the code is whole: on JOIN
        }
    }
    const formItems = () => G.step === "new" ? ["name", "pin", "pin2", "submit", "back"] : ["name", "pin", "submit", "back"];
    const inForm = () => G.step === "new" || G.step === "login";
    const inBox = () => inForm() || G.step === "online" || G.step === "join";  // a box over the title (no logo, no pokes)
    function go(step, sel = 0) {
        G.step = step; G.sel = sel; G.focus = 0; G.error = ""; G.pad = 0;
        if (step === "join") G.code = "";
        G.fields.pin = ""; G.fields.pin2 = "";
        sfx("coin");
    }
    function poke(i) {  // a bot jumps, spins and says something
        if (!G.data.bots[i]) return;
        const lines = G.data.lines;
        G.pokes[i] = { t0: performance.now() / 1000, line: lines[Math.floor(Math.random() * lines.length)] };
        sfx("blip");
    }
    function start() { G.attractDone = true; sfx("coin"); }  // PRESS ENTER was pressed
    function act(kind, value) {  // numbered, and sent again until Python has handled it
        G.pressN += 1;
        const press = { kind, value: { ...value, n: G.pressN }, t: performance.now(), tries: 1, n: G.pressN };
        if (kind === "submit") G.pending = press;
        G.lastPress = press;
        G.send(kind, press.value);
    }
    function submit() {
        if (G.pending) return;
        const f = G.fields;
        if (!f.name.trim()) { G.error = "TYPE YOUR NAME"; G.focus = 0; return; }
        if (f.pin.length < data.pinMin) {
            G.error = `THE PIN MUST BE ${data.pinMin} TO ${data.pinMax} DIGITS`; f.pin = ""; f.pin2 = ""; G.focus = 1; return;
        }
        if (G.step === "new" && f.pin2 !== f.pin) { G.error = "THE TWO PINS ARE NOT THE SAME"; G.fields.pin2 = ""; G.focus = 2; return; }
        G.error = "";
        act("submit", { mode: G.step, name: f.name, pin: f.pin, pin2: G.step === "new" ? f.pin2 : "" });
    }
    function activateFormItem(item) {
        if (item === "submit") submit();
        else if (item === "back") go("menu");
        else G.focus = Math.min(G.focus + 1, formItems().length - 1);
    }

    // ---------------------------------------------------------------- keys and mouse
    const stop = (e) => { e.preventDefault(); e.stopPropagation(); };
    const onKey = (e) => {
        if (!G.canvas || !G.canvas.isConnected || e.ctrlKey || e.metaKey || e.altKey) return;
        const key = e.key || "", k = key.toLowerCase();
        if (G.flyT0) return stop(e);  // flying into the arcade
        if (!inBox() && /^[1-9]$/.test(key) && Number(key) <= d.bots.length) { poke(Number(key) - 1); return stop(e); }
        if (!G.attractDone) {
            if (k === "enter" || k === " ") { start(); return stop(e); }
            return;
        }
        if (inForm()) {
            const items = formItems(), item = items[G.focus];
            if (k === "escape") { go("menu"); return stop(e); }
            if (k === "arrowdown" || (k === "tab" && !e.shiftKey)) { G.focus = (G.focus + 1) % items.length; sfx("blip"); return stop(e); }
            if (k === "arrowup" || (k === "tab" && e.shiftKey)) { G.focus = (G.focus + items.length - 1) % items.length; sfx("blip"); return stop(e); }
            if (k === "enter") {
                if (item === "pin2" || (item === "pin" && G.step === "login")) submit(); else activateFormItem(item);
                return stop(e);
            }
            if (item === "name" || item === "pin" || item === "pin2") {
                const field = item;
                if (k === "backspace") { G.fields[field] = G.fields[field].slice(0, -1); return stop(e); }
                if (key.length === 1) {  // a letter typed into a box never reaches the game's other keys (F, H...)
                    if (field === "name" && /[a-z0-9 _-]/i.test(key) && G.fields.name.length < data.nameMax) G.fields.name += key.toUpperCase();
                    if (field !== "name" && /[0-9]/.test(key) && G.fields[field].length < data.pinMax) G.fields[field] += key;
                    G.error = "";
                    return stop(e);
                }
            }
            return;
        }
        if (G.step === "join") {  // type the code (or move the yellow frame over the letters), Enter, Esc
            const keys = padKeys(), cols = 5, n = data.codeLetters.length;
            if (k === "escape") { go("online", 1); return stop(e); }
            if (k === "backspace") { padPress("DEL"); return stop(e); }
            if (k === "enter" && G.code.length === data.codeLength) { lobby({ action: "join", code: G.code }); return stop(e); }
            if (k === "enter" || k === " ") { padPress(keys[G.pad]); return stop(e); }
            const moves = { arrowleft: -1, arrowright: 1, arrowup: -cols, arrowdown: cols };
            if (k in moves) {
                let next = G.pad + moves[k];
                if (G.pad >= n && (k === "arrowup")) next = n - cols + Math.min(cols - 1, (G.pad - n) * 2);
                else if (G.pad < n && next >= n) next = n + Math.min(2, Math.floor((G.pad % cols) / 2));
                G.pad = Math.max(0, Math.min(keys.length - 1, next)); sfx("blip"); return stop(e);
            }
            if (key.length === 1 && data.codeLetters.includes(key.toUpperCase())) { padPress(key.toUpperCase()); return stop(e); }
            if (key.length === 1) return stop(e);  // (other letters do nothing here, not even the game's keys)
            return;
        }
        const items = MENUS[G.step];
        if (k === "escape" && G.step === "online") { go("mode", 1); return stop(e); }
        if (k === "arrowdown" || k === "s") { G.sel = (G.sel + 1) % items.length; sfx("blip"); return stop(e); }
        if (k === "arrowup" || k === "w") { G.sel = (G.sel + items.length - 1) % items.length; sfx("blip"); return stop(e); }
        if (k === "enter" || k === " ") { items[G.sel][1](); return stop(e); }
        if (k === "h" && G.step !== "online") { act("howto", {}); return stop(e); }
    };
    const where = (e) => {
        const box = canvas.getBoundingClientRect();
        return [(e.clientX - box.left) * 960 / box.width, (e.clientY - box.top) * 540 / box.height];
    };
    const hitAt = (x, y) => {  // a menu item or box wins over a bot standing behind it
        const inside = (h) => x >= h[0] && x <= h[2] && y >= h[1] && y <= h[3], hits = G.hits || [];
        return hits.find((h) => h[5] !== "bot" && inside(h)) || hits.find(inside);
    };
    const onMove = (e) => {
        const hit = hitAt(...where(e));
        canvas.style.cursor = hit || !G.attractDone ? "pointer" : "default";
        if (!hit || hit[5] === "bot") return;
        if (inForm()) { if (hit[5] !== "field") G.focus = hit[4]; }
        else if (G.step === "join") { if (G.pad !== hit[4]) { G.pad = hit[4]; sfx("blip"); } }
        else if (G.sel !== hit[4]) { G.sel = hit[4]; sfx("blip"); }
    };
    const onClick = (e) => {
        if (G.flyT0) return;
        const hit = hitAt(...where(e));
        if (hit && hit[5] === "bot") return poke(hit[4]);
        if (!G.attractDone) return start();
        if (!hit) return;
        if (inForm()) { G.focus = hit[4]; if (hit[5] !== "field") activateFormItem(formItems()[hit[4]]); }
        else if (G.step === "join") { G.pad = hit[4]; padPress(padKeys()[hit[4]]); }
        else { G.sel = hit[4]; MENUS[G.step][hit[4]][1](); }
    };
    // Listeners are added once; they always call the newest handlers (so a key is never handled twice).
    G.onKey = onKey; G.onMove = onMove; G.onClick = onClick;
    if (!G.keyListener) {
        G.keyListener = (e) => G.onKey(e);
        window.addEventListener("keydown", G.keyListener, true);  // before the page's other key listeners
    }
    if (!canvas.wired) {
        canvas.wired = true;
        canvas.addEventListener("mousemove", (e) => G.onMove(e));
        canvas.addEventListener("click", (e) => G.onClick(e));
    }
    if (!G.running) { G.running = true; requestAnimationFrame(frame); }

    // ---------------------------------------------------------------- drawing
    function img(key) {
        const im = G.images[key];
        if (im && im.complete && im.naturalWidth) return im;
        G.missing.add(key);
        return null;
    }
    function tinted(colour) {  // the letters in one colour, made once
        if (G.tinted[colour]) return G.tinted[colour];
        const atlas = img(G.data.font.img);
        if (!atlas) return null;
        const c = document.createElement("canvas");
        c.width = atlas.width; c.height = atlas.height;
        const x = c.getContext("2d");
        x.drawImage(atlas, 0, 0);
        x.globalCompositeOperation = "source-in";
        x.fillStyle = colour; x.fillRect(0, 0, c.width, c.height);
        return (G.tinted[colour] = c);
    }
    function textWidth(text, s) {
        const g = G.data.font.glyphs;
        let w = 0;
        for (const ch of text) { const m = g[ch] || g[" "]; w += (m[1] + 2) * s; }
        return Math.max(0, w - 2 * s);
    }
    function text(ctx, str, x, y, s, colour, align = "center", outline = 3) {
        str = String(str).toUpperCase();
        const g = G.data.font.glyphs, h = G.data.font.h;
        const front = tinted(colour), back = tinted("#16122b");
        if (!front || !back) return;
        let left = align === "center" ? x - textWidth(str, s) / 2 : align === "right" ? x - textWidth(str, s) : x;
        left = Math.round(left);
        const paint = (sheet, dx, dy) => {
            let cx = left;
            for (const ch of str) {
                const m = g[ch] || g[" "];
                ctx.drawImage(sheet, m[0], 0, m[1], h, cx + dx, y + dy, m[1] * s, h * s);
                cx += (m[1] + 2) * s;
            }
        };
        if (outline) for (const [dx, dy] of [[-1, 0], [1, 0], [0, -1], [0, 1], [-1, -1], [1, -1], [-1, 1], [1, 1], [0, 2], [1, 2], [-1, 2]])
            paint(back, dx * outline, dy * outline);
        paint(front, 0, 0);
    }
    function spotSprite(colour) {
        const key = "spot" + colour;
        if (G.tinted[key]) return G.tinted[key];
        const c = document.createElement("canvas");
        c.width = 160; c.height = 60;
        const x = c.getContext("2d");
        x.translate(80, 30); x.scale(1, 0.36);
        const g = x.createRadialGradient(0, 0, 0, 0, 0, 80);
        g.addColorStop(0, colour); g.addColorStop(1, "rgba(0,0,0,0)");
        x.globalAlpha = 0.45; x.fillStyle = g; x.fillRect(-80, -80, 160, 160);
        return (G.tinted[key] = c);
    }
    function vignette() {
        if (G.vignette) return G.vignette;
        const c = document.createElement("canvas");
        c.width = 960; c.height = 540;
        const x = c.getContext("2d");
        x.translate(480, 270); x.scale(480, 270);
        const v = x.createRadialGradient(0, 0, 0, 0, 0, 1.45);
        for (let i = 0; i <= 12; i++) {
            const rr = i / 12 * 1.45, edge = Math.min(1, Math.max(0, rr - 0.55) / 0.85);
            v.addColorStop(i / 12, `rgba(0, 0, 0, ${0.4 * edge * edge})`);
        }
        x.fillStyle = v; x.fillRect(-1, -1, 2, 2);
        return (G.vignette = c);
    }

    function frame(now) {
        if (!G.canvas || !G.canvas.isConnected) { G.running = false; return; }
        const t = now / 1000;
        if (G.lastPress && G.lastPress.n > (G.data.ack || 0) && now - G.lastPress.t > 1500 && G.lastPress.tries < 4) {
            G.lastPress.t = now; G.lastPress.tries += 1; G.send(G.lastPress.kind, G.lastPress.value);  // not handled yet
        }
        draw(t);
        if (G.flyT0 && t - G.flyT0 > 1.0 && !G.flySent) { G.flySent = G.enterSeen; act("entered", {}); }
        if (G.flySent && G.flySent !== G.enterSeen) G.flySent = 0;
        requestAnimationFrame(frame);
    }

    function draw(t) {
        const d = G.data, ctx = G.canvas.getContext("2d");
        G.missing = new Set();
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.imageSmoothingEnabled = false;
        ctx.globalCompositeOperation = "source-over";
        ctx.fillStyle = "#000"; ctx.fillRect(0, 0, 960, 540);
        let fly = 0;  // 0..1 while flying into the arcade after signing in
        if (G.flyT0) {
            fly = Math.min(1, (t - G.flyT0) / 1.0);
            const zoom = 1 + 6 * fly * fly * fly;
            ctx.setTransform(zoom, 0, 0, zoom, 480 * (1 - zoom), d.horizon * (1 - zoom));
        }
        const bg = img(d.bg);
        if (bg) ctx.drawImage(bg, 0, 0); else { ctx.fillStyle = "#120d2e"; ctx.fillRect(0, 0, 960, 540); }

        for (const [x, y, colour, phase] of d.stars) {  // twinkling stars
            ctx.globalAlpha = 0.35 + 0.65 * Math.max(0, Math.sin(t * 2.2 + phase));
            ctx.fillStyle = colour; ctx.fillRect(x, y, 3, 3);
        }
        ctx.globalAlpha = 1;

        // the neon floor grid, its lines sliding towards you
        const H = d.horizon, slide = (t * 0.45) % 1;
        ctx.fillStyle = "rgba(255, 79, 163, 0.55)";
        for (let i = 0; i < 9; i++) {
            const y = H + Math.round(Math.pow((i + slide) / 9, 1.8) * (540 - H) / 3) * 3;
            ctx.fillRect(0, y, 960, 3);
        }
        ctx.strokeStyle = "rgba(255, 79, 163, 0.45)"; ctx.lineWidth = 3;
        ctx.beginPath();
        for (let i = -10; i <= 10; i++) { ctx.moveTo(480 + i * 36, H); ctx.lineTo(480 + i * 180, 540); }
        ctx.stroke();

        const cab = img(d.cabinets);
        if (cab) ctx.drawImage(cab, 0, 0);

        // the five regulars dancing under coloured spotlights
        const [cw, ch] = d.cell, [fx, fy] = d.feet, tick = Math.floor(t * 2);
        const boxedOnline = G.step === "online" || G.step === "join";  // (behind the big online box: only their feet showed)
        const dancers = boxedOnline ? [] : d.bots.map((b, i) => ({ ...b, i, feet: d.feetY }));
        if (d.champion && !boxedOnline) dancers.push({ ...d.champion, i: 5, feet: d.feetY - 18, champ: true });
        ctx.globalCompositeOperation = "lighter";
        for (const b of dancers) { const sp = spotSprite(b.spot); ctx.drawImage(sp, b.x - 80, b.feet - 34); }
        ctx.globalCompositeOperation = "source-over";
        G.hits = [];
        const talk = [];
        for (const b of dancers) {
            const beatF = t * 2.4 + b.i * 0.7, beat = Math.floor(beatF) % 8;
            let hop = Math.round(Math.abs(Math.sin(beatF * Math.PI)) * 2) * 3;
            let dir = beat === 5 ? "left" : beat === 6 ? "right" : "down";
            let pose = beat % 2 ? 1 : 2;
            if (dir === "down" && beat === 3 && beatF % 1 < 0.35) pose = 3;
            const poked = G.pokes[b.i], since = poked ? t - poked.t0 : 99;
            if (since < 0.7) {  // poked: a big jump with a spin
                hop = Math.round(Math.sin(since / 0.7 * Math.PI) * 14) * 3;
                dir = ["down", "right", "up", "left"][Math.floor(since * 8) % 4];
                pose = 0;
            }
            if (since > 0.3 && since < 2.1) talk.push([b, poked.line]);  // says it as it lands
            if (b.champ) {  // a little gold podium
                ctx.fillStyle = "#7a4a0a"; ctx.fillRect(b.x - 54, b.feet, 108, 18);
                ctx.fillStyle = "#ffc23a"; ctx.fillRect(b.x - 54, b.feet, 108, 6);
            }
            ctx.fillStyle = "rgba(0, 0, 0, 0.35)";
            ctx.beginPath(); ctx.ellipse(b.x, b.feet + 2, 34 - hop / 3, 8, 0, 0, Math.PI * 2); ctx.fill();
            const sheet = img(b.sheet);
            if (sheet) {
                const col = d.dirs.indexOf(dir) * d.poses + pose, row = tick % b.rows;
                ctx.drawImage(sheet, col * cw, row * ch, cw, ch, b.x - fx * 2, b.feet - hop - fy * 2, cw * 2, ch * 2);
            }
            const tag = img(b.tags[tick % b.tags.length]);
            if (tag) ctx.drawImage(tag, b.x - b.anchor[0], b.feet - hop - 147 - b.anchor[1]);
            if (b.champ) {
                crown(ctx, b.x - 64, b.feet - hop - 196);
                text(ctx, b.titles > 1 ? `CHAMPION X${b.titles}` : "CHAMPION", b.x + 14, b.feet - hop - 202, 1, "#ffd84a", "center", 2);
            } else if (!fly && !inBox()) {
                G.hits.push([b.x - 48, b.feet - 190, b.x + 48, b.feet, b.i, "bot"]);
            }
        }

        // what a poked bot says, over its own name tag (under the menu, which always stays readable)
        if (!inBox() && !fly) for (const [b, line] of talk) bubble(ctx, b.x, b.feet - 132, line);
        ctx.drawImage(vignette(), 0, 0);
        const intro = G.introT0 ? Math.min(1, (t - G.introT0) / 0.9) : 1;  // the logo drops in and bounces
        const back = 1 + 2.7 * Math.pow(intro - 1, 3) + 1.7 * Math.pow(intro - 1, 2);  // ease out with an overshoot
        const drop = -Math.round((1 - back) * 330 / 3) * 3;
        const small = inForm() || G.step === "mode";  // smaller above the name and PIN boxes and the longer menu
        const logo = img(small ? d.logoSmall : d.logo);
        const boxed = G.step === "online" || G.step === "join";  // (the online box has its own title)
        if (logo && !boxed) ctx.drawImage(logo, 0, Math.round(Math.sin(t * 1.6) * 2) * 3 - (small ? 0 : 6) + drop);

        ctx.setTransform(1, 0, 0, 1, 0, 0);
        if (fly) {  // into the arcade: everything else gone, fade to black at the end
            ctx.fillStyle = `rgba(0, 0, 0, ${Math.max(0, (fly - 0.55) / 0.45)})`; ctx.fillRect(0, 0, 960, 540);
        } else if (!G.attractDone) {
            if (intro >= 1 && Math.floor(t * 2.2) % 2 === 0) text(ctx, "PRESS ENTER", 480, 270, 2, "#ffe94a");
        } else {
            if (inForm()) drawForm(ctx, t);
            else if (G.step === "online") drawOnline(ctx, t);
            else if (G.step === "join") drawJoin(ctx, t);
            else drawMenu(ctx, t);
            // (no key hints on the screen: How to play has them)
        }

        if (G.missing.size && t - G.lastNeed > 1.5) { G.lastNeed = t; G.send("need", Array.from(G.missing)); }
    }

    function drawMenu(ctx, t) {
        const mode = G.step === "mode", items = MENUS[G.step], y0 = mode ? 188 : 222, gap = mode ? 42 : 46;  // (LOG OUT clear of the name tags)
        if (mode) text(ctx, `HELLO, ${G.data.signedIn}!`, 480, y0 - 42, 2, "#3ad6ff");
        items.forEach(([label], i) => {
            const y = y0 + i * gap, chosen = i === G.sel, s = 2, w = textWidth(label, s);
            const bob = chosen ? Math.round(Math.sin(t * 6) * 1) * 2 : 0;
            text(ctx, label, 480, y + bob, s, chosen ? "#ffe94a" : "#ffffff");
            if (chosen) {  // spinning arcade coins either side
                coin(ctx, 480 - w / 2 - 34, y + 14, t);
                coin(ctx, 480 + w / 2 + 34, y + 14, t + 0.4);
            }
            G.hits.push([480 - w / 2 - 40, y - 6, 480 + w / 2 + 40, y + 36, i, "item"]);
        });
    }
    function box(ctx, left, top, right, bottom) {  // the dark box with the cyan and pink edges (as the forms)
        ctx.fillStyle = "rgba(10, 7, 28, 0.92)"; ctx.fillRect(left, top, right - left, bottom - top);
        ctx.strokeStyle = "#3ad6ff"; ctx.lineWidth = 4; ctx.strokeRect(left + 2, top + 2, right - left - 4, bottom - top - 4);
        ctx.strokeStyle = "rgba(255, 79, 163, 0.7)"; ctx.lineWidth = 2; ctx.strokeRect(left + 9, top + 9, right - left - 18, bottom - top - 18);
    }
    function button(ctx, x, y, w, h, label, chosen, s = 2, fill = null) {  // a chunky white button; yellow when chosen
        ctx.fillStyle = "#16122b"; ctx.fillRect(x + 4, y + 5, w, h);  // its shadow
        ctx.fillStyle = "#16122b"; ctx.fillRect(x - 3, y - 3, w + 6, h + 6);
        ctx.fillStyle = chosen ? "#ffe94a" : (fill || "#ffffff"); ctx.fillRect(x, y, w, h);
        text(ctx, label, x + w / 2, y + Math.round((h - G.data.font.h * s) / 2) + 2, s, "#16122b", "center", 0);
    }
    function dancer(ctx, b, x, feet, t, i) {  // you, dancing on the spot in the online box: big, with your name tag
        const d = G.data, [cw, ch] = d.cell, [fx, fy] = d.feet, tick = Math.floor(t * 2), k = 3, tk = 2;  // (sizes)
        const beatF = t * 2.4 + i * 0.7, beat = Math.floor(beatF) % 8;
        const hop = Math.round(Math.abs(Math.sin(beatF * Math.PI)) * 2) * 6;
        const dir = beat === 5 ? "left" : beat === 6 ? "right" : "down";
        let pose = beat % 2 ? 1 : 2;
        if (dir === "down" && beat === 3 && beatF % 1 < 0.35) pose = 3;
        ctx.fillStyle = "rgba(0, 0, 0, 0.35)";
        ctx.beginPath(); ctx.ellipse(x, feet + 3, 52 - hop / 3, 12, 0, 0, Math.PI * 2); ctx.fill();
        const sheet = img(b.sheet);
        if (sheet) {
            const col = d.dirs.indexOf(dir) * d.poses + pose, row = tick % b.rows;
            ctx.drawImage(sheet, col * cw, row * ch, cw, ch, x - fx * k, feet - hop - fy * k, cw * k, ch * k);
        }
        const tag = img(b.tags[tick % b.tags.length]);  // (the tag's own animation: it changes on every beat)
        if (tag) ctx.drawImage(tag, x - b.anchor[0] * tk, feet - hop - 74 * k - b.anchor[1] * tk, tag.width * tk, tag.height * tk);
    }
    function drawOnline(ctx, t) {  // PLAY ONLINE: you, dancing, and the four buttons (coins spin by the chosen one)
        const left = 196, top = 34, right = 764, bottom = 506;
        box(ctx, left, top, right, bottom);
        text(ctx, "PLAY ONLINE", 480, top + 22, 3, "#ffe94a");
        text(ctx, "EACH FRIEND ON THEIR OWN PHONE OR LAPTOP", 480, top + 78, 1, "#d9d4ff", "center", 2);
        text(ctx, "UP TO 4 PLAYERS  -  NO BOTS", 480, top + 100, 1, "#7cff3a", "center", 2);
        if (G.data.me) dancer(ctx, G.data.me, 300, 470, t, 2);
        MENUS.online.forEach(([label], i) => {
            const x = 404, y = 168 + i * 68, w = 316, h = 50, chosen = i === G.sel;
            const busy = i === 0 && G.pending && G.pending.kind === "lobby";
            button(ctx, x, y, w, h, busy ? "..." : label, chosen);
            if (chosen) { coin(ctx, x - 24, y + h / 2, t); coin(ctx, x + w + 24, y + h / 2, t + 0.4); }
            G.hits.push([x - 6, y - 6, x + w + 6, y + h + 6, i, "item"]);
        });
        if (G.error) text(ctx, G.error, 562, 448, 1, "#ff6b7a", "center", 2);
    }
    function drawJoin(ctx, t) {  // JOIN A LOBBY: the code in four boxes, and letters to pick with the arrows or a click
        const left = 196, top = 34, right = 764, bottom = 506, n = data.codeLength;
        box(ctx, left, top, right, bottom);
        text(ctx, "JOIN A LOBBY", 480, top + 22, 3, "#ffe94a");
        text(ctx, "TYPE YOUR FRIEND'S CODE", 480, top + 78, 1, "#d9d4ff", "center", 2);
        for (let i = 0; i < n; i++) {  // the code so far
            const x = 480 - n * 38 + i * 76 + 4, y = 136, here = i === G.code.length;
            ctx.fillStyle = "#1b1546"; ctx.fillRect(x, y, 64, 64);
            ctx.strokeStyle = here ? "#ffe94a" : "#3a2f6b"; ctx.lineWidth = here ? 4 : 3; ctx.strokeRect(x + 2, y + 2, 60, 60);
            if (i < G.code.length) text(ctx, G.code[i], x + 32, y + 12, 3, "#ffffff");
            else if (here && Math.floor(t * 2.5) % 2 === 0) { ctx.fillStyle = "#ffe94a"; ctx.fillRect(x + 16, y + 50, 32, 4); }
        }
        if (G.error) text(ctx, G.error, 480, 212, 1, "#ff6b7a", "center", 2);
        const keys = padKeys(), cols = 5, kw = 70, kh = 42, gap = 10, letters = data.codeLetters.length;
        const width = cols * kw + (cols - 1) * gap, x0 = 480 - width / 2, y0 = 236;
        keys.forEach((label, i) => {
            let x, y, w;
            if (i < letters) { x = x0 + (i % cols) * (kw + gap); y = y0 + Math.floor(i / cols) * (kh + gap); w = kw; }
            else {
                const third = (width - 2 * gap) / 3, k = i - letters;
                x = x0 + k * (third + gap); y = y0 + Math.ceil(letters / cols) * (kh + gap) + 4; w = third;
            }
            const ready = label === "JOIN" && G.code.length === n;
            const busy = label === "JOIN" && G.pending && G.pending.kind === "lobby";
            button(ctx, x, y, w, kh, busy ? "..." : label, i === G.pad, 2, ready ? "#7cff3a" : null);
            G.hits.push([x - 4, y - 4, x + w + 4, y + kh + 4, i, "pad"]);
        });
    }
    function coin(ctx, x, y, t) {
        const w = Math.max(4, Math.round(Math.abs(Math.cos(t * 3.5)) * 6) * 4);
        ctx.fillStyle = "#16122b"; ctx.fillRect(x - w / 2 - 3, y - 15, w + 6, 30);
        ctx.fillStyle = "#c98a12"; ctx.fillRect(x - w / 2, y - 12, w, 24);
        ctx.fillStyle = "#ffd84a"; ctx.fillRect(x - w / 2 + 3, y - 9, Math.max(0, w - 6), 18);
        if (w > 10) { ctx.fillStyle = "#fff6c4"; ctx.fillRect(x - 3, y - 6, 3, 9); }
    }
    function crown(ctx, x, y) {
        const rows = ["#..#..#", "#######", "#.###.#", "#######"];
        rows.forEach((row, r) => [...row].forEach((c, k) => {
            if (c === "#") { ctx.fillStyle = r === 0 ? "#fff6c4" : "#ffc23a"; ctx.fillRect(x + k * 4, y + r * 4, 4, 4); }
        }));
    }
    function bubble(ctx, x, y, line) {  // what a poked bot says
        const w = textWidth(line, 1) + 24, left = Math.max(8, Math.min(952 - w, x - w / 2));
        ctx.fillStyle = "#16122b"; ctx.fillRect(left - 3, y - 33, w + 6, 34);
        ctx.fillStyle = "#fff6da"; ctx.fillRect(left, y - 30, w, 28);
        ctx.beginPath(); ctx.moveTo(x - 6, y - 3); ctx.lineTo(x + 6, y - 3); ctx.lineTo(x, y + 7); ctx.fill();
        text(ctx, line, left + w / 2, y - 25, 1, "#16122b", "center", 0);
    }
    function drawForm(ctx, t) {
        const isNew = G.step === "new", items = formItems(), count = isNew ? 3 : 2;
        const top = isNew ? 140 : 166, left = 236, right = 724;
        const rowsTop = top + 70, by = rowsTop + count * 54 + 4, bottom = by + 98;
        ctx.fillStyle = "rgba(10, 7, 28, 0.92)"; ctx.fillRect(left, top, right - left, bottom - top);
        ctx.strokeStyle = "#3ad6ff"; ctx.lineWidth = 4; ctx.strokeRect(left + 2, top + 2, right - left - 4, bottom - top - 4);
        ctx.strokeStyle = "rgba(255, 79, 163, 0.7)"; ctx.lineWidth = 2; ctx.strokeRect(left + 9, top + 9, right - left - 18, bottom - top - 18);
        text(ctx, isNew ? "ENTER YOUR NAME" : "WELCOME BACK", 480, top + 20, 2, "#ffe94a");
        const rows = isNew ? [["NAME", "name"], ["PIN", "pin"], ["PIN AGAIN", "pin2"]] : [["NAME", "name"], ["PIN", "pin"]];
        rows.forEach(([label, field], i) => {
            const y = rowsTop + i * 54, focused = items[G.focus] === field;
            text(ctx, label, left + 30, y + 6, 1, focused ? "#ffe94a" : "#d9d4ff", "left", 2);
            const bx = left + 176, bw = right - left - 206;
            ctx.fillStyle = "#1c1642"; ctx.fillRect(bx, y - 6, bw, 40);
            ctx.strokeStyle = focused ? "#ffe94a" : "#3a2f6b"; ctx.lineWidth = 3; ctx.strokeRect(bx + 1.5, y - 4.5, bw - 3, 37);
            let end = bx + 12;
            if (field === "name") {
                text(ctx, G.fields.name, bx + 12, y, 2, "#ffffff", "left", 0);
                end = bx + 12 + textWidth(G.fields.name, 2) + 4;
            } else {
                for (let k = 0; k < G.fields[field].length; k++) { ctx.fillStyle = "#ffffff"; ctx.fillRect(bx + 14 + k * 22, y + 8, 12, 12); }
                end = bx + 14 + G.fields[field].length * 22;
            }
            if (focused && Math.floor(t * 2.5) % 2 === 0) { ctx.fillStyle = "#ffe94a"; ctx.fillRect(end, y + 1, 4, 26); }
            G.hits.push([bx, y - 6, bx + bw, y + 34, items.indexOf(field), "field"]);
        });
        [["submit", isNew ? "CREATE" : "LOG IN"], ["back", "BACK"]].forEach(([item, label], i) => {
            const w = i === 0 ? 210 : 140, x = i === 0 ? left + 36 : right - 36 - 140, focused = items[G.focus] === item;
            ctx.fillStyle = focused ? "#ffe94a" : "#1c1642"; ctx.fillRect(x, by, w, 40);
            ctx.strokeStyle = focused ? "#ffffff" : "#3ad6ff"; ctx.lineWidth = 3; ctx.strokeRect(x + 1.5, by + 1.5, w - 3, 37);
            const busy = item === "submit" && G.pending;
            text(ctx, busy ? "..." : label, x + w / 2, by + 6, 2, focused ? "#16122b" : "#ffffff", "center", 0);
            G.hits.push([x, by, x + w, by + 40, items.indexOf(item), "button"]);
        });
        if (G.error) text(ctx, G.error, 480, by + 58, 1, "#ff6b7a", "center", 2);
        else if (isNew) text(ctx, "REMEMBER YOUR PIN: IT CANNOT BE RECOVERED", 480, by + 58, 1, "#b9b0e8", "center", 2);
    }
}
"""

_title = st.components.v2.component("arcade_title", css=TITLE_CSS, js=TITLE_JS)
EVENTS = ("howto", "submit", "play", "lobby", "logout", "entered", "need")


def mount(data: dict, key: str = "arcade_title"):
    """Show the title screen. Returns the component result: result.howto, .submit, .play, .lobby, .logout, .entered,
    .need."""
    callbacks = {f"on_{name}_change": (lambda: None) for name in EVENTS}
    return _title(key=key, data=data, width="stretch", **callbacks)
