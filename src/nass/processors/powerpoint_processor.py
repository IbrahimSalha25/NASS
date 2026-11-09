"""
Microsoft PowerPoint (PPTX) presentation text extractor for NASS.
Extracts slide titles, body text frames, shapes, and tables preserving slide ordering.
Supports extracting embedded images per slide and performing OCR with provenance metadata.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, List, Optional

from nass.core.config import POWERPOINT_EXTENSIONS
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


class PowerPointExtractor(BaseExtractor):
    """Native and OCR hybrid text extractor for PowerPoint presentations (.pptx)."""

    def __init__(self, image_ocr_service: Optional[DocumentImageOcrService] = None):
        self.image_ocr_service = image_ocr_service or DocumentImageOcrService()

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in POWERPOINT_EXTENSIONS

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
            file_type=FileType.POWERPOINT,
            file_size_bytes=file_size,
            status=ProcessingStatus.PROCESSING,
            extraction_method=ExtractionMethod.NATIVE,
        )

        try:
            import pptx

            prs = pptx.Presentation(str(file_path))
            total_slides = len(prs.slides)
            doc_result.total_pages = total_slides

            if total_slides == 0:
                doc_result.status = ProcessingStatus.COMPLETED
                return doc_result

            for idx, slide in enumerate(prs.slides):
                if cancel_check and cancel_check():
                    doc_result.status = ProcessingStatus.CANCELLED
                    break

                page_num = idx + 1
                slide_text_blocks = []
                slide_title = f"شريحة {page_num}"

                # 1. Native text extraction
                if options.extract_native_text:
                    for shape in slide.shapes:
                        if shape.has_text_frame:
                            for paragraph in shape.text_frame.paragraphs:
                                t = paragraph.text.strip()
                                if t:
                                    slide_text_blocks.append(t)
                        elif shape.has_table:
                            for row in shape.table.rows:
                                row_txt = [c.text.strip() for c in row.cells if c.text.strip()]
                                if row_txt:
                                    slide_text_blocks.append(" | ".join(row_txt))

                # Check for slide title
                if slide.shapes.title and slide.shapes.title.text.strip():
                    slide_title = f"شريحة {page_num}: {slide.shapes.title.text.strip()}"

                native_text = "\n".join(slide_text_blocks).strip()

                # 2. Extract embedded images on this slide
                image_ocr_blocks = []
                slide_image_items: List[ExtractedImageItem] = []

                if options.extract_images_ocr:
                    img_idx = 1
                    for shape in slide.shapes:
                        if shape.shape_type == pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE:
                            try:
                                blob = shape.image.blob
                                ext = shape.image.ext
                                item = ExtractedImageItem(
                                    item_id=f"slide_{page_num}_img_{img_idx}",
                                    source_location=f"شريحة {page_num} - صورة #{img_idx}",
                                    image_bytes=blob,
                                    format=ext.upper(),
                                    page_or_section=page_num,
                                    order_in_section=img_idx,
                                )
                                slide_image_items.append(item)
                                img_idx += 1
                            except Exception as im_err:
                                logger.warning(f"Failed to read image on slide {page_num}: {im_err}")

                    if slide_image_items:
                        self.image_ocr_service.process_image_items_batch(
                            slide_image_items,
                            options=options,
                            cancel_check=cancel_check,
                        )
                        for item in slide_image_items:
                            if item.ocr_text:
                                image_ocr_blocks.append(
                                    f"[{item.source_location} - استخراج OCR]:\n{item.ocr_text}"
                                )

                image_ocr_text = "\n\n".join(image_ocr_blocks).strip()

                # Combine content for this slide
                combined_parts = []
                if native_text:
                    combined_parts.append(native_text)
                if image_ocr_text:
                    combined_parts.append(
                        f"[النصوص المستخرجة من صور الشريحة (OCR)]:\n{image_ocr_text}"
                    )

                final_slide_content = "\n\n".join(combined_parts).strip()
                if not final_slide_content:
                    final_slide_content = "[لا يوجد نص في هذه الشريحة]"

                # Method & Confidence
                method = ExtractionMethod.NATIVE
                if options.extract_images_ocr and slide_image_items:
                    method = ExtractionMethod.HYBRID if native_text else ExtractionMethod.OCR

                conf = 100.0
                if slide_image_items and not native_text:
                    valid_confs = [im.confidence for im in slide_image_items if im.confidence > 0]
                    conf = sum(valid_confs) / len(valid_confs) if valid_confs else 0.0

                img_details = [
                    {
                        "item_id": item.item_id,
                        "location": item.source_location,
                        "status": item.status.value,
                        "confidence": item.confidence,
                        "error": item.error_message,
                        "has_text": bool(item.ocr_text),
                    }
                    for item in slide_image_items
                ]

                page_res = PageResult(
                    page_number=page_num,
                    title=slide_title,
                    text=final_slide_content,
                    native_text=native_text,
                    image_ocr_text=image_ocr_text,
                    image_count=len(slide_image_items),
                    image_details=img_details,
                    confidence=conf,
                    status=ProcessingStatus.COMPLETED,
                    extraction_method=method,
                    is_embedded_text=bool(native_text),
                )

                # Optional math detection
                if options.extract_math and final_slide_content:
                    try:
                        from nass.engines.ocr.math_engine import MathRecognitionService
                        math_service = MathRecognitionService(preferred_engine=options.math_engine)
                        eqs = math_service.extract_equations(text_context=final_slide_content)
                        page_res.equations = [eq.latex for eq in eqs]
                    except Exception:
                        pass

                doc_result.pages.append(page_res)

                if progress_callback:
                    progress_callback(page_num, total_slides, page_res)

            if doc_result.status != ProcessingStatus.CANCELLED:
                doc_result.status = ProcessingStatus.COMPLETED

        except Exception as e:
            logger.error(f"Error extracting presentation {file_path.name}: {e}")
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
