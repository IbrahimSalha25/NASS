"""
Structured JSON file text extractor for NASS.
Formats hierarchical JSON key-value pairs into readable, human-friendly text.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, List, Optional

from nass.core.config import JSON_EXTENSIONS
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


class JsonExtractor(BaseExtractor):
    """Native text extractor for JSON data files."""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in JSON_EXTENSIONS

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
            file_type=FileType.JSON,
            file_size_bytes=file_size,
            total_pages=1,
            status=ProcessingStatus.PROCESSING,
            extraction_method=ExtractionMethod.NATIVE,
        )

        try:
            raw_text = TextExtractor._read_text_with_fallback(file_path)
            data = json.loads(raw_text)

            lines: List[str] = []
            self._format_json_node(data, lines, indent=0)
            formatted_text = "\n".join(lines).strip()

            page_res = PageResult(
                page_number=1,
                title="بيانات JSON",
                text=formatted_text,
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
            logger.error(f"Error parsing JSON file {file_path.name}: {e}")
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

    def _format_json_node(self, node: Any, output_lines: List[str], indent: int = 0):
        """Recursively format JSON objects and lists into clean indented lines."""
        prefix = "  " * indent
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, (dict, list)):
                    output_lines.append(f"{prefix}• {k}:")
                    self._format_json_node(v, output_lines, indent + 1)
                else:
                    output_lines.append(f"{prefix}• {k}: {v}")
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                if isinstance(item, (dict, list)):
                    output_lines.append(f"{prefix}[عنصر {idx + 1}]:")
                    self._format_json_node(item, output_lines, indent + 1)
                else:
                    output_lines.append(f"{prefix}- {item}")
        else:
            output_lines.append(f"{prefix}{node}")
