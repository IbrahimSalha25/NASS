"""
Navigation sidebar for NASS.
Provides quick switching between main views and displays live Tesseract engine status.
Fully supports proper Arabic RTL layout with right-edge alignment, full-width buttons,
right-flush active indicators, and aligned status cards.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from nass.core.config import DEFAULT_LOGO_PATH
from nass.core.i18n import I18n, tr
from nass.ui.icons import AppIcons


class SidebarNavButton(QPushButton):
    """
    Custom full-width sidebar button with precise RTL/LTR layout.
    Guarantees that in RTL: icon is pinned on the far right, followed immediately
    by the text label with a consistent 10px gap, leaving no uneven empty space.
    """

    def __init__(self, key: str, text: str, icon: QIcon, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebarButton")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        self._key = key

        # Internal layout holding icon and label
        self._content_layout = QHBoxLayout(self)
        self._content_layout.setContentsMargins(16, 0, 16, 0)
        self._content_layout.setSpacing(10)

        self.setLayoutDirection(Qt.RightToLeft if I18n.is_rtl() else Qt.LeftToRight)

        self.icon_lbl = QLabel(self)
        self.icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.icon_lbl.setFixedSize(18, 18)
        self.icon_lbl.setPixmap(icon.pixmap(18, 18))
        self.icon_lbl.setStyleSheet("background: transparent;")

        self.text_lbl = QLabel(text, self)
        self.text_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.text_lbl.setStyleSheet(
            "background: transparent; color: #E2E8F0; font-size: 13px; font-weight: 500;"
        )

        self._content_layout.addWidget(self.icon_lbl)
        self._content_layout.addWidget(self.text_lbl)
        self._content_layout.addStretch()

    def text(self) -> str:
        """Returns the visible text label for compatibility with test assertions."""
        return self.text_lbl.text()

    def setText(self, text: str) -> None:
        """Sets the visible text label."""
        self.text_lbl.setText(text)

    def set_direction(self, is_rtl: bool) -> None:
        """Applies direction to the button container."""
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)


class SidebarWidget(QFrame):
    """
    Navigation sidebar with branding, view switcher buttons, and live engine status.
    """

    page_changed = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebarFrame")
        self.setFixedWidth(230)
        self._last_installed: bool = False
        self._last_version: Optional[str] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 14)
        layout.setSpacing(4)

        # 1. Header with Logo, Title, and Official Slogan
        header_container = QWidget()
        header_container.setObjectName("sidebarHeaderContainer")
        header_container.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_layout.setSpacing(10)

        if DEFAULT_LOGO_PATH.exists():
            logo_lbl = QLabel()
            pix = QPixmap(str(DEFAULT_LOGO_PATH)).scaled(
                36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_lbl.setPixmap(pix)
            logo_lbl.setStyleSheet("background: transparent;")
            header_layout.addWidget(logo_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.lbl_app_title = QLabel(tr("app_name"))
        self.lbl_app_title.setObjectName("sidebarLogoTitle")
        self.lbl_app_slogan = QLabel(tr("app_slogan"))
        self.lbl_app_slogan.setObjectName("sidebarLogoSub")
        title_box.addWidget(self.lbl_app_title)
        title_box.addWidget(self.lbl_app_slogan)

        header_layout.addLayout(title_box)
        header_layout.addStretch()
        layout.addWidget(header_container)

        layout.addSpacing(14)

        # 2. Navigation items
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.buttons: List[SidebarNavButton] = []
        self.nav_keys: List[Tuple[str, QIcon]] = [
            ("nav_home", AppIcons.home("#E2E8F0")),
            ("nav_extract", AppIcons.ocr("#E2E8F0")),
            ("nav_batch_folder", AppIcons.folder("#E2E8F0")),
            ("nav_history", AppIcons.history("#E2E8F0")),
            ("nav_ocr_settings", AppIcons.ocr_settings("#E2E8F0")),
            ("nav_app_settings", AppIcons.app_settings("#E2E8F0")),
            ("nav_about", AppIcons.about("#E2E8F0")),
        ]

        is_rtl = I18n.is_rtl()
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)

        for idx, (key, icon) in enumerate(self.nav_keys):
            btn = SidebarNavButton(key, tr(key), icon, self)
            btn.set_direction(is_rtl)
            self.btn_group.addButton(btn, idx)
            layout.addWidget(btn)
            self.buttons.append(btn)

        self.buttons[0].setChecked(True)
        self.btn_group.idClicked.connect(self._on_button_clicked)

        layout.addStretch()

        # 3. Bottom engine status card
        status_container = QWidget()
        status_container.setStyleSheet("background: transparent;")
        sc_layout = QVBoxLayout(status_container)
        sc_layout.setContentsMargins(12, 0, 12, 0)

        self.status_box = QFrame()
        self.status_box.setObjectName("sidebarStatusCard")
        status_layout = QVBoxLayout(self.status_box)
        status_layout.setContentsMargins(8, 8, 8, 8)
        status_layout.setSpacing(4)

        self.lbl_engine_title = QLabel(tr("engine_status_title"))
        self.lbl_engine_title.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: bold; background: transparent;")
        self.lbl_engine_status = QLabel(tr("engine_status_checking"))
        self.lbl_engine_status.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: bold; background: transparent;")

        status_layout.addWidget(self.lbl_engine_title)
        status_layout.addWidget(self.lbl_engine_status)
        sc_layout.addWidget(self.status_box)
        layout.addWidget(status_container)

    def retranslate_ui(self) -> None:
        """Retranslates all text and adjusts layout direction for active language."""
        is_rtl = I18n.is_rtl()
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)

        self.lbl_app_title.setText(tr("app_name"))
        self.lbl_app_slogan.setText(tr("app_slogan"))
        self.lbl_engine_title.setText(tr("engine_status_title"))

        for idx, (key, _) in enumerate(self.nav_keys):
            if idx < len(self.buttons):
                btn = self.buttons[idx]
                btn.setText(tr(key))
                btn.set_direction(is_rtl)

        self.update_engine_status(self._last_installed, self._last_version)

    def _on_button_clicked(self, page_id: int) -> None:
        self.page_changed.emit(page_id)

    def set_active_page(self, page_id: int) -> None:
        if 0 <= page_id < len(self.buttons):
            self.buttons[page_id].setChecked(True)

    def update_engine_status(self, is_installed: bool, version: Optional[str] = None) -> None:
        """Update bottom status badge based on Tesseract availability with subtle semantic styling."""
        self._last_installed = is_installed
        self._last_version = version

        if is_installed:
            ver_text = f"v{version}" if version else ""
            ready_txt = tr("engine_status_ready")
            self.lbl_engine_status.setText(f"{ready_txt} ({ver_text})" if ver_text else ready_txt)
            self.lbl_engine_status.setStyleSheet("color: #34D399; font-size: 12px; font-weight: bold; background: transparent;")
            self.status_box.setStyleSheet(
                "background-color: rgba(6, 78, 59, 0.35); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 8px; padding: 6px 8px;"
            )
        else:
            self.lbl_engine_status.setText(tr("engine_status_not_installed"))
            self.lbl_engine_status.setStyleSheet("color: #F87171; font-size: 12px; font-weight: bold; background: transparent;")
            self.status_box.setStyleSheet(
                "background-color: rgba(127, 29, 29, 0.35); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 8px; padding: 6px 8px;"
            )
