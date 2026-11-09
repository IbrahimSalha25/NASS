"""
History view for NASS application.
Displays a log of processed documents and extraction results during the current session.
Allows re-scanning documents without saving duplicate files, and copying extracted texts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QClipboard, QGuiApplication
from PySide6.QtWidgets import (
    QFileDialog,
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

from nass.core.i18n import I18n, tr
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
    View managing document processing history, re-scanning, and result archiving.
    """

    rescan_requested = Signal(Path)

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
        self.lbl_title = QLabel(tr("history_title"))
        self.lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A;")
        self.lbl_desc = QLabel(tr("history_desc"))
        self.lbl_desc.setStyleSheet("font-size: 12px; color: #64748B;")
        title_box.addWidget(self.lbl_title)
        title_box.addWidget(self.lbl_desc)

        h_layout.addLayout(title_box)
        h_layout.addStretch()

        self.btn_clear = QPushButton(tr("history_clear_btn"))
        self.btn_clear.setObjectName("dangerButton")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self._clear_history)
        h_layout.addWidget(self.btn_clear)

        layout.addWidget(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self._setup_table_headers()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def _setup_table_headers(self) -> None:
        self.table.setHorizontalHeaderLabels([
            tr("history_col_time"),
            tr("history_col_name"),
            tr("history_col_type"),
            tr("history_col_method"),
            tr("history_col_pages"),
            tr("history_col_status"),
            tr("history_col_actions"),
        ])

    def retranslate_ui(self) -> None:
        """Retranslates table headers and view titles for the active language."""
        direction = Qt.RightToLeft if I18n.is_rtl() else Qt.LeftToRight
        self.setLayoutDirection(direction)

        self.lbl_title.setText(tr("history_title"))
        self.lbl_desc.setText(tr("history_desc"))
        self.btn_clear.setText(tr("history_clear_btn"))
        self._setup_table_headers()
        self._refresh_table()

    def add_record_from_result(self, result: DocumentResult) -> None:
        """
        Adds a completed document processing result to the session history.

        Args:
            result: The DocumentResult object to record.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_str = (
            ("اكتمل بنجاح" if I18n.is_rtl() else "Completed")
            if result.status == ProcessingStatus.COMPLETED
            else ("فشل" if I18n.is_rtl() else "Failed")
        )

        method_str = (
            ("نص رقمي مباشر" if I18n.is_rtl() else "Native Text")
            if result.extraction_method.value == "native"
            else (
                ("تعرف ضوئي (OCR)" if I18n.is_rtl() else "OCR")
                if result.extraction_method.value == "ocr"
                else ("معالجة هجينة" if I18n.is_rtl() else "Hybrid")
            )
        )

        rec = HistoryRecord(
            timestamp=now_str,
            file_name=result.file_path.name,
            file_path=str(result.file_path),
            file_type=result.file_type.value.upper(),
            extraction_method=method_str,
            total_pages=result.total_pages,
            confidence=result.average_confidence,
            text_content=result.full_text,
            status=status_str,
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
            if "نجاح" in rec.status or "Completed" in rec.status:
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.red)
            self.table.setItem(row, 5, status_item)

            # Actions widget with Re-scan and Copy buttons
            actions_widget = QWidget()
            aw_layout = QHBoxLayout(actions_widget)
            aw_layout.setContentsMargins(2, 2, 2, 2)
            aw_layout.setSpacing(4)

            btn_rescan = QPushButton(tr("history_btn_rescan"))
            btn_rescan.setIcon(AppIcons.refresh("#1E40AF"))
            btn_rescan.setCursor(Qt.PointingHandCursor)
            btn_rescan.setStyleSheet(
                "background-color: #EFF6FF; color: #1E40AF; border: 1px solid #BFDBFE; "
                "border-radius: 4px; padding: 4px 6px; font-size: 11px; font-weight: 500;"
            )
            btn_rescan.clicked.connect(lambda _, r=rec: self._rescan_record(r))

            btn_copy = QPushButton(tr("history_btn_copy"))
            btn_copy.setIcon(AppIcons.copy("#0F172A"))
            btn_copy.setCursor(Qt.PointingHandCursor)
            btn_copy.setStyleSheet(
                "background-color: #F8FAFC; color: #334155; border: 1px solid #CBD5E1; "
                "border-radius: 4px; padding: 4px 6px; font-size: 11px;"
            )
            btn_copy.clicked.connect(lambda _, t=rec.text_content: self._copy_text(t))

            aw_layout.addWidget(btn_rescan)
            aw_layout.addWidget(btn_copy)
            self.table.setCellWidget(row, 6, actions_widget)

    def _rescan_record(self, rec: HistoryRecord) -> None:
        """
        Handles re-scanning a file from history without duplicating stored files.
        If file path is valid, opens and re-extracts.
        If file path has changed or is missing, alerts the user with an option to locate it.
        """
        file_path = Path(rec.file_path)
        if file_path.exists() and file_path.is_file():
            # File still exists at recorded path
            msg = tr("history_file_same_msg", path=rec.file_path)
            reply = QMessageBox.information(
                self,
                tr("history_btn_rescan"),
                msg,
                QMessageBox.Ok | QMessageBox.Cancel,
                QMessageBox.Ok,
            )
            if reply == QMessageBox.Ok:
                self.rescan_requested.emit(file_path)
        else:
            # File path changed, moved or missing
            reply = QMessageBox.warning(
                self,
                tr("history_file_moved_title"),
                tr("history_file_moved_msg", path=rec.file_path),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                new_path, _ = QFileDialog.getOpenFileName(
                    self,
                    tr("extract_btn_browse"),
                    str(file_path.parent) if file_path.parent.exists() else "",
                    "All Supported Files (*.pdf *.png *.jpg *.jpeg *.tiff *.tif *.bmp *.webp "
                    "*.docx *.xlsx *.xls *.csv *.pptx *.txt *.md *.rtf *.html *.htm *.xml *.json *.odt *.epub);;"
                    "All Files (*.*)",
                )
                if new_path:
                    p = Path(new_path).resolve()
                    if p.exists():
                        rec.file_path = str(p)
                        rec.file_name = p.name
                        self._refresh_table()
                        self.rescan_requested.emit(p)

    def _copy_text(self, text: str) -> None:
        if text.strip():
            clipboard: QClipboard = QGuiApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, tr("copied_title"), tr("copied_msg"))
        else:
            QMessageBox.information(self, tr("warning_title"), tr("extract_status_empty"))

    def _clear_history(self) -> None:
        if not self.records:
            return
        reply = QMessageBox.question(
            self,
            tr("history_clear_btn"),
            "هل أنت متأكد من رغبتك في مسح سجل العمليات الحالية؟" if I18n.is_rtl() else "Are you sure you want to clear current session history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.records.clear()
            self._refresh_table()
