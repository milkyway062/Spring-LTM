from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from macro_gui.widgets.card import HeroCard, StatBlock

STYLE_MAP: dict[str, str] = {
    "primary": "BtnPrimary",
    "danger": "BtnDanger",
    "neutral": "BtnNeutral",
    "ghost": "BtnGhost",
}


def build(frame: QWidget, app) -> None:
    """Build the RUN page inside *frame*.

    Args:
        frame: Container widget owned by the page stack.
        app: MacroApp orchestrator instance.
    """
    scroll = QScrollArea(frame)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.NoFrame)

    frame_lay = QVBoxLayout(frame)
    frame_lay.setContentsMargins(0, 0, 0, 0)
    frame_lay.setSpacing(0)
    frame_lay.addWidget(scroll)

    inner = QWidget()
    inner.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    lay = QVBoxLayout(inner)
    lay.setContentsMargins(20, 20, 20, 20)
    lay.setSpacing(0)
    scroll.setWidget(inner)

    # ── Hero ──────────────────────────────────────────────────────
    lay.addWidget(HeroCard("Spring LTM", "Anime Vanguards automation"))
    lay.addSpacing(12)

    # ── Action buttons ────────────────────────────────────────────
    btn_row = QHBoxLayout()
    btn_row.setSpacing(8)

    for action in app.spec.actions.values():
        btn = QPushButton(action.label)
        btn.setObjectName(STYLE_MAP.get(action.style, "BtnNeutral"))
        btn.setFixedHeight(36)
        btn.setMinimumWidth(120)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(action.callback)
        app._action_buttons[action.id] = btn
        btn_row.addWidget(btn)

    btn_row.addStretch(1)
    lay.addLayout(btn_row)
    lay.addSpacing(16)

    # ── Stats row ─────────────────────────────────────────────────
    stats_row = QHBoxLayout()
    stats_row.setSpacing(10)

    for stat in app.spec.stats:
        blk = StatBlock(stat.label)
        app._stat_blocks[stat.id] = blk
        stats_row.addWidget(blk)

    stats_row.addStretch(1)
    lay.addLayout(stats_row)
    lay.addSpacing(16)

    # ── Phase block ───────────────────────────────────────────────
    phase_wrap = QWidget()
    phase_wrap.setObjectName("PhaseLine")
    phase_wrap.setAttribute(Qt.WA_StyledBackground, True)
    pw_lay = QHBoxLayout(phase_wrap)
    pw_lay.setContentsMargins(12, 8, 12, 8)
    pw_lay.setSpacing(0)

    phase_lbl = QLabel("—")
    phase_lbl.setObjectName("PhaseText")
    pw_lay.addWidget(phase_lbl)

    app._phase_lbl = phase_lbl
    lay.addWidget(phase_wrap)

    lay.addStretch(1)
