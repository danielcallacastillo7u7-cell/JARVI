"""Procedural ignition effects drawn directly by the existing JARVIS HUD."""
import math
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPen, QRadialGradient, QBrush

DURATION = 7.6

def ramp(t, start, end):
    x = max(0.0, min(1.0, (t - start) / (end - start)))
    return x * x * (3.0 - 2.0 * x)

def layer(t, start, end):
    return 1.0 if t is None else ramp(t, start, end)

def scale(t):
    return 1.0 if t is None else 0.03 + 0.97 * ramp(t, 0.3, 4.8)

def energy(p, cx, cy, size, t, accent):
    """Inward sparks and an ignition point use the actual HUD's center."""
    if t is None:
        return
    p.save()
    fade = 1.0 - ramp(t, 5.0, 6.2)
    p.setPen(Qt.PenStyle.NoPen)
    for i in range(44):
        phase = (i * 0.618034 + t * 0.31) % 1.0
        radius = size * (0.025 + 0.57 * (1.0 - phase) ** 1.7)
        angle = i * 2.399963 + t * 0.24
        color = QColor(accent)
        color.setAlpha(int(170 * math.sin(phase * math.pi) * fade * ramp(t, 0, 0.8)))
        p.setBrush(color)
        p.drawEllipse(QPointF(cx + math.cos(angle) * radius,
                             cy + math.sin(angle) * radius), 1.2, 1.2)
    glow = (0.4 + 0.15 * math.sin(t * 5)) * fade * ramp(t, 0, 0.7)
    _glow(p, cx, cy, size * 0.13, glow, accent)
    # Fine segmented tracks assemble between the HUD's existing large arcs.
    track_alpha = ramp(t, 1.1, 3.4) * (1.0 - ramp(t, 6.1, 7.6))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for track in range(3):
        radius = size * (0.19 + track * 0.066) * scale(t)
        color = QColor(accent)
        color.setAlpha(int(175 * track_alpha))
        p.setPen(QPen(color, 1.1 if track != 1 else 2.0))
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        for segment in range(48):
            angle = segment * 7.5 + (1 if track % 2 == 0 else -1) * t * 35
            p.drawArc(rect, int(angle * 16), int(3.5 * 16))
    p.restore()

def _glow(p, cx, cy, radius, intensity, accent):
    g = QRadialGradient(QPointF(cx, cy), max(1.0, radius))
    g.setColorAt(0, QColor(215, 250, 255, int(255 * intensity)))
    color = QColor(accent)
    color.setAlpha(int(180 * intensity))
    g.setColorAt(0.22, color)
    color.setAlpha(0)
    g.setColorAt(1, color)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(g))
    p.drawEllipse(QPointF(cx, cy), radius, radius)

def ignition(p, cx, cy, size, t, accent):
    """Brief bloom and expanding shockwave settle into the live reactor."""
    if t is None:
        return
    pulse = ramp(t, 5.1, 5.7) * (1.0 - ramp(t, 5.7, 7.2))
    if pulse <= 0:
        return
    p.save()
    _glow(p, cx, cy, size * 0.62, pulse * 0.86, accent)
    color = QColor(accent)
    color.setAlpha(int(210 * pulse))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(color, 1.5))
    radius = size * (0.1 + 0.65 * ramp(t, 5.55, 7.2))
    p.drawEllipse(QPointF(cx, cy), radius, radius)
    # Horizontal light streak, matching the reference's final ignition.
    for i in range(8, 0, -1):
        color.setAlpha(int(18 * pulse * (1 - i / 10)))
        p.setPen(QPen(color, i * 1.6))
        p.drawLine(QPointF(cx - size * 0.6, cy), QPointF(cx + size * 0.6, cy))
    p.restore()
