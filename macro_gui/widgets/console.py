"""Bottom-docked collapsible log drawer.

Animates the drawer's height between ``COLLAPSED_H`` and ``EXPANDED_H``
via two ``QPropertyAnimation`` instances stored on the instance so they
survive GC mid-flight (see ``pyside6-patterns §7``).
"""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QFont, QMouseEvent, QTextOption
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import macro_gui.theme as theme

COLLAPSED_H: int = 38
EXPANDED_H: int = 220


class ConsolePanel(QWidget):
    """Bottom console drawer.

    Public surface (``append_text``, ``clear``, ``is_expanded``,
    ``toggle``) mirrors the previous right-dock implementation so
    ``MacroApp._tick`` can keep calling it unchanged.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ConsoleDrawer")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._expanded: bool = False
        self.setFixedHeight(COLLAPSED_H)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._handle = _DrawerHandle(self)
        outer.addWidget(self._handle)

        self._text = QPlainTextEdit()
        self._text.setObjectName("LogView")
        self._text.setReadOnly(True)
        self._text.setFont(QFont("JetBrains Mono", 9))
        self._text.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self._text.setVisible(False)
        outer.addWidget(self._text, stretch=1)

        self._line_count: int = 0
        self._anim: QPropertyAnimation | None = None
        self._anim2: QPropertyAnimation | None = None

    def toggle(self) -> None:
        self._expanded = not self._expanded
        target_h = EXPANDED_H if self._expanded else COLLAPSED_H
        dur = 0 if theme.reduce_motion() else 220

        self._handle.set_expanded(self._expanded)
        self._text.setVisible(self._expanded)

        if dur == 0:
            self.setFixedHeight(target_h)
            return

        current_h = self.height()

        self._anim = QPropertyAnimation(self, b"minimumHeight", self)
        self._anim.setDuration(dur)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.setStartValue(current_h)
        self._anim.setEndValue(target_h)

        self._anim2 = QPropertyAnimation(self, b"maximumHeight", self)
        self._anim2.setDuration(dur)
        self._anim2.setEasingCurve(QEasingCurve.OutCubic)
        self._anim2.setStartValue(current_h)
        self._anim2.setEndValue(target_h)

        self._anim.start()
        self._anim2.start()

    def append_text(self, text: str) -> None:
        sb = self._text.verticalScrollBar()
        at_bottom = sb.value() >= sb.maximum() - 4
        self._text.appendPlainText(text)
        self._line_count += text.count("\n") + 1
        self._handle.set_count(self._line_count)
        if at_bottom:
            self._text.moveCursor(self._text.textCursor().End)

    def clear(self) -> None:
        self._text.clear()
        self._line_count = 0
        self._handle.set_count(0)

    def is_expanded(self) -> bool:
        return self._expanded


class _DrawerHandle(QWidget):
    """Top strip of the drawer — click to toggle, shows count + label."""

    def __init__(self, drawer: ConsolePanel) -> None:
        super().__init__(drawer)
        self._drawer = drawer
        self.setObjectName("ConsoleHandle")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(COLLAPSED_H)
        self.setCursor(Qt.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 0, 14, 0)
        lay.setSpacing(12)

        grip = QWidget()
        grip.setObjectName("ConsoleGrip")
        grip.setAttribute(Qt.WA_StyledBackground, True)
        grip.setFixedSize(34, 3)
        lay.addWidget(grip)

        self._lbl = QLabel("CONSOLE")
        self._lbl.setObjectName("ConsoleLabel")
        lay.addWidget(self._lbl)

        self._count = QLabel("0 lines")
        self._count.setObjectName("ConsoleCount")
        lay.addWidget(self._count)

        lay.addStretch(1)

        self._chev = QPushButton("▲ expand")
        self._chev.setObjectName("ConsoleToggle")
        self._chev.setCursor(Qt.PointingHandCursor)
        self._chev.setFlat(True)
        self._chev.clicked.connect(drawer.toggle)
        lay.addWidget(self._chev)

    def set_expanded(self, expanded: bool) -> None:
        self._chev.setText("▼ hide" if expanded else "▲ expand")

    def set_count(self, n: int) -> None:
        self._count.setText(f"{n} line{'s' if n != 1 else ''}")

    def mousePressEvent(self, e: QMouseEvent) -> None:  # noqa: N802
        if e.button() == Qt.LeftButton:
            self._drawer.toggle()
