"""
مدير استكشاف والتحقق من الملفات والمجلدات لنظام نَصّ (NASS).
يدعم المسارات العربية والمسافات ويتحقق من صلاحية الملفات.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Set, Tuple

from app.config import (
    SUPPORTED_ALL_EXTENSIONS,
    SUPPORTED_DOCUMENT_EXTENSIONS,
    SUPPORTED_IMAGE_EXTENSIONS,
)
from app.core.models import FileType
from app.utils.logger import logger


class FileManager:
    """إدارة واستكشاف ملفات الإدخال والتحقق من سلامتها."""

    @staticmethod
    def detect_file_type(file_path: Path) -> FileType:
        """تحديد نوع الملف (صورة أو PDF أو غير معروف)."""
        suffix = file_path.suffix.lower()
        if suffix in SUPPORTED_DOCUMENT_EXTENSIONS:
            return FileType.PDF
        elif suffix in SUPPORTED_IMAGE_EXTENSIONS:
            return FileType.IMAGE
        return FileType.UNKNOWN

    @classmethod
    def is_valid_file(cls, path: Path) -> Tuple[bool, Optional[str]]:
        """
        التحقق من إمكانية قراءة الملف وسلامته الأولية.
        يعيد (هل_الملف_صالح، رسالة_الخطأ_إن_وجدت).
        """
        if not path.exists():
            return False, "الملف غير موجود."

        if not path.is_file():
            return False, "المسار ليس ملفاً."

        try:
            size = path.stat().st_size
            if size == 0:
                return False, "الملف فارغ (0 بايت)."
        except Exception as e:
            return False, f"تعذر قراءة بيانات الملف: {e}"

        file_type = cls.detect_file_type(path)
        if file_type == FileType.UNKNOWN:
            return False, f"صيغة الملف '{path.suffix}' غير مدعومة."

        return True, None

    @classmethod
    def discover_files(
        cls,
        paths: List[Path | str],
        recursive: bool = True,
    ) -> List[Path]:
        """
        استكشاف واستخراج جميع الملفات المدعومة من قائمة مسارات أو مجلدات.
        يضمن عدم تكرار الملفات وترتيبها منطقياً.
        """
        collected: Set[Path] = set()

        for p_input in paths:
            path = Path(p_input).resolve()
            if not path.exists():
                logger.warning(f"المسار غير موجود: {path}")
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

        # ترتيب النتائج أبجدياً مع مراعاة الأحرف العربية
        return sorted(list(collected), key=lambda p: str(p).lower())
