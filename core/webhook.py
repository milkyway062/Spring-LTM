import logging
import time
from datetime import datetime, timezone

import requests

import macro_state

logger = logging.getLogger(__name__)


def _fmt_duration(seconds: float) -> str:
    s = int(seconds)
    days = s // 86400
    rem  = s % 86400
    h    = rem // 3600
    m    = (rem % 3600) // 60
    sec  = rem % 60
    if days > 0:
        return f"{days}d {h:02d}:{m:02d}:{sec:02d}"
    return f"{h:02d}:{m:02d}:{sec:02d}"


def send(run_time_secs: float, retries: int = 3) -> bool:
    macro_state.LAST_WEBHOOK_ATTEMPT = time.time()

    if not macro_state.WEBHOOK_URL or not macro_state.WEBHOOK_URL.startswith("https://discord.com/api/webhooks/"):
        logger.info("Webhook URL not configured; skipping.")
        macro_state.LAST_WEBHOOK_OK = False
        return False

    total_runs      = macro_state.state["total_runs"]
    total_run_time  = macro_state.state["total_run_time"]
    session_elapsed = time.time() - macro_state.state["session_start"]

    avg_secs    = total_run_time / total_runs if total_runs > 0 else 0
    avg_str     = f"{int(avg_secs // 60)}:{int(avg_secs % 60):02d}"
    run_str     = _fmt_duration(run_time_secs)
    session_str = _fmt_duration(session_elapsed)

    embed = {
        "title": "Spring LTM Macro",
        "color": 0x5b8dd9,
        "fields": [
            {"name": "🕒 Run Time",           "value": run_str,        "inline": True},
            {"name": "⏱️ Avg Clear Time",     "value": avg_str,        "inline": True},
            {"name": "🗓️ Session Time",       "value": session_str,    "inline": True},
            {"name": "🔁 Total Runs",         "value": str(total_runs),"inline": True},
        ],
        "footer":    {"text": f"Spring LTM Macro | Run time: {run_str}"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    payload = {
        "username": "Spring LTM Macro",
        "embeds":   [embed],
    }

    headers = {"Content-Type": "application/json"}
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(macro_state.WEBHOOK_URL, json=payload,
                                 headers=headers, timeout=10)
            if resp.status_code in (200, 201, 204):
                logger.info("Webhook sent (attempt %d).", attempt)
                macro_state.LAST_WEBHOOK_OK          = True
                macro_state.state["last_webhook_ok"] = True
                return True
            else:
                logger.warning("Webhook attempt %d failed: %s %s",
                               attempt, resp.status_code, resp.text)
        except requests.RequestException:
            logger.exception("Webhook attempt %d raised an exception", attempt)
        time.sleep(1)

    logger.error("All %d webhook attempts failed.", retries)
    macro_state.LAST_WEBHOOK_OK          = False
    macro_state.state["last_webhook_ok"] = False
    return False
