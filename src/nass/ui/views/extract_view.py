"""
Extraction view for NASS.
Handles single-file processing with intelligent method detection, preview, progress, and results.
Fully bilingual (Arabic/English) with responsive layouts for small screens.
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
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
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
from nass.processors.pdf_processor import PdfProcessor
from nass.services.export_service import ExportService
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

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 10, 14, 10)
        main_layout.setSpacing(10)

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

        # Right Panel: Options & Preview wrapped in ScrollArea for small screen heights
        right_panel = QFrame()
        right_panel.setObjectName("cardFrame")
        right_panel.setMinimumWidth(320)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(8)

        self.lbl_opts_title = QLabel(tr("extract_options_title"))
        self.lbl_opts_title.setStyleSheet("font-weight: bold; color: #1E3A8A; font-size: 12px;")
        right_layout.addWidget(self.lbl_opts_title)

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

        # Preview Section with direct page navigation controls [ - ]  3 / 12  [ + ]
        preview_header = QHBoxLayout()
        self.lbl_preview_title = QLabel(tr("extract_lbl_preview"))
        self.lbl_preview_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #1E293B;")
        preview_header.addWidget(self.lbl_preview_title)
        preview_header.addStretch()

        self.nav_container = QWidget()
        nav_layout = QHBoxLayout(self.nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(6)

        self.btn_prev_page = QPushButton("−")
        self.btn_prev_page.setToolTip(tr("extract_page_prev"))
        self.btn_prev_page.setFixedSize(26, 26)
        self.btn_prev_page.setCursor(Qt.PointingHandCursor)
        self.btn_prev_page.setEnabled(False)
        self.btn_prev_page.clicked.connect(self._go_prev_page)

        self.lbl_page_counter = QLabel("0 / 0")
        self.lbl_page_counter.setStyleSheet("font-size: 11px; font-weight: bold; color: #1E293B; min-width: 50px;")
        self.lbl_page_counter.setAlignment(Qt.AlignCenter)

        self.btn_next_page = QPushButton("+")
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

        # Results Tabs
        self.results_tabs = QTabWidget()

        # Tab 1: Extracted text
        tab_text_widget = QWidget()
        tt_layout = QVBoxLayout(tab_text_widget)
        tt_layout.setContentsMargins(4, 6, 4, 4)
        self.txt_output = QTextEdit()
        self.txt_output.setPlaceholderText(tr("extract_txt_placeholder"))
        self.txt_output.setLayoutDirection(Qt.RightToLeft if I18n.is_rtl() else Qt.LeftToRight)
        self.txt_output.textChanged.connect(self._update_text_counts)
        tt_layout.addWidget(self.txt_output)
        self.results_tabs.addTab(tab_text_widget, tr("extract_tab_text"))

        # Tab 2: Mathematical formulas (LaTeX)
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

    def load_file(self, file_path: Path):
        """Load selected document, identify its type, update preview, and prepare options."""
        self.current_file = file_path.resolve()
        self.current_doc_result = None
        self.page_images_cache.clear()
        self.txt_output.clear()
        self.txt_math_output.clear()
        self.current_preview_page = 1
        self.total_preview_pages = 1

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

        # Adapt UI controls based on file type
        is_ocr_needed = (file_type in (FileType.IMAGE, FileType.PDF))
        self.lang_container.setVisible(is_ocr_needed)
        self.dpi_container.setVisible(is_ocr_needed)
        self.chk_enhance.setVisible(is_ocr_needed)
        self.chk_single_col.setVisible(is_ocr_needed)

        # Page count and preview setup
        if file_type == FileType.PDF:
            try:
                page_count, is_enc, has_txt = PdfProcessor.get_document_info(self.current_file)
                if is_enc:
                    self.lbl_file_meta.setText(tr("extract_meta_encrypted_pdf"))
                    self.btn_start.setEnabled(False)
                    self._update_page_nav(1, 0)
                    return
                self._update_page_nav(1, page_count)
                self.lbl_stat_pages.setText(tr("extract_stat_pages_fmt", pages=page_count))
            except Exception as e:
                logger.warning(f"Could not read PDF metadata: {e}")
                self._update_page_nav(1, 1)
        elif file_type == FileType.IMAGE:
            self._update_page_nav(1, 1)
            self.lbl_stat_pages.setText(tr("extract_stat_pages_fmt", pages=1))
        else:
            self._update_page_nav(1, 1)
            self.lbl_stat_pages.setText(tr("extract_stat_pages_fmt", pages=1))

        self._render_current_page_preview(1)
        self.btn_start.setEnabled(True)
        self.lbl_progress_status.setText(tr("extract_file_ready"))
        self.progress_bar.setValue(0)

    def _update_page_nav(self, current: int, total: int):
        """Update direct page navigation state and counter [ - ]  current / total  [ + ]."""
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
        """Render page image preview for visual formats (PDF, images)."""
        if not self.current_file or not self.current_file.exists():
            return

        if page_num in self.page_images_cache:
            self.lbl_image_preview.setPixmap(self.page_images_cache[page_num])
            return

        file_type = FileUtils.detect_file_type(self.current_file)
        try:
            if file_type == FileType.IMAGE:
                pix = QPixmap(str(self.current_file))
                scaled = pix.scaledToWidth(380, Qt.SmoothTransformation)
                self.page_images_cache[page_num] = scaled
                self.lbl_image_preview.setPixmap(scaled)
            elif file_type == FileType.PDF:
                import fitz
                doc = fitz.open(str(self.current_file))
                if 0 <= page_num - 1 < len(doc):
                    page = doc[page_num - 1]
                    pil_img = PdfProcessor.render_page_to_image(page, dpi=120)
                    doc.close()

                    data = pil_img.tobytes("raw", "RGB")
                    qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format_RGB888)
                    pix = QPixmap.fromImage(qimg).scaledToWidth(380, Qt.SmoothTransformation)
                    self.page_images_cache[page_num] = pix
                    self.lbl_image_preview.setPixmap(pix)
            else:
                self.lbl_image_preview.setText(
                    tr("extract_direct_doc_preview", type=file_type.value.upper())
                )
        except Exception as e:
            logger.warning(f"Failed to generate preview for page {page_num}: {e}")
            self.lbl_image_preview.setText(tr("extract_preview_unavailable"))

    def _on_preview_page_changed(self, index: int):
        page_num = index + 1
        self._render_current_page_preview(page_num)
        self._sync_page_selection_stats(page_num)

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
        )

        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.combo_lang.setEnabled(False)
        self.combo_dpi.setEnabled(False)
        self.chk_enhance.setEnabled(False)
        self.chk_math.setEnabled(False)
        self.chk_single_col.setEnabled(False)

        self.progress_bar.setValue(0)
        self.lbl_progress_status.setText(tr("extract_status_reading"))
        self.txt_output.clear()
        self.txt_math_output.clear()

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
        current_text = self.txt_output.toPlainText()
        prefix = "\n\n" if current_text else ""
        header_title = page_res.title or (
            tr("extract_page_of_total", page=page_num, total=total_pages) if total_pages > 1 else ""
        )
        header = f"--- [{header_title}] ---\n" if header_title else ""
        self.txt_output.setText(f"{current_text}{prefix}{header}{page_res.text}")

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

            if self.current_doc_result.all_equations:
                self.results_tabs.setTabText(
                    1, tr("extract_tab_math_count", count=len(self.current_doc_result.all_equations))
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
                    dummy_page = PageResult(page_number=1, text=text)
                    doc_res = DocumentResult(
                        file_path=self.current_file or Path("extracted.docx"),
                        pages=[dummy_page],
                    )
                    ExportService.export_to_docx(doc_res, Path(path))
                QMessageBox.information(self, tr("copied_title"), tr("extract_export_docx_success", path=path))
            except Exception as e:
                QMessageBox.critical(self, tr("extract_export_error_title"), tr("extract_export_error_msg", err=e))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return
        file_path = Path(urls[0].toLocalFile()).resolve()
        valid, _ = FileUtils.is_valid_file(file_path)
        if valid:
            self.load_file(file_path)
            event.acceptProposedAction()

    def retranslate_ui(self) -> None:
        """Updates text elements based on current application language."""
        direction = Qt.RightToLeft if I18n.is_rtl() else Qt.LeftToRight
        self.setLayoutDirection(direction)

        if hasattr(self, "btn_change"):
            self.btn_change.setText(tr("extract_btn_change"))
        self.lbl_opts_title.setText(tr("extract_options_title"))
        self.lbl_lang_title.setText(tr("extract_lbl_ocr_lang"))
        self._populate_lang_combo()
        self.lbl_dpi_title.setText(tr("extract_lbl_dpi"))
        self._populate_dpi_combo()

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
        self.results_tabs.setTabText(0, tr("extract_tab_text"))
        self.results_tabs.setTabText(1, tr("extract_tab_math"))
        self.txt_output.setPlaceholderText(tr("extract_txt_placeholder"))
        self.txt_output.setLayoutDirection(direction)
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
