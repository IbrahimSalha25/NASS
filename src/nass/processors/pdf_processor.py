"""
PDF document extractor for NASS.
Implements intelligent hybrid processing: native embedded text extraction first, with OCR fallback for scanned pages.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Optional, Tuple

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
    """Unified extractor for PDF documents supporting native and OCR hybrid extraction."""

    def __init__(self, ocr_engine: Optional[OcrEngine] = None):
        self.ocr_engine = ocr_engine or OcrEngine()

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

                    embedded_text = ""
                    if options.extract_embedded_first:
                        embedded_text = PdfProcessor.extract_embedded_text_page(fitz_page)

                    if embedded_text and len(embedded_text.strip()) > 30:
                        page_result.text = embedded_text.strip()
                        page_result.is_embedded_text = True
                        page_result.confidence = 100.0
                        page_result.status = ProcessingStatus.COMPLETED
                        page_result.extraction_method = ExtractionMethod.NATIVE
                        page_result.duration_seconds = time.time() - page_start_time
                        used_native = True

                        if options.extract_math:
                            try:
                                from nass.engines.ocr.math_engine import MathRecognitionService
                                math_service = MathRecognitionService(preferred_engine=options.math_engine)
                                eqs = math_service.extract_equations(text_context=page_result.text)
                                page_result.equations = [eq.latex for eq in eqs]
                            except Exception as m_err:
                                logger.warning(f"Math extraction failed for page {page_num}: {m_err}")
                    else:
                        page_img = PdfProcessor.render_page_to_image(fitz_page, dpi=options.dpi)
                        enhanced_img = ImageProcessor.process(page_img, options)

                        effective_psm = 4 if options.single_column else options.psm

                        page_result = self.ocr_engine.extract_text(
                            image=enhanced_img,
                            language=options.language,
                            psm=effective_psm,
                            oem=options.oem,
                            extra_config=options.tesseract_config,
                            page_number=page_num,
                        )
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
