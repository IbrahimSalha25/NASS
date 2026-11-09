"""
Tests for UI/UX & logic polish:
1. Sidebar Tesseract OCR status card detection & semantic styling.
2. Checkbox & action button high-contrast styles.
3. OCR Settings English text LTR rendering and table alignment.
4. History single record deletion action with confirmation.
5. About screen full Arabic localization and developer social/repo links.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from nass.core.i18n import I18n, tr
from nass.core.models import DocumentResult, FileType, ProcessingStatus
from nass.ui.components.sidebar import SidebarWidget
from nass.ui.main_window import MainWindow
from nass.ui.styles import APP_STYLESHEET
from nass.ui.views.about_view import AboutView
from nass.ui.views.history_view import HistoryRecord, HistoryView
from nass.ui.views.ocr_settings_view import OcrSettingsView


@pytest.fixture
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


# ---------------------------------------------------------------------------
# 1. Sidebar Tesseract Detection & Semantic Card Styling
# ---------------------------------------------------------------------------
def test_sidebar_engine_status_styling(qapp):
    sidebar = SidebarWidget()

    # Installed state (green subtle semantic)
    sidebar.update_engine_status(is_installed=True, version="5.5.0")
    assert "v5.5.0" in sidebar.lbl_engine_status.text()
    assert "34D399" in sidebar.lbl_engine_status.styleSheet()

    # Missing state (muted red subtle semantic)
    sidebar.update_engine_status(is_installed=False)
    assert tr("engine_status_not_installed") in sidebar.lbl_engine_status.text()
    assert "F87171" in sidebar.lbl_engine_status.styleSheet()


def test_main_window_refreshes_engine_status_on_launch(qapp):
    window = MainWindow()
    # Should automatically verify Tesseract status on init
    assert window.sidebar._last_installed is True or window.sidebar._last_installed is False


# ---------------------------------------------------------------------------
# 2. Checkboxes & Action Buttons Contrast
# ---------------------------------------------------------------------------
def test_checkbox_contrast_in_stylesheet():
    assert "QCheckBox::indicator:checked" in APP_STYLESHEET
    assert "QCheckBox::indicator:hover" in APP_STYLESHEET
    assert "QPushButton#primaryButton:disabled" in APP_STYLESHEET
    assert "QPushButton#dangerButton:disabled" in APP_STYLESHEET


# ---------------------------------------------------------------------------
# 3. OCR Settings English Text Alignment & Rendering
# ---------------------------------------------------------------------------
def test_ocr_settings_ltr_for_technical_values(qapp):
    view = OcrSettingsView()
    assert view.lbl_version_val.layoutDirection() == Qt.LeftToRight
    assert view.lbl_exe_path_val.layoutDirection() == Qt.LeftToRight
    assert view.lbl_tessdata_val.layoutDirection() == Qt.LeftToRight
    assert view.lbl_pytesseract_val.layoutDirection() == Qt.LeftToRight


# ---------------------------------------------------------------------------
# 4. History Single Record Deletion Action
# ---------------------------------------------------------------------------
def test_history_single_record_deletion(qapp, tmp_path: Path, monkeypatch):
    import nass.ui.views.history_view as hv
    fake_storage = tmp_path / "temp_history.json"
    monkeypatch.setattr(hv, "HISTORY_STORAGE_FILE", fake_storage)

    history = HistoryView()
    history.records.clear()

    rec1 = HistoryRecord(
        timestamp="2026-11-09 10:00:00",
        file_name="doc1.pdf",
        file_path=str(tmp_path / "doc1.pdf"),
        file_type="PDF",
        extraction_method="مباشر",
        total_pages=1,
        confidence=100.0,
        text_content="Page 1",
        status="مكتمل",
    )
    rec2 = HistoryRecord(
        timestamp="2026-11-09 11:00:00",
        file_name="doc2.pdf",
        file_path=str(tmp_path / "doc2.pdf"),
        file_type="PDF",
        extraction_method="مباشر",
        total_pages=1,
        confidence=100.0,
        text_content="Page 2",
        status="مكتمل",
    )
    history.records.extend([rec1, rec2])
    history._refresh_table()
    assert len(history.records) == 2

    # Mock user accepting deletion confirmation dialog
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)

    # Delete first record
    history._delete_single_record(rec1)
    assert len(history.records) == 1
    assert history.records[0].file_name == "doc2.pdf"


# ---------------------------------------------------------------------------
# 5. About View Translations & Links
# ---------------------------------------------------------------------------
def test_about_view_arabic_localization_and_links(qapp):
    I18n.set_current_language("ar")
    about = AboutView()
    about.retranslate_ui()

    assert about.lbl_main_title.text() == "حول التطبيق"
    assert about.lbl_dev_heading.text() == "بطاقة المطور"
    assert "إبراهيم صالحة" in about.lbl_dev_name.text()
    assert about.btn_github.text() == "حساب GitHub"
    assert about.btn_linkedin.text() == "حساب LinkedIn"
    assert about.btn_email.text() == "البريد الإلكتروني"
    assert about.btn_repo.text() == "مستودع المشروع على GitHub"
