"""Command palette overlay — Ctrl+K fuzzy launcher.

Floats over the shell as a frameless translucent dialog. Lists pages,
actions, and themes; live-filters via a simple subsequence match;
Enter invokes the selected entry.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QGraphicsDropShadowEffect,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class PaletteItem:
    title: str
    section: str  # "Page" | "Action" | "Theme"
    callback: Callable[[], None]


def _subseq_score(query: str, target: str) -> int | None:
    """Return a score if all chars of *query* appear in order in *target*.

    Lower score = better match. None means no match.
    """
    if not query:
        return 0
    q = query.lower()
    t = target.lower()
    qi = 0
    last = -1
    gaps = 0
    for i, ch in enumerate(t):
        if qi < len(q) and ch == q[qi]:
            if last >= 0:
                gaps += i - last - 1
            last = i
            qi += 1
            if qi == len(q):
                return gaps + (len(t) - i)  # prefer earlier full matches
    return None


class CommandPalette(QDialog):
    """Frameless Ctrl+K launcher over the shell.

    Args:
        shell: Parent shell window — palette is centered against it.
    """

    def __init__(self, shell: QWidget) -> None:
        super().__init__(shell)
        self._shell = shell
        self._items: list[PaletteItem] = []
        self._filtered: list[PaletteItem] = []

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)

        self._card = QWidget(self)
        self._card.setObjectName("PaletteCard")
        self._card.setAttribute(Qt.WA_StyledBackground, True)

        shadow = QGraphicsDropShadowEffect(self._card)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(Qt.black)
        self._card.setGraphicsEffect(shadow)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 60, 40, 40)
        outer.addWidget(self._card)

        body = QVBoxLayout(self._card)
        body.setContentsMargins(14, 14, 14, 14)
        body.setSpacing(10)

        hint = QLabel("COMMAND PALETTE  ·  ↑↓ select  ·  ↵ run  ·  esc close")
        hint.setObjectName("PaletteHint")
        body.addWidget(hint)

        self._input = QLineEdit()
        self._input.setObjectName("PaletteInput")
        self._input.setPlaceholderText("Type a page, action, or theme…")
        self._input.textChanged.connect(self._refilter)
        self._input.returnPressed.connect(self._activate_current)
        body.addWidget(self._input)

        self._list = QListWidget()
        self._list.setObjectName("PaletteList")
        self._list.setUniformItemSizes(True)
        self._list.itemActivated.connect(lambda _i: self._activate_current())
        self._list.itemClicked.connect(lambda _i: self._activate_current())
        body.addWidget(self._list)

        self._input.installEventFilter(self)

        self.resize(560, 420)

    def set_items(self, items: list[PaletteItem]) -> None:
        self._items = list(items)
        self._refilter(self._input.text())

    def _refilter(self, query: str) -> None:
        scored: list[tuple[int, PaletteItem]] = []
        for it in self._items:
            score = _subseq_score(query, f"{it.section} {it.title}")
            if score is not None:
                scored.append((score, it))
        scored.sort(key=lambda p: p[0])

        self._filtered = [it for _, it in scored]
        self._list.clear()
        for it in self._filtered:
            row = QListWidgetItem(f"  {it.title}    ·  {it.section}")
            self._list.addItem(row)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _activate_current(self) -> None:
        idx = self._list.currentRow()
        if 0 <= idx < len(self._filtered):
            cb = self._filtered[idx].callback
            self.close()
            try:
                cb()
            except Exception:
                pass

    def eventFilter(self, obj: object, event: QEvent) -> bool:  # noqa: N802
        if obj is self._input and event.type() == QEvent.KeyPress:
            assert isinstance(event, QKeyEvent)
            key = event.key()
            if key == Qt.Key_Down:
                self._list.setCurrentRow(
                    min(self._list.count() - 1, self._list.currentRow() + 1)
                )
                return True
            if key == Qt.Key_Up:
                self._list.setCurrentRow(max(0, self._list.currentRow() - 1))
                return True
            if key == Qt.Key_Escape:
                self.close()
                return True
        return super().eventFilter(obj, event)

    def open_centered(self) -> None:
        self._input.clear()
        self._refilter("")
        if self._shell is not None:
            g = self._shell.geometry()
            self.move(
                g.x() + (g.width() - self.width()) // 2,
                g.y() + max(60, (g.height() - self.height()) // 3),
            )
        self._input.setFocus()
        self.show()
        self.raise_()
        self.activateWindow()
