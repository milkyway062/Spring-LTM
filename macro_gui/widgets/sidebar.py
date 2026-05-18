"""Icon-only left navigation rail."""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

import macro_gui.theme as theme

ICON_MAP: dict[str, str] = {
    "game":     "◉",
    "run":      "▶",
    "settings": "✦",
    "log":      "≡",
    "update":   "↑",
}

RAIL_W = 72
_INDICATOR_W = 3
_INDICATOR_INSET = 10  # vertical inset so the bar is shorter than the button


class SidebarNav(QWidget):
    """Vertical icon rail. Class name kept for ``MacroApp`` compatibility."""

    page_selected = Signal(str)

    def __init__(
        self,
        pages: list[tuple[str, str]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("NavRail")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedWidth(RAIL_W)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 18, 0, 18)
        outer.setSpacing(2)

        self._items: list[NavButton] = []
        for page_id, label in pages:
            btn = NavButton(page_id, label, ICON_MAP.get(page_id, "•"), self)
            btn.clicked_page.connect(self._on_click)
            outer.addWidget(btn)
            self._items.append(btn)

        outer.addStretch(1)

        # Floating indicator bar: child of the rail, positioned absolutely
        # and animated via geometry. Stays on top of NavButton siblings.
        self._indicator = QWidget(self)
        self._indicator.setObjectName("NavIndicator")
        self._indicator.setAttribute(Qt.WA_StyledBackground, True)
        self._indicator.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._indicator.setFixedWidth(_INDICATOR_W)
        self._indicator.hide()
        self._indicator_anim: QPropertyAnimation | None = None
        self._active_id: str | None = None

    def _on_click(self, page_id: str) -> None:
        self.set_active(page_id)
        self.page_selected.emit(page_id)

    def set_active(self, page_id: str) -> None:
        self._active_id = page_id
        for item in self._items:
            item.set_active(item.page_id == page_id)
        self._move_indicator_to(page_id)

    def _target_rect(self, page_id: str) -> QRect | None:
        for item in self._items:
            if item.page_id == page_id:
                g = item.geometry()
                return QRect(
                    0,
                    g.y() + _INDICATOR_INSET,
                    _INDICATOR_W,
                    max(8, g.height() - 2 * _INDICATOR_INSET),
                )
        return None

    def _move_indicator_to(self, page_id: str) -> None:
        target = self._target_rect(page_id)
        if target is None:
            return

        self._indicator.show()
        self._indicator.raise_()

        if theme.reduce_motion() or not self._indicator.isVisible():
            self._indicator.setGeometry(target)
            return

        start = self._indicator.geometry()
        if start.isEmpty() or start.width() == 0:
            # First show — snap into place, no jump animation from (0,0).
            self._indicator.setGeometry(target)
            return

        anim = QPropertyAnimation(self._indicator, b"geometry", self)
        anim.setDuration(240)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setStartValue(start)
        anim.setEndValue(target)
        anim.start()
        self._indicator_anim = anim

    def resizeEvent(self, e: object) -> None:  # noqa: N802
        super().resizeEvent(e)
        if self._active_id:
            target = self._target_rect(self._active_id)
            if target is not None:
                self._indicator.setGeometry(target)

    def showEvent(self, e: object) -> None:  # noqa: N802
        super().showEvent(e)
        if self._active_id:
            target = self._target_rect(self._active_id)
            if target is not None:
                self._indicator.setGeometry(target)
                self._indicator.show()
                self._indicator.raise_()


class NavButton(QWidget):
    """Single rail entry: glyph + active-state dot.

    Uses the dynamic ``active="true"`` property pattern; both the
    container and the inner labels are unpolished/polished on toggle
    so descendant QSS selectors update (see ``pyside6-patterns §3``).
    """

    clicked_page = Signal(str)

    def __init__(
        self,
        page_id: str,
        label: str,
        icon: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.page_id = page_id

        self.setObjectName("NavBtn")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("active", "false")
        self.setFixedSize(RAIL_W, 56)
        self.setToolTip(label)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 8, 0, 6)
        lay.setSpacing(2)
        lay.setAlignment(Qt.AlignCenter)

        self._icon_lbl = QLabel(icon)
        self._icon_lbl.setObjectName("NavIcon")
        self._icon_lbl.setAlignment(Qt.AlignCenter)
        self._icon_lbl.setFont(QFont("Segoe UI", 16))
        lay.addWidget(self._icon_lbl)

        self._dot_lbl = QLabel("●")
        self._dot_lbl.setObjectName("NavDot")
        self._dot_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._dot_lbl)

    def set_active(self, active: bool) -> None:
        self.setProperty("active", "true" if active else "false")
        for w in (self, self._icon_lbl, self._dot_lbl):
            self.style().unpolish(w)
            self.style().polish(w)
        self.update()

    def mousePressEvent(self, e: object) -> None:  # noqa: N802
        if hasattr(e, "button") and e.button() == Qt.LeftButton:
            self.clicked_page.emit(self.page_id)
