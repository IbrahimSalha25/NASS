"""
نماذج البيانات الأساسية لنظام نَصّ (NASS).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class ProcessingStatus(str, Enum):
    """حالات معالجة الملفات والصفحات."""
    PENDING = "pending"          # بانتظار المعالجة
    PROCESSING = "processing"    # جاري المعالجة
    COMPLETED = "completed"      # اكتملت بنجاح
    FAILED = "failed"            # فشلت المعالجة
    SKIPPED = "skipped"          # تم تخطيها
    CANCELLED = "cancelled"      # أُلغيت من قِبل المستخدم


class FileType(str, Enum):
    """أنواع الملفات المدعومة."""
    PDF = "pdf"
    IMAGE = "image"
    UNKNOWN = "unknown"


class OcrLanguage(str, Enum):
    """خيارات اللغات المدعومة افتراضياً."""
    ARABIC = "ara"
    ENGLISH = "eng"
    ARABIC_AND_ENGLISH = "ara+eng"


@dataclass
class PageResult:
    """بيانات نتيجة استخراج صفحة واحدة من مستند أو صورة."""
    page_number: int
    text: str = ""
    confidence: float = 0.0
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    is_embedded_text: bool = False  # هل النص مستخرج مباشرة من PDF بدون OCR


@dataclass
class DocumentResult:
    """بيانات نتيجة معالجة ملف مستند بالكامل (صورة أو PDF)."""
    file_path: Path
    file_type: FileType
    file_size_bytes: int
    total_pages: int = 1
    pages: List[PageResult] = field(default_factory=list)
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    total_duration_seconds: float = 0.0

    @property
    def full_text(self) -> str:
        """تجميع النص الكامل لكافة صفحات المستند مع فواصل واضحة."""
        page_texts = [p.text for p in self.pages if p.text.strip()]
        return "\n\n--- [فاصل الصفحات] ---\n\n".join(page_texts)

    @property
    def average_confidence(self) -> float:
        """حساب متوسط نسبة الثقة عبر الصفحات التي تحتوي نصاً وثقة صالحة."""
        valid_confidences = [
            p.confidence for p in self.pages
            if p.confidence > 0 and not p.is_embedded_text
        ]
        if not valid_confidences:
            return 100.0 if any(p.is_embedded_text for p in self.pages) else 0.0
        return sum(valid_confidences) / len(valid_confidences)


@dataclass
class OcrOptions:
    """خيارات وإعدادات تنفيذ OCR."""
    language: str = OcrLanguage.ARABIC_AND_ENGLISH.value
    apply_enhancement: bool = False
    enhance_contrast: bool = False
    denoise: bool = False
    threshold: bool = False
    deskew: bool = False
    dpi: int = 300
    extract_embedded_first: bool = True  # محاولة استخراج النص المضمن في PDF أولاً
