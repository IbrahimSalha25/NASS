"""
الأنماط البصرية وقوالب التصميم (QSS) لنظام نَصّ (NASS).
تصميم هادئ وعصري يراعي محاذاة RTL والخطوط العربية.
"""

# الألوان الأساسية
COLOR_PRIMARY = "#1E5E8A"         # أزرق هادئ
COLOR_PRIMARY_HOVER = "#18496B"
COLOR_PRIMARY_ACTIVE = "#123751"
COLOR_BG = "#F8FAFC"              # رمادي ثلجي خفيف جداً
COLOR_CARD = "#FFFFFF"            # بطاقات بيضاء نقية
COLOR_BORDER = "#E2E8F0"          # حدود خفيفة
COLOR_BORDER_FOCUS = "#3B82F6"
COLOR_TEXT = "#1E293B"            # كحلي غامق مريح للعين
COLOR_TEXT_MUTED = "#64748B"      # نص رمادي فرعي
COLOR_SUCCESS = "#10B981"         # أخضر هادئ للنجاح
COLOR_WARNING = "#F59E0B"         # برتقالي للتحذير
COLOR_ERROR = "#EF4444"           # أحمر للأخطاء

APP_STYLESHEET = f"""
/* النمط العام */
QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
    font-family: "Segoe UI", "Tahoma", "Cairo", sans-serif;
    font-size: 13px;
}}

/* النوافذ والقوائم الحاوية */
QMainWindow {{
    background-color: {COLOR_BG};
}}

/* العناوين والبطاقات */
QFrame#cardFrame {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 12px;
}}

QFrame#dropZone {{
    background-color: {COLOR_CARD};
    border: 2px dashed #CBD5E1;
    border-radius: 10px;
    padding: 24px;
}}

QFrame#dropZone:hover {{
    border-color: {COLOR_PRIMARY};
    background-color: #F1F5F9;
}}

/* الأزرار */
QPushButton {{
    background-color: #FFFFFF;
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 7px 16px;
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
    padding: 9px 22px;
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
    background-color: #FEF2F2;
    color: {COLOR_ERROR};
    border: 1px solid #FECACA;
}}

QPushButton#dangerButton:hover {{
    background-color: #FEE2E2;
}}

/* القوائم المنسدلة وحقول الإدخال */
QComboBox {{
    background-color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 6px 12px;
    min-width: 140px;
}}

QComboBox:focus {{
    border-color: {COLOR_BORDER_FOCUS};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

/* الجداول والقوائم */
QTableWidget {{
    background-color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    gridline-color: #F1F5F9;
    selection-background-color: #E0F2FE;
    selection-color: {COLOR_TEXT};
}}

QHeaderView::section {{
    background-color: #F8FAFC;
    color: {COLOR_TEXT_MUTED};
    font-weight: bold;
    border: none;
    border-bottom: 1px solid {COLOR_BORDER};
    padding: 8px 10px;
}}

/* شريط التقدم */
QProgressBar {{
    background-color: #E2E8F0;
    border-radius: 5px;
    height: 10px;
    text-align: center;
    font-size: 10px;
    color: transparent;
}}

QProgressBar::chunk {{
    background-color: {COLOR_PRIMARY};
    border-radius: 5px;
}}

/* مربعات الاختيار */
QCheckBox {{
    spacing: 8px;
    color: {COLOR_TEXT};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    background-color: #FFFFFF;
}}

QCheckBox::indicator:checked {{
    background-color: {COLOR_PRIMARY};
    border-color: {COLOR_PRIMARY};
}}

/* محرر ومستعرض النصوص */
QTextEdit {{
    background-color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 10px;
    font-family: "Segoe UI", "Tahoma", sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: {COLOR_TEXT};
}}

QTextEdit:focus {{
    border-color: {COLOR_BORDER_FOCUS};
}}

/* شريط الحالة */
QStatusBar {{
    background-color: #FFFFFF;
    border-top: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT_MUTED};
    font-size: 12px;
}}
"""
