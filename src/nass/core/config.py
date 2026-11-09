"""
Core configuration and constants for the NASS project.
Handles project paths, executable discovery, and supported file extensions.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional, Set

# Application metadata
APP_NAME = "نَصّ | NASS"
APP_VERSION = "1.0.0"
APP_SLOGAN = "حيث تتحول الصور إلى كلمات."
APP_ORGANIZATION = "NASS"
APP_DESCRIPTION = "Smart OCR & Document Text Extraction Desktop Application"

# Project path resolution
# src/nass/core/config.py -> 3 levels up is repository root
CONFIG_FILE_PATH = Path(__file__).resolve()
SRC_DIR = CONFIG_FILE_PATH.parent.parent.parent
PROJECT_ROOT = SRC_DIR.parent

ASSETS_DIR = PROJECT_ROOT / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
LOCAL_TESSDATA = PROJECT_ROOT / "tessdata"
DEFAULT_LOGO_PATH = IMAGES_DIR / "logo_NASS.png"
if not DEFAULT_LOGO_PATH.exists() and (PROJECT_ROOT / "logo_NASS.png").exists():
    DEFAULT_LOGO_PATH = PROJECT_ROOT / "logo_NASS.png"

# Default discovery paths for Tesseract on Windows systems
WINDOWS_DEFAULT_TESSERACT_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Tesseract-OCR" / "tesseract.exe",
]

# Supported file extension categories
IMAGE_EXTENSIONS: Set[str] = {
    ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"
}
PDF_EXTENSIONS: Set[str] = {
    ".pdf"
}
WORD_EXTENSIONS: Set[str] = {
    ".docx"
}
EXCEL_EXTENSIONS: Set[str] = {
    ".xlsx", ".xls", ".csv"
}
POWERPOINT_EXTENSIONS: Set[str] = {
    ".pptx"
}
TEXT_EXTENSIONS: Set[str] = {
    ".txt", ".md", ".rtf"
}
MARKUP_EXTENSIONS: Set[str] = {
    ".html", ".htm", ".xml"
}
JSON_EXTENSIONS: Set[str] = {
    ".json"
}
OPENDOC_EXTENSIONS: Set[str] = {
    ".odt", ".ods", ".odp", ".epub"
}

SUPPORTED_ALL_EXTENSIONS: Set[str] = (
    IMAGE_EXTENSIONS
    | PDF_EXTENSIONS
    | WORD_EXTENSIONS
    | EXCEL_EXTENSIONS
    | POWERPOINT_EXTENSIONS
    | TEXT_EXTENSIONS
    | MARKUP_EXTENSIONS
    | JSON_EXTENSIONS
    | OPENDOC_EXTENSIONS
)


def find_tesseract_executable() -> Optional[Path]:
    """
    Locate the Tesseract executable path.
    Checks user custom setting, environment variable, system PATH, and common Windows locations.
    """
    try:
        from nass.core.settings import SettingsManager
        custom_path = SettingsManager.get_instance().get("tesseract_custom_path")
        if custom_path:
            p = Path(custom_path)
            if p.is_file():
                return p
    except Exception:
        pass

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
    """
    Locate the tessdata directory containing trained language files.
    """
    try:
        from nass.core.settings import SettingsManager
        custom_tessdata = SettingsManager.get_instance().get("tessdata_custom_path")
        if custom_tessdata:
            p = Path(custom_tessdata)
            if p.is_dir() and list(p.glob("*.traineddata")):
                return p
    except Exception:
        pass

    # 1. Local project tessdata directory if it contains language packs
    if LOCAL_TESSDATA.is_dir():
        trained_files = list(LOCAL_TESSDATA.glob("*.traineddata"))
        if trained_files:
            return LOCAL_TESSDATA

    # 2. Environment variable TESSDATA_PREFIX
    env_prefix = os.environ.get("TESSDATA_PREFIX")
    if env_prefix:
        p = Path(env_prefix)
        if p.is_dir() and list(p.glob("*.traineddata")):
            return p

    # 3. Next to tesseract executable directory
    tess_exe = find_tesseract_executable()
    if tess_exe:
        parent_tessdata = tess_exe.parent / "tessdata"
        if parent_tessdata.is_dir() and list(parent_tessdata.glob("*.traineddata")):
            return parent_tessdata

    if LOCAL_TESSDATA.is_dir():
        return LOCAL_TESSDATA

    return None


def configure_pytesseract():
    """
    Configure pytesseract executable path and TESSDATA_PREFIX environment variable.
    """
    import pytesseract

    exe_path = find_tesseract_executable()
    if exe_path:
        pytesseract.pytesseract.tesseract_cmd = str(exe_path)

    tessdata_dir = find_tessdata_directory()
    if tessdata_dir:
        os.environ["TESSDATA_PREFIX"] = str(tessdata_dir)
