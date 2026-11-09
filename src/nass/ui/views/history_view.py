"""
History view for NASS application.
Displays a log of processed documents and extraction results during the current session.
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

from nass.core.models import DocumentResult, ProcessingStatus
from nass.ui.icons import AppIcons


@dataclass
class HistoryRecord:
    """Record representing a single extracted document in history."""
    timestamp: str
    file_name: str
    file_path: str
    file_type: str
    extraction_method: str
    total_pages: int
    confidence: float
    text_content: str
    status: str


class HistoryView(QWidget):
    """
    View managing document processing history and result archiving.
    """

    open_result_requested = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.records: List[HistoryRecord] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Header bar
        header = QFrame()
        header.setObjectName("cardFrame")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 12, 16, 12)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        lbl_title = QLabel("سجل عمليات الاستخراج")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A;")
        lbl_desc = QLabel("عرض أرشيف المستندات والملفات المعالجة خلال الجلسة الحالية")
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

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "وقت المعالجة",
            "اسم الملف",
            "النوع",
            "طريقة الاستخراج",
            "الصفحات",
            "الحالة",
            "إجراءات",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def add_record_from_result(self, result: DocumentResult) -> None:
        """
        Adds a completed document processing result to the session history.

        Args:
            result: The DocumentResult object to record.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_ar = "اكتمل بنجاح" if result.status == ProcessingStatus.COMPLETED else "فشل"
        
        method_ar = "نص رقمي مباشر" if result.extraction_method.value == "native_text" else (
            "تعرف ضوئي (OCR)" if result.extraction_method.value == "ocr" else "معالجة هجينة"
        )

        rec = HistoryRecord(
            timestamp=now_str,
            file_name=result.file_path.name,
            file_path=str(result.file_path),
            file_type=result.file_type.value.upper(),
            extraction_method=method_ar,
            total_pages=result.total_pages,
            confidence=result.average_confidence,
            text_content=result.full_text,
            status=status_ar,
        )
        self.records.insert(0, rec)
        self._refresh_table()

    def _refresh_table(self) -> None:
        self.table.setRowCount(len(self.records))
        for row, rec in enumerate(self.records):
            self.table.setItem(row, 0, QTableWidgetItem(rec.timestamp))
            self.table.setItem(row, 1, QTableWidgetItem(rec.file_name))
            self.table.setItem(row, 2, QTableWidgetItem(rec.file_type))
            self.table.setItem(row, 3, QTableWidgetItem(rec.extraction_method))
            self.table.setItem(row, 4, QTableWidgetItem(str(rec.total_pages)))

            status_item = QTableWidgetItem(rec.status)
            if "نجاح" in rec.status:
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.red)
            self.table.setItem(row, 5, status_item)

            btn_copy = QPushButton("نسخ النص")
            btn_copy.setIcon(AppIcons.copy())
            btn_copy.setCursor(Qt.PointingHandCursor)
            btn_copy.setStyleSheet(
                "background-color: #EFF6FF; color: #1E40AF; border: 1px solid #BFDBFE; "
                "border-radius: 4px; padding: 4px 8px; font-size: 11px;"
            )
            btn_copy.clicked.connect(lambda _, t=rec.text_content: self._copy_text(t))
            self.table.setCellWidget(row, 6, btn_copy)

    def _copy_text(self, text: str) -> None:
        if text.strip():
            clipboard: QClipboard = QGuiApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "تم النسخ", "تم نسخ نص المستند إلى الحافظة بنجاح.")
        else:
            QMessageBox.information(self, "تنبيه", "هذه العملية لا تحتوي على نص منسوخ.")

    def _clear_history(self) -> None:
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
