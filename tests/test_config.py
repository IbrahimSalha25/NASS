"""
اختبارات ملف الإعدادات والتحقق من مسارات Tesseract و tessdata.
"""

from app.config import (
    LOCAL_TESSDATA,
    SUPPORTED_ALL_EXTENSIONS,
    find_tessdata_directory,
    find_tesseract_executable,
)


def test_tesseract_executable_found():
    """التحقق من العثور على ملف tesseract.exe على النظام."""
    exe = find_tesseract_executable()
    assert exe is not None
    assert exe.exists()
    assert exe.name.lower() == "tesseract.exe"


def test_tessdata_directory_found():
    """التحقق من العثور على مجلد tessdata ووجود ملفات اللغات."""
    tessdata = find_tessdata_directory()
    assert tessdata is not None
    assert tessdata.exists()
    trained_files = list(tessdata.glob("*.traineddata"))
    assert len(trained_files) >= 2  # ara + eng على الأقل


def test_supported_extensions():
    """التحقق من قائمة الامتدادات المدعومة."""
    assert ".pdf" in SUPPORTED_ALL_EXTENSIONS
    assert ".png" in SUPPORTED_ALL_EXTENSIONS
    assert ".jpg" in SUPPORTED_ALL_EXTENSIONS
    assert ".webp" in SUPPORTED_ALL_EXTENSIONS
    assert ".tiff" in SUPPORTED_ALL_EXTENSIONS
