"""Frameless shell window with rounded glass body and drag-to-move support."""
from __future__ import annotations

import ctypes

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QMouseEvent, QResizeEvent
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

_gdi32 = ctypes.windll.gdi32
_user32 = ctypes.windll.user32
_RGN_DIFF = 4
_SHELL_RADIUS = 22  # matches token "radii.xl" in themes/*.json


class FramelessShell(QMainWindow):
    """Frameless main window with a rounded translucent shell.

    Layout is managed externally via ``set_topbar``, ``set_body`` and
    ``set_drawer``. Drag-to-move is delegated from the top bar through
    ``start_drag`` / ``do_drag`` / ``stop_drag``. The drag anchor MUST
    be updated on every move tick — otherwise the window drifts
    exponentially (see ``pyside6-patterns §6``).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(1240, 760)
        self.resize(1380, 860)

        central = QWidget()
        central.setObjectName("Shell")
        central.setAttribute(Qt.WA_StyledBackground, True)
        self.setCentralWidget(central)

        self._layout = QVBoxLayout(central)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._drag_pos: QPoint | None = None
        self._dragging: bool = False
        self._hole: QRect | None = None
        self._hole_radius: int = 0

    def set_topbar(self, widget: QWidget) -> None:
        self._layout.insertWidget(0, widget)

    def set_body(self, widget: QWidget) -> None:
        self._layout.addWidget(widget, stretch=1)

    def set_drawer(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)

    def start_drag(self, pos: QPoint) -> None:
        self._dragging = True
        self._drag_pos = pos

    def do_drag(self, pos: QPoint) -> None:
        if self._dragging and self._drag_pos is not None:
            self.move(self.pos() + (pos - self._drag_pos))
            self._drag_pos = pos

    def stop_drag(self) -> None:
        self._dragging = False
        self._drag_pos = None

    # ── window-region hole (lets Roblox show through) ───────────

    def set_hole_rect(self, rect: QRect, radius: int = 0) -> None:
        """Cut a (rounded) hole out of the shell's window region.

        Used by ``RobloxEmbed`` so the macro chrome is no longer
        rendered over the docked Roblox window. The hole's corners are
        rounded to match the embed surface so Roblox's rectangular
        render area is clipped to the same curve.
        """
        self._hole = QRect(rect)
        self._hole_radius = max(0, int(radius))
        self._apply_region()

    def clear_hole_rect(self) -> None:
        """Restore the full rounded shell region."""
        self._hole = None
        _user32.SetWindowRgn(int(self.winId()), 0, True)

    def _apply_region(self) -> None:
        w = max(self.width(), 1)
        h = max(self.height(), 1)
        full = _gdi32.CreateRoundRectRgn(
            0, 0, w + 1, h + 1, _SHELL_RADIUS * 2, _SHELL_RADIUS * 2
        )
        if self._hole is not None:
            if self._hole_radius > 0:
                hole = _gdi32.CreateRoundRectRgn(
                    self._hole.left(),
                    self._hole.top(),
                    self._hole.right() + 1,
                    self._hole.bottom() + 1,
                    self._hole_radius * 2,
                    self._hole_radius * 2,
                )
            else:
                hole = _gdi32.CreateRectRgn(
                    self._hole.left(),
                    self._hole.top(),
                    self._hole.right() + 1,
                    self._hole.bottom() + 1,
                )
            _gdi32.CombineRgn(full, full, hole, _RGN_DIFF)
            _gdi32.DeleteObject(hole)
        # SetWindowRgn takes ownership of *full*; don't delete it.
        _user32.SetWindowRgn(int(self.winId()), full, True)

    def resizeEvent(self, e: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(e)
        if self._hole is not None:
            self._apply_region()
