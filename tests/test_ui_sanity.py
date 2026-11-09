"""
UI Sanity Checks for NASS application.
Verifies MainWindow initialization, RTL layout direction, sidebar navigation,
and presence of all views (Home, Extract, History, OCR Settings, App Settings, About).
"""

from __future__ import annotations

import sys
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from nass.ui.main_window import MainWindow


def test_main_window_creation():
    """Verify MainWindow creation, RTL layout, sidebar, view stack, and navigation."""
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

    # Test switching pages
    window.switch_page(1)
    assert window.stack.currentIndex() == 1
    window.switch_page(3)
    assert window.stack.currentIndex() == 3
    window.switch_page(5)
    assert window.stack.currentIndex() == 5
    window.switch_page(0)
    assert window.stack.currentIndex() == 0
