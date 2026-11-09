"""
General application settings view for NASS.
Provides configuration options for export defaults, window persistence, and factory reset.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from nass.core.settings import SettingsManager


class AppSettingsView(QWidget):
    """
    View managing general application settings, default export formats, and UI preferences.
    """

    settings_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.settings = SettingsManager.get_instance()
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # Header bar
        header = QFrame()
        header.setObjectName("cardFrame")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 12, 16, 12)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        lbl_title = QLabel("إعدادات التطبيق العامة")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A;")
        lbl_desc = QLabel("تخصيص سلوك البرنامج الافتراضي، خيارات التصدير، وحجم النافذة")
        lbl_desc.setStyleSheet("font-size: 12px; color: #64748B;")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)
        h_layout.addLayout(title_box)
        layout.addWidget(header)

        # 1. Export options group
        grp_export = QGroupBox("خيارات تصدير النتائج الافتراضية")
        ge_layout = QVBoxLayout(grp_export)
        ge_layout.setSpacing(12)

        fmt_row = QHBoxLayout()
        lbl_fmt = QLabel("صيغة التصدير التلقائية:")
        lbl_fmt.setStyleSheet("font-size: 13px; font-weight: 500;")
        self.combo_export_fmt = QComboBox()
        self.combo_export_fmt.addItem("ملف نصي نقي (TXT - UTF-8)", "txt")
        self.combo_export_fmt.addItem("مستند ميكروسوفت وورد (DOCX - RTL)", "docx")
        self.combo_export_fmt.addItem("مستند رياضي (LaTeX - .tex)", "tex")

        # Set default from settings
        current_fmt = self.settings.get("export_default_format", "txt")
        idx = self.combo_export_fmt.findData(current_fmt)
        if idx >= 0:
            self.combo_export_fmt.setCurrentIndex(idx)

        fmt_row.addWidget(lbl_fmt)
        fmt_row.addWidget(self.combo_export_fmt, stretch=1)
        ge_layout.addLayout(fmt_row)

        self.chk_extract_embedded = QCheckBox("استخراج النصوص الرقمية المدمجة في ملفات PDF افتراضياً قبل محاولة OCR")
        self.chk_extract_embedded.setChecked(self.settings.get("extract_embedded_first", True))
        ge_layout.addWidget(self.chk_extract_embedded)

        layout.addWidget(grp_export)

        # 2. Window and UI preferences group
        grp_ui = QGroupBox("سلوك الواجهة والنافذة")
        gu_layout = QVBoxLayout(grp_ui)
        gu_layout.setSpacing(10)

        self.chk_remember_size = QCheckBox("تذكر أبعاد وموضع النافذة عند إعادة تشغيل البرنامج")
        self.chk_remember_size.setChecked(self.settings.get("remember_window_size", True))
        gu_layout.addWidget(self.chk_remember_size)

        layout.addWidget(grp_ui)

        # 3. Action buttons bar
        btn_bar = QHBoxLayout()
        btn_save = QPushButton("حفظ الإعدادات")
        btn_save.setObjectName("primaryButton")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self._save_settings)

        btn_reset_all = QPushButton("استعادة ضبط المصنع")
        btn_reset_all.setObjectName("dangerButton")
        btn_reset_all.setCursor(Qt.PointingHandCursor)
        btn_reset_all.clicked.connect(self._reset_all_settings)

        btn_bar.addWidget(btn_save)
        btn_bar.addWidget(btn_reset_all)
        btn_bar.addStretch()
        layout.addLayout(btn_bar)

        layout.addStretch()

    def _save_settings(self) -> None:
        """Saves current settings to disk."""
        self.settings.set("export_default_format", self.combo_export_fmt.currentData(), auto_save=False)
        self.settings.set("extract_embedded_first", self.chk_extract_embedded.isChecked(), auto_save=False)
        self.settings.set("remember_window_size", self.chk_remember_size.isChecked(), auto_save=True)
        QMessageBox.information(self, "تم الحفظ", "تم حفظ إعدادات التطبيق العامة بنجاح.")
        self.settings_changed.emit()

    def _reset_all_settings(self) -> None:
        """Resets all settings to default values after user confirmation."""
        reply = QMessageBox.question(
            self,
            "تأكيد استعادة الإعدادات",
            "هل أنت متأكد من رغبتك في إعادة تعيين كافة إعدادات التطبيق ومحرك OCR إلى قيمها الافتراضية؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.settings.reset_to_defaults()
            self.combo_export_fmt.setCurrentIndex(0)
            self.chk_extract_embedded.setChecked(True)
            self.chk_remember_size.setChecked(True)
            QMessageBox.information(self, "تمت الاستعادة", "تمت استعادة كافة إعدادات التطبيق الافتراضية بنجاح.")
            self.settings_changed.emit()
