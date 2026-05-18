"""Field row builder: maps a FieldSpec to a labelled PySide6 control.

The signature ``build_field(parent, spec, get, set_) -> QWidget`` is
unchanged from the previous implementation — only the layout chrome
around each control is restyled. The Settings page calls this factory
for every ``FieldSpec`` in ``MacroSpec.fields``.
"""
from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from macro_gui.spec import FieldSpec


def build_field(
    parent: QWidget,
    spec: FieldSpec,
    get: Callable[[], Any],
    set_: Callable[[Any], None],
) -> QWidget:
    """Build a single editorial-style field row.

    Layout: eyebrow (small caps), label + control on one line, help
    caption below in italics.

    Args:
        parent: Parent widget that will own the returned shell.
        spec: ``FieldSpec`` describing the control to build.
        get: Zero-arg callable that returns the current field value.
        set_: Single-arg callable that persists a new field value.

    Returns:
        A ``QWidget`` ready to be inserted into a vertical layout.
    """
    shell = QWidget(parent)
    shell.setObjectName("FieldShell")
    outer = QVBoxLayout(shell)
    outer.setContentsMargins(0, 0, 0, 16)
    outer.setSpacing(8)

    eyebrow = QLabel(spec.label.upper())
    eyebrow.setObjectName("FieldEyebrow")
    outer.addWidget(eyebrow)

    row = QWidget()
    row_lay = QHBoxLayout(row)
    row_lay.setContentsMargins(0, 0, 0, 0)
    row_lay.setSpacing(12)

    ctrl = _build_control(spec, get, set_)
    row_lay.addWidget(ctrl, stretch=1)
    outer.addWidget(row)

    if spec.help:
        help_lbl = QLabel(spec.help)
        help_lbl.setObjectName("FieldHelp")
        help_lbl.setWordWrap(True)
        outer.addWidget(help_lbl)

    return shell


def _build_control(
    spec: FieldSpec,
    get: Callable[[], Any],
    set_: Callable[[Any], None],
) -> QWidget:
    if spec.kind == "bool":
        cb = QCheckBox("Enabled" if bool(get()) else "Disabled")
        cb.setChecked(bool(get()))

        def _on_check(state: int) -> None:
            val = bool(state)
            cb.setText("Enabled" if val else "Disabled")
            set_(val)
            if spec.on_change is not None:
                spec.on_change(val)

        cb.stateChanged.connect(_on_check)
        return cb

    if spec.kind == "int":
        sb = QSpinBox()
        sb.setRange(0, 99999)
        sb.setValue(int(get()) if get() is not None else 0)
        sb.setFixedWidth(160)
        sb.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        def _on_spin(val: int) -> None:
            set_(val)
            if spec.on_change is not None:
                spec.on_change(val)

        sb.valueChanged.connect(_on_spin)
        return sb

    if spec.kind == "choice":
        cb2 = QComboBox()
        for choice in spec.choices:
            cb2.addItem(choice)
        current = get()
        if current is not None and str(current) in spec.choices:
            cb2.setCurrentText(str(current))
        cb2.setMaximumWidth(280)

        def _on_combo(text: str) -> None:
            set_(text)
            if spec.on_change is not None:
                spec.on_change(text)

        cb2.currentTextChanged.connect(_on_combo)
        return cb2

    # text / password
    le = QLineEdit()
    if spec.kind == "password":
        le.setEchoMode(QLineEdit.Password)
    le.setText(str(get()) if get() is not None else "")

    def _commit() -> None:
        val = le.text().strip()
        set_(val)
        if spec.on_change is not None:
            spec.on_change(val)

    le.editingFinished.connect(_commit)
    return le
