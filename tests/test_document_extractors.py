"""
Unit and integration tests for NASS multi-format document extractors.
Tests extraction from Word (DOCX), Excel (XLSX, CSV), PowerPoint (PPTX),
Plain text (TXT, MD, RTF), Web/Markup (HTML, XML), JSON, and OpenDocument/eBooks (ODT, EPUB).
"""

from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path

import pytest
from docx import Document
from openpyxl import Workbook
from pptx import Presentation
from pptx.util import Inches

from nass.core.models import ExtractionMethod, FileType, OcrOptions, ProcessingStatus
from nass.engines.document.document_engine import DocumentEngine
from nass.processors.docx_processor import DocxExtractor
from nass.processors.excel_processor import ExcelExtractor
from nass.processors.json_processor import JsonExtractor
from nass.processors.markup_processor import MarkupExtractor
from nass.processors.opendoc_processor import OpenDocumentExtractor
from nass.processors.powerpoint_processor import PowerPointExtractor
from nass.processors.text_processor import TextExtractor


@pytest.fixture
def temp_docs_dir(tmp_path: Path) -> Path:
    d = tmp_path / "test_docs"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# 1. Word (DOCX) Extractor Tests
# ---------------------------------------------------------------------------
def test_docx_extractor(temp_docs_dir: Path):
    doc_path = temp_docs_dir / "sample.docx"
    doc = Document()
    doc.add_heading("عنوان المستند", level=1)
    doc.add_paragraph("هذه فقرة تجريبية باللغة العربية داخل ملف وورد.")
    
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "الاسم"
    table.cell(0, 1).text = "العمر"
    table.cell(1, 0).text = "إبراهيم"
    table.cell(1, 1).text = "22"
    doc.save(str(doc_path))

    extractor = DocxExtractor()
    assert extractor.can_handle(doc_path)

    res = extractor.extract(doc_path, OcrOptions())
    assert res.status == ProcessingStatus.COMPLETED
    assert res.file_type == FileType.WORD
    assert res.extraction_method == ExtractionMethod.NATIVE
    assert "عنوان المستند" in res.full_text
    assert "إبراهيم" in res.full_text
    assert "22" in res.full_text
    assert res.average_confidence == 100.0


# ---------------------------------------------------------------------------
# 2. Excel (XLSX) & CSV Extractor Tests
# ---------------------------------------------------------------------------
def test_excel_extractor(temp_docs_dir: Path):
    xlsx_path = temp_docs_dir / "sample.xlsx"
    wb = Workbook()
    ws1 = wb.active
    ws1.title = "المبيعات"
    ws1.append(["المنتج", "الكمية", "السعر"])
    ws1.append(["برنامج نَصّ", 10, 500])

    ws2 = wb.create_sheet(title="المستخدمين")
    ws2.append(["المعرف", "الاسم"])
    ws2.append([101, "أحمد"])
    wb.save(str(xlsx_path))

    extractor = ExcelExtractor()
    assert extractor.can_handle(xlsx_path)

    res = extractor.extract(xlsx_path, OcrOptions())
    assert res.status == ProcessingStatus.COMPLETED
    assert res.file_type == FileType.EXCEL
    assert res.extraction_method == ExtractionMethod.NATIVE
    assert "المبيعات" in res.full_text
    assert "برنامج نَصّ" in res.full_text
    assert "المستخدمين" in res.full_text
    assert "أحمد" in res.full_text
    assert res.total_pages == 2


def test_csv_extractor(temp_docs_dir: Path):
    csv_path = temp_docs_dir / "sample.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Score"])
        writer.writerow([1, "Ibrahim", 99.5])
        writer.writerow([2, "Ali", 95.0])

    extractor = ExcelExtractor()
    assert extractor.can_handle(csv_path)

    res = extractor.extract(csv_path, OcrOptions())
    assert res.status == ProcessingStatus.COMPLETED
    assert res.file_type == FileType.EXCEL
    assert "Ibrahim" in res.full_text
    assert "99.5" in res.full_text


# ---------------------------------------------------------------------------
# 3. PowerPoint (PPTX) Extractor Tests
# ---------------------------------------------------------------------------
def test_pptx_extractor(temp_docs_dir: Path):
    pptx_path = temp_docs_dir / "sample.pptx"
    prs = Presentation()
    blank_slide_layout = prs.slide_layouts[6]

    # Slide 1
    slide1 = prs.slides.add_slide(blank_slide_layout)
    tx_box1 = slide1.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(2))
    tf1 = tx_box1.text_frame
    tf1.text = "مقدمة عن تطبيق نَصّ NASS"

    # Slide 2
    slide2 = prs.slides.add_slide(blank_slide_layout)
    tx_box2 = slide2.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(2))
    tf2 = tx_box2.text_frame
    tf2.text = "الشريحة الثانية: مميزات الاستخراج الذكي"
    prs.save(str(pptx_path))

    extractor = PowerPointExtractor()
    assert extractor.can_handle(pptx_path)

    res = extractor.extract(pptx_path, OcrOptions())
    assert res.status == ProcessingStatus.COMPLETED
    assert res.file_type == FileType.POWERPOINT
    assert res.total_pages == 2
    assert "مقدمة عن تطبيق نَصّ" in res.full_text
    assert "الشريحة الثانية" in res.full_text


# ---------------------------------------------------------------------------
# 4. Plain Text, Markdown & RTF Extractor Tests
# ---------------------------------------------------------------------------
def test_plain_text_and_markdown_extractor(temp_docs_dir: Path):
    txt_path = temp_docs_dir / "notes.txt"
    txt_path.write_text("هذا ملف نص عادي بسيط.\nالسطر الثاني.", encoding="utf-8")

    txt_ext = TextExtractor()
    assert txt_ext.can_handle(txt_path)
    res_txt = txt_ext.extract(txt_path, OcrOptions())
    assert res_txt.status == ProcessingStatus.COMPLETED
    assert "هذا ملف نص عادي بسيط" in res_txt.full_text

    md_path = temp_docs_dir / "README.md"
    md_path.write_text("# عنوان رئيسي\n\n- نقطة 1\n- نقطة 2", encoding="utf-8")
    assert txt_ext.can_handle(md_path)
    res_md = txt_ext.extract(md_path, OcrOptions())
    assert res_md.status == ProcessingStatus.COMPLETED
    assert "عنوان رئيسي" in res_md.full_text


def test_rtf_extractor(temp_docs_dir: Path):
    rtf_path = temp_docs_dir / "document.rtf"
    rtf_content = r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Courier;}}\f0\fs24 Hello \b World\b0!}"
    rtf_path.write_text(rtf_content, encoding="ascii")

    txt_ext = TextExtractor()
    assert txt_ext.can_handle(rtf_path)
    res = txt_ext.extract(rtf_path, OcrOptions())
    assert res.status == ProcessingStatus.COMPLETED
    assert "Hello" in res.full_text
    assert "World" in res.full_text


# ---------------------------------------------------------------------------
# 5. Markup (HTML, XML) Extractor Tests
# ---------------------------------------------------------------------------
def test_html_and_xml_extractor(temp_docs_dir: Path):
    html_path = temp_docs_dir / "page.html"
    html_content = (
        "<!DOCTYPE html><html><head><title>NASS</title></head>"
        "<body><h1>عنوان رئيسي</h1><p>فقرة تجريبية داخل HTML.</p></body></html>"
    )
    html_path.write_text(html_content, encoding="utf-8")

    markup_ext = MarkupExtractor()
    assert markup_ext.can_handle(html_path)
    res_html = markup_ext.extract(html_path, OcrOptions())
    assert res_html.status == ProcessingStatus.COMPLETED
    assert "عنوان رئيسي" in res_html.full_text
    assert "فقرة تجريبية" in res_html.full_text
    assert "<p>" not in res_html.full_text

    xml_path = temp_docs_dir / "data.xml"
    xml_content = (
        "<dataset><item id='1'><title>مشروع نَصّ</title><author>إبراهيم</author></item></dataset>"
    )
    xml_path.write_text(xml_content, encoding="utf-8")
    assert markup_ext.can_handle(xml_path)
    res_xml = markup_ext.extract(xml_path, OcrOptions())
    assert res_xml.status == ProcessingStatus.COMPLETED
    assert "مشروع نَصّ" in res_xml.full_text
    assert "إبراهيم" in res_xml.full_text


# ---------------------------------------------------------------------------
# 6. JSON Extractor Tests
# ---------------------------------------------------------------------------
def test_json_extractor(temp_docs_dir: Path):
    json_path = temp_docs_dir / "config.json"
    data = {
        "app_name": "نَصّ | NASS",
        "developer": {
            "name": "Ibrahim Salha",
            "role": "Computer Engineering Student",
            "skills": ["Python", "Computer Vision", "AI"]
        },
        "settings": {
            "theme": "navy",
            "port": 8080
        }
    }
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    json_ext = JsonExtractor()
    assert json_ext.can_handle(json_path)
    res = json_ext.extract(json_path, OcrOptions())
    assert res.status == ProcessingStatus.COMPLETED
    assert "نَصّ | NASS" in res.full_text
    assert "Ibrahim Salha" in res.full_text
    assert "Computer Vision" in res.full_text


# ---------------------------------------------------------------------------
# 7. OpenDocument (ODT) & EPUB Extractor Tests
# ---------------------------------------------------------------------------
def test_odt_extractor(temp_docs_dir: Path):
    odt_path = temp_docs_dir / "sample.odt"
    content_xml = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        b'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
        b'<office:body><office:text>'
        b'<text:h text:outline-level="1">\xd9\x85\xd8\xb3\xd8\xaa\xd9\x86\xd8\xaf ODT \xd8\xaa\xd8\xac\xd8\xb1\xd9\x8a\xd8\xa8\xd9\x8a</text:h>'
        b'<text:p>\xd9\x86\xd8\xb5 \xd8\xaf\xd8\xa7\xd8\xae\xd9\x84 \xd8\xa7\xd9\x84\xd9\x81\xd9\x82\xd8\xb1\xd8\xa9.</text:p>'
        b'</office:text></office:body></office:document-content>'
    )
    with zipfile.ZipFile(odt_path, "w") as zf:
        zf.writestr("content.xml", content_xml)

    opendoc_ext = OpenDocumentExtractor()
    assert opendoc_ext.can_handle(odt_path)
    res = opendoc_ext.extract(odt_path, OcrOptions())
    assert res.status == ProcessingStatus.COMPLETED
    assert "مستند ODT تجريبي" in res.full_text
    assert "نص داخل الفقرة" in res.full_text


def test_epub_extractor(temp_docs_dir: Path):
    epub_path = temp_docs_dir / "book.epub"
    chapter1 = (
        "<?xml version='1.0' encoding='utf-8'?>\n"
        "<html><head><title>Chapter 1</title></head>"
        "<body><h1>الفصل الأول</h1><p>بداية الكتاب الرقمي.</p></body></html>"
    )
    chapter2 = (
        "<?xml version='1.0' encoding='utf-8'?>\n"
        "<html><head><title>Chapter 2</title></head>"
        "<body><h1>الفصل الثاني</h1><p>استمرار القراءة.</p></body></html>"
    )
    with zipfile.ZipFile(epub_path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("OEBPS/chapter1.xhtml", chapter1.encode("utf-8"))
        zf.writestr("OEBPS/chapter2.xhtml", chapter2.encode("utf-8"))

    opendoc_ext = OpenDocumentExtractor()
    assert opendoc_ext.can_handle(epub_path)
    res = opendoc_ext.extract(epub_path, OcrOptions())
    assert res.status == ProcessingStatus.COMPLETED
    assert res.total_pages == 2
    assert "الفصل الأول" in res.full_text
    assert "الفصل الثاني" in res.full_text


# ---------------------------------------------------------------------------
# 8. DocumentEngine Unified Dispatcher Test
# ---------------------------------------------------------------------------
def test_document_engine_dispatch(temp_docs_dir: Path):
    engine = DocumentEngine.get_instance()
    
    # Test JSON dispatch
    json_path = temp_docs_dir / "test_engine.json"
    json_path.write_text('{"greeting": "مرحبا بالعالم"}', encoding="utf-8")
    res = engine.process_file(json_path)
    assert res.status == ProcessingStatus.COMPLETED
    assert "مرحبا بالعالم" in res.full_text

    # Test Markdown dispatch
    md_path = temp_docs_dir / "test_engine.md"
    md_path.write_text("# عنوان الاختبار", encoding="utf-8")
    res_md = engine.process_file(md_path)
    assert res_md.status == ProcessingStatus.COMPLETED
    assert "عنوان الاختبار" in res_md.full_text
