"""
مكون الشريط الجانبي (Sidebar) لتطبيق نَصّ (NASS).
يوفر تنقلاً سريعاً وواضحاً بين أقسام التطبيق مع شارة حالة Tesseract.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
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

from app.config import PROJECT_ROOT
from app.ui.icons import AppIcons


class SidebarWidget(QFrame):
    """الشريط الجانبي الرئيسي مع أزرار التنقل وشارة حالة المحرك."""

    # إشارة عند تغيير التبويب المحدد (رقم التبويب 0-5)
    page_changed = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("sidebarFrame")
        self.setFixedWidth(240)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 18, 12, 18)
        layout.setSpacing(6)

        # 1. ترويسة الشريط: الشعار واسم التطبيق
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        logo_path = PROJECT_ROOT / "logo_NASS.png"
        if logo_path.exists():
            logo_lbl = QLabel()
            pix = QPixmap(str(logo_path)).scaled(
                36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_lbl.setPixmap(pix)
            logo_lbl.setStyleSheet("background: transparent;")
            header_layout.addWidget(logo_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        app_title = QLabel("نَصّ | NASS")
        app_title.setObjectName("sidebarLogoTitle")
        app_sub = QLabel("من الصورة إلى النص")
        app_sub.setObjectName("sidebarLogoSub")
        title_box.addWidget(app_title)
        title_box.addWidget(app_sub)

        header_layout.addLayout(title_box)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        layout.addSpacing(16)

        # 2. مجموعة أزرار التنقل
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.buttons = []
        nav_items = [
            ("الرئيسية", AppIcons.home("#E2E8F0")),
            ("استخراج النصوص", AppIcons.ocr("#E2E8F0")),
            ("سجل العمليات", AppIcons.history("#E2E8F0")),
            ("إعدادات OCR", AppIcons.ocr_settings("#E2E8F0")),
            ("إعدادات التطبيق", AppIcons.app_settings("#E2E8F0")),
            ("حول التطبيق", AppIcons.about("#E2E8F0")),
        ]

        for idx, (title, icon) in enumerate(nav_items):
            btn = QPushButton(f"  {title}")
            btn.setObjectName("sidebarButton")
            btn.setCheckable(True)
            btn.setIcon(icon)
            btn.setCursor(Qt.PointingHandCursor)
            self.btn_group.addButton(btn, idx)
            layout.addWidget(btn , alignment= Alignment.shrinkToFit)
            self.buttons.append(btn)

        self.buttons[0].setChecked(True)
        self.btn_group.idClicked.connect(self._on_button_clicked)

        layout.addStretch()

        # 3. بطاقة حالة المحرك في أسفل الشريط
        self.status_box = QFrame()
        self.status_box.setStyleSheet(
            "background-color: #1E293B; border-radius: 8px; padding: 10px;"
        )
        status_layout = QVBoxLayout(self.status_box)
        status_layout.setContentsMargins(4, 4, 4, 4)
        status_layout.setSpacing(4)

        self.lbl_engine_title = QLabel("حالة Tesseract OCR:")
        self.lbl_engine_title.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: bold;")
        self.lbl_engine_status = QLabel("جاري الفحص...")
        self.lbl_engine_status.setStyleSheet("color: #10B981; font-size: 12px; font-weight: bold;")

        status_layout.addWidget(self.lbl_engine_title)
        status_layout.addWidget(self.lbl_engine_status)
        layout.addWidget(self.status_box)

    def _on_button_clicked(self, page_id: int):
        self.page_changed.emit(page_id)

    def set_active_page(self, page_id: int):
        if 0 <= page_id < len(self.buttons):
            self.buttons[page_id].setChecked(True)

    def update_engine_status(self, is_installed: bool, version: Optional[str] = None):
        """تحديث شارة الحالة السفلية."""
        if is_installed:
            ver_text = f"v{version}" if version else "جاهز"
            self.lbl_engine_status.setText(f"جاهز للعمل ({ver_text})")
            self.lbl_engine_status.setStyleSheet("color: #10B981; font-size: 12px; font-weight: bold;")
        else:
            self.lbl_engine_status.setText("غير مثبت أو غير مكتشف")
            self.lbl_engine_status.setStyleSheet("color: #EF4444; font-size: 12px; font-weight: bold;")
