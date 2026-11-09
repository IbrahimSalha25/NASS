"""
شريط خيارات وضبط معالجة OCR (اللغة، الجودة، وتحسينات الصور).
"""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from app.core.models import OcrLanguage, OcrOptions


class OptionsBarWidget(QFrame):
    """شريط التحكم بإعدادات اللغة وجودة المعالجة."""

    def __init__(self, available_languages: List[str] = None, parent=None):
        super().__init__(parent)
        self.setObjectName("cardFrame")
        self.available_langs = available_languages or ["ara", "eng"]
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # صف الخيارات الأساسية
        row_layout = QHBoxLayout()
        row_layout.setSpacing(20)

        # 1. اختيار اللغة
        lang_box = QHBoxLayout()
        lang_box.setSpacing(8)
        lang_label = QLabel("لغة المستند:")
        lang_label.setStyleSheet("font-weight: bold; color: #1E293B;")
        self.combo_lang = QComboBox()
        self.combo_lang.setCursor(Qt.PointingHandCursor)

        # إضافة خيارات اللغات المتوفرة
        self.combo_lang.addItem("العربية والإنجليزية (تلقائي)", OcrLanguage.ARABIC_AND_ENGLISH.value)
        self.combo_lang.addItem("العربية فقط", OcrLanguage.ARABIC.value)
        self.combo_lang.addItem("الإنجليزية فقط", OcrLanguage.ENGLISH.value)

        lang_box.addWidget(lang_label)
        lang_box.addWidget(self.combo_lang)

        # 2. اختيار جودة الاستخراج (DPI)
        dpi_box = QHBoxLayout()
        dpi_box.setSpacing(8)
        dpi_label = QLabel("دقة المعالجة:")
        dpi_label.setStyleSheet("font-weight: bold; color: #1E293B;")
        self.combo_dpi = QComboBox()
        self.combo_dpi.setCursor(Qt.PointingHandCursor)
        self.combo_dpi.addItem("300 DPI (عالي وموصى به)", 300)
        self.combo_dpi.addItem("200 DPI (متوسط متوازن)", 200)
        self.combo_dpi.addItem("150 DPI (سريع)", 150)

        dpi_box.addWidget(dpi_label)
        dpi_box.addWidget(self.combo_dpi)

        # 3. استخراج النص المضمن أولاً
        self.chk_embedded = QCheckBox("استخراج النص الأصلي المضمن في PDF أولاً")
        self.chk_embedded.setChecked(True)
        self.chk_embedded.setToolTip("يسرّع المعالجة ويضمن دقة 100% للمستندات النصية غير المصورة")

        row_layout.addLayout(lang_box)
        row_layout.addLayout(dpi_box)
        row_layout.addWidget(self.chk_embedded)
        row_layout.addStretch()

        # صف تحسينات الصور المتقدمة
        enhancement_layout = QHBoxLayout()
        enhancement_layout.setSpacing(15)

        self.chk_enable_enhancement = QCheckBox("تفعيل معالجة وتحسين الصور")
        self.chk_enable_enhancement.setChecked(False)
        self.chk_enable_enhancement.toggled.connect(self._toggle_enhancement_options)

        self.chk_contrast = QCheckBox("تحسين التباين")
        self.chk_denoise = QCheckBox("إزالة الضوضاء")
        self.chk_threshold = QCheckBox("ثنائية اللون (Binarization)")

        # إيقاف الخيارات الفرعية افتراضياً
        self.chk_contrast.setEnabled(False)
        self.chk_denoise.setEnabled(False)
        self.chk_threshold.setEnabled(False)

        enhancement_layout.addWidget(self.chk_enable_enhancement)
        enhancement_layout.addWidget(self.chk_contrast)
        enhancement_layout.addWidget(self.chk_denoise)
        enhancement_layout.addWidget(self.chk_threshold)
        enhancement_layout.addStretch()

        main_layout.addLayout(row_layout)
        main_layout.addLayout(enhancement_layout)

    def _toggle_enhancement_options(self, checked: bool):
        """تفعيل أو تعطيل خيارات التحسين الفرعية."""
        self.chk_contrast.setEnabled(checked)
        self.chk_denoise.setEnabled(checked)
        self.chk_threshold.setEnabled(checked)

    def get_options(self) -> OcrOptions:
        """قراءة الإعدادات الحالية من الواجهة وتجهيز كائن OcrOptions."""
        lang_data = self.combo_lang.currentData() or OcrLanguage.ARABIC_AND_ENGLISH.value
        dpi_data = self.combo_dpi.currentData() or 300
        apply_enh = self.chk_enable_enhancement.isChecked()

        return OcrOptions(
            language=str(lang_data),
            dpi=int(dpi_data),
            extract_embedded_first=self.chk_embedded.isChecked(),
            apply_enhancement=apply_enh,
            enhance_contrast=apply_enh and self.chk_contrast.isChecked(),
            denoise=apply_enh and self.chk_denoise.isChecked(),
            threshold=apply_enh and self.chk_threshold.isChecked(),
        )
