"""
About view for NASS application.
Displays developer information, license, technologies, and offline privacy statement.
Fully supports internationalization (Arabic/English).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from nass.core.config import APP_NAME, APP_VERSION, ASSETS_DIR, PROJECT_ROOT
from nass.core.i18n import I18n, tr
from nass.ui.icons import AppIcons


class AboutView(QWidget):
    """
    View displaying application metadata, developer profile, and open-source license.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(16)
        container_layout.setAlignment(Qt.AlignTop)

        # 1. Main Application Header Card
        app_card = QFrame()
        app_card.setObjectName("cardFrame")
        ac_layout = QVBoxLayout(app_card)
        ac_layout.setContentsMargins(24, 24, 24, 24)
        ac_layout.setSpacing(12)
        ac_layout.setAlignment(Qt.AlignCenter)

        # Logo
        logo_path = ASSETS_DIR / "images" / "logo_NASS.png"
        if not logo_path.exists():
            logo_path = PROJECT_ROOT / "logo_NASS.png"

        if logo_path.exists():
            lbl_logo = QLabel()
            pix = QPixmap(str(logo_path)).scaled(
                80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            lbl_logo.setPixmap(pix)
            lbl_logo.setAlignment(Qt.AlignCenter)
            ac_layout.addWidget(lbl_logo)

        self.lbl_app_title = QLabel(f"{APP_NAME} — Smart Document & OCR Extractor")
        self.lbl_app_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #0F172A;")
        self.lbl_app_title.setAlignment(Qt.AlignCenter)
        ac_layout.addWidget(self.lbl_app_title)

        self.lbl_slogan = QLabel(tr("app_slogan"))
        self.lbl_slogan.setStyleSheet("font-size: 15px; color: #7C3AED; font-weight: 600;")
        self.lbl_slogan.setAlignment(Qt.AlignCenter)
        ac_layout.addWidget(self.lbl_slogan)

        self.lbl_version = QLabel(f"{tr('version')} {APP_VERSION} • MIT License")
        self.lbl_version.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 500;")
        self.lbl_version.setAlignment(Qt.AlignCenter)
        ac_layout.addWidget(self.lbl_version)

        container_layout.addWidget(app_card)

        # 2. Developer Card (Ibrahim Salha)
        dev_card = QFrame()
        dev_card.setObjectName("cardFrame")
        dc_layout = QVBoxLayout(dev_card)
        dc_layout.setContentsMargins(20, 20, 20, 20)
        dc_layout.setSpacing(12)

        dev_header = QHBoxLayout()
        dev_title_box = QVBoxLayout()
        dev_title_box.setSpacing(2)

        self.lbl_dev_heading = QLabel("بطاقة المطور")
        self.lbl_dev_heading.setStyleSheet("font-size: 15px; font-weight: bold; color: #0F172A;")
        self.lbl_dev_name = QLabel("إبراهيم صالحة | Ibrahim Salha")
        self.lbl_dev_name.setStyleSheet("font-size: 14px; color: #1E40AF; font-weight: 600;")
        self.lbl_dev_role = QLabel("طالب هندسة أنظمة ذكية وحاسوب • مهتم بالذكاء الاصطناعي ومعالجة البيانات")
        self.lbl_dev_role.setStyleSheet("font-size: 12px; color: #64748B;")

        dev_title_box.addWidget(self.lbl_dev_heading)
        dev_title_box.addWidget(self.lbl_dev_name)
        dev_title_box.addWidget(self.lbl_dev_role)
        dev_header.addLayout(dev_title_box)
        dev_header.addStretch()

        self.btn_github = QPushButton("صفحة المطور على GitHub" if I18n.is_rtl() else "Developer GitHub")
        self.btn_github.setIcon(AppIcons.github())
        self.btn_github.setCursor(Qt.PointingHandCursor)
        self.btn_github.setStyleSheet(
            "background-color: #0F172A; color: white; border-radius: 6px; padding: 6px 14px; font-weight: 500;"
        )
        self.btn_github.clicked.connect(self._open_github)
        dev_header.addWidget(self.btn_github)

        dc_layout.addLayout(dev_header)

        self.lbl_dev_bio = QLabel(
            "تم تصميم وبناء تطبيق نَصّ (NASS) بحرص هندسي عالٍ ليكون حلاً محلياً شاملاً، ذكياً، ومفتوح المصدر "
            "لاستخراج النصوص من مختلف أنواع الملفات والمستندات والصور، مع مراعاة أعلى معايير الجودة، "
            "والنظافة المعمارية للكود البرمجي، وسهولة الاستخدام للجمهور العربي."
        )
        self.lbl_dev_bio.setWordWrap(True)
        self.lbl_dev_bio.setStyleSheet("color: #334155; font-size: 12px; line-height: 1.6;")
        dc_layout.addWidget(self.lbl_dev_bio)

        container_layout.addWidget(dev_card)

        # 3. Privacy & Offline Processing Guarantee Card
        privacy_card = QFrame()
        privacy_card.setObjectName("cardFrame")
        pc_layout = QVBoxLayout(privacy_card)
        pc_layout.setContentsMargins(20, 20, 20, 20)
        pc_layout.setSpacing(10)

        self.lbl_privacy_title = QLabel("ضمان الخصوصية والمعالجة المحلية بنسبة 100%")
        self.lbl_privacy_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #15803D;")

        self.lbl_privacy_text = QLabel(
            "يعمل تطبيق نَصّ بالكامل دون الحاجة إلى اتصال بالإنترنت بعد تثبيت المحرك وحزم اللغات.\n"
            "• لا يتم إرسال أي صورة، مستند، أو نص إلى خوادم خارجية أو واجهات سحابية (APIs).\n"
            "• معالجة ملفاتك، صورك، وكتبك تتم محلياً 100% داخل ذاكرة جهازك الشخصي.\n"
            "• الحفاظ الكامل والمطلق على سرية المستندات الحساسة والشخصية."
        )
        self.lbl_privacy_text.setWordWrap(True)
        self.lbl_privacy_text.setStyleSheet("color: #1E293B; font-size: 12px; line-height: 1.6;")

        pc_layout.addWidget(self.lbl_privacy_title)
        pc_layout.addWidget(self.lbl_privacy_text)
        container_layout.addWidget(privacy_card)

        # 4. Technologies & Open Source Stack
        tech_card = QFrame()
        tech_card.setObjectName("cardFrame")
        tc_layout = QVBoxLayout(tech_card)
        tc_layout.setContentsMargins(20, 20, 20, 20)
        tc_layout.setSpacing(10)

        self.lbl_tech_title = QLabel("التقنيات والمكتبات المستخدمة")
        self.lbl_tech_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #0F172A;")

        self.lbl_tech_list = QLabel(
            "• لغة البرمجة: Python 3.11+\n"
            "• إطار الواجهة الرسومية: PySide6 (Qt 6 for Python)\n"
            "• محرك التعرف الضوئي: Tesseract OCR عبر Pytesseract\n"
            "• معالجة مستندات PDF: PyMuPDF (fitz)\n"
            "• معالجة مستندات Office: python-docx (Word) و openpyxl (Excel) و python-pptx (PowerPoint)\n"
            "• معالجة الصور الرقمية: Pillow (PIL) و NumPy\n"
            "• استخراج الصيغ الرياضية: Built-in Math Engine (LaTeX)"
        )
        self.lbl_tech_list.setWordWrap(True)
        self.lbl_tech_list.setStyleSheet("color: #475569; font-size: 12px; line-height: 1.7;")

        tc_layout.addWidget(self.lbl_tech_title)
        tc_layout.addWidget(self.lbl_tech_list)
        container_layout.addWidget(tech_card)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def retranslate_ui(self) -> None:
        """Updates text for the active application language."""
        direction = Qt.RightToLeft if I18n.is_rtl() else Qt.LeftToRight
        self.setLayoutDirection(direction)

        self.lbl_slogan.setText(tr("app_slogan"))
        self.lbl_version.setText(f"{tr('version')} {APP_VERSION} • MIT License")

        if I18n.is_rtl():
            self.lbl_dev_heading.setText("بطاقة المطور")
            self.lbl_dev_role.setText("طالب هندسة أنظمة ذكية وحاسوب • مهتم بالذكاء الاصطناعي ومعالجة البيانات")
            self.btn_github.setText("صفحة المطور على GitHub")
            self.lbl_dev_bio.setText(
                "تم تصميم وبناء تطبيق نَصّ (NASS) بحرص هندسي عالٍ ليكون حلاً محلياً شاملاً، ذكياً، ومفتوح المصدر "
                "لاستخراج النصوص من مختلف أنواع الملفات والمستندات والصور، مع مراعاة أعلى معايير الجودة، "
                "والنظافة المعمارية للكود البرمجي، وسهولة الاستخدام للجمهور العربي."
            )
            self.lbl_privacy_title.setText("ضمان الخصوصية والمعالجة المحلية بنسبة 100%")
            self.lbl_privacy_text.setText(
                "يعمل تطبيق نَصّ بالكامل دون الحاجة إلى اتصال بالإنترنت بعد تثبيت المحرك وحزم اللغات.\n"
                "• لا يتم إرسال أي صورة، مستند، أو نص إلى خوادم خارجية أو واجهات سحابية (APIs).\n"
                "• معالجة ملفاتك، صورك، وكتبك تتم محلياً 100% داخل ذاكرة جهازك الشخصي.\n"
                "• الحفاظ الكامل والمطلق على سرية المستندات الحساسة والشخصية."
            )
            self.lbl_tech_title.setText("التقنيات والمكتبات المستخدمة")
        else:
            self.lbl_dev_heading.setText("Developer Card")
            self.lbl_dev_role.setText("Intelligent Systems & Computer Engineering Student • AI & Vision Enthusiast")
            self.btn_github.setText("Developer on GitHub")
            self.lbl_dev_bio.setText(
                "NASS is crafted with rigorous software engineering standards to deliver a comprehensive, "
                "smart, local-first open-source document extraction and OCR tool for Arabic and multilingual users."
            )
            self.lbl_privacy_title.setText("100% Local & Offline Privacy Guarantee")
            self.lbl_privacy_text.setText(
                "NASS operates entirely locally without requiring internet connectivity after engine setup.\n"
                "• Zero documents, images, or texts are sent to external servers or cloud APIs.\n"
                "• All processing takes place 100% on your local machine memory.\n"
                "• Absolute confidentiality and protection for your private and sensitive documents."
            )
            self.lbl_tech_title.setText("Technologies & Libraries")

    def _open_github(self) -> None:
        """Opens developer GitHub profile in the default system web browser."""
        QDesktopServices.openUrl(QUrl("https://github.com/IbrahimSalha25"))
