"""
Shared models and service for embedded image extraction and OCR text recognition across all document types (Word, PowerPoint, Excel, PDF).
"""

from __future__ import annotations

import io
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union

from PIL import Image

from nass.core.models import (
    ExtractionMethod,
    FileType,
    OcrOptions,
    PageResult,
    ProcessingStatus,
)
from nass.engines.ocr.ocr_engine import OcrEngine
from nass.processors.image_processor import ImageProcessor
from nass.utils.logger import logger


@dataclass
class ExtractedImageItem:
    """Represents an image extracted from a document with provenance metadata."""
    item_id: str                      # Unique ID (e.g., 'p1_img1' or 'slide2_shape3')
    source_location: str              # User-facing location description (e.g., 'الصفحة 1', 'الشريحة 2 - صورة 1', 'ورقة العمل: المبيعات (B4)')
    image_bytes: bytes                # Raw image binary
    format: str = "PNG"               # Image format (PNG, JPEG, etc.)
    page_or_section: int = 1          # 1-based page, slide, or sheet index
    order_in_section: int = 1         # 1-based index within the page/slide/sheet
    width: int = 0
    height: int = 0
    ocr_text: str = ""                # Extracted text via OCR
    confidence: float = 0.0           # OCR confidence percentage
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None

    def to_pil_image(self) -> Optional[Image.Image]:
        """Convert binary bytes to PIL Image safely."""
        try:
            return Image.open(io.BytesIO(self.image_bytes))
        except Exception as e:
            logger.warning(f"Failed to load image bytes for item {self.item_id}: {e}")
            return None


class DocumentImageOcrService:
    """
    Unified, reusable service to extract embedded images and perform OCR across all formats.
    """

    def __init__(self, ocr_engine: Optional[OcrEngine] = None):
        self.ocr_engine = ocr_engine or OcrEngine()

    def process_image_item(
        self,
        item: ExtractedImageItem,
        options: OcrOptions,
    ) -> ExtractedImageItem:
        """
        Enhance and perform OCR on a single ExtractedImageItem.
        Handles errors gracefully without skipping or silent failures.
        """
        item.status = ProcessingStatus.PROCESSING
        pil_img = item.to_pil_image()
        if pil_img is None:
            item.status = ProcessingStatus.FAILED
            item.error_message = "تعذر قراءة بيانات الصورة أو صيغتها غير مدعومة."
            return item

        try:
            # Check dimensions & validate
            w, h = pil_img.size
            item.width = w
            item.height = h

            if w < 10 or h < 10:
                item.status = ProcessingStatus.COMPLETED
                item.ocr_text = ""
                item.confidence = 100.0
                return item

            # Apply pre-OCR enhancements if enabled
            processed_img = pil_img
            if options.apply_enhancement:
                if options.grayscale:
                    processed_img = ImageProcessor.to_grayscale(processed_img)
                if options.enhance_contrast:
                    processed_img = ImageProcessor.enhance_contrast(processed_img)
                if options.denoise:
                    processed_img = ImageProcessor.denoise(processed_img)
                if options.threshold:
                    processed_img = ImageProcessor.apply_threshold(processed_img)
                if options.deskew:
                    processed_img = ImageProcessor.deskew(processed_img)

            # Perform OCR
            page_res = self.ocr_engine.extract_text(
                image=processed_img,
                language=options.language,
                psm=options.psm,
                oem=options.oem,
                extra_config=options.tesseract_config,
                page_number=item.page_or_section,
            )

            item.ocr_text = page_res.text.strip()
            item.confidence = page_res.confidence
            item.status = ProcessingStatus.COMPLETED
            if page_res.error_message:
                item.error_message = page_res.error_message

        except Exception as e:
            logger.error(f"OCR failed for image {item.item_id}: {e}")
            item.status = ProcessingStatus.FAILED
            item.error_message = f"فشل استخراج النص من الصورة: {e}"

        return item

    def process_image_items_batch(
        self,
        items: List[ExtractedImageItem],
        options: OcrOptions,
        progress_callback: Optional[Callable[[int, int, ExtractedImageItem], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> List[ExtractedImageItem]:
        """
        Process multiple images sequentially with cooperative cancellation and progress reports.
        """
        total = len(items)
        for idx, item in enumerate(items):
            if cancel_check and cancel_check():
                item.status = ProcessingStatus.CANCELLED
                item.error_message = "تم إلغاء المعالجة من قِبل المستخدم."
                if progress_callback:
                    progress_callback(idx + 1, total, item)
                break

            self.process_image_item(item, options)
            if progress_callback:
                progress_callback(idx + 1, total, item)

        return items
