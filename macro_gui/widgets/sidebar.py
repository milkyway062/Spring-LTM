"""Sidebar navigation with icon + label nav buttons."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

ICON_MAP: dict[str, str] = {
    "run":      "▶",
    "settings": "✦",
    "log":      "≡",
    "update":   "↑",
}

SIDEBAR_W = 160


class SidebarNav(QWidget):
    page_selected = Signal(str)

    def __init__(self, pages: list[tuple[str, str]],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedWidth(SIDEBAR_W)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        logo = QLabel("◈")
        logo.setObjectName("NavIcon")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedHeight(56)
        logo.setFont(QFont("Segoe UI", 18))
        outer.addWidget(logo)

        sep = QFrame()
        sep.setObjectName("Divider")
        sep.setAttribute(Qt.WA_StyledBackground, True)
        sep.setFixedHeight(1)
        outer.addWidget(sep)

        outer.addSpacing(6)

        self._items: list[NavButton] = []
        for page_id, label in pages:
            btn = NavButton(page_id, label, ICON_MAP.get(page_id, "•"), self)
            btn.clicked_page.connect(self._on_click)
            outer.addWidget(btn)
            self._items.append(btn)

        outer.addStretch(1)

    def _on_click(self, page_id: str) -> None:
        self.set_active(page_id)
        self.page_selected.emit(page_id)

    def set_active(self, page_id: str) -> None:
        for item in self._items:
            item.set_active(item.page_id == page_id)


class NavButton(QWidget):
    clicked_page = Signal(str)

    def __init__(self, page_id: str, label: str, icon: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.page_id = page_id
        self._active = False

        self.setObjectName("NavBtn")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("active", "false")
        self.setFixedWidth(SIDEBAR_W)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 10, 8, 10)
        lay.setSpacing(3)
        lay.setAlignment(Qt.AlignCenter)

        self._icon_lbl = QLabel(icon)
        self._icon_lbl.setObjectName("NavIcon")
        self._icon_lbl.setAlignment(Qt.AlignCenter)
        self._icon_lbl.setFont(QFont("Segoe UI", 16))
        lay.addWidget(self._icon_lbl)

        self._text_lbl = QLabel(label)
        self._text_lbl.setObjectName("NavLabel")
        self._text_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._text_lbl)

    def set_active(self, active: bool) -> None:
        self._active = active
        self.setProperty("active", "true" if active else "false")
        for w in (self, self._icon_lbl, self._text_lbl):
            self.style().unpolish(w)
            self.style().polish(w)
        self.update()

    def mousePressEvent(self, e: object) -> None:
        if hasattr(e, "button") and e.button() == Qt.LeftButton:
            self.clicked_page.emit(self.page_id)
