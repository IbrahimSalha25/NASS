"""
Unified Document Processing Engine for NASS.
Registers all document extractors, identifies file types, and dispatches extraction tasks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional

from nass.core.exceptions import UnsupportedFormatError
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
from nass.processors.docx_processor import DocxExtractor
from nass.processors.excel_processor import ExcelExtractor
from nass.processors.image_processor import ImageExtractor
from nass.processors.json_processor import JsonExtractor
from nass.processors.markup_processor import MarkupExtractor
from nass.processors.opendoc_processor import OpenDocumentExtractor
from nass.processors.pdf_processor import PdfExtractor
from nass.processors.powerpoint_processor import PowerPointExtractor
from nass.processors.text_processor import TextExtractor
from nass.utils.file_utils import FileUtils
from nass.utils.logger import logger


class DocumentEngine:
    """Central registry and dispatch engine for document text extraction."""

    _instance: Optional[DocumentEngine] = None

    def __init__(self, ocr_engine: Optional[OcrEngine] = None):
        self.ocr_engine = ocr_engine or OcrEngine()
        self.extractors: List[BaseExtractor] = [
            PdfExtractor(ocr_engine=self.ocr_engine),
            ImageExtractor(ocr_engine=self.ocr_engine),
            DocxExtractor(),
            ExcelExtractor(),
            PowerPointExtractor(),
            TextExtractor(),
            MarkupExtractor(),
            JsonExtractor(),
            OpenDocumentExtractor(),
        ]

    @classmethod
    def get_instance(cls) -> DocumentEngine:
        """Returns the shared singleton instance of DocumentEngine."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_extractor_for_file(self, file_path: Path) -> Optional[BaseExtractor]:
        """Find the matching extractor registered for this file."""
        for ext in self.extractors:
            if ext.can_handle(file_path):
                return ext
        return None

    def get_predicted_method(self, file_path: Path) -> ExtractionMethod:
        """Predict whether this file will use native digital extraction, OCR, or hybrid."""
        extractor = self.get_extractor_for_file(file_path)
        if extractor:
            return extractor.extraction_method
        return ExtractionMethod.NATIVE

    def extract_document(
        self,
        file_path: Path,
        options: Optional[OcrOptions] = None,
        progress_callback: Optional[Callable[[int, int, PageResult], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> DocumentResult:
        """
        Identify file type and extract content using the appropriate extractor.
        """
        opts = options or OcrOptions()
        valid, err = FileUtils.is_valid_file(file_path)
        if not valid:
            return DocumentResult(
                file_path=file_path,
                file_type=FileUtils.detect_file_type(file_path),
                file_size_bytes=file_path.stat().st_size if file_path.exists() else 0,
                status=ProcessingStatus.FAILED,
                error_message=err or "ملف غير صالح.",
            )

        extractor = self.get_extractor_for_file(file_path)
        if not extractor:
            logger.warning(f"No extractor available for file: {file_path.name}")
            return DocumentResult(
                file_path=file_path,
                file_type=FileType.UNKNOWN,
                file_size_bytes=file_path.stat().st_size if file_path.exists() else 0,
                status=ProcessingStatus.FAILED,
                error_message=f"صيغة الملف '{file_path.suffix}' غير مدعومة حالياً.",
            )

        logger.info(f"Extracting {file_path.name} with {extractor.__class__.__name__}")
        return extractor.extract(
            file_path=file_path,
            options=opts,
            progress_callback=progress_callback,
            cancel_check=cancel_check,
        )

    def process_file(
        self,
        file_path: Path,
        options: Optional[OcrOptions] = None,
        progress_callback: Optional[Callable[[int, int, PageResult], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> DocumentResult:
        """Alias for extract_document."""
        return self.extract_document(file_path, options, progress_callback, cancel_check)
