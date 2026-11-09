"""
Batch folder text extraction view for NASS.
Discovers all supported document and image files within a selected directory,
runs asynchronous batch extraction, presents live per-file results in a clean table,
and provides merged previews and multi-format exports (TXT, DOCX, CSV).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QClipboard, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from nass.core.i18n import I18n, tr
from nass.core.models import (
    DocumentResult,
    FileType,
    OcrOptions,
    PageResult,
    ProcessingStatus,
)
from nass.core.settings import SettingsManager
from nass.services.export_service import ExportService
from nass.ui.icons import AppIcons
from nass.utils.file_utils import FileUtils
from nass.utils.logger import logger
from nass.workers.ocr_worker import OcrWorker


class BatchFolderView(QWidget):
    """
    View managing batch folder text extraction lifecycle, file queue display,
    live processing progress, and aggregated results exporting.
    """

    file_rescan_requested = Signal(Path)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.settings = SettingsManager.get_instance()
        self.current_folder: Optional[Path] = None
        self.discovered_files: List[Path] = []
        self.processed_results: Dict[str, DocumentResult] = {}
        self.active_worker: Optional[OcrWorker] = None

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 10, 14, 10)
        main_layout.setSpacing(10)

        # 1. Header Card with Folder Chooser & Options
        header_card = QFrame()
        header_card.setObjectName("cardFrame")
        hc_layout = QVBoxLayout(header_card)
        hc_layout.setContentsMargins(14, 12, 14, 12)
        hc_layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(AppIcons.folder("#1E40AF").pixmap(30, 30))
        top_row.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.lbl_title = QLabel(tr("batch_title"))
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #0F172A;")
        self.lbl_desc = QLabel(tr("batch_desc"))
        self.lbl_desc.setStyleSheet("font-size: 11px; color: #64748B;")
        title_box.addWidget(self.lbl_title)
        title_box.addWidget(self.lbl_desc)
        top_row.addLayout(title_box)
        top_row.addStretch()

        self.btn_select_folder = QPushButton(tr("batch_btn_select_folder"))
        self.btn_select_folder.setObjectName("primaryButton")
        self.btn_select_folder.setCursor(Qt.PointingHandCursor)
        self.btn_select_folder.setIcon(AppIcons.folder("#FFFFFF"))
        self.btn_select_folder.setIconSize(QSize(18, 18))
        self.btn_select_folder.setFixedHeight(34)
        self.btn_select_folder.clicked.connect(self._choose_folder)
        top_row.addWidget(self.btn_select_folder)

        hc_layout.addLayout(top_row)

        # Folder Info & Options Row
        opts_row = QHBoxLayout()
        opts_row.setSpacing(16)

        self.lbl_folder_path = QLabel(tr("batch_no_folder"))
        self.lbl_folder_path.setStyleSheet("font-size: 12px; color: #334155; font-weight: 500;")
        opts_row.addWidget(self.lbl_folder_path, stretch=2)

        self.chk_recursive = QCheckBox(tr("batch_chk_recursive"))
        self.chk_recursive.setChecked(True)
        self.chk_recursive.toggled.connect(self._rescan_folder)
        opts_row.addWidget(self.chk_recursive)

        self.lbl_files_count = QLabel(tr("batch_files_discovered", count=0))
        self.lbl_files_count.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #1E40AF; "
            "background-color: #EFF6FF; border: 1px solid #BFDBFE; "
            "border-radius: 4px; padding: 3px 10px;"
        )
        opts_row.addWidget(self.lbl_files_count)

        hc_layout.addLayout(opts_row)
        main_layout.addWidget(header_card)

        # 2. Control Bar (Start / Cancel / Progress)
        control_bar = QFrame()
        control_bar.setObjectName("cardFrame")
        cb_layout = QHBoxLayout(control_bar)
        cb_layout.setContentsMargins(12, 8, 12, 8)
        cb_layout.setSpacing(10)

        self.btn_start = QPushButton(tr("batch_btn_start"))
        self.btn_start.setObjectName("primaryButton")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setFixedHeight(34)
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self._start_batch_processing)
        cb_layout.addWidget(self.btn_start)

        self.btn_cancel = QPushButton(tr("batch_btn_cancel"))
        self.btn_cancel.setObjectName("dangerButton")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setFixedHeight(34)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel_batch_processing)
        cb_layout.addWidget(self.btn_cancel)

        prog_box = QVBoxLayout()
        prog_box.setSpacing(2)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.lbl_progress_status = QLabel(tr("batch_status_idle"))
        self.lbl_progress_status.setStyleSheet("color: #64748B; font-size: 11px;")
        prog_box.addWidget(self.progress_bar)
        prog_box.addWidget(self.lbl_progress_status)
        cb_layout.addLayout(prog_box, stretch=2)

        main_layout.addWidget(control_bar)

        # 3. Main Tabs (Table View & Merged Text View)
        self.tabs = QTabWidget()

        # Tab A: Files Table
        tab_table_widget = QWidget()
        tt_layout = QVBoxLayout(tab_table_widget)
        tt_layout.setContentsMargins(4, 6, 4, 4)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self._setup_table_headers()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setAlternatingRowColors(True)
        tt_layout.addWidget(self.table)
        self.tabs.addTab(tab_table_widget, tr("batch_tab_table"))

        # Tab B: Merged Extracted Text Viewer
        tab_merged_widget = QWidget()
        tm_layout = QVBoxLayout(tab_merged_widget)
        tm_layout.setContentsMargins(4, 6, 4, 4)

        self.txt_merged = QTextEdit()
        self.txt_merged.setReadOnly(True)
        self.txt_merged.setPlaceholderText(tr("extract_txt_placeholder"))
        tm_layout.addWidget(self.txt_merged)
        self.tabs.addTab(tab_merged_widget, tr("batch_tab_merged"))

        main_layout.addWidget(self.tabs, stretch=2)

        # 4. Action Export Bar
        export_bar = QHBoxLayout()
        export_bar.setSpacing(6)

        self.btn_copy_merged = QPushButton(tr("batch_btn_copy_merged"))
        self.btn_copy_merged.setIcon(AppIcons.copy())
        self.btn_copy_merged.setIconSize(QSize(16, 16))
        self.btn_copy_merged.setFixedHeight(30)
        self.btn_copy_merged.setCursor(Qt.PointingHandCursor)
        self.btn_copy_merged.clicked.connect(self._copy_merged_text)

        self.btn_export_txt = QPushButton(tr("batch_btn_export_txt"))
        self.btn_export_txt.setIcon(AppIcons.export())
        self.btn_export_txt.setIconSize(QSize(16, 16))
        self.btn_export_txt.setFixedHeight(30)
        self.btn_export_txt.setCursor(Qt.PointingHandCursor)
        self.btn_export_txt.clicked.connect(self._export_merged_txt)

        self.btn_export_docx = QPushButton(tr("batch_btn_export_docx"))
        self.btn_export_docx.setIcon(AppIcons.export())
        self.btn_export_docx.setIconSize(QSize(16, 16))
        self.btn_export_docx.setFixedHeight(30)
        self.btn_export_docx.setCursor(Qt.PointingHandCursor)
        self.btn_export_docx.clicked.connect(self._export_merged_docx)

        self.btn_export_csv = QPushButton(tr("batch_btn_export_csv"))
        self.btn_export_csv.setIcon(AppIcons.export())
        self.btn_export_csv.setIconSize(QSize(16, 16))
        self.btn_export_csv.setFixedHeight(30)
        self.btn_export_csv.setCursor(Qt.PointingHandCursor)
        self.btn_export_csv.clicked.connect(self._export_csv_report)

        export_bar.addWidget(self.btn_copy_merged)
        export_bar.addStretch()
        export_bar.addWidget(self.btn_export_txt)
        export_bar.addWidget(self.btn_export_docx)
        export_bar.addWidget(self.btn_export_csv)
        main_layout.addLayout(export_bar)

    def _setup_table_headers(self) -> None:
        self.table.setHorizontalHeaderLabels([
            tr("batch_col_filename"),
            tr("batch_col_type"),
            tr("batch_col_status"),
            tr("batch_col_pages"),
            tr("batch_col_words"),
            tr("batch_col_chars"),
            tr("batch_col_actions"),
        ])

    def _choose_folder(self) -> None:
        """Open native directory picker to select folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            tr("batch_btn_select_folder"),
            str(self.current_folder) if self.current_folder else "",
        )
        if folder:
            p = Path(folder).resolve()
            if p.is_dir():
                self.current_folder = p
                self._rescan_folder()

    def _rescan_folder(self) -> None:
        """Scan current directory for supported files based on recursive option."""
        if not self.current_folder or not self.current_folder.is_dir():
            return

        self.lbl_folder_path.setText(tr("batch_folder_selected", path=str(self.current_folder)))
        self.lbl_progress_status.setText(tr("batch_status_scanning"))

        # Discover all supported documents
        self.discovered_files = FileUtils.discover_files(
            [self.current_folder],
            recursive=self.chk_recursive.isChecked(),
        )

        count = len(self.discovered_files)
        self.lbl_files_count.setText(tr("batch_files_discovered", count=count))

        if count > 0:
            self.btn_start.setEnabled(True)
            self.btn_select_folder.setText(tr("batch_btn_change_folder"))
            self.lbl_progress_status.setText(tr("batch_status_idle"))
        else:
            self.btn_start.setEnabled(False)
            self.lbl_progress_status.setText(tr("batch_status_empty_folder"))

        self.processed_results.clear()
        self.txt_merged.clear()
        self._populate_table_with_queue()

    def _populate_table_with_queue(self) -> None:
        """Populate table with queued files before extraction."""
        self.table.setRowCount(len(self.discovered_files))
        for row, f in enumerate(self.discovered_files):
            file_type = FileUtils.detect_file_type(f)
            type_name = file_type.display_name_ar if I18n.is_rtl() else file_type.value.upper()

            self.table.setItem(row, 0, QTableWidgetItem(f.name))
            self.table.setItem(row, 1, QTableWidgetItem(type_name))
            self.table.setItem(row, 2, QTableWidgetItem("في الانتظار" if I18n.is_rtl() else "Queued"))
            self.table.setItem(row, 3, QTableWidgetItem("-"))
            self.table.setItem(row, 4, QTableWidgetItem("-"))
            self.table.setItem(row, 5, QTableWidgetItem("-"))

            actions_widget = QWidget()
            aw_layout = QHBoxLayout(actions_widget)
            aw_layout.setContentsMargins(4, 2, 4, 2)
            lbl_dash = QLabel("-")
            lbl_dash.setAlignment(Qt.AlignCenter)
            aw_layout.addWidget(lbl_dash)
            self.table.setCellWidget(row, 6, actions_widget)

    def _start_batch_processing(self) -> None:
        """Start asynchronous batch processing worker across all discovered files."""
        if not self.discovered_files:
            return

        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_select_folder.setEnabled(False)
        self.chk_recursive.setEnabled(False)
        self.progress_bar.setValue(0)

        self.processed_results.clear()
        self.txt_merged.clear()

        # Build options matching global defaults
        opts = OcrOptions(
            language=self.settings.get("default_language", "ara+eng"),
            dpi=self.settings.get("dpi", 300),
            apply_enhancement=self.settings.get("apply_enhancement", False),
            enhance_contrast=self.settings.get("enhance_contrast", False),
            denoise=self.settings.get("denoise", False),
            extract_math=self.settings.get("math_enabled", False),
        )

        self.active_worker = OcrWorker(files=self.discovered_files, options=opts)
        self.active_worker.file_started.connect(self._on_worker_file_started)
        self.active_worker.file_finished.connect(self._on_worker_file_finished)
        self.active_worker.overall_progress.connect(self._on_worker_overall_progress)
        self.active_worker.all_finished.connect(self._on_worker_all_finished)
        self.active_worker.error_occurred.connect(self._on_worker_error)
        self.active_worker.start()

    def _cancel_batch_processing(self) -> None:
        if self.active_worker and self.active_worker.isRunning():
            self.lbl_progress_status.setText(tr("extract_status_stopping"))
            self.active_worker.cancel()
            self.btn_cancel.setEnabled(False)

    def _on_worker_file_started(self, current: int, total: int, file_path_str: str) -> None:
        p = Path(file_path_str)
        self.lbl_progress_status.setText(
            f"({current}/{total}) " + (f"جاري معالجة: {p.name}" if I18n.is_rtl() else f"Processing: {p.name}")
        )
        row = current - 1
        if 0 <= row < self.table.rowCount():
            item = QTableWidgetItem("جاري الاستخراج..." if I18n.is_rtl() else "Extracting...")
            item.setForeground(Qt.blue)
            self.table.setItem(row, 2, item)

    def _on_worker_file_finished(self, current: int, total: int, doc_res: DocumentResult) -> None:
        self.processed_results[str(doc_res.file_path)] = doc_res
        row = current - 1
        if 0 <= row < self.table.rowCount():
            # Update status
            is_ok = doc_res.status == ProcessingStatus.COMPLETED
            status_text = (
                ("اكتمل بنجاح" if I18n.is_rtl() else "Completed")
                if is_ok
                else ("فشل" if I18n.is_rtl() else "Failed")
            )
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(Qt.darkGreen if is_ok else Qt.red)
            self.table.setItem(row, 2, status_item)

            # Pages, Words, Chars
            full_txt = doc_res.full_text
            words = len(full_txt.split()) if full_txt else 0
            chars = len(full_txt) if full_txt else 0

            self.table.setItem(row, 3, QTableWidgetItem(str(doc_res.total_pages)))
            self.table.setItem(row, 4, QTableWidgetItem(f"{words:,}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{chars:,}"))

            # Actions: Preview and Copy buttons
            actions_widget = QWidget()
            aw_layout = QHBoxLayout(actions_widget)
            aw_layout.setContentsMargins(4, 2, 4, 2)
            aw_layout.setSpacing(4)

            btn_preview = QPushButton("معاينة" if I18n.is_rtl() else "Preview")
            btn_preview.setCursor(Qt.PointingHandCursor)
            btn_preview.setFixedHeight(24)
            btn_preview.setStyleSheet(
                "background-color: #EFF6FF; color: #1E40AF; border: 1px solid #BFDBFE; "
                "border-radius: 4px; padding: 2px 6px; font-size: 11px;"
            )
            btn_preview.clicked.connect(lambda _, r=doc_res: self._preview_single_file_result(r))

            btn_copy = QPushButton("نسخ" if I18n.is_rtl() else "Copy")
            btn_copy.setCursor(Qt.PointingHandCursor)
            btn_copy.setFixedHeight(24)
            btn_copy.setStyleSheet(
                "background-color: #F8FAFC; color: #334155; border: 1px solid #CBD5E1; "
                "border-radius: 4px; padding: 2px 6px; font-size: 11px;"
            )
            btn_copy.clicked.connect(lambda _, r=doc_res: self._copy_single_file_text(r))

            aw_layout.addWidget(btn_preview)
            aw_layout.addWidget(btn_copy)
            self.table.setCellWidget(row, 6, actions_widget)

        self._append_to_merged_view(doc_res)

    def _append_to_merged_view(self, doc: DocumentResult) -> None:
        """Appends formatted file section to merged text viewer."""
        current = self.txt_merged.toPlainText()
        separator = "=" * 60
        header = f"\n\n{separator}\nالملف: {doc.file_path.name}\nالمسار: {doc.file_path}\nطريقة المعالجة: {doc.method_display_name}\n{separator}\n\n"
        content = doc.full_text if doc.full_text.strip() else "[لا يوجد نص مستخرج أو حدث خطأ في الملف]"
        self.txt_merged.setText(f"{current}{header}{content}".strip())

    def _on_worker_overall_progress(self, pct: int, msg: str) -> None:
        self.progress_bar.setValue(pct)
        self.lbl_progress_status.setText(msg)

    def _on_worker_all_finished(self, results: List[DocumentResult]) -> None:
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_select_folder.setEnabled(True)
        self.chk_recursive.setEnabled(True)
        self.progress_bar.setValue(100)

        succeeded = sum(1 for r in results if r.status == ProcessingStatus.COMPLETED)
        failed = len(results) - succeeded
        self.lbl_progress_status.setText(
            tr("batch_status_completed", success=succeeded, failed=failed)
        )

    def _on_worker_error(self, err: str) -> None:
        QMessageBox.critical(self, tr("extract_error_title"), err)
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_select_folder.setEnabled(True)
        self.chk_recursive.setEnabled(True)

    def _preview_single_file_result(self, doc_res: DocumentResult) -> None:
        """Open modal dialog to preview single file extracted text."""
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("batch_preview_dialog_title", name=doc_res.file_path.name))
        dlg.resize(600, 450)
        dlg.setLayoutDirection(Qt.RightToLeft if I18n.is_rtl() else Qt.LeftToRight)

        d_layout = QVBoxLayout(dlg)
        d_layout.setContentsMargins(14, 14, 14, 14)
        d_layout.setSpacing(10)

        info_lbl = QLabel(
            f"الملف: {doc_res.file_path.name} | الصفحات: {doc_res.total_pages} | الطريقة: {doc_res.method_display_name}"
            if I18n.is_rtl() else
            f"File: {doc_res.file_path.name} | Pages: {doc_res.total_pages} | Method: {doc_res.method_display_name}"
        )
        info_lbl.setStyleSheet("font-weight: bold; color: #1E3A8A;")
        d_layout.addWidget(info_lbl)

        txt_view = QTextEdit()
        txt_view.setReadOnly(True)
        txt_view.setText(doc_res.full_text)
        txt_view.setLayoutDirection(Qt.RightToLeft if I18n.is_rtl() else Qt.LeftToRight)
        d_layout.addWidget(txt_view)

        btn_box = QHBoxLayout()
        btn_copy = QPushButton("نسخ النص" if I18n.is_rtl() else "Copy Text")
        btn_copy.setCursor(Qt.PointingHandCursor)
        btn_copy.clicked.connect(lambda: self._copy_single_file_text(doc_res))
        btn_close = QPushButton("إغلاق" if I18n.is_rtl() else "Close")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(dlg.accept)

        btn_box.addWidget(btn_copy)
        btn_box.addStretch()
        btn_box.addWidget(btn_close)
        d_layout.addLayout(btn_box)

        dlg.exec()

    def _copy_single_file_text(self, doc_res: DocumentResult) -> None:
        text = doc_res.full_text.strip()
        if not text:
            QMessageBox.information(self, tr("extract_notice_title"), tr("extract_status_empty"))
            return
        clipboard: QClipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, tr("copied_title"), tr("copied_msg"))

    def _copy_merged_text(self) -> None:
        text = self.txt_merged.toPlainText().strip()
        if not text:
            QMessageBox.information(self, tr("extract_notice_title"), tr("extract_status_empty"))
            return
        clipboard: QClipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, tr("copied_title"), tr("extract_copied_all_msg"))

    def _get_active_results_list(self) -> List[DocumentResult]:
        return [self.processed_results[str(f)] for f in self.discovered_files if str(f) in self.processed_results]

    def _export_merged_txt(self) -> None:
        results = self._get_active_results_list()
        if not results:
            QMessageBox.information(self, tr("extract_notice_title"), tr("extract_no_text_export"))
            return

        folder_name = self.current_folder.name if self.current_folder else "batch"
        default_name = f"{folder_name}_merged_extracted.txt"
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("extract_export_txt_title"),
            default_name,
            tr("extract_export_txt_filter"),
        )
        if path:
            try:
                ExportService.export_to_txt(results, Path(path))
                QMessageBox.information(self, tr("copied_title"), tr("extract_export_txt_success", path=path))
            except Exception as e:
                QMessageBox.critical(self, tr("extract_export_error_title"), tr("extract_export_error_msg", err=e))

    def _export_merged_docx(self) -> None:
        results = self._get_active_results_list()
        if not results:
            QMessageBox.information(self, tr("extract_notice_title"), tr("extract_no_text_export"))
            return

        folder_name = self.current_folder.name if self.current_folder else "batch"
        default_name = f"{folder_name}_merged_extracted.docx"
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("extract_export_docx_title"),
            default_name,
            tr("extract_export_docx_filter"),
        )
        if path:
            try:
                ExportService.export_to_docx(results, Path(path))
                QMessageBox.information(self, tr("copied_title"), tr("extract_export_docx_success", path=path))
            except Exception as e:
                QMessageBox.critical(self, tr("extract_export_error_title"), tr("extract_export_error_msg", err=e))

    def _export_csv_report(self) -> None:
        results = self._get_active_results_list()
        if not results:
            QMessageBox.information(self, tr("extract_notice_title"), tr("extract_no_text_export"))
            return

        folder_name = self.current_folder.name if self.current_folder else "batch"
        default_name = f"{folder_name}_batch_report.csv"
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("batch_export_csv_title"),
            default_name,
            tr("batch_export_csv_filter"),
        )
        if path:
            try:
                ExportService.export_to_csv(results, Path(path))
                QMessageBox.information(self, tr("copied_title"), tr("batch_export_csv_success", path=path))
            except Exception as e:
                QMessageBox.critical(self, tr("extract_export_error_title"), tr("extract_export_error_msg", err=e))

    def retranslate_ui(self) -> None:
        """Update texts when UI language switches."""
        direction = Qt.RightToLeft if I18n.is_rtl() else Qt.LeftToRight
        self.setLayoutDirection(direction)

        self.lbl_title.setText(tr("batch_title"))
        self.lbl_desc.setText(tr("batch_desc"))
        self.btn_select_folder.setText(
            tr("batch_btn_change_folder") if self.current_folder else tr("batch_btn_select_folder")
        )
        self.chk_recursive.setText(tr("batch_chk_recursive"))

        count = len(self.discovered_files)
        self.lbl_files_count.setText(tr("batch_files_discovered", count=count))
        if not self.current_folder:
            self.lbl_folder_path.setText(tr("batch_no_folder"))
            self.lbl_progress_status.setText(tr("batch_status_idle"))
        else:
            self.lbl_folder_path.setText(tr("batch_folder_selected", path=str(self.current_folder)))

        self.btn_start.setText(tr("batch_btn_start"))
        self.btn_cancel.setText(tr("batch_btn_cancel"))
        self.btn_copy_merged.setText(tr("batch_btn_copy_merged"))
        self.btn_export_txt.setText(tr("batch_btn_export_txt"))
        self.btn_export_docx.setText(tr("batch_btn_export_docx"))
        self.btn_export_csv.setText(tr("batch_btn_export_csv"))

        self.tabs.setTabText(0, tr("batch_tab_table"))
        self.tabs.setTabText(1, tr("batch_tab_merged"))
        self._setup_table_headers()
