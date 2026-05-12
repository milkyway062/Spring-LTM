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
from rblib.r_client import focus_roblox_window

logger = logging.getLogger(__name__)

_PLACE_ID              = 16146832113
_ROBLOX_LAUNCH_TIMEOUT = 120
_LOBBY_WAIT_TIMEOUT    = 180


def _get_roblox_exe() -> str | None:
    try:
        import psutil
        for proc in psutil.process_iter(["name", "exe"]):
            try:
                if "robloxplayerbeta" in proc.name().lower():
                    return proc.exe()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except ImportError:
        logger.warning("psutil not installed")
    return None


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
        pass


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


def _extract_link_code(value: str) -> str:
    from urllib.parse import urlparse, parse_qs
    qs = parse_qs(urlparse(value).query)
    if "privateServerLinkCode" in qs:
        return qs["privateServerLinkCode"][0]
    return value


def _get_roblox_exe_any() -> str | None:
    """Return Roblox exe path from running process or Windows registry fallback."""
    exe = _get_roblox_exe()
    if exe:
        return exe
    try:
        from rblib.r_client import get_roblox_path
        path = get_roblox_path()
        if path and os.path.isfile(path):
            return path
    except Exception:
        pass
    return None


def do_rejoin(
    stop_event: threading.Event | None = None,
    log_cb=print,
) -> bool:
    """Kill Roblox, relaunch directly into the private server, wait for lobby."""
    ps_code = macro_state.PRIVATE_SERVER_CODE.strip()
    if not ps_code:
        log_cb("Rejoin: no private server URL configured — skipping")
        return False

    roblox_exe = _get_roblox_exe_any()
    if not roblox_exe:
        log_cb("Rejoin: RobloxPlayerBeta.exe not found in processes or registry — cannot rejoin")
        return False

    macro_state._rejoin_in_progress = True
    try:
        return _do_rejoin_inner(roblox_exe, ps_code, stop_event, log_cb)
    finally:
        macro_state._rejoin_in_progress = False


def _do_rejoin_inner(roblox_exe, ps_code, stop_event, log_cb) -> bool:
    def stopped() -> bool:
        return stop_event is not None and stop_event.is_set()

    log_cb("Rejoin: killing Roblox…")
    _kill_roblox()
    kill_deadline = time.time() + 15
    while _roblox_running():
        if stopped():
            return False
        if time.time() >= kill_deadline:
            log_cb("Rejoin: Roblox process still alive after 15s — proceeding anyway")
            break
        time.sleep(0.5)

    link_code  = _extract_link_code(ps_code)
    rejoin_url = f"roblox://placeId={_PLACE_ID}&linkCode={link_code}/"
    log_cb(f"Rejoin: launching {rejoin_url[:60]}…")
    try:
        subprocess.Popen([roblox_exe, rejoin_url])
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

    log_cb("Rejoin: aligning Roblox window…")
    time.sleep(2)
    try:
        focus_roblox_window()
    except Exception:
        pass

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

    log_cb("Rejoin: complete")
    return True
