from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

import macro_gui.theme as theme
from macro_gui.widgets.card import Divider, SectionHeader
from macro_gui.widgets.field import build_field


def build(frame: QWidget, app) -> None:
    """Build the SETTINGS page inside *frame*.

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

    # ── Header ────────────────────────────────────────────────────
    lay.addWidget(SectionHeader("config", "Settings", "Configure macro behaviour"))
    lay.addSpacing(8)
    lay.addWidget(Divider())
    lay.addSpacing(16)

    # ── Fields ────────────────────────────────────────────────────
    for f in app.spec.fields:
        w = build_field(
            inner,
            f,
            get=lambda fid=f.id: app.get_field(fid),
            set_=lambda val, fid=f.id: app._set_field(fid, val),
        )
        lay.addWidget(w)
        lay.addSpacing(4)

    lay.addSpacing(24)

    # ── Appearance section ────────────────────────────────────────
    eye = QLabel("APPEARANCE")
    eye.setObjectName("SectionEyebrow")
    lay.addWidget(eye)
    lay.addSpacing(6)
    lay.addWidget(Divider())
    lay.addSpacing(12)

    theme_row = QWidget()
    tr_lay = QHBoxLayout(theme_row)
    tr_lay.setContentsMargins(0, 0, 0, 0)
    tr_lay.setSpacing(12)

    t_lbl = QLabel("Theme")
    t_lbl.setObjectName("FieldLabel")
    t_lbl.setFixedWidth(160)
    tr_lay.addWidget(t_lbl)

    combo = QComboBox()
    combo.setFixedWidth(200)
    for t in theme.available_themes():
        combo.addItem(t)
    combo.setCurrentText(theme.name())
    combo.currentTextChanged.connect(lambda t: app._switch_theme(t))
    tr_lay.addWidget(combo)
    tr_lay.addStretch(1)

    lay.addWidget(theme_row)
    lay.addStretch(1)
