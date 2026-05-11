import logging
import subprocess
import sys
import os
import time
import threading

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (
    os.path.join(_BASE, "rblib", "src"),
    os.path.join(_BASE, "avlib"),
    os.path.join(_BASE, "core"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import macro_state

logger = logging.getLogger(__name__)

_ROBLOX_LAUNCH_TIMEOUT = 120
_LOBBY_WAIT_TIMEOUT    = 180


def _kill_roblox() -> None:
    try:
        import psutil
        for proc in psutil.process_iter(["name"]):
            try:
                if "roblox" in proc.name().lower():
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except ImportError:
        logger.warning("psutil not installed — cannot kill Roblox processes")


def _roblox_running() -> bool:
    try:
        import psutil
        for proc in psutil.process_iter(["name"]):
            try:
                if "robloxplayerbeta" in proc.name().lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except ImportError:
        pass
    return False


def do_rejoin(
    stop_event: threading.Event | None = None,
    log_cb=print,
) -> bool:
    """Kill Roblox, relaunch via the private server URL, wait for lobby."""
    def stopped() -> bool:
        return stop_event is not None and stop_event.is_set()

    ps_code = macro_state.PRIVATE_SERVER_CODE.strip()
    if not ps_code:
        log_cb("Rejoin: no private server URL configured — skipping")
        return False

    log_cb("Rejoin: killing Roblox…")
    _kill_roblox()
    for _ in range(20):
        if stopped():
            return False
        time.sleep(0.1)

    log_cb("Rejoin: launching private server…")
    try:
        subprocess.Popen(["start", "", ps_code], shell=True)
    except Exception as exc:
        log_cb(f"Rejoin: launch failed — {exc}")
        return False

    log_cb("Rejoin: waiting for Roblox process…")
    deadline = time.time() + _ROBLOX_LAUNCH_TIMEOUT
    while time.time() < deadline:
        if stopped():
            return False
        if _roblox_running():
            break
        time.sleep(2)
    else:
        log_cb("Rejoin: timed out waiting for Roblox to launch")
        return False

    log_cb("Rejoin: waiting for lobby to load…")
    deadline = time.time() + _LOBBY_WAIT_TIMEOUT
    while time.time() < deadline:
        if stopped():
            return False
        try:
            from lobby_path import is_in_lobby
            if is_in_lobby():
                break
        except Exception:
            pass
        time.sleep(3)
    else:
        log_cb("Rejoin: timed out waiting for lobby — continuing anyway")

    try:
        import position_setup
        position_setup._first_run = True
    except Exception:
        pass

    try:
        from rblib.r_client import focus_roblox_window
        focus_roblox_window()
    except Exception:
        pass

    log_cb("Rejoin: complete")
    return True
