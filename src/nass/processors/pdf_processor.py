"""
PDF document extractor for NASS.
Implements intelligent hybrid processing: native embedded text extraction, page-level OCR for scanned documents,
and extraction of embedded images within PDF pages with OCR.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, List, Optional, Tuple

import fitz  # PyMuPDF
from PIL import Image

from nass.core.config import PDF_EXTENSIONS
from nass.core.models import (
    DocumentResult,
    ExtractionMethod,
    FileType,
    OcrOptions,
    PageResult,
    ProcessingStatus,
)
from nass.engines.base import BaseExtractor
from nass.engines.ocr.ocr_engine import OcrEngine
from nass.processors.image_processor import ImageProcessor
from nass.services.image_ocr_service import DocumentImageOcrService, ExtractedImageItem
from nass.utils.logger import logger


class PdfProcessor:
    """PDF helper utilities for metadata inspection and page rendering."""

    @staticmethod
    def get_document_info(file_path: Path) -> Tuple[int, bool, bool]:
        """
        Extract high-level info: (page_count, is_encrypted, has_embedded_text).
        """
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            doc = fitz.open(str(file_path))
        except Exception as e:
            raise ValueError(f"Could not open PDF file (may be corrupted): {e}")

        try:
            if doc.is_encrypted:
                return 0, True, False

            page_count = len(doc)
            if page_count == 0:
                return 0, False, False

            has_text = False
            sample_count = min(3, page_count)
            for i in range(sample_count):
                try:
                    page = doc[i]
                    text = page.get_text().strip()
                    if len(text) > 30:
                        has_text = True
                        break
                except Exception:
                    pass

            return page_count, False, has_text
        finally:
            doc.close()

    @staticmethod
    def extract_embedded_text_page(page) -> str:
        """Extract native digital text embedded in a PDF page."""
        return page.get_text("text").strip()

    @staticmethod
    def render_page_to_image(page, dpi: int = 300) -> Image.Image:
        """
        Render a PDF page to a PIL Image at specified DPI.
        Frees intermediate pixmap immediately to prevent memory leaks.
        """
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        try:
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            return img
        finally:
            pix = None


class PdfExtractor(BaseExtractor):
    """Unified extractor for PDF documents supporting native, page OCR, and embedded image OCR."""

    def __init__(
        self,
        ocr_engine: Optional[OcrEngine] = None,
        image_ocr_service: Optional[DocumentImageOcrService] = None,
    ):
        self.ocr_engine = ocr_engine or OcrEngine()
        self.image_ocr_service = image_ocr_service or DocumentImageOcrService(ocr_engine=self.ocr_engine)

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in PDF_EXTENSIONS

    @property
    def extraction_method(self) -> ExtractionMethod:
        return ExtractionMethod.HYBRID

    def extract(
        self,
        file_path: Path,
        options: OcrOptions,
        progress_callback: Optional[Callable[[int, int, PageResult], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> DocumentResult:
        start_time = time.time()
        file_size = file_path.stat().st_size if file_path.exists() else 0

        doc_result = DocumentResult(
            file_path=file_path,
            file_type=FileType.PDF,
            file_size_bytes=file_size,
            status=ProcessingStatus.PROCESSING,
        )

        try:
            doc = fitz.open(str(file_path))
        except Exception as e:
            doc_result.status = ProcessingStatus.FAILED
            doc_result.error_message = f"Could not open PDF file: {e}"
            doc_result.total_duration_seconds = time.time() - start_time
            return doc_result

        try:
            if doc.is_encrypted:
                doc_result.status = ProcessingStatus.FAILED
                doc_result.error_message = "ملف PDF محمي بكلمة مرور وغير قابل للقراءة."
                return doc_result

            total_pages = len(doc)
            doc_result.total_pages = total_pages

            if total_pages == 0:
                doc_result.status = ProcessingStatus.FAILED
                doc_result.error_message = "ملف PDF لا يحتوي على أي صفحات."
                return doc_result

            used_native = False
            used_ocr = False

            for page_idx in range(total_pages):
                if cancel_check and cancel_check():
                    logger.info(f"PDF processing cancelled for {file_path.name}")
                    doc_result.status = ProcessingStatus.CANCELLED
                    break

                page_num = page_idx + 1
                page_start_time = time.time()
                page_result = PageResult(page_number=page_num, status=ProcessingStatus.PROCESSING)

                try:
                    fitz_page = doc[page_idx]

                    # 1. Native text extraction
                    embedded_text = ""
                    if options.extract_native_text and options.extract_embedded_first:
                        embedded_text = PdfProcessor.extract_embedded_text_page(fitz_page)

                    native_found = bool(embedded_text and len(embedded_text.strip()) > 30)

                    # 2. Embedded images within page or whole-page OCR
                    image_ocr_blocks = []
                    page_image_items: List[ExtractedImageItem] = []

                    if native_found:
                        page_result.native_text = embedded_text.strip()
                        page_result.is_embedded_text = True
                        page_result.confidence = 100.0
                        page_result.status = ProcessingStatus.COMPLETED
                        page_result.extraction_method = ExtractionMethod.NATIVE
                        used_native = True

                        # If user also wants OCR on images embedded inside native PDF
                        if options.extract_images_ocr:
                            raw_images = fitz_page.get_images(full=True)
                            for img_idx, item in enumerate(raw_images, start=1):
                                try:
                                    xref = item[0]
                                    base_img = doc.extract_image(xref)
                                    if base_img and "image" in base_img:
                                        img_item = ExtractedImageItem(
                                            item_id=f"pdf_p{page_num}_img_{img_idx}",
                                            source_location=f"صفحة PDF {page_num} - صورة #{img_idx}",
                                            image_bytes=base_img["image"],
                                            format=base_img.get("ext", "png").upper(),
                                            page_or_section=page_num,
                                            order_in_section=img_idx,
                                        )
                                        page_image_items.append(img_item)
                                except Exception as im_err:
                                    logger.warning(f"Failed to extract image {img_idx} from PDF page {page_num}: {im_err}")

                            if page_image_items:
                                self.image_ocr_service.process_image_items_batch(
                                    page_image_items,
                                    options=options,
                                    cancel_check=cancel_check,
                                )
                                for p_im in page_image_items:
                                    if p_im.ocr_text:
                                        image_ocr_blocks.append(
                                            f"[{p_im.source_location} - استخراج OCR]:\n{p_im.ocr_text}"
                                        )
                                if image_ocr_blocks:
                                    used_ocr = True
                                    page_result.extraction_method = ExtractionMethod.HYBRID

                        image_ocr_text = "\n\n".join(image_ocr_blocks).strip()
                        page_result.image_ocr_text = image_ocr_text

                        # Combine
                        if image_ocr_text:
                            page_result.text = f"{page_result.native_text}\n\n[النصوص المستخرجة من صور الصفحة (OCR)]:\n{image_ocr_text}"
                        else:
                            page_result.text = page_result.native_text

                        if options.extract_math:
                            try:
                                from nass.engines.ocr.math_engine import MathRecognitionService
                                math_service = MathRecognitionService(preferred_engine=options.math_engine)
                                eqs = math_service.extract_equations(text_context=page_result.text)
                                page_result.equations = [eq.latex for eq in eqs]
                            except Exception as m_err:
                                logger.warning(f"Math extraction failed for page {page_num}: {m_err}")

                    else:
                        # Scanned page: Perform full-page OCR
                        page_img = PdfProcessor.render_page_to_image(fitz_page, dpi=options.dpi)
                        enhanced_img = ImageProcessor.process(page_img, options)

                        effective_psm = 4 if options.single_column else options.psm

                        ocr_res = self.ocr_engine.extract_text(
                            image=enhanced_img,
                            language=options.language,
                            psm=effective_psm,
                            oem=options.oem,
                            extra_config=options.tesseract_config,
                            page_number=page_num,
                        )
                        page_result.text = ocr_res.text.strip()
                        page_result.image_ocr_text = ocr_res.text.strip()
                        page_result.confidence = ocr_res.confidence
                        page_result.status = ocr_res.status
                        page_result.extraction_method = ExtractionMethod.OCR
                        page_result.is_embedded_text = False
                        used_ocr = True

                        if options.extract_math and page_result.status == ProcessingStatus.COMPLETED:
                            try:
                                from nass.engines.ocr.math_engine import MathRecognitionService
                                math_service = MathRecognitionService(preferred_engine=options.math_engine)
                                eqs = math_service.extract_equations(image=enhanced_img, text_context=page_result.text)
                                page_result.equations = [eq.latex for eq in eqs]
                            except Exception as m_err:
                                logger.warning(f"Math extraction failed for page {page_num}: {m_err}")

                    page_result.image_count = len(page_image_items)
                    page_result.image_details = [
                        {
                            "item_id": item.item_id,
                            "location": item.source_location,
                            "status": item.status.value,
                            "confidence": item.confidence,
                            "error": item.error_message,
                            "has_text": bool(item.ocr_text),
                        }
                        for item in page_image_items
                    ]
                    page_result.duration_seconds = time.time() - page_start_time

                except Exception as p_err:
                    logger.error(f"Error processing page {page_num} in {file_path.name}: {p_err}")
                    page_result.status = ProcessingStatus.FAILED
                    page_result.error_message = str(p_err)
                    page_result.duration_seconds = time.time() - page_start_time

                doc_result.pages.append(page_result)

                if progress_callback:
                    progress_callback(page_num, total_pages, page_result)

            if doc_result.status != ProcessingStatus.CANCELLED:
                doc_result.status = ProcessingStatus.COMPLETED

            if used_native and used_ocr:
                doc_result.extraction_method = ExtractionMethod.HYBRID
            elif used_native:
                doc_result.extraction_method = ExtractionMethod.NATIVE
            else:
                doc_result.extraction_method = ExtractionMethod.OCR

        except Exception as doc_err:
            logger.error(f"Unexpected error processing PDF {file_path.name}: {doc_err}")
            doc_result.status = ProcessingStatus.FAILED
            doc_result.error_message = str(doc_err)
        finally:
            doc.close()
            doc_result.total_duration_seconds = time.time() - start_time

        return doc_result
