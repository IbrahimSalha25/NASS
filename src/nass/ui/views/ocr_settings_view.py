"""
OCR and language settings view for NASS.
Provides comprehensive controls for Tesseract engine detection, language pack downloads,
pre-processing image filters, and mathematical formula extraction settings.
Fully localized in Arabic and English (all UI labels, tabs, status badges, and popup dialogs).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from nass.core.i18n import I18n, tr
from nass.core.settings import SettingsManager
from nass.engines.ocr.language_manager import LanguageManager
from nass.engines.ocr.math_engine import MathRecognitionEngine
from nass.engines.ocr.tesseract_manager import TesseractManager
from nass.ui.icons import AppIcons
from nass.utils.logger import logger


class LanguageDownloadWorker(QThread):
    """
    Background worker thread to download language pack files without freezing the GUI.
    """
    progress = Signal(int, int)  # (downloaded_bytes, total_bytes)
    finished_download = Signal(bool, str)

    def __init__(self, lang_code: str, lang_mgr: LanguageManager) -> None:
        super().__init__()
        self.lang_code = lang_code
        self.lang_mgr = lang_mgr
        self._cancelled = False

    def cancel(self) -> None:
        """Flags the download operation for cancellation."""
        self._cancelled = True

    def run(self) -> None:
        def on_prog(d: int, t: int) -> None:
            self.progress.emit(d, t)

        success, msg, _ = self.lang_mgr.download_and_install_language(
            self.lang_code,
            progress_callback=on_prog,
            cancel_check=lambda: self._cancelled,
        )
        self.finished_download.emit(success, msg)


class OcrSettingsView(QWidget):
    """
    View managing Tesseract OCR engine installation, language packs, and advanced configurations.
    """

    settings_updated = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.tess_mgr = TesseractManager()
        self.lang_mgr = LanguageManager()
        self.settings = SettingsManager.get_instance()
        self.math_engine = MathRecognitionEngine()
        self.download_worker: Optional[LanguageDownloadWorker] = None

        self._init_ui()
        self.refresh_all_data()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # Header bar
        header_frame = QFrame()
        header_frame.setObjectName("cardFrame")
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(14, 10, 14, 10)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.lbl_title = QLabel(tr("ocr_settings_title"))
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #0F172A;")
        self.lbl_desc = QLabel(tr("ocr_settings_desc"))
        self.lbl_desc.setStyleSheet("font-size: 12px; color: #64748B;")
        title_box.addWidget(self.lbl_title)
        title_box.addWidget(self.lbl_desc)
        h_layout.addLayout(title_box)
        h_layout.addStretch()

        self.btn_refresh = QPushButton(tr("ocr_settings_btn_refresh"))
        self.btn_refresh.setIcon(AppIcons.refresh())
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_all_data)
        h_layout.addWidget(self.btn_refresh)

        main_layout.addWidget(header_frame)

        # Tabs container
        self.tabs = QTabWidget()

        # Tab 1: Engine status & installation
        self.tab_engine = self._build_engine_tab()
        self.tabs.addTab(self.tab_engine, tr("ocr_settings_tab_engine"))

        # Tab 2: Language packs management
        self.tab_languages = self._build_languages_tab()
        self.tabs.addTab(self.tab_languages, tr("ocr_settings_tab_languages"))

        # Tab 3: Advanced recognition options
        self.tab_advanced = self._build_advanced_tab()
        self.tabs.addTab(self.tab_advanced, tr("ocr_settings_tab_advanced"))

        # Tab 4: Mathematical formulas engine
        self.tab_math = self._build_math_tab()
        self.tabs.addTab(self.tab_math, tr("ocr_settings_tab_math"))

        main_layout.addWidget(self.tabs, stretch=2)

    # -------------------------------------------------------------
    # 1. Engine tab
    # -------------------------------------------------------------
    def _build_engine_tab(self) -> QWidget:
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # General status card
        self.card_status = QFrame()
        self.card_status.setObjectName("cardFrame")
        cs_layout = QVBoxLayout(self.card_status)
        cs_layout.setSpacing(10)

        self.lbl_status_badge = QLabel(tr("ocr_settings_status_checking"))
        self.lbl_status_badge.setStyleSheet(
            "padding: 8px 14px; border-radius: 6px; font-weight: bold; font-size: 14px; background-color: #F1F5F9;"
        )
        cs_layout.addWidget(self.lbl_status_badge)

        self.lbl_version_title = QLabel(tr("ocr_settings_lbl_version"))
        self.lbl_version_val = QLabel("-")
        self.lbl_version_val.setLayoutDirection(Qt.LeftToRight)
        self.lbl_version_val.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.lbl_exe_path_title = QLabel(tr("ocr_settings_lbl_exe_path"))
        self.lbl_exe_path_val = QLabel("-")
        self.lbl_exe_path_val.setLayoutDirection(Qt.LeftToRight)
        self.lbl_exe_path_val.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.lbl_tessdata_title = QLabel(tr("ocr_settings_lbl_tessdata"))
        self.lbl_tessdata_val = QLabel("-")
        self.lbl_tessdata_val.setLayoutDirection(Qt.LeftToRight)
        self.lbl_tessdata_val.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.lbl_pytesseract_title = QLabel(tr("ocr_settings_lbl_pytesseract"))
        self.lbl_pytesseract_val = QLabel("-")
        self.lbl_pytesseract_val.setLayoutDirection(Qt.LeftToRight)
        self.lbl_pytesseract_val.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        for r_title, val_lbl in [
            (self.lbl_version_title, self.lbl_version_val),
            (self.lbl_exe_path_title, self.lbl_exe_path_val),
            (self.lbl_tessdata_title, self.lbl_tessdata_val),
            (self.lbl_pytesseract_title, self.lbl_pytesseract_val),
        ]:
            row = QHBoxLayout()
            r_title.setStyleSheet("font-weight: bold; min-width: 220px; color: #334155;")
            val_lbl.setStyleSheet(
                "color: #0F172A; font-family: 'Consolas', 'Courier New', monospace; "
                "font-size: 12px; background-color: #F8FAFC; border: 1px solid #E2E8F0; "
                "border-radius: 4px; padding: 3px 8px;"
            )
            val_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            row.addWidget(r_title)
            row.addWidget(val_lbl, stretch=1)
            cs_layout.addLayout(row)

        layout.addWidget(self.card_status)

        # Quick actions
        actions_frame = QFrame()
        actions_frame.setObjectName("cardFrame")
        af_layout = QHBoxLayout(actions_frame)
        af_layout.setSpacing(10)

        self.btn_verify = QPushButton(tr("ocr_settings_btn_verify"))
        self.btn_verify.setObjectName("primaryButton")
        self.btn_verify.setCursor(Qt.PointingHandCursor)
        self.btn_verify.clicked.connect(self._verify_installation_action)

        self.btn_browse_exe = QPushButton(tr("ocr_settings_btn_browse_exe"))
        self.btn_browse_exe.setCursor(Qt.PointingHandCursor)
        self.btn_browse_exe.clicked.connect(self._browse_custom_exe)

        self.btn_official_download = QPushButton(tr("ocr_settings_btn_official_download"))
        self.btn_official_download.setCursor(Qt.PointingHandCursor)
        self.btn_official_download.clicked.connect(self._open_official_download)

        self.btn_reset_paths = QPushButton(tr("ocr_settings_btn_reset_paths"))
        self.btn_reset_paths.setCursor(Qt.PointingHandCursor)
        self.btn_reset_paths.clicked.connect(self._reset_to_auto_discovery)

        af_layout.addWidget(self.btn_verify)
        af_layout.addWidget(self.btn_browse_exe)
        af_layout.addWidget(self.btn_official_download)
        af_layout.addWidget(self.btn_reset_paths)
        layout.addWidget(actions_frame)

        # Guide group
        self.guide_group = QGroupBox(tr("ocr_settings_grp_guide"))
        guide_layout = QVBoxLayout(self.guide_group)
        self.txt_guide = QTextEdit()
        self.txt_guide.setReadOnly(True)
        self.txt_guide.setFixedHeight(120)
        self.txt_guide.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; font-size: 12px;")
        guide_layout.addWidget(self.txt_guide)

        self.btn_open_installer = QPushButton(tr("ocr_settings_btn_open_installer"))
        self.btn_open_installer.setCursor(Qt.PointingHandCursor)
        self.btn_open_installer.clicked.connect(self._open_installer_dialog)
        guide_layout.addWidget(self.btn_open_installer, alignment=Qt.AlignLeft)

        layout.addWidget(self.guide_group)
        layout.addStretch()

        scroll.setWidget(container)
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(0, 0, 0, 0)
        w_layout.addWidget(scroll)
        return widget

    # -------------------------------------------------------------
    # 2. Languages tab
    # -------------------------------------------------------------
    def _build_languages_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        top_bar = QHBoxLayout()
        self.lbl_search = QLabel(tr("ocr_settings_lbl_search_lang"))
        self.txt_lang_search = QLineEdit()
        self.txt_lang_search.setPlaceholderText(tr("ocr_settings_placeholder_search_lang"))
        self.txt_lang_search.textChanged.connect(self._filter_languages_catalog)
        top_bar.addWidget(self.lbl_search)
        top_bar.addWidget(self.txt_lang_search, stretch=1)
        layout.addLayout(top_bar)

        splitter = QSplitter(Qt.Vertical)

        # Installed table
        installed_box = QFrame()
        installed_box.setObjectName("cardFrame")
        ib_layout = QVBoxLayout(installed_box)
        ib_layout.setContentsMargins(8, 8, 8, 8)
        self.lbl_inst_title = QLabel(tr("ocr_settings_title_installed"))
        self.lbl_inst_title.setStyleSheet("font-weight: bold; color: #1E40AF;")
        ib_layout.addWidget(self.lbl_inst_title)

        self.table_installed = QTableWidget()
        self.table_installed.setColumnCount(4)
        self._update_table_installed_headers()
        self.table_installed.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_installed.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_installed.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_installed.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        ib_layout.addWidget(self.table_installed)
        splitter.addWidget(installed_box)

        # Catalog table
        catalog_box = QFrame()
        catalog_box.setObjectName("cardFrame")
        cb_layout = QVBoxLayout(catalog_box)
        cb_layout.setContentsMargins(8, 8, 8, 8)
        self.lbl_cat_title = QLabel(tr("ocr_settings_title_catalog"))
        self.lbl_cat_title.setStyleSheet("font-weight: bold; color: #1E40AF;")
        cb_layout.addWidget(self.lbl_cat_title)

        self.table_catalog = QTableWidget()
        self.table_catalog.setColumnCount(4)
        self._update_table_catalog_headers()
        self.table_catalog.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_catalog.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_catalog.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_catalog.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        cb_layout.addWidget(self.table_catalog)

        self.progress_download = QProgressBar()
        self.progress_download.setValue(0)
        self.progress_download.setVisible(False)
        self.lbl_download_status = QLabel("")
        self.lbl_download_status.setStyleSheet("color: #64748B; font-size: 11px;")
        cb_layout.addWidget(self.progress_download)
        cb_layout.addWidget(self.lbl_download_status)

        splitter.addWidget(catalog_box)
        splitter.setSizes([200, 300])
        layout.addWidget(splitter)
        return widget

    def _update_table_installed_headers(self) -> None:
        self.table_installed.setHorizontalHeaderLabels([
            tr("ocr_settings_col_lang_code"),
            tr("ocr_settings_col_lang_name"),
            tr("ocr_settings_col_lang_size"),
            tr("ocr_settings_col_actions"),
        ])

    def _update_table_catalog_headers(self) -> None:
        self.table_catalog.setHorizontalHeaderLabels([
            tr("ocr_settings_col_lang_code"),
            tr("ocr_settings_col_lang_name"),
            tr("ocr_settings_col_status"),
            tr("ocr_settings_col_download"),
        ])

    # -------------------------------------------------------------
    # 3. Advanced recognition options tab
    # -------------------------------------------------------------
    def _build_advanced_tab(self) -> QWidget:
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        self.grp_basic = QGroupBox(tr("ocr_settings_grp_basic"))
        gb_layout = QVBoxLayout(self.grp_basic)
        gb_layout.setSpacing(10)

        # PSM
        psm_box = QVBoxLayout()
        self.lbl_psm = QLabel(tr("ocr_settings_lbl_psm"))
        self.lbl_psm.setStyleSheet("font-weight: bold;")
        self.combo_psm = QComboBox()
        self._populate_psm_combo()

        self.lbl_psm_desc = QLabel(tr("ocr_settings_lbl_psm_desc"))
        self.lbl_psm_desc.setStyleSheet("color: #64748B; font-size: 11px;")
        psm_box.addWidget(self.lbl_psm)
        psm_box.addWidget(self.combo_psm)
        psm_box.addWidget(self.lbl_psm_desc)
        gb_layout.addLayout(psm_box)

        # OEM
        oem_box = QVBoxLayout()
        self.lbl_oem = QLabel(tr("ocr_settings_lbl_oem"))
        self.lbl_oem.setStyleSheet("font-weight: bold;")
        self.combo_oem = QComboBox()
        self._populate_oem_combo()

        self.lbl_oem_desc = QLabel(tr("ocr_settings_lbl_oem_desc"))
        self.lbl_oem_desc.setStyleSheet("color: #64748B; font-size: 11px;")
        oem_box.addWidget(self.lbl_oem)
        oem_box.addWidget(self.combo_oem)
        oem_box.addWidget(self.lbl_oem_desc)
        gb_layout.addLayout(oem_box)

        # Image Filters
        filters_box = QVBoxLayout()
        self.lbl_filters = QLabel(tr("ocr_settings_lbl_filters"))
        self.lbl_filters.setStyleSheet("font-weight: bold;")
        self.chk_adv_gray = QCheckBox(tr("ocr_settings_chk_gray"))
        self.chk_adv_contrast = QCheckBox(tr("ocr_settings_chk_contrast"))
        self.chk_adv_denoise = QCheckBox(tr("ocr_settings_chk_denoise"))
        self.chk_adv_threshold = QCheckBox(tr("ocr_settings_chk_threshold"))
        self.chk_adv_deskew = QCheckBox(tr("ocr_settings_chk_deskew"))

        for c in (
            self.chk_adv_gray, self.chk_adv_contrast, self.chk_adv_denoise,
            self.chk_adv_threshold, self.chk_adv_deskew
        ):
            filters_box.addWidget(c)
        gb_layout.addLayout(filters_box)

        layout.addWidget(self.grp_basic)

        # Custom config
        self.grp_custom = QGroupBox(tr("ocr_settings_grp_custom"))
        gc_layout = QVBoxLayout(self.grp_custom)
        self.lbl_custom_cfg = QLabel(tr("ocr_settings_lbl_custom"))
        self.txt_custom_config = QLineEdit()
        self.txt_custom_config.setPlaceholderText("مثال: -c preserve_interword_spaces=1")
        gc_layout.addWidget(self.lbl_custom_cfg)
        gc_layout.addWidget(self.txt_custom_config)
        layout.addWidget(self.grp_custom)

        # Actions
        btn_bar = QHBoxLayout()
        self.btn_save_adv = QPushButton(tr("ocr_settings_btn_save_adv"))
        self.btn_save_adv.setObjectName("primaryButton")
        self.btn_save_adv.setCursor(Qt.PointingHandCursor)
        self.btn_save_adv.clicked.connect(self._save_advanced_settings)

        self.btn_reset_adv = QPushButton(tr("ocr_settings_btn_reset_adv"))
        self.btn_reset_adv.setCursor(Qt.PointingHandCursor)
        self.btn_reset_adv.clicked.connect(self._reset_advanced_defaults)

        btn_bar.addWidget(self.btn_save_adv)
        btn_bar.addWidget(self.btn_reset_adv)
        btn_bar.addStretch()
        layout.addLayout(btn_bar)

        layout.addStretch()
        scroll.setWidget(container)
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(0, 0, 0, 0)
        w_layout.addWidget(scroll)
        return widget

    def _populate_psm_combo(self) -> None:
        curr = self.combo_psm.currentData() if self.combo_psm.count() > 0 else 3
        self.combo_psm.clear()
        self.combo_psm.addItem(tr("ocr_settings_psm_3"), 3)
        self.combo_psm.addItem(tr("ocr_settings_psm_1"), 1)
        self.combo_psm.addItem(tr("ocr_settings_psm_4"), 4)
        self.combo_psm.addItem(tr("ocr_settings_psm_6"), 6)
        self.combo_psm.addItem(tr("ocr_settings_psm_7"), 7)
        self.combo_psm.addItem(tr("ocr_settings_psm_11"), 11)
        idx = self.combo_psm.findData(curr)
        if idx >= 0:
            self.combo_psm.setCurrentIndex(idx)

    def _populate_oem_combo(self) -> None:
        curr = self.combo_oem.currentData() if self.combo_oem.count() > 0 else 3
        self.combo_oem.clear()
        self.combo_oem.addItem(tr("ocr_settings_oem_3"), 3)
        self.combo_oem.addItem(tr("ocr_settings_oem_1"), 1)
        self.combo_oem.addItem(tr("ocr_settings_oem_0"), 0)
        idx = self.combo_oem.findData(curr)
        if idx >= 0:
            self.combo_oem.setCurrentIndex(idx)

    # -------------------------------------------------------------
    # 4. Math recognition tab
    # -------------------------------------------------------------
    def _build_math_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        card_math = QFrame()
        card_math.setObjectName("cardFrame")
        cm_layout = QVBoxLayout(card_math)
        cm_layout.setSpacing(12)

        self.lbl_math_title = QLabel(tr("ocr_settings_math_title"))
        self.lbl_math_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E40AF;")
        cm_layout.addWidget(self.lbl_math_title)

        self.chk_enable_math = QCheckBox(tr("ocr_settings_chk_math"))
        self.chk_enable_math.setStyleSheet("font-size: 13px; font-weight: bold;")
        self.chk_enable_math.setChecked(self.settings.get("math_enabled", False))
        self.chk_enable_math.toggled.connect(self._on_math_toggle)
        cm_layout.addWidget(self.chk_enable_math)

        engine_row = QHBoxLayout()
        self.lbl_m_engine = QLabel(tr("ocr_settings_lbl_math_engine"))
        self.combo_math_engine = QComboBox()
        self._populate_math_engine_combo()
        engine_row.addWidget(self.lbl_m_engine)
        engine_row.addWidget(self.combo_math_engine, stretch=1)
        cm_layout.addLayout(engine_row)

        self.box_pix_status = QFrame()
        self.box_pix_status.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px;")
        ps_layout = QVBoxLayout(self.box_pix_status)
        self.lbl_pix_status = QLabel(tr("ocr_settings_pix_checking"))
        self.lbl_pix_desc = QLabel(tr("ocr_settings_pix_desc"))
        self.lbl_pix_desc.setStyleSheet("color: #64748B; font-size: 11px;")
        ps_layout.addWidget(self.lbl_pix_status)
        ps_layout.addWidget(self.lbl_pix_desc)
        cm_layout.addWidget(self.box_pix_status)

        layout.addWidget(card_math)
        layout.addStretch()
        return widget

    def _populate_math_engine_combo(self) -> None:
        curr = self.combo_math_engine.currentData() if self.combo_math_engine.count() > 0 else "builtin"
        self.combo_math_engine.clear()
        self.combo_math_engine.addItem(tr("ocr_settings_math_builtin"), "builtin")
        self.combo_math_engine.addItem(tr("ocr_settings_math_pix2tex"), "pix2tex")
        idx = self.combo_math_engine.findData(curr)
        if idx >= 0:
            self.combo_math_engine.setCurrentIndex(idx)

    # -------------------------------------------------------------
    # Logic and event handlers
    # -------------------------------------------------------------
    def refresh_all_data(self) -> None:
        """Refreshes all diagnostic data for Tesseract engine, language packs, and math engine."""
        # 1. Tesseract status
        status = self.tess_mgr.get_engine_status()
        is_inst = status.get("is_installed", False)
        ver = status.get("version")

        if is_inst:
            self.lbl_status_badge.setText(tr("ocr_settings_status_ready", version=ver or ""))
            self.lbl_status_badge.setStyleSheet(
                "padding: 8px 14px; border-radius: 6px; font-weight: bold; font-size: 13px; background-color: #ECFDF5; color: #10B981;"
            )
        else:
            self.lbl_status_badge.setText(status.get("error_message") or tr("ocr_settings_status_not_found"))
            self.lbl_status_badge.setStyleSheet(
                "padding: 8px 14px; border-radius: 6px; font-weight: bold; font-size: 13px; background-color: #FEF2F2; color: #EF4444;"
            )

        self.lbl_version_val.setText(ver or "-")
        self.lbl_exe_path_val.setText(status.get("executable_path") or "-")
        self.lbl_tessdata_val.setText(status.get("tessdata_path") or "-")
        py_conn = status.get("pytesseract_connected", False)
        self.lbl_pytesseract_val.setText(tr("ocr_settings_connected") if py_conn else tr("ocr_settings_not_connected"))
        self.lbl_pytesseract_val.setStyleSheet(
            "color: #10B981; font-weight: bold;" if py_conn else "color: #EF4444; font-weight: bold;"
        )

        # Installation guide text
        info = self.tess_mgr.get_official_download_info()
        self.txt_guide.setText(info["guide"])

        # 2. Languages
        self._reload_languages_tables()

        # 3. Math engine status
        m_status = self.math_engine.get_engine_status()
        if m_status["pix2tex_available"]:
            self.lbl_pix_status.setText(tr("ocr_settings_pix_ready"))
            self.lbl_pix_status.setStyleSheet("color: #10B981; font-weight: bold;")
        else:
            self.lbl_pix_status.setText(tr("ocr_settings_pix_missing"))
            self.lbl_pix_status.setStyleSheet("color: #64748B; font-weight: bold;")

    def _reload_languages_tables(self) -> None:
        """Rebuilds installed and catalog language tables."""
        installed = self.lang_mgr.list_installed_languages()
        self.table_installed.setRowCount(len(installed))

        for row, item in enumerate(installed):
            item_code = QTableWidgetItem(item.code)
            item_code.setTextAlignment(Qt.AlignCenter)
            self.table_installed.setItem(row, 0, item_code)
            self.table_installed.setItem(row, 1, QTableWidgetItem(item.name_ar if I18n.is_rtl() else item.name_en))
            item_size = QTableWidgetItem(item.size_formatted)
            item_size.setTextAlignment(Qt.AlignCenter)
            self.table_installed.setItem(row, 2, item_size)

            btn_del = QPushButton(tr("ocr_settings_btn_delete"))
            btn_del.setObjectName("dangerButton")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.clicked.connect(lambda _, c=item.code: self._delete_language_action(c))
            self.table_installed.setCellWidget(row, 3, btn_del)

        self._filter_languages_catalog(self.txt_lang_search.text())

    def _filter_languages_catalog(self, query: str = "") -> None:
        """Filters the downloadable languages catalog by search query."""
        catalog = self.lang_mgr.list_all_catalog_languages(search_query=query)
        self.table_catalog.setRowCount(len(catalog))

        for row, item in enumerate(catalog):
            item_code = QTableWidgetItem(item.code)
            item_code.setTextAlignment(Qt.AlignCenter)
            self.table_catalog.setItem(row, 0, item_code)
            self.table_catalog.setItem(row, 1, QTableWidgetItem(item.name_ar if I18n.is_rtl() else item.name_en))

            status_str = tr("ocr_settings_status_installed") if item.is_installed else tr("ocr_settings_status_available")
            status_item = QTableWidgetItem(status_str)
            if item.is_installed:
                status_item.setForeground(Qt.darkGreen)
            self.table_catalog.setItem(row, 2, status_item)

            if item.is_installed:
                btn_installed = QPushButton(tr("ocr_settings_btn_installed"))
                btn_installed.setEnabled(False)
                self.table_catalog.setCellWidget(row, 3, btn_installed)
            else:
                btn_dl = QPushButton(tr("ocr_settings_btn_download"))
                btn_dl.setObjectName("primaryButton")
                btn_dl.setCursor(Qt.PointingHandCursor)
                btn_dl.clicked.connect(lambda _, c=item.code: self._download_language_action(c))
                self.table_catalog.setCellWidget(row, 3, btn_dl)

    def _download_language_action(self, lang_code: str) -> None:
        """Spawns background download worker for a language code."""
        if self.download_worker and self.download_worker.isRunning():
            QMessageBox.warning(self, tr("warning_title"), tr("ocr_settings_pop_dl_in_progress"))
            return

        self.progress_download.setVisible(True)
        self.progress_download.setValue(0)
        self.lbl_download_status.setText(tr("ocr_settings_pop_dl_starting", code=lang_code))

        self.download_worker = LanguageDownloadWorker(lang_code, self.lang_mgr)
        self.download_worker.progress.connect(self._on_download_progress)
        self.download_worker.finished_download.connect(self._on_download_finished)
        self.download_worker.start()

    def _on_download_progress(self, downloaded: int, total: int) -> None:
        if total > 0:
            pct = int((downloaded / total) * 100)
            self.progress_download.setValue(pct)
            mb_d = downloaded / (1024 * 1024)
            mb_t = total / (1024 * 1024)
            self.lbl_download_status.setText(tr("ocr_settings_pop_dl_progress", done=mb_d, total=mb_t, pct=pct))

    def _on_download_finished(self, success: bool, msg: str) -> None:
        self.progress_download.setVisible(False)
        self.lbl_download_status.setText("")
        if success:
            QMessageBox.information(self, tr("ocr_settings_pop_dl_success_title"), msg)
            self.refresh_all_data()
            self.settings_updated.emit()
        else:
            QMessageBox.critical(self, tr("ocr_settings_pop_dl_fail_title"), msg)

    def _delete_language_action(self, lang_code: str) -> None:
        reply = QMessageBox.question(
            self,
            tr("ocr_settings_pop_delete_title"),
            tr("ocr_settings_pop_delete_msg", code=lang_code),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            success, msg = self.lang_mgr.delete_language(lang_code)
            if success:
                QMessageBox.information(self, tr("ocr_settings_pop_deleted_title"), msg)
                self.refresh_all_data()
                self.settings_updated.emit()
            else:
                QMessageBox.warning(self, tr("ocr_settings_pop_cant_delete_title"), msg)

    def _verify_installation_action(self) -> None:
        success, msg, _ = self.tess_mgr.verify_installation()
        if success:
            QMessageBox.information(self, tr("ocr_settings_pop_verify_title"), msg)
        else:
            QMessageBox.warning(self, tr("ocr_settings_pop_verify_warn_title"), msg)
        self.refresh_all_data()

    def _browse_custom_exe(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("ocr_settings_pop_browse_exe_title"),
            "",
            tr("ocr_settings_pop_browse_exe_filter"),
        )
        if file_path:
            success, msg, _ = self.tess_mgr.set_custom_executable_path(Path(file_path))
            if success:
                QMessageBox.information(self, tr("ocr_settings_pop_path_set_title"), msg)
                self.refresh_all_data()
                self.settings_updated.emit()
            else:
                QMessageBox.critical(self, tr("ocr_settings_pop_invalid_path_title"), msg)

    def _open_official_download(self) -> None:
        info = self.tess_mgr.get_official_download_info()
        url = info["primary_url"]
        QDesktopServices.openUrl(url)

    def _reset_to_auto_discovery(self) -> None:
        self.tess_mgr.reset_to_auto_discovery()
        QMessageBox.information(self, tr("ocr_settings_pop_reset_discovery_title"), tr("ocr_settings_pop_reset_discovery_msg"))
        self.refresh_all_data()
        self.settings_updated.emit()

    def _open_installer_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("ocr_settings_pop_open_installer_title"),
            "",
            tr("ocr_settings_pop_open_installer_filter"),
        )
        if file_path:
            reply = QMessageBox.question(
                self,
                tr("ocr_settings_pop_confirm_run_installer_title"),
                tr("ocr_settings_pop_confirm_run_installer_msg", path=file_path),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                try:
                    os.startfile(file_path)
                except Exception as e:
                    QMessageBox.critical(self, tr("ocr_settings_pop_cant_run_installer_title"), tr("ocr_settings_pop_cant_run_installer_msg", err=e))

    def _save_advanced_settings(self) -> None:
        self.settings.set("psm", self.combo_psm.currentData(), auto_save=False)
        self.settings.set("oem", self.combo_oem.currentData(), auto_save=False)
        self.settings.set("tesseract_extra_config", self.txt_custom_config.text().strip(), auto_save=False)
        self.settings.set("threshold", self.chk_adv_threshold.isChecked(), auto_save=False)
        self.settings.set("enhance_contrast", self.chk_adv_contrast.isChecked(), auto_save=False)
        self.settings.set("denoise", self.chk_adv_denoise.isChecked(), auto_save=False)
        self.settings.set("deskew", self.chk_adv_deskew.isChecked(), auto_save=False)
        self.settings.save()
        QMessageBox.information(self, tr("ocr_settings_pop_save_adv_title"), tr("ocr_settings_pop_save_adv_msg"))
        self.settings_updated.emit()

    def _reset_advanced_defaults(self) -> None:
        self.settings.reset_to_defaults()
        self.combo_psm.setCurrentIndex(0)
        self.combo_oem.setCurrentIndex(0)
        self.txt_custom_config.clear()
        self.chk_adv_threshold.setChecked(False)
        self.chk_adv_contrast.setChecked(False)
        self.chk_adv_denoise.setChecked(False)
        self.chk_adv_deskew.setChecked(False)
        QMessageBox.information(self, tr("ocr_settings_pop_reset_adv_title"), tr("ocr_settings_pop_reset_adv_msg"))

    def _on_math_toggle(self, enabled: bool) -> None:
        self.settings.set("math_enabled", enabled)

    def retranslate_ui(self) -> None:
        """Dynamically retranslates UI elements upon language change."""
        direction = Qt.RightToLeft if I18n.is_rtl() else Qt.LeftToRight
        self.setLayoutDirection(direction)

        self.lbl_title.setText(tr("ocr_settings_title"))
        self.lbl_desc.setText(tr("ocr_settings_desc"))
        self.btn_refresh.setText(tr("ocr_settings_btn_refresh"))

        self.tabs.setTabText(0, tr("ocr_settings_tab_engine"))
        self.tabs.setTabText(1, tr("ocr_settings_tab_languages"))
        self.tabs.setTabText(2, tr("ocr_settings_tab_advanced"))
        self.tabs.setTabText(3, tr("ocr_settings_tab_math"))

        self.lbl_version_title.setText(tr("ocr_settings_lbl_version"))
        self.lbl_exe_path_title.setText(tr("ocr_settings_lbl_exe_path"))
        self.lbl_tessdata_title.setText(tr("ocr_settings_lbl_tessdata"))
        self.lbl_pytesseract_title.setText(tr("ocr_settings_lbl_pytesseract"))

        self.btn_verify.setText(tr("ocr_settings_btn_verify"))
        self.btn_browse_exe.setText(tr("ocr_settings_btn_browse_exe"))
        self.btn_official_download.setText(tr("ocr_settings_btn_official_download"))
        self.btn_reset_paths.setText(tr("ocr_settings_btn_reset_paths"))

        self.guide_group.setTitle(tr("ocr_settings_grp_guide"))
        self.btn_open_installer.setText(tr("ocr_settings_btn_open_installer"))

        self.lbl_search.setText(tr("ocr_settings_lbl_search_lang"))
        self.txt_lang_search.setPlaceholderText(tr("ocr_settings_placeholder_search_lang"))
        self.lbl_inst_title.setText(tr("ocr_settings_title_installed"))
        self.lbl_cat_title.setText(tr("ocr_settings_title_catalog"))

        self._update_table_installed_headers()
        self._update_table_catalog_headers()

        self.grp_basic.setTitle(tr("ocr_settings_grp_basic"))
        self.lbl_psm.setText(tr("ocr_settings_lbl_psm"))
        self.lbl_psm_desc.setText(tr("ocr_settings_lbl_psm_desc"))
        self._populate_psm_combo()

        self.lbl_oem.setText(tr("ocr_settings_lbl_oem"))
        self.lbl_oem_desc.setText(tr("ocr_settings_lbl_oem_desc"))
        self._populate_oem_combo()

        self.lbl_filters.setText(tr("ocr_settings_lbl_filters"))
        self.chk_adv_gray.setText(tr("ocr_settings_chk_gray"))
        self.chk_adv_contrast.setText(tr("ocr_settings_chk_contrast"))
        self.chk_adv_denoise.setText(tr("ocr_settings_chk_denoise"))
        self.chk_adv_threshold.setText(tr("ocr_settings_chk_threshold"))
        self.chk_adv_deskew.setText(tr("ocr_settings_chk_deskew"))

        self.grp_custom.setTitle(tr("ocr_settings_grp_custom"))
        self.lbl_custom_cfg.setText(tr("ocr_settings_lbl_custom"))
        self.btn_save_adv.setText(tr("ocr_settings_btn_save_adv"))
        self.btn_reset_adv.setText(tr("ocr_settings_btn_reset_adv"))

        self.lbl_math_title.setText(tr("ocr_settings_math_title"))
        self.chk_enable_math.setText(tr("ocr_settings_chk_math"))
        self.lbl_m_engine.setText(tr("ocr_settings_lbl_math_engine"))
        self._populate_math_engine_combo()
        self.lbl_pix_desc.setText(tr("ocr_settings_pix_desc"))

        self.refresh_all_data()
