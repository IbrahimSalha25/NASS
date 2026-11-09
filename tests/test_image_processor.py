"""
اختبارات وحدة تحسين الصور (ImageProcessor).
"""

from PIL import Image
from app.core.image_processor import ImageProcessor
from app.core.models import OcrOptions


def test_to_grayscale():
    """التحقق من تحويل الصورة الملونة إلى التدرج الرمادي."""
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    gray = ImageProcessor.to_grayscale(img)
    assert gray.mode == "L"


def test_enhance_contrast():
    """التحقق من تعزيز تباين الصورة دون انهيارها."""
    img = Image.new("L", (100, 100), color=128)
    enhanced = ImageProcessor.enhance_contrast(img, factor=1.5)
    assert enhanced.size == (100, 100)


def test_process_with_options_disabled():
    """التحقق من إرجاع الصورة كما هي دون تغيير عند تعطيل خيار التحسين."""
    img = Image.new("RGB", (50, 50), color=(100, 150, 200))
    options = OcrOptions(apply_enhancement=False)
    processed = ImageProcessor.process(img, options)
    assert processed == img
