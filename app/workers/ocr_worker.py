"""
عامل المعالجة في الخلفية (Background Worker) باستخدام QThread وإشارات Qt.
يضمن عدم تجميد الواجهة الرسومية ويوفر إمكانية الإلغاء التعاوني الآمن.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QThread, Signal

from app.core.models import DocumentResult, OcrOptions, PageResult, ProcessingStatus
from app.services.processing_service import ProcessingService
from app.utils.logger import logger


class OcrWorker(QThread):
    """خيط عمل منفصل لتنفيذ عمليات استخراج النصوص في الخلفية."""

    # إشارات التواصل مع الواجهة
    started_processing = Signal(int)  # إجمالي عدد الملفات
    file_started = Signal(int, int, str)  # (رقم الملف الحالي, الإجمالي, مسار الملف)
    page_progress = Signal(int, int, int, object)  # (رقم الملف, رقم الصفحة, إجمالي الصفحات, PageResult)
    file_finished = Signal(int, int, object)  # (رقم الملف, الإجمالي, DocumentResult)
    overall_progress = Signal(int, str)  # (النسبة المئوية 0-100, نص الحالة)
    all_finished = Signal(list)  # (قائمة كافة DocumentResult)
    cancelled = Signal()  # إشعار بإتمام الإلغاء
    error_occurred = Signal(str)  # إشعار بالأخطاء العامة

    def __init__(
        self,
        files: List[Path],
        options: OcrOptions,
        parent=None,
    ):
        super().__init__(parent)
        self.files = files
        self.options = options
        self.processing_service = ProcessingService()
        self._is_cancelled = False

    def cancel(self):
        """طلب إلغاء العملية بأمان عند الانتقال بين الصفحات أو الملفات."""
        logger.info("تم طلب إلغاء المعالجة من واجهة المستخدم.")
        self._is_cancelled = True

    def is_cancelled(self) -> bool:
        """فحص حالة الإلغاء الحالية."""
        return self._is_cancelled

    def run(self):
        """نقطة انطلاق الخيط وتنفيذ معالجة قائمة الملفات."""
        total_files = len(self.files)
        if total_files == 0:
            self.overall_progress.emit(100, "لا توجد ملفات للمعالجة.")
            self.all_finished.emit([])
            return

        self.started_processing.emit(total_files)
        self.overall_progress.emit(0, "بدء المعالجة...")

        all_results: List[DocumentResult] = []

        try:
            for file_idx, file_path in enumerate(self.files):
                if self._is_cancelled:
                    logger.info("توقفت المعالجة بناءً على طلب الإلغاء.")
                    break

                current_file_num = file_idx + 1
                self.file_started.emit(current_file_num, total_files, str(file_path))

                # حساب النسبة المئوية التقريبية للملف الحالي
                file_percent = int(((file_idx) / total_files) * 100)
                self.overall_progress.emit(
                    file_percent,
                    f"جاري معالجة الملف ({current_file_num} من {total_files}): {file_path.name}"
                )

                # دالة استدعاء لكل صفحة
                def on_page_progress(page_num: int, total_pages: int, page_res: PageResult):
                    self.page_progress.emit(current_file_num, page_num, total_pages, page_res)
                    # تحديث نسبة التقدم الدقيقة
                    if total_pages > 0:
                        inner_fraction = (page_num / total_pages) / total_files
                        total_pct = int(((file_idx / total_files) + inner_fraction) * 100)
                        self.overall_progress.emit(
                            min(99, total_pct),
                            f"معالجة {file_path.name} — الصفحة {page_num} من {total_pages}"
                        )

                # معالجة الملف الفعلي
                doc_result = self.processing_service.process_document(
                    file_path=file_path,
                    options=self.options,
                    page_callback=on_page_progress,
                    cancel_check=self.is_cancelled,
                )

                all_results.append(doc_result)
                self.file_finished.emit(current_file_num, total_files, doc_result)

            if self._is_cancelled:
                self.overall_progress.emit(100, "تم إلغاء المعالجة.")
                self.cancelled.emit()
            else:
                self.overall_progress.emit(100, "اكتملت جميع العمليات بنجاح.")

            self.all_finished.emit(all_results)

        except Exception as e:
            logger.error(f"خطأ عام داخل عامل الخلفية OcrWorker: {e}", exc_info=True)
            self.error_occurred.emit(f"حدث خطأ غير متوقع: {e}")
