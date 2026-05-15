from __future__ import annotations


def build_qss(tok: dict, rad: dict, spc: dict) -> str:
    """Build and return a complete QSS stylesheet string from theme dicts.

    Args:
        tok: Token dict from theme.tokens().
        rad: Radii dict from theme.radii().
        spc: Spacing dict from theme.spacing().

    Returns:
        A QSS string suitable for QApplication.setStyleSheet().
    """
    return f"""
/* ── Base ─────────────────────────────────────────────────────────── */
QWidget {{
    background: {tok['bg']};
    color: {tok['text']};
    font-family: {tok['font_family']};
    font-size: 10px;
}}

/* ── Shell ────────────────────────────────────────────────────────── */
#Shell {{
    background: {tok['bg']};
    border-radius: {rad['xl']}px;
}}

/* ── Top bar ──────────────────────────────────────────────────────── */
#TopBar {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {tok['card_top']},
        stop:1 {tok['card_bot']}
    );
    border-bottom: 1px solid {tok['border_hi']};
}}

#TopTitle {{
    color: {tok['text']};
    font-weight: bold;
    font-size: 13px;
}}

/* ── Sidebar ──────────────────────────────────────────────────────── */
#Sidebar {{
    background: {tok['surface']};
    border-right: 1px solid {tok['border']};
    border-top-right-radius: {rad['lg']}px;
    border-bottom-right-radius: {rad['lg']}px;
}}

#NavBtn {{
    background: transparent;
    border: none;
    border-left: 4px solid transparent;
    border-radius: {rad['xs']}px;
}}

#NavBtn:hover {{
    background: {tok['surface_2']};
}}

#NavBtn[active="true"] {{
    background: {tok['accent_soft']};
    border-left-color: {tok['accent']};
}}

#NavBtn[active="true"] #NavIcon,
#NavBtn[active="true"] #NavLabel {{
    color: {tok['accent']};
}}

#NavLabel {{
    color: {tok['text_dim']};
    font-size: 9px;
    background: transparent;
}}

#NavIcon {{
    color: {tok['text_dim']};
    font-size: 16px;
    background: transparent;
}}

/* ── Pills ────────────────────────────────────────────────────────── */
#PillVersion {{
    background: {tok['surface_2']};
    border: 1px solid {tok['border_hi']};
    border-radius: {rad['xs']}px;
    padding: 2px 8px;
    color: {tok['text_mid']};
    font-size: 10px;
}}

#PillHotkey {{
    background: {tok['surface']};
    border: 1px solid {tok['border']};
    border-radius: {rad['xs']}px;
    padding: 2px 7px;
    color: {tok['text_dim']};
    font-size: 10px;
}}

#PillStatus {{
    background: {tok['surface']};
    border: 1px solid {tok['border']};
    border-radius: {rad['xs']}px;
    padding: 2px 8px;
    color: {tok['text_mid']};
    font-size: 10px;
}}

/* ── Window chrome buttons ────────────────────────────────────────── */
#BtnClose {{
    background: transparent;
    border: none;
    border-radius: {rad['xs']}px;
}}
#BtnClose:hover {{
    background: rgba(239,68,68,0.20);
}}

#BtnMin {{
    background: transparent;
    border: none;
    border-radius: {rad['xs']}px;
}}
#BtnMin:hover {{
    background: {tok['surface_2']};
}}

#BtnDock {{
    background: transparent;
    border: none;
    border-radius: {rad['xs']}px;
}}
#BtnDock:hover {{
    background: {tok['surface_2']};
}}

/* ── Content areas ────────────────────────────────────────────────── */
#Content {{
    background: {tok['bg']};
}}

#PageWrapper {{
    background: {tok['bg']};
}}

/* ── Action buttons ───────────────────────────────────────────────── */
#BtnPrimary {{
    background: {tok['accent']};
    color: #ffffff;
    border: none;
    border-radius: {rad['sm']}px;
    padding: 8px 18px;
    font-weight: bold;
    font-size: 10px;
}}
#BtnPrimary:hover {{
    background: {tok['accent_hover']};
}}

#BtnDanger {{
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.30);
    color: {tok['err']};
    border-radius: {rad['sm']}px;
    padding: 8px 18px;
    font-size: 10px;
}}
#BtnDanger:hover {{
    background: rgba(239,68,68,0.22);
}}

#BtnNeutral {{
    background: {tok['surface_2']};
    border: 1px solid {tok['border_hi']};
    color: {tok['text']};
    border-radius: {rad['sm']}px;
    padding: 8px 18px;
    font-size: 10px;
}}
#BtnNeutral:hover {{
    background: {tok['border_hi']};
}}

#BtnGhost {{
    background: transparent;
    border: 1px solid {tok['border']};
    color: {tok['text_mid']};
    border-radius: {rad['sm']}px;
    padding: 8px 18px;
    font-size: 10px;
}}
#BtnGhost:hover {{
    background: {tok['surface']};
}}

/* ── Stat blocks ──────────────────────────────────────────────────── */
#StatBlock {{
    background: {tok['surface']};
    border: 1px solid {tok['border']};
    border-radius: {rad['md']}px;
    padding: 12px 16px;
}}

#StatValue {{
    color: {tok['text']};
    font-weight: bold;
    font-size: 22px;
}}

#StatLabel {{
    color: {tok['text_dim']};
    font-size: 9px;
}}

/* ── Cards ────────────────────────────────────────────────────────── */
#HeroCard {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {tok['card_top']},
        stop:1 {tok['surface']}
    );
    border: 1px solid {tok['accent_soft']};
    border-radius: {rad['md']}px;
    padding: 16px;
}}

#Card {{
    background: {tok['surface']};
    border: 1px solid {tok['border']};
    border-radius: {rad['md']}px;
}}
#Card:hover {{
    background: {tok['surface_2']};
    border-color: {tok['border_hi']};
}}

/* ── Typography ───────────────────────────────────────────────────── */
#SectionEyebrow {{
    color: {tok['text_dim']};
    font-size: 9px;
    font-weight: bold;
}}

#SectionTitle {{
    color: {tok['text']};
    font-weight: bold;
    font-size: 18px;
}}

#SectionSub {{
    color: {tok['text_mid']};
    font-size: 11px;
}}

#FieldLabel {{
    color: {tok['text_mid']};
    font-size: 10px;
}}

/* ── Form inputs ──────────────────────────────────────────────────── */
QLineEdit,
QSpinBox {{
    background: {tok['surface_2']};
    border: 1px solid {tok['border']};
    border-radius: {rad['xs']}px;
    padding: 5px 8px;
    color: {tok['text']};
    selection-background-color: {tok['accent_soft']};
}}
QLineEdit:focus,
QSpinBox:focus {{
    border-color: {tok['accent']};
}}

QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {tok['border_hi']};
    border-radius: 3px;
    background: {tok['surface_2']};
}}
QCheckBox::indicator:checked {{
    background: {tok['accent']};
    border-color: {tok['accent']};
}}

QComboBox {{
    background: {tok['surface_2']};
    border: 1px solid {tok['border']};
    border-radius: {rad['xs']}px;
    padding: 5px 8px;
    color: {tok['text']};
}}
QComboBox:focus {{
    border-color: {tok['accent']};
}}
QComboBox::drop-down {{
    background: {tok['surface']};
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background: {tok['surface']};
    border: 1px solid {tok['border_hi']};
    color: {tok['text']};
    selection-background-color: {tok['accent_soft']};
}}

/* ── Scrollbars ───────────────────────────────────────────────────── */
QScrollBar:vertical {{
    width: 6px;
    background: transparent;
    border-radius: 3px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {tok['border_hi']};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    height: 6px;
    background: transparent;
    border-radius: 3px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {tok['border_hi']};
    border-radius: 3px;
    min-width: 30px;
}}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: transparent;
}}

/* ── Console ──────────────────────────────────────────────────────── */
#Console {{
    background: {tok['surface']};
    border-left: 1px solid {tok['border']};
    border-radius: 0;
}}

QPlainTextEdit {{
    background: {tok['surface']};
    color: {tok['text_dim']};
    font-family: Consolas, monospace;
    font-size: 10px;
    border: none;
    selection-background-color: {tok['border_hi']};
}}

#ConsoleToggle {{
    background: {tok['surface_2']};
    border: 1px solid {tok['border']};
    border-radius: {rad['xs']}px;
    color: {tok['text_dim']};
    font-size: 9px;
    padding: 2px 6px;
}}
#ConsoleToggle:hover {{
    background: {tok['surface']};
}}

/* ── Phase / status lines ─────────────────────────────────────────── */
#PhaseLine {{
    background: {tok['surface_2']};
    border: 1px solid {tok['border']};
    border-radius: {rad['xs']}px;
    padding: 6px 10px;
}}

#PhaseText {{
    color: {tok['text_mid']};
    font-size: 10px;
    font-style: italic;
}}

/* ── Splitter & dividers ──────────────────────────────────────────── */
QSplitter::handle {{
    background: {tok['border']};
    width: 1px;
}}

#Divider {{
    background: {tok['border']};
    max-height: 1px;
}}

/* ── Toast notifications ──────────────────────────────────────────── */
#ToastWidget {{
    background: {tok['accent_soft']};
    border: 1px solid {tok['accent_soft']};
    border-radius: {rad['sm']}px;
    padding: 10px 16px;
}}

#ToastText {{
    color: {tok['text']};
    font-size: 10px;
}}
"""
