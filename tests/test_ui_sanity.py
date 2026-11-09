"""
اختبارات صحة واجهة المستخدم (UI Sanity Checks) لنظام نَصّ (NASS).
"""

import sys
import pytest


def test_main_window_creation():
    """التحقق من إنشاء النافذة الرئيسية وضبط اتجاه RTL والعنوان والهوية بنجاح."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from app.ui.main_window import MainWindow

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = MainWindow()
    assert "نَصّ" in window.windowTitle()
    assert window.layoutDirection() == Qt.RightToLeft
    assert window.file_table is not None
    assert window.drop_zone is not None
    assert window.options_bar is not None
    assert window.txt_result is not None
