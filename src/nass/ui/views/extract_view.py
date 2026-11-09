"""
Extraction view for NASS.
Handles single-file processing with intelligent method detection, multi-format visual preview (DOCX, PPTX, XLSX, PDF, Images),
zoom controls, discrete native vs. OCR image extraction options, and categorized provenance result tabs.
Fully bilingual (Arabic/English) with responsive layouts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QClipboard, QDragEnterEvent, QDropEvent, QGuiApplication, QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from nass.core.i18n import I18n, tr
from nass.core.models import (
    DocumentResult,
    ExtractionMethod,
    FileType,
    OcrOptions,
    PageResult,
    ProcessingStatus,
)
from nass.engines.document.document_engine import DocumentEngine
from nass.services.export_service import ExportService
from nass.services.preview_service import DocumentPreviewService
from nass.ui.icons import AppIcons
from nass.utils.file_utils import FileUtils
from nass.utils.logger import logger
from nass.workers.ocr_worker import OcrWorker


class ExtractView(QWidget):
    """View handling the extraction lifecycle for a selected document or image."""

    change_file_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.current_file: Optional[Path] = None
        self.current_doc_result: Optional[DocumentResult] = None
        self.active_worker: Optional[OcrWorker] = None
        self.document_engine = DocumentEngine()
        self.page_images_cache: Dict[int, QPixmap] = {}

        # Zoom state
        self.preview_zoom_factor: float = 1.0
        self.base_preview_width: int = 400

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 10, 14, 10)
        main_layout.setSpacing(10)

        # 0. Drag & Drop Notice Banner at the top of the Extract View
        self.drop_banner = QFrame()
        self.drop_banner.setObjectName("extractDropBanner")
        self.drop_banner.setStyleSheet(
            "QFrame#extractDropBanner {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EFF6FF, stop:1 #F5F3FF);"
            "  border: 1.5px dashed #818CF8;"
            "  border-radius: 8px;"
            "  padding: 6px 14px;"
            "}"
            "QFrame#extractDropBanner:hover {"
            "  background: #EEF2FF;"
            "  border-color: #4F46E5;"
            "}"
        )
        banner_layout = QHBoxLayout(self.drop_banner)
        banner_layout.setContentsMargins(10, 6, 10, 6)
        banner_layout.setSpacing(12)

        self.lbl_banner_icon = QLabel()
        self.lbl_banner_icon.setPixmap(AppIcons.upload("#4F46E5").pixmap(26, 26))
        banner_layout.addWidget(self.lbl_banner_icon)

        banner_text_box = QVBoxLayout()
        banner_text_box.setSpacing(2)
        self.lbl_banner_title = QLabel(tr("extract_drop_banner_title"))
        self.lbl_banner_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #1E1B4B;")
        self.lbl_banner_sub = QLabel(tr("extract_drop_banner_sub"))
        self.lbl_banner_sub.setStyleSheet("font-size: 11px; color: #4338CA;")
        banner_text_box.addWidget(self.lbl_banner_title)
        banner_text_box.addWidget(self.lbl_banner_sub)
        banner_layout.addLayout(banner_text_box, stretch=1)

        main_layout.addWidget(self.drop_banner)

        # 1. Selected File Header Card
        file_header = QFrame()
        file_header.setObjectName("cardFrame")
        fh_layout = QHBoxLayout(file_header)
        fh_layout.setContentsMargins(12, 8, 12, 8)
        fh_layout.setSpacing(12)

        self.lbl_file_icon = QLabel()
        self.lbl_file_icon.setPixmap(AppIcons.ocr("#1E40AF").pixmap(28, 28))
        fh_layout.addWidget(self.lbl_file_icon)

        meta_box = QVBoxLayout()
        meta_box.setSpacing(2)
        self.lbl_file_name = QLabel(tr("extract_no_file_title"))
        self.lbl_file_name.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B;")
        self.lbl_file_meta = QLabel(tr("extract_no_file_desc"))
        self.lbl_file_meta.setStyleSheet("font-size: 11px; color: #64748B;")
        self.lbl_method_badge = QLabel(tr("extract_method_label", method="-"))
        self.lbl_method_badge.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #7C3AED; background-color: #EDE9FE; padding: 2px 8px; border-radius: 4px;"
        )
        meta_box.addWidget(self.lbl_file_name)

        meta_row = QHBoxLayout()
        meta_row.addWidget(self.lbl_file_meta)
        meta_row.addWidget(self.lbl_method_badge)
        meta_row.addStretch()
        meta_box.addLayout(meta_row)

        fh_layout.addLayout(meta_box)
        fh_layout.addStretch()

        self.btn_change = QPushButton(tr("extract_btn_change"))
        self.btn_change.setCursor(Qt.PointingHandCursor)
        self.btn_change.setFixedHeight(30)
        self.btn_change.clicked.connect(self._select_another_file)
        fh_layout.addWidget(self.btn_change)

        main_layout.addWidget(file_header)

        # 2. Main Workspace Splitter
        self.splitter = QSplitter(Qt.Horizontal)

        # Right Panel: Options & Preview
        right_panel = QFrame()
        right_panel.setObjectName("cardFrame")
        right_panel.setMinimumWidth(340)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(8)

        self.lbl_opts_title = QLabel(tr("extract_options_title"))
        self.lbl_opts_title.setStyleSheet("font-weight: bold; color: #1E3A8A; font-size: 12px;")
        right_layout.addWidget(self.lbl_opts_title)

        # Separate extraction modes (Native vs Images OCR)
        self.modes_container = QFrame()
        self.modes_container.setStyleSheet("background-color: #F8FAFC; border-radius: 6px; padding: 4px;")
        modes_layout = QVBoxLayout(self.modes_container)
        modes_layout.setContentsMargins(6, 6, 6, 6)
        modes_layout.setSpacing(6)

        self.chk_extract_native = QCheckBox(tr("extract_chk_native_text"))
        self.chk_extract_native.setChecked(True)
        self.chk_extract_native.setStyleSheet("font-weight: bold; color: #1E293B;")

        self.chk_extract_images = QCheckBox(tr("extract_chk_images_ocr"))
        self.chk_extract_images.setChecked(True)
        self.chk_extract_images.setStyleSheet("font-weight: bold; color: #1E293B;")

        modes_layout.addWidget(self.chk_extract_native)
        modes_layout.addWidget(self.chk_extract_images)
        right_layout.addWidget(self.modes_container)

        # OCR Language row
        self.lang_container = QWidget()
        lang_row = QHBoxLayout(self.lang_container)
        lang_row.setContentsMargins(0, 0, 0, 0)
        self.lbl_lang_title = QLabel(tr("extract_lbl_ocr_lang"))
        self.lbl_lang_title.setStyleSheet("font-size: 12px; font-weight: 500;")
        self.combo_lang = QComboBox()
        self._populate_lang_combo()
        lang_row.addWidget(self.lbl_lang_title)
        lang_row.addWidget(self.combo_lang, stretch=1)
        right_layout.addWidget(self.lang_container)

        # DPI row
        self.dpi_container = QWidget()
        dpi_row = QHBoxLayout(self.dpi_container)
        dpi_row.setContentsMargins(0, 0, 0, 0)
        self.lbl_dpi_title = QLabel(tr("extract_lbl_dpi"))
        self.lbl_dpi_title.setStyleSheet("font-size: 12px; font-weight: 500;")
        self.combo_dpi = QComboBox()
        self._populate_dpi_combo()
        dpi_row.addWidget(self.lbl_dpi_title)
        dpi_row.addWidget(self.combo_dpi, stretch=1)
        right_layout.addWidget(self.dpi_container)

        # Quick enhancement options
        self.chk_enhance = QCheckBox(tr("extract_chk_enhance"))
        self.chk_math = QCheckBox(tr("extract_chk_math"))
        self.chk_single_col = QCheckBox(tr("extract_chk_single_col"))

        right_layout.addWidget(self.chk_enhance)
        right_layout.addWidget(self.chk_math)
        right_layout.addWidget(self.chk_single_col)

        # Action Buttons
        actions_box = QHBoxLayout()
        actions_box.setSpacing(6)

        self.btn_start = QPushButton(tr("extract_btn_start"))
        self.btn_start.setObjectName("primaryButton")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setFixedHeight(34)
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self._start_processing)

        self.btn_cancel = QPushButton(tr("extract_btn_stop"))
        self.btn_cancel.setObjectName("dangerButton")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setFixedHeight(34)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel_processing)

        actions_box.addWidget(self.btn_start, stretch=2)
        actions_box.addWidget(self.btn_cancel, stretch=1)
        right_layout.addLayout(actions_box)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.lbl_progress_status = QLabel(tr("extract_status_waiting"))
        self.lbl_progress_status.setStyleSheet("color: #64748B; font-size: 11px;")
        right_layout.addWidget(self.progress_bar)
        right_layout.addWidget(self.lbl_progress_status)

        # Preview Section with Navigation & Zoom controls
        preview_header = QHBoxLayout()
        self.lbl_preview_title = QLabel(tr("extract_lbl_preview"))
        self.lbl_preview_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #1E293B;")
        preview_header.addWidget(self.lbl_preview_title)
        preview_header.addStretch()

        # Zoom controls with attractive vector icons
        self.btn_zoom_out = QPushButton()
        self.btn_zoom_out.setIcon(AppIcons.zoom_out("#1E293B"))
        self.btn_zoom_out.setIconSize(QSize(16, 16))
        self.btn_zoom_out.setToolTip(tr("extract_zoom_out"))
        self.btn_zoom_out.setFixedSize(28, 26)
        self.btn_zoom_out.setCursor(Qt.PointingHandCursor)
        self.btn_zoom_out.clicked.connect(self._zoom_out_preview)

        self.btn_zoom_reset = QPushButton()
        self.btn_zoom_reset.setIcon(AppIcons.zoom_reset("#1E293B"))
        self.btn_zoom_reset.setIconSize(QSize(16, 16))
        self.btn_zoom_reset.setToolTip(tr("extract_zoom_reset"))
        self.btn_zoom_reset.setFixedSize(28, 26)
        self.btn_zoom_reset.setCursor(Qt.PointingHandCursor)
        self.btn_zoom_reset.clicked.connect(self._zoom_reset_preview)

        self.btn_zoom_in = QPushButton()
        self.btn_zoom_in.setIcon(AppIcons.zoom_in("#1E293B"))
        self.btn_zoom_in.setIconSize(QSize(16, 16))
        self.btn_zoom_in.setToolTip(tr("extract_zoom_in"))
        self.btn_zoom_in.setFixedSize(28, 26)
        self.btn_zoom_in.setCursor(Qt.PointingHandCursor)
        self.btn_zoom_in.clicked.connect(self._zoom_in_preview)

        preview_header.addWidget(self.btn_zoom_out)
        preview_header.addWidget(self.btn_zoom_reset)
        preview_header.addWidget(self.btn_zoom_in)

        # Page nav container
        self.nav_container = QWidget()
        nav_layout = QHBoxLayout(self.nav_container)
        nav_layout.setContentsMargins(4, 0, 0, 0)
        nav_layout.setSpacing(4)

        self.btn_prev_page = QPushButton()
        self.btn_prev_page.setIcon(AppIcons.arrow_left("#1E293B"))
        self.btn_prev_page.setIconSize(QSize(14, 14))
        self.btn_prev_page.setToolTip(tr("extract_page_prev"))
        self.btn_prev_page.setFixedSize(26, 26)
        self.btn_prev_page.setCursor(Qt.PointingHandCursor)
        self.btn_prev_page.setEnabled(False)
        self.btn_prev_page.clicked.connect(self._go_prev_page)

        self.lbl_page_counter = QLabel("0 / 0")
        self.lbl_page_counter.setStyleSheet("font-size: 11px; font-weight: bold; color: #1E293B; min-width: 50px;")
        self.lbl_page_counter.setAlignment(Qt.AlignCenter)

        self.btn_next_page = QPushButton()
        self.btn_next_page.setIcon(AppIcons.arrow_right("#1E293B"))
        self.btn_next_page.setIconSize(QSize(14, 14))
        self.btn_next_page.setToolTip(tr("extract_page_next"))
        self.btn_next_page.setFixedSize(26, 26)
        self.btn_next_page.setCursor(Qt.PointingHandCursor)
        self.btn_next_page.setEnabled(False)
        self.btn_next_page.clicked.connect(self._go_next_page)

        nav_layout.addWidget(self.btn_prev_page)
        nav_layout.addWidget(self.lbl_page_counter)
        nav_layout.addWidget(self.btn_next_page)
        preview_header.addWidget(self.nav_container)

        self.current_preview_page = 1
        self.total_preview_pages = 1

        right_layout.addLayout(preview_header)

        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setStyleSheet("background-color: #F1F5F9; border-radius: 6px;")
        self.lbl_image_preview = QLabel(tr("extract_no_preview"))
        self.lbl_image_preview.setAlignment(Qt.AlignCenter)
        self.lbl_image_preview.setStyleSheet("color: #94A3B8; padding: 12px;")
        self.preview_scroll.setWidget(self.lbl_image_preview)
        right_layout.addWidget(self.preview_scroll, stretch=2)

        # Left Panel: Results Viewer & Statistics
        left_panel = QFrame()
        left_panel.setObjectName("cardFrame")
        left_panel.setMinimumWidth(380)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(8)

        # Statistics Bar
        self.stats_bar = QFrame()
        self.stats_bar.setStyleSheet("background-color: #F8FAFC; border-radius: 6px; padding: 6px;")
        sb_layout = QHBoxLayout(self.stats_bar)
        sb_layout.setContentsMargins(6, 2, 6, 2)

        self.lbl_stat_pages = QLabel(tr("extract_stat_pages_fmt", pages=0))
        self.lbl_stat_words = QLabel(tr("extract_stat_words_fmt", words=0))
        self.lbl_stat_chars = QLabel(tr("extract_stat_chars_fmt", chars=0))
        self.lbl_stat_conf = QLabel(tr("extract_stat_confidence_val", conf=0.0))

        for lbl in (self.lbl_stat_pages, self.lbl_stat_words, self.lbl_stat_chars, self.lbl_stat_conf):
            lbl.setStyleSheet("font-weight: 500; font-size: 11px; color: #334155;")
            sb_layout.addWidget(lbl)
            sb_layout.addStretch()

        left_layout.addWidget(self.stats_bar)

        # Results Tabs: All, Native, Image OCR, Images Table, Math
        self.results_tabs = QTabWidget()

        # Tab 1: All Extracted Text
        tab_all_widget = QWidget()
        ta_layout = QVBoxLayout(tab_all_widget)
        ta_layout.setContentsMargins(4, 6, 4, 4)
        self.txt_output = QTextEdit()
        self.txt_output.setPlaceholderText(tr("extract_txt_placeholder"))
        self.txt_output.setLayoutDirection(Qt.RightToLeft if I18n.is_rtl() else Qt.LeftToRight)
        self.txt_output.textChanged.connect(self._update_text_counts)
        ta_layout.addWidget(self.txt_output)
        self.results_tabs.addTab(tab_all_widget, tr("extract_tab_all_text"))

        # Tab 2: Native Digital Text
        tab_native_widget = QWidget()
        tn_layout = QVBoxLayout(tab_native_widget)
        tn_layout.setContentsMargins(4, 6, 4, 4)
        self.txt_native_output = QTextEdit()
        self.txt_native_output.setPlaceholderText("النصوص الأصلية المكتوبة داخل المستند...")
        self.txt_native_output.setLayoutDirection(Qt.RightToLeft if I18n.is_rtl() else Qt.LeftToRight)
        tn_layout.addWidget(self.txt_native_output)
        self.results_tabs.addTab(tab_native_widget, tr("extract_tab_native_text"))

        # Tab 3: Embedded Images OCR Text
        tab_img_ocr_widget = QWidget()
        ti_layout = QVBoxLayout(tab_img_ocr_widget)
        ti_layout.setContentsMargins(4, 6, 4, 4)
        self.txt_image_ocr_output = QTextEdit()
        self.txt_image_ocr_output.setPlaceholderText("النصوص المستخرجة عبر OCR من الصور المضمنة...")
        self.txt_image_ocr_output.setLayoutDirection(Qt.RightToLeft if I18n.is_rtl() else Qt.LeftToRight)
        ti_layout.addWidget(self.txt_image_ocr_output)
        self.results_tabs.addTab(tab_img_ocr_widget, tr("extract_tab_images_ocr"))

        # Tab 4: Image Provenance Table
        tab_tbl_widget = QWidget()
        tbl_layout = QVBoxLayout(tab_tbl_widget)
        tbl_layout.setContentsMargins(4, 6, 4, 4)
        self.tbl_images = QTableWidget()
        self.tbl_images.setColumnCount(4)
        self.tbl_images.setHorizontalHeaderLabels(["المعرف", "الموقع بالمستند", "الحالة", "الدقة"])
        self.tbl_images.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_images.setAlternatingRowColors(True)
        tbl_layout.addWidget(self.tbl_images)
        self.results_tabs.addTab(tab_tbl_widget, tr("extract_tab_images_list", count=0))

        # Tab 5: Mathematical formulas (LaTeX)
        tab_math_widget = QWidget()
        tm_layout = QVBoxLayout(tab_math_widget)
        tm_layout.setContentsMargins(4, 6, 4, 4)
        self.txt_math_output = QTextEdit()
        self.txt_math_output.setPlaceholderText(tr("extract_math_placeholder"))
        self.txt_math_output.setLayoutDirection(Qt.LeftToRight)
        tm_layout.addWidget(self.txt_math_output)
        self.results_tabs.addTab(tab_math_widget, tr("extract_tab_math"))

        left_layout.addWidget(self.results_tabs, stretch=2)

        # Export & Copy toolbar
        export_bar = QHBoxLayout()
        export_bar.setSpacing(6)

        self.btn_copy_all = QPushButton(tr("extract_btn_copy_all"))
        self.btn_copy_all.setIcon(AppIcons.copy())
        self.btn_copy_all.setIconSize(QSize(16, 16))
        self.btn_copy_all.setFixedHeight(30)
        self.btn_copy_all.setCursor(Qt.PointingHandCursor)
        self.btn_copy_all.clicked.connect(self._copy_all_text)

        self.btn_copy_page = QPushButton(tr("extract_btn_copy_page"))
        self.btn_copy_page.setIcon(AppIcons.copy())
        self.btn_copy_page.setIconSize(QSize(16, 16))
        self.btn_copy_page.setFixedHeight(30)
        self.btn_copy_page.setCursor(Qt.PointingHandCursor)
        self.btn_copy_page.clicked.connect(self._copy_current_page_text)

        self.btn_export_txt = QPushButton(tr("extract_btn_export_txt"))
        self.btn_export_txt.setIcon(AppIcons.export())
        self.btn_export_txt.setIconSize(QSize(16, 16))
        self.btn_export_txt.setFixedHeight(30)
        self.btn_export_txt.setCursor(Qt.PointingHandCursor)
        self.btn_export_txt.clicked.connect(self._export_txt)

        self.btn_export_docx = QPushButton(tr("extract_btn_export_docx"))
        self.btn_export_docx.setIcon(AppIcons.export())
        self.btn_export_docx.setIconSize(QSize(16, 16))
        self.btn_export_docx.setFixedHeight(30)
        self.btn_export_docx.setCursor(Qt.PointingHandCursor)
        self.btn_export_docx.clicked.connect(self._export_docx)

        export_bar.addWidget(self.btn_copy_all)
        export_bar.addWidget(self.btn_copy_page)
        export_bar.addStretch()
        export_bar.addWidget(self.btn_export_txt)
        export_bar.addWidget(self.btn_export_docx)
        left_layout.addLayout(export_bar)

        self.splitter.addWidget(right_panel)
        self.splitter.addWidget(left_panel)
        self.splitter.setSizes([420, 640])
        main_layout.addWidget(self.splitter, stretch=2)

    def _populate_lang_combo(self) -> None:
        selected = self.combo_lang.currentData() if self.combo_lang.count() > 0 else "ara+eng"
        self.combo_lang.clear()
        self.combo_lang.addItem(tr("extract_lang_both"), "ara+eng")
        self.combo_lang.addItem(tr("extract_lang_ara"), "ara")
        self.combo_lang.addItem(tr("extract_lang_eng"), "eng")
        idx = self.combo_lang.findData(selected)
        if idx >= 0:
            self.combo_lang.setCurrentIndex(idx)

    def _populate_dpi_combo(self) -> None:
        selected = self.combo_dpi.currentData() if self.combo_dpi.count() > 0 else 300
        self.combo_dpi.clear()
        self.combo_dpi.addItem(tr("extract_dpi_std"), 300)
        self.combo_dpi.addItem(tr("extract_dpi_fast"), 150)
        self.combo_dpi.addItem(tr("extract_dpi_ultra"), 450)
        idx = self.combo_dpi.findData(selected)
        if idx >= 0:
            self.combo_dpi.setCurrentIndex(idx)

    def _zoom_in_preview(self):
        if self.preview_zoom_factor < 2.5:
            self.preview_zoom_factor += 0.25
            self._render_current_page_preview(self.current_preview_page)

    def _zoom_out_preview(self):
        if self.preview_zoom_factor > 0.5:
            self.preview_zoom_factor -= 0.25
            self._render_current_page_preview(self.current_preview_page)

    def _zoom_reset_preview(self):
        self.preview_zoom_factor = 1.0
        self._render_current_page_preview(self.current_preview_page)

    def load_file(self, file_path: Path):
        """Load selected document, identify its type, update preview, and prepare options."""
        self.current_file = file_path.resolve()
        self.current_doc_result = None
        self.page_images_cache.clear()
        self.txt_output.clear()
        self.txt_native_output.clear()
        self.txt_image_ocr_output.clear()
        self.txt_math_output.clear()
        self.tbl_images.setRowCount(0)
        self.current_preview_page = 1
        self.total_preview_pages = 1
        self.preview_zoom_factor = 1.0

        file_size_formatted = FileUtils.format_size(self.current_file.stat().st_size)
        file_type = FileUtils.detect_file_type(self.current_file)
        predicted_method = self.document_engine.get_predicted_method(self.current_file)

        type_name = file_type.display_name_ar if I18n.is_rtl() else file_type.value.upper()
        method_name = predicted_method.display_name_ar if I18n.is_rtl() else predicted_method.value.capitalize()

        self.lbl_file_name.setText(self.current_file.name)
        self.lbl_file_meta.setText(
            tr(
                "extract_file_meta_info",
                type=type_name,
                size=file_size_formatted,
                folder=self.current_file.parent.name,
            )
        )
        self.lbl_method_badge.setText(tr("extract_method_label", method=method_name))

        # Show native vs image extraction choices for office & PDF
        is_office_or_pdf = (file_type in (FileType.WORD, FileType.POWERPOINT, FileType.EXCEL, FileType.PDF))
        self.modes_container.setVisible(is_office_or_pdf)
        if file_type == FileType.IMAGE:
            self.chk_extract_native.setVisible(False)
            self.chk_extract_images.setChecked(True)
        else:
            self.chk_extract_native.setVisible(True)

        # Inspect page count via DocumentPreviewService
        page_count = DocumentPreviewService.get_document_page_count(self.current_file)
        self._update_page_nav(1, page_count)
        self.lbl_stat_pages.setText(tr("extract_stat_pages_fmt", pages=page_count))

        self._render_current_page_preview(1)
        self.btn_start.setEnabled(True)
        self.lbl_progress_status.setText(tr("extract_file_ready"))
        self.progress_bar.setValue(0)

    def _update_page_nav(self, current: int, total: int):
        """Update direct page navigation state and counter [ ◀ ]  current / total  [ ▶ ]."""
        self.current_preview_page = current
        self.total_preview_pages = total
        if total > 0:
            self.lbl_page_counter.setText(f"{current} / {total}")
            self.btn_prev_page.setEnabled(current > 1)
            self.btn_next_page.setEnabled(current < total)
        else:
            self.lbl_page_counter.setText("0 / 0")
            self.btn_prev_page.setEnabled(False)
            self.btn_next_page.setEnabled(False)

    def _go_prev_page(self):
        """Navigate to previous preview page."""
        if self.current_preview_page > 1:
            self.current_preview_page -= 1
            self._update_page_nav(self.current_preview_page, self.total_preview_pages)
            self._render_current_page_preview(self.current_preview_page)
            self._sync_page_selection_stats(self.current_preview_page)

    def _go_next_page(self):
        """Navigate to next preview page."""
        if self.current_preview_page < self.total_preview_pages:
            self.current_preview_page += 1
            self._update_page_nav(self.current_preview_page, self.total_preview_pages)
            self._render_current_page_preview(self.current_preview_page)
            self._sync_page_selection_stats(self.current_preview_page)

    def _sync_page_selection_stats(self, page_num: int):
        """Synchronize confidence statistics for current page."""
        idx = page_num - 1
        if self.current_doc_result and 0 <= idx < len(self.current_doc_result.pages):
            page_res = self.current_doc_result.pages[idx]
            if page_res.confidence > 0:
                self.lbl_stat_conf.setText(tr("extract_stat_confidence_val", conf=page_res.confidence))

    def _render_current_page_preview(self, page_num: int):
        """Render high quality visual preview using DocumentPreviewService with zoom scaling."""
        if not self.current_file or not self.current_file.exists():
            return

        cache_key = page_num
        target_w = int(self.base_preview_width * self.preview_zoom_factor)

        # Re-render if zoom changed or not cached
        if cache_key in self.page_images_cache and self.preview_zoom_factor == 1.0:
            self.lbl_image_preview.setPixmap(self.page_images_cache[cache_key])
            return

        try:
            pix = DocumentPreviewService.render_page_preview(
                file_path=self.current_file,
                page_num=page_num,
                target_width=target_w,
            )
            if self.preview_zoom_factor == 1.0:
                self.page_images_cache[cache_key] = pix
            self.lbl_image_preview.setPixmap(pix)
        except Exception as e:
            logger.warning(f"Failed to generate preview for page {page_num}: {e}")
            self.lbl_image_preview.setText(tr("extract_preview_unavailable"))

    def _start_processing(self):
        """Start document text extraction in background thread."""
        if not self.current_file:
            return

        opts = OcrOptions(
            language=self.combo_lang.currentData(),
            dpi=self.combo_dpi.currentData(),
            apply_enhancement=self.chk_enhance.isChecked(),
            enhance_contrast=self.chk_enhance.isChecked(),
            denoise=self.chk_enhance.isChecked(),
            single_column=self.chk_single_col.isChecked(),
            extract_math=self.chk_math.isChecked(),
            extract_native_text=self.chk_extract_native.isChecked(),
            extract_images_ocr=self.chk_extract_images.isChecked(),
        )

        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.combo_lang.setEnabled(False)
        self.combo_dpi.setEnabled(False)
        self.chk_enhance.setEnabled(False)
        self.chk_math.setEnabled(False)
        self.chk_single_col.setEnabled(False)
        self.chk_extract_native.setEnabled(False)
        self.chk_extract_images.setEnabled(False)

        self.progress_bar.setValue(0)
        self.lbl_progress_status.setText(tr("extract_status_reading"))
        self.txt_output.clear()
        self.txt_native_output.clear()
        self.txt_image_ocr_output.clear()
        self.txt_math_output.clear()
        self.tbl_images.setRowCount(0)

        self.active_worker = OcrWorker(files=[self.current_file], options=opts)
        self.active_worker.page_progress.connect(self._on_page_progress)
        self.active_worker.overall_progress.connect(self._on_overall_progress)
        self.active_worker.all_finished.connect(self._on_all_finished)
        self.active_worker.error_occurred.connect(self._on_error)

        self.active_worker.start()

    def _cancel_processing(self):
        if self.active_worker and self.active_worker.isRunning():
            self.lbl_progress_status.setText(tr("extract_status_stopping"))
            self.active_worker.cancel()
            self.btn_cancel.setEnabled(False)

    def _on_page_progress(self, file_idx: int, page_num: int, total_pages: int, page_res: PageResult):
        # 1. Update All Text
        current_text = self.txt_output.toPlainText()
        prefix = "\n\n" if current_text else ""
        header_title = page_res.title or (
            tr("extract_page_of_total", page=page_num, total=total_pages) if total_pages > 1 else ""
        )
        header = f"--- [{header_title}] ---\n" if header_title else ""
        self.txt_output.setText(f"{current_text}{prefix}{header}{page_res.text}")

        # 2. Update Native Text Tab
        if page_res.native_text:
            curr_native = self.txt_native_output.toPlainText()
            n_prefix = "\n\n" if curr_native else ""
            self.txt_native_output.setText(f"{curr_native}{n_prefix}{header}{page_res.native_text}")

        # 3. Update Image OCR Text Tab
        if page_res.image_ocr_text:
            curr_img_ocr = self.txt_image_ocr_output.toPlainText()
            i_prefix = "\n\n" if curr_img_ocr else ""
            self.txt_image_ocr_output.setText(f"{curr_img_ocr}{i_prefix}{header}{page_res.image_ocr_text}")

        # 4. Update Images Table
        for img_info in page_res.image_details:
            r = self.tbl_images.rowCount()
            self.tbl_images.insertRow(r)
            self.tbl_images.setItem(r, 0, QTableWidgetItem(img_info.get("item_id", "")))
            self.tbl_images.setItem(r, 1, QTableWidgetItem(img_info.get("location", "")))
            self.tbl_images.setItem(r, 2, QTableWidgetItem(img_info.get("status", "")))
            self.tbl_images.setItem(r, 3, QTableWidgetItem(f"{img_info.get('confidence', 0.0):.1f}%"))

        # 5. Math output
        if page_res.equations:
            math_text = self.txt_math_output.toPlainText()
            m_prefix = "\n\n" if math_text else ""
            m_lines = "\n".join(page_res.equations)
            label = "معادلات" if I18n.is_rtl() else "Formulas"
            self.txt_math_output.setText(f"{math_text}{m_prefix}% {label} {header_title}:\n{m_lines}")

    def _on_overall_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.lbl_progress_status.setText(msg)

    def _on_all_finished(self, results: List[DocumentResult]):
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.combo_lang.setEnabled(True)
        self.combo_dpi.setEnabled(True)
        self.chk_enhance.setEnabled(True)
        self.chk_math.setEnabled(True)
        self.chk_single_col.setEnabled(True)
        self.chk_extract_native.setEnabled(True)
        self.chk_extract_images.setEnabled(True)

        if results:
            self.current_doc_result = results[0]
            if self.current_doc_result.status == ProcessingStatus.COMPLETED:
                self.lbl_progress_status.setText(tr("extract_status_success"))
            else:
                self.lbl_progress_status.setText(tr("extract_status_failed"))

            self.progress_bar.setValue(100)

            # Update statistics
            avg_conf = self.current_doc_result.average_confidence
            self.lbl_stat_conf.setText(tr("extract_stat_confidence_val", conf=avg_conf))
            if avg_conf < 50.0 and avg_conf > 0:
                self.lbl_stat_conf.setStyleSheet("color: #F59E0B; font-weight: bold;")
            else:
                self.lbl_stat_conf.setStyleSheet("color: #10B981; font-weight: bold;")

            self.lbl_stat_pages.setText(tr("extract_stat_pages_fmt", pages=self.current_doc_result.total_pages))
            method_name = (
                self.current_doc_result.method_display_name
                if I18n.is_rtl() else
                self.current_doc_result.extraction_method.value.capitalize()
            )
            self.lbl_method_badge.setText(tr("extract_method_label", method=method_name))

            if len(self.current_doc_result.pages) > 1 and self.total_preview_pages <= 1:
                self._update_page_nav(1, len(self.current_doc_result.pages))

            total_images = sum(len(p.image_details) for p in self.current_doc_result.pages)
            self.results_tabs.setTabText(3, tr("extract_tab_images_list", count=total_images))

            if self.current_doc_result.all_equations:
                self.results_tabs.setTabText(
                    4, tr("extract_tab_math_count", count=len(self.current_doc_result.all_equations))
                )

        self._update_text_counts()

    def _on_error(self, err: str):
        QMessageBox.critical(self, tr("extract_error_title"), err)
        self._on_all_finished([])

    def _update_text_counts(self):
        text = self.txt_output.toPlainText()
        chars = len(text)
        words = len(text.split())
        self.lbl_stat_chars.setText(tr("extract_stat_chars_fmt", chars=chars))
        self.lbl_stat_words.setText(tr("extract_stat_words_fmt", words=words))

    def _select_another_file(self):
        self.change_file_requested.emit()

    def _copy_all_text(self):
        text = self.txt_output.toPlainText().strip()
        if not text:
            QMessageBox.information(self, tr("extract_notice_title"), tr("extract_status_empty"))
            return
        clipboard: QClipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, tr("copied_title"), tr("extract_copied_all_msg"))

    def _copy_current_page_text(self):
        if not self.current_doc_result:
            return
        idx = self.current_preview_page - 1
        if 0 <= idx < len(self.current_doc_result.pages):
            page_text = self.current_doc_result.pages[idx].text.strip()
            if page_text:
                clipboard: QClipboard = QGuiApplication.clipboard()
                clipboard.setText(page_text)
                title = self.current_doc_result.pages[idx].title or f"#{idx + 1}"
                QMessageBox.information(self, tr("copied_title"), tr("extract_copied_page_msg", title=title))
            else:
                QMessageBox.information(self, tr("extract_notice_title"), tr("extract_no_text_in_section"))

    def _export_txt(self):
        text = self.txt_output.toPlainText().strip()
        if not text:
            QMessageBox.information(self, tr("extract_notice_title"), tr("extract_no_text_export"))
            return

        default_name = f"{self.current_file.stem}_extracted.txt" if self.current_file else "extracted.txt"
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("extract_export_txt_title"),
            default_name,
            tr("extract_export_txt_filter"),
        )
        if path:
            try:
                if self.current_doc_result:
                    ExportService.export_to_txt(self.current_doc_result, Path(path))
                else:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(text)
                QMessageBox.information(self, tr("copied_title"), tr("extract_export_txt_success", path=path))
            except Exception as e:
                QMessageBox.critical(self, tr("extract_export_error_title"), tr("extract_export_error_msg", err=e))

    def _export_docx(self):
        text = self.txt_output.toPlainText().strip()
        if not text:
            QMessageBox.information(self, tr("extract_notice_title"), tr("extract_no_text_export"))
            return

        default_name = f"{self.current_file.stem}_extracted.docx" if self.current_file else "extracted.docx"
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("extract_export_docx_title"),
            default_name,
            tr("extract_export_docx_filter"),
        )
        if path:
            try:
                if self.current_doc_result:
                    ExportService.export_to_docx(self.current_doc_result, Path(path))
                else:
                    import docx
                    doc = docx.Document()
                    doc.add_paragraph(text)
                    doc.save(path)
                QMessageBox.information(self, tr("copied_title"), tr("extract_export_docx_success", path=path))
            except Exception as e:
                QMessageBox.critical(self, tr("extract_export_error_title"), tr("extract_export_error_msg", err=e))

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = Path(urls[0].toLocalFile()).resolve()
            valid, err = FileUtils.is_valid_file(path)
            if valid:
                self.load_file(path)
                event.acceptProposedAction()
            else:
                QMessageBox.warning(self, tr("extract_invalid_file_title"), err or "ملف غير مدعوم.")

    def retranslate_ui(self) -> None:
        """Updates text elements based on current application language."""
        direction = Qt.RightToLeft if I18n.is_rtl() else Qt.LeftToRight
        self.setLayoutDirection(direction)

        if hasattr(self, "lbl_banner_title"):
            self.lbl_banner_title.setText(tr("extract_drop_banner_title"))
            self.lbl_banner_sub.setText(tr("extract_drop_banner_sub"))
        if hasattr(self, "btn_change"):
            self.btn_change.setText(tr("extract_btn_change"))
        self.lbl_opts_title.setText(tr("extract_options_title"))
        self.lbl_lang_title.setText(tr("extract_lbl_ocr_lang"))
        self._populate_lang_combo()
        self.lbl_dpi_title.setText(tr("extract_lbl_dpi"))
        self._populate_dpi_combo()

        self.chk_extract_native.setText(tr("extract_chk_native_text"))
        self.chk_extract_images.setText(tr("extract_chk_images_ocr"))
        self.chk_enhance.setText(tr("extract_chk_enhance"))
        self.chk_math.setText(tr("extract_chk_math"))
        self.chk_single_col.setText(tr("extract_chk_single_col"))

        self.btn_start.setText(tr("extract_btn_start"))
        self.btn_cancel.setText(tr("extract_btn_stop"))
        self.btn_copy_all.setText(tr("extract_btn_copy_all"))
        self.btn_copy_page.setText(tr("extract_btn_copy_page"))
        self.btn_export_txt.setText(tr("extract_btn_export_txt"))
        self.btn_export_docx.setText(tr("extract_btn_export_docx"))

        self.lbl_preview_title.setText(tr("extract_lbl_preview"))
        self.btn_prev_page.setToolTip(tr("extract_page_prev"))
        self.btn_next_page.setToolTip(tr("extract_page_next"))

        self.results_tabs.setTabText(0, tr("extract_tab_all_text"))
        self.results_tabs.setTabText(1, tr("extract_tab_native_text"))
        self.results_tabs.setTabText(2, tr("extract_tab_images_ocr"))
        total_imgs = sum(len(p.image_details) for p in self.current_doc_result.pages) if self.current_doc_result else 0
        self.results_tabs.setTabText(3, tr("extract_tab_images_list", count=total_imgs))
        self.results_tabs.setTabText(4, tr("extract_tab_math"))

        self.txt_output.setPlaceholderText(tr("extract_txt_placeholder"))
        self.txt_output.setLayoutDirection(direction)
        self.txt_native_output.setLayoutDirection(direction)
        self.txt_image_ocr_output.setLayoutDirection(direction)
        self.txt_math_output.setPlaceholderText(tr("extract_math_placeholder"))

        if not self.current_file:
            self.lbl_file_name.setText(tr("extract_no_file_title"))
            self.lbl_file_meta.setText(tr("extract_no_file_desc"))
            self.lbl_method_badge.setText(tr("extract_method_label", method="-"))
            self.lbl_progress_status.setText(tr("extract_status_waiting"))
            self.lbl_image_preview.setText(tr("extract_no_preview"))
            self.lbl_stat_pages.setText(tr("extract_stat_pages_fmt", pages=0))
            self.lbl_stat_conf.setText(tr("extract_stat_confidence_val", conf=0.0))
        else:
            file_type = FileUtils.detect_file_type(self.current_file)
            type_name = file_type.display_name_ar if I18n.is_rtl() else file_type.value.upper()
            file_size_formatted = FileUtils.format_size(self.current_file.stat().st_size)
            self.lbl_file_meta.setText(
                tr(
                    "extract_file_meta_info",
                    type=type_name,
                    size=file_size_formatted,
                    folder=self.current_file.parent.name,
                )
            )
            if self.current_doc_result:
                method_name = (
                    self.current_doc_result.method_display_name
                    if I18n.is_rtl() else
                    self.current_doc_result.extraction_method.value.capitalize()
                )
                self.lbl_method_badge.setText(tr("extract_method_label", method=method_name))
                self.lbl_stat_pages.setText(tr("extract_stat_pages_fmt", pages=self.current_doc_result.total_pages))
                self.lbl_stat_conf.setText(tr("extract_stat_confidence_val", conf=self.current_doc_result.average_confidence))

        self._update_text_counts()
