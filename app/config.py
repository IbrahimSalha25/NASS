"""
إعدادات وثوابت مشروع نَصّ (NASS).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional

# المسارات الأساسية للمشروع
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_TESSDATA = PROJECT_ROOT / "tessdata"

# المسارات الافتراضية للبحث عن Tesseract على نظام Windows
WINDOWS_DEFAULT_TESSERACT_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Tesseract-OCR" / "tesseract.exe",
]

# الامتدادات المدعومة
SUPPORTED_IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"
}
SUPPORTED_DOCUMENT_EXTENSIONS = {
    ".pdf"
}
SUPPORTED_ALL_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_DOCUMENT_EXTENSIONS


def find_tesseract_executable() -> Optional[Path]:
    """البحث عن مسار Tesseract القابل للتنفيذ."""
    env_tess = os.environ.get("TESSERACT_CMD")
    if env_tess:
        p = Path(env_tess)
        if p.is_file():
            return p

    which_tess = shutil.which("tesseract")
    if which_tess:
        return Path(which_tess)

    for win_path in WINDOWS_DEFAULT_TESSERACT_PATHS:
        if win_path.is_file():
            return win_path

    return None


def find_tessdata_directory() -> Optional[Path]:
    """البحث عن مجلد ملفات اللغات (tessdata)."""
    # 1. المجلد المحلي داخل المشروع إذا احتوى على ملفات
    if LOCAL_TESSDATA.is_dir():
        trained_files = list(LOCAL_TESSDATA.glob("*.traineddata"))
        if trained_files:
            return LOCAL_TESSDATA

    # 2. متغير البيئة TESSDATA_PREFIX
    env_prefix = os.environ.get("TESSDATA_PREFIX")
    if env_prefix:
        p = Path(env_prefix)
        if p.is_dir() and list(p.glob("*.traineddata")):
            return p

    # 3. بجانب tesseract.exe
    tess_exe = find_tesseract_executable()
    if tess_exe:
        parent_tessdata = tess_exe.parent / "tessdata"
        if parent_tessdata.is_dir() and list(parent_tessdata.glob("*.traineddata")):
            return parent_tessdata

    if LOCAL_TESSDATA.is_dir():
        return LOCAL_TESSDATA

    return None


def configure_pytesseract():
    """تهيئة pytesseract وتعيين مسار التنفيذ ومتغير TESSDATA_PREFIX."""
    import pytesseract

    exe_path = find_tesseract_executable()
    if exe_path:
        pytesseract.pytesseract.tesseract_cmd = str(exe_path)

    tessdata_dir = find_tessdata_directory()
    if tessdata_dir:
        os.environ["TESSDATA_PREFIX"] = str(tessdata_dir)
