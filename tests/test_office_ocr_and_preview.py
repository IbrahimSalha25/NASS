"""
Comprehensive unit and integration tests for embedded image extraction, document OCR, and multi-format preview services.
Covers Word (DOCX), PowerPoint (PPTX), Excel (XLSX), and PDF files.
"""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock

import fitz
import openpyxl
import pytest
from docx import Document
from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.util import Inches

from nass.core.models import (
    DocumentResult,
    ExtractionMethod,
    FileType,
    OcrOptions,
    PageResult,
    ProcessingStatus,
)
from nass.engines.document.document_engine import DocumentEngine
from nass.processors.docx_processor import DocxExtractor
from nass.processors.excel_processor import ExcelExtractor
from nass.processors.pdf_processor import PdfExtractor
from nass.processors.powerpoint_processor import PowerPointExtractor
from nass.services.image_ocr_service import DocumentImageOcrService, ExtractedImageItem
from nass.services.preview_service import DocumentPreviewService


def _create_sample_png(text: str = "Test") -> bytes:
    """Helper creating a valid in-memory PNG image."""
    img = Image.new("RGB", (120, 60), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 20), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def test_dir(tmp_path: Path) -> Path:
    d = tmp_path / "office_ocr_tests"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# 1. DocumentImageOcrService tests
# ---------------------------------------------------------------------------
def test_image_ocr_service_processing():
    mock_ocr = MagicMock()
    mock_ocr.extract_text.return_value = PageResult(
        page_number=1,
        text="نص مستخرج تجريبي",
        confidence=95.0,
        status=ProcessingStatus.COMPLETED,
    )

    service = DocumentImageOcrService(ocr_engine=mock_ocr)
    item = ExtractedImageItem(
        item_id="test_1",
        source_location="صفحة 1",
        image_bytes=_create_sample_png("NASS"),
        page_or_section=1,
    )

    opts = OcrOptions(apply_enhancement=True, grayscale=True)
    res = service.process_image_item(item, opts)

    assert res.status == ProcessingStatus.COMPLETED
    assert res.ocr_text == "نص مستخرج تجريبي"
    assert res.confidence == 95.0
    assert mock_ocr.extract_text.called


def test_image_ocr_service_corrupt_data():
    service = DocumentImageOcrService()
    corrupted_item = ExtractedImageItem(
        item_id="corrupt_1",
        source_location="صفحة 2",
        image_bytes=b"not an image binary",
    )
    res = service.process_image_item(corrupted_item, OcrOptions())
    assert res.status == ProcessingStatus.FAILED
    assert "تعذر قراءة بيانات الصورة" in res.error_message


# ---------------------------------------------------------------------------
# 2. Word (DOCX) Embedded Image Extraction & OCR
# ---------------------------------------------------------------------------
def test_docx_embedded_image_ocr(test_dir: Path):
    doc_path = test_dir / "sample_images.docx"
    doc = Document()
    doc.add_heading("مستند يحتوي صوراً", level=1)
    doc.add_paragraph("نص الفقرة الأساسية داخل الوورد.")

    img_data = _create_sample_png("نص الصورة")
    doc.add_picture(io.BytesIO(img_data))
    doc.save(str(doc_path))

    mock_ocr_service = MagicMock(spec=DocumentImageOcrService)

    def fake_batch(items, options, cancel_check=None):
        for im in items:
            im.ocr_text = "استخراج ذكي لصورة الوورد"
            im.confidence = 94.0
            im.status = ProcessingStatus.COMPLETED
        return items

    mock_ocr_service.process_image_items_batch.side_effect = fake_batch

    extractor = DocxExtractor(image_ocr_service=mock_ocr_service)

    # A) Test with both Native & Images OCR enabled
    opts = OcrOptions(extract_native_text=True, extract_images_ocr=True)
    res = extractor.extract(doc_path, opts)

    assert res.status == ProcessingStatus.COMPLETED
    assert len(res.pages) == 1
    page = res.pages[0]
    assert "نص الفقرة الأساسية" in page.native_text
    assert "استخراج ذكي لصورة الوورد" in page.image_ocr_text
    assert page.image_count == 1
    assert res.extraction_method == ExtractionMethod.HYBRID

    # B) Test with Images OCR disabled
    opts_no_ocr = OcrOptions(extract_native_text=True, extract_images_ocr=False)
    res_no_ocr = extractor.extract(doc_path, opts_no_ocr)
    assert res_no_ocr.pages[0].image_count == 0
    assert not res_no_ocr.pages[0].image_ocr_text


# ---------------------------------------------------------------------------
# 3. PowerPoint (PPTX) Embedded Image Extraction & OCR
# ---------------------------------------------------------------------------
def test_pptx_embedded_image_ocr(test_dir: Path):
    pptx_path = test_dir / "sample_presentation.pptx"
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "عنوان العرض التقديمي"

    img_bytes = _create_sample_png("نص شريحة باوربوينت")
    slide.shapes.add_picture(io.BytesIO(img_bytes), Inches(1), Inches(1), Inches(2), Inches(1))
    prs.save(str(pptx_path))

    mock_ocr_service = MagicMock(spec=DocumentImageOcrService)

    def fake_batch_pptx(items, options, cancel_check=None):
        for im in items:
            im.ocr_text = "نص مستخرج من صورة الشريحة"
            im.confidence = 92.5
            im.status = ProcessingStatus.COMPLETED
        return items

    mock_ocr_service.process_image_items_batch.side_effect = fake_batch_pptx

    extractor = PowerPointExtractor(image_ocr_service=mock_ocr_service)
    opts = OcrOptions(extract_native_text=True, extract_images_ocr=True)
    res = extractor.extract(pptx_path, opts)

    assert res.status == ProcessingStatus.COMPLETED
    assert len(res.pages) == 1
    slide_res = res.pages[0]
    assert "عنوان العرض التقديمي" in slide_res.native_text
    assert "نص مستخرج من صورة الشريحة" in slide_res.image_ocr_text
    assert slide_res.image_count == 1
    assert "شريحة 1 - صورة #1" in slide_res.image_details[0]["location"]


# ---------------------------------------------------------------------------
# 4. Excel (XLSX) Embedded Image Extraction & OCR
# ---------------------------------------------------------------------------
def test_excel_embedded_image_ocr(test_dir: Path):
    xlsx_path = test_dir / "sample_sheet.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "البيانات المالية"
    ws["A1"] = "الإيرادات"
    ws["B1"] = 50000

    img_bytes = _create_sample_png("رسم بياني")
    xl_img = openpyxl.drawing.image.Image(io.BytesIO(img_bytes))
    ws.add_image(xl_img, "D2")
    wb.save(str(xlsx_path))

    mock_ocr_service = MagicMock(spec=DocumentImageOcrService)

    def fake_batch_xl(items, options, cancel_check=None):
        for im in items:
            im.ocr_text = "نص داخل صورة الإكسل"
            im.confidence = 90.0
            im.status = ProcessingStatus.COMPLETED
        return items

    mock_ocr_service.process_image_items_batch.side_effect = fake_batch_xl

    extractor = ExcelExtractor(image_ocr_service=mock_ocr_service)
    opts = OcrOptions(extract_native_text=True, extract_images_ocr=True)
    res = extractor.extract(xlsx_path, opts)

    assert res.status == ProcessingStatus.COMPLETED
    sheet_res = res.pages[0]
    assert "الإيرادات" in sheet_res.native_text
    assert "نص داخل صورة الإكسل" in sheet_res.image_ocr_text
    assert sheet_res.image_count == 1
    assert "البيانات المالية" in sheet_res.image_details[0]["location"]


# ---------------------------------------------------------------------------
# 5. PDF Embedded Image Extraction & OCR
# ---------------------------------------------------------------------------
def test_pdf_embedded_image_ocr(test_dir: Path):
    pdf_path = test_dir / "sample_pdf_with_image.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Sample embedded native text inside PDF document that exceeds thirty characters.")

    img_bytes = _create_sample_png("مخطط توضيحي داخل PDF")
    page.insert_image(fitz.Rect(50, 100, 200, 200), stream=img_bytes)
    doc.save(str(pdf_path))
    doc.close()

    mock_ocr_service = MagicMock(spec=DocumentImageOcrService)

    def fake_batch_pdf(items, options, cancel_check=None):
        for im in items:
            im.ocr_text = "نص الصورة داخل البي دي إف"
            im.confidence = 96.0
            im.status = ProcessingStatus.COMPLETED
        return items

    mock_ocr_service.process_image_items_batch.side_effect = fake_batch_pdf

    extractor = PdfExtractor(image_ocr_service=mock_ocr_service)
    opts = OcrOptions(extract_native_text=True, extract_images_ocr=True, extract_embedded_first=True)
    res = extractor.extract(pdf_path, opts)

    assert res.status == ProcessingStatus.COMPLETED
    assert len(res.pages) == 1
    p_res = res.pages[0]
    assert "Sample embedded native text" in p_res.native_text
    assert "نص الصورة داخل البي دي إف" in p_res.image_ocr_text
    assert p_res.image_count == 1


# ---------------------------------------------------------------------------
# 6. DocumentPreviewService tests
# ---------------------------------------------------------------------------
def test_document_preview_page_counts(test_dir: Path):
    # DOCX
    docx_file = test_dir / "doc_preview.docx"
    d = Document()
    d.add_paragraph("Paragraph 1")
    d.save(str(docx_file))
    assert DocumentPreviewService.get_document_page_count(docx_file) >= 1

    # PPTX
    pptx_file = test_dir / "prs_preview.pptx"
    p = Presentation()
    p.slides.add_slide(p.slide_layouts[0])
    p.slides.add_slide(p.slide_layouts[1])
    p.save(str(pptx_file))
    assert DocumentPreviewService.get_document_page_count(pptx_file) == 2

    # XLSX
    xlsx_file = test_dir / "sheet_preview.xlsx"
    w = openpyxl.Workbook()
    w.create_sheet("Sheet 2")
    w.save(str(xlsx_file))
    assert DocumentPreviewService.get_document_page_count(xlsx_file) == 2


def test_document_preview_rendering(test_dir: Path):
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    docx_file = test_dir / "render_test.docx"
    d = Document()
    d.add_heading("عنوان المستند للمعاينة", level=1)
    d.add_paragraph("هذا نص المعاينة البصرية داخل التطبيق.")
    d.save(str(docx_file))

    pix = DocumentPreviewService.render_page_preview(docx_file, page_num=1, target_width=350)
    assert not pix.isNull()
    assert pix.width() == 350
    assert pix.height() > 200
