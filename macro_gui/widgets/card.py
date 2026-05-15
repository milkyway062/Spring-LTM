"""Card and stat block widgets."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget


class StatBlock(QWidget):
    def __init__(self, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatBlock")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumWidth(110)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(3)
        lay.setAlignment(Qt.AlignCenter)

        self._val = QLabel("—")
        self._val.setObjectName("StatValue")
        self._val.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._val)

        self._lbl = QLabel(label.upper())
        self._lbl.setObjectName("StatLabel")
        self._lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._lbl)

    def set(self, value: str) -> None:
        self._val.setText(value)

    def value(self) -> str:
        return self._val.text()


class HeroCard(QWidget):
    def __init__(self, title: str, subtitle: str = "",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("HeroCard")
        self.setAttribute(Qt.WA_StyledBackground, True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(4)

        t = QLabel(title)
        t.setObjectName("SectionTitle")
        lay.addWidget(t)

        if subtitle:
            s = QLabel(subtitle)
            s.setObjectName("SectionSub")
            s.setWordWrap(True)
            lay.addWidget(s)


class SectionHeader(QWidget):
    def __init__(self, eyebrow: str, title: str, subtitle: str = "",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)

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
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Divider")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(1)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
