"""
Home dashboard view for NASS.
Features a responsive drag-and-drop zone, file attachment trigger,
supported formats guide, and real-time engine status cards.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from nass.core.config import DEFAULT_LOGO_PATH
from nass.core.i18n import I18n, tr
from nass.ui.icons import AppIcons
from nass.utils.file_utils import FileUtils
from nass.utils.logger import logger


class DropCardFrame(QFrame):
    """
    Dedicated drop-target frame with native drag-and-drop event handling
    and reactive visual hover feedback.
    """

    file_dropped = Signal(Path)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            self._set_highlight(True)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            self._set_highlight(True)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._set_highlight(False)
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        self._set_highlight(False)
        urls = event.mimeData().urls()
        if not urls:
            return

        path = Path(urls[0].toLocalFile()).resolve()
        valid, _ = FileUtils.is_valid_file(path)
        if valid:
            self.file_dropped.emit(path)
            event.acceptProposedAction()

    def _set_highlight(self, active: bool) -> None:
        self.setProperty("dragOver", active)
        self.style().unpolish(self)
        self.style().polish(self)


class HomeView(QWidget):
    """
    Main home dashboard screen with drag & drop zone, formats guide, and live status.
    Fully responsive for small and standard screen dimensions.
    """

    file_selected = Signal(Path)
    navigate_to_settings = Signal()
    navigate_to_batch = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._last_is_installed: bool = False
        self._last_version: Optional[str] = None
        self._last_langs: List[str] = []
        self._init_ui()

    def _init_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(14, 10, 14, 10)
        outer_layout.setSpacing(8)

        # ScrollArea wrapper so small screen resolutions never clip content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(10)

        # 1. Top Welcome Banner
        banner_frame = QFrame()
        banner_frame.setObjectName("cardFrame")
        banner_layout = QHBoxLayout(banner_frame)
        banner_layout.setContentsMargins(14, 10, 14, 10)
        banner_layout.setSpacing(14)

        if DEFAULT_LOGO_PATH.exists():
            logo_lbl = QLabel()
            pix = QPixmap(str(DEFAULT_LOGO_PATH)).scaled(
                46, 46, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_lbl.setPixmap(pix)
            banner_layout.addWidget(logo_lbl)

        info_box = QVBoxLayout()
        info_box.setSpacing(2)
        self.lbl_welcome = QLabel(tr("home_welcome"))
        self.lbl_welcome.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E3A8A;")
        self.lbl_slogan = QLabel(f"{tr('app_name')} — {tr('app_slogan')}")
        self.lbl_slogan.setStyleSheet("font-size: 12px; font-weight: 500; color: #7C3AED;")
        self.lbl_desc = QLabel(tr("app_desc"))
        self.lbl_desc.setStyleSheet("color: #64748B; font-size: 11px;")
        info_box.addWidget(self.lbl_welcome)
        info_box.addWidget(self.lbl_slogan)
        info_box.addWidget(self.lbl_desc)

        banner_layout.addLayout(info_box)
        banner_layout.addStretch()
        main_layout.addWidget(banner_frame)

        # 2. Single-file DropZone with responsive attach file button
        self.drop_card = DropCardFrame(self)
        self.drop_card.file_dropped.connect(self.file_selected)

        drop_layout = QVBoxLayout(self.drop_card)
        drop_layout.setContentsMargins(20, 20, 20, 20)
        drop_layout.setSpacing(10)
        drop_layout.setAlignment(Qt.AlignCenter)

        self.lbl_drop_title = QLabel(tr("home_drop_title"))
        self.lbl_drop_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E293B;")
        self.lbl_drop_title.setAlignment(Qt.AlignCenter)
        self.lbl_drop_title.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.lbl_drop_sub = QLabel(tr("home_drop_sub"))
        self.lbl_drop_sub.setStyleSheet("font-size: 12px; color: #64748B;")
        self.lbl_drop_sub.setAlignment(Qt.AlignCenter)
        self.lbl_drop_sub.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.setAlignment(Qt.AlignCenter)

        self.btn_select_file = QPushButton(tr("home_btn_select"))
        self.btn_select_file.setObjectName("primaryButton")
        self.btn_select_file.setCursor(Qt.PointingHandCursor)
        self.btn_select_file.setIcon(AppIcons.upload("#FFFFFF"))
        self.btn_select_file.setIconSize(QSize(18, 18))
        self.btn_select_file.setMinimumHeight(40)
        self.btn_select_file.setMinimumWidth(180)
        self.btn_select_file.setStyleSheet(
            "QPushButton#primaryButton { padding: 8px 18px; font-size: 13px; font-weight: bold; border-radius: 8px; }"
        )
        self.btn_select_file.clicked.connect(self._open_file_dialog)

        self.btn_batch_folder = QPushButton(tr("batch_title"))
        self.btn_batch_folder.setCursor(Qt.PointingHandCursor)
        self.btn_batch_folder.setIcon(AppIcons.folder("#1E40AF"))
        self.btn_batch_folder.setIconSize(QSize(18, 18))
        self.btn_batch_folder.setMinimumHeight(40)
        self.btn_batch_folder.setMinimumWidth(180)
        self.btn_batch_folder.setStyleSheet(
            "background-color: #EFF6FF; color: #1E40AF; border: 1px solid #BFDBFE; "
            "padding: 8px 18px; font-size: 13px; font-weight: bold; border-radius: 8px;"
        )
        self.btn_batch_folder.clicked.connect(self.navigate_to_batch)

        btn_row.addWidget(self.btn_select_file)
        btn_row.addWidget(self.btn_batch_folder)

        drop_layout.addWidget(self.lbl_drop_title)
        drop_layout.addWidget(self.lbl_drop_sub)
        drop_layout.addSpacing(2)
        drop_layout.addLayout(btn_row)

        main_layout.addWidget(self.drop_card, stretch=2)

        # 3. Supported Formats Badge Bar
        formats_frame = QFrame()
        formats_frame.setObjectName("cardFrame")
        ff_layout = QVBoxLayout(formats_frame)
        ff_layout.setContentsMargins(12, 8, 12, 8)
        ff_layout.setSpacing(4)

        self.lbl_fmt_title = QLabel(tr("home_formats_title"))
        self.lbl_fmt_title.setStyleSheet("font-weight: bold; color: #1E3A8A; font-size: 11px;")
        self.lbl_fmt_list = QLabel(tr("home_formats_list"))
        self.lbl_fmt_list.setStyleSheet("color: #475569; font-size: 11px; line-height: 1.4;")
        ff_layout.addWidget(self.lbl_fmt_title)
        ff_layout.addWidget(self.lbl_fmt_list)
        main_layout.addWidget(formats_frame)

        # 4. Quick Status Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)

        # Engine Card
        self.card_engine = QFrame()
        self.card_engine.setObjectName("statCard")
        c1_layout = QVBoxLayout(self.card_engine)
        c1_layout.setContentsMargins(10, 8, 10, 8)
        self.c1_title = QLabel(tr("stat_engine_title"))
        self.c1_title.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold;")
        self.lbl_card_engine = QLabel(tr("engine_status_checking"))
        self.lbl_card_engine.setStyleSheet("color: #10B981; font-size: 13px; font-weight: bold;")
        self.btn_ocr_settings = QPushButton(tr("stat_engine_btn"))
        self.btn_ocr_settings.setCursor(Qt.PointingHandCursor)
        self.btn_ocr_settings.setFixedHeight(26)
        self.btn_ocr_settings.setStyleSheet("font-size: 11px; padding: 2px 6px;")
        self.btn_ocr_settings.clicked.connect(self.navigate_to_settings)
        c1_layout.addWidget(self.c1_title)
        c1_layout.addWidget(self.lbl_card_engine)
        c1_layout.addWidget(self.btn_ocr_settings)

        # Languages Card
        self.card_langs = QFrame()
        self.card_langs.setObjectName("statCard")
        c2_layout = QVBoxLayout(self.card_langs)
        c2_layout.setContentsMargins(10, 8, 10, 8)
        self.c2_title = QLabel(tr("stat_langs_title"))
        self.c2_title.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold;")
        self.lbl_card_langs = QLabel(tr("stat_langs_val"))
        self.lbl_card_langs.setStyleSheet("color: #2563EB; font-size: 13px; font-weight: bold;")
        self.lbl_c2_sub = QLabel(tr("stat_langs_sub"))
        self.lbl_c2_sub.setStyleSheet("color: #64748B; font-size: 10px;")
        c2_layout.addWidget(self.c2_title)
        c2_layout.addWidget(self.lbl_card_langs)
        c2_layout.addWidget(self.lbl_c2_sub)

        # Privacy Card
        self.card_privacy = QFrame()
        self.card_privacy.setObjectName("statCard")
        c3_layout = QVBoxLayout(self.card_privacy)
        c3_layout.setContentsMargins(10, 8, 10, 8)
        self.c3_title = QLabel(tr("stat_privacy_title"))
        self.c3_title.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold;")
        self.lbl_priv_status = QLabel(tr("stat_privacy_val"))
        self.lbl_priv_status.setStyleSheet("color: #10B981; font-size: 13px; font-weight: bold;")
        self.lbl_priv_desc = QLabel(tr("stat_privacy_sub"))
        self.lbl_priv_desc.setStyleSheet("color: #64748B; font-size: 10px;")
        c3_layout.addWidget(self.c3_title)
        c3_layout.addWidget(self.lbl_priv_status)
        c3_layout.addWidget(self.lbl_priv_desc)

        stats_layout.addWidget(self.card_engine)
        stats_layout.addWidget(self.card_langs)
        stats_layout.addWidget(self.card_privacy)
        main_layout.addLayout(stats_layout)

        scroll_area.setWidget(container)
        outer_layout.addWidget(scroll_area)

    def retranslate_ui(self) -> None:
        """Retranslates all labels and texts for active language."""
        direction = Qt.RightToLeft if I18n.is_rtl() else Qt.LeftToRight
        self.setLayoutDirection(direction)

        self.lbl_welcome.setText(tr("home_welcome"))
        self.lbl_slogan.setText(f"{tr('app_name')} — {tr('app_slogan')}")
        self.lbl_desc.setText(tr("app_desc"))
        self.lbl_drop_title.setText(tr("home_drop_title"))
        self.lbl_drop_sub.setText(tr("home_drop_sub"))
        self.btn_select_file.setText(tr("home_btn_select"))
        self.btn_batch_folder.setText(tr("batch_title"))
        self.lbl_fmt_title.setText(tr("home_formats_title"))
        self.lbl_fmt_list.setText(tr("home_formats_list"))

        self.c1_title.setText(tr("stat_engine_title"))
        self.btn_ocr_settings.setText(tr("stat_engine_btn"))
        self.c2_title.setText(tr("stat_langs_title"))
        self.lbl_c2_sub.setText(tr("stat_langs_sub"))
        self.c3_title.setText(tr("stat_privacy_title"))
        self.lbl_priv_status.setText(tr("stat_privacy_val"))
        self.lbl_priv_desc.setText(tr("stat_privacy_sub"))

        self.update_engine_info(self._last_is_installed, self._last_version, self._last_langs)

    def update_engine_info(self, is_installed: bool, version: Optional[str], langs: List[str]) -> None:
        """Update live status badges."""
        self._last_is_installed = is_installed
        self._last_version = version
        self._last_langs = langs

        if is_installed:
            ready_str = tr("engine_status_ready")
            ver_text = f"v{version}" if version else ""
            self.lbl_card_engine.setText(f"{ready_str} {ver_text}".strip())
            self.lbl_card_engine.setStyleSheet("color: #10B981; font-size: 13px; font-weight: bold;")
        else:
            self.lbl_card_engine.setText(tr("engine_status_not_installed"))
            self.lbl_card_engine.setStyleSheet("color: #EF4444; font-size: 13px; font-weight: bold;")

        if langs:
            lang_names = []
            if "ara" in langs:
                lang_names.append("العربية" if I18n.is_rtl() else "Arabic")
            if "eng" in langs:
                lang_names.append("الإنجليزية" if I18n.is_rtl() else "English")
            other_count = len([l for l in langs if l not in ("ara", "eng", "osd")])
            if other_count > 0:
                lang_names.append(f"+{other_count}")
            self.lbl_card_langs.setText("، ".join(lang_names) if lang_names else f"{len(langs)} langs")
        else:
            self.lbl_card_langs.setText(tr("stat_langs_val"))

    def _open_file_dialog(self) -> None:
        """Open file dialog for choosing any supported document."""
        filters = (
            "All Supported Files (*.pdf *.png *.jpg *.jpeg *.tiff *.tif *.bmp *.webp *.docx *.xlsx *.xls *.csv *.pptx *.txt *.md *.rtf *.html *.htm *.xml *.json *.odt *.epub);;"
            "PDF Documents (*.pdf);;"
            "Images (*.png *.jpg *.jpeg *.tiff *.tif *.bmp *.webp);;"
            "Word Documents (*.docx);;"
            "Excel Spreadsheets (*.xlsx *.xls *.csv);;"
            "PowerPoint Presentations (*.pptx);;"
            "Text & Data Files (*.txt *.md *.rtf *.html *.xml *.json *.odt *.epub);;"
            "All Files (*.*)"
        )
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("extract_btn_browse"),
            "",
            filters,
        )
        if file_path:
            p = Path(file_path).resolve()
            valid, _ = FileUtils.is_valid_file(p)
            if valid:
                self.file_selected.emit(p)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return

        first_path = Path(urls[0].toLocalFile()).resolve()
        valid, _ = FileUtils.is_valid_file(first_path)
        if valid:
            self.file_selected.emit(first_path)
            event.acceptProposedAction()
