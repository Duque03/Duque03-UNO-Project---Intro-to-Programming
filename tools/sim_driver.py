"""The app as tools/simulate_app.py runs it: app.py with three test hooks and nothing else changed.

- st.session_state["_sim_click"] = (x, y): a click on the game picture in this run (as INPUT_JS would send it);
- st.session_state["_sim_start"] = True: start the match in st.session_state["match"] straight away (no walk);
- the game's clock is tools/sim_clock.py: waiting moves it forward instead of taking real time, so animations, bot
  thinking and every countdown take their full time in the game but none for real; the soft glow is off (slow).
"""

import os
import pathlib
import sys
import time

os.environ["ARCADE_STRICT"] = "1"  # a problem must stop the run here (the game itself recovers: state.recover)

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import streamlit as st  # noqa: E402

from arcade import ui  # noqa: E402

if not hasattr(ui, "_sim_setup"):  # (this file runs again on every run, in the same process: wrap only once)
    ui._sim_setup = ui.setup_page


def setup_page():
    _use_sim_clock()  # (app.py has imported every screen by now)
    ui._sim_setup()
    click = st.session_state.pop("_sim_click", None)
    if click is not None:
        st.session_state["_click"] = click
    if st.session_state.pop("_sim_start", False):
        from arcade import match

        match.start_game()


ui.setup_page = setup_page
ui.GLOW = False  # the soft glow is only a look, and the slowest part of making a picture
import sim_clock  # noqa: E402  (tools/ is on the path: this file's folder)


def _use_sim_clock():
    """The game's modules use the simulator's clock (Streamlit keeps the real one)."""
    for name, module in list(sys.modules.items()):
        if (name == "arcade" or name.startswith("arcade.")) and getattr(module, "time", None) is time:
            module.time = sim_clock


exec(compile((ROOT / "app.py").read_text(), "app.py", "exec"))
