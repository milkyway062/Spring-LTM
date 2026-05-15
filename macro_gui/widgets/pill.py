"""Pills: version badge, hotkey badge, status indicator."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget

_KIND_TO_OBJ: dict[str, str] = {
    "version": "PillVersion",
    "hotkey":  "PillHotkey",
    "status":  "PillStatus",
}


class Pill(QLabel):
    """Compact badge.  Extends QLabel so QSS background/border render natively.

    Args:
        text: Display text.
        kind: ``"version"`` | ``"hotkey"`` | ``"status"``.
        parent: Optional parent widget.
    """

    def __init__(self, text: str, kind: str = "hotkey",
                 parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName(_KIND_TO_OBJ.get(kind, "PillHotkey"))
        self.setAlignment(Qt.AlignCenter)

    def set_text(self, text: str) -> None:
        self.setText(text)
