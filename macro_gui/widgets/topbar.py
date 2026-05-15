"""Top bar: title, pills, status dot, and frameless window controls."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QMouseEvent, QPainter
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

import macro_gui.theme as theme
from macro_gui.widgets.pill import Pill


class TopBar(QWidget):
    """Frameless window top bar.

    Provides drag-to-move, window controls (close/min/dock), a version pill,
    hotkey pills, and a live status indicator.

    Signals:
        close_clicked: Emitted when the close button is pressed.
        min_clicked: Emitted when the minimise button is pressed.
        dock_toggled: Emitted with ``True`` when docking is activated,
            ``False`` when deactivated.

    Args:
        title: Application name shown on the left.
        version: Version string shown as a pill next to the title.
        hotkeys: Sequence of ``(label, key)`` pairs rendered as hotkey pills.
        parent: Optional parent widget.
    """

    close_clicked = Signal()
    min_clicked = Signal()
    dock_toggled = Signal(bool)

    def __init__(
        self,
        title: str,
        version: str,
        hotkeys: list[tuple[str, str]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(56)
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._shell: QWidget | None = None
        self._dock_active: bool = False

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 12, 0)
        lay.setSpacing(8)

        # Title label
        self._title_lbl = QLabel(title)
        self._title_lbl.setObjectName("TopTitle")
        lay.addWidget(self._title_lbl)

        # Version pill
        lay.addWidget(Pill(version, "version"))
        lay.addSpacing(4)

        # Hotkey pills
        for label, _ in hotkeys:
            lay.addWidget(Pill(label, "hotkey"))

        lay.addStretch(1)

        # Status pill + dot
        self._status_pill = Pill("idle", "status")
        lay.addWidget(self._status_pill)

        self._dot = _StatusDot(self)
        lay.addWidget(self._dot)

        lay.addSpacing(8)

        # Window control buttons
        self._btn_dock = _WinBtn("⊞", "BtnDock", self)
        self._btn_dock.clicked.connect(self._on_dock)
        lay.addWidget(self._btn_dock)

        self._btn_min = _WinBtn("—", "BtnMin", self)
        self._btn_min.clicked.connect(self.min_clicked)
        lay.addWidget(self._btn_min)

        self._btn_close = _WinBtn("✕", "BtnClose", self)
        self._btn_close.clicked.connect(self.close_clicked)
        lay.addWidget(self._btn_close)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_shell(self, shell: QWidget) -> None:
        """Bind the shell window so drag events can be forwarded.

        Args:
            shell: The :class:`~macro_gui.widgets.frame.FramelessShell` instance.
        """
        self._shell = shell

    def set_status(self, text: str, dot_color: str) -> None:
        """Update the status pill text and dot colour.

        Args:
            text: Human-readable status string (e.g. ``"running"``).
            dot_color: CSS hex colour string for the status dot.
        """
        self._status_pill.set_text(text)
        self._dot.set_color(dot_color)

    def pulse_dot(self, color_a: str, color_b: str, state: bool) -> bool:
        """Alternate the dot between two colours; returns the next state.

        Call this from a QTimer to create a blinking effect.

        Args:
            color_a: Colour shown when *state* transitions to ``True``.
            color_b: Colour shown when *state* transitions to ``False``.
            state: Current toggle state.

        Returns:
            The new toggle state (inverted from *state*).
        """
        return self._dot.pulse(color_a, color_b, state)

    # ------------------------------------------------------------------
    # Internal handlers
    # ------------------------------------------------------------------

    def _on_dock(self) -> None:
        self._dock_active = not self._dock_active
        self.dock_toggled.emit(self._dock_active)

    # ------------------------------------------------------------------
    # Mouse drag forwarding
    # ------------------------------------------------------------------

    def mousePressEvent(self, e: QMouseEvent) -> None:  # noqa: N802
        if e.button() == Qt.LeftButton and self._shell is not None:
            self._shell.start_drag(e.globalPosition().toPoint())

    def mouseMoveEvent(self, e: QMouseEvent) -> None:  # noqa: N802
        if self._shell is not None:
            self._shell.do_drag(e.globalPosition().toPoint())

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:  # noqa: N802
        if self._shell is not None:
            self._shell.stop_drag()

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:  # noqa: N802
        if e.button() == Qt.LeftButton and self._shell is not None:
            if self._shell.isMaximized():
                self._shell.showNormal()
            else:
                self._shell.showMaximized()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


class _WinBtn(QPushButton):
    """Compact frameless window control button."""

    def __init__(self, text: str, obj_name: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName(obj_name)
        self.setFixedSize(28, 28)
        self.setCursor(Qt.PointingHandCursor)


class _StatusDot(QWidget):
    """Small filled-circle status indicator painted with QPainter."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(10, 10)
        self._color: str = "#33333f"

    def set_color(self, color: str) -> None:
        """Set the dot fill colour.

        Args:
            color: CSS hex colour string.
        """
        self._color = color
        self.update()

    def pulse(self, color_a: str, color_b: str, state: bool) -> bool:
        """Flip between two colours and return the new state.

        Args:
            color_a: Colour for the ``True`` state.
            color_b: Colour for the ``False`` state.
            state: Current state before the pulse.

        Returns:
            The new state after toggling.
        """
        next_state = not state
        self.set_color(color_a if next_state else color_b)
        return next_state

    def paintEvent(self, e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(QColor(self._color)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(1, 1, 8, 8)
