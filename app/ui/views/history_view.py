"""
شاشة سجل العمليات (History View) لتطبيق نَصّ (NASS).
تعرض أرشيف الملفات المعالجة ونتائجها مع إمكانية مراجعتها ونسخها مجدداً.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QClipboard, QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.models import DocumentResult
from app.ui.icons import AppIcons


@dataclass
class HistoryRecord:
    timestamp: str
    file_name: str
    file_path: str
    total_pages: int
    confidence: float
    text_content: str
    status: str


class HistoryView(QWidget):
    """شاشة سجل عمليات الاستخراج."""

    open_result_requested = Signal(object)  # يرسل HistoryRecord أو نص

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.records: List[HistoryRecord] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        header = QFrame()
        header.setObjectName("cardFrame")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(14, 10, 14, 10)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        lbl_title = QLabel("سجل عمليات الاستخراج")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E3A8A;")
        lbl_desc = QLabel("عرض العمليات السابقة خلال جلسة العمل الحالية مع إمكانية نسخها ومراجعتها")
        lbl_desc.setStyleSheet("font-size: 12px; color: #64748B;")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)

        h_layout.addLayout(title_box)
        h_layout.addStretch()

        btn_clear = QPushButton("مسح السجل")
        btn_clear.setObjectName("dangerButton")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.clicked.connect(self._clear_history)
        h_layout.addWidget(btn_clear)

        layout.addWidget(header)

        # جدول السجل
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "وقت المعالجة", "اسم الملف", "عدد الصفحات", "متوسط الثقة", "الحالة", "إجراءات"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

    def add_record_from_result(self, result: DocumentResult):
        """إضافة عملية جديدة إلى السجل."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_ar = "اكتمل بنجاح" if result.status.value == "completed" else "فشل"
        rec = HistoryRecord(
            timestamp=now_str,
            file_name=result.file_path.name,
            file_path=str(result.file_path),
            total_pages=result.total_pages,
            confidence=result.average_confidence,
            text_content=result.full_text,
            status=status_ar,
        )
        self.records.insert(0, rec)
        self._refresh_table()

    def _refresh_table(self):
        self.table.setRowCount(len(self.records))
        for row, rec in enumerate(self.records):
            self.table.setItem(row, 0, QTableWidgetItem(rec.timestamp))
            self.table.setItem(row, 1, QTableWidgetItem(rec.file_name))
            self.table.setItem(row, 2, QTableWidgetItem(str(rec.total_pages)))
            self.table.setItem(row, 3, QTableWidgetItem(f"{rec.confidence:.1f}%"))

            status_item = QTableWidgetItem(rec.status)
            if "نجاح" in rec.status:
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.red)
            self.table.setItem(row, 4, status_item)

            btn_copy = QPushButton("نسخ النص")
            btn_copy.setIcon(AppIcons.copy())
            btn_copy.setCursor(Qt.PointingHandCursor)
            btn_copy.clicked.connect(lambda _, t=rec.text_content: self._copy_text(t))
            self.table.setCellWidget(row, 5, btn_copy)

    def _copy_text(self, text: str):
        if text.strip():
            clipboard: QClipboard = QGuiApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "تم النسخ", "تم نسخ نص العملية إلى الحافظة بنجاح.")
        else:
            QMessageBox.information(self, "تنبيه", "هذه العملية لا تحتوي على نص منسوخ.")

    def _clear_history(self):
        if not self.records:
            return
        reply = QMessageBox.question(
            self,
            "تأكيد مسح السجل",
            "هل أنت متأكد من رغبتك في مسح سجل العمليات الحالية؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.records.clear()
            self._refresh_table()
