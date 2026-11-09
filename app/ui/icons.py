"""
أيقونات متجهة نقية (Pure Vector QIcon) لتطبيق نَصّ (NASS).
تضمن مظهراً احترافياً وأنيقاً بدون الحاجة لملفات خارجية وتتجنب الإيموجي تماماً.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def create_colored_icon(draw_func, color_hex: str = "#FFFFFF", size: int = 24) -> QIcon:
    """رسم أيقونة بدقة عالية باللون المطلوب."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor(color_hex), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)

    draw_func(painter, size)
    painter.end()

    return QIcon(pixmap)


def _draw_home(p: QPainter, s: int):
    # شكل منزل
    path = QPainterPath()
    path.moveTo(s * 0.5, s * 0.18)
    path.lineTo(s * 0.85, s * 0.48)
    path.lineTo(s * 0.75, s * 0.48)
    path.lineTo(s * 0.75, s * 0.82)
    path.lineTo(s * 0.25, s * 0.82)
    path.lineTo(s * 0.25, s * 0.48)
    path.lineTo(s * 0.15, s * 0.48)
    path.closeSubpath()
    p.drawPath(path)


def _draw_document_ocr(p: QPainter, s: int):
    # شكل مستند مع خطوط نص
    rect = QRectF(s * 0.22, s * 0.15, s * 0.56, s * 0.70)
    p.drawRoundedRect(rect, 2, 2)
    # أسطر نصية
    p.drawLine(QPointF(s * 0.32, s * 0.35), QPointF(s * 0.68, s * 0.35))
    p.drawLine(QPointF(s * 0.32, s * 0.50), QPointF(s * 0.68, s * 0.50))
    p.drawLine(QPointF(s * 0.32, s * 0.65), QPointF(s * 0.54, s * 0.65))


def _draw_history(p: QPainter, s: int):
    # شكل ساعة / سجل
    p.drawEllipse(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64))
    p.drawLine(QPointF(s * 0.50, s * 0.50), QPointF(s * 0.50, s * 0.32))
    p.drawLine(QPointF(s * 0.50, s * 0.50), QPointF(s * 0.66, s * 0.50))


def _draw_gear(p: QPainter, s: int):
    # شكل ترس / إعدادات
    p.drawEllipse(QRectF(s * 0.32, s * 0.32, s * 0.36, s * 0.36))
    p.drawEllipse(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64))


def _draw_language(p: QPainter, s: int):
    # شكل كرة أرضية / لغة
    p.drawEllipse(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64))
    p.drawEllipse(QRectF(s * 0.34, s * 0.18, s * 0.32, s * 0.64))
    p.drawLine(QPointF(s * 0.18, s * 0.50), QPointF(s * 0.82, s * 0.50))


def _draw_about(p: QPainter, s: int):
    # علامة معلومات (i داخل دائرة)
    p.drawEllipse(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64))
    p.drawPoint(QPointF(s * 0.50, s * 0.36))
    p.drawLine(QPointF(s * 0.50, s * 0.46), QPointF(s * 0.50, s * 0.66))


def _draw_copy(p: QPainter, s: int):
    # ورقتان متطابقتان للنسخ
    p.drawRoundedRect(QRectF(s * 0.32, s * 0.32, s * 0.48, s * 0.54), 2, 2)
    p.drawPolyline([
        QPointF(s * 0.68, s * 0.22),
        QPointF(s * 0.20, s * 0.22),
        QPointF(s * 0.20, s * 0.70),
    ])


def _draw_export(p: QPainter, s: int):
    # صندوق وسهم صاعد للتصدير
    p.drawPolyline([
        QPointF(s * 0.22, s * 0.45),
        QPointF(s * 0.22, s * 0.78),
        QPointF(s * 0.78, s * 0.78),
        QPointF(s * 0.78, s * 0.45),
    ])
    p.drawLine(QPointF(s * 0.50, s * 0.22), QPointF(s * 0.50, s * 0.60))
    p.drawLine(QPointF(s * 0.34, s * 0.36), QPointF(s * 0.50, s * 0.22))
    p.drawLine(QPointF(s * 0.66, s * 0.36), QPointF(s * 0.50, s * 0.22))


def _draw_check(p: QPainter, s: int):
    # علامة صح
    p.drawPolyline([
        QPointF(s * 0.22, s * 0.52),
        QPointF(s * 0.42, s * 0.72),
        QPointF(s * 0.78, s * 0.28),
    ])


def _draw_refresh(p: QPainter, s: int):
    # سهم دائري للتحديث
    p.drawArc(QRectF(s * 0.20, s * 0.20, s * 0.60, s * 0.60), 45 * 16, 270 * 16)
    p.drawLine(QPointF(s * 0.75, s * 0.25), QPointF(s * 0.85, s * 0.38))
    p.drawLine(QPointF(s * 0.75, s * 0.50), QPointF(s * 0.85, s * 0.38))


class AppIcons:
    """واجهة موحدة لجميع أيقونات التطبيق."""

    @staticmethod
    def home(color: str = "#FFFFFF") -> QIcon:
        return create_colored_icon(_draw_home, color)

    @staticmethod
    def ocr(color: str = "#FFFFFF") -> QIcon:
        return create_colored_icon(_draw_document_ocr, color)

    @staticmethod
    def history(color: str = "#FFFFFF") -> QIcon:
        return create_colored_icon(_draw_history, color)

    @staticmethod
    def ocr_settings(color: str = "#FFFFFF") -> QIcon:
        return create_colored_icon(_draw_language, color)

    @staticmethod
    def app_settings(color: str = "#FFFFFF") -> QIcon:
        return create_colored_icon(_draw_gear, color)

    @staticmethod
    def about(color: str = "#FFFFFF") -> QIcon:
        return create_colored_icon(_draw_about, color)

    @staticmethod
    def copy(color: str = "#1E293B") -> QIcon:
        return create_colored_icon(_draw_copy, color)

    @staticmethod
    def export(color: str = "#1E293B") -> QIcon:
        return create_colored_icon(_draw_export, color)

    @staticmethod
    def check(color: str = "#10B981") -> QIcon:
        return create_colored_icon(_draw_check, color)

    @staticmethod
    def refresh(color: str = "#1E293B") -> QIcon:
        return create_colored_icon(_draw_refresh, color)
