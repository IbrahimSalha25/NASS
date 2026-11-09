"""
النافذة الرئيسية لتطبيق نَصّ (NASS) — PySide6 بتخطيط RTL وتجربة مستخدم عصرية.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard, QGuiApplication, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.config import PROJECT_ROOT

from app.core.file_manager import FileManager
from app.core.models import DocumentResult, OcrOptions, PageResult, ProcessingStatus
from app.core.ocr_engine import OcrEngine
from app.services.export_service import ExportService
from app.ui.components.drop_zone import DropZoneWidget
from app.ui.components.file_table import FileTableWidget
from app.ui.components.options_bar import OptionsBarWidget
from app.ui.styles import APP_STYLESHEET
from app.utils.logger import logger
from app.workers.ocr_worker import OcrWorker


class MainWindow(QMainWindow):
    """النافذة الأساسية لتطبيق نَصّ."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("نَصّ | NASS — من الصورة إلى النص")
        self.resize(1180, 780)
        self.setMinimumSize(950, 600)
        self.setLayoutDirection(Qt.RightToLeft)

        # تهيئة المحرك وحالة التطبيق
        self.ocr_engine = OcrEngine()
        self.engine_status = self.ocr_engine.get_status()
        self.loaded_files: List[Path] = []
        self.results_map: Dict[int, DocumentResult] = {}
        self.current_worker: Optional[OcrWorker] = None

        # بناء الواجهة
        self._init_ui()
        self._update_engine_status_badge()
        self.setStyleSheet(APP_STYLESHEET)

    def _init_ui(self):
        """بناء تخطيط عناصر الواجهة الرئيسية."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. الشريط العلوي (الهوية، الشعار، وحالة Tesseract)
        header_frame = QFrame()
        header_frame.setObjectName("cardFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(12)

        # شعار التطبيق وأيقونة النافذة
        logo_path = PROJECT_ROOT / "logo_NASS.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))
            logo_label = QLabel()
            pixmap = QPixmap(str(logo_path)).scaled(
                44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_label.setPixmap(pixmap)
            header_layout.addWidget(logo_label)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        app_title = QLabel("نَصّ | NASS")
        app_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E5E8A;")
        app_sub = QLabel("من الصورة إلى النص — استخراج النصوص محلياً بدقة وأمان")
        app_sub.setStyleSheet("font-size: 12px; color: #64748B;")
        title_box.addWidget(app_title)
        title_box.addWidget(app_sub)

        # شارة حالة المحرك
        self.badge_engine = QLabel("جاري التحقق من محرك OCR...")
        self.badge_engine.setStyleSheet(
            "padding: 6px 12px; border-radius: 6px; font-weight: bold; background-color: #F1F5F9; color: #475569;"
        )

        header_layout.addLayout(title_box)
        header_layout.addStretch()
        header_layout.addWidget(self.badge_engine)
        main_layout.addWidget(header_frame)

        # 2. منطقة العمل الرئيسية (مقسمة بين الإدخال والنتائج)
        splitter = QSplitter(Qt.Horizontal)

        # الجانب الأيمن: إضافة الملفات والجدول والخيارات
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # منطقة السحب والإفلات
        self.drop_zone = DropZoneWidget()
        self.drop_zone.files_selected.connect(self._on_files_added)
        right_layout.addWidget(self.drop_zone)

        # جدول الملفات المضافة
        self.file_table = FileTableWidget()
        self.file_table.file_removed.connect(self._on_file_removed)
        self.file_table.file_selected.connect(self._on_file_selected)
        right_layout.addWidget(self.file_table)

        # شريط الخيارات المتقدمة (اللغة، الجودة، التحسين)
        self.options_bar = OptionsBarWidget(
            available_languages=self.engine_status.get("languages", [])
        )
        right_layout.addWidget(self.options_bar)

        # أزرار الإجراءات
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.btn_start = QPushButton("بدء استخراج النصوص")
        self.btn_start.setObjectName("primaryButton")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self._start_ocr_processing)

        self.btn_cancel = QPushButton("إلغاء المعالجة")
        self.btn_cancel.setObjectName("dangerButton")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel_ocr_processing)

        self.btn_clear = QPushButton("مسح القائمة")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self._clear_all_files)

        actions_layout.addWidget(self.btn_start)
        actions_layout.addWidget(self.btn_cancel)
        actions_layout.addWidget(self.btn_clear)
        right_layout.addLayout(actions_layout)

        # شريط التقدم وحالة العملية
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.lbl_status = QLabel("جاهز لإضافة الملفات والبدء")
        self.lbl_status.setStyleSheet("color: #64748B; font-size: 12px;")

        right_layout.addWidget(self.progress_bar)
        right_layout.addWidget(self.lbl_status)

        # الجانب الأيسر: مستعرض ومحرر النصوص والنتائج
        left_panel = QFrame()
        left_panel.setObjectName("cardFrame")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        results_header = QHBoxLayout()
        self.lbl_results_title = QLabel("معاينة النص المستخرج:")
        self.lbl_results_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B;")
        results_header.addWidget(self.lbl_results_title)
        results_header.addStretch()

        self.btn_copy = QPushButton("نسخ النص")
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.clicked.connect(self._copy_results_to_clipboard)

        self.btn_export_txt = QPushButton("حفظ كـ TXT")
        self.btn_export_txt.setCursor(Qt.PointingHandCursor)
        self.btn_export_txt.clicked.connect(self._export_to_txt)

        self.btn_export_docx = QPushButton("تصدير كـ Word")
        self.btn_export_docx.setCursor(Qt.PointingHandCursor)
        self.btn_export_docx.clicked.connect(self._export_to_docx)

        results_header.addWidget(self.btn_copy)
        results_header.addWidget(self.btn_export_txt)
        results_header.addWidget(self.btn_export_docx)
        left_layout.addLayout(results_header)

        # محرر وعارض النصوص
        self.txt_result = QTextEdit()
        self.txt_result.setPlaceholderText(
            "سيظهر هنا النص المستخرج من المستندات والصور...\nيمكنك مراجعته وتحريره ونسخه أو تصديره مباشرة."
        )
        self.txt_result.setLayoutDirection(Qt.RightToLeft)
        left_layout.addWidget(self.txt_result)

        # إضافة الجانبين إلى المقسم وتحديد النسب
        splitter.addWidget(right_panel)
        splitter.addWidget(left_panel)
        splitter.setSizes([600, 500])

        main_layout.addWidget(splitter)

    def _update_engine_status_badge(self):
        """تحديث شارة Tesseract في الشريط العلوي بناءً على الحالة الحقيقية."""
        if not self.engine_status.get("is_available"):
            self.badge_engine.setText("تنبيه: محرك Tesseract غير مثبت أو غير متاح")
            self.badge_engine.setStyleSheet(
                "padding: 6px 12px; border-radius: 6px; font-weight: bold; background-color: #FEF2F2; color: #EF4444;"
            )
            return

        langs = self.engine_status.get("languages", [])
        has_ara = "ara" in langs
        has_eng = "eng" in langs

        if has_ara and has_eng:
            self.badge_engine.setText(f"محرك Tesseract جاهز (العربية + الإنجليزية) v{self.engine_status.get('version', '')}")
            self.badge_engine.setStyleSheet(
                "padding: 6px 12px; border-radius: 6px; font-weight: bold; background-color: #ECFDF5; color: #10B981;"
            )
        elif has_ara or has_eng:
            available_str = "العربية" if has_ara else "الإنجليزية"
            self.badge_engine.setText(f"محرك Tesseract متاح جزئياً ({available_str} فقط)")
            self.badge_engine.setStyleSheet(
                "padding: 6px 12px; border-radius: 6px; font-weight: bold; background-color: #FFFBEB; color: #F59E0B;"
            )
        else:
            self.badge_engine.setText("محرك Tesseract متاح ولكن تنقصه ملفات اللغات")
            self.badge_engine.setStyleSheet(
                "padding: 6px 12px; border-radius: 6px; font-weight: bold; background-color: #FFFBEB; color: #F59E0B;"
            )

    def _on_files_added(self, paths: List[Path]):
        """استكشاف وإضافة مسارات الملفات والمجلدات المحددة."""
        discovered = FileManager.discover_files(paths)
        if not discovered:
            self.lbl_status.setText("لم يتم العثور على ملفات صور أو PDF مدعومة في المسارات المحددة.")
            return

        added_count = 0
        for file_path in discovered:
            if file_path not in self.loaded_files:
                self.loaded_files.append(file_path)
                self.file_table.add_file_row(file_path)
                added_count += 1

        self.btn_start.setEnabled(len(self.loaded_files) > 0)
        self.lbl_status.setText(f"تمت إضافة {added_count} ملفات جديدة. الإجمالي: {len(self.loaded_files)} ملف.")

    def _on_file_removed(self, index: int):
        """معالجة حذف ملف من الجدول والقائمة."""
        if 0 <= index < len(self.loaded_files):
            removed_file = self.loaded_files.pop(index)
            self.results_map.pop(index, None)
            self.btn_start.setEnabled(len(self.loaded_files) > 0)
            self.lbl_status.setText(f"تمت إزالة: {removed_file.name}")

    def _clear_all_files(self):
        """مسح كافة الملفات والنتائج من القائمة."""
        self.loaded_files.clear()
        self.results_map.clear()
        self.file_table.setRowCount(0)
        self.txt_result.clear()
        self.btn_start.setEnabled(False)
        self.progress_bar.setValue(0)
        self.lbl_status.setText("تم تفريغ القائمة.")

    def _on_file_selected(self, index: int):
        """عرض النتائج الخاصة بالملف الذي ضغط عليه المستخدم في الجدول."""
        if index in self.results_map:
            doc_res = self.results_map[index]
            self.lbl_results_title.setText(f"معاينة: {doc_res.file_path.name}")
            self.txt_result.setText(doc_res.full_text)

    def _start_ocr_processing(self):
        """بدء عملية الاستخراج في خيط خلفي منفصل."""
        if not self.loaded_files:
            return

        options = self.options_bar.get_options()

        # قفل عناصر التحكم أثناء العمل
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_clear.setEnabled(False)
        self.drop_zone.setEnabled(False)
        self.options_bar.setEnabled(False)

        # إنشاء خيط العامل
        self.current_worker = OcrWorker(files=list(self.loaded_files), options=options)
        self.current_worker.file_started.connect(self._on_worker_file_started)
        self.current_worker.page_progress.connect(self._on_worker_page_progress)
        self.current_worker.file_finished.connect(self._on_worker_file_finished)
        self.current_worker.overall_progress.connect(self._on_worker_overall_progress)
        self.current_worker.all_finished.connect(self._on_worker_all_finished)
        self.current_worker.error_occurred.connect(self._on_worker_error)

        self.current_worker.start()

    def _cancel_ocr_processing(self):
        """طلب إلغاء العملية الجارية."""
        if self.current_worker and self.current_worker.isRunning():
            self.lbl_status.setText("جاري إيقاف المعالجة بأمان...")
            self.current_worker.cancel()
            self.btn_cancel.setEnabled(False)

    def _on_worker_file_started(self, current_file: int, total_files: int, file_path_str: str):
        row_idx = current_file - 1
        self.file_table.update_file_status(row_idx, ProcessingStatus.PROCESSING)

    def _on_worker_page_progress(self, file_idx: int, page_num: int, total_pages: int, page_res: PageResult):
        # تحديث النص اللحظي إذا كان المستخدم يشاهد هذا الملف
        row_idx = file_idx - 1
        if page_res.text:
            current_text = self.txt_result.toPlainText()
            prefix = "\n\n" if current_text else ""
            self.txt_result.setText(f"{current_text}{prefix}--- [صفحة {page_num}] ---\n{page_res.text}")

    def _on_worker_file_finished(self, current_file: int, total_files: int, doc_result: DocumentResult):
        row_idx = current_file - 1
        self.results_map[row_idx] = doc_result
        self.file_table.update_file_status(
            row_idx=row_idx,
            status=doc_result.status,
            pages_count=doc_result.total_pages,
            confidence=doc_result.average_confidence,
            error_msg=doc_result.error_message,
        )

    def _on_worker_overall_progress(self, percentage: int, message: str):
        self.progress_bar.setValue(percentage)
        self.lbl_status.setText(message)

    def _on_worker_all_finished(self, results: List[DocumentResult]):
        """استعادة حالة الأزرار وعرض التقرير النهائي."""
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_clear.setEnabled(True)
        self.drop_zone.setEnabled(True)
        self.options_bar.setEnabled(True)

        # تجميع النص النهائي الكامل لكل الملفات
        all_texts = [r.full_text for r in results if r.full_text.strip()]
        if all_texts:
            self.txt_result.setText("\n\n" + "=" * 50 + "\n\n".join(all_texts))
            self.lbl_results_title.setText(f"النتائج المجمعة ({len(results)} ملفات)")

    def _on_worker_error(self, err_msg: str):
        QMessageBox.critical(self, "خطأ في المعالجة", err_msg)
        self._on_worker_all_finished([])

    def _copy_results_to_clipboard(self):
        """نسخ النص الظاهر حالياً إلى الحافظة."""
        text = self.txt_result.toPlainText().strip()
        if not text:
            self.lbl_status.setText("لا يوجد نص لنسخه.")
            return

        clipboard: QClipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        self.lbl_status.setText("تم نسخ النص بنجاح إلى الحافظة.")

    def _export_to_txt(self):
        """تصدير النتائج إلى ملف نصي UTF-8."""
        docs = list(self.results_map.values())
        if not docs:
            # إذا لم توجد كائنات بيانات، نأخذ النص من المحرر
            text = self.txt_result.toPlainText().strip()
            if not text:
                QMessageBox.information(self, "تنبيه", "لا توجد نتائج نصوص لتصديرها.")
                return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ النص المستخرج",
            "extracted_text.txt",
            "ملفات نصية (*.txt);;جميع الملفات (*.*)",
        )
        if file_path:
            try:
                if docs:
                    ExportService.export_to_txt(docs, Path(file_path))
                else:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(self.txt_result.toPlainText())
                QMessageBox.information(self, "نجاح التصدير", f"تم حفظ الملف النصي بنجاح في:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ في التصدير", f"تعذر حفظ الملف: {e}")

    def _export_to_docx(self):
        """تصدير النتائج إلى مستند Word (DOCX)."""
        docs = list(self.results_map.values())
        if not docs:
            QMessageBox.information(self, "تنبيه", "يرجى إتمام استخراج النصوص قبل التصدير إلى Word.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "تصدير إلى مستند Word",
            "extracted_document.docx",
            "مستندات وورد (*.docx);;جميع الملفات (*.*)",
        )
        if file_path:
            try:
                ExportService.export_to_docx(docs, Path(file_path))
                QMessageBox.information(self, "نجاح التصدير", f"تم إنشاء مستند Word بنجاح في:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ في التصدير", f"تعذر حفظ مستند Word: {e}")
