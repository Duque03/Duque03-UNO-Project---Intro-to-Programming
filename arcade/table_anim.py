"""Animations on top of the table picture: cards flying, the deal, the roulette that picks who starts.

The table is still one picture sent by Python (the state after the move). An animation is drawn by the browser on a
see-through canvas laid exactly over that picture (ANIM_JS, placed by `ui.Slot.overlay`): first a picture of the table
as it was before the move ("under", without the cards that are about to fly), then the cards moving, then the canvas
clears and the real picture shows through. Python only describes the animation (the pictures of the cards, where each
one starts and lands, and when); the browser moves them smoothly. Each animation has an id and plays only once.

    {"id": "uno-3", "total": 1800, "under": <picture>, "sprites": {"back": <picture>, ...},
     "moves": [{"img": "back", "from": [x, y], "to": [x, y], "at": 0, "dur": 420,
                "s0": 1, "s1": 0.25, "arc": 30, "stay": True, "sound": "card"}, ...],
     "spin": {"seats": [[x, y, w, h], ...], "winner": 2, "at": 1200, "dur": 2200, "label": "label"}}

Times are in milliseconds from the start. Positions are the top-left corners of the pictures, on the 960x540 table
picture. s0 and s1: the size at the start and at the end (1 = the picture's own size); h0 and h1: how tall it
looks at the start and at the end (cards.LYING for a card lying on the table, 1 for one held up). A move with "stay" stays where
it landed until the end (a card that reached the pile). The spin lights the seats one after the other, slowing down,
and stops on the winner; then the label picture shows in the middle until the end.

Python waits (time.sleep) for `total` before it moves on, so nothing else changes on the table meanwhile.
"""

from __future__ import annotations

import base64
import io

import streamlit as st

from arcade import ui

ANIM_JS = r"""
export default function (component) {
    const { data, parentElement } = component;
    const A = window.__arcadeAnim || (window.__arcadeAnim = { done: new Set(), current: null });
    let canvas = parentElement.querySelector("canvas");
    if (!canvas) {
        canvas = document.createElement("canvas");
        canvas.width = 960; canvas.height = 540;
        canvas.style.cssText = "display:block;width:100%;height:auto;aspect-ratio:16/9;pointer-events:none;";
        parentElement.appendChild(canvas);
    }
    const ctx = canvas.getContext("2d");
    ctx.imageSmoothingEnabled = false;
    if (!data || !data.id || A.done.has(data.id)) { ctx.clearRect(0, 0, 960, 540); return; }
    A.done.add(data.id);  // plays once, even if Streamlit draws this element again
    A.current = data.id;
    const sound = (name) => {  // through SOUND_JS (arcade/sound.py), which knows if the sound is on
        const audio = window.__arcadeAudio;
        if (name && audio && audio.effect) audio.effect(name);
    };

    const load = (src) => new Promise((done) => {
        if (!src) { done(null); return; }
        const img = new Image();
        img.onload = () => done(img);
        img.onerror = () => done(null);
        img.src = src;
    });
    const names = Object.keys(data.sprites || {});
    Promise.all([load(data.under), ...names.map((n) => load(data.sprites[n]))]).then(([under, ...loaded]) => {
        const sprite = {};
        names.forEach((n, i) => { sprite[n] = loaded[i]; });
        const ease = (p) => 1 - Math.pow(1 - p, 3);
        const moves = (data.moves || []).map((m) => Object.assign({ played: false }, m));
        const spin = data.spin;
        let lastSeat = -1;
        const t0 = performance.now();

        const drawSpin = (t) => {
            const p = Math.min(1, (t - spin.at) / spin.dur), n = spin.seats.length;
            const steps = n * 3 + spin.winner;  // three laps, then it stops on the one who starts
            const at = Math.min(steps, Math.floor(ease(p) * (steps + 0.999))) % n;
            if (at !== lastSeat) { lastSeat = at; sound(p >= 1 ? "coin" : "tick"); }
            const [x, y, w, h] = spin.seats[at];
            ctx.save();
            ctx.lineWidth = 6;
            ctx.strokeStyle = p >= 1 ? `rgba(255, 233, 74, ${0.7 + 0.3 * Math.sin(t / 70)})` : "#ffe94a";
            ctx.shadowColor = "#ffe94a"; ctx.shadowBlur = 20;
            ctx.strokeRect(x, y, w, h);
            ctx.restore();
            const label = sprite[spin.label];
            // the name of who starts, between the pile and the hand
            if (p >= 1 && label) ctx.drawImage(label, 480 - label.width / 2, 384 - label.height / 2);
        };

        const frame = (now) => {
            if (A.current !== data.id) return;  // a newer animation took over the canvas
            const t = now - t0;
            ctx.clearRect(0, 0, 960, 540);
            if (t >= data.total) return;  // done: the real picture shows through
            if (under) ctx.drawImage(under, 0, 0, 960, 540);
            for (const m of moves) {
                const p = (t - m.at) / m.dur;
                if (p < 0) continue;
                if (!m.played) { m.played = true; sound(m.sound); }
                if (p >= 1 && !m.stay) continue;
                const img = sprite[m.img];
                if (!img) continue;
                const k = Math.min(1, p), e = ease(k);
                const s0 = m.s0 === undefined ? 1 : m.s0, s1 = m.s1 === undefined ? s0 : m.s1;
                const s = s0 + (s1 - s0) * e;
                const h0 = m.h0 === undefined ? 1 : m.h0, h1 = m.h1 === undefined ? 1 : m.h1;
                const flat = h0 + (h1 - h0) * e;  // lying on the table (shorter) or held up
                const x = m.from[0] + (m.to[0] - m.from[0]) * e;
                const y = m.from[1] + (m.to[1] - m.from[1]) * e - Math.sin(k * Math.PI) * (m.arc || 0);
                ctx.drawImage(img, Math.round(x), Math.round(y), Math.round(img.width * s),
                              Math.round(img.height * s * flat));
            }
            if (spin && t >= spin.at) drawSpin(t);
            requestAnimationFrame(frame);
        };
        requestAnimationFrame(frame);
    });
}
"""
_component = st.components.v2.component("arcade_table_anim", js=ANIM_JS)


def encode(img) -> str:
    """A small picture with see-through parts (a card, a label), as text the browser can draw."""
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def new_id(prefix: str) -> str:
    """A fresh id for an animation (each one plays once in the browser)."""
    st.session_state["_anim_count"] = st.session_state.get("_anim_count", 0) + 1
    return f"{prefix}-{st.session_state['_anim_count']}"


def play(slot, plan: dict) -> None:
    """Lay the animation over the picture in `slot`.

    plan: like the dict at the top of this file, with Pillow pictures for "under" and the sprites. Call this before
    showing the picture of the table after the move: the canvas covers the old picture straight away (with "under"),
    so the new one can arrive behind it without anyone seeing it early.
    """
    data = dict(plan, id=plan.get("id") or new_id("anim"))
    if data.get("under") is not None:
        data["under"] = ui.inline(data["under"])  # exactly like the real picture (with the same glow)
    data["sprites"] = {name: encode(img) for name, img in plan.get("sprites", {}).items()}
    with slot.overlay():
        _component(data=data)


def seconds(plan: dict) -> float:
    """How long the animation lasts, in seconds (Python waits that long before it goes on)."""
    return plan.get("total", 0) / 1000
