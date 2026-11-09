"""
Configuration tests for verifying Tesseract executable and tessdata path discovery.
"""

from app.config import (
    LOCAL_TESSDATA,
    SUPPORTED_ALL_EXTENSIONS,
    find_tessdata_directory,
    find_tesseract_executable,
)


def test_tesseract_executable_found():
    """Verify that tesseract.exe is successfully discovered on the system."""
    exe = find_tesseract_executable()
    assert exe is not None
    assert exe.exists()
    assert exe.name.lower() == "tesseract.exe"


def test_tessdata_directory_found():
    """Verify that tessdata directory is discovered and contains language packages."""
    tessdata = find_tessdata_directory()
    assert tessdata is not None
    assert tessdata.exists()
    trained_files = list(tessdata.glob("*.traineddata"))
    assert len(trained_files) >= 2  # At least ara + eng


def test_supported_extensions():
    """Verify list of supported file extensions."""
    assert ".pdf" in SUPPORTED_ALL_EXTENSIONS
    assert ".png" in SUPPORTED_ALL_EXTENSIONS
    assert ".jpg" in SUPPORTED_ALL_EXTENSIONS
    assert ".webp" in SUPPORTED_ALL_EXTENSIONS
    assert ".tiff" in SUPPORTED_ALL_EXTENSIONS
