"""
Tesseract OCR Engine wrapper using pytesseract.
Handles text extraction, word confidence calculation, and parameter configurations.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PIL import Image

from nass.core.config import (
    configure_pytesseract,
    find_tessdata_directory,
    find_tesseract_executable,
)
from nass.core.models import ExtractionMethod, PageResult, ProcessingStatus
from nass.utils.logger import logger


class OcrEngine:
    """Core OCR engine interfacing with Tesseract via pytesseract."""

    def __init__(self):
        configure_pytesseract()

    def get_status(self) -> Dict[str, Any]:
        """Check Tesseract installation status, version, and available language packs."""
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
            status["error_message"] = "Tesseract OCR engine is not installed or tesseract.exe was not found."
            return status

        tessdata_dir = find_tessdata_directory()
        status["tessdata_path"] = str(tessdata_dir) if tessdata_dir else None

        try:
            version_str = pytesseract.get_tesseract_version()
            status["version"] = str(version_str)
            status["is_available"] = True
        except Exception as e:
            logger.error(f"Error checking Tesseract version: {e}")
            status["error_message"] = f"Failed to execute Tesseract: {e}"
            return status

        try:
            langs = self.get_available_languages()
            status["languages"] = langs
        except Exception as e:
            logger.warning(f"Failed to retrieve available languages: {e}")
            status["languages"] = []

        return status

    def get_available_languages(self) -> List[str]:
        """Retrieve the list of installed language traineddata codes."""
        import pytesseract

        tessdata_dir = find_tessdata_directory()
        if tessdata_dir:
            os.environ["TESSDATA_PREFIX"] = str(tessdata_dir)

        try:
            langs = pytesseract.get_languages()
            if langs:
                return sorted(langs)
        except Exception as e:
            logger.warning(f"Failed to retrieve languages via pytesseract: {e}")

        # Fallback to direct directory glob
        if tessdata_dir and tessdata_dir.is_dir():
            files = tessdata_dir.glob("*.traineddata")
            return sorted([f.stem for f in files if f.is_file()])

        return []

    def is_language_available(self, lang_code: str) -> bool:
        """Check if requested language or language combination (e.g. ara+eng) is installed."""
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
        """Extract text and confidence scores from an image using Tesseract."""
        import pytesseract
        from pytesseract import Output

        configure_pytesseract()

        start_time = time.time()
        result = PageResult(
            page_number=page_number,
            status=ProcessingStatus.PROCESSING,
            extraction_method=ExtractionMethod.OCR,
            is_embedded_text=False,
        )

        pil_image: Optional[Image.Image] = None
        opened_internally = False

        try:
            if isinstance(image, (str, Path)):
                image_path = Path(image)
                if not image_path.exists():
                    raise FileNotFoundError(f"Image file not found: {image_path}")
                pil_image = Image.open(image_path)
                opened_internally = True
            elif isinstance(image, Image.Image):
                pil_image = image
            else:
                raise ValueError(f"Unsupported image input type: {type(image)}")

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
                        f"Language '{language}' partially available. Using '{actual_language}'."
                    )
                elif available:
                    actual_language = available[0]
                    logger.warning(
                        f"Language '{language}' not available. Falling back to '{actual_language}'."
                    )
                else:
                    raise RuntimeError("No language pack files installed in tessdata directory.")

            # 1. Primary text extraction
            text = pytesseract.image_to_string(
                pil_image,
                lang=actual_language,
                config=custom_config,
            )
            result.text = text.strip()

            # 2. Extract word-level data for confidence calculation
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
                logger.warning(f"Could not compute confidence scores for page {page_number}: {data_err}")
                result.confidence = 0.0

            result.status = ProcessingStatus.COMPLETED

        except Exception as e:
            logger.error(f"OCR text extraction failed for page {page_number}: {e}")
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
