from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_THEMES_DIR = Path(__file__).parent / "themes"
_current: dict = {}


def load(name: str = "default") -> None:
    """Load theme by name from themes/*.json. Call on startup or theme swap."""
    global _current
    path = _THEMES_DIR / f"{name}.json"
    with path.open() as f:
        data = json.load(f)
    _current = data


def tokens() -> dict[str, str]:
    """Return the flat token dict for the active theme."""
    return _current.get("tokens", {})


def radii() -> dict[str, int]:
    """Return border-radius scale for the active theme."""
    return _current.get("radii", {"xl": 16, "lg": 14, "md": 12, "sm": 10, "xs": 8})


def spacing() -> dict[str, int]:
    """Return spacing scale for the active theme."""
    return _current.get("spacing", {"xl": 20, "lg": 16, "md": 12, "sm": 8, "xs": 4})


def reduce_motion() -> bool:
    """Return True if the active theme requests reduced motion."""
    return bool(_current.get("reduce_motion", False))


def name() -> str:
    """Return the name of the active theme."""
    return _current.get("name", "default")


def available_themes() -> list[str]:
    """Return stem names of all theme JSON files found in the themes directory."""
    return [p.stem for p in _THEMES_DIR.glob("*.json")]


def __getattr__(attr: str) -> Any:
    """Resolve token or radius key as a module attribute.

    Lookup is case-insensitive so legacy callers using uppercase
    constants (``theme.ACCENT``) keep working alongside the lowercase
    token keys actually stored in the JSON.
    """
    key = attr.lower()
    t = tokens()
    if key in t:
        return t[key]
    if attr in t:
        return t[attr]
    r = radii()
    if key in r:
        return r[key]
    if attr in r:
        return r[attr]
    raise AttributeError(attr)


# Pre-load default theme on import
load("default")
