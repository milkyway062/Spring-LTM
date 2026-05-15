"""Field row builder: maps a FieldSpec to a labelled PySide6 control."""
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
    """Build a labelled field row from *spec*.

    Returns a ``QWidget`` containing a ``QLabel`` on the left and the
    appropriate control on the right.  An optional help caption is rendered
    below the control row when ``spec.help`` is set.

    Supported ``spec.kind`` values:

    * ``"text"`` — :class:`~PySide6.QtWidgets.QLineEdit`, committed on
      ``editingFinished``.
    * ``"password"`` — same as ``"text"`` with ``Password`` echo mode.
    * ``"int"`` — :class:`~PySide6.QtWidgets.QSpinBox`, range 0–99 999.
    * ``"bool"`` — :class:`~PySide6.QtWidgets.QCheckBox` (no text label).
    * ``"choice"`` — :class:`~PySide6.QtWidgets.QComboBox` populated from
      ``spec.choices``.

    Args:
        parent: Parent widget to own the returned container.
        spec: Field specification describing the control to build.
        get: Zero-arg callable that returns the current field value.
        set_: Single-arg callable that persists a new field value.

    Returns:
        A ``QWidget`` row ready to be added to a layout.
    """
    container = QWidget(parent)
    outer = QVBoxLayout(container)
    outer.setContentsMargins(0, 0, 0, 6)
    outer.setSpacing(2)

    row = QWidget()
    row_lay = QHBoxLayout(row)
    row_lay.setContentsMargins(0, 0, 0, 0)
    row_lay.setSpacing(12)

    lbl = QLabel(spec.label)
    lbl.setObjectName("FieldLabel")
    lbl.setFixedWidth(160)
    lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
    row_lay.addWidget(lbl)

    ctrl: QWidget

    if spec.kind == "bool":
        ctrl = QCheckBox()
        ctrl.setChecked(bool(get()))

        def _on_check(state: int) -> None:
            val = bool(state)
            set_(val)
            if spec.on_change is not None:
                spec.on_change(val)

        ctrl.stateChanged.connect(_on_check)

    elif spec.kind == "int":
        ctrl = QSpinBox()
        ctrl.setRange(0, 99999)
        ctrl.setValue(int(get()) if get() is not None else 0)
        ctrl.setFixedWidth(120)

        def _on_spin(val: int) -> None:
            set_(val)
            if spec.on_change is not None:
                spec.on_change(val)

        ctrl.valueChanged.connect(_on_spin)

    elif spec.kind == "choice":
        ctrl = QComboBox()
        for choice in spec.choices:
            ctrl.addItem(choice)
        current = get()
        if current is not None and str(current) in spec.choices:
            ctrl.setCurrentText(str(current))
        ctrl.setFixedWidth(200)

        def _on_combo(text: str) -> None:
            set_(text)
            if spec.on_change is not None:
                spec.on_change(text)

        ctrl.currentTextChanged.connect(_on_combo)

    else:
        # text / password
        ctrl = QLineEdit()
        if spec.kind == "password":
            ctrl.setEchoMode(QLineEdit.Password)
        ctrl.setText(str(get()) if get() is not None else "")
        ctrl.setFixedWidth(240)

        def _commit() -> None:
            val = ctrl.text().strip()  # type: ignore[union-attr]
            set_(val)
            if spec.on_change is not None:
                spec.on_change(val)

        ctrl.editingFinished.connect(_commit)

    row_lay.addWidget(ctrl)
    row_lay.addStretch(1)
    outer.addWidget(row)

    if spec.help:
        help_lbl = QLabel(spec.help)
        # Inline style for the dim help caption — not worth a QSS selector.
        help_lbl.setStyleSheet(
            "color: #7d8699; font-size: 9px; font-style: italic;"
        )
        help_lbl.setIndent(172)
        outer.addWidget(help_lbl)

    return container
