"""
Tests for UI/UX improvements:
1. Label transparent backgrounds.
2. Sidebar RTL menu items alignment to right edge with icons adjacent to text.
3. PDF page navigation buttons [ - ] 3 / 12 [ + ].
4. Batch Folder Text Extraction (BatchFolderView) and CSV export.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from nass.core.i18n import I18n, tr
from nass.core.models import (
    DocumentResult,
    FileType,
    PageResult,
    ProcessingStatus,
)
from nass.services.export_service import ExportService
from nass.ui.components.sidebar import SidebarNavButton, SidebarWidget
from nass.ui.styles import APP_STYLESHEET
from nass.ui.views.batch_folder_view import BatchFolderView
from nass.ui.views.extract_view import ExtractView


@pytest.fixture
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


# ---------------------------------------------------------------------------
# 1. Transparent Labels & Stylesheet Checks
# ---------------------------------------------------------------------------
def test_label_transparency_in_stylesheet():
    """Verify that QLabel transparent background rule is defined in stylesheet."""
    assert "QLabel {" in APP_STYLESHEET
    assert "background-color: transparent;" in APP_STYLESHEET


# ---------------------------------------------------------------------------
# 2. Sidebar Alignment & RTL Layout
# ---------------------------------------------------------------------------
def test_sidebar_nav_button_rtl_alignment(qapp):
    """Verify SidebarNavButton layout aligns icon to the right and text next to it in RTL."""
    from PySide6.QtGui import QIcon
    I18n.set_current_language("ar")
    btn = SidebarNavButton("home", "اختبار", QIcon())
    assert btn.text() == "اختبار"
    assert btn.layoutDirection() == Qt.RightToLeft

    # Switch to LTR
    btn.set_direction(is_rtl=False)
    assert btn.layoutDirection() == Qt.LeftToRight


def test_sidebar_widget_batch_nav_button(qapp):
    """Verify sidebar includes the batch folder navigation button."""
    I18n.set_current_language("ar")
    sidebar = SidebarWidget()
    # Find batch folder button
    batch_btn = None
    for b in sidebar.buttons:
        if b.text() == tr("nav_batch_folder"):
            batch_btn = b
            break
    assert batch_btn is not None


# ---------------------------------------------------------------------------
# 3. Direct PDF Page Navigation [ - ] Page / Total [ + ]
# ---------------------------------------------------------------------------
def test_extract_view_page_navigation(qapp, tmp_path: Path, monkeypatch):
    """Test PDF page navigation controls update counters and button states."""
    view = ExtractView()
    test_pdf = tmp_path / "sample.pdf"
    test_pdf.write_bytes(b"%PDF-1.4 test")

    view.current_file = test_pdf
    # Stub preview rendering to avoid loading invalid mock pdf with fitz
    monkeypatch.setattr(view, "_render_current_page_preview", lambda p: None)

    view._update_page_nav(1, 10)

    assert view.lbl_page_counter.text() == "1 / 10"
    assert view.btn_prev_page.isEnabled() is False
    assert view.btn_next_page.isEnabled() is True

    # Navigate next
    view._go_next_page()
    assert view.current_preview_page == 2
    assert view.lbl_page_counter.text() == "2 / 10"
    assert view.btn_prev_page.isEnabled() is True
    assert view.btn_next_page.isEnabled() is True

    # Jump to last page
    view._update_page_nav(10, 10)
    assert view.btn_prev_page.isEnabled() is True
    assert view.btn_next_page.isEnabled() is False


# ---------------------------------------------------------------------------
# 4. Batch Folder View & CSV Export Tests
# ---------------------------------------------------------------------------
def test_batch_folder_view_initial_state(qapp):
    """Test initial state of BatchFolderView."""
    view = BatchFolderView()
    assert view.current_folder is None
    assert len(view.discovered_files) == 0
    assert view.btn_start.isEnabled() is False
    assert view.btn_cancel.isEnabled() is False
    assert view.btn_copy_merged.isEnabled() is True


def test_batch_folder_csv_export(tmp_path: Path):
    """Test CSV export functionality with UTF-8-sig encoding for Arabic text."""
    p1 = PageResult(page_number=1, text="نص مستخرج من الملف الأول", confidence=95.0)
    p2 = PageResult(page_number=2, text="الصفحة الثانية", confidence=95.0)
    doc1 = DocumentResult(
        file_path=tmp_path / "file1.pdf",
        file_type=FileType.PDF,
        file_size_bytes=1024,
        status=ProcessingStatus.COMPLETED,
        total_pages=2,
        pages=[p1, p2],
    )

    p_img = PageResult(page_number=1, text="نص باللغة العربية والإنجليزية Hello World", confidence=98.0)
    doc2 = DocumentResult(
        file_path=tmp_path / "file2.png",
        file_type=FileType.IMAGE,
        file_size_bytes=2048,
        status=ProcessingStatus.COMPLETED,
        total_pages=1,
        pages=[p_img],
    )

    csv_path = tmp_path / "exported_results.csv"
    res_path = ExportService.export_to_csv([doc1, doc2], csv_path)
    assert res_path == csv_path
    assert csv_path.exists()

    content = csv_path.read_text(encoding="utf-8-sig")
    assert "file1.pdf" in content
    assert "file2.png" in content
    assert "PDF" in content
    assert "IMAGE" in content
