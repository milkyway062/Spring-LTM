import threading

PRIVATE_SERVER_CODE    = ""
WEBHOOK_URL            = ""
LAST_WEBHOOK_OK        = False
LAST_WEBHOOK_ATTEMPT   = 0.0
AUTO_REJOIN_AFTER_RUNS = 0
LARGE_LOBBY_ICONS      = True

_disconnect_event    = threading.Event()
_stuck_event         = threading.Event()
_auto_rejoin_event   = threading.Event()
_crash_event         = threading.Event()
_match_ended_event   = threading.Event()
_rejoin_in_progress  = False
_just_rejoined       = False

state = {
    "total_runs":       0,
    "total_run_time":   0.0,
    "session_start":    0.0,
    "run_start":        0.0,
    "last_run_time":    0.0,
    "last_webhook_ok":  False,
    "running":          False,
    "runs_since_rejoin": 0,
    "last_wave_seen":   0.0,
}

_lock = threading.Lock()
