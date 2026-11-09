"""
Main application entry point for NASS.
Initializes the Qt application instance, configures logging, and launches MainWindow.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from nass.core.config import APP_NAME, APP_ORGANIZATION, APP_VERSION
from nass.ui.main_window import MainWindow
from nass.utils.logger import logger


def main() -> int:
    """
    Main entry point for starting the NASS desktop application.

    Returns:
        Exit code from the Qt event loop.
    """
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}...")

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORGANIZATION)
    app.setApplicationVersion(APP_VERSION)
    app.setLayoutDirection(Qt.RightToLeft)

    window = MainWindow()
    window.show()

    logger.info("Application main window launched.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
