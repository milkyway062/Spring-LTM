"""Update page — check GitHub for a newer release."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from macro_gui.widgets.card import Divider, GlassCard, SectionHeader


def build(frame: QWidget, app) -> None:
    """Build the UPDATE page inside *frame*."""
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(40, 36, 40, 36)
    lay.setSpacing(20)

    lay.addWidget(
        SectionHeader(
            "maintenance",
            "Update",
            "Check GitHub for the latest release of Spring LTM.",
        )
    )
    lay.addWidget(Divider())

    card = GlassCard()
    card.body.setContentsMargins(28, 24, 28, 24)
    card.body.setSpacing(14)

    row = QHBoxLayout()
    row.setSpacing(14)

    btn = QPushButton("CHECK FOR UPDATES")
    btn.setObjectName("BtnPrimary")
    btn.setMinimumSize(220, 40)
    btn.setCursor(Qt.PointingHandCursor)
    btn.clicked.connect(app._on_update)
    app._update_btn = btn
    row.addWidget(btn)
    row.addStretch(1)

    card.body.addLayout(row)

    status_lbl = QLabel("")
    status_lbl.setObjectName("SectionSub")
    status_lbl.setWordWrap(True)
    app._update_status_lbl = status_lbl
    card.body.addWidget(status_lbl)

    lay.addWidget(card)
    lay.addStretch(1)
