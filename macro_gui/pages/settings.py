"""Settings page — editorial column of fields plus theme switcher."""
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
from macro_gui.widgets.card import Divider, GlassCard, SectionHeader
from macro_gui.widgets.field import build_field


def build(frame: QWidget, app) -> None:
    """Build the SETTINGS page inside *frame*."""
    scroll = QScrollArea(frame)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.NoFrame)

    frame_lay = QVBoxLayout(frame)
    frame_lay.setContentsMargins(0, 0, 0, 0)
    frame_lay.setSpacing(0)
    frame_lay.addWidget(scroll)

    inner = QWidget()
    inner.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    inner.setMaximumWidth(880)
    lay = QVBoxLayout(inner)
    lay.setContentsMargins(40, 36, 40, 36)
    lay.setSpacing(20)
    scroll.setWidget(inner)

    lay.addWidget(
        SectionHeader(
            "config · 01",
            "Configuration",
            "Webhooks, hotkeys, rejoin cadence, and visual tuning.",
        )
    )
    lay.addWidget(Divider())

    # ── fields card ──────────────────────────────────────────────
    fields_card = GlassCard()
    fields_card.body.setContentsMargins(28, 24, 28, 12)
    fields_card.body.setSpacing(0)

    for f in app.spec.fields:
        w = build_field(
            inner,
            f,
            get=lambda fid=f.id: app.get_field(fid),
            set_=lambda val, fid=f.id: app._set_field(fid, val),
        )
        fields_card.body.addWidget(w)

    lay.addWidget(fields_card)

    # ── appearance card ──────────────────────────────────────────
    appearance = GlassCard()
    appearance.body.setContentsMargins(28, 22, 28, 22)
    appearance.body.setSpacing(14)

    eye = QLabel("APPEARANCE · 02")
    eye.setObjectName("SectionEyebrow")
    appearance.body.addWidget(eye)

    theme_label = QLabel("Theme")
    theme_label.setObjectName("FieldEyebrow")
    appearance.body.addWidget(theme_label)

    theme_row = QHBoxLayout()
    theme_row.setSpacing(12)

    combo = QComboBox()
    combo.setMaximumWidth(280)
    for t in theme.available_themes():
        combo.addItem(t)
    combo.setCurrentText(theme.name())
    combo.currentTextChanged.connect(lambda t: app._switch_theme(t))
    theme_row.addWidget(combo)

    caption = QLabel("Switches the entire window palette without restart.")
    caption.setObjectName("FieldHelp")
    caption.setWordWrap(True)
    theme_row.addWidget(caption, stretch=1)

    appearance.body.addLayout(theme_row)
    lay.addWidget(appearance)

    lay.addStretch(1)
