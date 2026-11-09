"""
Tests for domain models (Models) in NASS.
"""

from pathlib import Path
from app.core.models import DocumentResult, FileType, PageResult, ProcessingStatus


def test_page_result_defaults():
    """Test default values of PageResult instance."""
    page = PageResult(page_number=1)
    assert page.page_number == 1
    assert page.text == ""
    assert page.confidence == 0.0
    assert page.status == ProcessingStatus.PENDING
    assert not page.is_embedded_text


def test_document_result_properties():
    """Test average confidence computation and full text aggregation for DocumentResult."""
    p1 = PageResult(page_number=1, text="الصفحة الأولى", confidence=90.0)
    p2 = PageResult(page_number=2, text="Page Two", confidence=80.0)
    p3 = PageResult(page_number=3, text="", confidence=0.0)  # Empty page

    doc = DocumentResult(
        file_path=Path("sample.pdf"),
        file_type=FileType.PDF,
        file_size_bytes=1024,
        total_pages=3,
        pages=[p1, p2, p3],
    )

    # Verify full text aggregation
    full = doc.full_text
    assert "الصفحة الأولى" in full
    assert "Page Two" in full
    assert "--- [فاصل الصفحات] ---" in full

    # Verify average confidence (ignoring zero-confidence pages)
    assert doc.average_confidence == 85.0
