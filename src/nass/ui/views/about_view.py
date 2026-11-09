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
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(14, 12, 14, 12)
        outer_layout.setSpacing(10)

        # Header bar matching other screens
        header = QFrame()
        header.setObjectName("cardFrame")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(14, 10, 14, 10)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.lbl_main_title = QLabel(tr("about_title"))
        self.lbl_main_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #0F172A;")
        self.lbl_main_desc = QLabel(tr("about_desc"))
        self.lbl_main_desc.setStyleSheet("font-size: 12px; color: #64748B;")
        title_box.addWidget(self.lbl_main_title)
        title_box.addWidget(self.lbl_main_desc)
        h_layout.addLayout(title_box)
        outer_layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(4, 4, 4, 4)
        container_layout.setSpacing(12)
        container_layout.setAlignment(Qt.AlignTop)

        # 1. Main Application Header Card
        app_card = QFrame()
        app_card.setObjectName("cardFrame")
        ac_layout = QVBoxLayout(app_card)
        ac_layout.setContentsMargins(28, 28, 28, 28)
        ac_layout.setSpacing(14)
        ac_layout.setAlignment(Qt.AlignCenter)

        # Logo
        logo_path = ASSETS_DIR / "images" / "logo_NASS.png"
        if not logo_path.exists():
            logo_path = PROJECT_ROOT / "logo_NASS.png"

        if logo_path.exists():
            lbl_logo = QLabel()
            pix = QPixmap(str(logo_path)).scaled(
                85, 85, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            lbl_logo.setPixmap(pix)
            lbl_logo.setAlignment(Qt.AlignCenter)
            ac_layout.addWidget(lbl_logo)

        self.lbl_app_title = QLabel(f"{APP_NAME} — Smart Document & OCR Extractor")
        self.lbl_app_title.setStyleSheet("font-size: 24px; font-weight: 800; color: #0F172A; letter-spacing: 0.5px;")
        self.lbl_app_title.setAlignment(Qt.AlignCenter)
        ac_layout.addWidget(self.lbl_app_title)

        self.lbl_slogan = QLabel(tr("app_slogan"))
        self.lbl_slogan.setStyleSheet(
            "font-size: 16px; color: #6D28D9; font-weight: 700; "
            "background-color: #F5F3FF; padding: 4px 16px; border-radius: 20px;"
        )
        self.lbl_slogan.setAlignment(Qt.AlignCenter)
        ac_layout.addWidget(self.lbl_slogan, alignment=Qt.AlignCenter)

        self.lbl_app_tagline = QLabel(
            "الجيل الجديد لاستخراج النصوص الذكي من المستندات الرقمية والصور • قوة هندسية، خصوصية مطلقة، وبدون إنترنت"
            if I18n.is_rtl() else
            "Next-Generation Smart Text Extraction for Documents & Images • High Engineering Quality, 100% Local Privacy"
        )
        self.lbl_app_tagline.setStyleSheet("font-size: 13px; color: #475569; font-weight: 500;")
        self.lbl_app_tagline.setAlignment(Qt.AlignCenter)
        ac_layout.addWidget(self.lbl_app_tagline)

        self.lbl_version = QLabel(f"{tr('version')} {APP_VERSION} • رخصة مفتوحة المصدر (MIT License)")
        self.lbl_version.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 600;")
        self.lbl_version.setAlignment(Qt.AlignCenter)
        ac_layout.addWidget(self.lbl_version)

        container_layout.addWidget(app_card)

        # 2. Developer Card (Ibrahim Salha)
        dev_card = QFrame()
        dev_card.setObjectName("cardFrame")
        dc_layout = QVBoxLayout(dev_card)
        dc_layout.setContentsMargins(20, 20, 20, 20)
        dc_layout.setSpacing(14)

        dev_header = QHBoxLayout()
        dev_title_box = QVBoxLayout()
        dev_title_box.setSpacing(2)

        self.lbl_dev_heading = QLabel(tr("about_dev_heading"))
        self.lbl_dev_heading.setStyleSheet("font-size: 15px; font-weight: bold; color: #0F172A;")
        self.lbl_dev_name = QLabel(tr("about_dev_name"))
        self.lbl_dev_name.setStyleSheet("font-size: 14px; color: #1E40AF; font-weight: 600;")
        self.lbl_dev_role = QLabel(tr("about_dev_role"))
        self.lbl_dev_role.setStyleSheet("font-size: 12px; color: #64748B;")

        dev_title_box.addWidget(self.lbl_dev_heading)
        dev_title_box.addWidget(self.lbl_dev_name)
        dev_title_box.addWidget(self.lbl_dev_role)
        dev_header.addLayout(dev_title_box)
        dev_header.addStretch()
        dc_layout.addLayout(dev_header)

        # Developer personal links (GitHub, LinkedIn, Email, Portfolio)
        links_box = QHBoxLayout()
        links_box.setSpacing(8)

        self.btn_github = QPushButton(tr("about_btn_github"))
        self.btn_github.setIcon(AppIcons.github())
        self.btn_github.setCursor(Qt.PointingHandCursor)
        self.btn_github.setStyleSheet(
            "background-color: #0F172A; color: white; border-radius: 6px; padding: 6px 12px; font-weight: 500; font-size: 12px;"
        )
        self.btn_github.clicked.connect(self._open_github)

        self.btn_linkedin = QPushButton(tr("about_btn_linkedin"))
        self.btn_linkedin.setIcon(AppIcons.linkedin())
        self.btn_linkedin.setCursor(Qt.PointingHandCursor)
        self.btn_linkedin.setStyleSheet(
            "background-color: #0A66C2; color: white; border-radius: 6px; padding: 6px 12px; font-weight: 500; font-size: 12px;"
        )
        self.btn_linkedin.clicked.connect(self._open_linkedin)

        self.btn_email = QPushButton(tr("about_btn_email"))
        self.btn_email.setIcon(AppIcons.mail())
        self.btn_email.setCursor(Qt.PointingHandCursor)
        self.btn_email.setStyleSheet(
            "background-color: #F8FAFC; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 12px; font-weight: 500; font-size: 12px;"
        )
        self.btn_email.clicked.connect(self._open_email)

        links_box.addWidget(self.btn_github)
        links_box.addWidget(self.btn_linkedin)
        links_box.addWidget(self.btn_email)
        links_box.addStretch()
        dc_layout.addLayout(links_box)

        self.lbl_dev_bio = QLabel(
            "تم تصميم وبناء تطبيق نَصّ (NASS) ليكون منصة سطح مكتب هندسية رائدة، تدمج بين خوارزميات التعرف الضوئي على المحارف (OCR)، "
            "والاستخراج المباشر للنصوص من مستندات Office وPDF، مع دعم كامل للصور المضمنة والمعادلات الرياضية (LaTeX). "
            "صُمم التطبيق ليعمل محلياً بصورة كاملة 100% دون خوادم سحابية، مع مراعاة قصوى لخصوصية البيانات وجودة تجربة المستخدم العربية."
        )
        self.lbl_dev_bio.setWordWrap(True)
        self.lbl_dev_bio.setStyleSheet("color: #334155; font-size: 13px; line-height: 1.8;")
        dc_layout.addWidget(self.lbl_dev_bio)

        container_layout.addWidget(dev_card)

        # 3. Project Info & Repository Card
        repo_card = QFrame()
        repo_card.setObjectName("cardFrame")
        rc_layout = QVBoxLayout(repo_card)
        rc_layout.setContentsMargins(20, 20, 20, 20)
        rc_layout.setSpacing(10)

        self.lbl_repo_title = QLabel(tr("about_project_info_title"))
        self.lbl_repo_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E40AF;")

        self.lbl_repo_desc = QLabel(tr("about_project_repo_desc"))
        self.lbl_repo_desc.setStyleSheet("color: #334155; font-size: 12px;")

        self.btn_repo = QPushButton(tr("about_btn_repo"))
        self.btn_repo.setIcon(AppIcons.github("#1E40AF"))
        self.btn_repo.setCursor(Qt.PointingHandCursor)
        self.btn_repo.setStyleSheet(
            "background-color: #EFF6FF; color: #1E40AF; border: 1px solid #BFDBFE; "
            "border-radius: 6px; padding: 6px 14px; font-weight: 600; font-size: 12px;"
        )
        self.btn_repo.clicked.connect(self._open_repository)

        rc_layout.addWidget(self.lbl_repo_title)
        rc_layout.addWidget(self.lbl_repo_desc)
        rc_layout.addWidget(self.btn_repo, alignment=Qt.AlignLeft if not I18n.is_rtl() else Qt.AlignRight)
        container_layout.addWidget(repo_card)

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
        outer_layout.addWidget(scroll)

    def retranslate_ui(self) -> None:
        """Updates text for the active application language."""
        direction = Qt.RightToLeft if I18n.is_rtl() else Qt.LeftToRight
        self.setLayoutDirection(direction)

        self.lbl_main_title.setText(tr("about_title"))
        self.lbl_main_desc.setText(tr("about_desc"))
        self.lbl_slogan.setText(tr("app_slogan"))
        self.lbl_version.setText(f"{tr('version')} {APP_VERSION} • MIT License")
        self.lbl_dev_heading.setText(tr("about_dev_heading"))
        self.lbl_dev_name.setText(tr("about_dev_name"))
        self.lbl_dev_role.setText(tr("about_dev_role"))
        self.btn_github.setText(tr("about_btn_github"))
        self.btn_linkedin.setText(tr("about_btn_linkedin"))
        self.btn_email.setText(tr("about_btn_email"))
        self.lbl_repo_title.setText(tr("about_project_info_title"))
        self.lbl_repo_desc.setText(tr("about_project_repo_desc"))
        self.btn_repo.setText(tr("about_btn_repo"))
        self.lbl_privacy_title.setText(tr("about_privacy_title"))
        self.lbl_tech_title.setText(tr("about_tech_title"))

        if hasattr(self, "lbl_app_tagline"):
            self.lbl_app_tagline.setText(
                "الجيل الجديد لاستخراج النصوص الذكي من المستندات الرقمية والصور • قوة هندسية، خصوصية مطلقة، وبدون إنترنت"
                if I18n.is_rtl() else
                "Next-Generation Smart Text Extraction for Documents & Images • High Engineering Quality, 100% Local Privacy"
            )

        if I18n.is_rtl():
            self.lbl_dev_bio.setText(
                "تم تصميم وبناء تطبيق نَصّ (NASS) ليكون منصة سطح مكتب هندسية رائدة، تدمج بين خوارزميات التعرف الضوئي على المحارف (OCR)، "
                "والاستخراج المباشر للنصوص من مستندات Office وPDF، مع دعم كامل للصور المضمنة والمعادلات الرياضية (LaTeX). "
                "صُمم التطبيق ليعمل محلياً بصورة كاملة 100% دون خوادم سحابية، مع مراعاة قصوى لخصوصية البيانات وجودة تجربة المستخدم العربية."
            )
            self.lbl_privacy_text.setText(
                "يعمل تطبيق نَصّ بالكامل دون الحاجة إلى اتصال بالإنترنت بعد تثبيت المحرك وحزم اللغات.\n"
                "• لا يتم إرسال أي صورة، مستند، أو نص إلى خوادم خارجية أو واجهات سحابية (APIs).\n"
                "• معالجة ملفاتك، صورك، وكتبك تتم محلياً 100% داخل ذاكرة جهازك الشخصي.\n"
                "• الحفاظ الكامل والمطلق على سرية المستندات الحساسة والشخصية."
            )
        else:
            self.lbl_dev_bio.setText(
                "NASS is an advanced engineering desktop platform integrating Optical Character Recognition (OCR) "
                "with native digital extraction across Office and PDF documents, including embedded images and LaTeX formulas. "
                "It operates 100% locally with zero cloud dependencies, prioritizing user privacy and seamless Arabic UX."
            )
            self.lbl_privacy_text.setText(
                "NASS operates entirely locally without requiring internet connectivity after engine setup.\n"
                "• Zero documents, images, or texts are sent to external servers or cloud APIs.\n"
                "• All processing takes place 100% on your local machine memory.\n"
                "• Absolute confidentiality and protection for your private and sensitive documents."
            )

    def _open_github(self) -> None:
        """Opens developer GitHub profile in the default system web browser."""
        QDesktopServices.openUrl(QUrl("https://github.com/IbrahimSalha25"))

    def _open_linkedin(self) -> None:
        """Opens developer LinkedIn profile in the default system web browser."""
        QDesktopServices.openUrl(QUrl("https://linkedin.com/in/ibrahim-salha"))

    def _open_email(self) -> None:
        """Opens default mail client to contact the developer."""
        QDesktopServices.openUrl(QUrl("mailto:ibrahimsalha.eng@gmail.com"))

    def _open_repository(self) -> None:
        """Opens application GitHub repository."""
        QDesktopServices.openUrl(QUrl("https://github.com/IbrahimSalha25/NASS"))
