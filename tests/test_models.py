"""
اختبارات نماذج البيانات (Models) لنظام نَصّ (NASS).
"""

from pathlib import Path
from app.core.models import DocumentResult, FileType, PageResult, ProcessingStatus


def test_page_result_defaults():
    """اختبار القيم الافتراضية لنتيجة الصفحة."""
    page = PageResult(page_number=1)
    assert page.page_number == 1
    assert page.text == ""
    assert page.confidence == 0.0
    assert page.status == ProcessingStatus.PENDING
    assert not page.is_embedded_text


def test_document_result_properties():
    """اختبار حساب متوسط الثقة وتجميع النص الكامل للمستند."""
    p1 = PageResult(page_number=1, text="الصفحة الأولى", confidence=90.0)
    p2 = PageResult(page_number=2, text="Page Two", confidence=80.0)
    p3 = PageResult(page_number=3, text="", confidence=0.0)  # صفحة فارغة

    doc = DocumentResult(
        file_path=Path("sample.pdf"),
        file_type=FileType.PDF,
        file_size_bytes=1024,
        total_pages=3,
        pages=[p1, p2, p3],
    )

    # التحقق من النص الكامل
    full = doc.full_text
    assert "الصفحة الأولى" in full
    assert "Page Two" in full
    assert "--- [فاصل الصفحات] ---" in full

    # التحقق من متوسط الثقة (تجاهل الصفحات ذات الثقة الصفرية)
    assert doc.average_confidence == 85.0
