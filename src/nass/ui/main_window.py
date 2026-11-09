"""
Main application window for NASS.
Implements the multi-page stack, responsive navigation, drag & drop support,
and bilingual (Arabic/English) layout orchestration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent, QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from nass.core.config import APP_NAME, APP_VERSION, ASSETS_DIR, PROJECT_ROOT
from nass.core.i18n import I18n, tr
from nass.core.models import DocumentResult
from nass.core.settings import SettingsManager
from nass.engines.ocr.tesseract_manager import TesseractManager
from nass.ui.components.sidebar import SidebarWidget
from nass.ui.styles import get_stylesheet
from nass.ui.views.about_view import AboutView
from nass.ui.views.app_settings_view import AppSettingsView
from nass.ui.views.batch_folder_view import BatchFolderView
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

        self.setAcceptDrops(True)

        width = self.settings.get("window_width", 1200)
        height = self.settings.get("window_height", 800)
        self.resize(width, height)
        self.setMinimumSize(880, 560)

        # Set application window icon
        logo_path = ASSETS_DIR / "images" / "logo_NASS.png"
        if not logo_path.exists():
            logo_path = PROJECT_ROOT / "logo_NASS.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self._init_ui()
        self._connect_signals()

        initial_lang = self.settings.get("app_language", "ar")
        self.apply_language(initial_lang)

        logger.info("MainWindow initialized successfully.")

    def _init_ui(self) -> None:
        """Constructs UI layout: sidebar and stacked view container."""
        central_widget = QWidget(self)
        central_widget.setAcceptDrops(True)
        self.setCentralWidget(central_widget)

        self.root_layout = QHBoxLayout(central_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        # 1. Navigation Sidebar
        self.sidebar = SidebarWidget(self)
        self.root_layout.addWidget(self.sidebar)

        # 2. Main content stack
        self.stack = QStackedWidget(self)

        # Page 0: Home view
        self.home_view = HomeView(self)
        self.stack.addWidget(self.home_view)

        # Page 1: Extract view
        self.extract_view = ExtractView(self)
        self.stack.addWidget(self.extract_view)

        # Page 2: Batch folder view
        self.batch_folder_view = BatchFolderView(self)
        self.stack.addWidget(self.batch_folder_view)

        # Page 3: History view
        self.history_view = HistoryView(self)
        self.stack.addWidget(self.history_view)

        # Page 4: OCR Settings view
        self.ocr_settings_view = OcrSettingsView(self)
        self.stack.addWidget(self.ocr_settings_view)

        # Page 5: General App Settings view
        self.app_settings_view = AppSettingsView(self)
        self.stack.addWidget(self.app_settings_view)

        # Page 6: About view
        self.about_view = AboutView(self)
        self.stack.addWidget(self.about_view)

        self.root_layout.addWidget(self.stack, stretch=1)

    def _connect_signals(self) -> None:
        """Connects signals across sidebar and views."""
        # Sidebar navigation
        self.sidebar.page_changed.connect(self.switch_page)

        # Home view transitions
        self.home_view.file_selected.connect(self._on_file_selected_from_home)
        self.home_view.navigate_to_settings.connect(lambda: self.switch_page(4))
        self.home_view.navigate_to_batch.connect(lambda: self.switch_page(2))

        # Extract view events
        self.extract_view.change_file_requested.connect(self._select_new_file)
        self.extract_view.btn_start.clicked.connect(self._bind_worker_to_history)

        # Batch folder view events
        self.batch_folder_view.btn_start.clicked.connect(self._bind_batch_worker_to_history)

        # History view re-scan
        self.history_view.rescan_requested.connect(self._on_file_selected_from_home)

        # Settings synchronization & language switching
        self.ocr_settings_view.settings_updated.connect(self._on_settings_updated)
        self.app_settings_view.settings_changed.connect(self._on_settings_updated)
        self.app_settings_view.language_changed.connect(self.apply_language)

    def apply_language(self, lang_code: str) -> None:
        """
        Dynamically applies application language, layout direction (RTL/LTR),
        stylesheets, and triggers retranslation on child views.
        """
        I18n.set_current_language(lang_code)
        is_rtl = I18n.is_rtl()
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight

        self.setLayoutDirection(direction)
        if self.centralWidget():
            self.centralWidget().setLayoutDirection(direction)

        # Apply customized stylesheet matching orientation
        self.setStyleSheet(get_stylesheet(is_rtl=is_rtl))

        # Update window title
        app_title = tr("app_name")
        self.setWindowTitle(f"{app_title} — {tr('app_title_full')} (v{APP_VERSION})")

        # Retranslate all views
        if hasattr(self, "sidebar"):
            self.sidebar.retranslate_ui()
        if hasattr(self, "home_view"):
            self.home_view.retranslate_ui()
        if hasattr(self, "extract_view"):
            self.extract_view.retranslate_ui()
        if hasattr(self, "batch_folder_view"):
            self.batch_folder_view.retranslate_ui()
        if hasattr(self, "history_view"):
            self.history_view.retranslate_ui()
        if hasattr(self, "app_settings_view"):
            self.app_settings_view.retranslate_ui()

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
            "All Supported Files (*.pdf *.png *.jpg *.jpeg *.tiff *.tif *.bmp *.webp "
            "*.docx *.xlsx *.xls *.csv *.pptx *.txt *.md *.rtf *.html *.htm *.xml *.json *.odt *.epub);;"
            "PDF Documents (*.pdf);;"
            "Images (*.png *.jpg *.jpeg *.tiff *.tif *.bmp *.webp);;"
            "Word Documents (*.docx);;"
            "Excel Spreadsheets (*.xlsx *.xls *.csv);;"
            "PowerPoint Presentations (*.pptx);;"
            "Text & Markdown (*.txt *.md *.rtf);;"
            "Web & Markup (*.html *.htm *.xml *.json);;"
            "OpenDocument & eBooks (*.odt *.epub);;"
            "All Files (*.*)"
        )
        file_path_str, _ = QFileDialog.getOpenFileName(
            self,
            tr("extract_btn_browse"),
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

    def _bind_batch_worker_to_history(self) -> None:
        """Binds active batch extraction worker completion to history view."""
        worker = self.batch_folder_view.active_worker
        if worker:
            worker.file_finished.connect(lambda _, __, doc_res: self.history_view.add_record_from_result(doc_res))

    def _on_worker_finished_record_history(self, results: list[DocumentResult]) -> None:
        """Records completed extraction result in history."""
        if results:
            self.history_view.add_record_from_result(results[0])

    def _on_settings_updated(self) -> None:
        """Synchronizes status across views after settings change."""
        if hasattr(self, "history_view"):
            self.history_view.apply_settings_limits()
        self.ocr_settings_view.refresh_all_data()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls:
            path = Path(urls[0].toLocalFile()).resolve()
            valid, _ = FileUtils.is_valid_file(path)
            if valid:
                self._on_file_selected_from_home(path)
                event.acceptProposedAction()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Saves window size on close if preference enabled."""
        if self.settings.get("remember_window_size", True):
            self.settings.set("window_width", self.width(), auto_save=False)
            self.settings.set("window_height", self.height(), auto_save=True)
        super().closeEvent(event)
