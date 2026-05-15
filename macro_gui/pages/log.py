from __future__ import annotations

from PySide6.QtGui import QFont, QTextOption
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from macro_gui.widgets.card import Divider, SectionHeader


def build(frame: QWidget, app) -> None:
    """Build the LOG page inside *frame*.

    Mirrors the same log output as the right console dock.  The app tick
    drains the log queue into *app._log_text* on every interval.

    Args:
        frame: Container widget owned by the page stack.
        app: MacroApp orchestrator instance.
    """
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(20, 20, 20, 20)
    lay.setSpacing(0)

    # ── Header ────────────────────────────────────────────────────
    lay.addWidget(SectionHeader("output", "Log", "Live output from macro worker"))
    lay.addSpacing(8)
    lay.addWidget(Divider())
    lay.addSpacing(12)

    # ── Text area ─────────────────────────────────────────────────
    text = QPlainTextEdit()
    text.setReadOnly(True)
    text.setFont(QFont("Consolas", 9))
    text.setWordWrapMode(QTextOption.WrapMode.WordWrap)
    lay.addWidget(text, stretch=1)

    app._log_text = text

    # ── Toolbar ───────────────────────────────────────────────────
    btn_row = QHBoxLayout()
    btn_row.setSpacing(8)

    clear_btn = QPushButton("Clear")
    clear_btn.setObjectName("BtnGhost")
    clear_btn.setFixedSize(80, 28)
    clear_btn.clicked.connect(text.clear)
    btn_row.addWidget(clear_btn)
    btn_row.addStretch(1)

    lay.addSpacing(8)
    lay.addLayout(btn_row)
