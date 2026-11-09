"""
Processing service coordinating document extraction workflows for NASS.
Decouples UI and workers from specific extractor implementations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from nass.core.models import DocumentResult, OcrOptions, PageResult
from nass.engines.document.document_engine import DocumentEngine
from nass.engines.ocr.ocr_engine import OcrEngine


class ProcessingService:
    """High-level service coordinating file text extraction."""

    def __init__(self, ocr_engine: Optional[OcrEngine] = None):
        self.ocr_engine = ocr_engine or OcrEngine()
        self.document_engine = DocumentEngine(ocr_engine=self.ocr_engine)

    def process_document(
        self,
        file_path: Path,
        options: OcrOptions,
        page_callback: Optional[Callable[[int, int, PageResult], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> DocumentResult:
        """Process any supported document or image file."""
        return self.document_engine.extract_document(
            file_path=file_path,
            options=options,
            progress_callback=page_callback,
            cancel_check=cancel_check,
        )
