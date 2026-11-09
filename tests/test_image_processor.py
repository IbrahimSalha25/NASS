"""
Tests for image enhancement module (ImageProcessor).
"""

from PIL import Image
from app.core.image_processor import ImageProcessor
from app.core.models import OcrOptions


def test_to_grayscale():
    """Verify converting color image to grayscale."""
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    gray = ImageProcessor.to_grayscale(img)
    assert gray.mode == "L"


def test_enhance_contrast():
    """Verify image contrast enhancement without shape changes."""
    img = Image.new("L", (100, 100), color=128)
    enhanced = ImageProcessor.enhance_contrast(img, factor=1.5)
    assert enhanced.size == (100, 100)


def test_process_with_options_disabled():
    """Verify returning original image untouched when enhancement option is disabled."""
    img = Image.new("RGB", (50, 50), color=(100, 150, 200))
    options = OcrOptions(apply_enhancement=False)
    processed = ImageProcessor.process(img, options)
    assert processed == img
