"""
Visual design styles and QSS stylesheet for NASS.
Unified modern design: Deep navy blue with calm purple accents and full RTL alignment.
"""

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

APP_STYLESHEET = f"""
/* Universal widget settings with Arabic font cascade */
QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
    font-family: "IBM Plex Sans Arabic", "Tajawal", "Segoe UI", "Tahoma", "Cairo", sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: {COLOR_BG};
}}

/* Right sidebar container */
QFrame#sidebarFrame {{
    background-color: {COLOR_SIDEBAR_BG};
    border-left: 1px solid #1E293B;
    border-right: none;
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
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 500;
    text-align: right;
    margin: 2px 8px;
}}

QPushButton#sidebarButton:hover {{
    background-color: {COLOR_SIDEBAR_HOVER};
    color: #FFFFFF;
}}

QPushButton#sidebarButton:checked {{
    background-color: {COLOR_SIDEBAR_ACTIVE};
    color: #FFFFFF;
    font-weight: bold;
    border-right: 4px solid {COLOR_ACCENT};
}}

/* Card containers */
QFrame#cardFrame {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    padding: 16px;
}}

QFrame#statCard {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 12px;
}}

/* Drag & Drop Zone */
QFrame#dropZone {{
    background-color: {COLOR_CARD};
    border: 2px dashed #CBD5E1;
    border-radius: 12px;
    padding: 28px;
}}

QFrame#dropZone:hover {{
    border-color: {COLOR_PRIMARY};
    background-color: #F1F5F9;
}}

/* Buttons */
QPushButton {{
    background-color: #FFFFFF;
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: #F1F5F9;
    border-color: #CBD5E1;
}}

QPushButton:pressed {{
    background-color: #E2E8F0;
}}

QPushButton#primaryButton {{
    background-color: {COLOR_PRIMARY};
    color: #FFFFFF;
    border: none;
    font-weight: bold;
    font-size: 14px;
    padding: 10px 22px;
    border-radius: 8px;
}}

QPushButton#primaryButton:hover {{
    background-color: {COLOR_PRIMARY_HOVER};
}}

QPushButton#primaryButton:pressed {{
    background-color: {COLOR_PRIMARY_ACTIVE};
}}

QPushButton#primaryButton:disabled {{
    background-color: #94A3B8;
    color: #F8FAFC;
}}

QPushButton#dangerButton {{
    background-color: {COLOR_ERROR_BG};
    color: {COLOR_ERROR};
    border: 1px solid #FECACA;
    font-weight: bold;
    padding: 8px 18px;
    border-radius: 6px;
}}

QPushButton#dangerButton:hover {{
    background-color: #FEE2E2;
}}

QPushButton#accentButton {{
    background-color: {COLOR_ACCENT};
    color: #FFFFFF;
    border: none;
    font-weight: bold;
    padding: 8px 18px;
    border-radius: 6px;
}}

QPushButton#accentButton:hover {{
    background-color: #6D28D9;
}}

/* Inputs & Form elements */
QLineEdit, QComboBox, QSpinBox {{
    background-color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 7px 10px;
    color: {COLOR_TEXT};
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border-color: {COLOR_BORDER_FOCUS};
}}

QComboBox::drop-down {{
    border: none;
    padding-left: 10px;
}}

/* Text Editors */
QTextEdit {{
    background-color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 12px;
    font-size: 14px;
    line-height: 1.6;
    selection-background-color: #BFDBFE;
}}

/* Progress Bar */
QProgressBar {{
    background-color: #E2E8F0;
    border: none;
    border-radius: 6px;
    height: 10px;
    text-align: center;
    color: transparent;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_PRIMARY}, stop:1 {COLOR_ACCENT});
    border-radius: 6px;
}}

/* Tables */
QTableWidget {{
    background-color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    gridline-color: #F1F5F9;
}}

QHeaderView::section {{
    background-color: #F8FAFC;
    color: {COLOR_TEXT_MUTED};
    font-weight: bold;
    border: none;
    border-bottom: 1px solid {COLOR_BORDER};
    padding: 8px;
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    background-color: #FFFFFF;
    top: -1px;
}}

QTabBar::tab {{
    background-color: #F1F5F9;
    color: {COLOR_TEXT_MUTED};
    border: 1px solid {COLOR_BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 9px 18px;
    margin-left: 2px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background-color: #FFFFFF;
    color: {COLOR_PRIMARY};
    font-weight: bold;
    border-bottom: 2px solid {COLOR_PRIMARY};
}}

/* ScrollBars */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: #CBD5E1;
    min-height: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: #94A3B8;
}}
"""
