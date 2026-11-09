"""
Microsoft PowerPoint (PPTX) presentation text extractor for NASS.
Extracts slide titles, body text frames, shapes, and tables preserving slide ordering.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Optional

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
from nass.utils.logger import logger


class PowerPointExtractor(BaseExtractor):
    """Native text extractor for PowerPoint presentations (.pptx)."""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in POWERPOINT_EXTENSIONS

    @property
    def extraction_method(self) -> ExtractionMethod:
        return ExtractionMethod.NATIVE

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

                slide_content = "\n".join(slide_text_blocks).strip()

                page_res = PageResult(
                    page_number=page_num,
                    title=slide_title,
                    text=slide_content if slide_content else "[لا يوجد نص في هذه الشريحة]",
                    confidence=100.0,
                    status=ProcessingStatus.COMPLETED,
                    extraction_method=ExtractionMethod.NATIVE,
                    is_embedded_text=True,
                )

                # Optional math detection
                if options.extract_math and slide_content:
                    try:
                        from nass.engines.ocr.math_engine import MathRecognitionService
                        math_service = MathRecognitionService(preferred_engine=options.math_engine)
                        eqs = math_service.extract_equations(text_context=slide_content)
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
