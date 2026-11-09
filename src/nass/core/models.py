"""
Data models and representations for the NASS application.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class ProcessingStatus(str, Enum):
    """Execution status for document and page processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class FileType(str, Enum):
    """Categorized file types supported by NASS."""
    IMAGE = "image"
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"
    TEXT = "text"
    MARKUP = "markup"
    JSON = "json"
    OPENDOC = "opendocument"
    UNKNOWN = "unknown"

    @property
    def display_name_ar(self) -> str:
        names = {
            FileType.IMAGE: "صورة",
            FileType.PDF: "مستند PDF",
            FileType.WORD: "مستند وورد (Word)",
            FileType.EXCEL: "جدول بيانات (Excel/CSV)",
            FileType.POWERPOINT: "عرض تقديمي (PowerPoint)",
            FileType.TEXT: "ملف نصي (Plain Text)",
            FileType.MARKUP: "ملف ويب (HTML/XML)",
            FileType.JSON: "بيانات مهيكلة (JSON)",
            FileType.OPENDOC: "مستند مفتوح (OpenDocument/EPUB)",
            FileType.UNKNOWN: "ملف غير مدعوم",
        }
        return names.get(self, "ملف")


class ExtractionMethod(str, Enum):
    """Method used to extract text from a file or page."""
    NATIVE = "native"
    OCR = "ocr"
    HYBRID = "hybrid"

    @property
    def display_name_ar(self) -> str:
        names = {
            ExtractionMethod.NATIVE: "استخراج مباشر (بدون OCR)",
            ExtractionMethod.OCR: "محرك Tesseract OCR",
            ExtractionMethod.HYBRID: "معالجة هجينة (مباشر + OCR)",
        }
        return names.get(self, "استخراج")


class OcrLanguage(str, Enum):
    """Common OCR language presets."""
    ARABIC = "ara"
    ENGLISH = "eng"
    ARABIC_AND_ENGLISH = "ara+eng"


@dataclass
class PageResult:
    """Extraction result for a single page, sheet, slide, or section."""
    page_number: int
    title: Optional[str] = None
    text: str = ""
    equations: List[str] = field(default_factory=list)
    confidence: float = 0.0
    status: ProcessingStatus = ProcessingStatus.PENDING
    extraction_method: ExtractionMethod = ExtractionMethod.NATIVE
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    is_embedded_text: bool = True


@dataclass
class DocumentResult:
    """Complete extraction result for a processed document or file."""
    file_path: Path
    file_type: FileType
    file_size_bytes: int
    total_pages: int = 1
    pages: List[PageResult] = field(default_factory=list)
    status: ProcessingStatus = ProcessingStatus.PENDING
    extraction_method: ExtractionMethod = ExtractionMethod.NATIVE
    error_message: Optional[str] = None
    total_duration_seconds: float = 0.0

    @property
    def full_text(self) -> str:
        """Concatenate all page texts with clear section separators."""
        page_texts = []
        for p in self.pages:
            t = p.text.strip()
            if t:
                if p.title:
                    page_texts.append(f"=== {p.title} ===\n{t}")
                else:
                    page_texts.append(t)
        return "\n\n--- [فاصل الصفحات] ---\n\n".join(page_texts)

    @property
    def all_equations(self) -> List[str]:
        """Aggregate all extracted LaTeX equations."""
        equations: List[str] = []
        for p in self.pages:
            equations.extend(p.equations)
        return equations

    @property
    def average_confidence(self) -> float:
        """Calculate average confidence score across pages that required OCR."""
        ocr_confidences = [
            p.confidence for p in self.pages
            if p.confidence > 0 and p.extraction_method == ExtractionMethod.OCR
        ]
        if not ocr_confidences:
            # Native extraction has 100% confidence
            return 100.0 if any(p.status == ProcessingStatus.COMPLETED for p in self.pages) else 0.0
        return sum(ocr_confidences) / len(ocr_confidences)

    @property
    def method_display_name(self) -> str:
        """Human-readable Arabic representation of extraction method."""
        return self.extraction_method.display_name_ar


@dataclass
class OcrOptions:
    """Options and parameters for document processing and OCR."""
    language: str = OcrLanguage.ARABIC_AND_ENGLISH.value
    apply_enhancement: bool = False
    grayscale: bool = False
    enhance_contrast: bool = False
    denoise: bool = False
    threshold: bool = False
    deskew: bool = False
    single_column: bool = False
    dpi: int = 300
    psm: int = 3
    oem: int = 3
    tesseract_config: str = ""
    extract_embedded_first: bool = True
    extract_math: bool = False
    math_engine: str = "builtin"
