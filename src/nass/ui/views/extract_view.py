"""
Extraction view for NASS.
Handles single-file processing with intelligent method detection, preview, progress, and results.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
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
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(12)

        # 1. Selected File Header Card
        file_header = QFrame()
        file_header.setObjectName("cardFrame")
        fh_layout = QHBoxLayout(file_header)
        fh_layout.setContentsMargins(14, 10, 14, 10)
        fh_layout.setSpacing(12)

        self.lbl_file_icon = QLabel()
        self.lbl_file_icon.setPixmap(AppIcons.ocr("#1E40AF").pixmap(32, 32))
        fh_layout.addWidget(self.lbl_file_icon)

        meta_box = QVBoxLayout()
        meta_box.setSpacing(2)
        self.lbl_file_name = QLabel("لا يوجد ما نعمل عليه الآن. اختر ملفاً للبدء.")
        self.lbl_file_name.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E293B;")
        self.lbl_file_meta = QLabel("اختر ملفك من الشاشة الرئيسية، ودع الباقي علينا.")
        self.lbl_file_meta.setStyleSheet("font-size: 12px; color: #64748B;")
        self.lbl_method_badge = QLabel("طريقة المعالجة: -")
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

        self.btn_change = QPushButton("اختيار ملف آخر")
        self.btn_change.setCursor(Qt.PointingHandCursor)
        self.btn_change.clicked.connect(self._select_another_file)
        fh_layout.addWidget(self.btn_change)

        main_layout.addWidget(file_header)

        # 2. Main Workspace Splitter
        self.splitter = QSplitter(Qt.Horizontal)

        # Right Panel: Options & Preview
        right_panel = QFrame()
        right_panel.setObjectName("cardFrame")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        opts_title = QLabel("إعدادات استخراج المحتوى:")
        opts_title.setStyleSheet("font-weight: bold; color: #1E3A8A; font-size: 13px;")
        right_layout.addWidget(opts_title)

        # OCR Language row
        self.lang_container = QWidget()
        lang_row = QHBoxLayout(self.lang_container)
        lang_row.setContentsMargins(0, 0, 0, 0)
        lang_lbl = QLabel("لغة التعرف (OCR):")
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("العربية + الإنجليزية (تلقائي)", "ara+eng")
        self.combo_lang.addItem("العربية فقط", "ara")
        self.combo_lang.addItem("الإنجليزية فقط", "eng")
        lang_row.addWidget(lang_lbl)
        lang_row.addWidget(self.combo_lang, stretch=1)
        right_layout.addWidget(self.lang_container)

        # DPI row
        self.dpi_container = QWidget()
        dpi_row = QHBoxLayout(self.dpi_container)
        dpi_row.setContentsMargins(0, 0, 0, 0)
        dpi_lbl = QLabel("دقة المعالجة:")
        self.combo_dpi = QComboBox()
        self.combo_dpi.addItem("دقة قياسية موصى بها (300 DPI)", 300)
        self.combo_dpi.addItem("دقة سريعة (150 DPI)", 150)
        self.combo_dpi.addItem("دقة فائقة (450 DPI)", 450)
        dpi_row.addWidget(dpi_lbl)
        dpi_row.addWidget(self.combo_dpi, stretch=1)
        right_layout.addWidget(self.dpi_container)

        # Quick enhancement options
        self.chk_enhance = QCheckBox("تحسين التباين وإزالة التشويش تلقائياً")
        self.chk_math = QCheckBox("استخراج المعادلات الرياضية (LaTeX)")
        self.chk_single_col = QCheckBox("معالجة الصفحة كعمود نصي واحد")

        right_layout.addWidget(self.chk_enhance)
        right_layout.addWidget(self.chk_math)
        right_layout.addWidget(self.chk_single_col)

        # Action Buttons
        actions_box = QHBoxLayout()
        actions_box.setSpacing(8)

        self.btn_start = QPushButton("بدء استخراج النص")
        self.btn_start.setObjectName("primaryButton")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self._start_processing)

        self.btn_cancel = QPushButton("إلغاء")
        self.btn_cancel.setObjectName("dangerButton")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel_processing)

        actions_box.addWidget(self.btn_start, stretch=2)
        actions_box.addWidget(self.btn_cancel, stretch=1)
        right_layout.addLayout(actions_box)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.lbl_progress_status = QLabel("جاهز للبدء")
        self.lbl_progress_status.setStyleSheet("color: #64748B; font-size: 12px;")
        right_layout.addWidget(self.progress_bar)
        right_layout.addWidget(self.lbl_progress_status)

        # Preview Section
        preview_header = QHBoxLayout()
        lbl_preview_title = QLabel("معاينة الصفحة / المحتوى:")
        lbl_preview_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #1E293B;")
        preview_header.addWidget(lbl_preview_title)
        preview_header.addStretch()

        self.combo_pages = QComboBox()
        self.combo_pages.setEnabled(False)
        self.combo_pages.currentIndexChanged.connect(self._on_preview_page_changed)
        preview_header.addWidget(self.combo_pages)
        right_layout.addLayout(preview_header)

        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setStyleSheet("background-color: #F1F5F9; border-radius: 6px;")
        self.lbl_image_preview = QLabel("لا توجد معاينة حالياً")
        self.lbl_image_preview.setAlignment(Qt.AlignCenter)
        self.lbl_image_preview.setStyleSheet("color: #94A3B8; padding: 16px;")
        self.preview_scroll.setWidget(self.lbl_image_preview)
        right_layout.addWidget(self.preview_scroll, stretch=2)

        # Left Panel: Results Viewer & Statistics
        left_panel = QFrame()
        left_panel.setObjectName("cardFrame")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        # Statistics Bar
        self.stats_bar = QFrame()
        self.stats_bar.setStyleSheet("background-color: #F8FAFC; border-radius: 6px; padding: 8px;")
        sb_layout = QHBoxLayout(self.stats_bar)
        sb_layout.setContentsMargins(8, 4, 8, 4)

        self.lbl_stat_pages = QLabel("الصفحات / الشرائح: 0")
        self.lbl_stat_words = QLabel("الكلمات: 0")
        self.lbl_stat_chars = QLabel("الحروف: 0")
        self.lbl_stat_conf = QLabel("متوسط الدقة: -")

        for lbl in (self.lbl_stat_pages, self.lbl_stat_words, self.lbl_stat_chars, self.lbl_stat_conf):
            lbl.setStyleSheet("font-weight: 500; font-size: 12px; color: #334155;")
            sb_layout.addWidget(lbl)
            sb_layout.addStretch()

        left_layout.addWidget(self.stats_bar)

        # Results Tabs
        self.results_tabs = QTabWidget()

        # Tab 1: Extracted text
        tab_text_widget = QWidget()
        tt_layout = QVBoxLayout(tab_text_widget)
        tt_layout.setContentsMargins(4, 8, 4, 4)
        self.txt_output = QTextEdit()
        self.txt_output.setPlaceholderText("سيظهر النص المستخرج هنا فور اكتمال المعالجة...")
        self.txt_output.setLayoutDirection(Qt.RightToLeft)
        self.txt_output.textChanged.connect(self._update_text_counts)
        tt_layout.addWidget(self.txt_output)
        self.results_tabs.addTab(tab_text_widget, "النص المستخرج")

        # Tab 2: Mathematical formulas (LaTeX)
        tab_math_widget = QWidget()
        tm_layout = QVBoxLayout(tab_math_widget)
        tm_layout.setContentsMargins(4, 8, 4, 4)
        self.txt_math_output = QTextEdit()
        self.txt_math_output.setPlaceholderText("لا توجد معادلات رياضية مستخرجة في هذا الملف حتى الآن.")
        self.txt_math_output.setLayoutDirection(Qt.LeftToRight)
        tm_layout.addWidget(self.txt_math_output)
        self.results_tabs.addTab(tab_math_widget, "المعادلات (LaTeX)")

        left_layout.addWidget(self.results_tabs, stretch=2)

        # Export & Copy toolbar
        export_bar = QHBoxLayout()
        export_bar.setSpacing(8)

        self.btn_copy_all = QPushButton("نسخ النص كاملاً")
        self.btn_copy_all.setIcon(AppIcons.copy())
        self.btn_copy_all.setCursor(Qt.PointingHandCursor)
        self.btn_copy_all.clicked.connect(self._copy_all_text)

        self.btn_copy_page = QPushButton("نسخ القسم الحالي")
        self.btn_copy_page.setIcon(AppIcons.copy())
        self.btn_copy_page.setCursor(Qt.PointingHandCursor)
        self.btn_copy_page.clicked.connect(self._copy_current_page_text)

        self.btn_export_txt = QPushButton("تصدير TXT")
        self.btn_export_txt.setIcon(AppIcons.export())
        self.btn_export_txt.setCursor(Qt.PointingHandCursor)
        self.btn_export_txt.clicked.connect(self._export_txt)

        self.btn_export_docx = QPushButton("تصدير Word")
        self.btn_export_docx.setIcon(AppIcons.export())
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
        self.splitter.setSizes([450, 650])
        main_layout.addWidget(self.splitter, stretch=2)

    def load_file(self, file_path: Path):
        """Load selected document, identify its type, update preview, and prepare options."""
        self.current_file = file_path.resolve()
        self.current_doc_result = None
        self.page_images_cache.clear()
        self.txt_output.clear()
        self.txt_math_output.clear()
        self.combo_pages.clear()

        file_size_formatted = FileUtils.format_size(self.current_file.stat().st_size)
        file_type = FileUtils.detect_file_type(self.current_file)
        predicted_method = self.document_engine.get_predicted_method(self.current_file)

        self.lbl_file_name.setText(self.current_file.name)
        self.lbl_file_meta.setText(
            f"النوع: {file_type.display_name_ar} | الحجم: {file_size_formatted} | المجلد: {self.current_file.parent.name}"
        )
        self.lbl_method_badge.setText(f"طريقة المعالجة: {predicted_method.display_name_ar}")

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
                    self.lbl_file_meta.setText("تنبيه: ملف PDF محمي بكلمة مرور وغير قابل للقراءة.")
                    self.btn_start.setEnabled(False)
                    return
                for i in range(1, page_count + 1):
                    self.combo_pages.addItem(f"الصفحة {i} من {page_count}", i)
                self.combo_pages.setEnabled(True)
                self.lbl_stat_pages.setText(f"الصفحات: {page_count}")
            except Exception as e:
                logger.warning(f"Could not read PDF metadata: {e}")
        elif file_type == FileType.IMAGE:
            self.combo_pages.addItem("صورة (1 من 1)", 1)
            self.combo_pages.setEnabled(False)
            self.lbl_stat_pages.setText("الصفحات: 1")
        else:
            self.combo_pages.addItem("مستند رقمي كامل", 1)
            self.combo_pages.setEnabled(False)
            self.lbl_stat_pages.setText("مستند رقمي مباشر")

        self._render_current_page_preview(1)
        self.btn_start.setEnabled(True)
        self.lbl_progress_status.setText("الملف جاهز للاستخراج.")
        self.progress_bar.setValue(0)

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
                    f"مستند رقمي مباشر ({file_type.display_name_ar})\nسيتم استخراج النصوص مباشرة وبسرعة فائقة."
                )
        except Exception as e:
            logger.warning(f"Failed to generate preview for page {page_num}: {e}")
            self.lbl_image_preview.setText("معاينة بصرية غير متوفرة لهذا الملف.")

    def _on_preview_page_changed(self, index: int):
        if index >= 0 and self.combo_pages.count() > 0:
            page_num = self.combo_pages.currentData() or (index + 1)
            self._render_current_page_preview(page_num)

            if self.current_doc_result and 0 <= index < len(self.current_doc_result.pages):
                page_res = self.current_doc_result.pages[index]
                if page_res.confidence > 0:
                    self.lbl_stat_conf.setText(f"ثقة القسم: {page_res.confidence:.1f}%")

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
        self.lbl_progress_status.setText("نقرأ محتوى ملفك الآن...")
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
            self.lbl_progress_status.setText("جاري إيقاف المعالجة بأمان...")
            self.active_worker.cancel()
            self.btn_cancel.setEnabled(False)

    def _on_page_progress(self, file_idx: int, page_num: int, total_pages: int, page_res: PageResult):
        current_text = self.txt_output.toPlainText()
        prefix = "\n\n" if current_text else ""
        header_title = page_res.title or (f"الصفحة {page_num} من {total_pages}" if total_pages > 1 else "")
        header = f"--- [{header_title}] ---\n" if header_title else ""
        self.txt_output.setText(f"{current_text}{prefix}{header}{page_res.text}")

        if page_res.equations:
            math_text = self.txt_math_output.toPlainText()
            m_prefix = "\n\n" if math_text else ""
            m_lines = "\n".join(page_res.equations)
            self.txt_math_output.setText(f"{math_text}{m_prefix}% معادلات {header_title}:\n{m_lines}")

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
                self.lbl_progress_status.setText("اكتملت العملية، وأصبح النص جاهزاً.")
            else:
                self.lbl_progress_status.setText("فشلت معالجة بعض أو كل أجزاء الملف.")

            self.progress_bar.setValue(100)

            # Update statistics
            avg_conf = self.current_doc_result.average_confidence
            self.lbl_stat_conf.setText(f"متوسط الثقة: {avg_conf:.1f}%")
            if avg_conf < 50.0 and avg_conf > 0:
                self.lbl_stat_conf.setStyleSheet("color: #F59E0B; font-weight: bold;")
            else:
                self.lbl_stat_conf.setStyleSheet("color: #10B981; font-weight: bold;")

            self.lbl_stat_pages.setText(f"الصفحات / الأقسام: {self.current_doc_result.total_pages}")
            self.lbl_method_badge.setText(f"طريقة المعالجة: {self.current_doc_result.method_display_name}")

            # Populate combo pages if multi-section
            if len(self.current_doc_result.pages) > 1 and self.combo_pages.count() <= 1:
                self.combo_pages.clear()
                for p in self.current_doc_result.pages:
                    title = p.title or f"الصفحة {p.page_number}"
                    self.combo_pages.addItem(title, p.page_number)
                self.combo_pages.setEnabled(True)

            if self.current_doc_result.all_equations:
                self.results_tabs.setTabText(
                    1, f"المعادلات ({len(self.current_doc_result.all_equations)})"
                )

        self._update_text_counts()

    def _on_error(self, err: str):
        QMessageBox.critical(self, "خطأ في المعالجة", err)
        self._on_all_finished([])

    def _update_text_counts(self):
        text = self.txt_output.toPlainText()
        chars = len(text)
        words = len(text.split())
        self.lbl_stat_chars.setText(f"الحروف: {chars:,}")
        self.lbl_stat_words.setText(f"الكلمات: {words:,}")

    def _select_another_file(self):
        self.change_file_requested.emit()

    def _copy_all_text(self):
        text = self.txt_output.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "تنبيه", "لم نعثر على نص قابل للاستخراج في هذا الملف.")
            return
        clipboard: QClipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "تم النسخ", "تم نسخ النص كاملاً إلى الحافظة بنجاح.")

    def _copy_current_page_text(self):
        if not self.current_doc_result:
            return
        idx = self.combo_pages.currentIndex()
        if 0 <= idx < len(self.current_doc_result.pages):
            page_text = self.current_doc_result.pages[idx].text.strip()
            if page_text:
                clipboard: QClipboard = QGuiApplication.clipboard()
                clipboard.setText(page_text)
                title = self.current_doc_result.pages[idx].title or f"الصفحة {idx + 1}"
                QMessageBox.information(self, "تم النسخ", f"تم نسخ نص [{title}] إلى الحافظة.")
            else:
                QMessageBox.information(self, "تنبيه", "لم نعثر على نص قابل للاستخراج في هذا القسم.")

    def _export_txt(self):
        text = self.txt_output.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "تنبيه", "لم نعثر على نص قابل للاستخراج لتصديره.")
            return

        default_name = f"{self.current_file.stem}_extracted.txt" if self.current_file else "extracted.txt"
        path, _ = QFileDialog.getSaveFileName(self, "حفظ النص المستخرج كـ TXT", default_name, "ملف نصي (*.txt)")
        if path:
            try:
                if self.current_doc_result:
                    ExportService.export_to_txt(self.current_doc_result, Path(path))
                else:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(text)
                QMessageBox.information(self, "تم التصدير", f"تم حفظ ملف TXT بنجاح في:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ في الحفظ", f"تعذر حفظ الملف: {e}")

    def _export_docx(self):
        text = self.txt_output.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "تنبيه", "لم نعثر على نص قابل للاستخراج لتصديره.")
            return

        default_name = f"{self.current_file.stem}_extracted.docx" if self.current_file else "extracted.docx"
        path, _ = QFileDialog.getSaveFileName(self, "حفظ النص المستخرج كـ Word", default_name, "مستند Word (*.docx)")
        if path:
            try:
                if self.current_doc_result:
                    ExportService.export_to_docx(self.current_doc_result, Path(path))
                else:
                    from nass.core.models import DocumentResult, PageResult
                    dummy_page = PageResult(page_number=1, text=text)
                    doc_res = DocumentResult(
                        file_path=self.current_file or Path("extracted.docx"),
                        pages=[dummy_page],
                    )
                    ExportService.export_to_docx(doc_res, Path(path))
                QMessageBox.information(self, "تم التصدير", f"تم حفظ مستند Word بنجاح في:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ في الحفظ", f"تعذر حفظ الملف: {e}")

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
        self.btn_start.setText(tr("extract_btn_start"))
        self.btn_cancel.setText(tr("extract_btn_stop"))
        self.btn_copy_all.setText(tr("extract_btn_copy_all"))
        self.btn_copy_page.setText(tr("extract_btn_copy_page"))
        self.btn_export_txt.setText(tr("extract_btn_export_txt"))
        self.btn_export_docx.setText(tr("extract_btn_export_docx"))

        if not self.current_file:
            self.lbl_file_name.setText(tr("extract_no_file_title"))
            self.lbl_file_meta.setText(tr("extract_no_file_desc"))
            self.lbl_progress_status.setText(tr("extract_status_waiting"))

