"""
اختبارات خدمة التصدير (Export Service) لملفات TXT و DOCX.
"""

from pathlib import Path
from app.core.models import DocumentResult, FileType, PageResult, ProcessingStatus
from app.services.export_service import ExportService


def test_export_to_txt(tmp_path: Path):
    """التحقق من تصدير النصوص إلى TXT بترميز UTF-8 وفواصل واضحة."""
    p1 = PageResult(page_number=1, text="مرحباً بكم في مشروع نَصّ", confidence=95.0)
    p2 = PageResult(page_number=2, text="Welcome to NASS OCR", confidence=98.0)

    doc = DocumentResult(
        file_path=Path("sample_doc.pdf"),
        file_type=FileType.PDF,
        file_size_bytes=2048,
        total_pages=2,
        pages=[p1, p2],
        status=ProcessingStatus.COMPLETED,
    )

    out_file = tmp_path / "output.txt"
    ExportService.export_to_txt(doc, out_file)

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "مرحباً بكم في مشروع نَصّ" in content
    assert "Welcome to NASS OCR" in content
    assert "الصفحة 1" in content
    assert "الصفحة 2" in content


def test_export_to_docx(tmp_path: Path):
    """التحقق من إنشاء ملف Word (DOCX) بنجاح."""
    p1 = PageResult(page_number=1, text="فقرة باللغة العربية داخل ملف وورد", confidence=90.0)

    doc = DocumentResult(
        file_path=Path("arabic.pdf"),
        file_type=FileType.PDF,
        file_size_bytes=1000,
        total_pages=1,
        pages=[p1],
        status=ProcessingStatus.COMPLETED,
    )

    out_file = tmp_path / "output.docx"
    ExportService.export_to_docx(doc, out_file)

    assert out_file.exists()
    assert out_file.stat().st_size > 0
