# -*- coding: utf-8 -*-
# ui/widgets/lotto_ball_widget.py
import sys
import os
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("LottoBallWidget")

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QPainter, QColor, QBrush, QRadialGradient, QLinearGradient, QPen


class LottoBallWidget(QWidget):
    """
    High-resolution 3D glossy lotto ball widget with enhanced radial gradients,
    dual specular highlights, and official color-band themes.
    """
    def __init__(self, number: int = None, is_bonus: bool = False, parent=None):
        super().__init__(parent)
        self.number = number
        self.is_bonus = is_bonus
        self.setFixedSize(36, 36)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_num = QLabel("" if self.number is None else str(self.number), self)
        self.lbl_num.setAlignment(Qt.AlignCenter)
        self.lbl_num.setStyleSheet("background: transparent; border: none;")
        
        self.layout.addWidget(self.lbl_num)
        self.update_style()
        _log.debug("LottoBallWidget initialized with high-def 3D profile.")

    def set_number(self, number: int, is_bonus: bool = False):
        """Sets the ball number and updates its visual appearance."""
        self.number = number
        self.is_bonus = is_bonus
        self.lbl_num.setText(str(number) if number is not None else "")
        self.update_style()
        self.update()

    def clear(self):
        """Clears the ball state and forces a clean repaint to remove residuals."""
        self.number = None
        self.is_bonus = False
        self.lbl_num.setText("")
        self.update()

    def update_style(self):
        """Updates text color and font matching the sphere bounds."""
        if self.number is None:
            return

        text_color = "#1e272e" if 1 <= self.number <= 10 else "#ffffff"
        self.lbl_num.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                border: none;
                color: {text_color};
                font-weight: bold;
                font-size: 11pt;
                font-family: 'Segoe UI';
            }}
        """)

    @staticmethod
    def get_ball_theme_colors(num: int) -> tuple:
        """Returns high-definition inner highlight, mid-tone, and deep shadow colors for official lotto bands."""
        if 1 <= num <= 10:
            return "#fff9c4", "#f1c40f", "#b7950b"  # Yellow band (1~10)
        elif 11 <= num <= 20:
            return "#d4e6f1", "#2980b9", "#1b4f72"  # Blue band (11~20)
        elif 21 <= num <= 30:
            return "#fadbd8", "#e74c3c", "#922b21"  # Red band (21~30)
        elif 31 <= num <= 40:
            return "#ebedef", "#7f8c8d", "#2c3e50"  # Gray band (31~40)
        else:
            return "#d4efdf", "#27ae60", "#145a32"  # Green band (41~45)

    @staticmethod
    def draw_ball(painter: QPainter, x: float, y: float, number: int, radius: float = 15.0, is_bonus: bool = False, show_label: bool = True):
        """Static utility method to draw a high-def glossy 3D lotto ball on any QPainter surface."""
        if number is None:
            return

        c_inner, c_mid, c_outer = LottoBallWidget.get_ball_theme_colors(number)

        if is_bonus:
            halo_pen = QPen(QColor("#f39c12"), 3.5, Qt.SolidLine)
            painter.setPen(halo_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QRectF(x - radius - 3.5, y - radius - 3.5, (radius + 3.5) * 2, (radius + 3.5) * 2))

        # 1. Base 3D Radial Gradient (Simulating spherical volume)
        gradient = QRadialGradient(x - radius * 0.32, y - radius * 0.32, radius * 1.25)
        gradient.setColorAt(0.0, QColor(c_inner))
        gradient.setColorAt(0.5, QColor(c_mid))
        gradient.setColorAt(0.92, QColor(c_outer))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 180))

        border_color = QColor("#d35400" if is_bonus else "#1e272e")
        border_width = 2.0 if is_bonus else 0.8

        painter.setPen(QPen(border_color, border_width))
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QRectF(x - radius, y - radius, radius * 2, radius * 2))

        # 2. Primary Glossy Specular Highlight (Top-Left soft reflection)
        highlight_gradient = QRadialGradient(x - radius * 0.38, y - radius * 0.38, radius * 0.65)
        highlight_gradient.setColorAt(0.0, QColor(255, 255, 255, 230))
        highlight_gradient.setColorAt(0.5, QColor(255, 255, 255, 120))
        highlight_gradient.setColorAt(1.0, QColor(255, 255, 255, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(highlight_gradient))
        painter.drawEllipse(QRectF(x - radius * 0.78, y - radius * 0.78, radius * 0.95, radius * 0.95))

        # 3. Secondary Rim Reflection (Bottom ambient bounce light for rich depth)
        rim_gradient = QLinearGradient(x, y + radius * 0.2, x, y + radius)
        rim_gradient.setColorAt(0.0, QColor(255, 255, 255, 0))
        rim_gradient.setColorAt(1.0, QColor(255, 255, 255, 50))
        
        painter.setBrush(QBrush(rim_gradient))
        painter.drawEllipse(QRectF(x - radius * 0.9, y - radius * 0.9, radius * 1.8, radius * 1.8))

        if show_label:
            text_color = "#1e272e" if 1 <= number <= 10 else "#ffffff"
            painter.setPen(QPen(QColor(text_color)))
            font_size = max(6, int(radius * 0.62))
            font = QFont("Segoe UI", font_size, QFont.Bold)
            painter.setFont(font)
            
            # Subtle text drop shadow for enhanced readability
            painter.setPen(QPen(QColor(0, 0, 0, 140)))
            painter.drawText(QRectF(x - radius + 1, y - radius + 1.2, radius * 2, radius * 2), Qt.AlignCenter, str(number))
            
            painter.setPen(QPen(QColor(text_color)))
            painter.drawText(QRectF(x - radius, y - radius, radius * 2, radius * 2), Qt.AlignCenter, str(number))

    def paintEvent(self, event):
        """Paints a high-resolution 3D glossy sphere perfectly sized to the widget boundaries."""
        if self.number is None:
            painter = QPainter(self)
            painter.eraseRect(self.rect())
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        width = self.width()
        height = self.height()
        
        radius = (min(width, height) / 2.0) - 1.0
        cx, cy = width / 2.0, height / 2.0

        self.draw_ball(painter, cx, cy, self.number, radius=radius, is_bonus=self.is_bonus, show_label=True)