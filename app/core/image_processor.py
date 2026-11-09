"""
وحدة معالجة وتحسين الصور قبل تمريرها لمحرك OCR.
جميع التحسينات اختيارية ولا تعدل الملف الأصلي، مع دعم احتياطي لمكتبة PIL النقية.
"""

from __future__ import annotations

from typing import Optional
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from app.core.models import OcrOptions
from app.utils.logger import logger


class ImageProcessor:
    """معالج تحسين جودة الصور لدعم استخراج النصوص."""

    @classmethod
    def to_grayscale(cls, image: Image.Image) -> Image.Image:
        """تحويل الصورة إلى التدرج الرمادي."""
        if image.mode == "L":
            return image
        return image.convert("L")

    @classmethod
    def enhance_contrast(cls, image: Image.Image, factor: float = 1.5) -> Image.Image:
        """تحسين تباين الصورة للمساعدة في إبراز الأحرف الباهتة."""
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)

    @classmethod
    def denoise(cls, image: Image.Image) -> Image.Image:
        """إزالة الضوضاء والتشويش باعتدال لتجنب محو نقاط الحروف."""
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
            # حل احتياطي عبر مرشحات PIL
            return image.filter(ImageFilter.SMOOTH_MORE)

    @classmethod
    def apply_threshold(cls, image: Image.Image) -> Image.Image:
        """
        تطبيق العتبة الثنائية (Binarization) لفصل النص عن الخلفيات الملونة.
        """
        gray_img = cls.to_grayscale(image)
        try:
            import cv2
            import numpy as np

            cv_img = np.array(gray_img)
            _, thresh = cv2.threshold(cv_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return Image.fromarray(thresh, mode="L")
        except ImportError:
            # حل احتياطي عبر العتبة النقطية في PIL
            threshold_val = 140
            return gray_img.point(lambda p: 255 if p > threshold_val else 0, mode="1")

    @classmethod
    def deskew(cls, image: Image.Image) -> Image.Image:
        """تقدير وتصحيح ميلان الصفحة باعتدال."""
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
        """تطبيق سلسلة التحسينات المختارة."""
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
            logger.warning(f"تعذر استكمال تحسين الصورة بالكامل: {e}. سيتم استخدام الصورة الأصلية.")
            return image

        return result
