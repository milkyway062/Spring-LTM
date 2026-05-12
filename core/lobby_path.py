"""
Lobby Pathing (Spring LTM)
--------------------------
Ported from Happy macro v2 (core/rejoin.py).
Closes lobby UI (daily rewards + leaderboard) then routes through the
AV lobby to the target Area / Stage / Act.

TODO(Spring LTM): set _TARGET_AREA / _TARGET_STAGE / _TARGET_ACT to the
Spring event destination once the Areas / Stages enum is updated to
include it (see avlib/AnimeVangaurdsLibrary/tools/av_game.py).
"""

import os
import sys
import threading
import time

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (
    os.path.join(_BASE, "rblib", "src"),
    os.path.join(_BASE, "avlib"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from AnimeVangaurdsLibrary.tools.av_game import Areas, lobby_path
import macro_state

# ------------------------------------------------------------------
# Target — CHANGE ME for Spring LTM
# ------------------------------------------------------------------
# Placeholder values copied from the Happy macro (Raid > Stage 4 > Act 1).
# Replace with the Spring LTM area/stage/act once known.
_TARGET_AREA: Areas = Areas.WINTER_EVENT
_TARGET_STAGE: int = 9
_TARGET_ACT: int = 1

# ------------------------------------------------------------------
# Image paths
# ------------------------------------------------------------------
_AREA_ICON = os.path.join(
    _BASE, "avlib", "AnimeVangaurdsLibrary", "tools", "resources", "AreaIcon.png"
)
_VOTE_START_IMG = os.path.join(_BASE, "Images", "vote_start.png")

# Lobby UI close coordinates (verify these match the Spring LTM build)
_DAILY_REWARDS_CLOSE = (654, 187)
_LEADERBOARD_CLOSE   = (642, 115)


def is_in_lobby() -> bool:
    """True if the AreaIcon (lobby hub) is visible on screen."""
    try:
        from rblib import r_util
        return r_util.imageExists(_AREA_ICON, 0.75)
    except Exception:
        return False


def wait_for_vote_start(
    stop_event: threading.Event | None = None,
    log_cb=print,
    timeout: float = 120,
) -> bool:
    """Block until the Vote Start button appears. False on stop/timeout."""
    def stopped() -> bool:
        return stop_event is not None and stop_event.is_set()

    log_cb("Waiting for Vote Start…")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if stopped():
            return False
        try:
            from rblib import r_util
            if r_util.imageExists(_VOTE_START_IMG, 0.7):
                log_cb("Vote Start detected — game loaded")
                return True
        except Exception:
            pass
        time.sleep(0.5)

    log_cb("Vote Start wait timed out")
    return False


def _daily_rewards_visible() -> bool:
    try:
        from rblib import r_util
        return r_util.pixelMatchesColor(*_DAILY_REWARDS_CLOSE, (255, 255, 255), 5)
    except Exception:
        return False


def _close_lobby_ui(log_cb=print) -> None:
    """Dismiss daily rewards popup and leaderboard before pathing."""
    from rblib import r_input
    if _daily_rewards_visible():
        log_cb("Lobby: closing daily rewards")
        r_input.Click(*_DAILY_REWARDS_CLOSE, 0.3)
    log_cb("Lobby: closing leaderboard")
    r_input.Click(*_LEADERBOARD_CLOSE, 0.3)


def do_lobby_path(
    stop_event: threading.Event | None = None,
    log_cb=print,
) -> None:
    """Close lobby UI then path to the configured Spring LTM destination."""
    _close_lobby_ui(log_cb=log_cb)
    log_cb(
        f"Lobby path: navigating to {_TARGET_AREA.name} "
        f"(Stage {_TARGET_STAGE}, Act {_TARGET_ACT})"
    )
    lobby_path(_TARGET_AREA, _TARGET_STAGE, _TARGET_ACT, large_icons=macro_state.LARGE_LOBBY_ICONS)
    wait_for_vote_start(stop_event=stop_event, log_cb=log_cb)


if __name__ == "__main__":
    do_lobby_path()
