"""
Excel (XLSX, XLS) and CSV spreadsheet text extractor for NASS.
Extracts tabular data preserving worksheet names and row/column relationships.
"""

from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Callable, Optional

from nass.core.config import EXCEL_EXTENSIONS
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


class ExcelExtractor(BaseExtractor):
    """Native text extractor for Excel (.xlsx, .xls) and CSV spreadsheets."""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in EXCEL_EXTENSIONS

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
            file_type=FileType.EXCEL,
            file_size_bytes=file_size,
            status=ProcessingStatus.PROCESSING,
            extraction_method=ExtractionMethod.NATIVE,
        )

        try:
            if suffix == ".csv":
                self._extract_csv(file_path, doc_result, options, progress_callback)
            else:
                self._extract_xlsx(file_path, doc_result, options, progress_callback, cancel_check)

            doc_result.status = ProcessingStatus.COMPLETED
        except Exception as e:
            logger.error(f"Error extracting spreadsheet {file_path.name}: {e}")
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

    def _extract_csv(
        self,
        file_path: Path,
        doc_result: DocumentResult,
        options: OcrOptions,
        progress_callback: Optional[Callable],
    ):
        """Extract CSV file content with multiple encoding fallbacks."""
        encodings = ["utf-8", "utf-8-sig", "cp1256", "latin-1"]
        raw_text = None

        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                raw_text = content
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if raw_text is None:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                raw_text = f.read()

        lines = raw_text.splitlines()
        rows_formatted = []
        reader = csv.reader(lines)
        for r in reader:
            cleaned = [c.strip() for c in r if c.strip()]
            if cleaned:
                rows_formatted.append(" | ".join(cleaned))

        formatted_text = "\n".join(rows_formatted).strip()

        page_res = PageResult(
            page_number=1,
            title="ملف CSV",
            text=formatted_text,
            confidence=100.0,
            status=ProcessingStatus.COMPLETED,
            extraction_method=ExtractionMethod.NATIVE,
            is_embedded_text=True,
        )
        doc_result.pages = [page_res]
        doc_result.total_pages = 1

        if progress_callback:
            progress_callback(1, 1, page_res)

    def _extract_xlsx(
        self,
        file_path: Path,
        doc_result: DocumentResult,
        options: OcrOptions,
        progress_callback: Optional[Callable],
        cancel_check: Optional[Callable],
    ):
        """Extract multi-sheet XLSX workbook using openpyxl."""
        import openpyxl

        wb = openpyxl.load_workbook(str(file_path), data_only=True, read_only=True)
        sheet_names = wb.sheetnames
        doc_result.total_pages = len(sheet_names)

        for idx, sheet_name in enumerate(sheet_names):
            if cancel_check and cancel_check():
                doc_result.status = ProcessingStatus.CANCELLED
                break

            page_num = idx + 1
            ws = wb[sheet_name]

            row_lines = []
            for row in ws.iter_rows(values_only=True):
                non_empty = [str(val).strip() for val in row if val is not None and str(val).strip()]
                if non_empty:
                    row_lines.append(" | ".join(non_empty))

            sheet_text = "\n".join(row_lines).strip()
            page_res = PageResult(
                page_number=page_num,
                title=f"ورقة العمل: {sheet_name}",
                text=sheet_text,
                confidence=100.0,
                status=ProcessingStatus.COMPLETED,
                extraction_method=ExtractionMethod.NATIVE,
                is_embedded_text=True,
            )

            doc_result.pages.append(page_res)
            if progress_callback:
                progress_callback(page_num, len(sheet_names), page_res)

        wb.close()
