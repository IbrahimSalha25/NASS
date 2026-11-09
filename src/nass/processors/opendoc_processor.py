"""
OpenDocument (ODT, ODS, ODP) and EPUB eBook text extractor for NASS.
Uses standard library zipfile and XML/HTML parsing without external dependencies.
"""

from __future__ import annotations

import time
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable, Optional

from nass.core.config import OPENDOC_EXTENSIONS
from nass.core.models import (
    DocumentResult,
    ExtractionMethod,
    FileType,
    OcrOptions,
    PageResult,
    ProcessingStatus,
)
from nass.engines.base import BaseExtractor
from nass.processors.markup_processor import _HTMLTextExtractor
from nass.utils.logger import logger


class OpenDocumentExtractor(BaseExtractor):
    """Native text extractor for OpenDocument formats (.odt, .ods, .odp) and EPUB eBooks."""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in OPENDOC_EXTENSIONS

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
            file_type=FileType.OPENDOC,
            file_size_bytes=file_size,
            status=ProcessingStatus.PROCESSING,
            extraction_method=ExtractionMethod.NATIVE,
        )

        try:
            if suffix == ".epub":
                self._extract_epub(file_path, doc_result, options, progress_callback, cancel_check)
            else:
                self._extract_opendocument(file_path, doc_result, options, progress_callback)

            doc_result.status = ProcessingStatus.COMPLETED

        except Exception as e:
            logger.error(f"Error parsing OpenDocument {file_path.name}: {e}")
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

    def _extract_opendocument(
        self,
        file_path: Path,
        doc_result: DocumentResult,
        options: OcrOptions,
        progress_callback: Optional[Callable],
    ):
        """Extract text from OpenDocument zip package (content.xml)."""
        paragraphs = []
        with zipfile.ZipFile(file_path, "r") as z:
            if "content.xml" in z.namelist():
                xml_data = z.read("content.xml")
                root = ET.fromstring(xml_data)

                # Iterate through all elements, catching any text node
                for elem in root.iter():
                    tag_lower = elem.tag.lower()
                    if tag_lower.endswith(("p", "h", "table-cell")):
                        # Collect full text within this node
                        txt = "".join(elem.itertext()).strip()
                        if txt:
                            paragraphs.append(txt)

        full_text = "\n\n".join(paragraphs).strip()
        page_res = PageResult(
            page_number=1,
            title="مستند OpenDocument",
            text=full_text,
            confidence=100.0,
            status=ProcessingStatus.COMPLETED,
            extraction_method=ExtractionMethod.NATIVE,
            is_embedded_text=True,
        )
        doc_result.pages = [page_res]
        doc_result.total_pages = 1

        if progress_callback:
            progress_callback(1, 1, page_res)

    def _extract_epub(
        self,
        file_path: Path,
        doc_result: DocumentResult,
        options: OcrOptions,
        progress_callback: Optional[Callable],
        cancel_check: Optional[Callable],
    ):
        """Extract chapters from EPUB eBook zip archive."""
        chapters = []
        with zipfile.ZipFile(file_path, "r") as z:
            # Find all HTML/XHTML chapter files
            namelist = [
                n for n in z.namelist()
                if n.lower().endswith((".xhtml", ".html", ".htm"))
                and not n.lower().endswith(("toc.xhtml", "nav.xhtml"))
            ]
            doc_result.total_pages = len(namelist)

            for idx, name in enumerate(namelist):
                if cancel_check and cancel_check():
                    doc_result.status = ProcessingStatus.CANCELLED
                    break

                page_num = idx + 1
                raw_html = z.read(name).decode("utf-8", errors="replace")
                parser = _HTMLTextExtractor()
                parser.feed(raw_html)
                chapter_text = parser.get_text()

                page_res = PageResult(
                    page_number=page_num,
                    title=f"فصل {page_num}",
                    text=chapter_text,
                    confidence=100.0,
                    status=ProcessingStatus.COMPLETED,
                    extraction_method=ExtractionMethod.NATIVE,
                    is_embedded_text=True,
                )
                doc_result.pages.append(page_res)

                if progress_callback:
                    progress_callback(page_num, len(namelist), page_res)
