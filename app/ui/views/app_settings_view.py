"""
شاشة إعدادات التطبيق العامة لنظام نَصّ (NASS).
تتيح تخصيص خيارات التصدير وسلوك النوافذ واستعادة كافة الإعدادات.
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

from app.core.settings_manager import SettingsManager


class AppSettingsView(QWidget):
    """شاشة إعدادات التطبيق العامة."""

    settings_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.settings = SettingsManager.get_instance()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        header = QFrame()
        header.setObjectName("cardFrame")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(14, 10, 14, 10)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        lbl_title = QLabel("إعدادات التطبيق العامة")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E3A8A;")
        lbl_desc = QLabel("تخصيص سلوك البرنامج وخيارات التصدير والواجهة")
        lbl_desc.setStyleSheet("font-size: 12px; color: #64748B;")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)
        h_layout.addLayout(title_box)
        layout.addWidget(header)

        # بطاقة خيارات التصدير
        grp_export = QGroupBox("خيارات تصدير النتائج")
        ge_layout = QVBoxLayout(grp_export)
        ge_layout.setSpacing(10)

        fmt_row = QHBoxLayout()
        lbl_fmt = QLabel("صيغة التصدير الافتراضية:")
        self.combo_export_fmt = QComboBox()
        self.combo_export_fmt.addItem("ملف نصي نقي (TXT - UTF-8)", "txt")
        self.combo_export_fmt.addItem("مستند ميكروسوفت وورد (DOCX - RTL)", "docx")
        fmt_row.addWidget(lbl_fmt)
        fmt_row.addWidget(self.combo_export_fmt, stretch=1)
        ge_layout.addLayout(fmt_row)

        self.chk_include_headers = QCheckBox("تضمين فواصل الصفحات وأسماء الملفات تلقائياً في الملفات المصدرة")
        self.chk_include_headers.setChecked(True)
        ge_layout.addWidget(self.chk_include_headers)

        layout.addWidget(grp_export)

        # بطاقة سلوك النافذة والواجهة
        grp_ui = QGroupBox("سلوك الواجهة والنافذة")
        gu_layout = QVBoxLayout(grp_ui)
        self.chk_remember_size = QCheckBox("تذكر أبعاد وموضع النافذة عند إعادة التشغيل")
        self.chk_remember_size.setChecked(self.settings.get("remember_window_size", True))
        gu_layout.addWidget(self.chk_remember_size)
        layout.addWidget(grp_ui)

        # أزرار الإجراءات
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

    def _save_settings(self):
        self.settings.set("export_default_format", self.combo_export_fmt.currentData(), auto_save=False)
        self.settings.set("remember_window_size", self.chk_remember_size.isChecked(), auto_save=True)
        QMessageBox.information(self, "تم الحفظ", "تم حفظ إعدادات التطبيق بنجاح.")
        self.settings_changed.emit()

    def _reset_all_settings(self):
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
            self.chk_remember_size.setChecked(True)
            QMessageBox.information(self, "تمت الاستعادة", "تمت استعادة كافة إعدادات التطبيق الافتراضية بنجاح.")
            self.settings_changed.emit()
