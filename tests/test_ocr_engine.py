"""
Tests for Optical Character Recognition engine (OcrEngine).
"""

from pathlib import Path
from PIL import Image, ImageDraw

from app.core.models import ProcessingStatus
from app.core.ocr_engine import OcrEngine


def test_ocr_engine_status():
    """Verify Tesseract OCR engine status and available languages."""
    engine = OcrEngine()
    status = engine.get_status()

    assert status["is_available"] is True
    assert status["executable_path"] is not None
    assert status["tessdata_path"] is not None
    assert "eng" in status["languages"]
    assert "ara" in status["languages"]


def test_ocr_extract_english_text():
    """Verify extracting English text, computing confidence, and measuring duration."""
    img = Image.new("RGB", (350, 80), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 30), "NASS OCR 2026", fill=(0, 0, 0))

    engine = OcrEngine()
    res = engine.extract_text(img, language="eng")

    assert res.status == ProcessingStatus.COMPLETED
    assert "2026" in res.text or "NASS" in res.text
    assert res.confidence > 0
    assert res.duration_seconds > 0


def test_ocr_invalid_file_path():
    """Verify safe handling of non-existent file without raising uncaught exceptions."""
    engine = OcrEngine()
    res = engine.extract_text("non_existent_file.png", language="eng")

    assert res.status == ProcessingStatus.FAILED
    assert res.error_message is not None
    assert "غير موجود" in res.error_message
