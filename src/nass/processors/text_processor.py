"""
Plain text, Markdown, and RTF document extractor for NASS.
Handles character encoding detection (UTF-8, CP1256, Latin-1) and RTF control word stripping.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Callable, Optional

from nass.core.config import TEXT_EXTENSIONS
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


class TextExtractor(BaseExtractor):
    """Native extractor for plain text files (.txt, .md, .rtf)."""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in TEXT_EXTENSIONS

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
        suffix = file_path.suffix.lower()

        doc_result = DocumentResult(
            file_path=file_path,
            file_type=FileType.TEXT,
            file_size_bytes=file_size,
            total_pages=1,
            status=ProcessingStatus.PROCESSING,
            extraction_method=ExtractionMethod.NATIVE,
        )

        try:
            content = self._read_text_with_fallback(file_path)

            if suffix == ".rtf":
                content = self._strip_rtf(content)

            page_res = PageResult(
                page_number=1,
                title="ملف نصي",
                text=content.strip(),
                confidence=100.0,
                status=ProcessingStatus.COMPLETED,
                extraction_method=ExtractionMethod.NATIVE,
                is_embedded_text=True,
                duration_seconds=time.time() - start_time,
            )

            if options.extract_math and content:
                try:
                    from nass.engines.ocr.math_engine import MathRecognitionService
                    math_service = MathRecognitionService(preferred_engine=options.math_engine)
                    eqs = math_service.extract_equations(text_context=content)
                    page_res.equations = [eq.latex for eq in eqs]
                except Exception:
                    pass

            doc_result.pages = [page_res]
            doc_result.status = ProcessingStatus.COMPLETED

            if progress_callback:
                progress_callback(1, 1, page_res)

        except Exception as e:
            logger.error(f"Error reading text file {file_path.name}: {e}")
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

    @staticmethod
    def _read_text_with_fallback(file_path: Path) -> str:
        """Attempt reading with UTF-8, UTF-8-SIG, CP1256 (Arabic), and Latin-1."""
        encodings = ["utf-8", "utf-8-sig", "cp1256", "utf-16", "latin-1"]
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    @staticmethod
    def _strip_rtf(text: str) -> str:
        """Strip basic RTF control commands and extract readable text."""
        # Remove metadata groups like font tables and stylesheets
        text = re.sub(r"\{\*?\\[^{}]+?\}", "", text)
        # Convert paragraph/line breaks
        text = re.sub(r"\\(par|line)\b", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"\\tab\b", "\t", text, flags=re.IGNORECASE)
        # Convert hex characters
        def replace_hex(m: re.Match) -> str:
            try:
                return bytes.fromhex(m.group(1)).decode("cp1256", errors="replace")
            except Exception:
                return ""
        text = re.sub(r"\\\'([0-9a-f]{2})", replace_hex, text, flags=re.IGNORECASE)
        # Remove remaining control words like \b, \fs24, \ansi
        text = re.sub(r"\\[a-z]{1,32}(-?\d+)? ?", "", text, flags=re.IGNORECASE)
        # Remove stray braces
        text = re.sub(r"[{}]", "", text)
        # Collapse excessive newlines
        return re.sub(r"\n{3,}", "\n\n", text).strip()
