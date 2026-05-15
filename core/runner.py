"""Worker thread, watchdogs, and restart logic extracted from gui.py."""
from __future__ import annotations
import ctypes
import threading
import time

import macro_state
import webhook
from main_loop import run
from lobby_path import do_lobby_path, is_in_lobby, is_in_game
from rejoin import do_rejoin, _roblox_running
from rblib.r_client import focus_roblox_window

import os
_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DISCONNECT_IMG = os.path.join(_HERE, "Images", "Disconnected.png")
_STUCK_TIMEOUT = 180


class Runner:
    def __init__(self, app):
        """app: MacroApp — used for log/status/phase callbacks."""
        self._app = app
        self._thread:     threading.Thread | None = None
        self._stop_event: threading.Event         = threading.Event()

    # ── public controls ───────────────────────────────────────────

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        from macro_gui import theme
        self._app._apply_config()
        self._stop_event.clear()
        self._app.set_status("running", theme.OK)
        self._app.set_phase("Starting…")
        self._app.set_action_state("start", False)
        self._app.set_action_state("stop",  True)
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self):
        self._app._save_prefs()
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_ulong(self._thread.ident),
                ctypes.py_object(SystemExit),
            )
        from macro_gui import theme
        self._app.set_status("stopping…", theme.WARN)
        self._app.set_action_state("stop", False)

    def align(self):
        focus_roblox_window()
        self._app.set_phase("Window aligned")

    # ── watchdogs ─────────────────────────────────────────────────

    def _disconnect_watcher(self):
        from rblib import r_util, r_input
        while not self._stop_event.is_set() and macro_state.state.get("running"):
            try:
                if r_util.imageExists(_DISCONNECT_IMG, 0.85):
                    self._log("Disconnect detected — dismissing dialog")
                    self._set_phase("Disconnected — reconnecting…")
                    self._set_dot_err()
                    r_input.Click(408, 371, 0.3)
                    macro_state._disconnect_event.set()
                    if self._thread and self._thread.is_alive():
                        ctypes.pythonapi.PyThreadState_SetAsyncExc(
                            ctypes.c_ulong(self._thread.ident),
                            ctypes.py_object(SystemExit),
                        )
                    return
            except Exception:
                pass
            time.sleep(2)

    def _crash_watcher(self):
        time.sleep(15)
        consecutive = 0
        while not self._stop_event.is_set() and macro_state.state.get("running"):
            if macro_state._rejoin_in_progress:
                consecutive = 0
                time.sleep(5)
                continue
            if not _roblox_running():
                consecutive += 1
                if consecutive >= 2:
                    self._log("Roblox crash detected — restarting…")
                    self._set_phase("Roblox crashed — restarting…")
                    self._set_dot_err()
                    macro_state._crash_event.set()
                    if self._thread and self._thread.is_alive():
                        ctypes.pythonapi.PyThreadState_SetAsyncExc(
                            ctypes.c_ulong(self._thread.ident),
                            ctypes.py_object(SystemExit),
                        )
                    return
            else:
                consecutive = 0
            time.sleep(5)

    def _stuck_watcher(self):
        while not self._stop_event.is_set() and macro_state.state.get("running"):
            time.sleep(10)
            if self._stop_event.is_set() or not macro_state.state.get("running"):
                break
            last = macro_state.state.get("last_wave_seen", 0.0)
            if last > 0 and time.time() - last > _STUCK_TIMEOUT:
                self._log("Stuck: no wave for 3 min — force rejoining")
                self._set_phase("Stuck — force rejoin…")
                self._set_dot_err()
                macro_state._stuck_event.set()
                if self._thread and self._thread.is_alive():
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(
                        ctypes.c_ulong(self._thread.ident),
                        ctypes.py_object(SystemExit),
                    )
                return

    # ── worker ────────────────────────────────────────────────────

    def _worker(self):
        _was_disconnect  = macro_state._disconnect_event.is_set()
        _was_match_ended = macro_state._match_ended_event.is_set()
        macro_state._disconnect_event.clear()
        macro_state._match_ended_event.clear()
        macro_state._auto_rejoin_event.clear()
        macro_state._crash_event.clear()
        macro_state.state.update({
            "session_start":     macro_state.state.get("session_start") or time.time(),
            "total_runs":        macro_state.state.get("total_runs", 0),
            "runs_since_rejoin": macro_state.state.get("runs_since_rejoin", 0),
            "running":           True,
            "last_wave_seen":    time.time(),
        })

        threading.Thread(target=self._disconnect_watcher, daemon=True).start()
        threading.Thread(target=self._stuck_watcher,      daemon=True).start()
        threading.Thread(target=self._crash_watcher,      daemon=True).start()

        try:
            if macro_state._stuck_event.is_set():
                macro_state._stuck_event.clear()
                self._log("Stuck watchdog: force rejoining Roblox…")
                self._set_phase("Force rejoin…")
                ok = do_rejoin(stop_event=self._stop_event, log_cb=self._log)
                if not ok or self._stop_event.is_set():
                    return
                macro_state.state["runs_since_rejoin"] = 0

            if _was_disconnect:
                self._log("Disconnect recovery — rejoining private server…")
                self._set_phase("Rejoining after disconnect…")
                ok = do_rejoin(stop_event=self._stop_event, log_cb=self._log)
                if not ok or self._stop_event.is_set():
                    return
                macro_state.state["runs_since_rejoin"] = 0

            if _was_match_ended:
                self._log("Match ended — rejoining for next run…")
                self._set_phase("Rejoining after match…")
                ok = do_rejoin(stop_event=self._stop_event, log_cb=self._log)
                if not ok or self._stop_event.is_set():
                    return
                macro_state.state["runs_since_rejoin"] = 0

            if not _roblox_running():
                self._log("Roblox not running — launching…")
                self._set_phase("Launching Roblox…")
                ok = do_rejoin(stop_event=self._stop_event, log_cb=self._log)
                if not ok and not self._stop_event.is_set():
                    self._log("Launch: first attempt failed — retrying once…")
                    time.sleep(3)
                    ok = do_rejoin(stop_event=self._stop_event, log_cb=self._log)
                if not ok or self._stop_event.is_set():
                    self._log("Launch: failed to open Roblox — stopping")
                    self._set_phase("Launch failed — stopped")
                    self._set_dot_err()
                    return

            if macro_state._just_rejoined:
                macro_state._just_rejoined = False
                self._log("Post-rejoin — assuming lobby, pathing to Spring LTM")
                self._set_phase("Lobby pathing…")
                do_lobby_path(stop_event=self._stop_event, log_cb=self._log)
                macro_state.state["last_wave_seen"] = time.time()
            else:
                _deadline = time.time() + 120
                _found_lobby = _found_game = False
                while time.time() < _deadline and not self._stop_event.is_set():
                    if is_in_lobby():
                        _found_lobby = True; break
                    if is_in_game():
                        _found_game = True; break
                    time.sleep(2)
                if self._stop_event.is_set():
                    return
                if _found_lobby:
                    self._log("Lobby detected — pathing to Spring LTM")
                    self._set_phase("Lobby pathing…")
                    do_lobby_path(stop_event=self._stop_event, log_cb=self._log)
                    macro_state.state["last_wave_seen"] = time.time()
                elif _found_game:
                    self._log("Game instance detected — skipping lobby path")
                    macro_state.state["last_wave_seen"] = time.time()
                else:
                    self._log("Warning: lobby/game not detected within 120s — continuing")

            while not self._stop_event.is_set():
                run_start = time.time()
                macro_state.state["run_start"] = run_start
                self._set_phase(f"Run {macro_state.state['total_runs'] + 1}")

                run(stop_event=self._stop_event, log_cb=self._log)

                if self._stop_event.is_set():
                    break
                if macro_state._match_ended_event.is_set():
                    self._log("Match ended — rejoining for next run")
                    break

                elapsed = time.time() - run_start
                macro_state.state["total_runs"]        += 1
                macro_state.state["total_run_time"]    += elapsed
                macro_state.state["last_run_time"]      = elapsed
                macro_state.state["runs_since_rejoin"] += 1
                macro_state.state["last_wave_seen"]     = time.time()

                n     = macro_state.AUTO_REJOIN_AFTER_RUNS
                since = macro_state.state["runs_since_rejoin"]
                if n > 0:
                    self._log(f"Run done — {since}/{n} runs since rejoin")
                else:
                    self._log(f"Run done — run #{macro_state.state['total_runs']} (auto rejoin off)")

                threading.Thread(
                    target=webhook.send, args=(elapsed,), daemon=True).start()

                if n > 0 and since >= n:
                    self._log(f"Auto rejoin: {n} runs reached — rejoining")
                    self._set_phase("Auto rejoin…")
                    ok = do_rejoin(stop_event=self._stop_event, log_cb=self._log)
                    if not ok and not self._stop_event.is_set():
                        self._log("Auto rejoin: first attempt failed — retrying…")
                        time.sleep(3)
                        ok = do_rejoin(stop_event=self._stop_event, log_cb=self._log)
                    if not ok or self._stop_event.is_set():
                        self._log("Auto rejoin: failed — stopping")
                        self._set_phase("Rejoin failed — stopped")
                        self._set_dot_err()
                        return
                    macro_state.state["runs_since_rejoin"] = 0
                    macro_state.state["last_wave_seen"]    = time.time()
                    macro_state._auto_rejoin_event.set()
                    break

            self._set_phase("Stopped")

        except Exception as exc:
            self._log(f"ERROR: {exc}")
            self._set_dot_err()
            self._set_phase(f"Error: {exc}")
        finally:
            macro_state.state["running"] = False
            root = self._app.root
            if macro_state._stuck_event.is_set() and not self._stop_event.is_set():
                root.after(0, self._restart_after_stuck)
            elif macro_state._crash_event.is_set() and not self._stop_event.is_set():
                root.after(0, self._restart)
            elif macro_state._disconnect_event.is_set() and not self._stop_event.is_set():
                root.after(0, self._restart_after_disconnect)
            elif macro_state._match_ended_event.is_set() and not self._stop_event.is_set():
                root.after(0, self._restart)
            elif macro_state._auto_rejoin_event.is_set() and not self._stop_event.is_set():
                root.after(0, self._restart)
            else:
                root.after(0, self._on_idle)

    # ── restart helpers ───────────────────────────────────────────

    def _restart(self):
        from macro_gui import theme
        self._app.set_status("rejoining…", theme.WARN)
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _restart_after_disconnect(self):
        try:
            focus_roblox_window()
        except Exception:
            pass
        self._restart()

    def _restart_after_stuck(self):
        self._restart()

    def _on_idle(self):
        from macro_gui import theme
        self._app.set_action_state("start", True)
        self._app.set_action_state("stop",  False)
        self._app.set_status("idle", theme.BORDER_HI)

    # ── helpers ───────────────────────────────────────────────────

    def _log(self, msg: str):
        self._app.log(msg)

    def _set_phase(self, text: str):
        self._app.set_phase(text)

    def _set_dot_err(self):
        from macro_gui import theme
        self._app.set_status("error", theme.ERR)
