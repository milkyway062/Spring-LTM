import ctypes
import ctypes.wintypes
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
_LOBBY_WAIT_TIMEOUT    = 180

# ── session helpers ────────────────────────────────────────────────────────

_k32 = ctypes.windll.kernel32

def _my_session_id() -> int:
    sid = ctypes.c_ulong(0)
    _k32.ProcessIdToSessionId(_k32.GetCurrentProcessId(), ctypes.byref(sid))
    return sid.value


def _proc_session_id(pid: int) -> int | None:
    sid = ctypes.c_ulong(0)
    if _k32.ProcessIdToSessionId(ctypes.c_ulong(pid), ctypes.byref(sid)):
        return sid.value
    return None


_ROBLOX_NAMES = {"robloxplayerbeta.exe", "robloxplayerlauncher.exe", "robloxcrashhandler.exe"}


def _is_roblox_name(name: str) -> bool:
    return name.lower() in _ROBLOX_NAMES


def _roblox_procs_all():
    """All roblox-named processes on this machine."""
    try:
        import psutil
        out = []
        for proc in psutil.process_iter(["name", "pid"]):
            try:
                if _is_roblox_name(proc.name()):
                    out.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return out
    except ImportError:
        return []


def _roblox_procs_session():
    """Roblox processes in OUR Windows session only."""
    my_sid = _my_session_id()
    return [p for p in _roblox_procs_all() if _proc_session_id(p.pid) == my_sid]


def _roblox_running() -> bool:
    return len(_roblox_procs_session()) > 0


def _roblox_window_visible() -> bool:
    """True if a 'Roblox' titled window exists in this session (pygetwindow is session-local)."""
    try:
        import pygetwindow
        return any(w.title == "Roblox" for w in pygetwindow.getAllWindows())
    except Exception:
        return False


# ── exe path ──────────────────────────────────────────────────────────────

def _get_roblox_exe() -> str | None:
    """Registry first (stable across auto-updates), running-process fallback."""
    try:
        from rblib.r_client import get_roblox_path
        path = get_roblox_path()
        if path and os.path.isfile(path):
            return path
    except Exception:
        pass
    try:
        import psutil
        for proc in psutil.process_iter(["name", "exe"]):
            try:
                if "robloxplayerbeta" in proc.name().lower():
                    exe = proc.exe()
                    if exe and os.path.isfile(exe):
                        return exe
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except ImportError:
        pass
    return None


# ── kill ──────────────────────────────────────────────────────────────────

def _kill_roblox(log_cb=print) -> bool:
    """Kill all roblox processes in our session. Returns True when clear."""
    try:
        import psutil
    except ImportError:
        log_cb("Rejoin: psutil not installed — cannot kill")
        return False

    my_sid = _my_session_id()
    all_procs  = _roblox_procs_all()
    sess_procs = [p for p in all_procs if _proc_session_id(p.pid) == my_sid]

    log_cb(
        f"Rejoin: killing {len(sess_procs)} roblox process(es) in session {my_sid} "
        f"({len(all_procs)} total on machine)"
    )

    if not sess_procs:
        return True

    for proc in sess_procs:
        try:
            proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    _, alive = psutil.wait_procs(sess_procs, timeout=10)

    for proc in alive:
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                creationflags=subprocess.CREATE_NO_WINDOW,
                capture_output=True,
            )
        except Exception:
            pass

    deadline = time.time() + 20
    while time.time() < deadline:
        if not _roblox_running():
            log_cb("Rejoin: all session processes terminated")
            return True
        time.sleep(0.5)

    log_cb("Rejoin: WARNING — roblox process(es) still alive after 20s kill attempt")
    return False


# ── private-server URL ────────────────────────────────────────────────────

def _extract_link_code(value: str) -> str:
    from urllib.parse import urlparse, parse_qs
    qs = parse_qs(urlparse(value).query)
    if "privateServerLinkCode" in qs:
        return qs["privateServerLinkCode"][0]
    return value


# ── public API ────────────────────────────────────────────────────────────

def do_rejoin(
    stop_event: threading.Event | None = None,
    log_cb=print,
) -> bool:
    ps_code = macro_state.PRIVATE_SERVER_CODE.strip()
    if not ps_code:
        log_cb("Rejoin: no private server URL configured — skipping")
        return False

    roblox_exe = _get_roblox_exe()
    if not roblox_exe:
        log_cb("Rejoin: RobloxPlayerBeta.exe not found in registry or processes — cannot rejoin")
        return False

    macro_state._rejoin_in_progress = True
    try:
        return _do_rejoin_inner(roblox_exe, ps_code, stop_event, log_cb)
    finally:
        macro_state._rejoin_in_progress = False


def _do_rejoin_inner(roblox_exe, ps_code, stop_event, log_cb) -> bool:
    def stopped() -> bool:
        return stop_event is not None and stop_event.is_set()

    my_sid = _my_session_id()
    log_cb(f"Rejoin: session id={my_sid} | exe={roblox_exe}")

    log_cb("Rejoin: killing Roblox…")
    kill_ok = _kill_roblox(log_cb=log_cb)
    if not kill_ok:
        log_cb("Rejoin: kill did not fully clear — attempting launch anyway")
    if stopped():
        return False

    link_code  = _extract_link_code(ps_code)
    rejoin_url = f"roblox://placeId={_PLACE_ID}&linkCode={link_code}/"

    launched = False
    for attempt in range(1, 4):
        if stopped():
            return False

        log_cb(f"Rejoin: launch attempt {attempt}/3 — {rejoin_url[:60]}…")
        try:
            proc = subprocess.Popen(
                [roblox_exe, rejoin_url],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            log_cb(f"Rejoin: launcher pid={proc.pid}")
        except Exception as exc:
            log_cb(f"Rejoin: Popen failed — {exc}")
            time.sleep(3)
            continue

        # wait for the player process in our session
        deadline = time.time() + 40
        while time.time() < deadline:
            if stopped():
                return False
            if _roblox_running():
                break
            time.sleep(1)
        else:
            log_cb(f"Rejoin: attempt {attempt}/3 — RobloxPlayerBeta never appeared in session")
            _kill_roblox(log_cb=log_cb)
            continue

        # wait for the window to surface (session-local pygetwindow)
        deadline = time.time() + 15
        while time.time() < deadline:
            if stopped():
                return False
            if _roblox_window_visible():
                break
            time.sleep(0.5)
        else:
            log_cb(f"Rejoin: attempt {attempt}/3 — Roblox window did not appear")
            _kill_roblox(log_cb=log_cb)
            continue

        log_cb(f"Rejoin: Roblox running and window visible (attempt {attempt}/3)")
        launched = True
        break

    if not launched:
        log_cb("Rejoin: all 3 launch attempts failed")
        return False

    log_cb("Rejoin: aligning window…")
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
                log_cb("Rejoin: lobby detected")
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
