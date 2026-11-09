"""
اختبارات صحة واجهة المستخدم (UI Sanity Checks) لنظام نَصّ (NASS).
"""

import sys
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def test_main_window_creation():
    """التحقق من إنشاء النافذة الرئيسية وضبط اتجاه RTL والعنوان والهوية والشريط الجانبي والصفحات."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = MainWindow()
    assert "نَصّ" in window.windowTitle()
    assert window.layoutDirection() == Qt.RightToLeft
    assert window.sidebar is not None
    assert window.stack is not None
    assert window.home_view is not None
    assert window.extract_view is not None
    assert window.ocr_settings_view is not None
    assert window.history_view is not None
    assert window.app_settings_view is not None
    assert window.about_view is not None

    # اختبار التبديل بين الصفحات
    window.switch_page(1)
    assert window.stack.currentIndex() == 1
    window.switch_page(3)
    assert window.stack.currentIndex() == 3
    window.switch_page(0)
    assert window.stack.currentIndex() == 0
