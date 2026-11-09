"""
Microsoft Word (DOCX) document text extractor for NASS.
Extracts headings, paragraphs, and tables preserving document flow.
Supports extracting embedded images and performing OCR with provenance metadata.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, List, Optional

from nass.core.config import WORD_EXTENSIONS
from nass.core.models import (
    DocumentResult,
    ExtractionMethod,
    FileType,
    OcrOptions,
    PageResult,
    ProcessingStatus,
)
from nass.engines.base import BaseExtractor
from nass.services.image_ocr_service import DocumentImageOcrService, ExtractedImageItem
from nass.utils.logger import logger


class DocxExtractor(BaseExtractor):
    """Native and OCR hybrid text extractor for Word (.docx) documents."""

    def __init__(self, image_ocr_service: Optional[DocumentImageOcrService] = None):
        self.image_ocr_service = image_ocr_service or DocumentImageOcrService()

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in WORD_EXTENSIONS

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
            file_type=FileType.WORD,
            file_size_bytes=file_size,
            total_pages=1,
            status=ProcessingStatus.PROCESSING,
            extraction_method=ExtractionMethod.NATIVE,
        )

        try:
            import docx

            doc = docx.Document(str(file_path))
            content_blocks = []

            # 1. Extract native digital text if requested
            if options.extract_native_text:
                # Extract paragraphs & headings
                for p in doc.paragraphs:
                    txt = p.text.strip()
                    if txt:
                        content_blocks.append(txt)

                # Extract tables
                for t_idx, table in enumerate(doc.tables):
                    content_blocks.append(f"\n--- [جدول {t_idx + 1}] ---")
                    for row in table.rows:
                        row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                        if row_cells:
                            content_blocks.append(" | ".join(row_cells))

            native_text = "\n\n".join(content_blocks).strip()

            # 2. Extract embedded images if OCR is requested
            image_ocr_blocks = []
            extracted_image_items: List[ExtractedImageItem] = []

            if options.extract_images_ocr:
                img_idx = 1
                for rel in doc.part.rels.values():
                    if "image" in rel.reltype:
                        try:
                            blob = rel.target_part.blob
                            item = ExtractedImageItem(
                                item_id=f"docx_img_{img_idx}",
                                source_location=f"مستند Word - صورة #{img_idx}",
                                image_bytes=blob,
                                page_or_section=1,
                                order_in_section=img_idx,
                            )
                            extracted_image_items.append(item)
                            img_idx += 1
                        except Exception as im_err:
                            logger.warning(f"Failed to read image relation in docx: {im_err}")

                if extracted_image_items:
                    self.image_ocr_service.process_image_items_batch(
                        extracted_image_items,
                        options=options,
                        cancel_check=cancel_check,
                    )
                    for item in extracted_image_items:
                        if item.ocr_text:
                            image_ocr_blocks.append(
                                f"[{item.source_location} - استخراج OCR]:\n{item.ocr_text}"
                            )

            image_ocr_text = "\n\n".join(image_ocr_blocks).strip()

            # Combine texts according to enabled options
            combined_parts = []
            if native_text:
                combined_parts.append(native_text)
            if image_ocr_text:
                combined_parts.append(
                    f"\n--- [النصوص المستخرجة من الصور المضمنة (OCR)] ---\n{image_ocr_text}"
                )

            final_text = "\n\n".join(combined_parts).strip()

            # Determine extraction method
            method = ExtractionMethod.NATIVE
            if options.extract_images_ocr and extracted_image_items:
                method = ExtractionMethod.HYBRID if native_text else ExtractionMethod.OCR
            doc_result.extraction_method = method

            img_details = [
                {
                    "item_id": item.item_id,
                    "location": item.source_location,
                    "status": item.status.value,
                    "confidence": item.confidence,
                    "error": item.error_message,
                    "has_text": bool(item.ocr_text),
                }
                for item in extracted_image_items
            ]

            # Calculate average confidence
            conf = 100.0
            if extracted_image_items and not native_text:
                valid_confs = [im.confidence for im in extracted_image_items if im.confidence > 0]
                conf = sum(valid_confs) / len(valid_confs) if valid_confs else 0.0

            page_result = PageResult(
                page_number=1,
                title="مستند Word",
                text=final_text,
                native_text=native_text,
                image_ocr_text=image_ocr_text,
                image_count=len(extracted_image_items),
                image_details=img_details,
                confidence=conf,
                status=ProcessingStatus.COMPLETED,
                extraction_method=method,
                duration_seconds=time.time() - start_time,
                is_embedded_text=bool(native_text),
            )

            # Optional math extraction
            if options.extract_math and final_text:
                try:
                    from nass.engines.ocr.math_engine import MathRecognitionService
                    math_service = MathRecognitionService(preferred_engine=options.math_engine)
                    eqs = math_service.extract_equations(text_context=final_text)
                    page_result.equations = [eq.latex for eq in eqs]
                except Exception as m_err:
                    logger.warning(f"Math extraction failed for Word document: {m_err}")

            doc_result.pages = [page_result]
            doc_result.status = ProcessingStatus.COMPLETED

            if progress_callback:
                progress_callback(1, 1, page_result)

        except Exception as e:
            logger.error(f"Error extracting DOCX {file_path.name}: {e}")
            doc_result.status = ProcessingStatus.FAILED
            doc_result.error_message = str(e)
            doc_result.pages = [
                PageResult(
                    page_number=1,
                    status=ProcessingStatus.FAILED,
                    error_message=str(e),
                    extraction_method=ExtractionMethod.NATIVE,
                )
            ]
        finally:
            doc_result.total_duration_seconds = time.time() - start_time

        return doc_result
