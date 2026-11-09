"""
Export service supporting TXT, DOCX, and LaTeX output formats.
Preserves UTF-8 encoding, RTL Arabic paragraph alignment, and page separation.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Union

from nass.core.models import DocumentResult
from nass.utils.logger import logger


class ExportService:
    """Service for exporting extracted document results to user-selected formats."""

    @staticmethod
    def export_to_txt(
        documents: Union[DocumentResult, List[DocumentResult]],
        output_path: Path | str,
        include_headers: bool = True,
    ) -> Path:
        """Export extracted text to UTF-8 plain text file."""
        path = Path(output_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        docs = [documents] if isinstance(documents, DocumentResult) else documents
        lines: List[str] = []

        for doc in docs:
            if include_headers:
                lines.append("=" * 60)
                lines.append(f"الملف: {doc.file_path.name}")
                lines.append(f"طريقة الاستخراج: {doc.method_display_name}")
                lines.append(f"عدد الصفحات / الأقسام: {doc.total_pages}")
                if doc.average_confidence > 0:
                    lines.append(f"متوسط الدقة / الثقة: {doc.average_confidence:.1f}%")
                lines.append("=" * 60)
                lines.append("")

            for page in doc.pages:
                if include_headers and doc.total_pages > 1:
                    header_title = page.title or f"الصفحة {page.page_number}"
                    lines.append(f"--- [{header_title}] ---")
                    lines.append("")

                if page.text.strip():
                    lines.append(page.text)
                elif page.error_message:
                    lines.append(f"[خطأ في استخراج هذا القسم: {page.error_message}]")
                else:
                    lines.append("[لا يوجد نص مكتشف في هذا القسم]")

                if page.equations:
                    lines.append("")
                    lines.append("المعادلات الرياضية (LaTeX):")
                    for eq in page.equations:
                        lines.append(f"  {eq}")

                lines.append("")

            lines.append("")

        content = "\n".join(lines).strip()

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"TXT exported successfully: {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to export TXT: {e}")
            raise IOError(f"Could not save TXT file: {e}")

    @staticmethod
    def export_to_docx(
        documents: Union[DocumentResult, List[DocumentResult]],
        output_path: Path | str,
    ) -> Path:
        """Export extracted text to Word (DOCX) document with RTL alignment."""
        import docx
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        path = Path(output_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        docs = [documents] if isinstance(documents, DocumentResult) else documents
        doc_file = docx.Document()

        for doc_idx, doc in enumerate(docs):
            if doc_idx > 0:
                doc_file.add_page_break()

            heading = doc_file.add_heading(f"نَصّ — {doc.file_path.name}", level=1)
            heading.alignment = WD_ALIGN_PARAGRAPH.RIGHT

            info_p = doc_file.add_paragraph()
            info_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            info_run = info_p.add_run(
                f"طريقة الاستخراج: {doc.method_display_name} | الصفحات: {doc.total_pages} | متوسط الثقة: {doc.average_confidence:.1f}%"
            )
            info_run.font.italic = True

            doc_file.add_paragraph("-" * 40).alignment = WD_ALIGN_PARAGRAPH.RIGHT

            for page in doc.pages:
                if doc.total_pages > 1:
                    header_title = page.title or f"الصفحة {page.page_number}"
                    page_head = doc_file.add_heading(header_title, level=2)
                    page_head.alignment = WD_ALIGN_PARAGRAPH.RIGHT

                text_content = page.text.strip()
                if text_content:
                    for para in text_content.split("\n"):
                        if para.strip():
                            p = doc_file.add_paragraph(para.strip())
                            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                else:
                    p = doc_file.add_paragraph("[لا يوجد نص مكتشف في هذا القسم]")
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

                if page.equations:
                    eq_heading = doc_file.add_heading("المعادلات الرياضية (LaTeX):", level=3)
                    eq_heading.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    for eq in page.equations:
                        p_eq = doc_file.add_paragraph(eq)
                        p_eq.alignment = WD_ALIGN_PARAGRAPH.LEFT

        try:
            doc_file.save(str(path))
            logger.info(f"DOCX exported successfully: {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to export DOCX: {e}")
            raise IOError(f"Could not save DOCX file: {e}")

    @staticmethod
    def export_to_latex(
        documents: Union[DocumentResult, List[DocumentResult]],
        output_path: Path | str,
    ) -> Path:
        """Export extracted LaTeX equations to a .tex document."""
        path = Path(output_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        docs = [documents] if isinstance(documents, DocumentResult) else documents

        lines = [
            r"% LaTeX document generated by NASS (نَصّ) - Where images become words",
            r"\documentclass{article}",
            r"\usepackage{amsmath}",
            r"\usepackage{amssymb}",
            r"\begin{document}",
            "",
        ]

        for doc in docs:
            lines.append(f"% Document: {doc.file_path.name}")
            for page in doc.pages:
                if page.equations:
                    lines.append(f"% --- Page {page.page_number} ---")
                    for eq in page.equations:
                        lines.append(eq)
                        lines.append("")

        lines.append(r"\end{document}")
        content = "\n".join(lines)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"LaTeX exported successfully: {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to export LaTeX: {e}")
            raise IOError(f"Could not save LaTeX file: {e}")

    @staticmethod
    def export_to_csv(
        documents: Union[DocumentResult, List[DocumentResult]],
        output_path: Path | str,
    ) -> Path:
        """Export batch extraction summary and metrics to UTF-8 CSV with BOM for Excel."""
        import csv

        path = Path(output_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        docs = [documents] if isinstance(documents, DocumentResult) else documents

        try:
            # utf-8-sig ensures Excel on Windows displays Arabic without encoding distortion
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "اسم الملف",
                    "المسار الكامل",
                    "نوع الملف",
                    "طريقة الاستخراج",
                    "الحالة",
                    "عدد الصفحات",
                    "عدد الكلمات",
                    "عدد الحروف",
                    "متوسط الدقة (%)",
                    "مدة المعالجة (ثانية)",
                    "رسالة الخطأ (إن وجدت)",
                ])

                for doc in docs:
                    full_txt = doc.full_text
                    words = len(full_txt.split()) if full_txt else 0
                    chars = len(full_txt) if full_txt else 0
                    writer.writerow([
                        doc.file_path.name,
                        str(doc.file_path),
                        doc.file_type.value.upper(),
                        doc.method_display_name,
                        doc.status.value,
                        doc.total_pages,
                        words,
                        chars,
                        f"{doc.average_confidence:.1f}",
                        f"{getattr(doc, 'total_duration_seconds', 0.0):.2f}",
                        doc.error_message or "",
                    ])

            logger.info(f"CSV report exported successfully: {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise IOError(f"Could not save CSV file: {e}")

