from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Literal


@dataclass(frozen=True)
class HotkeySpec:
    key: str
    label: str
    action_id: str


@dataclass(frozen=True)
class ActionSpec:
    id: str
    label: str
    style: Literal["primary", "danger", "neutral", "ghost"]
    callback: Callable[[], None]


@dataclass(frozen=True)
class FieldSpec:
    id: str
    label: str
    kind: Literal["text", "int", "bool", "password", "choice"]
    default: Any
    help: str | None = None
    on_change: Callable[[Any], None] | None = None
    choices: tuple[str, ...] = ()


@dataclass(frozen=True)
class StatSpec:
    id: str
    label: str
    getter: Callable[[], str]


@dataclass(frozen=True)
class CardSpec:
    title: str
    subtitle: str
    image_url: str
    border_color: str
    on_click: Callable[[], None] | None = None


@dataclass(frozen=True)
class PageSpec:
    id: str
    label: str
    icon_name: str
    builder: Callable[..., None]


@dataclass
class MacroSpec:
    title: str
    version: str
    accent: str
    pages: tuple[PageSpec, ...]
    hotkeys: tuple[HotkeySpec, ...]
    actions: dict[str, ActionSpec]
    fields: tuple[FieldSpec, ...]
    stats: tuple[StatSpec, ...]
    log_queue: Any | None = None
    on_start: Callable[[], None] | None = None
    on_stop: Callable[[], None] | None = None
    on_close: Callable[[], None] | None = None
    status_getter: Callable[[], tuple[str, str]] | None = None
