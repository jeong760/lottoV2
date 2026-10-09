# ui/widgets/donut_metric_widget.py
import sys
import os
import logging
import math

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("DonutMetricWidget")

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QSizePolicy
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QColor, QPainter, QPen


class DonutChartPainter(QWidget):
    """
    Custom widget that paints an elegant, perfectly proportional 1:1 square donut chart.
    Supports both raw percentage mode and dual-value ratio mode (v1:v2) with exact center text alignment.
    """
    def __init__(self, percentage=0.0, center_text="0:0", color="#2980b9", parent=None):
        super().__init__(parent)
        self.percentage = max(0.0, min(100.0, percentage))
        self.center_text = center_text
        self.color = color
        # Lock 1:1 aspect ratio square size
        self.setFixedSize(70, 70)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def set_data(self, percentage, center_text, color=None):
        self.percentage = max(0.0, min(100.0, percentage))
        self.center_text = center_text
        if color:
            self.color = color
        self.update()

    def set_ratio_data(self, v1: int, v2: int, color=None):
        """Helper to compute percentage and display 'v1:v2' text in center."""
        total = v1 + v2
        if total <= 0:
            pct = 0.0
        else:
            pct = (v1 / total) * 100.0
        
        center_text = f"{v1}:{v2}"
        self.set_data(pct, center_text, color)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        side = min(width, height)
        margin = 8
        rect = QRectF(margin, margin, side - (margin * 2), side - (margin * 2))

        # 1. Draw background track ring (always visible base track)
        bg_pen = QPen(QColor("#dfe4ea"), 7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(bg_pen)
        painter.drawEllipse(rect)

        # 2. Draw progress arc if percentage > 0
        if self.percentage > 0.0:
            prog_pen = QPen(QColor(self.color), 7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(prog_pen)

            # Draw arc (0 to 100% mapped to 0 to 5760 in Qt units, starting from top 90 degrees)
            start_angle = 90 * 16
            span_angle_qt = int(- (self.percentage / 100.0) * 5760)
            painter.drawArc(rect, start_angle, span_angle_qt)

        # 3. Draw center text perfectly aligned in the exact middle
        painter.setPen(QColor("#2c3e50"))
        
        font = QFont("Segoe UI")
        font.setPointSizeF(9.5)
        font.setBold(True)
        painter.setFont(font)
        
        full_rect = QRectF(0, 0, width, height)
        painter.drawText(full_rect, Qt.AlignCenter, self.center_text)


class DonutMetricWidget(QGroupBox):
    """
    Square-proportioned Metric Widget featuring a Donut Chart with locked 1:1 ratio.
    Stacks elements vertically to ensure an exact square aspect ratio layout, 
    wrapped inside a styled GroupBox with a left-aligned title.
    """
    def __init__(self, title="Metric Widget", chart_color="#2980b9", parent=None):
        super().__init__(title, parent)
        self.base_color = chart_color
        self.chart_color = chart_color
        self.init_ui()

    def init_ui(self):
        # Apply strict QGroupBox styling with left-aligned title border
        self.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10px;
                color: #2c3e50;
                margin-top: 12px;
            }
            QGroupBox::title {
                subcontrol-position: top left;
                subcontrol-origin: margin;
                left: 10px;
                padding: 2px 6px;
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 4px;
            }
        """)

        # Use vertical layout to stack chart and description for a square aspect ratio
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 16, 10, 8)  # Top margin adjusted for the title
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        self.chart = DonutChartPainter(percentage=0.0, center_text="0:0", color=self.chart_color)
        layout.addWidget(self.chart, alignment=Qt.AlignCenter)

        # Center-aligned descriptive text container
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        info_layout.setAlignment(Qt.AlignCenter)

        self.lbl_title_desc = QLabel("• Tendency Info")
        self.lbl_title_desc.setStyleSheet("font-weight: bold; font-size: 10.5px; color: #2c3e50; border: none;")
        self.lbl_title_desc.setAlignment(Qt.AlignCenter)
        
        self.lbl_sub_desc = QLabel("• Standby...")
        self.lbl_sub_desc.setStyleSheet("font-size: 9.5px; color: #7f8c8d; border: none;")
        self.lbl_sub_desc.setAlignment(Qt.AlignCenter)

        info_layout.addWidget(self.lbl_title_desc)
        info_layout.addWidget(self.lbl_sub_desc)

        info_container = QWidget()
        info_container.setLayout(info_layout)
        info_container.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #e1e2e6;
                border-radius: 6px;
                padding: 4px 6px;
            }
        """)
        layout.addWidget(info_container)

        self.setLayout(layout)
        
        # Enforce strict square dimensions (equal width and height)
        self.setFixedSize(160, 160)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def set_custom_size(self, width: int = None, height: int = None, min_width: int = None, max_height: int = None):
        """Allows manual adjustment of widget dimensions with support for both positional and keyword arguments."""
        if width is not None and height is not None:
            self.setFixedSize(width, height)
        elif min_width is not None and max_height is not None:
            self.setFixedSize(min_width, max_height)

    def _resolve_dynamic_color(self, v1: int, v2: int) -> str:
        """Determines color dynamically based on ratio balance or extreme values."""
        total = v1 + v2
        if total <= 0:
            return self.base_color

        # For 6-number ratios (like Odd/Even or High/Low where optimal is 3:3)
        if total == 6:
            if v1 == 3:
                return self.base_color  # Optimal balanced color
            elif v1 in [2, 4]:
                return "#f39c12"        # Moderate variance (Amber warning)
            else:
                return "#e74c3c"        # Extreme skew (Alert red)
        
        return self.base_color

    def update_metric(self, percentage: float, center_text: str, description: str):
        """Updates the donut chart ratio, center display text, and subordinate description."""
        self.chart.set_data(percentage, center_text, self.chart_color)
        self.lbl_sub_desc.setText(f"• {description}")

    def update_ratio_metric(self, v1: int, v2: int, primary_desc: str, sub_desc: str):
        """Updates metric using dual ratio values with dynamic color adaptation."""
        dynamic_color = self._resolve_dynamic_color(v1, v2)
        self.chart_color = dynamic_color

        self.chart.set_ratio_data(v1, v2, dynamic_color)
        self.lbl_title_desc.setText(f"• {primary_desc}")
        self.lbl_sub_desc.setText(f"• {sub_desc}")