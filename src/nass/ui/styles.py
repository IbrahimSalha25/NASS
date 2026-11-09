"""
Visual design styles and QSS stylesheet for NASS.
Unified modern design: Deep navy blue with calm purple accents and full RTL/LTR support.
"""

from __future__ import annotations

COLOR_SIDEBAR_BG = "#0F172A"       # Deep night navy slate for sidebar
COLOR_SIDEBAR_HOVER = "#1E293B"    # Hover effect for sidebar items
COLOR_SIDEBAR_ACTIVE = "#1E3A8A"   # Active/selected sidebar item
COLOR_SIDEBAR_TEXT = "#E2E8F0"     # High readability text
COLOR_SIDEBAR_MUTED = "#94A3B8"

COLOR_PRIMARY = "#1E40AF"          # Primary royal navy blue
COLOR_PRIMARY_HOVER = "#1D4ED8"
COLOR_PRIMARY_ACTIVE = "#172554"

COLOR_ACCENT = "#7C3AED"           # Soft purple accent
COLOR_ACCENT_LIGHT = "#EDE9FE"

COLOR_BG = "#F8FAFC"               # Comfortable snow slate page background
COLOR_CARD = "#FFFFFF"             # Crisp pure white cards
COLOR_BORDER = "#E2E8F0"           # Light subtle border
COLOR_BORDER_FOCUS = "#2563EB"

COLOR_TEXT = "#0F172A"             # Dark navy text
COLOR_TEXT_MUTED = "#64748B"       # Secondary muted gray text

COLOR_SUCCESS = "#10B981"
COLOR_SUCCESS_BG = "#ECFDF5"
COLOR_WARNING = "#F59E0B"
COLOR_WARNING_BG = "#FFFBEB"
COLOR_ERROR = "#EF4444"
COLOR_ERROR_BG = "#FEF2F2"


def get_stylesheet(is_rtl: bool = True) -> str:
    """
    Generates application stylesheet tailored for RTL (Arabic) or LTR (English) layout.
    """
    sidebar_border = (
        "border-left: 1px solid #1E293B; border-right: none;"
        if is_rtl else
        "border-right: 1px solid #1E293B; border-left: none;"
    )
    btn_align = "text-align: right;" if is_rtl else "text-align: left;"
    btn_active_border = (
        f"border-right: 4px solid {COLOR_ACCENT}; border-left: none;"
        if is_rtl else
        f"border-left: 4px solid {COLOR_ACCENT}; border-right: none;"
    )

    return f"""
/* Universal widget settings with Arabic font cascade */
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
    border: 1px solid {COLOR_BORDER};
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
    border: none;
    font-weight: bold;
}}

QPushButton#primaryButton:hover {{
    background-color: {COLOR_PRIMARY_HOVER};
}}

QPushButton#primaryButton:pressed {{
    background-color: {COLOR_PRIMARY_ACTIVE};
}}

QPushButton#dangerButton {{
    background-color: #EF4444;
    color: #FFFFFF;
    border: none;
}}

QPushButton#dangerButton:hover {{
    background-color: #DC2626;
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
    border-color: {COLOR_PRIMARY};
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
    background-color: #EFF6FF;
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
