from __future__ import annotations

import threading
from typing import Any

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer
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
from macro_gui.widgets.dock import SideBySideDocker
from macro_gui.widgets.frame import FramelessShell
from macro_gui.widgets.sidebar import SidebarNav
from macro_gui.widgets.topbar import TopBar


class MacroApp:
    """Central orchestrator for the Spring LTM PySide6 GUI.

    Creates the application window, builds the page stack, wires the
    sidebar, topbar, and console dock, and drives periodic stat/log
    updates via a 500 ms QTimer tick.

    Args:
        spec: Fully-populated MacroSpec describing pages, actions, fields,
              stats, and hotkeys.
    """

    def __init__(self, spec: MacroSpec) -> None:
        self.spec = spec

        # Mutable state ────────────────────────────────────────────
        self._field_values: dict[str, Any] = {f.id: f.default for f in spec.fields}
        self._stat_blocks: dict[str, StatBlock] = {}
        self._action_buttons: dict[str, Any] = {}
        self._page_frames: dict[str, QWidget] = {}
        self._active_page: str | None = None
        self._pulse_state: bool = False

        # Assigned by page builders ────────────────────────────────
        self._phase_lbl = None
        self._log_text = None
        self._update_btn = None
        self._update_status_lbl = None

        # Animation handles (kept alive to prevent GC mid-animation)
        self._page_out_anim: QPropertyAnimation | None = None
        self._page_in_anim: QPropertyAnimation | None = None
        self._switch_anim_out: QPropertyAnimation | None = None
        self._switch_anim_in: QPropertyAnimation | None = None

        # Qt application ───────────────────────────────────────────
        self._app = QApplication.instance() or QApplication([])
        self._apply_theme()

        self._shell = FramelessShell()
        self._shell.setWindowTitle(spec.title)

        self._dock = SideBySideDocker(self._shell)
        self._dock.status_changed.connect(self._on_dock_status)

        self._build_layout()

        if spec.pages:
            first_id = spec.pages[0].id
            self._active_page = first_id
            self._sidebar.set_active(first_id)

        self._shell.closeEvent = lambda e: self._on_close_event(e)

        # Tick timer ───────────────────────────────────────────────
        self._tick_timer = QTimer()
        self._tick_timer.setInterval(500)
        self._tick_timer.timeout.connect(self._tick)
        self._tick_timer.start()

    # ── Theme ─────────────────────────────────────────────────────

    def _apply_theme(self) -> None:
        qss = build_qss(theme.tokens(), theme.radii(), theme.spacing())
        self._app.setStyleSheet(qss)

    def _switch_theme(self, name: str) -> None:
        """Cross-fade the shell opacity while swapping the theme stylesheet.

        Args:
            name: Theme identifier recognised by *theme.load()*.
        """
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

        # TopBar
        hk_labels = [(h.label, h.key) for h in spec.hotkeys]
        self._topbar = TopBar(spec.title, f"v{spec.version}", hk_labels)
        self._topbar.set_shell(self._shell)
        self._topbar.close_clicked.connect(lambda: self._shell.close())
        self._topbar.min_clicked.connect(self._shell.showMinimized)
        self._topbar.dock_toggled.connect(self._dock.set_active)
        self._shell.set_topbar(self._topbar)

        # Body: [sidebar | stacked content | console]
        body = QWidget()
        body.setObjectName("Content")
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        # Sidebar
        page_defs = [(p.id, p.label) for p in spec.pages]
        self._sidebar = SidebarNav(page_defs)
        self._sidebar.page_selected.connect(self._show_page)
        body_lay.addWidget(self._sidebar)

        # Stacked pages
        self._stack = QStackedWidget()
        self._stack.setObjectName("PageWrapper")
        for page in spec.pages:
            f = QWidget()
            f.setObjectName("PageWrapper")
            page.builder(f, self)
            self._stack.addWidget(f)
            self._page_frames[page.id] = f
        body_lay.addWidget(self._stack, stretch=1)

        # Console dock (right panel)
        self._console = ConsolePanel()
        body_lay.addWidget(self._console)

        self._shell.set_body(body)

    # ── Navigation ────────────────────────────────────────────────

    def _show_page(self, page_id: str) -> None:
        """Switch the stacked widget to the page identified by *page_id*.

        A short opacity fade is used unless reduce-motion is enabled.

        Args:
            page_id: Page identifier matching a PageSpec.id.
        """
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
        """Persist a field value and fire its on_change callback.

        Args:
            field_id: FieldSpec.id to update.
            value: New value for the field.
        """
        self._field_values[field_id] = value
        spec_field = next((f for f in self.spec.fields if f.id == field_id), None)
        if spec_field and spec_field.on_change:
            spec_field.on_change(value)

    def get_field(self, field_id: str) -> Any:
        """Return the current value for *field_id*.

        Args:
            field_id: FieldSpec.id to look up.

        Returns:
            Stored value or None if unknown.
        """
        return self._field_values.get(field_id)

    # ── Status ────────────────────────────────────────────────────

    def set_status(self, text: str, dot_color: str) -> None:
        """Thread-safe update of the topbar status pill.

        Args:
            text: Human-readable status string.
            dot_color: CSS colour for the indicator dot.
        """
        QTimer.singleShot(0, lambda: self._topbar.set_status(text, dot_color))

    def set_phase(self, text: str) -> None:
        """Thread-safe update of the phase label on the Run page.

        Args:
            text: Phase description to display.
        """
        if self._phase_lbl:
            QTimer.singleShot(0, lambda: self._phase_lbl.setText(text))

    def log(self, msg: str) -> None:
        """Enqueue *msg* for display in the console and Log page.

        Args:
            msg: Log line to append.
        """
        if self.spec.log_queue is not None:
            try:
                self.spec.log_queue.put_nowait(msg)
            except Exception:
                pass

    # ── Action state ──────────────────────────────────────────────

    def set_action_state(self, action_id: str, enabled: bool) -> None:
        """Enable or disable an action button by its spec id.

        Args:
            action_id: ActionSpec.id of the target button.
            enabled: True to enable, False to disable.
        """
        btn = self._action_buttons.get(action_id)
        if btn:
            QTimer.singleShot(0, lambda: btn.setEnabled(enabled))

    # ── Update helpers ────────────────────────────────────────────

    def _on_update(self) -> None:
        """Disable the update button and run *_run_update* in a daemon thread."""
        if self._update_btn:
            self._update_btn.setEnabled(False)
            self._update_btn.setText("Checking…")
        if hasattr(self, "_run_update"):
            threading.Thread(target=self._run_update, daemon=True).start()

    def _set_update_status(self, msg: str) -> None:
        """Thread-safe update of the update-page status label.

        Args:
            msg: Status message to display.
        """
        if self._update_status_lbl:
            QTimer.singleShot(0, lambda: self._update_status_lbl.setText(msg))

    # ── Dock ──────────────────────────────────────────────────────

    def _on_dock_status(self, status: str) -> None:
        colors: dict[str, str] = {
            "docked": "#34c759",
            "no game": "#e6a23c",
            "idle": "#7d8699",
        }
        self.set_status(status, colors.get(status, "#7d8699"))

    # ── Close ─────────────────────────────────────────────────────

    def _on_close_event(self, event) -> None:
        self._tick_timer.stop()
        if self.spec.on_close:
            self.spec.on_close()
        event.accept()

    # ── Tick ──────────────────────────────────────────────────────

    def _tick(self) -> None:
        """Periodic 500 ms update: refresh stats, pulse dot, drain log queue."""
        # Stat blocks
        for s in self.spec.stats:
            blk = self._stat_blocks.get(s.id)
            if blk:
                try:
                    blk.set(s.getter())
                except Exception:
                    pass

        # Status dot pulse when macro is running
        if self.spec.status_getter:
            try:
                text, _dot = self.spec.status_getter()
                if "running" in text:
                    self._pulse_state = self._topbar.pulse_dot(
                        "#34c759", "#1a7a3a", self._pulse_state
                    )
            except Exception:
                pass

        # Drain log queue into console panel and Log page
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
                if self._log_text:
                    self._log_text.appendPlainText(combined)

    # ── Run ───────────────────────────────────────────────────────

    def exec(self) -> int:
        """Show the shell window and enter the Qt event loop.

        Returns:
            Exit code from QApplication.exec().
        """
        self._shell.show()
        return self._app.exec()
