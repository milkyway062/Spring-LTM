"""Right-docked collapsible log panel."""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QFont, QTextOption
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import macro_gui.theme as theme

EXPANDED_W: int = 240
COLLAPSED_W: int = 32


class ConsolePanel(QWidget):
    """Collapsible monospace log panel docked to the right edge of the shell.

    The panel animates between :data:`EXPANDED_W` and :data:`COLLAPSED_W`
    unless ``theme.reduce_motion()`` returns ``True``, in which case the
    resize is instant.

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Console")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedWidth(EXPANDED_W)
        self._expanded: bool = True

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header bar
        hdr = QWidget()
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(8, 6, 8, 6)

        self._header_lbl = QLabel("LOG")
        self._header_lbl.setObjectName("SectionEyebrow")
        hdr_lay.addWidget(self._header_lbl)
        hdr_lay.addStretch()

        self._toggle_btn = QPushButton("◀")
        self._toggle_btn.setObjectName("ConsoleToggle")
        self._toggle_btn.setFixedSize(22, 22)
        self._toggle_btn.setCursor(Qt.PointingHandCursor)
        self._toggle_btn.clicked.connect(self.toggle)
        hdr_lay.addWidget(self._toggle_btn)

        lay.addWidget(hdr)

        # Monospace text area
        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setFont(QFont("Consolas,Courier New,monospace", 9))
        self._text.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        lay.addWidget(self._text, stretch=1)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("ConsoleToggle")
        clear_btn.setFixedHeight(24)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self._text.clear)
        lay.addWidget(clear_btn)

        # Animation references kept alive on the instance to avoid GC
        self._anim: QPropertyAnimation | None = None
        self._anim2: QPropertyAnimation | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def toggle(self) -> None:
        """Toggle the panel between expanded and collapsed states."""
        self._expanded = not self._expanded
        target_w = EXPANDED_W if self._expanded else COLLAPSED_W
        dur = 0 if theme.reduce_motion() else 220

        self._toggle_btn.setText("◀" if self._expanded else "▶")
        self._header_lbl.setVisible(self._expanded)
        self._text.setVisible(self._expanded)

        if dur == 0:
            self.setFixedWidth(target_w)
            return

        current_w = self.width()

        self._anim = QPropertyAnimation(self, b"minimumWidth", self)
        self._anim.setDuration(dur)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.setStartValue(current_w)
        self._anim.setEndValue(target_w)

        self._anim2 = QPropertyAnimation(self, b"maximumWidth", self)
        self._anim2.setDuration(dur)
        self._anim2.setEasingCurve(QEasingCurve.OutCubic)
        self._anim2.setStartValue(current_w)
        self._anim2.setEndValue(target_w)

        self._anim.start()
        self._anim2.start()

    def append_text(self, text: str) -> None:
        """Append *text* to the log, auto-scrolling if already at the bottom.

        Args:
            text: Line(s) to append.
        """
        sb = self._text.verticalScrollBar()
        at_bottom = sb.value() >= sb.maximum() - 4
        self._text.appendPlainText(text)
        if at_bottom:
            self._text.moveCursor(self._text.textCursor().End)

    def clear(self) -> None:
        """Clear all log content."""
        self._text.clear()

    def is_expanded(self) -> bool:
        """Return ``True`` if the panel is currently expanded."""
        return self._expanded
