"""
HTML and XML markup document text extractor for NASS.
Uses standard library HTMLParser and ElementTree to strip markup and extract readable body content.
"""

from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Optional

from nass.core.config import MARKUP_EXTENSIONS
from nass.core.models import (
    DocumentResult,
    ExtractionMethod,
    FileType,
    OcrOptions,
    PageResult,
    ProcessingStatus,
)
from nass.engines.base import BaseExtractor
from nass.processors.text_processor import TextExtractor
from nass.utils.logger import logger


class _HTMLTextExtractor(HTMLParser):
    """Internal streaming HTML text parser ignoring scripts and styles."""

    def __init__(self):
        super().__init__()
        self.result = []
        self._ignore = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() in ("script", "style", "noscript", "head"):
            self._ignore = True
        elif tag.lower() in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "br"):
            self.result.append("\n")

    def handle_endtag(self, tag):
        if tag.lower() in ("script", "style", "noscript", "head"):
            self._ignore = False
        elif tag.lower() in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"):
            self.result.append("\n")

    def handle_data(self, data):
        if not self._ignore:
            cleaned = data.strip()
            if cleaned:
                self.result.append(cleaned + " ")

    def get_text(self) -> str:
        text = "".join(self.result)
        # Collapse excessive newlines
        import re
        return re.sub(r"\n{3,}", "\n\n", text).strip()


class MarkupExtractor(BaseExtractor):
    """Native text extractor for Web & Markup documents (.html, .htm, .xml)."""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in MARKUP_EXTENSIONS

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
            file_type=FileType.MARKUP,
            file_size_bytes=file_size,
            total_pages=1,
            status=ProcessingStatus.PROCESSING,
            extraction_method=ExtractionMethod.NATIVE,
        )

        try:
            raw_content = TextExtractor._read_text_with_fallback(file_path)

            if suffix == ".xml":
                extracted_text = self._parse_xml(raw_content)
            else:
                parser = _HTMLTextExtractor()
                parser.feed(raw_content)
                extracted_text = parser.get_text()

            page_res = PageResult(
                page_number=1,
                title="مستند ويب / ترميز",
                text=extracted_text,
                confidence=100.0,
                status=ProcessingStatus.COMPLETED,
                extraction_method=ExtractionMethod.NATIVE,
                is_embedded_text=True,
                duration_seconds=time.time() - start_time,
            )

            doc_result.pages = [page_res]
            doc_result.status = ProcessingStatus.COMPLETED

            if progress_callback:
                progress_callback(1, 1, page_res)

        except Exception as e:
            logger.error(f"Error parsing markup {file_path.name}: {e}")
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
    def _parse_xml(xml_content: str) -> str:
        """Extract all text nodes from XML hierarchy."""
        try:
            root = ET.fromstring(xml_content)
            texts = []
            for elem in root.iter():
                t = elem.text.strip() if elem.text else ""
                if t:
                    texts.append(f"{elem.tag}: {t}")
            return "\n".join(texts).strip()
        except Exception:
            # Fallback to regex or html parser
            parser = _HTMLTextExtractor()
            parser.feed(xml_content)
            return parser.get_text()
