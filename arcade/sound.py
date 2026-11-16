"""Music and sound effects (task A7).

The sounds are made in the browser with the Web Audio API, so there are no
sound files and nothing heavy is sent: Python only queues the *name* of a sound
with play(), and render() (called once at the end of every run in app.py)
hands the last few names to SOUND_JS, which plays the ones it has not played yet.

The music is a short original loop. M turns it on and off; the browser
remembers the choice (localStorage). Browsers only allow sound after the first
click or key press, so the music starts then.
"""

from __future__ import annotations

import streamlit as st

SOUNDS = ["start", "table", "win", "lose", "tie", "coin", "blip", "pause"]
MAX_QUEUE = 5  # only the last few cues are kept; the browser skips those it already played


def add_cue(queue: list[dict], name: str) -> list[dict]:
    """A new queue with the sound added at the end. Unknown names are refused."""
    if name not in SOUNDS:
        raise ValueError(f"unknown sound: {name}")
    last = queue[-1]["id"] if queue else 0
    return (list(queue) + [{"id": last + 1, "name": name}])[-MAX_QUEUE:]


def play(name: str) -> None:
    """Ask the browser to play a sound at the end of this run (or of the next one, after st.rerun())."""
    st.session_state["_sounds"] = add_cue(st.session_state.get("_sounds", []), name)


SOUND_JS = """
export default function (component) {
    const A = window.__arcadeAudio || (window.__arcadeAudio = { lastCue: 0, musicOn: null, started: false });
    if (A.musicOn === null) {
        try { A.musicOn = localStorage.getItem("arcadeMusic") !== "off"; } catch (e) { A.musicOn = true; }
    }

    const context = () => {
        if (!A.ctx) {
            const Ctx = window.AudioContext || window.webkitAudioContext;
            if (!Ctx) return null;
            A.ctx = new Ctx();
            A.master = A.ctx.createGain();
            A.master.gain.value = 0.18;
            A.master.connect(A.ctx.destination);
        }
        return A.ctx;
    };

    // one note: frequency in Hz, start in seconds from now, length in seconds
    const note = (freq, start, length, type = "square", volume = 0.5) => {
        const ctx = context();
        if (!ctx || !freq) return;
        const t = ctx.currentTime + start;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = type;
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(volume, t);
        gain.gain.exponentialRampToValueAtTime(0.001, t + length);
        osc.connect(gain).connect(A.master);
        osc.start(t);
        osc.stop(t + length + 0.02);
    };
    const hz = (n) => 440 * Math.pow(2, (n - 69) / 12);  // MIDI note number to Hz
    const run = (notes, step, type, volume) => notes.forEach((n, i) => note(hz(n), i * step, step * 1.4, type, volume));

    const EFFECTS = {
        start: () => run([60, 64, 67, 72, 76], 0.07, "square", 0.35),
        table: () => run([67, 72], 0.08, "square", 0.3),
        win: () => { run([72, 76, 79, 84], 0.09, "square", 0.35); note(hz(88), 0.38, 0.5, "triangle", 0.5); },
        lose: () => run([67, 64, 60, 55], 0.14, "triangle", 0.5),
        tie: () => run([67, 67], 0.12, "triangle", 0.45),
        coin: () => { note(hz(83), 0, 0.07, "square", 0.3); note(hz(88), 0.07, 0.25, "square", 0.3); },
        blip: () => note(hz(81), 0, 0.05, "square", 0.25),
        pause: () => run([64, 57], 0.08, "triangle", 0.45),
    };

    // The music: two bars of an original tune over a bass line, looped (16 steps a bar)
    const MELODY = [69, 0, 72, 0, 76, 0, 74, 72, 69, 0, 67, 0, 69, 0, 0, 0,
                    72, 0, 74, 0, 76, 0, 79, 76, 74, 0, 72, 0, 74, 0, 0, 0];
    const BASS = [45, 0, 45, 0, 52, 0, 45, 0, 43, 0, 43, 0, 50, 0, 43, 0,
                  41, 0, 41, 0, 48, 0, 41, 0, 43, 0, 43, 0, 50, 0, 47, 0];
    const STEP = 60 / 120 / 4;  // 120 beats a minute, four steps a beat
    const startMusic = () => {
        const ctx = context();
        if (!ctx || A.musicTimer) return;
        A.step = 0;
        A.next = ctx.currentTime + 0.1;
        A.musicTimer = setInterval(() => {  // schedule a little ahead so the beat stays steady
            while (A.next < ctx.currentTime + 0.25) {
                const i = A.step % MELODY.length;
                const at = A.next - ctx.currentTime;
                if (MELODY[i]) note(hz(MELODY[i]), at, STEP * 1.6, "square", 0.12);
                if (BASS[i]) note(hz(BASS[i]), at, STEP * 1.8, "triangle", 0.3);
                A.step += 1;
                A.next += STEP;
            }
        }, 60);
    };
    const stopMusic = () => { clearInterval(A.musicTimer); A.musicTimer = null; };

    if (!A.started) {  // only once per page, even though Streamlit calls this function on every run
        A.started = true;
        const wake = () => {  // browsers only allow sound after a click or a key press
            const ctx = context();
            if (ctx && ctx.state === "suspended") ctx.resume();
            if (A.musicOn) startMusic();
        };
        document.addEventListener("pointerdown", wake);
        document.addEventListener("keydown", (event) => {
            const tag = (event.target.tagName || "").toLowerCase();
            const key = (event.key || "").toLowerCase();
            if (key === "m" && tag !== "input" && tag !== "textarea" && !event.ctrlKey && !event.metaKey) {
                A.musicOn = !A.musicOn;
                try { localStorage.setItem("arcadeMusic", A.musicOn ? "on" : "off"); } catch (e) {}
                if (A.musicOn) startMusic(); else stopMusic();
            }
            wake();
        });
    }

    const cues = (component.data && component.data.cues) || [];
    for (const cue of cues) {
        if (typeof cue.id !== "number" || cue.id <= A.lastCue) continue;
        A.lastCue = cue.id;
        const effect = EFFECTS[cue.name];
        if (effect && context()) effect();
    }
}
"""
_player = st.components.v2.component("arcade_sound", js=SOUND_JS)


def render() -> None:
    """Hand the latest sound names to the browser. Call once, at the end of every run."""
    st.markdown("<style>.st-key-sound_player { display: none; }</style>", unsafe_allow_html=True)
    _player(key="sound_player", data={"cues": st.session_state.get("_sounds", [])})
