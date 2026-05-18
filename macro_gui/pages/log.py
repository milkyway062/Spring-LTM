"""Log page — full-width terminal panel mirroring the console drawer."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextOption
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from macro_gui.widgets.card import Divider, GlassCard, SectionHeader


def build(frame: QWidget, app) -> None:
    """Build the LOG page inside *frame*."""
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(40, 36, 40, 36)
    lay.setSpacing(20)

    lay.addWidget(
        SectionHeader(
            "stream · live",
            "Log",
            "Worker output, mirrored from the bottom drawer.",
        )
    )
    lay.addWidget(Divider())

    card = GlassCard()
    card.body.setContentsMargins(20, 18, 20, 18)
    card.body.setSpacing(12)

    text = QPlainTextEdit()
    text.setObjectName("LogView")
    text.setReadOnly(True)
    text.setFont(QFont("JetBrains Mono", 10))
    text.setWordWrapMode(QTextOption.WrapMode.WordWrap)
    card.body.addWidget(text, stretch=1)

    app._log_text = text
    app._log_targets.append(text)

    btn_row = QHBoxLayout()
    btn_row.setSpacing(8)
    btn_row.addStretch(1)

    clear_btn = QPushButton("CLEAR")
    clear_btn.setObjectName("BtnGhost")
    clear_btn.setMinimumSize(100, 32)
    clear_btn.setCursor(Qt.PointingHandCursor)
    clear_btn.clicked.connect(text.clear)
    btn_row.addWidget(clear_btn)

    card.body.addLayout(btn_row)
    lay.addWidget(card, stretch=1)
