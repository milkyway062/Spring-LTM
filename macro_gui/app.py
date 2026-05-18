"""MacroApp — central orchestrator for the editorial-glass shell.

Builds the frameless window, top bar, icon rail, page stack, and bottom
console drawer; drives the 500 ms tick that drains the log queue,
refreshes stat blocks, and pulses the status dot.

The public surface (constructor signature, ``exec``, ``log``,
``set_status``, ``set_phase``, ``set_action_state``, ``_switch_theme``,
``_set_field``, ``get_field``, and the internal handles
``_action_buttons`` / ``_stat_blocks`` / ``_field_values`` /
``_phase_lbl`` / ``_log_text`` / ``_update_btn`` /
``_update_status_lbl``) is unchanged so ``SpringApp(MacroApp)`` in
``gui.v2.py`` keeps working.
"""
from __future__ import annotations

import threading
from typing import Any

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import macro_gui.theme as theme
from macro_gui.qss import build_qss
from macro_gui.spec import MacroSpec
from macro_gui.widgets.card import StatBlock
from macro_gui.widgets.console import ConsolePanel
from macro_gui.widgets.frame import FramelessShell
from macro_gui.widgets.palette import CommandPalette, PaletteItem
from macro_gui.widgets.sidebar import SidebarNav
from macro_gui.widgets.topbar import TopBar


class MacroApp:
    """Orchestrate the PySide6 shell for the Spring LTM macro.

    Args:
        spec: Fully-populated ``MacroSpec`` describing pages, actions,
            fields, stats, hotkeys, and the log queue.
    """

    def __init__(self, *args: Any) -> None:
        # Backwards-compatible signature: ``MacroApp(spec)`` or the
        # legacy ``MacroApp(root, spec)`` form used by SpringApp in
        # gui.v2.py before the Qt rewrite. ``root`` is a leftover
        # Tk/ctk handle and is kept only so callers that still touch
        # ``self.root`` (e.g. ``SpringApp._on_close``) keep working.
        if len(args) == 1:
            self.root = None
            spec = args[0]
        elif len(args) == 2:
            self.root, spec = args
        else:
            raise TypeError(
                f"MacroApp() takes 1 or 2 positional arguments, got {len(args)}"
            )
        self.spec = spec

        self._field_values: dict[str, Any] = {f.id: f.default for f in spec.fields}
        # Stat and action registries hold *lists* — multiple pages can
        # surface the same stat or wire the same action.
        self._stat_blocks: dict[str, list[StatBlock]] = {}
        self._action_buttons: dict[str, list[Any]] = {}
        self._log_targets: list[Any] = []
        self._page_frames: dict[str, QWidget] = {}
        self._active_page: str | None = None
        self._pulse_state: bool = False

        # Page-builder injection points (set inside builders).
        self._phase_lbl = None
        self._log_text = None
        self._update_btn = None
        self._update_status_lbl = None

        # Animation handles kept on self to survive GC mid-flight
        # (pyside6-patterns §7).
        self._page_out_anim: QPropertyAnimation | None = None
        self._page_in_anim: QPropertyAnimation | None = None
        self._switch_anim_out: QPropertyAnimation | None = None
        self._switch_anim_in: QPropertyAnimation | None = None

        self._app = QApplication.instance() or QApplication([])
        self._apply_theme()

        self._shell = FramelessShell()
        self._shell.setWindowTitle(spec.title)

        self._build_layout()

        # Initial active state is set directly — calling _show_page on
        # index 0 hits the early-return guard (pyside6-patterns §8).
        if spec.pages:
            first_id = spec.pages[0].id
            self._active_page = first_id
            self._sidebar.set_active(first_id)

        self._shell.closeEvent = lambda e: self._on_close_event(e)

        self._tick_timer = QTimer()
        self._tick_timer.setInterval(500)
        self._tick_timer.timeout.connect(self._tick)
        self._tick_timer.start()

    # ── Theme ─────────────────────────────────────────────────────

    def _apply_theme(self) -> None:
        qss = build_qss(theme.tokens(), theme.radii(), theme.spacing())
        self._app.setStyleSheet(qss)

    def _switch_theme(self, name: str) -> None:
        """Cross-fade the shell opacity while swapping the theme stylesheet."""
        dur = 0 if theme.reduce_motion() else 200
        if dur > 0:
            effect = QGraphicsOpacityEffect(self._shell)
            self._shell.setGraphicsEffect(effect)
            anim_out = QPropertyAnimation(effect, b"opacity", self._shell)
            anim_out.setDuration(dur // 2)
            anim_out.setStartValue(1.0)
            anim_out.setEndValue(0.0)
            anim_out.finished.connect(
                lambda: self._do_switch_theme(name, effect, dur)
            )
            anim_out.start()
            self._switch_anim_out = anim_out
        else:
            theme.load(name)
            self._apply_theme()

    def _do_switch_theme(
        self, name: str, effect: QGraphicsOpacityEffect, dur: int
    ) -> None:
        theme.load(name)
        self._apply_theme()
        anim_in = QPropertyAnimation(effect, b"opacity", self._shell)
        anim_in.setDuration(dur // 2)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        anim_in.finished.connect(lambda: self._shell.setGraphicsEffect(None))
        anim_in.start()
        self._switch_anim_in = anim_in

    # ── Layout ────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        spec = self.spec

        hk_labels = [(h.label, h.key) for h in spec.hotkeys]
        self._topbar = TopBar(spec.title, f"v{spec.version}", hk_labels)
        self._topbar.set_shell(self._shell)
        self._topbar.close_clicked.connect(lambda: self._shell.close())
        self._topbar.min_clicked.connect(self._shell.showMinimized)
        self._shell.set_topbar(self._topbar)

        body = QWidget()
        body.setObjectName("Content")
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        page_defs = [(p.id, p.label) for p in spec.pages]
        self._sidebar = SidebarNav(page_defs)
        self._sidebar.page_selected.connect(self._show_page)
        body_lay.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._stack.setObjectName("PageWrapper")
        for page in spec.pages:
            f = QWidget()
            f.setObjectName("PageWrapper")
            page.builder(f, self)
            self._stack.addWidget(f)
            self._page_frames[page.id] = f
        body_lay.addWidget(self._stack, stretch=1)

        self._shell.set_body(body)

        self._console = ConsolePanel()
        self._shell.set_drawer(self._console)

        # Command palette — Ctrl+K, lazy-built so theme/qss is already live.
        self._palette: CommandPalette | None = None
        sc = QShortcut(QKeySequence("Ctrl+K"), self._shell)
        sc.setContext(Qt.ApplicationShortcut)
        sc.activated.connect(self._open_palette)

    def _open_palette(self) -> None:
        if self._palette is None:
            self._palette = CommandPalette(self._shell)
            self._palette.set_items(self._build_palette_items())
        else:
            # Rebuild every open — themes/actions could have changed.
            self._palette.set_items(self._build_palette_items())
        self._palette.open_centered()

    def _build_palette_items(self) -> list[PaletteItem]:
        items: list[PaletteItem] = []
        for p in self.spec.pages:
            pid = p.id
            items.append(PaletteItem(
                title=f"Go to {p.label}",
                section="Page",
                callback=lambda pid=pid: self._show_page(pid),
            ))
        for aid, a in self.spec.actions.items():
            items.append(PaletteItem(
                title=a.label.strip(),
                section="Action",
                callback=a.callback,
            ))
        for tname in theme.available_themes():
            items.append(PaletteItem(
                title=f"Theme · {tname}",
                section="Theme",
                callback=lambda n=tname: self._switch_theme(n),
            ))
        return items

    # ── Navigation ────────────────────────────────────────────────

    def _show_page(self, page_id: str) -> None:
        if page_id not in self._page_frames:
            return

        new_idx = self._stack.indexOf(self._page_frames[page_id])
        if self._stack.currentIndex() == new_idx:
            return

        if not theme.reduce_motion():
            cur = self._stack.currentWidget()
            effect = QGraphicsOpacityEffect(cur)
            cur.setGraphicsEffect(effect)
            anim = QPropertyAnimation(effect, b"opacity", cur)
            anim.setDuration(100)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)

            def _swap(nidx: int = new_idx, c: QWidget = cur) -> None:
                c.setGraphicsEffect(None)
                self._stack.setCurrentIndex(nidx)
                new = self._stack.currentWidget()
                eff2 = QGraphicsOpacityEffect(new)
                new.setGraphicsEffect(eff2)
                a2 = QPropertyAnimation(eff2, b"opacity", new)
                a2.setDuration(160)
                a2.setEasingCurve(QEasingCurve.OutCubic)
                a2.setStartValue(0.0)
                a2.setEndValue(1.0)
                a2.finished.connect(lambda: new.setGraphicsEffect(None))
                a2.start()
                self._page_in_anim = a2

            anim.finished.connect(_swap)
            anim.start()
            self._page_out_anim = anim
        else:
            self._stack.setCurrentIndex(new_idx)

        self._active_page = page_id
        self._sidebar.set_active(page_id)

    # ── Field handling ────────────────────────────────────────────

    def _set_field(self, field_id: str, value: Any) -> None:
        self._field_values[field_id] = value
        spec_field = next((f for f in self.spec.fields if f.id == field_id), None)
        if spec_field and spec_field.on_change:
            spec_field.on_change(value)

    def get_field(self, field_id: str) -> Any:
        return self._field_values.get(field_id)

    # ── Status / phase / log ──────────────────────────────────────

    def set_status(self, text: str, dot_color: str) -> None:
        """Thread-safe topbar status update."""
        QTimer.singleShot(0, lambda: self._topbar.set_status(text, dot_color))

    def set_phase(self, text: str) -> None:
        if self._phase_lbl:
            QTimer.singleShot(0, lambda: self._phase_lbl.setText(text))

    def log(self, msg: str) -> None:
        if self.spec.log_queue is not None:
            try:
                self.spec.log_queue.put_nowait(msg)
            except Exception:
                pass

    def set_action_state(self, action_id: str, enabled: bool) -> None:
        btns = self._action_buttons.get(action_id, [])
        for btn in btns:
            QTimer.singleShot(0, lambda b=btn: b.setEnabled(enabled))

    # ── Update helpers ────────────────────────────────────────────

    def _on_update(self) -> None:
        if self._update_btn:
            self._update_btn.setEnabled(False)
            self._update_btn.setText("Checking…")
        if hasattr(self, "_run_update"):
            threading.Thread(target=self._run_update, daemon=True).start()

    def _set_update_status(self, msg: str) -> None:
        if self._update_status_lbl:
            QTimer.singleShot(0, lambda: self._update_status_lbl.setText(msg))

    # ── Close ─────────────────────────────────────────────────────

    def _on_close_event(self, event) -> None:
        self._tick_timer.stop()
        if self.spec.on_close:
            self.spec.on_close()
        event.accept()

    # ── Tick ──────────────────────────────────────────────────────

    def _tick(self) -> None:
        for s in self.spec.stats:
            blks = self._stat_blocks.get(s.id, [])
            if not blks:
                continue
            try:
                val = s.getter()
            except Exception:
                continue
            for blk in blks:
                try:
                    blk.set(val)
                except Exception:
                    pass

        if self.spec.status_getter:
            try:
                text, _dot = self.spec.status_getter()
                if "running" in text:
                    self._pulse_state = self._topbar.pulse_dot(
                        "#5fd07a", "#1e5a35", self._pulse_state
                    )
            except Exception:
                pass

        if self.spec.log_queue is not None:
            msgs: list[str] = []
            try:
                while True:
                    msgs.append(self.spec.log_queue.get_nowait())
            except Exception:
                pass
            if msgs:
                combined = "\n".join(msgs)
                self._console.append_text(combined)
                for target in self._log_targets:
                    try:
                        target.appendPlainText(combined)
                    except Exception:
                        pass

    # ── Run ───────────────────────────────────────────────────────

    def exec(self) -> int:
        self._shell.show()
        return self._app.exec()

    # ``run`` is an alias kept for gui.v2.py's ``app.run()`` call site.
    run = exec
