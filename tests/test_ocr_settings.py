"""
Tests for advanced OCR options (PSM, OEM, DPI, Grayscale, Config).
"""

from PIL import Image

from app.core.models import OcrOptions
from app.core.ocr_engine import OcrEngine
from app.core.image_processor import ImageProcessor


def test_ocr_options_defaults():
    opts = OcrOptions()
    assert opts.psm == 3
    assert opts.oem == 3
    assert opts.dpi == 300
    assert opts.grayscale is False
    assert opts.single_column is False
    assert opts.extract_math is False


def test_image_processor_with_grayscale_option():
    img = Image.new("RGB", (50, 50), color=(100, 150, 200))
    opts = OcrOptions(grayscale=True)
    processed = ImageProcessor.process(img, opts)
    assert processed.mode == "L"


def test_ocr_engine_with_custom_psm_and_oem():
    engine = OcrEngine()
    test_img = Image.new("RGB", (100, 30), color="white")
    # Test extract_text call with customized PSM and OEM values
    res = engine.extract_text(test_img, language="eng", psm=6, oem=3, extra_config="")
    assert res is not None
    assert res.page_number == 1
