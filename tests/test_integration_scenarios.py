"""
Integration scenario tests verifying project acceptance criteria and workflows.
"""

import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import pytest

from app.core.file_manager import FileManager
from app.core.models import FileType, OcrOptions, ProcessingStatus
from app.core.ocr_engine import OcrEngine
from app.core.tesseract_manager import TesseractManager
from app.services.export_service import ExportService
from app.services.processing_service import ProcessingService


@pytest.fixture
def sample_english_image(tmp_path: Path) -> Path:
    """Create a clean English synthetic test image."""
    img_path = tmp_path / "test_english.png"
    img = Image.new("RGB", (400, 100), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 35), "Hello World 123", fill="black")
    img.save(img_path)
    return img_path


@pytest.fixture
def sample_multipage_pdf(tmp_path: Path) -> Path:
    """Create a two-page synthetic test PDF."""
    pdf_path = tmp_path / "test_multipage.pdf"
    doc = fitz.open()

    p1 = doc.new_page()
    p1.insert_text((50, 50), "First Page English Text", fontsize=16)

    p2 = doc.new_page()
    p2.insert_text((50, 50), "Second Page Formula y = 2*x + 1", fontsize=16)

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def test_scenario_tesseract_discovery():
    """Scenarios 1 & 2: Inspect and verify Tesseract OCR engine discovery."""
    mgr = TesseractManager()
    status = mgr.get_engine_status()
    assert "is_installed" in status
    assert "available_languages" in status
    assert "platform" in status


def test_scenario_english_image_processing(sample_english_image: Path):
    """Scenario 8: Process English image file."""
    service = ProcessingService()
    opts = OcrOptions(language="eng", psm=3)
    res = service.process_image_file(sample_english_image, opts)
    assert res.status == ProcessingStatus.COMPLETED
    assert len(res.pages) == 1
    assert "Hello" in res.pages[0].text or "123" in res.pages[0].text


def test_scenario_multipage_pdf_processing(sample_multipage_pdf: Path):
    """Scenario 10: Process multipage PDF document sequentially."""
    service = ProcessingService()
    opts = OcrOptions(language="eng", extract_embedded_first=True)
    res = service.process_pdf_file(sample_multipage_pdf, opts)

    assert res.status == ProcessingStatus.COMPLETED
    assert res.total_pages == 2
    assert len(res.pages) == 2
    assert "First Page" in res.pages[0].text
    assert "Second Page" in res.pages[1].text


def test_scenario_math_recognition_enabled(sample_multipage_pdf: Path):
    """Scenarios 11 & 12: Extract math formulas and test enabling/disabling."""
    service = ProcessingService()

    # 1. Math extraction enabled
    opts_with_math = OcrOptions(language="eng", extract_math=True, extract_embedded_first=True)
    res_math = service.process_pdf_file(sample_multipage_pdf, opts_with_math)
    assert res_math.status == ProcessingStatus.COMPLETED
    assert len(res_math.pages[1].equations) > 0
    assert "2 \\times x" in res_math.pages[1].equations[0] or "y" in res_math.pages[1].equations[0]

    # 2. Math extraction disabled
    opts_no_math = OcrOptions(language="eng", extract_math=False, extract_embedded_first=True)
    res_no_math = service.process_pdf_file(sample_multipage_pdf, opts_no_math)
    assert len(res_no_math.pages[1].equations) == 0


def test_scenario_cancellation(sample_multipage_pdf: Path):
    """Scenario 13: Mid-page extraction cancellation."""
    service = ProcessingService()
    opts = OcrOptions(language="eng", extract_embedded_first=False)

    call_count = [0]

    def cancel_after_page_one():
        call_count[0] += 1
        return call_count[0] >= 1

    res = service.process_pdf_file(
        sample_multipage_pdf,
        options=opts,
        cancel_check=cancel_after_page_one,
    )
    assert res.status == ProcessingStatus.CANCELLED
    assert len(res.pages) < 2


def test_scenario_export_formats(sample_multipage_pdf: Path, tmp_path: Path):
    """Scenario 14: Export extraction results to TXT, DOCX, and LaTeX."""
    service = ProcessingService()
    opts = OcrOptions(language="eng", extract_math=True, extract_embedded_first=True)
    doc_res = service.process_pdf_file(sample_multipage_pdf, opts)

    txt_path = tmp_path / "export.txt"
    docx_path = tmp_path / "export.docx"
    tex_path = tmp_path / "export.tex"

    ExportService.export_to_txt(doc_res, txt_path)
    ExportService.export_to_docx(doc_res, docx_path)
    ExportService.export_to_latex(doc_res, tex_path)

    assert txt_path.exists() and txt_path.stat().st_size > 50
    assert docx_path.exists() and docx_path.stat().st_size > 1000
    assert tex_path.exists() and "\\documentclass" in tex_path.read_text(encoding="utf-8")


def test_scenario_corrupt_file_handling(tmp_path: Path):
    """Scenario 15: Handle corrupted file gracefully with clear error message."""
    corrupt_pdf = tmp_path / "corrupt.pdf"
    corrupt_pdf.write_bytes(b"NOT_A_VALID_PDF_HEADER_12345")

    service = ProcessingService()
    opts = OcrOptions()
    res = service.process_pdf_file(corrupt_pdf, opts)
    assert res.status == ProcessingStatus.FAILED
    assert res.error_message is not None
    assert "تعذر فتح" in res.error_message or "تالف" in res.error_message
