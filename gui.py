import ctypes
import json
import os
import queue
import sys
import threading
import time
import tkinter as tk

_HERE = os.path.dirname(os.path.abspath(__file__))

import pytesseract as _pt
_pt.pytesseract.tesseract_cmd = os.path.join(_HERE, "tesseract", "tesseract.exe")

for _p in (
    os.path.join(_HERE, "rblib", "src"),
    os.path.join(_HERE, "avlib"),
    os.path.join(_HERE, "core"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import keyboard
import macro_state
import webhook
from main_loop import run
from lobby_path import do_lobby_path, is_in_lobby
from rblib.r_client import focus_roblox_window

_CONFIG_PATH = os.path.join(_HERE, "config.json")

def _load_config() -> dict:
    try:
        with open(_CONFIG_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _save_config(data: dict) -> None:
    with open(_CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ── Palette ────────────────────────────────────────────────────────────────
BG      = "#13120f"
SURFACE = "#1a1916"
CARD    = "#1f1d19"
CARD2   = "#252320"
BORDER  = "#2e2b24"
BORDER2 = "#3a3730"
ENTRY   = "#17160f"
FG      = "#e8e0d0"
FG_DIM  = "#7a7060"
FG_MID  = "#a89880"
SEL_BG  = "#2e2b24"

GREEN   = "#6dbb5e"
GREEN_D = "#3d7a30"
GREEN_A = "#58a04a"
RED     = "#c45c5c"
RED_D   = "#7a2828"
RED_A   = "#a84444"
AMBER   = "#d49030"
AMBER_A = "#b87820"
BLUE    = "#5b8dd9"

_DOT_IDLE = "#3a3730"
_DOT_RUN  = GREEN
_DOT_STOP = AMBER
_DOT_ERR  = RED

FONT_UI    = ("Segoe UI",          10)
FONT_LABEL = ("Segoe UI",           9)
FONT_SMALL = ("Segoe UI",           8)
FONT_TITLE = ("Segoe UI Semibold", 12)
FONT_STAT  = ("Segoe UI Semibold", 22)
FONT_MONO  = ("Consolas",           9)

WIN_W = 460


# ── Helpers ────────────────────────────────────────────────────────────────

def _hover(w, n, a):
    w.bind("<Enter>", lambda _: w.config(bg=a))
    w.bind("<Leave>", lambda _: w.config(bg=n))

def _fmt_time(s: float) -> str:
    s = int(max(0, s))
    return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"


# ── GUI ────────────────────────────────────────────────────────────────────

class MacroGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Spring LTM Macro")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.geometry(f"{WIN_W}x1")

        self._thread:     threading.Thread | None = None
        self._stop_event: threading.Event         = threading.Event()
        self._log_queue:  queue.Queue             = queue.Queue(maxsize=600)
        self._pulse:      bool                    = False
        self._cfg                                 = _load_config()

        self._build_ui()
        self._apply_config()
        self._tick()
        self.root.update_idletasks()
        self.root.geometry(f"{WIN_W}x{self.root.winfo_reqheight()}")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        keyboard.on_press_key("f1", lambda _: self.root.after(0, self._on_start))
        keyboard.on_press_key("f3", lambda _: self.root.after(0, self._on_stop))

    # ── widget factories ───────────────────────────────────────

    def _section(self, title: str) -> tk.Frame:
        row = tk.Frame(self.root, bg=BG)
        row.pack(fill="x", padx=14, pady=(10, 0))
        tk.Frame(row, bg=BORDER, height=1).pack(side="left", fill="y", padx=(0, 6))
        tk.Label(row, text=title, bg=BG, fg=FG_DIM,
                 font=FONT_SMALL).pack(side="left")
        tk.Frame(row, bg=BORDER, height=1).pack(side="left", fill="both",
                                                 expand=True, padx=(6, 0))
        outer = tk.Frame(self.root, bg=BORDER2)
        outer.pack(fill="x", padx=14, pady=(4, 0))
        inner = tk.Frame(outer, bg=CARD)
        inner.pack(fill="x", padx=1, pady=1)
        return inner

    def _btn(self, parent, text, cmd, bg, hbg,
             width=None, font=FONT_UI, state="normal", fg=FG):
        kw = dict(text=text, bg=bg, fg=fg,
                  activebackground=hbg, activeforeground=fg,
                  relief="flat", bd=0, cursor="hand2",
                  font=font, command=cmd, state=state,
                  padx=16, pady=8)
        if width:
            kw["width"] = width
        b = tk.Button(parent, **kw)
        if state != "disabled":
            _hover(b, bg, hbg)
        return b

    def _entry(self, parent, var, width=None, show=None):
        kw = dict(textvariable=var, bg=ENTRY, fg=FG,
                  insertbackground=FG, selectbackground=SEL_BG,
                  selectforeground=FG, relief="flat", bd=0,
                  font=FONT_UI, highlightthickness=1,
                  highlightbackground=BORDER2, highlightcolor=AMBER)
        if width:
            kw["width"] = width
        if show:
            kw["show"] = show
        e = tk.Entry(parent, **kw)
        e.bind("<FocusIn>",  lambda _: e.config(highlightbackground=AMBER))
        e.bind("<FocusOut>", lambda _: e.config(highlightbackground=BORDER2))
        return e

    def _row(self, parent, pady=(4, 4)) -> tk.Frame:
        f = tk.Frame(parent, bg=CARD)
        f.pack(fill="x", padx=14, pady=pady)
        return f

    def _field_label(self, parent, text, width=15):
        tk.Label(parent, text=text, bg=CARD, fg=FG_MID,
                 font=FONT_LABEL, width=width, anchor="w").pack(side="left")

    def _sep(self, parent, color=BORDER):
        tk.Frame(parent, bg=color, height=1).pack(fill="x")

    # ── build ──────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_controls()
        self._build_stats()
        self._build_config()
        self._build_status()
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(14, 6))

        left = tk.Frame(hdr, bg=BG)
        left.pack(side="left")
        tk.Label(left, text="◆", bg=BG, fg=BLUE,
                 font=("Segoe UI", 14)).pack(side="left", padx=(0, 6))
        tk.Label(left, text="Spring LTM Macro", bg=BG, fg=FG,
                 font=FONT_TITLE).pack(side="left")

        right = tk.Frame(hdr, bg=BG)
        right.pack(side="right")
        self._dot_cv = tk.Canvas(right, width=8, height=8,
                                  bg=BG, highlightthickness=0)
        self._dot_cv.pack(side="left", padx=(0, 6))
        self._dot_id = self._dot_cv.create_oval(1, 1, 7, 7,
                                                  fill=_DOT_IDLE, outline="")
        self._status_var = tk.StringVar(value="idle")
        tk.Label(right, textvariable=self._status_var,
                 bg=BG, fg=FG_DIM, font=FONT_LABEL).pack(side="left")

    def _build_controls(self):
        inner = self._section("CONTROLS")

        row = tk.Frame(inner, bg=CARD)
        row.pack(fill="x", padx=12, pady=12)

        self._start_btn = self._btn(row, "▶  Start", self._on_start,
                                    GREEN_D, GREEN_A, fg="#d0f0c0")
        self._start_btn.pack(side="left", padx=(0, 6))

        self._stop_btn = self._btn(row, "■  Stop", self._on_stop,
                                   RED_D, RED_A, fg="#f0d0d0", state="disabled")
        self._stop_btn.pack(side="left", padx=(0, 6))

        self._align_btn = self._btn(row, "⊡  Align", self._on_align,
                                    CARD2, BORDER2)
        self._align_btn.pack(side="left")

        tk.Label(row, text="F1  /  F3", bg=CARD, fg=FG_DIM,
                 font=FONT_SMALL).pack(side="right", padx=2)

    def _build_stats(self):
        inner = self._section("STATS")

        nums = tk.Frame(inner, bg=CARD)
        nums.pack(fill="x", padx=14, pady=(14, 10))

        self._runs_var = tk.StringVar(value="0")
        blk = tk.Frame(nums, bg=CARD)
        blk.pack(side="left")
        tk.Label(blk, textvariable=self._runs_var, bg=CARD, fg=FG,
                 font=FONT_STAT).pack(anchor="w")
        tk.Label(blk, text="RUNS", bg=CARD, fg=FG_DIM,
                 font=("Segoe UI", 7)).pack(anchor="w")

        self._sep(inner)

        timers = tk.Frame(inner, bg=CARD)
        timers.pack(fill="x", padx=14, pady=(8, 14))

        self._sess_var     = tk.StringVar(value="00:00:00")
        self._run_var      = tk.StringVar(value="00:00:00")
        self._last_run_var = tk.StringVar(value="—")

        for label, var in (
            ("Session", self._sess_var),
            ("Run",     self._run_var),
            ("Last",    self._last_run_var),
        ):
            blk = tk.Frame(timers, bg=CARD)
            blk.pack(side="left", padx=(0, 24))
            tk.Label(blk, text=label, bg=CARD, fg=FG_DIM,
                     font=FONT_SMALL).pack(side="left", padx=(0, 5))
            tk.Label(blk, textvariable=var, bg=CARD, fg=FG,
                     font=FONT_LABEL).pack(side="left")

    def _build_config(self):
        inner = self._section("CONFIG")

        row = self._row(inner, pady=(12, 4))
        self._field_label(row, "Private Server")
        self._ps_var = tk.StringVar(value=self._cfg.get("private_server", ""))
        self._entry(row, self._ps_var).pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._btn(row, "Join", self._on_join_ps, CARD2, BORDER2,
                  font=FONT_LABEL).pack(side="left")

        row = self._row(inner, pady=(4, 12))
        self._field_label(row, "Webhook URL")
        self._wh_var = tk.StringVar(value=self._cfg.get("webhook_url", ""))
        wh = self._entry(row, self._wh_var)
        wh.pack(side="left", fill="x", expand=True)
        wh.bind("<FocusOut>", lambda _: self._save_prefs())
        wh.bind("<Return>",   lambda _: self._save_prefs())

        for var in (self._ps_var,):
            var.trace_add("write", lambda *_: self._save_prefs())

    def _build_status(self):
        inner = self._section("STATUS")
        self._phase_var = tk.StringVar(value="—")
        tk.Label(inner, textvariable=self._phase_var,
                 bg=CARD, fg=FG_MID, font=FONT_LABEL,
                 anchor="w", padx=14, pady=8).pack(fill="x")

    def _build_footer(self):
        foot = tk.Frame(self.root, bg=BG)
        foot.pack(fill="x", padx=14, pady=(10, 10))

        self._show_log = tk.BooleanVar(value=False)
        tk.Checkbutton(foot, text="Show log", variable=self._show_log,
                       command=self._toggle_log,
                       bg=BG, fg=FG_DIM, selectcolor=ENTRY,
                       activebackground=BG, activeforeground=FG,
                       font=FONT_SMALL, bd=0, cursor="hand2").pack(side="left")

        self._log_frame = tk.Frame(self.root, bg=SURFACE, bd=0)
        self._log_frame.pack(fill="x", padx=14, pady=(0, 10))
        self._log_frame.pack_forget()

        self._log_text = tk.Text(
            self._log_frame, height=9, state="disabled", wrap="word",
            font=FONT_MONO, bg=SURFACE, fg=FG_DIM, relief="flat", bd=0,
            padx=10, pady=8, insertbackground=FG, selectbackground=SEL_BG,
        )
        sb = tk.Scrollbar(self._log_frame, command=self._log_text.yview,
                          bg=SURFACE, troughcolor=BG, width=10, relief="flat")
        self._log_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._log_text.pack(side="left", fill="both", expand=True)

    # ── config persistence ─────────────────────────────────────

    def _apply_config(self):
        macro_state.WEBHOOK_URL         = self._wh_var.get().strip()
        macro_state.PRIVATE_SERVER_CODE = self._ps_var.get().strip()

    def _save_prefs(self):
        macro_state.WEBHOOK_URL         = self._wh_var.get().strip()
        macro_state.PRIVATE_SERVER_CODE = self._ps_var.get().strip()
        _save_config({
            "private_server": self._ps_var.get().strip(),
            "webhook_url":    self._wh_var.get().strip(),
        })

    # ── worker ─────────────────────────────────────────────────

    def _worker(self):
        macro_state.state.update({
            "session_start": time.time(),
            "total_runs":    0,
            "running":       True,
        })

        try:
            if is_in_lobby():
                self._log("Lobby detected — pathing to Spring LTM")
                self._set_phase("Lobby pathing…")
                do_lobby_path(stop_event=self._stop_event, log_cb=self._log)

            while not self._stop_event.is_set():
                run_start = time.time()
                macro_state.state["run_start"] = run_start
                self._set_phase(f"Run {macro_state.state['total_runs'] + 1}")

                run(stop_event=self._stop_event, log_cb=self._log)

                if self._stop_event.is_set():
                    break

                elapsed = time.time() - run_start
                macro_state.state["total_runs"]     += 1
                macro_state.state["total_run_time"] += elapsed
                macro_state.state["last_run_time"]   = elapsed

                threading.Thread(
                    target=webhook.send,
                    args=(elapsed,),
                    daemon=True,
                ).start()

            self._set_phase("Stopped")

        except Exception as exc:
            self._log(f"ERROR: {exc}")
            self.root.after(0, lambda: self._set_status("error", _DOT_ERR))
            self.root.after(0, lambda: self._set_phase(f"Error: {exc}"))
        finally:
            macro_state.state["running"] = False
            self.root.after(0, self._on_run_complete)

    def _on_run_complete(self):
        self._start_btn.config(state="normal")
        _hover(self._start_btn, GREEN_D, GREEN_A)
        self._stop_btn.config(state="disabled")
        self._set_status("idle", _DOT_IDLE)

    # ── actions ────────────────────────────────────────────────

    def _on_start(self):
        if self._thread and self._thread.is_alive():
            return
        self._save_prefs()
        self._stop_event.clear()
        self._set_status("running", _DOT_RUN)
        self._set_phase("Starting…")
        self._start_btn.config(state="disabled")
        self._stop_btn.config(state="normal")
        _hover(self._stop_btn, RED_D, RED_A)
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _on_stop(self):
        self._save_prefs()
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_ulong(self._thread.ident),
                ctypes.py_object(SystemExit),
            )
        self._set_status("stopping…", _DOT_STOP)
        self._stop_btn.config(state="disabled")

    def _on_align(self):
        focus_roblox_window()
        self._set_phase("Window aligned")

    def _on_join_ps(self):
        code = self._ps_var.get().strip()
        if not code:
            self._set_status("no private server set", _DOT_ERR)
            return
        try:
            os.startfile(code)
        except Exception:
            import subprocess
            subprocess.Popen(["start", code], shell=True)

    def _on_close(self):
        self._save_prefs()
        self._stop_event.set()
        self.root.destroy()

    # ── helpers ────────────────────────────────────────────────

    def _set_status(self, text: str, dot: str):
        self._status_var.set(text)
        self._dot_cv.itemconfig(self._dot_id, fill=dot)

    def _set_phase(self, text: str):
        self.root.after(0, lambda: self._phase_var.set(text))

    def _log(self, msg: str):
        try:
            self._log_queue.put_nowait(msg)
        except queue.Full:
            pass

    def _toggle_log(self):
        if self._show_log.get():
            self._log_frame.pack(fill="x", padx=14, pady=(0, 10))
        else:
            self._log_frame.pack_forget()
        self.root.update_idletasks()
        self.root.geometry(f"{WIN_W}x{self.root.winfo_reqheight()}")

    # ── tick ───────────────────────────────────────────────────

    def _tick(self):
        st = macro_state.state

        self._runs_var.set(str(st["total_runs"]))

        if st["session_start"] > 0 and st["running"]:
            self._sess_var.set(_fmt_time(time.time() - st["session_start"]))
        if st["running"] and st["run_start"] > 0:
            self._run_var.set(_fmt_time(time.time() - st["run_start"]))
        if st["last_run_time"] > 0:
            self._last_run_var.set(_fmt_time(st["last_run_time"]))

        if st["running"]:
            self._pulse = not self._pulse
            self._dot_cv.itemconfig(self._dot_id,
                                     fill=GREEN if self._pulse else GREEN_A)

        if self._show_log.get():
            msgs = []
            try:
                while True:
                    msgs.append(self._log_queue.get_nowait())
            except queue.Empty:
                pass
            if msgs:
                at_bottom = self._log_text.yview()[1] >= 0.99
                self._log_text.config(state="normal")
                self._log_text.insert("end", "\n".join(msgs) + "\n")
                if at_bottom:
                    self._log_text.see("end")
                self._log_text.config(state="disabled")

        self.root.after(500, self._tick)


# ── entry ──────────────────────────────────────────────────────────────────

_MUTEX = None

def _single_instance() -> bool:
    global _MUTEX
    _MUTEX = ctypes.windll.kernel32.CreateMutexW(None, True, "SpringLTMMacro_Instance")
    return ctypes.windll.kernel32.GetLastError() != 183


if __name__ == "__main__":
    if not _single_instance():
        import tkinter.messagebox as mb
        _r = tk.Tk(); _r.withdraw()
        mb.showerror("Already running", "Spring LTM Macro is already running.")
        _r.destroy()
        sys.exit(1)

    root = tk.Tk()
    MacroGUI(root)
    root.mainloop()
