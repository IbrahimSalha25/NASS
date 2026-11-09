"""
نقطة انطلاق تطبيق نَصّ | NASS
"""

from __future__ import annotations

import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.utils.logger import logger


def main():
    """تشغيل التطبيق الرئيسي."""
    logger.info("بدء تشغيل تطبيق نَصّ | NASS...")

    app = QApplication(sys.argv)
    app.setApplicationName("نَصّ | NASS")
    app.setOrganizationName("NASS")
    app.setLayoutDirection(Qt.RightToLeft)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
