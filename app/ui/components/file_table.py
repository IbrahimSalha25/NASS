"""
جدول عرض الملفات المضافة وحالتها أثناء دورة حياة المعالجة.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from app.core.file_manager import FileManager
from app.core.models import DocumentResult, FileType, ProcessingStatus


class FileTableWidget(QTableWidget):
    """جدول عرض الملفات وحالاتها وتفاصيل كل مستند."""

    file_removed = Signal(int)    # إرسال فهرس الملف المحذوف
    file_selected = Signal(int)   # إرسال فهرس الملف عند اختياره لعرض نتائجه

    HEADERS = ["اسم الملف", "النوع", "الحجم", "الصفحات", "الثقة", "الحالة", "حذف"]

    def __init__(self, parent=None):
        super().__init__(0, len(self.HEADERS), parent)
        self.setHorizontalHeaderLabels(self.HEADERS)
        self._setup_table()
        self.itemSelectionChanged.connect(self._on_selection_changed)

    def _setup_table(self):
        """تهيئة خصائص الجدول ومحاذاته."""
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)

        # ضبط عرض الأعمدة
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)       # اسم الملف
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # النوع
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # الحجم
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # الصفحات
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # الثقة
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # الحالة
        header.setSectionResizeMode(6, QHeaderView.Fixed)            # زر الحذف
        self.setColumnWidth(6, 65)

    def add_file_row(self, file_path: Path):
        """إضافة سطر جديد لملف مضاف إلى القائمة."""
        row_idx = self.rowCount()
        self.insertRow(row_idx)

        # 1. اسم الملف
        name_item = QTableWidgetItem(file_path.name)
        name_item.setToolTip(str(file_path))
        name_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 2. النوع
        file_type = FileManager.detect_file_type(file_path)
        type_str = "مستند PDF" if file_type == FileType.PDF else "صورة"
        type_item = QTableWidgetItem(type_str)
        type_item.setTextAlignment(Qt.AlignCenter)

        # 3. الحجم
        try:
            size_kb = file_path.stat().st_size / 1024
            size_str = f"{size_kb / 1024:.1f} MB" if size_kb > 1024 else f"{size_kb:.0f} KB"
        except Exception:
            size_str = "-"
        size_item = QTableWidgetItem(size_str)
        size_item.setTextAlignment(Qt.AlignCenter)

        # 4. الصفحات
        pages_item = QTableWidgetItem("-")
        pages_item.setTextAlignment(Qt.AlignCenter)

        # 5. الثقة
        conf_item = QTableWidgetItem("-")
        conf_item.setTextAlignment(Qt.AlignCenter)

        # 6. الحالة
        status_item = QTableWidgetItem("بانتظار البدء")
        status_item.setTextAlignment(Qt.AlignCenter)
        status_item.setForeground(QColor("#64748B"))

        # 7. زر الإزالة
        del_btn = QPushButton("إزالة")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(
            "padding: 2px 6px; font-size: 11px; background-color: #F8FAFC; border: 1px solid #E2E8F0;"
        )
        del_btn.clicked.connect(lambda _, r=row_idx: self._remove_row(r))

        self.setItem(row_idx, 0, name_item)
        self.setItem(row_idx, 1, type_item)
        self.setItem(row_idx, 2, size_item)
        self.setItem(row_idx, 3, pages_item)
        self.setItem(row_idx, 4, conf_item)
        self.setItem(row_idx, 5, status_item)
        self.setCellWidget(row_idx, 6, del_btn)

    def _remove_row(self, row: int):
        """حذف سطر من الجدول وإعادة ضبط مؤشرات الأزرار."""
        self.removeRow(row)
        # إعادة ربط الأزرار المتبقية بالفهارس الصحيحة
        for r in range(self.rowCount()):
            btn = self.cellWidget(r, 6)
            if isinstance(btn, QPushButton):
                btn.clicked.disconnect()
                btn.clicked.connect(lambda _, curr_r=r: self._remove_row(curr_r))
        self.file_removed.emit(row)

    def update_file_status(
        self,
        row_idx: int,
        status: ProcessingStatus,
        pages_count: Optional[int] = None,
        confidence: Optional[float] = None,
        error_msg: Optional[str] = None,
    ):
        """تحديث بيانات السطر عند تغيير حالة المعالجة."""
        if row_idx >= self.rowCount():
            return

        # تحديث عدد الصفحات
        if pages_count is not None:
            p_item = self.item(row_idx, 3)
            if p_item:
                p_item.setText(str(pages_count))

        # تحديث نسبة الثقة
        if confidence is not None and confidence > 0:
            c_item = self.item(row_idx, 4)
            if c_item:
                c_item.setText(f"{confidence:.1f}%")

        # تحديث الحالة ولونها
        s_item = self.item(row_idx, 5)
        if s_item:
            if status == ProcessingStatus.PROCESSING:
                s_item.setText("جاري الاستخراج...")
                s_item.setForeground(QColor("#1E5E8A"))
            elif status == ProcessingStatus.COMPLETED:
                s_item.setText("اكتمل بنجاح")
                s_item.setForeground(QColor("#10B981"))
            elif status == ProcessingStatus.FAILED:
                s_item.setText("فشل")
                s_item.setForeground(QColor("#EF4444"))
                if error_msg:
                    s_item.setToolTip(error_msg)
            elif status == ProcessingStatus.CANCELLED:
                s_item.setText("أُلغي")
                s_item.setForeground(QColor("#F59E0B"))

    def _on_selection_changed(self):
        """إرسال الفهرس عند اختيار سطر لمطالعة تفاصيله."""
        selected_rows = self.selectionModel().selectedRows()
        if selected_rows:
            self.file_selected.emit(selected_rows[0].row())
