"""
Camera Sequence Tuner
---------------------
Build and test the camera movement sequence for Spring LTM.
Saves to config/camera_sequence.json.

Step types:
  key   <key> <secs>   - hold a key for N seconds (i, o, w, a, s, d, ...)
  mouse <dx> <dy>      - move mouse by (dx, dy) pixels (relative)
  delay <secs>         - wait N seconds

Commands:
  a key   <key> <secs>   append key-hold step       e.g.  a key i 1.5
  a mouse <dx>  <dy>     append mouse-move step      e.g.  a mouse 0 3000
  a delay <secs>         append delay step           e.g.  a delay 0.5
  i <idx> key   <key> <secs>   insert before index
  i <idx> mouse <dx>  <dy>
  i <idx> delay <secs>
  e <idx> key   <key> <secs>   edit step at index
  e <idx> mouse <dx>  <dy>
  e <idx> delay <secs>
  d <idx>                delete step
  u <idx>                move step up
  x <idx>                move step down
  t                      test sequence (3 s countdown, focus Roblox first)
  s                      save to config/camera_sequence.json
  r                      reload from file (discard unsaved changes)
  p                      print current sequence
  q                      quit
"""

import ctypes
import json
import os
import sys
import time

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (
    os.path.join(_BASE, "rblib", "src"),
    os.path.join(_BASE, "avlib"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from rblib import r_input

SEQUENCE_PATH = os.path.join(_BASE, "config", "camera_sequence.json")


def load() -> list[dict]:
    with open(SEQUENCE_PATH, "r") as f:
        return json.load(f)


def save(seq: list[dict]) -> None:
    with open(SEQUENCE_PATH, "w") as f:
        json.dump(seq, f, indent=2)
    print("  Saved.")


def fmt_step(step: dict) -> str:
    t = step["type"]
    if t == "key":
        return f"key  {step['key'].upper()}  {step['duration']:.2f}s"
    if t == "mouse":
        return f"mouse  dx={step['dx']}  dy={step['dy']}"
    if t == "delay":
        return f"delay  {step['seconds']:.2f}s"
    return str(step)


def print_sequence(seq: list[dict]) -> None:
    if not seq:
        print("  (empty)")
        return
    for i, step in enumerate(seq):
        print(f"  [{i}]  {fmt_step(step)}")


_mouse_event = ctypes.windll.user32.mouse_event


def _mouse_move(dx: int, dy: int) -> None:
    if dx:
        _mouse_event(0x0001, dx, 0, 0, 0)
    if dy:
        _mouse_event(0x0001, 0, dy, 0, 0)


def run_step(step: dict) -> None:
    t = step["type"]
    if t == "key":
        r_input.PressKey(step["key"], step["duration"])
    elif t == "mouse":
        _mouse_move(step["dx"], step["dy"])
    elif t == "delay":
        time.sleep(step["seconds"])


def run_sequence(seq: list[dict]) -> None:
    if not seq:
        print("  Sequence is empty — nothing to run.")
        return
    print("  Running in 3...")
    time.sleep(1)
    print("  2...")
    time.sleep(1)
    print("  1...")
    time.sleep(1)
    print("  GO")
    for step in seq:
        run_step(step)
    print("  Done.")


# ------------------------------------------------------------------
# Parsing helpers
# ------------------------------------------------------------------

def _parse_float(raw: str, label: str = "value") -> float | None:
    try:
        v = float(raw)
        return v
    except ValueError:
        print(f"  Bad {label}: {raw!r} — expected a number")
        return None


def _parse_positive(raw: str, label: str = "duration") -> float | None:
    v = _parse_float(raw, label)
    if v is not None and v <= 0:
        print(f"  {label} must be > 0")
        return None
    return v


def _parse_int(raw: str, label: str = "value") -> int | None:
    try:
        return int(raw)
    except ValueError:
        print(f"  Bad {label}: {raw!r} — expected integer")
        return None


def _parse_index(raw: str, seq: list) -> int | None:
    idx = _parse_int(raw, "index")
    if idx is None:
        return None
    if not (0 <= idx < len(seq)):
        print(f"  Index {idx} out of range (0–{len(seq) - 1})")
        return None
    return idx


def _parse_step(parts: list[str]) -> dict | None:
    """Parse step type + args from a list of tokens. Returns step dict or None."""
    if not parts:
        print("  Missing step type (key / mouse / delay)")
        return None

    t = parts[0].lower()

    if t == "key":
        if len(parts) < 3:
            print("  Usage: key <key> <secs>")
            return None
        dur = _parse_positive(parts[2], "duration")
        if dur is None:
            return None
        return {"type": "key", "key": parts[1].lower(), "duration": dur}

    if t == "mouse":
        if len(parts) < 3:
            print("  Usage: mouse <dx> <dy>")
            return None
        dx = _parse_int(parts[1], "dx")
        dy = _parse_int(parts[2], "dy")
        if dx is None or dy is None:
            return None
        return {"type": "mouse", "dx": dx, "dy": dy}

    if t == "delay":
        if len(parts) < 2:
            print("  Usage: delay <secs>")
            return None
        secs = _parse_positive(parts[1], "seconds")
        if secs is None:
            return None
        return {"type": "delay", "seconds": secs}

    print(f"  Unknown step type: {t!r} — use key / mouse / delay")
    return None


# ------------------------------------------------------------------
# Main loop
# ------------------------------------------------------------------

def main() -> None:
    seq = load()
    dirty = False

    print(__doc__)
    print(f"Config: {SEQUENCE_PATH}\n")

    while True:
        print("\nCurrent sequence:")
        print_sequence(seq)
        print()

        try:
            raw = input("cmd> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not raw:
            continue

        parts = raw.split()
        cmd = parts[0].lower()

        if cmd == "q":
            if dirty:
                ans = input("  Unsaved changes. Save before quitting? [y/n] ").strip().lower()
                if ans == "y":
                    save(seq)
            break

        elif cmd == "s":
            save(seq)
            dirty = False

        elif cmd == "r":
            seq = load()
            dirty = False
            print("  Reloaded.")

        elif cmd == "p":
            pass  # printed at top of loop

        elif cmd == "t":
            run_sequence(seq)

        elif cmd == "a":
            step = _parse_step(parts[1:])
            if step:
                seq.append(step)
                dirty = True

        elif cmd == "i":
            if len(parts) < 3:
                print("  Usage: i <idx> <step-type> ...")
                continue
            if not seq:
                idx = 0
            else:
                idx = _parse_index(parts[1], seq)
                if idx is None:
                    continue
            step = _parse_step(parts[2:])
            if step:
                seq.insert(idx, step)
                dirty = True

        elif cmd == "e":
            if len(parts) < 3:
                print("  Usage: e <idx> <step-type> ...")
                continue
            idx = _parse_index(parts[1], seq)
            if idx is None:
                continue
            step = _parse_step(parts[2:])
            if step:
                seq[idx] = step
                dirty = True

        elif cmd == "d":
            if len(parts) != 2:
                print("  Usage: d <idx>")
                continue
            idx = _parse_index(parts[1], seq)
            if idx is not None:
                removed = seq.pop(idx)
                print(f"  Removed [{idx}] {fmt_step(removed)}")
                dirty = True

        elif cmd == "u":
            if len(parts) != 2:
                print("  Usage: u <idx>")
                continue
            idx = _parse_index(parts[1], seq)
            if idx is not None:
                if idx == 0:
                    print("  Already at top.")
                else:
                    seq[idx - 1], seq[idx] = seq[idx], seq[idx - 1]
                    dirty = True

        elif cmd == "x":
            if len(parts) != 2:
                print("  Usage: x <idx>")
                continue
            idx = _parse_index(parts[1], seq)
            if idx is not None:
                if idx == len(seq) - 1:
                    print("  Already at bottom.")
                else:
                    seq[idx], seq[idx + 1] = seq[idx + 1], seq[idx]
                    dirty = True

        else:
            print(f"  Unknown command: {cmd!r} — type 'q' to quit")

    print("Bye.")


if __name__ == "__main__":
    main()
