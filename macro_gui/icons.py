from __future__ import annotations

import hashlib
import io
import urllib.request
from pathlib import Path

from PIL import Image
from PySide6.QtGui import QImage, QPixmap

_CACHE_DIR = Path(__file__).parent / "_cache"
_CACHE_DIR.mkdir(exist_ok=True)

_PLACEHOLDER_COLOR = (30, 30, 45)

# Unicode glyphs for sidebar nav items (no image required).
NAV_GLYPHS: dict[str, str] = {
    "run": "▶",
    "settings": "⚙",
    "log": "≡",
    "update": "↑",
}


def _placeholder(size: tuple[int, int]) -> QPixmap:
    """Return a solid-colour placeholder QPixmap.

    Args:
        size: (width, height) in pixels.

    Returns:
        QPixmap filled with *_PLACEHOLDER_COLOR*.
    """
    img = Image.new("RGB", size, _PLACEHOLDER_COLOR)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qimg = QImage.fromData(buf.getvalue())
    return QPixmap.fromImage(qimg)


def fetch(url: str, size: tuple[int, int] = (56, 56)) -> QPixmap:
    """Fetch an image from *url*, resize it, cache it, and return a QPixmap.

    Results are cached on disk in *_CACHE_DIR* keyed by a SHA-1 of the URL
    and size so repeated calls are instant.  On any network or decoding
    failure the function returns a placeholder pixmap instead of raising.

    Args:
        url: Remote image URL.
        size: Target (width, height) in pixels.

    Returns:
        QPixmap of the requested size, or a placeholder on failure.
    """
    key = hashlib.sha1(f"{url}{size}".encode()).hexdigest()
    cache_path = _CACHE_DIR / f"{key}.png"

    if cache_path.exists():
        try:
            img = Image.open(cache_path).convert("RGB").resize(size, Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            qimg = QImage.fromData(buf.getvalue())
            return QPixmap.fromImage(qimg)
        except Exception:
            cache_path.unlink(missing_ok=True)

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "MacroGUI-IconFetcher/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        img = Image.open(io.BytesIO(data)).convert("RGB").resize(size, Image.LANCZOS)
        img.save(cache_path)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qimg = QImage.fromData(buf.getvalue())
        return QPixmap.fromImage(qimg)
    except Exception:
        return _placeholder(size)
