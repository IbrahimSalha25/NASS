"""
محرك استخراج النصوص (OCR Engine) باستخدام Tesseract عبر Pytesseract.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image

from app.config import (
    configure_pytesseract,
    find_tessdata_directory,
    find_tesseract_executable,
)
from app.core.models import PageResult, ProcessingStatus
from app.utils.logger import logger


class OcrEngine:
    """محرك OCR للتواصل مع Tesseract واستخراج النصوص وبيانات الثقة."""

    def __init__(self):
        configure_pytesseract()

    def get_status(self) -> Dict[str, Any]:
        """التحقق من حالة Tesseract وإصداره واللغات المتوفرة."""
        import pytesseract

        status: Dict[str, Any] = {
            "is_available": False,
            "version": None,
            "executable_path": None,
            "tessdata_path": None,
            "languages": [],
            "error_message": None,
        }

        exe_path = find_tesseract_executable()
        status["executable_path"] = str(exe_path) if exe_path else None

        if not exe_path or not exe_path.exists():
            status["error_message"] = "محرك Tesseract غير مثبت أو لم يتم العثور على مسار tesseract.exe."
            return status

        tessdata_dir = find_tessdata_directory()
        status["tessdata_path"] = str(tessdata_dir) if tessdata_dir else None

        try:
            version_str = pytesseract.get_tesseract_version()
            status["version"] = str(version_str)
            status["is_available"] = True
        except Exception as e:
            logger.error(f"خطأ في التحقق من إصدار Tesseract: {e}")
            status["error_message"] = f"تعذر استدعاء Tesseract: {e}"
            return status

        try:
            langs = self.get_available_languages()
            status["languages"] = langs
        except Exception as e:
            logger.warning(f"تعذر استرداد قائمة اللغات: {e}")
            status["languages"] = []

        return status

    def get_available_languages(self) -> List[str]:
        """استرجاع اللغات المتوفرة فعلياً."""
        import pytesseract

        tessdata_dir = find_tessdata_directory()
        if tessdata_dir:
            os.environ["TESSDATA_PREFIX"] = str(tessdata_dir)

        try:
            langs = pytesseract.get_languages()
            if langs:
                return sorted(langs)
        except Exception as e:
            logger.warning(f"فشل get_languages عبر pytesseract: {e}")

        # كحل احتياطي، فحص ملفات *.traineddata مباشرة في مجلد tessdata
        if tessdata_dir and tessdata_dir.is_dir():
            files = tessdata_dir.glob("*.traineddata")
            langs = [f.stem for f in files if f.is_file()]
            return sorted(langs)

        return []

    def is_language_available(self, lang_code: str) -> bool:
        """فحص هل اللغة المطلوبة متوفرة (فردي أو مركب)."""
        available = set(self.get_available_languages())
        required_parts = lang_code.split("+")
        return all(part in available for part in required_parts)

    def extract_text(
        self,
        image: Union[Image.Image, Path, str],
        language: str = "ara+eng",
        psm: int = 3,
        oem: Optional[int] = None,
        extra_config: str = "",
        page_number: int = 1,
    ) -> PageResult:
        """استخراج النص من صورة وحساب نسبة الثقة والمدة الزمنية مع دعم PSM وOEM والتهيئة المخصصة."""
        import pytesseract
        from pytesseract import Output

        # التأكد من تهيئة متغيرات البيئة
        configure_pytesseract()

        start_time = time.time()
        result = PageResult(page_number=page_number, status=ProcessingStatus.PROCESSING)

        pil_image: Optional[Image.Image] = None
        opened_internally = False
        try:
            if isinstance(image, (str, Path)):
                image_path = Path(image)
                if not image_path.exists():
                    raise FileNotFoundError(f"ملف الصورة غير موجود: {image_path}")
                pil_image = Image.open(image_path)
                opened_internally = True
            elif isinstance(image, Image.Image):
                pil_image = image
            else:
                raise ValueError(f"نوع إدخال غير مدعوم للصورة: {type(image)}")

            if pil_image.mode not in ("RGB", "L"):
                pil_image = pil_image.convert("RGB")

            config_parts = [f"--psm {psm}"]
            if oem is not None:
                config_parts.append(f"--oem {oem}")
            if extra_config and extra_config.strip():
                config_parts.append(extra_config.strip())
            custom_config = " ".join(config_parts)

            actual_language = language
            if not self.is_language_available(language):
                available = self.get_available_languages()
                parts = [p for p in language.split("+") if p in available]
                if parts:
                    actual_language = "+".join(parts)
                    logger.warning(
                        f"اللغة المطلوبة '{language}' غير متوفرة بالكامل. تم استخدام '{actual_language}' المتاحة."
                    )
                elif available:
                    actual_language = available[0]
                    logger.warning(
                        f"اللغة المطلوبة '{language}' غير متوفرة. تم التراجع إلى '{actual_language}'."
                    )
                else:
                    raise RuntimeError("لا توجد أي لغات مثبتة أو متوفرة في مجلد tessdata.")

            # 1. استخراج النص
            text = pytesseract.image_to_string(
                pil_image,
                lang=actual_language,
                config=custom_config,
            )
            result.text = text.strip()

            # 2. استخراج بيانات الكلمات ونسبة الثقة
            try:
                data = pytesseract.image_to_data(
                    pil_image,
                    lang=actual_language,
                    config=custom_config,
                    output_type=Output.DICT,
                )
                confidences = []
                for conf, word in zip(data.get("conf", []), data.get("text", [])):
                    try:
                        conf_val = float(conf)
                        if conf_val >= 0 and str(word).strip():
                            confidences.append(conf_val)
                    except (ValueError, TypeError):
                        continue

                result.confidence = (sum(confidences) / len(confidences)) if confidences else 0.0
            except Exception as data_err:
                logger.warning(f"تعذر حساب درجات الثقة للصفحة {page_number}: {data_err}")
                result.confidence = 0.0

            result.status = ProcessingStatus.COMPLETED

        except Exception as e:
            logger.error(f"فشل استخراج النص للصفحة {page_number}: {e}")
            result.status = ProcessingStatus.FAILED
            result.error_message = str(e)
        finally:
            if opened_internally and pil_image:
                try:
                    pil_image.close()
                except Exception:
                    pass
            result.duration_seconds = time.time() - start_time

        return result
