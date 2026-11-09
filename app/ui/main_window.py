"""
النافذة الرئيسية لتطبيق نَصّ (NASS) — PySide6 بتخطيط RTL كامل وشريط جانبي وتصميم احترافي موحد.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from app.config import PROJECT_ROOT
from app.core.file_manager import FileManager
from app.core.settings_manager import SettingsManager
from app.core.tesseract_manager import TesseractManager
from app.ui.components.sidebar import SidebarWidget
from app.ui.styles import APP_STYLESHEET
from app.ui.views.about_view import AboutView
from app.ui.views.app_settings_view import AppSettingsView
from app.ui.views.extract_view import ExtractView
from app.ui.views.history_view import HistoryView
from app.ui.views.home_view import HomeView
from app.ui.views.ocr_settings_view import OcrSettingsView
from app.utils.logger import logger


class MainWindow(QMainWindow):
    """النافذة الأساسية لتطبيق نَصّ مع هيكل الصفحات المتعددة والشريط الجانبي."""

    def __init__(self):
        super().__init__()
        self.settings = SettingsManager.get_instance()
        self.tess_mgr = TesseractManager()

        self.setWindowTitle("نَصّ | NASS — Smart OCR Desktop Application")
        width = self.settings.get("window_width", 1200)
        height = self.settings.get("window_height", 800)
        self.resize(width, height)
        self.setMinimumSize(980, 640)
        self.setLayoutDirection(Qt.RightToLeft)

        # أيقونة النافذة
        logo_path = PROJECT_ROOT / "logo_NASS.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self._init_ui()
        self._connect_signals()
        self.setStyleSheet(APP_STYLESHEET)
        self.refresh_engine_status()

    def _init_ui(self):
        """بناء تخطيط الواجهة: الشريط الجانبي والصفحات المكدسة."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. الشريط الجانبي
        self.sidebar = SidebarWidget(self)
        root_layout.addWidget(self.sidebar)

        # 2. مكدس الصفحات (Stacked Pages)
        self.stack = QStackedWidget(self)

        # الصفحة 0: الرئيسية
        self.home_view = HomeView(self)
        self.stack.addWidget(self.home_view)

        # الصفحة 1: استخراج النصوص
        self.extract_view = ExtractView(self)
        self.stack.addWidget(self.extract_view)

        # الصفحة 2: سجل العمليات
        self.history_view = HistoryView(self)
        self.stack.addWidget(self.history_view)

        # الصفحة 3: إعدادات محرك OCR
        self.ocr_settings_view = OcrSettingsView(self)
        self.stack.addWidget(self.ocr_settings_view)

        # الصفحة 4: إعدادات التطبيق
        self.app_settings_view = AppSettingsView(self)
        self.stack.addWidget(self.app_settings_view)

        # الصفحة 5: حول التطبيق
        self.about_view = AboutView(self)
        self.stack.addWidget(self.about_view)

        root_layout.addWidget(self.stack, stretch=1)

    def _connect_signals(self):
        """ربط إشارات التنقل والتفاعل بين الصفحات."""
        # التنقل عبر الشريط الجانبي
        self.sidebar.page_changed.connect(self.stack.setCurrentIndex)

        # عند اختيار ملف من الصفحة الرئيسية، الانتقال مباشرة لصفحة الاستخراج
        self.home_view.file_selected.connect(self._on_file_selected_from_home)
        self.home_view.navigate_to_settings.connect(lambda: self.switch_page(3))

        # عند طلب تغيير الملف من شاشة الاستخراج
        self.extract_view.change_file_requested.connect(self._select_new_file)

        # تحديث حالة المحرك عند تعديل الإعدادات
        self.ocr_settings_view.settings_updated.connect(self.refresh_engine_status)

        # تسجيل العمليات في شاشة السجل فور انتهائها
        self.extract_view.btn_start.clicked.connect(self._bind_worker_to_history)

    def _on_file_selected_from_home(self, file_path: Path):
        """تحميل الملف والانتقال لشاشة الاستخراج."""
        self.extract_view.load_file(file_path)
        self.switch_page(1)

    def _select_new_file(self):
        """فتح نافذة اختيار ملف جديد."""
        filters = (
            "جميع الملفات المدعومة (*.pdf *.png *.jpg *.jpeg *.tiff *.tif *.bmp *.webp);;"
            "ملفات PDF (*.pdf);;"
            "ملفات الصور (*.png *.jpg *.jpeg *.tiff *.tif *.bmp *.webp);;"
            "جميع الملفات (*.*)"
        )
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "اختيار ملف للاستخراج",
            "",
            filters,
        )
        if file_path:
            p = Path(file_path).resolve()
            valid, _ = FileManager.is_valid_file(p)
            if valid:
                self.extract_view.load_file(p)

    def _bind_worker_to_history(self):
        """ربط اكتمال العامل بحفظ النتيجة في سجل العمليات."""
        worker = self.extract_view.active_worker
        if worker:
            worker.all_finished.connect(self._on_worker_finished_record_history)

    def _on_worker_finished_record_history(self, results):
        if results:
            self.history_view.add_record_from_result(results[0])

    def switch_page(self, page_index: int):
        """التبديل إلى صفحة محددة وتحديث الشريط الجانبي."""
        self.stack.setCurrentIndex(page_index)
        self.sidebar.set_active_page(page_index)

    def refresh_engine_status(self):
        """فحص وتحديث حالة Tesseract في الشريط الجانبي والصفحة الرئيسية."""
        status = self.tess_mgr.get_engine_status()
        is_inst = status.get("is_installed", False)
        ver = status.get("version")
        langs = status.get("available_languages", [])

        self.sidebar.update_engine_status(is_inst, ver)
        self.home_view.update_engine_info(is_inst, ver, langs)

    def closeEvent(self, event):
        """حفظ إعدادات النافذة عند الإغلاق."""
        if self.settings.get("remember_window_size", True):
            self.settings.set("window_width", self.width(), auto_save=False)
            self.settings.set("window_height", self.height(), auto_save=True)
        event.accept()
