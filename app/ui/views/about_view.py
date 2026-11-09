"""
شاشة حول التطبيق (About View) لنظام نَصّ (NASS).
توفر نبذة عن التطبيق، أهدافه، الإصدار، وتأكيد المعالجة المحلية الخالصة.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.config import PROJECT_ROOT


class AboutView(QWidget):
    """شاشة التعريف بالتطبيق والترخيص."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        card = QFrame()
        card.setObjectName("cardFrame")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(24, 24, 24, 24)
        c_layout.setSpacing(14)
        c_layout.setAlignment(Qt.AlignCenter)

        # الشعار
        logo_path = PROJECT_ROOT / "logo_NASS.png"
        if logo_path.exists():
            lbl_logo = QLabel()
            pix = QPixmap(str(logo_path)).scaled(
                72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            lbl_logo.setPixmap(pix)
            lbl_logo.setAlignment(Qt.AlignCenter)
            c_layout.addWidget(lbl_logo)

        lbl_app_name = QLabel("نَصّ | NASS — Smart OCR")
        lbl_app_name.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E3A8A;")
        lbl_app_name.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(lbl_app_name)

        lbl_slogan = QLabel("من الصورة إلى النص — الإصدار 1.0.0 المستقر")
        lbl_slogan.setStyleSheet("font-size: 13px; color: #64748B; font-weight: 500;")
        lbl_slogan.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(lbl_slogan)

        # مربع الوصف والخصوصية
        desc_box = QFrame()
        desc_box.setStyleSheet(
            "background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px;"
        )
        db_layout = QVBoxLayout(desc_box)
        db_layout.setSpacing(10)

        p1 = QLabel(
            "تطبيق نَصّ (NASS) هو أداة ذكية وحديثة صُممت لتمكين المستخدمين من استخراج النصوص العربية والإنجليزية والرموز الرياضية "
            "من الصور والمستندات المصورة وملفات PDF بدقة عالية وسرعة فائقة."
        )
        p1.setWordWrap(True)
        p1.setStyleSheet("color: #1E293B; line-height: 1.6; font-size: 13px;")

        p2 = QLabel(
            "المعالجة المحلية الخالصة:\n"
            "يعمل التطبيق محلياً بنسبة 100% على جهازك دون إرسال أي مستند أو صورة إلى الإنترنت أو أي طرف ثالث، "
            "مما يضمن الخصوصية الكاملة وسرية بياناتك ومستنداتك الشخصية والرسمية."
        )
        p2.setWordWrap(True)
        p2.setStyleSheet("color: #1E293B; font-weight: 500; font-size: 13px;")

        p3 = QLabel(
            "المحركات والتقنيات المستخدمة:\n"
            "• Python 3.12+ و PySide6 (Qt for Python)\n"
            "• Tesseract OCR Engine عبر Pytesseract\n"
            "• PyMuPDF (fitz) لمعالجة مستندات PDF بدقة متناهية\n"
            "• Pillow و OpenCV لتحسين ومعالجة جودة الصور\n"
            "• نظام مدمج لاستخراج المعادلات الرياضية بصيغة LaTeX"
        )
        p3.setWordWrap(True)
        p3.setStyleSheet("color: #475569; font-size: 12px;")

        db_layout.addWidget(p1)
        db_layout.addWidget(p2)
        db_layout.addWidget(p3)

        c_layout.addWidget(desc_box)
        layout.addWidget(card)
        layout.addStretch()
