"""
Excel (XLSX, XLS) and CSV spreadsheet text extractor for NASS.
Extracts tabular data preserving worksheet names and row/column relationships.
Supports extracting embedded images within worksheets and performing OCR with provenance metadata.
"""

from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Callable, List, Optional

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
from nass.services.image_ocr_service import DocumentImageOcrService, ExtractedImageItem
from nass.utils.logger import logger


class ExcelExtractor(BaseExtractor):
    """Native and OCR hybrid text extractor for Excel (.xlsx, .xls) and CSV spreadsheets."""

    def __init__(self, image_ocr_service: Optional[DocumentImageOcrService] = None):
        self.image_ocr_service = image_ocr_service or DocumentImageOcrService()

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in EXCEL_EXTENSIONS

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

            if doc_result.status != ProcessingStatus.CANCELLED:
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
            native_text=formatted_text,
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
        """Extract multi-sheet XLSX workbook and process embedded images."""
        import openpyxl

        wb = openpyxl.load_workbook(str(file_path), data_only=True)
        sheet_names = wb.sheetnames
        doc_result.total_pages = len(sheet_names)

        overall_has_ocr = False
        overall_has_native = False

        for idx, sheet_name in enumerate(sheet_names):
            if cancel_check and cancel_check():
                doc_result.status = ProcessingStatus.CANCELLED
                break

            page_num = idx + 1
            ws = wb[sheet_name]

            # 1. Native text extraction
            native_lines = []
            if options.extract_native_text:
                for row in ws.iter_rows(values_only=True):
                    non_empty = [str(val).strip() for val in row if val is not None and str(val).strip()]
                    if non_empty:
                        native_lines.append(" | ".join(non_empty))

            native_sheet_text = "\n".join(native_lines).strip()
            if native_sheet_text:
                overall_has_native = True

            # 2. Extract embedded images on this worksheet
            image_ocr_blocks = []
            sheet_image_items: List[ExtractedImageItem] = []

            if options.extract_images_ocr:
                ws_images = getattr(ws, "_images", [])
                for img_idx, img_obj in enumerate(ws_images, start=1):
                    try:
                        raw_data = img_obj._data()
                        # Determine cell anchor if available
                        loc_hint = f"ورقة العمل: {sheet_name} - صورة #{img_idx}"
                        anchor = getattr(img_obj, "anchor", None)
                        if anchor and hasattr(anchor, "_from"):
                            row_c = getattr(anchor._from, "row", 0) + 1
                            col_c = getattr(anchor._from, "col", 0) + 1
                            col_name = chr(64 + col_c) if 1 <= col_c <= 26 else str(col_c)
                            loc_hint = f"ورقة العمل: {sheet_name} ({col_name}{row_c}) - صورة #{img_idx}"

                        item = ExtractedImageItem(
                            item_id=f"sheet_{page_num}_img_{img_idx}",
                            source_location=loc_hint,
                            image_bytes=raw_data,
                            page_or_section=page_num,
                            order_in_section=img_idx,
                        )
                        sheet_image_items.append(item)
                    except Exception as im_err:
                        logger.warning(f"Failed to read image in sheet {sheet_name}: {im_err}")

                if sheet_image_items:
                    self.image_ocr_service.process_image_items_batch(
                        sheet_image_items,
                        options=options,
                        cancel_check=cancel_check,
                    )
                    for item in sheet_image_items:
                        if item.ocr_text:
                            image_ocr_blocks.append(
                                f"[{item.source_location} - استخراج OCR]:\n{item.ocr_text}"
                            )

            image_ocr_text = "\n\n".join(image_ocr_blocks).strip()
            if image_ocr_text:
                overall_has_ocr = True

            # Combine content for this sheet
            combined_parts = []
            if native_sheet_text:
                combined_parts.append(native_sheet_text)
            if image_ocr_text:
                combined_parts.append(
                    f"[النصوص المستخرجة من صور ورقة العمل (OCR)]:\n{image_ocr_text}"
                )

            final_sheet_text = "\n\n".join(combined_parts).strip()
            if not final_sheet_text:
                final_sheet_text = "[لا توجد بيانات أو نصوص في هذه الورقة]"

            method = ExtractionMethod.NATIVE
            if options.extract_images_ocr and sheet_image_items:
                method = ExtractionMethod.HYBRID if native_sheet_text else ExtractionMethod.OCR

            conf = 100.0
            if sheet_image_items and not native_sheet_text:
                valid_confs = [im.confidence for im in sheet_image_items if im.confidence > 0]
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
                for item in sheet_image_items
            ]

            page_res = PageResult(
                page_number=page_num,
                title=f"ورقة العمل: {sheet_name}",
                text=final_sheet_text,
                native_text=native_sheet_text,
                image_ocr_text=image_ocr_text,
                image_count=len(sheet_image_items),
                image_details=img_details,
                confidence=conf,
                status=ProcessingStatus.COMPLETED,
                extraction_method=method,
                is_embedded_text=bool(native_sheet_text),
            )

            doc_result.pages.append(page_res)
            if progress_callback:
                progress_callback(page_num, len(sheet_names), page_res)

        wb.close()

        # Update overall document extraction method
        if overall_has_ocr and overall_has_native:
            doc_result.extraction_method = ExtractionMethod.HYBRID
        elif overall_has_ocr:
            doc_result.extraction_method = ExtractionMethod.OCR
        else:
            doc_result.extraction_method = ExtractionMethod.NATIVE
