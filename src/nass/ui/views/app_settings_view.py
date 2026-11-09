"""
General application settings view for NASS.
Provides configuration options for application language (Arabic/English),
history retention limit (default 50 files), export defaults, window persistence, and factory reset.
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
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from nass.core.i18n import I18n, tr
from nass.core.settings import SettingsManager


class AppSettingsView(QWidget):
    """
    View managing general application settings, language preference, history limits, and defaults.
    """

    settings_changed = Signal()
    language_changed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.settings = SettingsManager.get_instance()
        self._init_ui()

    def _init_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(14, 12, 14, 12)
        outer_layout.setSpacing(10)

        # Header bar
        header = QFrame()
        header.setObjectName("cardFrame")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(14, 10, 14, 10)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.lbl_title = QLabel(tr("settings_title"))
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #0F172A;")
        self.lbl_desc = QLabel(tr("settings_desc"))
        self.lbl_desc.setStyleSheet("font-size: 12px; color: #64748B;")
        title_box.addWidget(self.lbl_title)
        title_box.addWidget(self.lbl_desc)
        h_layout.addLayout(title_box)
        outer_layout.addWidget(header)

        # Scrollable container for settings groups
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        # 1. Application Language Group
        self.grp_lang = QGroupBox(tr("settings_grp_language"))
        gl_layout = QVBoxLayout(self.grp_lang)
        gl_layout.setSpacing(8)

        lang_row = QHBoxLayout()
        self.lbl_lang = QLabel(tr("settings_lbl_language"))
        self.lbl_lang.setStyleSheet("font-size: 13px; font-weight: 500;")
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("العربية (الافتراضية) - Arabic (Default)", "ar")
        self.combo_lang.addItem("English - الإنجليزية", "en")

        current_lang = self.settings.get("app_language", "ar")
        idx_lang = self.combo_lang.findData(current_lang)
        if idx_lang >= 0:
            self.combo_lang.setCurrentIndex(idx_lang)

        lang_row.addWidget(self.lbl_lang)
        lang_row.addWidget(self.combo_lang, stretch=1)
        gl_layout.addLayout(lang_row)
        layout.addWidget(self.grp_lang)

        # 2. History & Archiving Group
        self.grp_history = QGroupBox(tr("nav_history"))
        gh_layout = QVBoxLayout(self.grp_history)
        gh_layout.setSpacing(8)

        hist_row = QHBoxLayout()
        self.lbl_max_history = QLabel(tr("settings_lbl_max_history"))
        self.lbl_max_history.setStyleSheet("font-size: 13px; font-weight: 500;")
        self.spin_max_history = QSpinBox()
        self.spin_max_history.setRange(5, 500)
        self.spin_max_history.setSingleStep(5)
        self.spin_max_history.setValue(self.settings.get("max_history_records", 50))
        self.spin_max_history.setFixedWidth(100)
        self.spin_max_history.setFixedHeight(30)

        hist_row.addWidget(self.lbl_max_history)
        hist_row.addWidget(self.spin_max_history)
        hist_row.addStretch()
        gh_layout.addLayout(hist_row)

        self.lbl_max_history_desc = QLabel(tr("settings_desc_max_history"))
        self.lbl_max_history_desc.setStyleSheet("font-size: 11px; color: #64748B;")
        gh_layout.addWidget(self.lbl_max_history_desc)
        layout.addWidget(self.grp_history)

        # 3. Export options group
        self.grp_export = QGroupBox(tr("settings_grp_export"))
        ge_layout = QVBoxLayout(self.grp_export)
        ge_layout.setSpacing(10)

        fmt_row = QHBoxLayout()
        self.lbl_fmt = QLabel(tr("settings_lbl_export_fmt"))
        self.lbl_fmt.setStyleSheet("font-size: 13px; font-weight: 500;")
        self.combo_export_fmt = QComboBox()
        self.combo_export_fmt.addItem("ملف نصي نقي (TXT - UTF-8)", "txt")
        self.combo_export_fmt.addItem("مستند ميكروسوفت وورد (DOCX - RTL)", "docx")
        self.combo_export_fmt.addItem("مستند رياضي (LaTeX - .tex)", "tex")

        current_fmt = self.settings.get("export_default_format", "txt")
        idx = self.combo_export_fmt.findData(current_fmt)
        if idx >= 0:
            self.combo_export_fmt.setCurrentIndex(idx)

        fmt_row.addWidget(self.lbl_fmt)
        fmt_row.addWidget(self.combo_export_fmt, stretch=1)
        ge_layout.addLayout(fmt_row)

        self.chk_extract_embedded = QCheckBox(tr("settings_chk_embedded"))
        self.chk_extract_embedded.setChecked(self.settings.get("extract_embedded_first", True))
        ge_layout.addWidget(self.chk_extract_embedded)

        layout.addWidget(self.grp_export)

        # 4. Window and UI preferences group
        self.grp_ui = QGroupBox(tr("settings_grp_ui"))
        gu_layout = QVBoxLayout(self.grp_ui)
        gu_layout.setSpacing(8)

        self.chk_remember_size = QCheckBox(tr("settings_chk_remember_size"))
        self.chk_remember_size.setChecked(self.settings.get("remember_window_size", True))
        gu_layout.addWidget(self.chk_remember_size)

        layout.addWidget(self.grp_ui)

        # 5. Action buttons bar
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(8)
        self.btn_save = QPushButton(tr("settings_btn_save"))
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setFixedHeight(34)
        self.btn_save.clicked.connect(self._save_settings)

        self.btn_reset_all = QPushButton(tr("settings_btn_reset"))
        self.btn_reset_all.setObjectName("dangerButton")
        self.btn_reset_all.setCursor(Qt.PointingHandCursor)
        self.btn_reset_all.setFixedHeight(34)
        self.btn_reset_all.clicked.connect(self._reset_all_settings)

        btn_bar.addWidget(self.btn_save)
        btn_bar.addWidget(self.btn_reset_all)
        btn_bar.addStretch()
        layout.addLayout(btn_bar)

        layout.addStretch()
        scroll_area.setWidget(container)
        outer_layout.addWidget(scroll_area)

    def retranslate_ui(self) -> None:
        """Retranslates labels and headers for current application language."""
        direction = Qt.RightToLeft if I18n.is_rtl() else Qt.LeftToRight
        self.setLayoutDirection(direction)

        self.lbl_title.setText(tr("settings_title"))
        self.lbl_desc.setText(tr("settings_desc"))
        self.grp_lang.setTitle(tr("settings_grp_language"))
        self.lbl_lang.setText(tr("settings_lbl_language"))
        self.grp_history.setTitle(tr("nav_history"))
        self.lbl_max_history.setText(tr("settings_lbl_max_history"))
        self.lbl_max_history_desc.setText(tr("settings_desc_max_history"))
        self.grp_export.setTitle(tr("settings_grp_export"))
        self.lbl_fmt.setText(tr("settings_lbl_export_fmt"))
        self.chk_extract_embedded.setText(tr("settings_chk_embedded"))
        self.grp_ui.setTitle(tr("settings_grp_ui"))
        self.chk_remember_size.setText(tr("settings_chk_remember_size"))
        self.btn_save.setText(tr("settings_btn_save"))
        self.btn_reset_all.setText(tr("settings_btn_reset"))

    def _save_settings(self) -> None:
        """Saves current settings to disk and applies language change if updated."""
        old_lang = self.settings.get("app_language", "ar")
        new_lang = self.combo_lang.currentData()

        self.settings.set("app_language", new_lang, auto_save=False)
        self.settings.set("max_history_records", self.spin_max_history.value(), auto_save=False)
        self.settings.set("export_default_format", self.combo_export_fmt.currentData(), auto_save=False)
        self.settings.set("extract_embedded_first", self.chk_extract_embedded.isChecked(), auto_save=False)
        self.settings.set("remember_window_size", self.chk_remember_size.isChecked(), auto_save=True)

        I18n.set_current_language(new_lang)

        QMessageBox.information(self, tr("copied_title"), tr("settings_saved_msg"))
        self.settings_changed.emit()

        if new_lang != old_lang:
            self.language_changed.emit(new_lang)

    def _reset_all_settings(self) -> None:
        """Resets all settings to default values after user confirmation."""
        confirm_text = (
            "هل أنت متأكد من رغبتك في إعادة تعيين كافة إعدادات التطبيق ومحرك OCR إلى قيمها الافتراضية؟"
            if I18n.is_rtl() else
            "Are you sure you want to reset all application and OCR engine settings to defaults?"
        )
        reply = QMessageBox.question(
            self,
            tr("confirm_title"),
            confirm_text,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.settings.reset_to_defaults()
            self.combo_lang.setCurrentIndex(0)
            self.spin_max_history.setValue(50)
            self.combo_export_fmt.setCurrentIndex(0)
            self.chk_extract_embedded.setChecked(True)
            self.chk_remember_size.setChecked(True)
            I18n.set_current_language("ar")
            QMessageBox.information(self, tr("confirm_title"), tr("settings_saved_msg"))
            self.settings_changed.emit()
            self.language_changed.emit("ar")
