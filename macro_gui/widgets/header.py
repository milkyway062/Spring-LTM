from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from macro_gui import theme


class HeaderBar(ctk.CTkFrame):
    def __init__(self, master, title: str, version: str,
                 hotkeys: list[tuple[str, str]], **kw):
        super().__init__(
            master,
            height=theme.HEADER_H,
            corner_radius=0,
            fg_color=theme.SURFACE,
            **kw,
        )
        self.pack_propagate(False)

        ctk.CTkLabel(
            self, text=title,
            font=theme.FONT_TITLE,
            text_color=theme.TEXT,
        ).pack(side="left", padx=(10, 6))

        Pill(self, version, fg=theme.TEXT_MID, border=theme.BORDER_HI).pack(
            side="left", padx=2)

        for label, _ in hotkeys:
            Pill(self, label, fg=theme.TEXT_DIM, border=theme.BORDER).pack(
                side="left", padx=2)

        self._dot_canvas = tk.Canvas(
            self, width=8, height=8,
            bg=theme.SURFACE, highlightthickness=0,
        )
        self._dot_canvas.pack(side="right", padx=(4, 10))
        self._dot_id = self._dot_canvas.create_oval(1, 1, 7, 7,
                                                     fill=theme.BORDER_HI,
                                                     outline="")

        self._status_lbl = ctk.CTkLabel(
            self, text="idle",
            font=theme.FONT_LABEL,
            text_color=theme.TEXT_DIM,
        )
        self._status_lbl.pack(side="right", padx=(0, 4))

        sep = tk.Frame(self, bg=theme.BORDER, height=1)
        sep.place(relx=0, rely=1.0, anchor="sw", relwidth=1.0)

    def set_status(self, text: str, dot_color: str):
        self._status_lbl.configure(text=text)
        self._dot_canvas.itemconfig(self._dot_id, fill=dot_color)

    def pulse_dot(self, color_a: str, color_b: str, state: bool) -> bool:
        next_state = not state
        self._dot_canvas.itemconfig(
            self._dot_id,
            fill=color_a if next_state else color_b,
        )
        return next_state


class Pill(ctk.CTkFrame):
    def __init__(self, master, text: str, fg: str = None,
                 border: str = None, bg: str = None, **kw):
        _bg = bg or theme.SURFACE_2
        super().__init__(
            master,
            corner_radius=4,
            fg_color=_bg,
            border_width=1,
            border_color=border or theme.BORDER,
            **kw,
        )
        ctk.CTkLabel(
            self, text=text,
            font=theme.FONT_SMALL,
            text_color=fg or theme.TEXT_MID,
        ).pack(padx=5, pady=1)
