"""
Camera Sequence Executor
------------------------
Loads config/camera_sequence.json and runs each step.
Called from position_setup.py after voting start.

Step types:
  key   - hold a key for N seconds
  mouse - right-click drag by (dx, dy) to rotate camera
  delay - wait N seconds
"""

import ctypes
import ctypes.wintypes
import json
import os
import sys
import time

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (
    os.path.join(_BASE, "rblib", "src"),
    os.path.join(_BASE, "avlib"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from rblib import r_input

SEQUENCE_PATH = os.path.join(_BASE, "config", "camera_sequence.json")


def load_sequence() -> list[dict]:
    with open(SEQUENCE_PATH, "r") as f:
        return json.load(f)


_mouse_event = ctypes.windll.user32.mouse_event


def _mouse_move(dx: int, dy: int) -> None:
    if dx:
        _mouse_event(0x0001, dx, 0, 0, 0)
    if dy:
        _mouse_event(0x0001, 0, dy, 0, 0)


def run_step(step: dict) -> None:
    t = step["type"]
    if t == "key":
        r_input.PressKey(step["key"], step["duration"])
    elif t == "mouse":
        _mouse_move(step["dx"], step["dy"])
    elif t == "delay":
        time.sleep(step["seconds"])


def run_camera_sequence(log_cb=print) -> None:
    sequence = load_sequence()
    if not sequence:
        log_cb("Camera: sequence empty — skipping")
        return
    log_cb(f"Camera: running {len(sequence)} step(s)")
    for step in sequence:
        run_step(step)
    log_cb("Camera: done")
