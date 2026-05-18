"""Glass surfaces: HeroCard, GlassCard, StatBlock, SectionHeader, Divider.

Every custom-``QWidget`` subclass calls
``setAttribute(Qt.WA_StyledBackground, True)`` in ``__init__`` — without
it, QSS ``background``/``border``/``border-radius`` silently no-op
(see ``pyside6-patterns §1``).
"""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, Qt, QVariantAnimation
from PySide6.QtWidgets import (
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

import macro_gui.theme as theme


class HeroCard(QWidget):
    """Wide top card with eyebrow, display headline, subtitle, meta strip."""

    def __init__(
        self,
        eyebrow: str,
        title: str,
        subtitle: str = "",
        meta: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("HeroCard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(180)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 30, 36, 26)
        lay.setSpacing(10)

        eb = QLabel(eyebrow.upper())
        eb.setObjectName("HeroEyebrow")
        lay.addWidget(eb)

        t = QLabel(title)
        t.setObjectName("HeroTitle")
        lay.addWidget(t)

        if subtitle:
            s = QLabel(subtitle)
            s.setObjectName("HeroSub")
            s.setWordWrap(True)
            lay.addWidget(s)

        lay.addStretch(1)

        if meta:
            m = QLabel(meta)
            m.setObjectName("HeroMeta")
            lay.addWidget(m)


class GlassCard(QWidget):
    """Generic translucent card container.

    Children are added to ``self.body`` so callers don't fight the
    outer padding/margins.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(20, 18, 20, 18)
        self.body.setSpacing(8)


class StatBlock(QWidget):
    """Two-row block: big mono value on top, small uppercase label below."""

    def __init__(
        self,
        label: str,
        accent: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatBlock")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(112)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 18)
        lay.setSpacing(4)

        self._val = QLabel("—")
        self._val.setObjectName("StatAccent" if accent else "StatValue")
        self._val.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lay.addWidget(self._val)

        lay.addStretch(1)

        self._lbl = QLabel(label.upper())
        self._lbl.setObjectName("StatLabel")
        self._lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lay.addWidget(self._lbl)

        self._tween: QVariantAnimation | None = None
        self._last_int: int | None = None

    def set(self, value: str) -> None:
        """Set the stat value. Animates between integers; falls back to direct
        ``setText`` for non-numeric strings (timer formats, em-dash, etc.)."""
        text = str(value)
        new_int = self._as_int(text)

        if (
            new_int is not None
            and self._last_int is not None
            and new_int != self._last_int
            and not theme.reduce_motion()
        ):
            self._animate_to(self._last_int, new_int)
            self._last_int = new_int
            return

        if self._tween is not None:
            self._tween.stop()
            self._tween = None
        self._val.setText(text)
        self._last_int = new_int

    def _animate_to(self, start: int, end: int) -> None:
        if self._tween is not None:
            self._tween.stop()
        anim = QVariantAnimation(self)
        anim.setStartValue(int(start))
        anim.setEndValue(int(end))
        # Step duration scales gently with the magnitude of the change so a
        # single +1 reads as a quick flick and a large jump still feels paced.
        delta = abs(end - start)
        anim.setDuration(min(700, 220 + delta * 12))
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.valueChanged.connect(lambda v: self._val.setText(str(int(v))))
        anim.finished.connect(lambda: self._val.setText(str(end)))
        anim.start()
        self._tween = anim

    @staticmethod
    def _as_int(text: str) -> int | None:
        s = text.strip()
        if not s:
            return None
        try:
            return int(s)
        except ValueError:
            return None

    def value(self) -> str:
        return self._val.text()


class SectionHeader(QWidget):
    """Editorial header: small accent eyebrow + display title + sub line."""

    def __init__(
        self,
        eyebrow: str,
        title: str,
        subtitle: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        # No styled background — purely a layout container.

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        e = QLabel(eyebrow.upper())
        e.setObjectName("SectionEyebrow")
        lay.addWidget(e)

        t = QLabel(title)
        t.setObjectName("SectionTitle")
        lay.addWidget(t)

        if subtitle:
            s = QLabel(subtitle)
            s.setObjectName("SectionSub")
            s.setWordWrap(True)
            lay.addWidget(s)


class Divider(QWidget):
    """One-pixel horizontal hairline divider."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Divider")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(1)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)


