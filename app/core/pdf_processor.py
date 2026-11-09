"""
معالج ملفات PDF: فحص النصوص المضمنة وتحويل الصفحات لصور صفحة بصفحة عبر PyMuPDF.
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator, Optional, Tuple
from PIL import Image

from app.core.models import PageResult, ProcessingStatus
from app.utils.logger import logger


class PdfProcessor:
    """معالج مستندات PDF بكفاءة عالية واستهلاك ذاكرة منخفض."""

    @staticmethod
    def get_document_info(file_path: Path) -> Tuple[int, bool, bool]:
        """
        استخراج معلومات عامة عن ملف PDF:
        (عدد الصفحات، هل هو محمي بكلمة مرور، هل يحتوي على طبقة نصية)
        """
        import fitz  # PyMuPDF

        if not file_path.exists():
            raise FileNotFoundError(f"ملف PDF غير موجود: {file_path}")

        try:
            doc = fitz.open(str(file_path))
        except Exception as e:
            raise ValueError(f"تعذر فتح ملف PDF (قد يكون تالفاً): {e}")

        try:
            if doc.is_encrypted:
                return 0, True, False

            page_count = len(doc)
            if page_count == 0:
                return 0, False, False

            # فحص عينة من الصفحات (حتى أول 3 صفحات) لمعرفة إن كان يحتوي نصاً مضمناً
            has_text = False
            sample_count = min(3, page_count)
            for i in range(sample_count):
                try:
                    page = doc[i]
                    text = page.get_text().strip()
                    # إذا كانت الصفحة تحتوي على أكثر من 30 حرفاً حقيقياً
                    if len(text) > 30:
                        has_text = True
                        break
                except Exception:
                    pass

            return page_count, False, has_text
        finally:
            doc.close()

    @staticmethod
    def extract_embedded_text_page(page) -> str:
        """استخراج النص الأصلي المضمن في صفحة PDF بدون الحاجة إلى OCR."""
        text = page.get_text("text")
        return text.strip()

    @staticmethod
    def render_page_to_image(page, dpi: int = 300) -> Image.Image:
        """
        تحويل صفحة PDF إلى كائن PIL Image بدقة (DPI) محددة.
        يتم تحرير الموارد فوراً لتجنب تراكم الذاكرة.
        """
        import fitz

        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        # alpha=False لضمان خلفية بيضاء نقية
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        try:
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            return img
        finally:
            pix = None  # تحرير الذاكرة على الفور
