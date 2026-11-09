"""
Home dashboard view for NASS.
Features single-file dropzone, supported formats overview, and live engine status.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from nass.core.config import DEFAULT_LOGO_PATH
from nass.ui.icons import AppIcons
from nass.utils.file_utils import FileUtils


class HomeView(QWidget):
    """Main home dashboard screen with warm Arabic microcopy."""

    file_selected = Signal(Path)
    navigate_to_settings = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # 1. Top Welcome Banner
        banner_frame = QFrame()
        banner_frame.setObjectName("cardFrame")
        banner_layout = QHBoxLayout(banner_frame)
        banner_layout.setContentsMargins(18, 14, 18, 14)
        banner_layout.setSpacing(16)

        if DEFAULT_LOGO_PATH.exists():
            logo_lbl = QLabel()
            pix = QPixmap(str(DEFAULT_LOGO_PATH)).scaled(
                54, 54, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_lbl.setPixmap(pix)
            banner_layout.addWidget(logo_lbl)

        info_box = QVBoxLayout()
        info_box.setSpacing(3)
        lbl_welcome = QLabel("كل ملفاتك تبدأ رحلتها من هنا.")
        lbl_welcome.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E3A8A;")
        lbl_slogan = QLabel("نَصّ | NASS — حيث تتحول الصور إلى كلمات.")
        lbl_slogan.setStyleSheet("font-size: 13px; font-weight: 500; color: #7C3AED;")
        lbl_desc = QLabel("تطبيقك المحلي لاستخراج النصوص الذكي من المستندات الرقمية والصور بأمان تام وبدون إنترنت.")
        lbl_desc.setStyleSheet("color: #64748B; font-size: 12px;")
        info_box.addWidget(lbl_welcome)
        info_box.addWidget(lbl_slogan)
        info_box.addWidget(lbl_desc)

        banner_layout.addLayout(info_box)
        banner_layout.addStretch()
        main_layout.addWidget(banner_frame)

        # 2. Single-file DropZone
        self.drop_card = QFrame()
        self.drop_card.setObjectName("dropZone")
        self.drop_card.setAcceptDrops(True)
        self.drop_card.installEventFilter(self)

        drop_layout = QVBoxLayout(self.drop_card)
        drop_layout.setContentsMargins(28, 30, 28, 30)
        drop_layout.setSpacing(12)
        drop_layout.setAlignment(Qt.AlignCenter)

        lbl_drop_title = QLabel("اسحب ملفك وأفلته هنا، أو اختره من جهازك.")
        lbl_drop_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E293B;")
        lbl_drop_title.setAlignment(Qt.AlignCenter)

        lbl_drop_sub = QLabel("اختر ملفك، ودع الباقي علينا.")
        lbl_drop_sub.setStyleSheet("font-size: 13px; color: #64748B;")
        lbl_drop_sub.setAlignment(Qt.AlignCenter)

        btn_select_file = QPushButton("  اختيار ملف للبدء  ")
        btn_select_file.setObjectName("primaryButton")
        btn_select_file.setCursor(Qt.PointingHandCursor)
        btn_select_file.setIcon(AppIcons.ocr("#FFFFFF"))
        btn_select_file.clicked.connect(self._open_file_dialog)

        drop_layout.addWidget(lbl_drop_title)
        drop_layout.addWidget(lbl_drop_sub)
        drop_layout.addSpacing(4)
        drop_layout.addWidget(btn_select_file, alignment=Qt.AlignCenter)

        main_layout.addWidget(self.drop_card, stretch=2)

        # 3. Supported Formats Badge Bar
        formats_frame = QFrame()
        formats_frame.setObjectName("cardFrame")
        ff_layout = QVBoxLayout(formats_frame)
        ff_layout.setContentsMargins(14, 10, 14, 10)
        ff_layout.setSpacing(6)

        lbl_fmt_title = QLabel("الصيغ المدعومة فعلياً:")
        lbl_fmt_title.setStyleSheet("font-weight: bold; color: #1E3A8A; font-size: 12px;")
        lbl_fmt_list = QLabel(
            "• مستندات وصور: PDF، PNG، JPG، JPEG، WEBP، BMP، TIFF\n"
            "• أوفيس وجداول: DOCX، XLSX، XLS، CSV، PPTX\n"
            "• نصوص وويب وبيانات: TXT، MD، RTF، HTML، XML، JSON، ODT، EPUB"
        )
        lbl_fmt_list.setStyleSheet("color: #475569; font-size: 12px; line-height: 1.5;")
        ff_layout.addWidget(lbl_fmt_title)
        ff_layout.addWidget(lbl_fmt_list)
        main_layout.addWidget(formats_frame)

        # 4. Quick Status Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        # Engine Card
        self.card_engine = QFrame()
        self.card_engine.setObjectName("statCard")
        c1_layout = QVBoxLayout(self.card_engine)
        c1_title = QLabel("محرك Tesseract")
        c1_title.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold;")
        self.lbl_card_engine = QLabel("جاري التحقق...")
        self.lbl_card_engine.setStyleSheet("color: #10B981; font-size: 14px; font-weight: bold;")
        btn_ocr_settings = QPushButton("إدارة المحرك")
        btn_ocr_settings.setCursor(Qt.PointingHandCursor)
        btn_ocr_settings.clicked.connect(lambda: self.navigate_to_settings.emit())
        c1_layout.addWidget(c1_title)
        c1_layout.addWidget(self.lbl_card_engine)
        c1_layout.addWidget(btn_ocr_settings)

        # Languages Card
        self.card_langs = QFrame()
        self.card_langs.setObjectName("statCard")
        c2_layout = QVBoxLayout(self.card_langs)
        c2_title = QLabel("اللغات المثبتة")
        c2_title.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold;")
        self.lbl_card_langs = QLabel("العربية + الإنجليزية")
        self.lbl_card_langs.setStyleSheet("color: #1E3A8A; font-size: 14px; font-weight: bold;")
        lbl_c2_sub = QLabel("دعم النصوص المختلطة والثنائية")
        lbl_c2_sub.setStyleSheet("color: #64748B; font-size: 11px;")
        c2_layout.addWidget(c2_title)
        c2_layout.addWidget(self.lbl_card_langs)
        c2_layout.addWidget(lbl_c2_sub)

        # Privacy Card
        self.card_privacy = QFrame()
        self.card_privacy.setObjectName("statCard")
        c3_layout = QVBoxLayout(self.card_privacy)
        c3_title = QLabel("الخصوصية والأمان")
        c3_title.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold;")
        lbl_priv_status = QLabel("معالجة محلية 100%")
        lbl_priv_status.setStyleSheet("color: #7C3AED; font-size: 14px; font-weight: bold;")
        lbl_priv_desc = QLabel("لا يتم إرسال أي مستند أو صورة لخوادم خارجية")
        lbl_priv_desc.setStyleSheet("color: #64748B; font-size: 11px;")
        c3_layout.addWidget(c3_title)
        c3_layout.addWidget(lbl_priv_status)
        c3_layout.addWidget(lbl_priv_desc)

        stats_layout.addWidget(self.card_engine)
        stats_layout.addWidget(self.card_langs)
        stats_layout.addWidget(self.card_privacy)
        main_layout.addLayout(stats_layout)

    def update_engine_info(self, is_installed: bool, version: Optional[str], langs: List[str]):
        """Update live status badges."""
        if is_installed:
            self.lbl_card_engine.setText(f"جاهز ومثبت v{version or ''}")
            self.lbl_card_engine.setStyleSheet("color: #10B981; font-size: 14px; font-weight: bold;")
        else:
            self.lbl_card_engine.setText("غير مثبت - يتطلب الإعداد")
            self.lbl_card_engine.setStyleSheet("color: #EF4444; font-size: 14px; font-weight: bold;")

        if langs:
            lang_names = []
            if "ara" in langs:
                lang_names.append("العربية")
            if "eng" in langs:
                lang_names.append("الإنجليزية")
            other_count = len([l for l in langs if l not in ("ara", "eng", "osd")])
            if other_count > 0:
                lang_names.append(f"+{other_count} لغات")
            self.lbl_card_langs.setText("، ".join(lang_names) if lang_names else f"{len(langs)} لغات")

    def _open_file_dialog(self):
        """Open file dialog for choosing any supported document."""
        filters = (
            "جميع الملفات المدعومة (*.pdf *.png *.jpg *.jpeg *.tiff *.tif *.bmp *.webp *.docx *.xlsx *.xls *.csv *.pptx *.txt *.md *.rtf *.html *.htm *.xml *.json *.odt *.epub);;"
            "ملفات PDF (*.pdf);;"
            "ملفات الصور (*.png *.jpg *.jpeg *.tiff *.tif *.bmp *.webp);;"
            "مستندات Word (*.docx);;"
            "جداول بيانات Excel (*.xlsx *.xls *.csv);;"
            "عروض PowerPoint (*.pptx);;"
            "ملفات نصية وبيانات (*.txt *.md *.rtf *.html *.xml *.json *.odt *.epub);;"
            "جميع الملفات (*.*)"
        )
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "اختيار مستند أو صورة للمعالجة",
            "",
            filters,
        )
        if file_path:
            p = Path(file_path).resolve()
            valid, err = FileUtils.is_valid_file(p)
            if valid:
                self.file_selected.emit(p)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if not urls:
            return

        first_path = Path(urls[0].toLocalFile()).resolve()
        valid, _ = FileUtils.is_valid_file(first_path)
        if valid:
            self.file_selected.emit(first_path)
            event.acceptProposedAction()
