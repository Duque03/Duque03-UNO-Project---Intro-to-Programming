"""The game's clock in the simulator: waiting moves it forward instead of taking real time.

tools/sim_driver.py puts this module in place of `time` inside the game's own modules (arcade.*), and only there:
Streamlit keeps the real clock. So a 2-second UNO window, a bot thinking or a 10-second deal take their full time in
the game, and none for real.
"""

import time as _real

offset = [0.0]


def time() -> float:
    return _real.time() + offset[0]


def sleep(seconds: float) -> None:
    offset[0] += max(0.0, float(seconds))


def __getattr__(name):  # everything else (monotonic, strftime, ...) is the real time module's
    return getattr(_real, name)
