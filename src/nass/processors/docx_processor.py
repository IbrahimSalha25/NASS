"""
Microsoft Word (DOCX) document text extractor for NASS.
Extracts headings, paragraphs, and tables preserving document flow.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Optional

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
from nass.utils.logger import logger


class DocxExtractor(BaseExtractor):
    """Native text extractor for Word (.docx) documents."""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in WORD_EXTENSIONS

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

            # 1. Extract paragraphs & headings
            for p in doc.paragraphs:
                txt = p.text.strip()
                if txt:
                    content_blocks.append(txt)

            # 2. Extract tables
            for t_idx, table in enumerate(doc.tables):
                content_blocks.append(f"\n--- [جدول {t_idx + 1}] ---")
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_cells:
                        content_blocks.append(" | ".join(row_cells))

            full_text = "\n\n".join(content_blocks).strip()

            page_result = PageResult(
                page_number=1,
                title="مستند Word",
                text=full_text,
                confidence=100.0,
                status=ProcessingStatus.COMPLETED,
                extraction_method=ExtractionMethod.NATIVE,
                duration_seconds=time.time() - start_time,
                is_embedded_text=True,
            )

            # Optional math extraction from text
            if options.extract_math and full_text:
                try:
                    from nass.engines.ocr.math_engine import MathRecognitionService
                    math_service = MathRecognitionService(preferred_engine=options.math_engine)
                    eqs = math_service.extract_equations(text_context=full_text)
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
