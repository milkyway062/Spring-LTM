"""Run page — hero + bento stats + controls strip + phase tag."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from macro_gui.widgets.card import GlassCard, HeroCard, StatBlock

STYLE_MAP: dict[str, str] = {
    "primary": "BtnPrimary",
    "danger":  "BtnDanger",
    "neutral": "BtnNeutral",
    "ghost":   "BtnGhost",
}


def build(frame: QWidget, app) -> None:
    """Build the RUN page inside *frame*."""
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
    lay.setContentsMargins(40, 36, 40, 36)
    lay.setSpacing(22)
    scroll.setWidget(inner)

    # ── hero ──────────────────────────────────────────────────────
    lay.addWidget(
        HeroCard(
            eyebrow="Spring LTM · Limited Time Mode",
            title="Spring,\nautomated.",
            subtitle=(
                "Hands-off Anime Vanguards runs — auto-rejoin, "
                "crash recovery, and lobby pathing handled for you."
            ),
            meta="Press F1 to start · F3 to stop",
        )
    )

    # ── bento stat grid (2×N depending on stat count) ────────────
    grid_wrap = GlassCard()
    grid_wrap.body.setContentsMargins(24, 22, 24, 22)
    grid_wrap.body.setSpacing(16)

    eyebrow = QLabel("LIVE SIGNAL")
    eyebrow.setObjectName("SectionEyebrow")
    grid_wrap.body.addWidget(eyebrow)

    grid = QGridLayout()
    grid.setHorizontalSpacing(14)
    grid.setVerticalSpacing(14)

    accent_ids = {"runs", "uptime"}
    stats = list(app.spec.stats)
    for i, stat in enumerate(stats):
        blk = StatBlock(stat.label, accent=(stat.id in accent_ids))
        app._stat_blocks.setdefault(stat.id, []).append(blk)
        grid.addWidget(blk, i // 2, i % 2)

    grid_wrap.body.addLayout(grid)
    lay.addWidget(grid_wrap)

    # ── controls strip ────────────────────────────────────────────
    ctrl_wrap = GlassCard()
    ctrl_wrap.body.setContentsMargins(24, 18, 24, 18)
    ctrl_wrap.body.setSpacing(10)

    ctrl_eye = QLabel("CONTROLS")
    ctrl_eye.setObjectName("SectionEyebrow")
    ctrl_wrap.body.addWidget(ctrl_eye)

    btn_row = QHBoxLayout()
    btn_row.setSpacing(10)

    for action in app.spec.actions.values():
        btn = QPushButton(action.label.upper())
        btn.setObjectName(STYLE_MAP.get(action.style, "BtnNeutral"))
        btn.setMinimumHeight(40)
        btn.setMinimumWidth(140)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(action.callback)
        app._action_buttons.setdefault(action.id, []).append(btn)
        btn_row.addWidget(btn)

    btn_row.addStretch(1)
    ctrl_wrap.body.addLayout(btn_row)
    lay.addWidget(ctrl_wrap)

    # ── phase tag ─────────────────────────────────────────────────
    phase_row = QHBoxLayout()
    phase_row.setContentsMargins(4, 0, 0, 0)
    phase_row.setSpacing(10)

    arrow = QLabel("›")
    arrow.setObjectName("SectionEyebrow")
    phase_row.addWidget(arrow)

    p_lbl = QLabel("ready")
    p_lbl.setObjectName("PhaseText")
    phase_row.addWidget(p_lbl)
    phase_row.addStretch(1)

    app._phase_lbl = p_lbl
    lay.addLayout(phase_row)

    lay.addStretch(1)
