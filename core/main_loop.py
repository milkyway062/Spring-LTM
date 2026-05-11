import os
import sys
import time
import threading

try:
    import keyboard
except ImportError:
    keyboard = None

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (
    os.path.join(_BASE, "rblib", "src"),
    os.path.join(_BASE, "avlib"),
    os.path.join(_BASE, "core"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from rblib import r_input, r_util
from AnimeVangaurdsLibrary.tools.av_game import start, read_wave, restart_match
from AnimeVangaurdsLibrary.tools.av_unit import place_unit

from position_setup import setup_position
import macro_state


def _tracked_wave() -> int:
    val = read_wave()
    if val >= 1:
        macro_state.state["last_wave_seen"] = time.time()
    return val

NINJUTSU_SELL_NO  = (466, 369)
NINJUTSU_SELL_YES = (355, 370)
_PLACEMENT_IMG    = os.path.join(_BASE, "Images", "PlacementPhase.png")
_PLACEMENT_REGION = (730, 150, 55, 47)


def ninjutsu_sell_no() -> None:
    r_input.Click(*NINJUTSU_SELL_NO, 0.1)


def ninjutsu_sell_yes() -> None:
    r_input.Click(*NINJUTSU_SELL_YES, 0.1)


def place_ninjutsu(hotbar_index: int, pos: tuple[int, int], dismiss=ninjutsu_sell_no, wait: float = 0.5) -> None:
    r_input.PressKey(str(hotbar_index))
    r_input.Click(*pos, 0.1)
    time.sleep(wait)
    dismiss()
    time.sleep(0.3)


def run(stop_event: threading.Event | None = None, log_cb=print) -> None:
    def stopped() -> bool:
        return stop_event is not None and stop_event.is_set()

    macro_state.state["last_wave_seen"] = time.time()
    setup_position(log_cb=log_cb)
    if stopped(): return

    log_cb("Loop: voting start")
    start()
    time.sleep(0.2)
    r_input.Click(590, 172, 0.1)
    if stopped(): return

    log_cb("Loop: placing slot 5")
    place_unit(5, (446, 272), auto_upgrade=True)
    if stopped(): return

    log_cb("Loop: placing slot 3")
    place_unit(3, (185, 114))
    if stopped(): return

    log_cb("Loop: placing slot 2 (unit 1)")
    place_unit(2, (234, 115))
    if stopped(): return

    log_cb("Loop: placing slot 2 (unit 2)")
    place_unit(2, (216, 128))
    if stopped(): return

    log_cb("Loop: placing slot 6")
    place_unit(6, (491, 318), auto_upgrade=True)
    if stopped(): return

    log_cb("Loop: placing slot 2 (unit 3)")
    place_unit(2, (254, 105))
    if stopped(): return

    log_cb("Loop: placing slot 3 (unit 2)")
    place_ninjutsu(3, (199, 103))
    if stopped(): return

    log_cb("Loop: placing slot 1 (unit 1)")
    place_unit(1, (151, 129))
    if stopped(): return

    log_cb("Loop: placing slot 1 (unit 2)")
    place_unit(1, (169, 136))
    if stopped(): return

    log_cb("Loop: placing slot 1 (unit 3)")
    place_unit(1, (190, 145))
    if stopped(): return

    log_cb("Loop: placing slot 3 (unit 3)")
    place_ninjutsu(3, (171, 101))
    if stopped(): return

    log_cb("Loop: placing slot 4 (unit 1)")
    place_ninjutsu(4, (215, 99))
    if stopped(): return

    log_cb("Loop: placing slot 4 (unit 2)")
    place_ninjutsu(4, (192, 122))
    if stopped(): return

    log_cb("Loop: placing slot 4 (unit 3)")
    place_ninjutsu(4, (207, 107))
    if stopped(): return
    time.sleep(0.3)
    r_input.PressKey("e")
    time.sleep(0.5)

    log_cb("Loop: waiting for wave 5...")
    while not stopped():
        if _tracked_wave() >= 5 and _tracked_wave() >= 5:
            break
        time.sleep(0.3)
    if stopped(): return

    log_cb("Loop: waiting for wave 20...")
    while not stopped() and _tracked_wave() < 20:
        while not stopped() and not r_util.imageExists(_PLACEMENT_IMG, 0.8, region=_PLACEMENT_REGION):
            r_input.Click(282, 240, 0.1)
        if stopped(): return
        r_input.Click(666, 105, 0.2)
        r_input.Click(589, 173, 0.2)
        while not stopped() and r_util.imageExists(_PLACEMENT_IMG, 0.8, region=_PLACEMENT_REGION):
            time.sleep(0.1)
        if stopped(): return
        r_input.PressKey("e")
    if stopped(): return

    log_cb("Loop: restarting match")
    restart_match()


if __name__ == "__main__":
    _stop = threading.Event()

    def _killswitch():
        print("\n[F3] Killswitch triggered — stopping...")
        os._exit(0)

    if keyboard:
        keyboard.add_hotkey("f3", _killswitch)
        print("Press F3 to stop.")
    else:
        print("Warning: 'keyboard' not installed — F3 killswitch disabled.")

    run(stop_event=_stop)
    print("Stopped.")
