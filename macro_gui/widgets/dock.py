"""Side-by-side Roblox window snap helper."""
from __future__ import annotations

import sys

from PySide6.QtCore import (
    QEasingCurve,
    QObject,
    QPropertyAnimation,
    QRect,
    QTimer,
    Signal,
)
from PySide6.QtWidgets import QApplication, QWidget

import macro_gui.theme as theme


class SideBySideDocker(QObject):
    """Watches a Roblox window and snaps the macro GUI to its right edge.

    The docker polls at 500 ms intervals while active.  When the Roblox
    window moves or disappears the macro window is repositioned accordingly.

    Only works on Windows (``win32gui`` required).  On other platforms,
    :meth:`_find_roblox` always returns ``None`` and the docker degrades
    gracefully.

    Signals:
        status_changed: Emitted with one of ``"docked"``, ``"no game"``, or
            ``"idle"`` whenever the docking state changes.

    Args:
        window: The application main window to reposition.
        target_substr: Case-insensitive substring matched against window titles
            to locate the target game window.  Defaults to ``"Roblox"``.
        parent: Optional QObject parent.
    """

    status_changed = Signal(str)

    def __init__(
        self,
        window: QWidget,
        target_substr: str = "Roblox",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._window = window
        self._target = target_substr
        self._active: bool = False
        self._last_roblox_rect: tuple[int, int, int, int] | None = None

        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._watch)

        # Animation reference kept alive on the instance.
        self._snap_anim: QPropertyAnimation | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_active(self, active: bool) -> None:
        """Enable or disable side-by-side docking.

        Args:
            active: ``True`` to start docking; ``False`` to stop.
        """
        self._active = active
        if active:
            self._timer.start()
            if not self._find_roblox():
                self.status_changed.emit("no game")
            else:
                self.snap(animate=True)
        else:
            self._timer.stop()
            self.status_changed.emit("idle")

    def snap(self, animate: bool = False) -> None:
        """Immediately reposition the macro window next to the Roblox window.

        Args:
            animate: Whether to animate the move.  Animation is skipped when
                ``theme.reduce_motion()`` is ``True``.
        """
        rect = self._find_roblox()
        if rect is None:
            self.status_changed.emit("no game")
            return

        x, y, rx2, ry2 = rect
        roblox_right = rx2
        roblox_top = y
        roblox_h = ry2 - y

        screen = QApplication.primaryScreen().geometry()
        new_h = max(640, min(roblox_h, screen.height() - roblox_top - 40))
        new_x = roblox_right + 8
        new_y = roblox_top

        # Clamp so the window does not fall off the right edge.
        if new_x + self._window.width() > screen.width():
            new_x = max(0, screen.width() - self._window.width())

        if animate and not theme.reduce_motion():
            self._snap_anim = QPropertyAnimation(
                self._window, b"geometry", self._window
            )
            self._snap_anim.setDuration(200)
            self._snap_anim.setEasingCurve(QEasingCurve.OutCubic)
            self._snap_anim.setStartValue(self._window.geometry())
            self._snap_anim.setEndValue(
                QRect(new_x, new_y, self._window.width(), new_h)
            )
            self._snap_anim.start()
        else:
            self._window.move(new_x, new_y)
            self._window.resize(self._window.width(), new_h)

        self.status_changed.emit("docked")
        self._last_roblox_rect = rect

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _watch(self) -> None:
        """Timer callback — re-snap if the Roblox window has moved."""
        if not self._active:
            return
        rect = self._find_roblox()
        if rect is None:
            if self._last_roblox_rect is not None:
                self.status_changed.emit("no game")
                self._last_roblox_rect = None
            return
        if rect != self._last_roblox_rect:
            self.snap(animate=False)

    def _find_roblox(self) -> tuple[int, int, int, int] | None:
        """Return the bounding rect of the first visible matching window.

        Returns:
            ``(left, top, right, bottom)`` in screen coordinates, or ``None``
            if the window could not be found or the platform is not Windows.
        """
        if sys.platform != "win32":
            return None
        try:
            import win32gui  # type: ignore[import]

            results: list[tuple[int, int, int, int]] = []

            def _enum_cb(hwnd: int, _: object) -> None:
                title = win32gui.GetWindowText(hwnd)
                if (
                    self._target.lower() in title.lower()
                    and win32gui.IsWindowVisible(hwnd)
                ):
                    results.append(win32gui.GetWindowRect(hwnd))

            win32gui.EnumWindows(_enum_cb, None)
            return results[0] if results else None
        except Exception:
            return None
