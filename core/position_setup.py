"""
Position Setup (Spring LTM)
---------------------------
Sequence:
  1. Focus Roblox window
  2. Close chat
  3. Vote start
  4. Click (760, 176) twice (0.5 s between)
  5. Click (587, 172)
  6. TP-to-spawn loop until SPAWN_REF_IMAGE shows in expected region
  7. Wait for wave 1
  8. Restart match
"""

import os
import sys
import time

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (
    os.path.join(_BASE, "rblib", "src"),
    os.path.join(_BASE, "avlib"),
    os.path.join(_BASE, "core"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from rblib import r_input, r_util
from rblib.r_client import focus_roblox_window
from AnimeVangaurdsLibrary.tools.av_game import read_wave, restart_match, return_to_spawn, start
from camera import run_camera_sequence

SPAWN_REF_IMAGE  = os.path.join(_BASE, "Images", "SpawnRef.png")
SPAWN_REF_REGION = (120, 302, 311, 509)   # x, y, w, h

POST_START_CLICK_1 = (760, 176)
POST_START_CLICK_2 = (587, 172)
CHAT_CLOSE_POS     = (161, 65)

_first_run = True


def setup_position(log_cb=print) -> None:
    global _first_run

    log_cb("Positioning: aligning Roblox window")
    focus_roblox_window()

    if _first_run:
        log_cb("Positioning: closing chat")
        r_input.Click(*CHAT_CLOSE_POS, 0.1)
        r_input.Click(*CHAT_CLOSE_POS, 0.1)
        r_input.Click(214, 353, 0.5)

    log_cb("Positioning: voting start")
    start()

    if _first_run:
        log_cb("Positioning: zooming out")
        r_input.PressKey("o", 5)

        log_cb(f"Positioning: clicking {POST_START_CLICK_1} twice")
        r_input.Click(*POST_START_CLICK_1, 0.1)
        time.sleep(1.0)
        r_input.Click(*POST_START_CLICK_1, 0.1)
        time.sleep(0.5)

        log_cb("Positioning: zooming out")
        r_input.PressKey("o", 5)

        log_cb(f"Positioning: clicking {POST_START_CLICK_2}")
        r_input.Click(*POST_START_CLICK_2, 0.1)

        time.sleep(1.5)
        tp_count = 0
        while not r_util.imageExists(SPAWN_REF_IMAGE, 0.8, region=SPAWN_REF_REGION):
            tp_count += 1
            log_cb(f"Positioning: TP to spawn (attempt {tp_count})")
            return_to_spawn()
            time.sleep(2)
        log_cb("Positioning: spawn view confirmed")

        focus_roblox_window()
        r_input.RightClick(44, 365, 0.1)
        time.sleep(3)
        r_input.RightClick(255, 344, 0.1)
        time.sleep(2.5)
        run_camera_sequence(log_cb=log_cb)

        log_cb("Positioning: waiting for wave 1...")
        while read_wave() < 1:
            time.sleep(0.5)

        log_cb("Positioning: restarting match")
        restart_match()
        _first_run = False

    log_cb("Positioning complete")


if __name__ == "__main__":
    setup_position()
