"""
Image enhancement processor and Image OCR extractor for NASS.
Uses OpenCV and PIL for pre-OCR enhancements (grayscale, contrast, denoise, threshold, deskew).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Optional

from PIL import Image, ImageEnhance, ImageFilter

from nass.core.config import IMAGE_EXTENSIONS
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
from nass.utils.logger import logger


class ImageProcessor:
    """Pre-processing filters to improve image OCR readability."""

    @classmethod
    def to_grayscale(cls, image: Image.Image) -> Image.Image:
        """Convert image to single-channel grayscale."""
        if image.mode == "L":
            return image
        return image.convert("L")

    @classmethod
    def enhance_contrast(cls, image: Image.Image, factor: float = 1.5) -> Image.Image:
        """Enhance contrast to emphasize faint characters."""
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)

    @classmethod
    def denoise(cls, image: Image.Image) -> Image.Image:
        """Moderate denoising to reduce artifacts while preserving character dots."""
        try:
            import cv2
            import numpy as np

            if image.mode == "L":
                cv_img = np.array(image)
                denoised = cv2.fastNlMeansDenoising(cv_img, None, h=7, templateWindowSize=7, searchWindowSize=21)
                return Image.fromarray(denoised, mode="L")
            else:
                rgb_img = image.convert("RGB")
                cv_img = np.array(rgb_img)[:, :, ::-1].copy()
                denoised = cv2.fastNlMeansDenoisingColored(cv_img, None, h=7, hColor=7, templateWindowSize=7, searchWindowSize=21)
                rgb_back = cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB)
                return Image.fromarray(rgb_back)
        except ImportError:
            return image.filter(ImageFilter.SMOOTH_MORE)

    @classmethod
    def apply_threshold(cls, image: Image.Image) -> Image.Image:
        """Apply Otsu adaptive binarization to cleanly separate text from background."""
        gray_img = cls.to_grayscale(image)
        try:
            import cv2
            import numpy as np

            cv_img = np.array(gray_img)
            _, thresh = cv2.threshold(cv_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return Image.fromarray(thresh, mode="L")
        except ImportError:
            threshold_val = 140
            return gray_img.point(lambda p: 255 if p > threshold_val else 0, mode="1")

    @classmethod
    def deskew(cls, image: Image.Image) -> Image.Image:
        """Estimate and correct text baseline skew angle."""
        try:
            import cv2
            import numpy as np

            gray = cls.to_grayscale(image)
            cv_img = np.array(gray)

            inv = cv2.bitwise_not(cv_img)
            thresh = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

            coords = np.column_stack(np.where(thresh > 0))
            if len(coords) < 50:
                return image

            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            else:
                angle = -angle

            if abs(angle) < 0.5 or abs(angle) > 30.0:
                return image

            (h, w) = cv_img.shape[:2]
            center = (w // 2, h // 2)
            m = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                cv_img, m, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            return Image.fromarray(rotated, mode="L")
        except Exception:
            return image

    @classmethod
    def process(cls, image: Image.Image, options: OcrOptions) -> Image.Image:
        """Apply selected chain of pre-processing filters in memory."""
        if not options.apply_enhancement and not options.grayscale:
            return image

        result = image
        try:
            if (
                options.grayscale
                or options.threshold
                or options.enhance_contrast
                or options.denoise
                or options.deskew
            ):
                result = cls.to_grayscale(result)

            if options.deskew:
                result = cls.deskew(result)

            if options.denoise:
                result = cls.denoise(result)

            if options.enhance_contrast:
                result = cls.enhance_contrast(result)

            if options.threshold:
                result = cls.apply_threshold(result)

        except Exception as e:
            logger.warning(f"Image enhancement chain encountered an issue: {e}. Using raw image.")
            return image

        return result


class ImageExtractor(BaseExtractor):
    """Extractor for standard image formats using Tesseract OCR."""

    def __init__(self, ocr_engine: Optional[OcrEngine] = None):
        self.ocr_engine = ocr_engine or OcrEngine()

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in IMAGE_EXTENSIONS

    @property
    def extraction_method(self) -> ExtractionMethod:
        return ExtractionMethod.OCR

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
            file_type=FileType.IMAGE,
            file_size_bytes=file_size,
            total_pages=1,
            status=ProcessingStatus.PROCESSING,
            extraction_method=ExtractionMethod.OCR,
        )

        try:
            with Image.open(file_path) as raw_img:
                img = raw_img.convert("RGB") if raw_img.mode not in ("RGB", "L") else raw_img.copy()

            processed_img = ImageProcessor.process(img, options)
            effective_psm = 4 if options.single_column else options.psm

            page_res = self.ocr_engine.extract_text(
                image=processed_img,
                language=options.language,
                psm=effective_psm,
                oem=options.oem,
                extra_config=options.tesseract_config,
                page_number=1,
            )
            page_res.extraction_method = ExtractionMethod.OCR

            if options.extract_math and page_res.status == ProcessingStatus.COMPLETED:
                try:
                    from nass.engines.ocr.math_engine import MathRecognitionService
                    math_service = MathRecognitionService(preferred_engine=options.math_engine)
                    eqs = math_service.extract_equations(image=processed_img, text_context=page_res.text)
                    page_res.equations = [eq.latex for eq in eqs]
                except Exception as m_err:
                    logger.warning(f"Math extraction failed for image: {m_err}")

            doc_result.pages = [page_res]
            doc_result.status = page_res.status
            if page_res.status == ProcessingStatus.FAILED:
                doc_result.error_message = page_res.error_message

            if progress_callback:
                progress_callback(1, 1, page_res)

        except Exception as e:
            logger.error(f"Image extraction failed for {file_path.name}: {e}")
            doc_result.status = ProcessingStatus.FAILED
            doc_result.error_message = str(e)
            page_res = PageResult(
                page_number=1,
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                extraction_method=ExtractionMethod.OCR,
            )
            doc_result.pages = [page_res]
            if progress_callback:
                progress_callback(1, 1, page_res)
        finally:
            doc_result.total_duration_seconds = time.time() - start_time

        return doc_result
