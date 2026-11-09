"""
Vector icon renderer for NASS.
Generates clean, scalable QIcon graphics without external assets or emoji.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def create_colored_icon(draw_func, color_hex: str = "#FFFFFF", size: int = 24) -> QIcon:
    """Render antialiased vector icon into a QIcon."""
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
    rect = QRectF(s * 0.22, s * 0.15, s * 0.56, s * 0.70)
    p.drawRoundedRect(rect, 2, 2)
    p.drawLine(QPointF(s * 0.32, s * 0.35), QPointF(s * 0.68, s * 0.35))
    p.drawLine(QPointF(s * 0.32, s * 0.50), QPointF(s * 0.68, s * 0.50))
    p.drawLine(QPointF(s * 0.32, s * 0.65), QPointF(s * 0.54, s * 0.65))


def _draw_history(p: QPainter, s: int):
    p.drawEllipse(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64))
    p.drawLine(QPointF(s * 0.50, s * 0.50), QPointF(s * 0.50, s * 0.32))
    p.drawLine(QPointF(s * 0.50, s * 0.50), QPointF(s * 0.66, s * 0.50))


def _draw_gear(p: QPainter, s: int):
    p.drawEllipse(QRectF(s * 0.32, s * 0.32, s * 0.36, s * 0.36))
    p.drawEllipse(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64))


def _draw_language(p: QPainter, s: int):
    p.drawEllipse(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64))
    p.drawEllipse(QRectF(s * 0.34, s * 0.18, s * 0.32, s * 0.64))
    p.drawLine(QPointF(s * 0.18, s * 0.50), QPointF(s * 0.82, s * 0.50))


def _draw_about(p: QPainter, s: int):
    p.drawEllipse(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64))
    p.drawPoint(QPointF(s * 0.50, s * 0.36))
    p.drawLine(QPointF(s * 0.50, s * 0.46), QPointF(s * 0.50, s * 0.66))


def _draw_copy(p: QPainter, s: int):
    p.drawRoundedRect(QRectF(s * 0.32, s * 0.32, s * 0.48, s * 0.54), 2, 2)
    p.drawPolyline([
        QPointF(s * 0.68, s * 0.22),
        QPointF(s * 0.20, s * 0.22),
        QPointF(s * 0.20, s * 0.70),
    ])


def _draw_export(p: QPainter, s: int):
    p.drawPolyline([
        QPointF(s * 0.22, s * 0.45),
        QPointF(s * 0.22, s * 0.78),
        QPointF(s * 0.78, s * 0.78),
        QPointF(s * 0.78, s * 0.45),
    ])
    p.drawLine(QPointF(s * 0.50, s * 0.22), QPointF(s * 0.50, s * 0.60))
    p.drawLine(QPointF(s * 0.34, s * 0.36), QPointF(s * 0.50, s * 0.22))
    p.drawLine(QPointF(s * 0.66, s * 0.36), QPointF(s * 0.50, s * 0.22))


def _draw_refresh(p: QPainter, s: int):
    p.drawArc(QRectF(s * 0.20, s * 0.20, s * 0.60, s * 0.60), 45 * 16, 270 * 16)
    p.drawLine(QPointF(s * 0.75, s * 0.25), QPointF(s * 0.85, s * 0.38))
    p.drawLine(QPointF(s * 0.75, s * 0.50), QPointF(s * 0.85, s * 0.38))


def _draw_github(p: QPainter, s: int):
    # Stylized GitHub cat silhouette
    p.drawEllipse(QRectF(s * 0.22, s * 0.22, s * 0.56, s * 0.56))
    p.drawLine(QPointF(s * 0.35, s * 0.25), QPointF(s * 0.30, s * 0.15))
    p.drawLine(QPointF(s * 0.65, s * 0.25), QPointF(s * 0.70, s * 0.15))


def _draw_upload(p: QPainter, s: int):
    # Base tray
    p.drawLine(QPointF(s * 0.22, s * 0.66), QPointF(s * 0.22, s * 0.80))
    p.drawLine(QPointF(s * 0.22, s * 0.80), QPointF(s * 0.78, s * 0.80))
    p.drawLine(QPointF(s * 0.78, s * 0.80), QPointF(s * 0.78, s * 0.66))
    # Up arrow shaft
    p.drawLine(QPointF(s * 0.50, s * 0.20), QPointF(s * 0.50, s * 0.64))
    # Up arrow head
    p.drawLine(QPointF(s * 0.50, s * 0.20), QPointF(s * 0.32, s * 0.38))
    p.drawLine(QPointF(s * 0.50, s * 0.20), QPointF(s * 0.68, s * 0.38))


def _draw_folder(p: QPainter, s: int):
    # Folder tab and body
    path = QPainterPath()
    path.moveTo(s * 0.15, s * 0.32)
    path.lineTo(s * 0.40, s * 0.32)
    path.lineTo(s * 0.48, s * 0.42)
    path.lineTo(s * 0.85, s * 0.42)
    path.lineTo(s * 0.85, s * 0.78)
    path.lineTo(s * 0.15, s * 0.78)
    path.closeSubpath()
    p.drawPath(path)


def _draw_trash(p: QPainter, s: int):
    # Trash can body
    rect = QRectF(s * 0.28, s * 0.36, s * 0.44, s * 0.46)
    p.drawRoundedRect(rect, 2, 2)
    # Lid & handle
    p.drawLine(QPointF(s * 0.20, s * 0.36), QPointF(s * 0.80, s * 0.36))
    p.drawLine(QPointF(s * 0.40, s * 0.24), QPointF(s * 0.60, s * 0.24))
    p.drawLine(QPointF(s * 0.40, s * 0.24), QPointF(s * 0.40, s * 0.36))
    p.drawLine(QPointF(s * 0.60, s * 0.24), QPointF(s * 0.60, s * 0.36))
    # Vertical ribs
    p.drawLine(QPointF(s * 0.42, s * 0.46), QPointF(s * 0.42, s * 0.72))
    p.drawLine(QPointF(s * 0.58, s * 0.46), QPointF(s * 0.58, s * 0.72))


def _draw_globe(p: QPainter, s: int):
    p.drawEllipse(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64))
    p.drawLine(QPointF(s * 0.18, s * 0.50), QPointF(s * 0.82, s * 0.50))
    p.drawEllipse(QRectF(s * 0.34, s * 0.18, s * 0.32, s * 0.64))


def _draw_mail(p: QPainter, s: int):
    rect = QRectF(s * 0.18, s * 0.25, s * 0.64, s * 0.50)
    p.drawRoundedRect(rect, 2, 2)
    path = QPainterPath()
    path.moveTo(s * 0.18, s * 0.25)
    path.lineTo(s * 0.50, s * 0.52)
    path.lineTo(s * 0.82, s * 0.25)
    p.drawPath(path)


def _draw_linkedin(p: QPainter, s: int):
    rect = QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64)
    p.drawRoundedRect(rect, 3, 3)
    p.drawLine(QPointF(s * 0.36, s * 0.42), QPointF(s * 0.36, s * 0.68))
    p.drawPoint(QPointF(s * 0.36, s * 0.32))
    path = QPainterPath()
    path.moveTo(s * 0.50, s * 0.68)
    path.lineTo(s * 0.50, s * 0.46)
    path.quadTo(s * 0.50, s * 0.40, s * 0.58, s * 0.40)
    path.quadTo(s * 0.66, s * 0.40, s * 0.66, s * 0.48)
    path.lineTo(s * 0.66, s * 0.68)
    p.drawPath(path)


class AppIcons:
    """Unified icon registry for the application."""

    @staticmethod
    def home(color: str = "#FFFFFF") -> QIcon:
        return create_colored_icon(_draw_home, color)

    @staticmethod
    def folder(color: str = "#FFFFFF") -> QIcon:
        return create_colored_icon(_draw_folder, color)

    @staticmethod
    def ocr(color: str = "#FFFFFF") -> QIcon:
        return create_colored_icon(_draw_document_ocr, color)

    @staticmethod
    def upload(color: str = "#FFFFFF") -> QIcon:
        return create_colored_icon(_draw_upload, color)

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
    def refresh(color: str = "#1E293B") -> QIcon:
        return create_colored_icon(_draw_refresh, color)

    @staticmethod
    def github(color: str = "#1E293B") -> QIcon:
        return create_colored_icon(_draw_github, color)

    @staticmethod
    def trash(color: str = "#EF4444") -> QIcon:
        return create_colored_icon(_draw_trash, color)

    @staticmethod
    def linkedin(color: str = "#0A66C2") -> QIcon:
        return create_colored_icon(_draw_linkedin, color)

    @staticmethod
    def mail(color: str = "#EA4335") -> QIcon:
        return create_colored_icon(_draw_mail, color)

    @staticmethod
    def globe(color: str = "#0F172A") -> QIcon:
        return create_colored_icon(_draw_globe, color)
