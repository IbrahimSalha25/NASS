"""
خدمة تصدير النصوص المستخرجة إلى صيغ TXT و DOCX مع دعم ترميز UTF-8 وتنسيق RTL.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Union

from app.core.models import DocumentResult
from app.utils.logger import logger


class ExportService:
    """خدمة تصدير وحفظ نتائج استخراج النصوص."""

    @staticmethod
    def export_to_txt(
        documents: Union[DocumentResult, List[DocumentResult]],
        output_path: Path | str,
        include_headers: bool = True,
    ) -> Path:
        """
        تصدير النصوص إلى ملف نصي (TXT) بترميز UTF-8 النقي.
        """
        path = Path(output_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        docs = [documents] if isinstance(documents, DocumentResult) else documents

        lines: List[str] = []
        for doc in docs:
            if include_headers:
                lines.append("=" * 60)
                lines.append(f"الملف: {doc.file_path.name}")
                lines.append(f"عدد الصفحات: {doc.total_pages}")
                if doc.average_confidence > 0:
                    lines.append(f"متوسط الثقة التقريبية: {doc.average_confidence:.1f}%")
                lines.append("=" * 60)
                lines.append("")

            for page in doc.pages:
                if include_headers and doc.total_pages > 1:
                    lines.append(f"--- [الصفحة {page.page_number}] ---")
                    lines.append("")

                if page.text.strip():
                    lines.append(page.text)
                elif page.error_message:
                    lines.append(f"[خطأ في استخراج الصفحة: {page.error_message}]")
                else:
                    lines.append("[لا يوجد نص مكتشف في هذه الصفحة]")

                lines.append("")

            lines.append("")

        content = "\n".join(lines).strip()

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"تم تصدير ملف TXT بنجاح إلى: {path}")
            return path
        except Exception as e:
            logger.error(f"فشل تصدير ملف TXT إلى {path}: {e}")
            raise IOError(f"تعذر حفظ ملف النص: {e}")

    @staticmethod
    def export_to_docx(
        documents: Union[DocumentResult, List[DocumentResult]],
        output_path: Path | str,
    ) -> Path:
        """
        تصدير النتائج إلى مستند Word (DOCX) مع ضبط اتجاه الفقرات العربية إلى اليمين (RTL).
        """
        import docx
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        path = Path(output_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        docs = [documents] if isinstance(documents, DocumentResult) else documents
        doc_file = docx.Document()

        for doc_idx, doc in enumerate(docs):
            if doc_idx > 0:
                doc_file.add_page_break()

            # عنوان المستند
            heading = doc_file.add_heading(f"نَصّ — {doc.file_path.name}", level=1)
            heading.alignment = WD_ALIGN_PARAGRAPH.RIGHT

            # ملخص المعلومات
            info_p = doc_file.add_paragraph()
            info_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            info_run = info_p.add_run(
                f"الصفحات: {doc.total_pages} | متوسط الثقة: {doc.average_confidence:.1f}%"
            )
            info_run.font.italic = True

            doc_file.add_paragraph("-" * 40).alignment = WD_ALIGN_PARAGRAPH.RIGHT

            for page in doc.pages:
                if doc.total_pages > 1:
                    page_head = doc_file.add_heading(f"الصفحة {page.page_number}", level=2)
                    page_head.alignment = WD_ALIGN_PARAGRAPH.RIGHT

                text_content = page.text.strip()
                if text_content:
                    for para in text_content.split("\n"):
                        if para.strip():
                            p = doc_file.add_paragraph(para.strip())
                            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                else:
                    p = doc_file.add_paragraph("[لا يوجد نص مكتشف في هذه الصفحة]")
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        try:
            doc_file.save(str(path))
            logger.info(f"تم تصدير مستند DOCX بنجاح إلى: {path}")
            return path
        except Exception as e:
            logger.error(f"فشل تصدير مستند DOCX إلى {path}: {e}")
            raise IOError(f"تعذر حفظ مستند DOCX: {e}")
