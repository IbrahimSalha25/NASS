"""
Main application window for NASS.
Implements the multi-page stack, right-hand sidebar navigation, RTL layout,
and cohesive Deep Navy / Royal Blue styling.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from nass.core.config import APP_NAME, APP_VERSION, ASSETS_DIR, PROJECT_ROOT
from nass.core.models import DocumentResult
from nass.core.settings import SettingsManager
from nass.engines.ocr.tesseract_manager import TesseractManager
from nass.ui.components.sidebar import SidebarWidget
from nass.ui.styles import APP_STYLESHEET
from nass.ui.views.about_view import AboutView
from nass.ui.views.app_settings_view import AppSettingsView
from nass.ui.views.extract_view import ExtractView
from nass.ui.views.history_view import HistoryView
from nass.ui.views.home_view import HomeView
from nass.ui.views.ocr_settings_view import OcrSettingsView
from nass.utils.file_utils import FileUtils
from nass.utils.logger import logger


class MainWindow(QMainWindow):
    """
    Main application window hosting all views and handling view orchestration.
    """

    def __init__(self) -> None:
        super().__init__()
        self.settings = SettingsManager.get_instance()
        self.tess_mgr = TesseractManager()

        self.setWindowTitle(f"{APP_NAME} — Smart Document & OCR Extractor (v{APP_VERSION})")
        
        width = self.settings.get("window_width", 1200)
        height = self.settings.get("window_height", 800)
        self.resize(width, height)
        self.setMinimumSize(980, 640)
        self.setLayoutDirection(Qt.RightToLeft)

        # Set application window icon
        logo_path = ASSETS_DIR / "images" / "logo_NASS.png"
        if not logo_path.exists():
            logo_path = PROJECT_ROOT / "logo_NASS.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self._init_ui()
        self._connect_signals()
        self.setStyleSheet(APP_STYLESHEET)
        logger.info("MainWindow initialized successfully.")

    def _init_ui(self) -> None:
        """Constructs UI layout: right sidebar and stacked view container."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Right Sidebar (first in RTL puts it on the right)
        self.sidebar = SidebarWidget(self)
        root_layout.addWidget(self.sidebar)

        # 2. Main content stack
        self.stack = QStackedWidget(self)

        # Page 0: Home view
        self.home_view = HomeView(self)
        self.stack.addWidget(self.home_view)

        # Page 1: Extract view
        self.extract_view = ExtractView(self)
        self.stack.addWidget(self.extract_view)

        # Page 2: History view
        self.history_view = HistoryView(self)
        self.stack.addWidget(self.history_view)

        # Page 3: OCR Settings view
        self.ocr_settings_view = OcrSettingsView(self)
        self.stack.addWidget(self.ocr_settings_view)

        # Page 4: General App Settings view
        self.app_settings_view = AppSettingsView(self)
        self.stack.addWidget(self.app_settings_view)

        # Page 5: About view
        self.about_view = AboutView(self)
        self.stack.addWidget(self.about_view)

        root_layout.addWidget(self.stack, stretch=1)

    def _connect_signals(self) -> None:
        """Connects signals across sidebar and views."""
        # Sidebar navigation
        self.sidebar.page_changed.connect(self.switch_page)

        # Home view transitions
        self.home_view.file_selected.connect(self._on_file_selected_from_home)
        self.home_view.navigate_to_settings.connect(lambda: self.switch_page(3))

        # Extract view events
        self.extract_view.change_file_requested.connect(self._select_new_file)
        self.extract_view.btn_start.clicked.connect(self._bind_worker_to_history)

        # Settings synchronization
        self.ocr_settings_view.settings_updated.connect(self._on_settings_updated)
        self.app_settings_view.settings_changed.connect(self._on_settings_updated)

    def switch_page(self, page_index: int) -> None:
        """
        Switches currently visible view and updates sidebar selection state.

        Args:
            page_index: Index of the target page in QStackedWidget.
        """
        self.stack.setCurrentIndex(page_index)
        self.sidebar.set_active_page(page_index)

    def _on_file_selected_from_home(self, file_path: Path) -> None:
        """Loads file selected from home view and transitions to extract view."""
        self.extract_view.load_file(file_path)
        self.switch_page(1)

    def _select_new_file(self) -> None:
        """Opens native file chooser for all supported document types."""
        filters = (
            "جميع الملفات المدعومة (*.pdf *.png *.jpg *.jpeg *.tiff *.tif *.bmp *.webp "
            "*.docx *.xlsx *.xls *.csv *.pptx *.txt *.md *.rtf *.html *.htm *.xml *.json *.odt *.epub);;"
            "مستندات PDF (*.pdf);;"
            "ملفات الصور (*.png *.jpg *.jpeg *.tiff *.tif *.bmp *.webp);;"
            "مستندات Word (*.docx);;"
            "جداول Excel وبيانات (*.xlsx *.xls *.csv);;"
            "عروض PowerPoint (*.pptx);;"
            "ملفات نصية وماركداون (*.txt *.md *.rtf);;"
            "ملفات ويب وبرمجة (*.html *.htm *.xml *.json);;"
            "مستندات مفتوحة وكتب (*.odt *.epub);;"
            "جميع الملفات (*.*)"
        )
        file_path_str, _ = QFileDialog.getOpenFileName(
            self,
            "اختيار ملف للاستخراج",
            "",
            filters,
        )
        if file_path_str:
            p = Path(file_path_str).resolve()
            valid, _ = FileUtils.is_valid_file(p)
            if valid:
                self.extract_view.load_file(p)

    def _bind_worker_to_history(self) -> None:
        """Binds active extraction worker completion to history view."""
        worker = self.extract_view.active_worker
        if worker:
            worker.all_finished.connect(self._on_worker_finished_record_history)

    def _on_worker_finished_record_history(self, results: list[DocumentResult]) -> None:
        """Records completed extraction result in history."""
        if results:
            self.history_view.add_record_from_result(results[0])

    def _on_settings_updated(self) -> None:
        """Synchronizes status across views after settings change."""
        self.ocr_settings_view.refresh_all_data()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Saves window size on close if preference enabled."""
        if self.settings.get("remember_window_size", True):
            self.settings.set("window_width", self.width(), auto_save=False)
            self.settings.set("window_height", self.height(), auto_save=True)
        super().closeEvent(event)
