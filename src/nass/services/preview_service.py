"""
Unified Document Preview Service for NASS.
Renders high-quality preview representations of DOCX, PPTX, XLSX, PDF, and Images as QPixmap / PIL Images.
Pure Python + PySide6 / PyMuPDF implementation requiring no external Office installations.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QLinearGradient, QPainter, QPen, QPixmap

from nass.core.models import FileType
from nass.processors.pdf_processor import PdfProcessor
from nass.utils.file_utils import FileUtils
from nass.utils.logger import logger


class DocumentPreviewService:
    """
    Renders visual previews for documents and manages page navigation counts.
    """

    @classmethod
    def get_document_page_count(cls, file_path: Path) -> int:
        """Inspect file and return total viewable pages, slides, sheets, or 1 for images."""
        if not file_path.exists():
            return 1

        file_type = FileUtils.detect_file_type(file_path)
        try:
            if file_type == FileType.PDF:
                cnt, is_enc, _ = PdfProcessor.get_document_info(file_path)
                return max(1, cnt)
            elif file_type == FileType.POWERPOINT:
                import pptx
                prs = pptx.Presentation(str(file_path))
                return max(1, len(prs.slides))
            elif file_type == FileType.EXCEL:
                import openpyxl
                wb = openpyxl.load_workbook(str(file_path), read_only=True)
                count = len(wb.sheetnames)
                wb.close()
                return max(1, count)
            elif file_type == FileType.WORD:
                import docx
                doc = docx.Document(str(file_path))
                # Count sections or paragraph volume to estimate pages gracefully
                # Word docs don't have strict page divisions in XML, so we segment by headings/breaks or volume
                total_paras = len(doc.paragraphs)
                # Count explicit page breaks
                breaks = 0
                for p in doc.paragraphs:
                    if "w:br" in p._p.xml and 'type="page"' in p._p.xml:
                        breaks += 1
                estimated = max(1, breaks + 1)
                # If large document without explicit breaks, segment every 15 paragraphs
                if breaks == 0 and total_paras > 15:
                    estimated = max(1, (total_paras + 14) // 15)
                return estimated
            elif file_type == FileType.IMAGE:
                return 1
            else:
                return 1
        except Exception as e:
            logger.warning(f"Error getting page count for {file_path.name}: {e}")
            return 1

    @classmethod
    def render_page_preview(
        cls,
        file_path: Path,
        page_num: int = 1,
        target_width: int = 400,
    ) -> QPixmap:
        """
        Generate a styled, responsive QPixmap preview for a given page/slide/sheet.
        """
        if not file_path.exists():
            return cls._render_error_card("الملف غير موجود", target_width)

        file_type = FileUtils.detect_file_type(file_path)
        try:
            if file_type == FileType.IMAGE:
                pix = QPixmap(str(file_path))
                if not pix.isNull():
                    return pix.scaledToWidth(target_width, Qt.SmoothTransformation)
                return cls._render_error_card("تعذر تحميل الصورة", target_width)

            elif file_type == FileType.PDF:
                import fitz
                doc = fitz.open(str(file_path))
                if 0 <= page_num - 1 < len(doc):
                    page = doc[page_num - 1]
                    pil_img = PdfProcessor.render_page_to_image(page, dpi=130)
                    doc.close()
                    return cls._pil_to_pixmap(pil_img, target_width)
                doc.close()
                return cls._render_error_card("الصفحة غير متوفرة", target_width)

            elif file_type == FileType.POWERPOINT:
                return cls._render_pptx_slide_preview(file_path, page_num, target_width)

            elif file_type == FileType.WORD:
                return cls._render_docx_page_preview(file_path, page_num, target_width)

            elif file_type == FileType.EXCEL:
                return cls._render_excel_sheet_preview(file_path, page_num, target_width)

            else:
                return cls._render_text_preview_card(file_path, page_num, target_width)

        except Exception as e:
            logger.error(f"Failed to render preview for {file_path.name} (page {page_num}): {e}")
            return cls._render_error_card(f"خطأ في المعاينة: {e}", target_width)

    # -------------------------------------------------------------------------
    # PowerPoint Slide Visual Rendering
    # -------------------------------------------------------------------------
    @classmethod
    def _render_pptx_slide_preview(cls, file_path: Path, slide_num: int, target_width: int) -> QPixmap:
        import pptx
        prs = pptx.Presentation(str(file_path))
        if not (1 <= slide_num <= len(prs.slides)):
            return cls._render_error_card("الشريحة غير موجودة", target_width)

        slide = prs.slides[slide_num - 1]

        # Standard slide aspect ratio 16:9 or 4:3
        prs_w = prs.slide_width or 9144000
        prs_h = prs.slide_height or 5143500
        aspect = prs_h / prs_w if prs_w > 0 else 0.5625
        target_height = int(target_width * aspect)

        img = QImage(target_width, target_height, QImage.Format_ARGB32)
        img.fill(QColor("#FFFFFF"))

        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw subtle border & header bar
        painter.setPen(QPen(QColor("#E2E8F0"), 1))
        painter.drawRect(0, 0, target_width - 1, target_height - 1)

        # Background header
        painter.fillRect(0, 0, target_width, 4, QColor("#D97706"))

        # Inspect slide shapes
        slide_title = ""
        body_lines: List[str] = []
        images_found: List[Tuple[bytes, str]] = []

        for shape in slide.shapes:
            if shape.has_text_frame:
                txt = shape.text_frame.text.strip()
                if not txt:
                    continue
                if shape == slide.shapes.title or not slide_title:
                    slide_title = txt.splitlines()[0]
                else:
                    body_lines.extend(txt.splitlines()[:5])
            if shape.shape_type == pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE:
                try:
                    images_found.append((shape.image.blob, shape.image.ext))
                except Exception:
                    pass

        # Draw Title
        y = 35
        painter.setPen(QColor("#1E293B"))
        title_font = QFont("Segoe UI", 13, QFont.Bold)
        painter.setFont(title_font)
        title_rect = QRect(20, y, target_width - 40, 45)
        display_title = slide_title if slide_title else f"شريحة عرض #{slide_num}"
        painter.drawText(title_rect, Qt.AlignLeft | Qt.TextWordWrap, display_title)
        y += 50

        # Draw body lines
        painter.setPen(QColor("#475569"))
        body_font = QFont("Segoe UI", 10)
        painter.setFont(body_font)
        for line in body_lines[:4]:
            if y + 25 > target_height - 60:
                break
            line_rect = QRect(25, y, target_width - 50, 22)
            painter.drawText(line_rect, Qt.AlignLeft | Qt.TextSingleLine, f"• {line}")
            y += 24

        # Draw embedded image thumbnails inside slide preview if available
        if images_found:
            y_img = max(y + 10, target_height - 85)
            x_img = 25
            for img_blob, _ in images_found[:3]:
                try:
                    sub_pix = QPixmap()
                    sub_pix.loadFromData(img_blob)
                    if not sub_pix.isNull():
                        thumb = sub_pix.scaled(70, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        painter.drawPixmap(x_img, y_img, thumb)
                        painter.setPen(QPen(QColor("#CBD5E1"), 1))
                        painter.drawRect(x_img, y_img, thumb.width(), thumb.height())
                        x_img += thumb.width() + 10
                except Exception:
                    pass

        # Slide Number Badge in lower corner
        badge_rect = QRect(target_width - 65, target_height - 25, 50, 18)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#F1F5F9"))
        painter.drawRoundedRect(badge_rect, 3, 3)
        painter.setPen(QColor("#64748B"))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.drawText(badge_rect, Qt.AlignCenter, f"{slide_num}/{len(prs.slides)}")

        painter.end()
        return QPixmap.fromImage(img)

    # -------------------------------------------------------------------------
    # Word (DOCX) Page Visual Rendering
    # -------------------------------------------------------------------------
    @classmethod
    def _render_docx_page_preview(cls, file_path: Path, page_num: int, target_width: int) -> QPixmap:
        import docx
        doc = docx.Document(str(file_path))
        target_height = int(target_width * 1.35)  # A4 proportion

        img = QImage(target_width, target_height, QImage.Format_ARGB32)
        img.fill(QColor("#FFFFFF"))

        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)

        # Border
        painter.setPen(QPen(QColor("#E2E8F0"), 1))
        painter.drawRect(0, 0, target_width - 1, target_height - 1)

        # Word blue header line
        painter.fillRect(0, 0, target_width, 4, QColor("#2563EB"))

        # Slice paragraphs for this estimated page
        paras_per_page = 12
        start_idx = (page_num - 1) * paras_per_page
        end_idx = start_idx + paras_per_page
        page_paras = doc.paragraphs[start_idx:end_idx]

        y = 30
        painter.setPen(QColor("#1E293B"))
        painter.setFont(QFont("Segoe UI", 12, QFont.Bold))

        # Check for first heading or title
        first_title = ""
        for p in page_paras:
            if p.style and "heading" in p.style.name.lower():
                first_title = p.text.strip()
                break

        if first_title:
            t_rect = QRect(25, y, target_width - 50, 40)
            painter.drawText(t_rect, Qt.AlignLeft | Qt.TextWordWrap, first_title)
            y += 45

        # Render regular paragraphs
        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(QColor("#334155"))
        for p in page_paras:
            txt = p.text.strip()
            if not txt or txt == first_title:
                continue
            if y + 30 > target_height - 70:
                break
            p_rect = QRect(25, y, target_width - 50, 36)
            painter.drawText(p_rect, Qt.AlignLeft | Qt.TextWordWrap, txt)
            y += 38

        # Draw image thumbnails if images exist in relationships
        doc_images = []
        for rel in doc.part.rels.values():
            if "image" in rel.reltype:
                try:
                    doc_images.append(rel.target_part.blob)
                except Exception:
                    pass

        if doc_images:
            y_img = target_height - 90
            x_img = 25
            for img_blob in doc_images[:3]:
                try:
                    sub_pix = QPixmap()
                    sub_pix.loadFromData(img_blob)
                    if not sub_pix.isNull():
                        thumb = sub_pix.scaled(65, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        painter.drawPixmap(x_img, y_img, thumb)
                        painter.setPen(QPen(QColor("#CBD5E1"), 1))
                        painter.drawRect(x_img, y_img, thumb.width(), thumb.height())
                        x_img += thumb.width() + 10
                except Exception:
                    pass

        # Footer page badge
        badge_rect = QRect(target_width // 2 - 30, target_height - 25, 60, 18)
        painter.setPen(QColor("#94A3B8"))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(badge_rect, Qt.AlignCenter, f"- {page_num} -")

        painter.end()
        return QPixmap.fromImage(img)

    # -------------------------------------------------------------------------
    # Excel Sheet Grid Visual Rendering
    # -------------------------------------------------------------------------
    @classmethod
    def _render_excel_sheet_preview(cls, file_path: Path, sheet_index: int, target_width: int) -> QPixmap:
        import openpyxl
        wb = openpyxl.load_workbook(str(file_path), data_only=True)
        sheet_names = wb.sheetnames
        if not (1 <= sheet_index <= len(sheet_names)):
            wb.close()
            return cls._render_error_card("ورقة العمل غير متوفرة", target_width)

        sheet_name = sheet_names[sheet_index - 1]
        ws = wb[sheet_name]

        target_height = int(target_width * 0.75)
        img = QImage(target_width, target_height, QImage.Format_ARGB32)
        img.fill(QColor("#FFFFFF"))

        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)

        # Border & Excel green top header
        painter.setPen(QPen(QColor("#E2E8F0"), 1))
        painter.drawRect(0, 0, target_width - 1, target_height - 1)
        painter.fillRect(0, 0, target_width, 4, QColor("#16A34A"))

        # Sheet Tab Header
        tab_rect = QRect(15, 12, target_width - 30, 26)
        painter.fillRect(tab_rect, QColor("#F1F5F9"))
        painter.setPen(QColor("#0F172A"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(tab_rect.adjusted(10, 0, -10, 0), Qt.AlignVCenter | Qt.AlignLeft, f"ورقة العمل: {sheet_name}")

        # Draw Grid Table Header & Rows
        start_y = 48
        cols = min(6, ws.max_column or 1)
        rows = min(12, ws.max_row or 1)
        col_w = (target_width - 30) // cols
        row_h = 22

        # Header Cells
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        for c in range(cols):
            c_rect = QRect(15 + c * col_w, start_y, col_w, row_h)
            painter.fillRect(c_rect, QColor("#E2E8F0"))
            painter.setPen(QColor("#CBD5E1"))
            painter.drawRect(c_rect)
            painter.setPen(QColor("#475569"))
            col_letter = chr(65 + c)
            painter.drawText(c_rect, Qt.AlignCenter, col_letter)

        # Data Rows
        painter.setFont(QFont("Segoe UI", 8))
        for r_idx in range(1, rows + 1):
            curr_y = start_y + r_idx * row_h
            if curr_y + row_h > target_height - 40:
                break
            for c_idx in range(1, cols + 1):
                cell_rect = QRect(15 + (c_idx - 1) * col_w, curr_y, col_w, row_h)
                painter.setPen(QColor("#E2E8F0"))
                painter.drawRect(cell_rect)

                try:
                    val = ws.cell(row=r_idx, column=c_idx).value
                    val_str = str(val).strip() if val is not None else ""
                except Exception:
                    val_str = ""

                if val_str:
                    painter.setPen(QColor("#1E293B"))
                    painter.drawText(cell_rect.adjusted(4, 0, -4, 0), Qt.AlignVCenter | Qt.AlignLeft, val_str[:12])

        # Check for sheet images
        sheet_images = getattr(ws, "_images", [])
        if sheet_images:
            y_img = target_height - 60
            x_img = 20
            for im in sheet_images[:2]:
                try:
                    data = im._data()
                    sub_pix = QPixmap()
                    sub_pix.loadFromData(data)
                    if not sub_pix.isNull():
                        thumb = sub_pix.scaled(60, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        painter.drawPixmap(x_img, y_img, thumb)
                        painter.setPen(QPen(QColor("#16A34A"), 1))
                        painter.drawRect(x_img, y_img, thumb.width(), thumb.height())
                        x_img += thumb.width() + 10
                except Exception:
                    pass

        # Sheet count badge
        badge_rect = QRect(target_width - 85, target_height - 24, 75, 18)
        painter.setPen(QColor("#64748B"))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(badge_rect, Qt.AlignCenter, f"{sheet_index}/{len(sheet_names)}")

        painter.end()
        wb.close()
        return QPixmap.fromImage(img)

    # -------------------------------------------------------------------------
    # Helper utilities
    # -------------------------------------------------------------------------
    @classmethod
    def _pil_to_pixmap(cls, pil_img: Image.Image, target_width: int) -> QPixmap:
        rgb_img = pil_img.convert("RGB")
        buf = io.BytesIO()
        rgb_img.save(buf, format="PNG")
        pix = QPixmap()
        pix.loadFromData(buf.getvalue())
        if target_width > 0 and not pix.isNull():
            return pix.scaledToWidth(target_width, Qt.SmoothTransformation)
        return pix

    @classmethod
    def _render_error_card(cls, message: str, target_width: int) -> QPixmap:
        h = int(target_width * 0.75)
        img = QImage(target_width, h, QImage.Format_ARGB32)
        img.fill(QColor("#F8FAFC"))
        painter = QPainter(img)
        painter.setPen(QColor("#94A3B8"))
        painter.drawRect(0, 0, target_width - 1, h - 1)
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(QRect(20, 20, target_width - 40, h - 40), Qt.AlignCenter | Qt.TextWordWrap, message)
        painter.end()
        return QPixmap.fromImage(img)

    @classmethod
    def _render_text_preview_card(cls, file_path: Path, page_num: int, target_width: int) -> QPixmap:
        h = int(target_width * 0.8)
        img = QImage(target_width, h, QImage.Format_ARGB32)
        img.fill(QColor("#FFFFFF"))
        painter = QPainter(img)
        painter.setPen(QPen(QColor("#E2E8F0"), 1))
        painter.drawRect(0, 0, target_width - 1, h - 1)
        painter.fillRect(0, 0, target_width, 4, QColor("#64748B"))

        painter.setPen(QColor("#1E293B"))
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(20, 30, f"ملف: {file_path.name}")

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            sample = "\n".join(content.splitlines()[:15])
        except Exception:
            sample = "معاينة الملف النصي..."

        painter.setPen(QColor("#475569"))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(QRect(20, 50, target_width - 40, h - 70), Qt.AlignLeft | Qt.TextWordWrap, sample)
        painter.end()
        return QPixmap.fromImage(img)
