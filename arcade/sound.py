"""Music and sound effects (task A7).

The sounds are made in the browser with the Web Audio API, so there are no
sound files and nothing heavy is sent: Python only queues the *name* of a sound
with play(), and render() (called once at the end of every run in app.py)
hands the last few names to SOUND_JS, which plays the ones it has not played yet.

The music: five original tunes (arcade/music.py), one for the title, one for the
arcade room and one for each game. They are written into SOUND_JS once, and each
run only tells the browser which tune the screen wants; the browser fades from one
to the other. M, or the little note in the top-left corner, turns the music on and off;
the browser remembers the choice (localStorage). Browsers only allow sound after
the first click or key press, so the music starts then.
"""

from __future__ import annotations

import json

import streamlit as st

from arcade import music

SOUNDS = ["start", "table", "win", "lose", "tie", "coin", "blip", "pause", "card", "tick"]
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
            A.musicGain = A.ctx.createGain();  // the music has its own volume, so it can fade between tunes
            A.musicGain.connect(A.master);
            A.noise = A.ctx.createBuffer(1, A.ctx.sampleRate * 0.3, A.ctx.sampleRate);  // for the drums
            const samples = A.noise.getChannelData(0);
            for (let i = 0; i < samples.length; i++) samples[i] = Math.random() * 2 - 1;
        }
        return A.ctx;
    };

    // one note: frequency in Hz, start in seconds from now, length in seconds
    const note = (freq, start, length, type = "square", volume = 0.5, out = null) => {
        const ctx = context();
        if (!ctx || !freq) return;
        const t = ctx.currentTime + start;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = type;
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(volume, t);
        gain.gain.exponentialRampToValueAtTime(0.001, t + length);
        osc.connect(gain).connect(out || A.master);
        osc.start(t);
        osc.stop(t + length + 0.02);
    };
    const drum = (kind, start) => {  // k kick, s snare, h hi-hat, all made from a falling tone or noise
        const ctx = A.ctx, t = ctx.currentTime + Math.max(0, start), gain = ctx.createGain();
        if (kind === "k") {
            const osc = ctx.createOscillator();
            osc.frequency.setValueAtTime(140, t);
            osc.frequency.exponentialRampToValueAtTime(42, t + 0.12);
            gain.gain.setValueAtTime(0.55, t);
            gain.gain.exponentialRampToValueAtTime(0.001, t + 0.16);
            osc.connect(gain).connect(A.musicGain);
            osc.start(t); osc.stop(t + 0.18);
            return;
        }
        const source = ctx.createBufferSource(), filter = ctx.createBiquadFilter();
        source.buffer = A.noise;
        filter.type = kind === "s" ? "bandpass" : "highpass";
        filter.frequency.value = kind === "s" ? 1800 : 7000;
        const volume = kind === "s" ? 0.22 : 0.07, length = kind === "s" ? 0.12 : 0.04;
        gain.gain.setValueAtTime(volume, t);
        gain.gain.exponentialRampToValueAtTime(0.001, t + length);
        source.connect(filter).connect(gain).connect(A.musicGain);
        source.start(t); source.stop(t + length + 0.02);
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
        card: () => {  // a card sliding on the table: a short burst of noise that falls in pitch
            const ctx = A.ctx, t = ctx.currentTime;
            const source = ctx.createBufferSource(), filter = ctx.createBiquadFilter(), gain = ctx.createGain();
            source.buffer = A.noise;
            filter.type = "bandpass";
            filter.frequency.setValueAtTime(2600, t);
            filter.frequency.exponentialRampToValueAtTime(800, t + 0.08);
            gain.gain.setValueAtTime(0.32, t);
            gain.gain.exponentialRampToValueAtTime(0.001, t + 0.09);
            source.connect(filter).connect(gain).connect(A.master);
            source.start(t); source.stop(t + 0.11);
        },
        tick: () => note(hz(79), 0, 0.03, "square", 0.16),  // the roulette passing a player
    };

    // The music: the tunes of arcade/music.py (Python writes them in below), one for each kind of screen.
    const SCORE = __SCORE__;
    const VOICES = {  // how each part of a tune sounds
        lead: { type: "square", volume: 0.1, hold: 0.9 },
        bass: { type: "triangle", volume: 0.28, hold: 0.95 },
        arp: { type: "square", volume: 0.035, hold: 0.8 },
        stabs: { type: "square", volume: 0.03, hold: 0.55 },
    };
    const steps = (name) => {  // the tune as a list of steps, each with the notes that start on it (built once)
        const tune = SCORE[name];
        if (tune.rows) return tune.rows;
        const rows = Array.from({ length: tune.bars * 16 }, () => []);
        for (const voice of Object.keys(VOICES)) {
            for (const [step, midi, length] of (tune[voice] || [])) rows[step % rows.length].push([voice, midi, length]);
        }
        for (const [step, kind] of (tune.drums || [])) rows[step % rows.length].push(["drum", kind]);
        return (tune.rows = rows);
    };
    const tick = () => {  // schedule a little ahead so the beat stays steady
        const ctx = A.ctx;
        if (A.want && A.want !== A.playing && !A.fading) {  // the screen wants another tune: fade over to it
            A.fading = true;
            A.musicGain.gain.setTargetAtTime(0, ctx.currentTime, 0.08);
            setTimeout(() => {
                A.playing = A.want; A.step = 0; A.next = ctx.currentTime + 0.05;
                A.musicGain.gain.setTargetAtTime(1, ctx.currentTime, 0.05);
                A.fading = false;
            }, 300);
        }
        const tune = SCORE[A.playing];
        if (!tune) return;
        const rows = steps(A.playing), step = 60 / tune.bpm / 4;
        while (A.next < ctx.currentTime + 0.2) {
            const i = A.step % rows.length;
            const swing = i % 4 === 2 ? tune.swing * step : 0;  // the offbeats a little late, for a bouncy feel
            const at = A.next + swing - ctx.currentTime;
            for (const event of rows[i]) {
                if (event[0] === "drum") { drum(event[1], at); continue; }
                const voice = VOICES[event[0]];
                note(hz(event[1]), at, event[2] * step * voice.hold + 0.04, voice.type, voice.volume, A.musicGain);
            }
            A.step += 1;
            A.next += step;
        }
    };
    const startMusic = () => {
        const ctx = context();
        if (!ctx || A.musicTimer) return;
        A.playing = A.want || "title";
        A.step = 0;
        A.next = ctx.currentTime + 0.1;
        A.musicGain.gain.cancelScheduledValues(ctx.currentTime);
        A.musicGain.gain.setValueAtTime(1, ctx.currentTime);
        A.musicTimer = setInterval(tick, 50);
    };
    const stopMusic = () => { clearInterval(A.musicTimer); A.musicTimer = null; };
    const toggleMusic = () => {  // the M key and the MUSIC button
        A.musicOn = !A.musicOn;
        try { localStorage.setItem("arcadeMusic", A.musicOn ? "on" : "off"); } catch (e) {}
        if (A.musicOn) startMusic(); else stopMusic();
        if (A.label) A.label();
    };

    if (!A.started) {  // only once per page, even though Streamlit calls this function on every run
        A.started = true;
        const wake = () => {  // browsers only allow sound after a click or a key press
            const ctx = context();
            if (ctx && ctx.state === "suspended") ctx.resume();
            if (A.musicOn) startMusic();
        };
        // The title screen and the room handle their own keys and stop them, so the first key press is heard
        // here first (capture on the window) just to wake the sound. M is only read below, where a key that the
        // title used for typing a name never arrives.
        window.addEventListener("pointerdown", wake, true);
        window.addEventListener("keydown", wake, true);
        document.addEventListener("keydown", (event) => {
            const tag = (event.target.tagName || "").toLowerCase();
            const key = (event.key || "").toLowerCase();
            if (key === "m" && tag !== "input" && tag !== "textarea" && !event.ctrlKey && !event.metaKey) toggleMusic();
            wake();
        });
        // The music button (a small icon in the top-left corner, next to full screen): the mouse can do what M does.
        // It goes on the page itself, because this component's own box is hidden.
        const button = document.createElement("button");
        button.className = "arcade-music";
        button.style.cssText = "position:fixed;top:8px;left:10px;z-index:1000;cursor:pointer;width:34px;height:34px;"
            + "padding:0;font:1.3rem 'Jersey 10',monospace;line-height:1;color:#f3ead2;"
            + "background:#16122b;border:3px solid #3ad6ff;border-radius:0;box-shadow:3px 3px 0 #05030d;";
        button.addEventListener("mouseenter", () => { button.style.background = "#2a2150"; });
        button.addEventListener("mouseleave", () => { button.style.background = "#16122b"; });
        A.label = () => {  // a small note icon, crossed out when the music is off
            button.textContent = A.musicOn ? "\u266a" : "\u00d7";
            button.title = A.musicOn ? "Music on (M)" : "Music off (M)";
        };
        button.addEventListener("click", (event) => {
            event.stopPropagation();
            toggleMusic();
            button.blur();  // so a later Space or Enter does not press it again
        });
        document.body.appendChild(button);
        A.label();
    }

    A.effect = (name) => { const effect = EFFECTS[name]; if (effect && context()) effect(); };  // for the title screen

    if (component.data && component.data.track) A.want = component.data.track;  // the tune this screen wants
    const cues = (component.data && component.data.cues) || [];
    for (const cue of cues) {
        if (typeof cue.id !== "number" || cue.id <= A.lastCue) continue;
        A.lastCue = cue.id;
        const effect = EFFECTS[cue.name];
        if (effect && context()) effect();
    }
}
"""
SOUND_JS = SOUND_JS.replace("__SCORE__", json.dumps(music.TRACKS, separators=(",", ":")))
_player = st.components.v2.component("arcade_sound", js=SOUND_JS)


def render() -> None:
    """Hand the latest sound names to the browser. Call once, at the end of every run."""
    st.markdown("<style>.st-key-sound_player { display: none; }</style>", unsafe_allow_html=True)
    track = music.track_for(st.session_state.get("screen", "title"), st.session_state.get("_track"))
    st.session_state["_track"] = track
    _player(key="sound_player", data={"cues": st.session_state.get("_sounds", []), "track": track})
