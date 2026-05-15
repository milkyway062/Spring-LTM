from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from macro_gui.widgets.card import Divider, SectionHeader


def build(frame: QWidget, app) -> None:
    """Build the UPDATE page inside *frame*.

    Args:
        frame: Container widget owned by the page stack.
        app: MacroApp orchestrator instance.
    """
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(20, 20, 20, 20)
    lay.setSpacing(0)

    # ── Header ────────────────────────────────────────────────────
    lay.addWidget(
        SectionHeader("maintenance", "Update", "Check GitHub for the latest version")
    )
    lay.addSpacing(8)
    lay.addWidget(Divider())
    lay.addSpacing(20)

    # ── Check button ──────────────────────────────────────────────
    btn = QPushButton("Check for Updates")
    btn.setObjectName("BtnPrimary")
    btn.setFixedSize(180, 36)
    btn.setCursor(Qt.PointingHandCursor)
    btn.clicked.connect(app._on_update)
    app._update_btn = btn
    lay.addWidget(btn, alignment=Qt.AlignLeft)
    lay.addSpacing(12)

    # ── Status label ──────────────────────────────────────────────
    status_lbl = QLabel("")
    status_lbl.setObjectName("SectionSub")
    status_lbl.setWordWrap(True)
    app._update_status_lbl = status_lbl
    lay.addWidget(status_lbl)

    lay.addStretch(1)
