"""
منطقة السحب والإفلات (Drop Zone) المتوافقة مع ملفات PDF والصور والمجلدات.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.config import SUPPORTED_ALL_EXTENSIONS


class DropZoneWidget(QFrame):
    """عنصر واجهة تفاعلي لسحب وإفلات الملفات واختيارها."""

    files_selected = Signal(list)  # إرسال قائمة المسارات المحددة

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        # العنوان الرئيسي للمنطقة
        self.title_label = QLabel("اسحب وأفلت ملفات PDF والصور أو المجلدات هنا")
        self.title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E293B;")
        self.title_label.setAlignment(Qt.AlignCenter)

        # النص التوضيحي للصيغ المدعومة
        supported_text = "الصيغ المدعومة: PDF, PNG, JPG, JPEG, TIFF, BMP, WEBP"
        self.subtitle_label = QLabel(supported_text)
        self.subtitle_label.setStyleSheet("font-size: 12px; color: #64748B;")
        self.subtitle_label.setAlignment(Qt.AlignCenter)

        # أزرار التصفح والاختيار
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)
        btn_layout.setSpacing(10)

        self.btn_select_files = QPushButton("اختيار ملفات...")
        self.btn_select_files.setCursor(Qt.PointingHandCursor)
        self.btn_select_files.clicked.connect(self._browse_files)

        self.btn_select_folder = QPushButton("اختيار مجلد...")
        self.btn_select_folder.setCursor(Qt.PointingHandCursor)
        self.btn_select_folder.clicked.connect(self._browse_folder)

        btn_layout.addWidget(self.btn_select_files)
        btn_layout.addWidget(self.btn_select_folder)

        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addLayout(btn_layout)

    def dragEnterEvent(self, event):
        """فحص نوع البيانات عند بدء السحب داخل العنصر."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("border-color: #1E5E8A; background-color: #EFF6FF;")
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        """إعادة المظهر الافتراضي عند مغادرة المؤشر."""
        self.setStyleSheet("")
        event.accept()

    def dropEvent(self, event):
        """التقاط المسارات المفلتة وإرسالها."""
        self.setStyleSheet("")
        urls = event.mimeData().urls()
        paths: List[Path] = []
        for url in urls:
            local_path = url.toLocalFile()
            if local_path:
                paths.append(Path(local_path))

        if paths:
            self.files_selected.emit(paths)
        event.acceptProposedAction()

    def _browse_files(self):
        """فتح نافذة اختيار ملفات متعددة."""
        extensions_pattern = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_ALL_EXTENSIONS))
        filter_str = f"الملفات المدعومة ({extensions_pattern});;جميع الملفات (*.*)"
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "اختر ملفات لاستخراج النصوص",
            "",
            filter_str,
        )
        if file_paths:
            self.files_selected.emit([Path(p) for p in file_paths])

    def _browse_folder(self):
        """فتح نافذة اختيار مجلد كامل."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "اختر مجلداً يحتوي على صور أو ملفات PDF",
            "",
        )
        if folder_path:
            self.files_selected.emit([Path(folder_path)])
