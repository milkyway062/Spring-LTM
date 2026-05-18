"""Snap-dock the Roblox window over a Qt embed area.

Roblox's anti-cheat (Hyperion) terminates the process when its window
is reparented via ``SetParent`` or has its frame styles stripped, so
true embedding isn't possible. Instead this widget *visually docks*
Roblox over its viewport: every heartbeat tick (and on every resize)
the Roblox HWND is moved and sized to the embed area's screen
rectangle. Roblox stays a top-level window and keeps full input.

Caveats:
  * Alt-tab can place another window on top — bring Spring LTM back to
    the front and the next tick snaps Roblox back over the embed area.
  * If Spring LTM is minimised, Roblox is left alone.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

try:
    from rblib.r_client import get_roblox_hwnd
except Exception:  # rblib only available in app context
    def get_roblox_hwnd() -> int | None:  # type: ignore[misc]
        return None


_user32 = ctypes.windll.user32

_SWP_NOSIZE = 0x0001
_SWP_NOMOVE = 0x0002
_SWP_NOZORDER = 0x0004
_SWP_NOACTIVATE = 0x0010
_SWP_SHOWWINDOW = 0x0040
_HWND_TOP = 0


def _frame_offsets(hwnd: int) -> tuple[int, int, int, int]:
    """Return ``(left, top, right, bottom)`` non-client margins for *hwnd*.

    Lets the caller size and position Roblox so its *client area*
    (the game render surface) aligns with a target rect instead of its
    outer window rect — i.e. the title bar and borders hang outside
    the visible region.
    """
    wr = wintypes.RECT()
    _user32.GetWindowRect(hwnd, ctypes.byref(wr))
    pt = wintypes.POINT(0, 0)
    _user32.ClientToScreen(hwnd, ctypes.byref(pt))
    cr = wintypes.RECT()
    _user32.GetClientRect(hwnd, ctypes.byref(cr))

    left = pt.x - wr.left
    top = pt.y - wr.top
    win_w = wr.right - wr.left
    win_h = wr.bottom - wr.top
    right = win_w - left - cr.right
    bottom = win_h - top - cr.bottom
    return left, top, right, bottom


class RobloxEmbed(QWidget):
    """Embed-area placeholder that snap-docks Roblox over its rectangle."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("EmbedSurface")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumSize(640, 360)

        self._hwnd: int | None = None
        self._docking: bool = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._placeholder = QLabel(
            "Roblox docks here when running.\n"
            "Launch the game, then press Dock."
        )
        self._placeholder.setObjectName("EmbedPlaceholder")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setWordWrap(True)
        lay.addWidget(self._placeholder)

        self._beat = QTimer(self)
        self._beat.setInterval(250)
        self._beat.timeout.connect(self._snap)

    def is_docked(self) -> bool:
        return self._docking

    def attach(self) -> bool:
        """Locate Roblox and start the snap loop."""
        hwnd = get_roblox_hwnd()
        if not hwnd:
            return False
        self._hwnd = hwnd
        self._docking = True
        self._placeholder.setVisible(False)
        self._snap()
        self._beat.start()
        return True

    def detach(self) -> None:
        """Stop the snap loop. Roblox keeps its current geometry."""
        self._docking = False
        self._beat.stop()
        self._hwnd = None
        self._placeholder.setVisible(True)
        self._clear_shell_hole()

    # Aliases kept so older callers reading earlier docs still work.
    dock = attach
    undock = detach

    def _snap(self) -> None:
        if not self._docking or self._hwnd is None:
            return
        if not _user32.IsWindow(self._hwnd):
            self.detach()
            return

        top_left = self.mapToGlobal(self.rect().topLeft())
        cw = max(self.width(), 1)
        ch = max(self.height(), 1)
        l, t, r, b = _frame_offsets(self._hwnd)
        shell_hwnd = int(self.window().winId())
        # 1. Position Roblox so its CLIENT area aligns with the embed
        #    rect. The title bar + borders fall outside and get
        #    covered by the macro chrome.
        # 2. Then pin Roblox just BELOW the shell in z-order so that
        #    if Roblox gains focus it can't raise above us. The hole
        #    in the shell region lets it remain visible.
        _user32.SetWindowPos(
            self._hwnd, shell_hwnd,
            int(top_left.x()) - l,
            int(top_left.y()) - t,
            cw + l + r,
            ch + t + b,
            _SWP_NOACTIVATE | _SWP_SHOWWINDOW,
        )
        self._push_shell_hole()

    # Matches token "radii.lg" used by EmbedSurface / GlassCard QSS.
    _CORNER_RADIUS = 18

    def _push_shell_hole(self) -> None:
        shell = self.window()
        if not hasattr(shell, "set_hole_rect"):
            return
        tl = self.mapTo(shell, self.rect().topLeft())
        shell.set_hole_rect(
            QRect(tl.x(), tl.y(), self.width(), self.height()),
            self._CORNER_RADIUS,
        )

    def _clear_shell_hole(self) -> None:
        shell = self.window()
        if hasattr(shell, "clear_hole_rect"):
            shell.clear_hole_rect()

    def resizeEvent(self, e: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(e)
        self._snap()

    def moveEvent(self, e) -> None:  # noqa: N802
        super().moveEvent(e)
        self._snap()

    def hideEvent(self, e) -> None:  # noqa: N802
        self._beat.stop()
        self._clear_shell_hole()
        super().hideEvent(e)

    def showEvent(self, e) -> None:  # noqa: N802
        super().showEvent(e)
        if self._docking:
            self._beat.start()
            self._snap()

    def closeEvent(self, e) -> None:  # noqa: N802
        self.detach()
        super().closeEvent(e)
