"""Editorial dark-glass stylesheet builder.

Single source of QSS for the macro_gui PySide6 shell. The output is a
flat f-string template — no fragmented blocks — so the cascade is easy
to scan top-to-bottom.

Gradient discipline: only two linear-gradient selectors are permitted —
the shell backdrop and the hero card surface. All other surfaces are
flat translucent token fills. See ``pyside6-patterns §5``.
"""

from __future__ import annotations


def build_qss(tok: dict, rad: dict, spc: dict) -> str:
    """Render the full stylesheet for the active theme.

    Args:
        tok: Token dict from ``theme.tokens()``.
        rad: Radius scale from ``theme.radii()``.
        spc: Spacing scale from ``theme.spacing()`` (unused today; kept
            for signature stability so callers and hot-reload paths
            don't need to change).

    Returns:
        A fully-rendered QSS string suitable for
        ``QApplication.setStyleSheet``.
    """
    _ = spc

    return f"""
    /* ── shell backdrop (gradient 1/2) ────────────────────────────── */
    #Shell {{
        background: qlineargradient(
            x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 {tok['backdrop_top']},
            stop: 1 {tok['backdrop_bot']}
        );
        border-radius: {rad['xl']}px;
        border: 1px solid {tok['border_hairline']};
    }}

    #AccentGlow {{
        background: {tok['accent_glow']};
        border-radius: 240px;
    }}

    /* ── top bar ─────────────────────────────────────────────────── */
    #TopBar {{
        background: transparent;
        border-bottom: 1px solid {tok['border_hairline']};
    }}
    #Brand {{
        color: {tok['text']};
        font-family: {tok['font_display']};
        font-size: 18px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }}
    #BrandDot {{
        color: {tok['accent']};
        font-size: 20px;
        padding-right: 4px;
    }}
    #BrandTagline {{
        color: {tok['text_dim']};
        font-family: {tok['font_family']};
        font-size: 10px;
        letter-spacing: 2px;
        text-transform: uppercase;
    }}

    /* ── pills ───────────────────────────────────────────────────── */
    #PillVersion, #PillHotkey, #PillStatus {{
        background: {tok['glass_2']};
        border: 1px solid {tok['border_hairline']};
        border-top: 1px solid {tok['border_highlight']};
        border-radius: 999px;
        color: {tok['text_mid']};
        font-family: {tok['font_mono']};
        font-size: 10px;
        letter-spacing: 0.5px;
        padding: 4px 10px;
        min-height: 18px;
    }}
    #PillHotkey {{ color: {tok['text']}; }}
    #PillStatus {{ color: {tok['text_dim']}; }}

    /* ── window controls ─────────────────────────────────────────── */
    #BtnMin, #BtnClose {{
        background: transparent;
        color: {tok['text_dim']};
        border: none;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 500;
        padding: 0;
    }}
    #BtnMin:hover {{
        background: {tok['glass_2']};
        color: {tok['text']};
    }}
    #BtnClose:hover {{
        background: rgba(255, 90, 110, 0.20);
        color: {tok['err']};
    }}

    /* ── nav rail ────────────────────────────────────────────────── */
    #NavRail {{
        background: transparent;
        border-right: 1px solid {tok['border_hairline']};
    }}
    #NavBtn {{
        background: transparent;
        border: none;
        border-radius: 0;
    }}
    #NavBtn:hover {{ background: {tok['glass_1']}; }}
    #NavBtn[active="true"] {{
        background: {tok['glass_2']};
    }}
    #NavIndicator {{
        background: {tok['accent']};
        border-top-right-radius: 2px;
        border-bottom-right-radius: 2px;
    }}
    #NavIcon {{
        color: {tok['text_dim']};
        background: transparent;
        font-size: 18px;
        font-family: {tok['font_family']};
    }}
    #NavBtn[active="true"] #NavIcon {{ color: {tok['accent']}; }}
    #NavDot {{
        background: transparent;
        color: transparent;
        font-size: 6px;
    }}
    #NavBtn[active="true"] #NavDot {{ color: {tok['accent']}; }}

    /* ── pages & scroll containers ───────────────────────────────── */
    #PageWrapper {{ background: transparent; }}
    QScrollArea {{ background: transparent; border: none; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}

    /* ── hero card (gradient 2/2) ────────────────────────────────── */
    #HeroCard {{
        background: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 1,
            stop: 0 {tok['hero_top']},
            stop: 1 {tok['hero_bot']}
        );
        border: 1px solid {tok['border_hairline']};
        border-top: 1px solid {tok['border_highlight']};
        border-radius: {rad['xl']}px;
    }}
    #HeroEyebrow {{
        color: {tok['accent']};
        font-family: {tok['font_mono']};
        font-size: 10px;
        letter-spacing: 3px;
        text-transform: uppercase;
        background: transparent;
    }}
    #HeroTitle {{
        color: {tok['text']};
        font-family: {tok['font_display']};
        font-size: 48px;
        font-weight: 500;
        letter-spacing: -1.5px;
        background: transparent;
    }}
    #HeroSub {{
        color: {tok['text_mid']};
        font-family: {tok['font_family']};
        font-size: 13px;
        letter-spacing: 0.2px;
        background: transparent;
    }}
    #HeroMeta {{
        color: {tok['text_dim']};
        font-family: {tok['font_mono']};
        font-size: 11px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        background: transparent;
    }}

    /* ── embed surface (Roblox snaps over this rectangle) ────────── */
    #EmbedSurface {{
        background: {tok['glass_1']};
        border: 1px solid {tok['border_hairline']};
        border-top: 1px solid {tok['border_highlight']};
        border-radius: {rad['lg']}px;
    }}
    #EmbedPlaceholder {{
        background: transparent;
        color: {tok['text_dim']};
        font-family: {tok['font_mono']};
        font-size: 11px;
        letter-spacing: 1.5px;
        padding: 80px 20px;
    }}

    /* ── glass cards & stat blocks ───────────────────────────────── */
    #GlassCard, #StatBlock {{
        background: {tok['glass_1']};
        border: 1px solid {tok['border_hairline']};
        border-top: 1px solid {tok['border_highlight']};
        border-radius: {rad['lg']}px;
    }}
    #StatValue {{
        color: {tok['text']};
        font-family: {tok['font_mono']};
        font-size: 30px;
        font-weight: 500;
        letter-spacing: -0.5px;
        background: transparent;
    }}
    #StatLabel {{
        color: {tok['text_dim']};
        font-family: {tok['font_family']};
        font-size: 10px;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        background: transparent;
    }}
    #StatAccent {{
        color: {tok['accent']};
        font-family: {tok['font_mono']};
        font-size: 30px;
        font-weight: 500;
        background: transparent;
    }}
    #PhaseText {{
        color: {tok['text']};
        font-family: {tok['font_mono']};
        font-size: 13px;
        letter-spacing: 0.5px;
        background: transparent;
    }}

    /* ── section headers ─────────────────────────────────────────── */
    #SectionEyebrow {{
        color: {tok['accent']};
        font-family: {tok['font_mono']};
        font-size: 10px;
        letter-spacing: 3px;
        text-transform: uppercase;
        background: transparent;
    }}
    #SectionTitle {{
        color: {tok['text']};
        font-family: {tok['font_display']};
        font-size: 28px;
        font-weight: 500;
        letter-spacing: -0.8px;
        background: transparent;
    }}
    #SectionSub {{
        color: {tok['text_mid']};
        font-family: {tok['font_family']};
        font-size: 12px;
        background: transparent;
    }}
    #Divider {{ background: {tok['border_hairline']}; }}

    /* ── fields ──────────────────────────────────────────────────── */
    #FieldShell {{ background: transparent; }}
    #FieldEyebrow {{
        color: {tok['text_dim']};
        font-family: {tok['font_mono']};
        font-size: 9px;
        letter-spacing: 2px;
        text-transform: uppercase;
        background: transparent;
    }}
    #FieldHelp {{
        color: {tok['text_faint']};
        font-family: {tok['font_family']};
        font-size: 10px;
        font-style: italic;
        background: transparent;
    }}
    #FieldLabel {{
        color: {tok['text']};
        font-family: {tok['font_family']};
        font-size: 13px;
        background: transparent;
    }}
    QLineEdit, QSpinBox, QComboBox {{
        background: {tok['glass_input']};
        border: 1px solid {tok['border_hairline']};
        border-top: 1px solid {tok['border_highlight']};
        border-radius: {rad['sm']}px;
        color: {tok['text']};
        font-family: {tok['font_family']};
        font-size: 12px;
        padding: 8px 10px;
        selection-background-color: {tok['accent_soft']};
        selection-color: {tok['text']};
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border: 1px solid {tok['accent']};
    }}
    QComboBox::drop-down {{ border: none; width: 18px; }}
    QComboBox QAbstractItemView {{
        background: {tok['backdrop_bot']};
        border: 1px solid {tok['border_hairline']};
        color: {tok['text']};
        selection-background-color: {tok['accent_soft']};
        outline: none;
        padding: 4px;
    }}
    QCheckBox {{
        color: {tok['text']};
        font-family: {tok['font_family']};
        font-size: 12px;
        spacing: 8px;
        background: transparent;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {tok['border_strong']};
        border-radius: 4px;
        background: {tok['glass_input']};
    }}
    QCheckBox::indicator:checked {{
        background: {tok['accent']};
        border: 1px solid {tok['accent']};
    }}

    /* ── buttons ─────────────────────────────────────────────────── */
    #BtnPrimary {{
        background: {tok['accent']};
        border: 1px solid {tok['accent']};
        border-radius: {rad['sm']}px;
        color: #0a0d18;
        font-family: {tok['font_family']};
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
        padding: 10px 22px;
        text-transform: uppercase;
    }}
    #BtnPrimary:hover  {{ background: {tok['accent_hover']}; border: 1px solid {tok['accent_hover']}; }}
    #BtnPrimary:disabled {{
        background: {tok['glass_2']};
        color: {tok['text_faint']};
        border: 1px solid {tok['border_hairline']};
    }}
    #BtnDanger {{
        background: transparent;
        border: 1px solid {tok['err']};
        border-radius: {rad['sm']}px;
        color: {tok['err']};
        font-family: {tok['font_family']};
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
        padding: 10px 22px;
        text-transform: uppercase;
    }}
    #BtnDanger:hover {{ background: rgba(255, 122, 138, 0.12); }}
    #BtnNeutral, #BtnGhost {{
        background: {tok['glass_2']};
        border: 1px solid {tok['border_hairline']};
        border-top: 1px solid {tok['border_highlight']};
        border-radius: {rad['sm']}px;
        color: {tok['text']};
        font-family: {tok['font_family']};
        font-size: 12px;
        font-weight: 500;
        letter-spacing: 0.4px;
        padding: 10px 18px;
    }}
    #BtnGhost {{ background: transparent; }}
    #BtnNeutral:hover, #BtnGhost:hover {{
        background: {tok['glass_1']};
        border: 1px solid {tok['border_strong']};
    }}

    /* ── console drawer ──────────────────────────────────────────── */
    #ConsoleDrawer {{
        background: {tok['glass_1']};
        border-top: 1px solid {tok['border_hairline']};
    }}
    #ConsoleHandle {{
        background: transparent;
        border: none;
        border-top: 1px solid {tok['border_hairline']};
    }}
    #ConsoleHandle:hover {{ background: {tok['glass_1']}; }}
    #ConsoleGrip {{
        background: {tok['border_strong']};
        border-radius: 2px;
    }}
    #ConsoleLabel {{
        color: {tok['text_dim']};
        font-family: {tok['font_mono']};
        font-size: 9px;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        background: transparent;
    }}
    #ConsoleCount {{
        color: {tok['accent']};
        font-family: {tok['font_mono']};
        font-size: 9px;
        letter-spacing: 1px;
        background: transparent;
    }}
    #ConsoleToggle {{
        background: transparent;
        border: none;
        color: {tok['text_dim']};
        font-size: 11px;
        padding: 0 8px;
    }}
    #ConsoleToggle:hover {{ color: {tok['text']}; }}
    #LogView {{
        background: transparent;
        border: none;
        color: {tok['text_mid']};
        font-family: {tok['font_mono']};
        font-size: 10px;
        padding: 4px 14px;
        selection-background-color: {tok['accent_soft']};
        selection-color: {tok['text']};
    }}

    /* ── scrollbars ──────────────────────────────────────────────── */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 4px 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {tok['border_strong']};
        border-radius: 4px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {tok['text_faint']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        background: transparent; border: none; height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 2px 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {tok['border_strong']};
        border-radius: 4px;
        min-width: 24px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        background: transparent; border: none; width: 0;
    }}

    /* ── command palette ─────────────────────────────────────────── */
    #PaletteCard {{
        background: {tok['backdrop_bot']};
        border: 1px solid {tok['border_highlight']};
        border-radius: {rad['lg']}px;
    }}
    #PaletteHint {{
        color: {tok['text_dim']};
        font-family: {tok['font_mono']};
        font-size: 9px;
        letter-spacing: 2px;
        text-transform: uppercase;
        background: transparent;
        padding: 2px 6px;
    }}
    #PaletteInput {{
        background: {tok['glass_input']};
        border: 1px solid {tok['border_hairline']};
        border-top: 1px solid {tok['border_highlight']};
        border-radius: {rad['sm']}px;
        color: {tok['text']};
        font-family: {tok['font_family']};
        font-size: 14px;
        padding: 12px 14px;
        selection-background-color: {tok['accent_soft']};
    }}
    #PaletteInput:focus {{ border: 1px solid {tok['accent']}; }}
    #PaletteList {{
        background: transparent;
        border: none;
        color: {tok['text']};
        font-family: {tok['font_family']};
        font-size: 12px;
        outline: none;
    }}
    #PaletteList::item {{
        background: transparent;
        border-radius: {rad['sm']}px;
        padding: 8px 10px;
        margin: 1px 0;
    }}
    #PaletteList::item:hover {{ background: {tok['glass_1']}; }}
    #PaletteList::item:selected {{
        background: {tok['accent_soft']};
        color: {tok['text']};
    }}

    QToolTip {{
        background: {tok['backdrop_bot']};
        border: 1px solid {tok['border_hairline']};
        color: {tok['text']};
        font-family: {tok['font_family']};
        font-size: 11px;
        padding: 6px 10px;
    }}
    """
