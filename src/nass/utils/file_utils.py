"""
File discovery, type identification, and size utilities for the NASS application.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Set, Tuple

from nass.core.config import (
    EXCEL_EXTENSIONS,
    IMAGE_EXTENSIONS,
    JSON_EXTENSIONS,
    MARKUP_EXTENSIONS,
    OPENDOC_EXTENSIONS,
    PDF_EXTENSIONS,
    POWERPOINT_EXTENSIONS,
    SUPPORTED_ALL_EXTENSIONS,
    TEXT_EXTENSIONS,
    WORD_EXTENSIONS,
)
from nass.core.models import FileType
from nass.utils.logger import logger


class FileUtils:
    """Utility methods for file identification, validation, and discovery."""

    @staticmethod
    def detect_file_type(file_path: Path) -> FileType:
        """Identify the FileType category based on the file suffix."""
        suffix = file_path.suffix.lower()
        if suffix in PDF_EXTENSIONS:
            return FileType.PDF
        elif suffix in IMAGE_EXTENSIONS:
            return FileType.IMAGE
        elif suffix in WORD_EXTENSIONS:
            return FileType.WORD
        elif suffix in EXCEL_EXTENSIONS:
            return FileType.EXCEL
        elif suffix in POWERPOINT_EXTENSIONS:
            return FileType.POWERPOINT
        elif suffix in TEXT_EXTENSIONS:
            return FileType.TEXT
        elif suffix in MARKUP_EXTENSIONS:
            return FileType.MARKUP
        elif suffix in JSON_EXTENSIONS:
            return FileType.JSON
        elif suffix in OPENDOC_EXTENSIONS:
            return FileType.OPENDOC
        return FileType.UNKNOWN

    @classmethod
    def is_valid_file(cls, path: Path) -> Tuple[bool, Optional[str]]:
        """
        Check if the path exists, is a non-empty readable file, and has a supported extension.
        Returns: (is_valid, error_message).
        """
        if not path.exists():
            return False, "الملف المحدد غير موجود على القرص."

        if not path.is_file():
            return False, "المسار المحدد هو مجلد وليس ملفاً صالحاً."

        try:
            size = path.stat().st_size
            if size == 0:
                return False, "الملف فارغ بحجم (0 بايت)."
        except Exception as e:
            return False, f"تعذر قراءة بيانات الملف: {e}"

        file_type = cls.detect_file_type(path)
        if file_type == FileType.UNKNOWN:
            return False, f"صيغة الملف '{path.suffix}' غير مدعومة حالياً."

        return True, None

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format byte size into human readable string."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"

    @classmethod
    def discover_files(
        cls,
        paths: List[Path | str],
        recursive: bool = True,
    ) -> List[Path]:
        """
        Scan paths and folders for supported document files, avoiding duplicates.
        """
        collected: Set[Path] = set()

        for p_input in paths:
            path = Path(p_input).resolve()
            if not path.exists():
                logger.warning(f"Path does not exist: {path}")
                continue

            if path.is_file():
                valid, _ = cls.is_valid_file(path)
                if valid:
                    collected.add(path)
            elif path.is_dir():
                pattern = "**/*" if recursive else "*"
                for entry in path.glob(pattern):
                    if entry.is_file():
                        valid, _ = cls.is_valid_file(entry)
                        if valid:
                            collected.add(entry.resolve())

        return sorted(list(collected), key=lambda p: str(p).lower())
