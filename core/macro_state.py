import threading

PRIVATE_SERVER_CODE  = ""
WEBHOOK_URL          = ""
LAST_WEBHOOK_OK      = False
LAST_WEBHOOK_ATTEMPT = 0.0

state = {
    "total_runs":      0,
    "total_run_time":  0.0,
    "session_start":   0.0,
    "run_start":       0.0,
    "last_run_time":   0.0,
    "last_webhook_ok": False,
    "running":         False,
}

_lock = threading.Lock()
