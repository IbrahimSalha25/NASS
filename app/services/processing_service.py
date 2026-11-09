"""
خدمة تنسيق معالجة المستندات والصور وإدارة تدفق العمل.
مستقلة تماماً عن الواجهة الرسومية وتدعم الإلغاء والتقارير المرحلية.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, List, Optional

from PIL import Image

from app.core.file_manager import FileManager
from app.core.image_processor import ImageProcessor
from app.core.models import (
    DocumentResult,
    FileType,
    OcrOptions,
    PageResult,
    ProcessingStatus,
)
from app.core.ocr_engine import OcrEngine
from app.core.pdf_processor import PdfProcessor
from app.utils.logger import logger


class ProcessingService:
    """خدمة المعالجة الرئيسية لملفات الصور والـ PDF."""

    def __init__(self, ocr_engine: Optional[OcrEngine] = None):
        self.ocr_engine = ocr_engine or OcrEngine()

    def process_image_file(
        self,
        file_path: Path,
        options: OcrOptions,
    ) -> DocumentResult:
        """معالجة ملف صورة فردي."""
        start_time = time.time()
        file_size = file_path.stat().st_size if file_path.exists() else 0

        doc_result = DocumentResult(
            file_path=file_path,
            file_type=FileType.IMAGE,
            file_size_bytes=file_size,
            total_pages=1,
            status=ProcessingStatus.PROCESSING,
        )

        try:
            with Image.open(file_path) as raw_img:
                # التأكد من نمط الألوان
                img = raw_img.convert("RGB") if raw_img.mode not in ("RGB", "L") else raw_img.copy()

            # تطبيق التحسينات الاختيارية
            processed_img = ImageProcessor.process(img, options)

            # تنفيذ OCR
            page_res = self.ocr_engine.extract_text(
                image=processed_img,
                language=options.language,
                page_number=1,
            )

            doc_result.pages = [page_res]
            doc_result.status = page_res.status
            if page_res.status == ProcessingStatus.FAILED:
                doc_result.error_message = page_res.error_message

        except Exception as e:
            logger.error(f"خطأ أثناء معالجة الصورة {file_path.name}: {e}")
            doc_result.status = ProcessingStatus.FAILED
            doc_result.error_message = str(e)
            doc_result.pages = [
                PageResult(
                    page_number=1,
                    status=ProcessingStatus.FAILED,
                    error_message=str(e),
                )
            ]
        finally:
            doc_result.total_duration_seconds = time.time() - start_time

        return doc_result

    def process_pdf_file(
        self,
        file_path: Path,
        options: OcrOptions,
        progress_callback: Optional[Callable[[int, int, PageResult], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> DocumentResult:
        """معالجة مستند PDF صفحة بصفحة بكفاءة عالية."""
        import fitz

        start_time = time.time()
        file_size = file_path.stat().st_size if file_path.exists() else 0

        doc_result = DocumentResult(
            file_path=file_path,
            file_type=FileType.PDF,
            file_size_bytes=file_size,
            status=ProcessingStatus.PROCESSING,
        )

        # 1. فحص المستند الأساسي
        try:
            total_pages, is_encrypted, _ = PdfProcessor.get_document_info(file_path)
            doc_result.total_pages = total_pages

            if is_encrypted:
                doc_result.status = ProcessingStatus.FAILED
                doc_result.error_message = "ملف PDF محمي بكلمة مرور."
                return doc_result

            if total_pages == 0:
                doc_result.status = ProcessingStatus.FAILED
                doc_result.error_message = "ملف PDF فارغ ولا يحتوي على صفحات."
                return doc_result
        except Exception as e:
            doc_result.status = ProcessingStatus.FAILED
            doc_result.error_message = f"تعذر قراءة ملف PDF: {e}"
            return doc_result

        # 2. فتح المستند ومعالجة الصفحات تتابعياً
        doc = fitz.open(str(file_path))
        try:
            for page_idx in range(total_pages):
                # التحقق من طلب الإلغاء بين الصفحات
                if cancel_check and cancel_check():
                    logger.info(f"تم إلغاء معالجة ملف PDF {file_path.name} عند الصفحة {page_idx + 1}")
                    doc_result.status = ProcessingStatus.CANCELLED
                    break

                page_num = page_idx + 1
                page_start_time = time.time()
                fitz_page = doc[page_idx]
                page_result = PageResult(page_number=page_num, status=ProcessingStatus.PROCESSING)

                try:
                    # فحص النص المضمن إذا كان الخيار مفعلاً
                    embedded_text = ""
                    if options.extract_embedded_first:
                        embedded_text = PdfProcessor.extract_embedded_text_page(fitz_page)

                    if embedded_text and len(embedded_text.strip()) > 30:
                        # اعتماد النص المضمن دون الحاجة لـ OCR
                        page_result.text = embedded_text.strip()
                        page_result.is_embedded_text = True
                        page_result.confidence = 100.0
                        page_result.status = ProcessingStatus.COMPLETED
                        page_result.duration_seconds = time.time() - page_start_time
                    else:
                        # تحويل الصفحة لصورة بدقة DPI المحددة
                        page_img = PdfProcessor.render_page_to_image(fitz_page, dpi=options.dpi)
                        enhanced_img = ImageProcessor.process(page_img, options)

                        # تنفيذ OCR
                        page_result = self.ocr_engine.extract_text(
                            image=enhanced_img,
                            language=options.language,
                            page_number=page_num,
                        )

                except Exception as p_err:
                    logger.error(f"خطأ في معالجة الصفحة {page_num} من {file_path.name}: {p_err}")
                    page_result.status = ProcessingStatus.FAILED
                    page_result.error_message = str(p_err)
                    page_result.duration_seconds = time.time() - page_start_time

                doc_result.pages.append(page_result)

                if progress_callback:
                    progress_callback(page_num, total_pages, page_result)

            if doc_result.status != ProcessingStatus.CANCELLED:
                doc_result.status = ProcessingStatus.COMPLETED

        except Exception as doc_err:
            logger.error(f"خطأ غير متوقع أثناء معالجة صفحات {file_path.name}: {doc_err}")
            doc_result.status = ProcessingStatus.FAILED
            doc_result.error_message = str(doc_err)
        finally:
            doc.close()
            doc_result.total_duration_seconds = time.time() - start_time

        return doc_result

    def process_document(
        self,
        file_path: Path,
        options: OcrOptions,
        page_callback: Optional[Callable[[int, int, PageResult], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> DocumentResult:
        """توجيه الملف إلى المعالج المناسب (صورة أو PDF)."""
        file_type = FileManager.detect_file_type(file_path)

        if file_type == FileType.IMAGE:
            res = self.process_image_file(file_path, options)
            if page_callback and res.pages:
                page_callback(1, 1, res.pages[0])
            return res
        elif file_type == FileType.PDF:
            return self.process_pdf_file(
                file_path=file_path,
                options=options,
                progress_callback=page_callback,
                cancel_check=cancel_check,
            )
        else:
            return DocumentResult(
                file_path=file_path,
                file_type=FileType.UNKNOWN,
                file_size_bytes=0,
                status=ProcessingStatus.FAILED,
                error_message=f"نوع الملف غير مدعوم: {file_path.suffix}",
            )
