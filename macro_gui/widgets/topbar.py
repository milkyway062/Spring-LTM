"""Top bar: brand mark, hotkey pills, status, frameless window controls."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QMouseEvent, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from macro_gui.widgets.pill import Pill


class TopBar(QWidget):
    """Frameless window top bar.

    Provides drag-to-move (delegated to the shell), window controls,
    a version pill, hotkey pills, and a live status indicator.

    Signals:
        close_clicked: Emitted when the close button is pressed.
        min_clicked: Emitted when the minimise button is pressed.
        dock_toggled: Kept for API compatibility with the previous
            side-dock layout; never emitted by this rewrite.

    Args:
        title: Application name shown next to the brand glyph.
        version: Version string shown as a pill.
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
        self.setFixedHeight(64)
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._shell: QWidget | None = None

        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 0, 14, 0)
        lay.setSpacing(10)

        dot = QLabel("◆")
        dot.setObjectName("BrandDot")
        lay.addWidget(dot)

        self._title_lbl = QLabel(title)
        self._title_lbl.setObjectName("Brand")
        lay.addWidget(self._title_lbl)

        tag = QLabel("Anime Vanguards")
        tag.setObjectName("BrandTagline")
        lay.addSpacing(6)
        lay.addWidget(tag)

        lay.addStretch(1)

        for label, _ in hotkeys:
            lay.addWidget(Pill(label, "hotkey"))

        lay.addSpacing(8)
        lay.addWidget(Pill(version, "version"))
        lay.addSpacing(10)

        self._status_pill = Pill("idle", "status")
        lay.addWidget(self._status_pill)

        self._dot = _StatusDot(self)
        lay.addWidget(self._dot)

        lay.addSpacing(14)

        self._btn_min = _WinBtn("—", "BtnMin", self)
        self._btn_min.clicked.connect(self.min_clicked)
        lay.addWidget(self._btn_min)

        self._btn_close = _WinBtn("✕", "BtnClose", self)
        self._btn_close.clicked.connect(self.close_clicked)
        lay.addWidget(self._btn_close)

    def set_shell(self, shell: QWidget) -> None:
        self._shell = shell

    def set_status(self, text: str, dot_color: str) -> None:
        self._status_pill.set_text(text)
        self._dot.set_color(dot_color)

    def pulse_dot(self, color_a: str, color_b: str, state: bool) -> bool:
        return self._dot.pulse(color_a, color_b, state)

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


class _WinBtn(QPushButton):
    def __init__(
        self, text: str, obj_name: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(text, parent)
        self.setObjectName(obj_name)
        self.setFixedSize(30, 30)
        self.setCursor(Qt.PointingHandCursor)


class _StatusDot(QWidget):
    """Filled-circle status indicator drawn via QPainter."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(10, 10)
        self._color: str = "#3a4153"

    def set_color(self, color: str) -> None:
        self._color = color
        self.update()

    def pulse(self, color_a: str, color_b: str, state: bool) -> bool:
        next_state = not state
        self.set_color(color_a if next_state else color_b)
        return next_state

    def paintEvent(self, e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(QColor(self._color)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(1, 1, 8, 8)
