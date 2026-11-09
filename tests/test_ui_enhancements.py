"""
Unit and UI tests for NASS UI enhancements:
1. Drag & drop file acceptance in HomeView, ExtractView, and MainWindow.
2. Sidebar button layout direction and RTL/LTR alignment.
3. History view re-scanning (existing file vs missing file).
4. Application language setting and dynamic switching (Arabic/English).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PySide6.QtCore import QMimeData, QPointF, Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QApplication

from nass.core.i18n import I18n, tr
from nass.core.models import DocumentResult, FileType, ProcessingStatus
from nass.core.settings import SettingsManager
from nass.ui.components.sidebar import SidebarWidget
from nass.ui.main_window import MainWindow
from nass.ui.views.app_settings_view import AppSettingsView
from nass.ui.views.history_view import HistoryRecord, HistoryView
from nass.ui.views.home_view import HomeView


@pytest.fixture
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    f = tmp_path / "test_doc.txt"
    f.write_text("Hello NASS", encoding="utf-8")
    return f


# ---------------------------------------------------------------------------
# 1. Drag & Drop Tests
# ---------------------------------------------------------------------------
def test_home_view_drag_and_drop(qapp, sample_file: Path):
    view = HomeView()
    assert view.acceptDrops() is True
    assert view.drop_card.acceptDrops() is True

    selected_paths = []
    view.file_selected.connect(selected_paths.append)

    # Simulate drag enter
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(sample_file))])
    
    enter_event = QDragEnterEvent(
        QPointF(50, 50).toPoint(),
        Qt.CopyAction,
        mime,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    view.dragEnterEvent(enter_event)
    assert enter_event.isAccepted() is True

    # Simulate drop
    drop_event = QDropEvent(
        QPointF(50, 50).toPoint(),
        Qt.CopyAction,
        mime,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    view.dropEvent(drop_event)
    assert len(selected_paths) == 1
    assert selected_paths[0] == sample_file


def test_main_window_drag_and_drop(qapp, sample_file: Path):
    window = MainWindow()
    assert window.acceptDrops() is True

    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(sample_file))])

    drop_event = QDropEvent(
        QPointF(100, 100).toPoint(),
        Qt.CopyAction,
        mime,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    window.dropEvent(drop_event)

    # Should transition to ExtractView with loaded file
    assert window.stack.currentIndex() == 1
    assert window.extract_view.current_file == sample_file


# ---------------------------------------------------------------------------
# 2. Sidebar Navigation Layout Direction & Alignment
# ---------------------------------------------------------------------------
def test_sidebar_layout_direction_rtl_and_ltr(qapp):
    I18n.set_current_language("ar")
    sidebar = SidebarWidget()
    assert sidebar.layoutDirection() == Qt.RightToLeft
    for btn in sidebar.buttons:
        assert btn.layoutDirection() == Qt.RightToLeft

    # Switch to English
    I18n.set_current_language("en")
    sidebar.retranslate_ui()
    assert sidebar.layoutDirection() == Qt.LeftToRight
    for btn in sidebar.buttons:
        assert btn.layoutDirection() == Qt.LeftToRight

    # Reset to Arabic default
    I18n.set_current_language("ar")
    sidebar.retranslate_ui()
    assert sidebar.layoutDirection() == Qt.RightToLeft


# ---------------------------------------------------------------------------
# 3. History Re-scan Tests
# ---------------------------------------------------------------------------
def test_history_rescan_file_exists(qapp, sample_file: Path, monkeypatch, tmp_path: Path):
    # Use temporary file for history storage to isolate test
    fake_storage = tmp_path / "temp_history.json"
    import nass.ui.views.history_view as hv
    monkeypatch.setattr(hv, "HISTORY_STORAGE_FILE", fake_storage)

    history = HistoryView()
    history.records.clear()
    doc_res = DocumentResult(
        file_path=sample_file,
        file_type=FileType.TEXT,
        file_size_bytes=sample_file.stat().st_size,
        status=ProcessingStatus.COMPLETED,
    )
    history.add_record_from_result(doc_res)
    assert len(history.records) == 1

    rescanned_paths = []
    history.rescan_requested.connect(rescanned_paths.append)

    # Monkeypatch QMessageBox.information to automatically accept
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok)

    history._rescan_record(history.records[0])
    assert len(rescanned_paths) == 1
    assert rescanned_paths[0] == sample_file


def test_history_rescan_file_missing(qapp, tmp_path: Path, monkeypatch):
    fake_storage = tmp_path / "temp_history.json"
    import nass.ui.views.history_view as hv
    monkeypatch.setattr(hv, "HISTORY_STORAGE_FILE", fake_storage)

    missing_file = tmp_path / "deleted_file.txt"
    history = HistoryView()
    history.records.clear()
    rec = HistoryRecord(
        timestamp="2026-11-09 12:00:00",
        file_name="deleted_file.txt",
        file_path=str(missing_file),
        file_type="TEXT",
        extraction_method="نص رقمي مباشر",
        total_pages=1,
        confidence=100.0,
        text_content="some text",
        status="اكتمل بنجاح",
    )
    history.records.append(rec)
    history._refresh_table()

    rescanned_paths = []
    history.rescan_requested.connect(rescanned_paths.append)

    # Monkeypatch QMessageBox.warning to simulate user declining manual location
    from PySide6.QtWidgets import QMessageBox
    warning_called = []
    def mock_warning(*args, **kwargs):
        warning_called.append(True)
        return QMessageBox.No

    monkeypatch.setattr(QMessageBox, "warning", mock_warning)
    history._rescan_record(history.records[0])

    assert len(warning_called) == 1
    assert len(rescanned_paths) == 0  # Not rescanned because user declined


# ---------------------------------------------------------------------------
# 4. Language Settings & i18n Switching Tests
# ---------------------------------------------------------------------------
def test_i18n_translation():
    I18n.set_current_language("ar")
    assert tr("app_slogan") == "حيث تتحول الصور إلى كلمات."
    assert tr("nav_home") == "الرئيسية"
    assert I18n.is_rtl() is True

    I18n.set_current_language("en")
    assert tr("app_slogan") == "Where images become words."
    assert tr("nav_home") == "Home"
    assert I18n.is_rtl() is False

    # Restore Arabic default
    I18n.set_current_language("ar")


def test_main_window_apply_language(qapp):
    window = MainWindow()

    # Apply English
    window.apply_language("en")
    assert window.layoutDirection() == Qt.LeftToRight
    assert "Home" in window.sidebar.buttons[0].text()
    assert I18n.get_current_language() == "en"

    # Apply Arabic
    window.apply_language("ar")
    assert window.layoutDirection() == Qt.RightToLeft
    assert "الرئيسية" in window.sidebar.buttons[0].text()
    assert I18n.get_current_language() == "ar"


# ---------------------------------------------------------------------------
# 5. History Retention Limit (Default 50) Tests
# ---------------------------------------------------------------------------
def test_history_max_records_retention(qapp, tmp_path: Path):
    history = HistoryView()
    history.records.clear()
    history.settings.set("max_history_records", 5)

    for i in range(10):
        f = tmp_path / f"file_{i}.txt"
        f.write_text(f"content {i}", encoding="utf-8")
        res = DocumentResult(
            file_path=f,
            file_type=FileType.TEXT,
            file_size_bytes=10,
            status=ProcessingStatus.COMPLETED,
        )
        history.add_record_from_result(res)

    # Should only retain the last 5 records
    assert len(history.records) == 5
    assert history.records[0].file_name == "file_9.txt"
    assert history.records[-1].file_name == "file_5.txt"

    # Reset setting to default 50
    history.settings.set("max_history_records", 50)


def test_app_settings_view_max_history(qapp, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok)

    view = AppSettingsView()
    assert view.spin_max_history.value() >= 5
    view.spin_max_history.setValue(75)
    view._save_settings()
    assert SettingsManager.get_instance().get("max_history_records") == 75

    # Restore default
    view.spin_max_history.setValue(50)
    view._save_settings()
    assert SettingsManager.get_instance().get("max_history_records") == 50


# ---------------------------------------------------------------------------
# 6. ExtractView Bilingual Elements & Responsive Sizing
# ---------------------------------------------------------------------------
def test_extract_view_bilingual_texts(qapp, sample_file: Path):
    from nass.ui.views.extract_view import ExtractView

    view = ExtractView()
    view.load_file(sample_file)

    # Arabic mode
    I18n.set_current_language("ar")
    view.retranslate_ui()
    assert "بدء استخراج النص" in view.btn_start.text() or "استخراج" in view.btn_start.text()
    assert "إيقاف" in view.btn_cancel.text() or "إلغاء" in view.btn_cancel.text()
    assert "تصدير TXT" in view.btn_export_txt.text()
    assert "تصدير Word" in view.btn_export_docx.text()
    assert "إعدادات استخراج المحتوى" in view.lbl_opts_title.text()

    # English mode
    I18n.set_current_language("en")
    view.retranslate_ui()
    assert "Start Extraction" in view.btn_start.text()
    assert "Stop" in view.btn_cancel.text() or "Cancel" in view.btn_cancel.text()
    assert "Export TXT" in view.btn_export_txt.text()
    assert "Export Word" in view.btn_export_docx.text()
    assert "Extraction Options" in view.lbl_opts_title.text()

    # Restore Arabic default
    I18n.set_current_language("ar")


def test_main_window_responsive_minimum_size(qapp):
    window = MainWindow()
    min_size = window.minimumSize()
    # Ensure minimum width <= 900 and height <= 600 for small displays
    assert min_size.width() <= 900
    assert min_size.height() <= 600

