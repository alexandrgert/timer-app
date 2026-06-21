from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

_ICON_CACHE: dict[str, QIcon] = {}


def line_icon(key: str, draw, color: str = "#828B9A") -> QIcon:
    """Build (and cache) a crisp line-art QIcon drawn by ``draw(painter)``."""
    cache_key = f"{key}:{color}"
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    scale = 4
    pixmap = QPixmap(16 * scale, 16 * scale)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(scale, scale)
    pen = QPen(QColor(color))
    pen.setWidthF(1.3)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    draw(painter)
    painter.end()

    icon = QIcon(pixmap)
    _ICON_CACHE[cache_key] = icon
    return icon


def draw_trash(painter) -> None:
    painter.drawLine(QPointF(3, 4.6), QPointF(13, 4.6))
    handle = QPainterPath()
    handle.moveTo(6, 4.6)
    handle.lineTo(6, 3.3)
    handle.quadTo(6, 2.7, 6.6, 2.7)
    handle.lineTo(9.4, 2.7)
    handle.quadTo(10, 2.7, 10, 3.3)
    handle.lineTo(10, 4.6)
    painter.drawPath(handle)
    body = QPainterPath()
    body.moveTo(4.4, 4.6)
    body.lineTo(5.1, 13.2)
    body.lineTo(10.9, 13.2)
    body.lineTo(11.6, 4.6)
    painter.drawPath(body)


def draw_stopwatch(painter) -> None:
    painter.drawEllipse(QRectF(3, 4.7, 10, 10))
    painter.drawLine(QPointF(8, 9.7), QPointF(8, 6.8))
    painter.drawLine(QPointF(8, 9.7), QPointF(10.1, 10.5))
    painter.drawLine(QPointF(8, 2.3), QPointF(8, 3.9))
    painter.drawLine(QPointF(6, 2.3), QPointF(10, 2.3))
