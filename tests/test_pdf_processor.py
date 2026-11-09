"""
Tests for PDF processing module (PdfProcessor).
"""

from pathlib import Path
import pytest
from PIL import Image

from app.core.pdf_processor import PdfProcessor


def test_pdf_info_non_existent():
    """Verify raising FileNotFoundError when passed a non-existent file path."""
    with pytest.raises(FileNotFoundError):
        PdfProcessor.get_document_info(Path("non_existent_file.pdf"))


def test_pdf_embedded_text_and_render(tmp_path: Path):
    """Test extracting embedded digital text and rendering pages to raster images using PyMuPDF."""
    import fitz

    # Create a test PDF document
    pdf_path = tmp_path / "test_doc.pdf"
    doc = fitz.open()

    page1 = doc.new_page(width=595, height=842)
    # Insert long text on first page (> 30 characters)
    sample_text = "This is a comprehensive test document containing extractable embedded text for NASS application."
    page1.insert_text((50, 100), sample_text, fontsize=14)

    page2 = doc.new_page(width=595, height=842)
    page2.insert_text((50, 100), "Short text", fontsize=12)

    doc.save(str(pdf_path))
    doc.close()

    # 1. Test document metadata extraction
    page_count, is_encrypted, has_text = PdfProcessor.get_document_info(pdf_path)
    assert page_count == 2
    assert not is_encrypted
    assert has_text is True

    # 2. Test extracting embedded text and page image rendering
    doc_read = fitz.open(str(pdf_path))
    try:
        p1 = doc_read[0]
        embedded = PdfProcessor.extract_embedded_text_page(p1)
        assert "comprehensive test document" in embedded

        # Render page to PIL image
        img = PdfProcessor.render_page_to_image(p1, dpi=150)
        assert isinstance(img, Image.Image)
        assert img.width > 0
        assert img.height > 0
    finally:
        doc_read.close()
