"""
Asynchronous background worker executing document processing tasks via PySide6 QThread.
Maintains a responsive UI, dispatches real-time progress signals, and enables cooperative cancellation.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QThread, Signal

from nass.core.models import DocumentResult, OcrOptions, PageResult
from nass.services.processing_service import ProcessingService
from nass.utils.logger import logger


class OcrWorker(QThread):
    """Background worker thread for asynchronous document and image processing."""

    started_processing = Signal(int)
    file_started = Signal(int, int, str)
    page_progress = Signal(int, int, int, object)  # (file_num, page_num, total_pages, PageResult)
    file_finished = Signal(int, int, object)  # (file_num, total_files, DocumentResult)
    overall_progress = Signal(int, str)  # (percentage, status_text)
    all_finished = Signal(list)  # (List[DocumentResult])
    cancelled = Signal()
    error_occurred = Signal(str)

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
        """Request cooperative cancellation between pages and documents."""
        logger.info("Cancellation requested by user.")
        self._is_cancelled = True

    def is_cancelled(self) -> bool:
        """Check whether cancellation was requested."""
        return self._is_cancelled

    def run(self):
        """Execute processing pipeline for all queued files."""
        total_files = len(self.files)
        if total_files == 0:
            self.overall_progress.emit(100, "لا توجد ملفات للمعالجة.")
            self.all_finished.emit([])
            return

        self.started_processing.emit(total_files)
        self.overall_progress.emit(0, "بدء استخراج النصوص...")

        all_results: List[DocumentResult] = []

        try:
            for file_idx, file_path in enumerate(self.files):
                if self._is_cancelled:
                    logger.info("Worker stopped due to cancellation.")
                    break

                current_file_num = file_idx + 1
                self.file_started.emit(current_file_num, total_files, str(file_path))

                file_percent = int(((file_idx) / total_files) * 100)
                self.overall_progress.emit(
                    file_percent,
                    f"نقرأ محتوى ملفك الآن ({current_file_num} من {total_files}): {file_path.name}"
                )

                def on_page_progress(page_num: int, total_pages: int, page_res: PageResult):
                    self.page_progress.emit(current_file_num, page_num, total_pages, page_res)
                    if total_pages > 0:
                        inner_fraction = (page_num / total_pages) / total_files
                        total_pct = int(((file_idx / total_files) + inner_fraction) * 100)
                        self.overall_progress.emit(
                            min(99, total_pct),
                            f"نقرأ محتوى ملفك الآن: {file_path.name} — الصفحة {page_num} من {total_pages}"
                        )

                doc_result = self.processing_service.process_document(
                    file_path=file_path,
                    options=self.options,
                    page_callback=on_page_progress,
                    cancel_check=self.is_cancelled,
                )

                all_results.append(doc_result)
                self.file_finished.emit(current_file_num, total_files, doc_result)

            if self._is_cancelled:
                self.overall_progress.emit(100, "تم إيقاف المعالجة.")
                self.cancelled.emit()
            else:
                self.overall_progress.emit(100, "اكتملت العملية، وأصبح النص جاهزاً.")

            self.all_finished.emit(all_results)

        except Exception as e:
            logger.error(f"Fatal worker error during processing: {e}")
            self.error_occurred.emit(f"خطأ أثناء المعالجة: {e}")
