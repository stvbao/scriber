from __future__ import annotations

from importlib.resources import as_file, files

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap


def create_app_icon() -> QIcon:
    packaged_icon = _load_packaged_icon()
    if not packaged_icon.isNull():
        return packaged_icon

    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256, 512):
        icon.addPixmap(_render_icon(size))
    return icon


def _load_packaged_icon() -> QIcon:
    try:
        resource = files("scriber.gui.assets").joinpath("icon.png")
        with as_file(resource) as icon_path:
            icon = QIcon(str(icon_path))
            if not icon.isNull():
                return icon
    except Exception:
        pass
    return QIcon()


def _render_icon(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pad = size * 0.08
    rect = QRectF(pad, pad, size - (pad * 2), size - (pad * 2))
    radius = size * 0.22

    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, QColor("#33c0b3"))
    gradient.setColorAt(1.0, QColor("#0f3d56"))

    painter.setBrush(gradient)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(rect, radius, radius)

    border_pen = QPen(QColor(255, 255, 255, 78), max(1, round(size * 0.008)))
    painter.setPen(border_pen)
    inner_pad = size * 0.16
    inner_rect = QRectF(
        inner_pad,
        inner_pad,
        size - (inner_pad * 2),
        size - (inner_pad * 2),
    )
    painter.drawRoundedRect(inner_rect, size * 0.23, size * 0.23)

    pen = QPen(QColor("#f8fbfc"), max(2, round(size * 0.024)))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)

    points = [
        QPointF(size * 0.27, size * 0.36),
        QPointF(size * 0.36, size * 0.33),
        QPointF(size * 0.45, size * 0.40),
        QPointF(size * 0.54, size * 0.28),
        QPointF(size * 0.62, size * 0.36),
    ]
    for start, end in zip(points, points[1:]):
        painter.drawLine(start, end)

    cursor_pen = QPen(QColor("#f8fbfc"), max(2, round(size * 0.03)))
    cursor_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(cursor_pen)
    painter.drawLine(
        QPointF(size * 0.66, size * 0.28),
        QPointF(size * 0.66, size * 0.42),
    )

    painter.end()
    return pixmap
