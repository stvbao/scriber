from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap


def create_app_icon() -> QIcon:
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256, 512):
        icon.addPixmap(_render_icon(size))
    return icon


def _render_icon(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pad = size * 0.08
    rect = QRectF(pad, pad, size - (pad * 2), size - (pad * 2))
    radius = size * 0.22

    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, QColor("#4fc3f7"))
    gradient.setColorAt(0.48, QColor("#2b6cb0"))
    gradient.setColorAt(1.0, QColor("#16395f"))

    painter.setBrush(gradient)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(rect, radius, radius)

    pen = QPen(QColor("#f6fbff"), max(2, round(size * 0.065)))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)

    points = [
        QPointF(size * 0.22, size * 0.55),
        QPointF(size * 0.34, size * 0.42),
        QPointF(size * 0.46, size * 0.64),
        QPointF(size * 0.58, size * 0.35),
        QPointF(size * 0.72, size * 0.57),
    ]
    for start, end in zip(points, points[1:]):
        painter.drawLine(start, end)

    painter.end()
    return pixmap
