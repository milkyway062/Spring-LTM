"""Game page — Roblox embedded on the left, compact control rail on the right.

The right rail surfaces the essentials only (status pill, key stats,
start/stop, mini log) so the heavy Settings page stays the home of
field configuration. Embed reparenting is handled by ``RobloxEmbed``.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextOption
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from macro_gui.widgets.card import GlassCard, StatBlock
from macro_gui.widgets.embed import RobloxEmbed

STYLE_MAP: dict[str, str] = {
    "primary": "BtnPrimary",
    "danger":  "BtnDanger",
    "neutral": "BtnNeutral",
    "ghost":   "BtnGhost",
}


def build(frame: QWidget, app) -> None:
    """Build the GAME page inside *frame*."""
    root = QHBoxLayout(frame)
    root.setContentsMargins(24, 24, 24, 24)
    root.setSpacing(20)

    # ── left: Roblox embed surface ───────────────────────────────
    embed = RobloxEmbed()
    root.addWidget(embed, stretch=1)

    # ── right: control rail ──────────────────────────────────────
    rail = QWidget()
    rail.setFixedWidth(340)
    rail_lay = QVBoxLayout(rail)
    rail_lay.setContentsMargins(0, 0, 0, 0)
    rail_lay.setSpacing(14)

    # session header card
    head = GlassCard()
    head.body.setContentsMargins(22, 18, 22, 18)
    head.body.setSpacing(6)
    eye = QLabel("SESSION · LIVE")
    eye.setObjectName("SectionEyebrow")
    head.body.addWidget(eye)
    sess = QLabel("Spring LTM")
    sess.setObjectName("SectionTitle")
    head.body.addWidget(sess)
    sub = QLabel("F1 start · F3 stop · F4 webhook test")
    sub.setObjectName("SectionSub")
    sub.setWordWrap(True)
    head.body.addWidget(sub)
    rail_lay.addWidget(head)

    # attach/detach controls
    embed_ctrl = GlassCard()
    embed_ctrl.body.setContentsMargins(20, 16, 20, 16)
    embed_ctrl.body.setSpacing(10)
    ec_eye = QLabel("DOCK")
    ec_eye.setObjectName("SectionEyebrow")
    embed_ctrl.body.addWidget(ec_eye)

    btn_row = QHBoxLayout()
    btn_row.setSpacing(8)
    dock_btn = QPushButton("DOCK")
    dock_btn.setObjectName("BtnPrimary")
    dock_btn.setMinimumHeight(34)
    dock_btn.setCursor(Qt.PointingHandCursor)

    undock_btn = QPushButton("UNDOCK")
    undock_btn.setObjectName("BtnGhost")
    undock_btn.setMinimumHeight(34)
    undock_btn.setCursor(Qt.PointingHandCursor)

    state_lbl = QLabel("not docked")
    state_lbl.setObjectName("FieldHelp")

    def _do_dock() -> None:
        ok = embed.attach()
        state_lbl.setText("docked" if ok else "Roblox not running")

    def _do_undock() -> None:
        embed.detach()
        state_lbl.setText("not docked")

    dock_btn.clicked.connect(_do_dock)
    undock_btn.clicked.connect(_do_undock)

    btn_row.addWidget(dock_btn)
    btn_row.addWidget(undock_btn)
    embed_ctrl.body.addLayout(btn_row)
    embed_ctrl.body.addWidget(state_lbl)
    rail_lay.addWidget(embed_ctrl)

    # stats grid (2×2)
    stats_card = GlassCard()
    stats_card.body.setContentsMargins(20, 16, 20, 18)
    stats_card.body.setSpacing(10)
    s_eye = QLabel("SIGNAL")
    s_eye.setObjectName("SectionEyebrow")
    stats_card.body.addWidget(s_eye)

    grid = QGridLayout()
    grid.setHorizontalSpacing(10)
    grid.setVerticalSpacing(10)
    accent_ids = {"runs", "uptime"}
    for i, stat in enumerate(app.spec.stats[:4]):
        blk = StatBlock(stat.label, accent=(stat.id in accent_ids))
        app._stat_blocks.setdefault(stat.id, []).append(blk)
        grid.addWidget(blk, i // 2, i % 2)
    stats_card.body.addLayout(grid)
    rail_lay.addWidget(stats_card)

    # actions
    actions_card = GlassCard()
    actions_card.body.setContentsMargins(20, 16, 20, 16)
    actions_card.body.setSpacing(10)
    a_eye = QLabel("CONTROLS")
    a_eye.setObjectName("SectionEyebrow")
    actions_card.body.addWidget(a_eye)
    a_row = QHBoxLayout()
    a_row.setSpacing(8)
    for action in app.spec.actions.values():
        btn = QPushButton(action.label.upper())
        btn.setObjectName(STYLE_MAP.get(action.style, "BtnNeutral"))
        btn.setMinimumHeight(38)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(action.callback)
        app._action_buttons.setdefault(action.id, []).append(btn)
        a_row.addWidget(btn)
    a_row.addStretch(1)
    actions_card.body.addLayout(a_row)
    rail_lay.addWidget(actions_card)

    # mini log
    log_card = GlassCard()
    log_card.body.setContentsMargins(20, 16, 20, 16)
    log_card.body.setSpacing(8)
    l_eye = QLabel("LOG")
    l_eye.setObjectName("SectionEyebrow")
    log_card.body.addWidget(l_eye)

    mini = QPlainTextEdit()
    mini.setObjectName("LogView")
    mini.setReadOnly(True)
    mini.setFont(QFont("JetBrains Mono", 9))
    mini.setWordWrapMode(QTextOption.WrapMode.NoWrap)
    mini.setMaximumBlockCount(120)
    mini.setFixedHeight(120)
    log_card.body.addWidget(mini)
    app._log_targets.append(mini)
    rail_lay.addWidget(log_card)

    rail_lay.addStretch(1)
    root.addWidget(rail)
