"""
Visual design styles and QSS stylesheet for NASS.
Unified modern design: Deep navy blue with vibrant logo-derived accents and full RTL/LTR support.
"""

from __future__ import annotations

# ==========================================
# Official NASS Brand Color Palette & Tokens
# (Extracted from assets/images/logo_NASS.png)
# ==========================================

# Sidebar & Brand Anchors
COLOR_SIDEBAR_BG = "#0A1931"       # Deep Brand Navy from Logo core
COLOR_SIDEBAR_HOVER = "#15284F"    # Elevated Navy for hover states
COLOR_SIDEBAR_ACTIVE = "#1E3A8A"   # Active/selected sidebar item background
COLOR_SIDEBAR_TEXT = "#E2E8F0"     # High-contrast slate text
COLOR_SIDEBAR_MUTED = "#94A3B8"    # Subtitle and secondary muted text

# Primary Brand Actions & Focus
COLOR_PRIMARY = "#2563EB"          # Vibrant logo blue for primary actions
COLOR_PRIMARY_HOVER = "#1D4ED8"    # Darker blue on hover
COLOR_PRIMARY_ACTIVE = "#1E40AF"   # Deep navy blue on press

# Accents & Highlights
COLOR_ACCENT = "#4F46E5"           # Indigo accent for active borders and badges
COLOR_ACCENT_LIGHT = "#EEF2FF"     # Soft indigo wash for selection highlights

# Backgrounds & Cards
COLOR_BG = "#F8FAFC"               # Comfortable slate-white page background
COLOR_CARD = "#FFFFFF"             # Crisp pure white cards
COLOR_SURFACE_ELEVATED = "#F1F5F9" # Drop zone and elevated card surface
COLOR_BORDER = "#E2E8F0"           # Light subtle border
COLOR_BORDER_FOCUS = "#2563EB"     # Focused input outline

# Typography
COLOR_TEXT = "#0F172A"             # Dark navy primary text (AAA contrast)
COLOR_TEXT_MUTED = "#475569"       # Secondary slate text (AA contrast)

# Status & Feedback
COLOR_SUCCESS = "#059669"          # Emerald green for success
COLOR_SUCCESS_BG = "#ECFDF5"       # Soft green tint
COLOR_WARNING = "#D97706"          # Amber for warnings
COLOR_WARNING_BG = "#FFFBEB"       # Soft amber tint
COLOR_ERROR = "#DC2626"            # Red for errors
COLOR_ERROR_BG = "#FEF2F2"         # Soft red tint


def get_stylesheet(is_rtl: bool = True) -> str:
    """
    Generates application stylesheet tailored for RTL (Arabic) or LTR (English) layout.
    """
    sidebar_border = (
        "border-left: 1px solid #15284F; border-right: none;"
        if is_rtl else
        "border-right: 1px solid #15284F; border-left: none;"
    )
    btn_active_border = (
        f"border-right: 4px solid {COLOR_ACCENT}; border-left: none;"
        if is_rtl else
        f"border-left: 4px solid {COLOR_ACCENT}; border-right: none;"
    )

    from nass.core.config import ASSETS_DIR
    chk_checked_path = (ASSETS_DIR / "icons" / "checkbox_checked.png").resolve().as_posix()
    chk_hover_path = (ASSETS_DIR / "icons" / "checkbox_checked_hover.png").resolve().as_posix()
    chk_disabled_path = (ASSETS_DIR / "icons" / "checkbox_checked_disabled.png").resolve().as_posix()

    return f"""
/* Checkboxes & Radio Buttons */
QCheckBox {{
    color: {COLOR_TEXT};
    spacing: 9px;
    font-size: 13px;
    font-weight: 500;
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 5px;
    border: 1.8px solid #94A3B8;
    background-color: #FFFFFF;
}}

QCheckBox::indicator:hover {{
    border-color: {COLOR_PRIMARY};
    background-color: #EFF6FF;
}}

QCheckBox::indicator:checked {{
    border: none;
    background-color: transparent;
    image: url("{chk_checked_path}");
}}

QCheckBox::indicator:checked:hover {{
    border: none;
    background-color: transparent;
    image: url("{chk_hover_path}");
}}

QCheckBox::indicator:disabled {{
    border-color: #CBD5E1;
    background-color: #F1F5F9;
}}

QCheckBox::indicator:checked:disabled {{
    border: none;
    background-color: transparent;
    image: url("{chk_disabled_path}");
}}

/* Sidebar status card */
QFrame#sidebarStatusCard {{
    background-color: rgba(21, 40, 79, 0.75);
    border: 1px solid rgba(79, 70, 229, 0.35);
    border-radius: 8px;
    padding: 8px 10px;
}}

QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
    font-family: "IBM Plex Sans Arabic", "Tajawal", "Segoe UI", "Tahoma", "Cairo", sans-serif;
    font-size: 13px;
}}

/* Ensure all labels have transparent background to prevent color patch artifacts */
QLabel {{
    background-color: transparent;
}}

QMainWindow {{
    background-color: {COLOR_BG};
}}

/* Sidebar container */
QFrame#sidebarFrame {{
    background-color: {COLOR_SIDEBAR_BG};
    {sidebar_border}
    padding: 0px;
}}

QWidget#sidebarHeaderContainer {{
    background-color: transparent;
}}

QLabel#sidebarLogoTitle {{
    color: #FFFFFF;
    font-size: 18px;
    font-weight: bold;
    background: transparent;
}}

QLabel#sidebarLogoSub {{
    color: {COLOR_SIDEBAR_MUTED};
    font-size: 11px;
    background: transparent;
}}

QPushButton#sidebarButton {{
    background-color: transparent;
    color: {COLOR_SIDEBAR_TEXT};
    border: none;
    border-radius: 0px;
    padding: 0px;
    margin: 1px 0px;
    width: 100%;
}}

QPushButton#sidebarButton:hover {{
    background-color: {COLOR_SIDEBAR_HOVER};
    color: #FFFFFF;
}}

QPushButton#sidebarButton:checked {{
    background-color: {COLOR_SIDEBAR_ACTIVE};
    color: #FFFFFF;
    font-weight: bold;
    {btn_active_border}
}}

/* Card containers */
QFrame#cardFrame {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    padding: 12px 14px;
}}

QFrame#statCard {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 10px 12px;
}}

/* Drag & Drop Zone */
QFrame#dropZone {{
    background-color: {COLOR_CARD};
    border: 2px dashed #CBD5E1;
    border-radius: 12px;
    padding: 20px 24px;
}}

QFrame#dropZone:hover, QFrame#dropZone[dragOver="true"] {{
    border-color: {COLOR_PRIMARY};
    background-color: #EFF6FF;
}}

/* Buttons */
QPushButton {{
    background-color: #FFFFFF;
    color: {COLOR_TEXT};
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: #F8FAFC;
    border-color: #94A3B8;
}}

QPushButton#primaryButton {{
    background-color: {COLOR_PRIMARY};
    color: #FFFFFF;
    border: 1px solid {COLOR_PRIMARY};
    font-weight: bold;
}}

QPushButton#primaryButton:hover {{
    background-color: {COLOR_PRIMARY_HOVER};
    border-color: {COLOR_PRIMARY_HOVER};
}}

QPushButton#primaryButton:pressed {{
    background-color: {COLOR_PRIMARY_ACTIVE};
    border-color: {COLOR_PRIMARY_ACTIVE};
}}

QPushButton#primaryButton:disabled {{
    background-color: #94A3B8;
    border-color: #94A3B8;
    color: #F1F5F9;
}}

QPushButton#dangerButton {{
    background-color: {COLOR_ERROR};
    color: #FFFFFF;
    border: 1px solid {COLOR_ERROR};
    font-weight: 500;
}}

QPushButton#dangerButton:hover {{
    background-color: #B91C1C;
    border-color: #991B1B;
}}

QPushButton#dangerButton:disabled {{
    background-color: #FCA5A5;
    border-color: #FCA5A5;
    color: #FFFFFF;
}}

/* Inputs & Combo */
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {{
    background-color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    color: {COLOR_TEXT};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border-color: {COLOR_BORDER_FOCUS};
}}

QComboBox::drop-down {{
    border: none;
    padding-left: 6px;
    padding-right: 6px;
}}

/* Progress Bar */
QProgressBar {{
    background-color: #E2E8F0;
    border-radius: 4px;
    text-align: center;
    color: {COLOR_TEXT};
    font-size: 11px;
    font-weight: bold;
    height: 12px;
}}

QProgressBar::chunk {{
    background-color: {COLOR_PRIMARY};
    border-radius: 4px;
}}

/* Table Widget */
QTableWidget {{
    background-color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    gridline-color: #F1F5F9;
}}

QHeaderView::section {{
    background-color: #F8FAFC;
    color: #475569;
    padding: 8px;
    border: none;
    border-bottom: 1px solid {COLOR_BORDER};
    font-weight: bold;
    font-size: 12px;
}}

QTableWidget::item {{
    padding: 6px;
}}

QTableWidget::item:selected {{
    background-color: {COLOR_ACCENT_LIGHT};
    color: {COLOR_PRIMARY};
}}

/* ScrollBars */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: #CBD5E1;
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: #94A3B8;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    background: {COLOR_CARD};
    border-radius: 8px;
}}

QTabBar::tab {{
    background: #E2E8F0;
    color: #475569;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background: {COLOR_PRIMARY};
    color: #FFFFFF;
    font-weight: bold;
}}
"""


# Default stylesheet (RTL)
APP_STYLESHEET = get_stylesheet(is_rtl=True)
