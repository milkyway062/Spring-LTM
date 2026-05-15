import ctypes
import hashlib
import json
import os
import queue
import sys
import threading
import time
import urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))

import pytesseract as _pt
_pt.pytesseract.tesseract_cmd = os.path.join(_HERE, "tesseract", "tesseract.exe")

for _p in (
    os.path.join(_HERE, "rblib", "src"),
    os.path.join(_HERE, "avlib"),
    os.path.join(_HERE, "core"),
    _HERE,
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import keyboard
import macro_state
import customtkinter as ctk

from macro_gui import (
    MacroApp, MacroSpec, PageSpec, FieldSpec,
    ActionSpec, StatSpec, HotkeySpec,
)
from macro_gui import theme
from macro_gui.pages import run as run_page, settings as settings_page
from macro_gui.pages import log as log_page, update as update_page
from core.runner import Runner

_CONFIG_PATH = os.path.join(_HERE, "config.json")

VERSION = "0.1"

GITHUB_REPO = "milkyway062/Spring-LTM"


# ── config helpers ─────────────────────────────────────────────────────────

def _load_config() -> dict:
    try:
        with open(_CONFIG_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_config(data: dict) -> None:
    with open(_CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _fmt_time(s: float) -> str:
    s = int(max(0, s))
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


# ── single-instance mutex ─────────────────────────────────────────────────

_MUTEX = None


def _single_instance() -> bool:
    global _MUTEX
    _MUTEX = ctypes.windll.kernel32.CreateMutexW(None, True, "SpringLTMMacro_Instance")
    return ctypes.windll.kernel32.GetLastError() != 183


# ── App subclass wiring Spring LTM specifics ──────────────────────────────

class SpringApp(MacroApp):
    def __init__(self, root: ctk.CTk, spec: MacroSpec, cfg: dict):
        self._cfg = cfg
        # Pre-populate field values from saved config
        for f in spec.fields:
            if f.id in cfg:
                spec_default_override = cfg[f.id]
                # will be overwritten by parent via _field_values
        super().__init__(root, spec)
        # Apply saved values
        for f in spec.fields:
            if f.id in cfg:
                self._field_values[f.id] = cfg[f.id]
        self._apply_config()

    def _apply_config(self):
        macro_state.WEBHOOK_URL            = str(self._field_values.get("webhook_url", "")).strip()
        macro_state.PRIVATE_SERVER_CODE    = str(self._field_values.get("private_server", "")).strip()
        macro_state.AUTO_REJOIN_AFTER_RUNS = _parse_int(self._field_values.get("auto_rejoin_runs", 0))
        macro_state.LARGE_LOBBY_ICONS      = bool(self._field_values.get("large_lobby_icons", True))

    def _save_prefs(self):
        self._apply_config()
        _save_config({
            "private_server":    str(self._field_values.get("private_server", "")),
            "webhook_url":       str(self._field_values.get("webhook_url", "")),
            "auto_rejoin_runs":  str(self._field_values.get("auto_rejoin_runs", 0)),
            "large_lobby_icons": bool(self._field_values.get("large_lobby_icons", True)),
        })

    def _on_close(self):
        self._save_prefs()
        if self.spec.on_close:
            self.spec.on_close()
        self.root.destroy()

    # updater wired in
    def _run_update(self):
        BASE_API   = f"https://api.github.com/repos/{GITHUB_REPO}"
        BASE_DIR   = _HERE
        SKIP_FILES = {"config.json"}
        SKIP_DIRS  = {"__pycache__", ".git", ".claude", "tesseract"}

        def git_blob_sha(path):
            try:
                with open(path, "rb") as fh:
                    data = fh.read()
                return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
            except FileNotFoundError:
                return None

        def fetch(url):
            req = urllib.request.Request(url, headers={"User-Agent": "SpringLTM-Updater"})
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.read()

        try:
            repo_info = json.loads(fetch(BASE_API))
            branch    = repo_info.get("default_branch", "master")
            self._set_update_status("Fetching file list…")

            tree_data = json.loads(fetch(f"{BASE_API}/git/trees/{branch}?recursive=1"))
            to_update = []
            for item in tree_data.get("tree", []):
                if item["type"] != "blob":
                    continue
                path  = item["path"]
                parts = path.replace("\\", "/").split("/")
                if any(p in SKIP_DIRS for p in parts[:-1]):
                    continue
                if parts[-1] in SKIP_FILES:
                    continue
                local_path = os.path.join(BASE_DIR, *parts)
                if git_blob_sha(local_path) != item["sha"]:
                    to_update.append((path, parts))

            if not to_update:
                self._set_update_status("Already up to date!")
                return

            for i, (path, parts) in enumerate(to_update):
                self._set_update_status(f"Updating {parts[-1]} ({i + 1}/{len(to_update)})…")
                data       = fetch(f"https://raw.githubusercontent.com/{GITHUB_REPO}/{branch}/{path}")
                local_path = os.path.join(BASE_DIR, *parts)
                os.makedirs(os.path.dirname(local_path) or BASE_DIR, exist_ok=True)
                with open(local_path, "wb") as fh:
                    fh.write(data)

            self._set_update_status(f"Updated {len(to_update)} file(s) — restart to apply.")

        except Exception as exc:
            self._set_update_status(f"Update failed: {exc}")
        finally:
            if self._update_btn:
                self.root.after(0, lambda: self._update_btn.configure(
                    state="normal", text="Check for Updates"))


def _parse_int(val) -> int:
    try:
        return max(0, int(val))
    except (ValueError, TypeError):
        return 0


# ── entry ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not _single_instance():
        import tkinter.messagebox as mb
        import tkinter as tk
        _r = tk.Tk(); _r.withdraw()
        mb.showerror("Already running", "Spring LTM Macro is already running.")
        _r.destroy()
        sys.exit(1)

    cfg = _load_config()
    log_q: queue.Queue = queue.Queue(maxsize=600)

    spec = MacroSpec(
        title="Spring LTM",
        version=VERSION,
        accent=theme.ACCENT,
        pages=(
            PageSpec("run",      "RUN",      "run",      run_page.build),
            PageSpec("settings", "SETTINGS", "settings", settings_page.build),
            PageSpec("log",      "LOG",      "log",      log_page.build),
            PageSpec("update",   "UPDATE",   "update",   update_page.build),
        ),
        hotkeys=(
            HotkeySpec("f1", "F1 Start", "start"),
            HotkeySpec("f3", "F3 Stop",  "stop"),
        ),
        actions={
            "start": ActionSpec("start", "▶  Start", "primary", lambda: runner.start()),
            "stop":  ActionSpec("stop",  "■  Stop",  "danger",  lambda: runner.stop()),
            "align": ActionSpec("align", "⊡  Align", "neutral", lambda: runner.align()),
        },
        fields=(
            FieldSpec("auto_rejoin_runs", "Rejoin every (runs)", "int",     cfg.get("auto_rejoin_runs", 0),
                      help="0 = off"),
            FieldSpec("private_server",   "Private server URL",  "text",    cfg.get("private_server", "")),
            FieldSpec("webhook_url",      "Webhook URL",         "password", cfg.get("webhook_url", "")),
            FieldSpec("large_lobby_icons","Large area icons",    "bool",    cfg.get("large_lobby_icons", True)),
        ),
        stats=(
            StatSpec("runs",         "RUNS",
                     lambda: str(macro_state.state["total_runs"])),
            StatSpec("since_rejoin", "SINCE REJOIN",
                     lambda: str(macro_state.state["runs_since_rejoin"])),
            StatSpec("session",      "SESSION",
                     lambda: _fmt_time(time.time() - macro_state.state["session_start"])
                     if macro_state.state["session_start"] > 0 else "—"),
            StatSpec("run",          "RUN",
                     lambda: _fmt_time(time.time() - macro_state.state["run_start"])
                     if macro_state.state.get("running") and macro_state.state["run_start"] > 0 else "—"),
        ),
        log_queue=log_q,
        status_getter=lambda: (macro_state.state.get("running") and "running" or "idle", ""),
    )

    root = ctk.CTk()
    app  = SpringApp(root, spec, cfg)

    # Runner needs app reference; actions use closures so this works
    runner = Runner(app)
    # Patch action callbacks now that runner exists (lambdas already capture runner ref above)

    keyboard.on_press_key("f1", lambda _: root.after(0, runner.start))
    keyboard.on_press_key("f3", lambda _: root.after(0, runner.stop))

    app.run()
