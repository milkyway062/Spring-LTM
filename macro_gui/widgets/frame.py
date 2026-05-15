"""Frameless shell window with rounded corners and drag-to-move support."""
from __future__ import annotations

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget


class FramelessShell(QMainWindow):
    """Frameless main window with a rounded, translucent shell.

    Layout is managed externally via :meth:`set_topbar` and :meth:`set_body`.
    The shell is not resizable in v1 — minimum size is 960×640.

    Drag-to-move is delegated from the TopBar widget via
    :meth:`start_drag`, :meth:`do_drag`, and :meth:`stop_drag`.

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(800, 560)
        self.resize(960, 640)

        central = QWidget()
        central.setObjectName("Shell")
        self.setCentralWidget(central)

        self._layout = QVBoxLayout(central)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._drag_pos: QPoint | None = None
        self._dragging: bool = False
        self._topbar_h: int = 56

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def set_topbar(self, widget: QWidget) -> None:
        """Insert *widget* as the top bar (index 0 in the shell layout).

        Args:
            widget: The top-bar widget, typically :class:`~macro_gui.widgets.topbar.TopBar`.
        """
        self._layout.insertWidget(0, widget)
        self._topbar_h = widget.minimumHeight() or 56

    def set_body(self, widget: QWidget) -> None:
        """Append *widget* as the body area, taking all remaining vertical space.

        Args:
            widget: Body widget containing the sidebar/content/console row.
        """
        self._layout.addWidget(widget, stretch=1)

    # ------------------------------------------------------------------
    # Drag-to-move protocol (called by TopBar)
    # ------------------------------------------------------------------

    def start_drag(self, pos: QPoint) -> None:
        """Begin a window drag sequence.

        Args:
            pos: Current cursor position in global screen coordinates.
        """
        self._dragging = True
        self._drag_pos = pos

    def do_drag(self, pos: QPoint) -> None:
        """Continue a window drag sequence, moving the window.

        Args:
            pos: Current cursor position in global screen coordinates.
        """
        if self._dragging and self._drag_pos is not None:
            delta = pos - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = pos

    def stop_drag(self) -> None:
        """End the current window drag sequence."""
        self._dragging = False
        self._drag_pos = None
